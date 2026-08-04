"""DB engine seam (#005 1c, slice 1) — the single change-point for the SQLite -> Postgres swap.

SQLite stays the default and behaves byte-for-byte as before: `db.connect()` returns a native
`sqlite3` connection on the sqlite dialect (this module is not in that hot path). For a Postgres
URL (`DATABASE_URL=postgresql+psycopg://...`), `db.connect()` returns a `_PGConnection` that exposes
the SAME API the ~20 repositories already use — `execute(sql, params)` with `?` placeholders,
`fetchone` / `fetchall`, rows that support `row["col"]`, `row[0]` and `dict(row)`, plus
`commit` / `rollback` / `close` — by translating `?` -> `%s` for psycopg and adapting psycopg rows.
So the repositories and their ~500 placeholders are UNCHANGED. That is the payoff of the 1b sweep.

What this slice does NOT do (lands in slice 2, when Postgres becomes the engine): per-dialect
schema DDL in Alembic, the `init` -> `alembic upgrade head` cutover, the 14
`INSERT OR REPLACE/IGNORE` -> `ON CONFLICT` upserts, `lastrowid` -> `RETURNING`, the two
`PRAGMA table_info` -> `information_schema` lookups, and the one SQLite date function. Until then,
SQLite is the only fully wired dialect; this module makes Postgres reachable and testable.
"""
from urllib.parse import urlparse
import os
import re as _re
from . import config

_engines = {}


def url():
    """Live DB URL. A Postgres `DATABASE_URL` wins as-is; otherwise SQLite, derived *live* from
    `config.DB_PATH` so a runtime override (and the test suite's `config.DB_PATH` monkeypatch) is
    honoured — keeping alembic and `db.connect()` pointed at the same file."""
    du = config.DATABASE_URL
    if urlparse(du).scheme.split("+")[0].lower() in ("postgresql", "postgres"):
        return du
    return "sqlite:///" + os.path.abspath(config.DB_PATH)


def dialect():
    scheme = urlparse(url()).scheme.split("+")[0].lower()
    return "postgresql" if scheme in ("postgresql", "postgres") else (scheme or "sqlite")


def engine():
    """Lazily-built SQLAlchemy engine, cached per-URL (so per-test SQLite paths each get their own).
    NullPool — one DBAPI connection per checkout, matching the open/close-per-operation model the
    app already uses. SQLAlchemy is imported only here, so a pure-SQLite run never imports it."""
    u = url()
    eng = _engines.get(u)
    if eng is None:
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool
        eng = _engines[u] = create_engine(u, poolclass=NullPool, future=True)
    return eng


def translate_placeholders(sql):
    """`?` (sqlite/qmark) -> `%s` (psycopg/pyformat). Any literal `%` is doubled first so pyformat
    does not mis-parse it (the current SQL contains none — verified — but this keeps it safe)."""
    return sql.replace("%", "%%").replace("?", "%s")


# --- INSERT OR REPLACE/IGNORE -> ON CONFLICT (Postgres). Keyed by each table's real unique key, so
#     the repositories keep their sqlite-style SQL unchanged — the wrapper rewrites at execute time. ---
_CONFLICT_KEYS = {
    "category_products": ("tenant_id", "segment", "asin"),
    "sourcing_list":     ("tenant_id", "asin", "segment"),
    "seller_skus":       ("tenant_id", "asin"),
    "rules":             ("rule_id",),
    "products":          ("tenant_id", "internal_sku"),
    "channel_listings":  ("tenant_id", "channel", "channel_id"),
    "channels":          ("tenant_id", "channel"),
    "channel_economics": ("tenant_id", "internal_sku", "channel"),
    "keepa_snapshots":   ("tenant_id", "asin", "captured_at"),
    "tierc_signals":     ("tenant_id", "dedup_key"),
    "seller_orders":     ("tenant_id", "order_id"),
    "card_research":     ("tenant_id", "dedup_key"),
    "card_why":          ("tenant_id", "dedup_key"),
    "sku_field_provenance": ("tenant_id", "internal_sku", "field", "basis"),
    "account_interpretation": ("tenant_id", "category", "key"),
    "pending_confirmations": ("tenant_id", "ckey"),
    "ad_performance": ("tenant_id", "internal_sku", "period_start", "grain"),
    "sku_revenue_period": ("tenant_id", "internal_sku", "period_start", "grain"),
    "ingested_reports": ("tenant_id", "content_hash"),
    "cogs_suggestions": ("tenant_id", "internal_sku"),
    "tenant_topology": ("tenant_id",),
    "sku_crosswalk": ("tenant_id", "channel", "store_id", "external_sku", "external_variant_id"),
    "ad_entity_perf": ("tenant_id", "campaign", "ad_group", "advertised_asin", "period_start", "grain"),
    "ad_search_term": ("tenant_id", "campaign", "ad_group", "customer_search_term", "period_start", "grain"),
    "ad_ingest_summary": ("tenant_id",),
}

_UPSERT_RE = _re.compile(r"^\s*INSERT\s+OR\s+(REPLACE|IGNORE)\s+INTO\s+(\w+)\s*\(([^)]*)\)", _re.I | _re.S)


def rewrite_upsert(sql):
    """Rewrite `INSERT OR REPLACE/IGNORE INTO t(cols) ...` to Postgres `ON CONFLICT`:
    REPLACE -> DO UPDATE the non-key columns; IGNORE -> DO NOTHING. No-op for any other SQL."""
    m = _UPSERT_RE.match(sql)
    if not m:
        return sql
    mode, table, collist = m.group(1).upper(), m.group(2), m.group(3)
    cols = [c.strip() for c in collist.split(",") if c.strip()]
    base = _re.sub(r"^(\s*)INSERT\s+OR\s+(?:REPLACE|IGNORE)\s+INTO", r"\1INSERT INTO", sql,
                   count=1, flags=_re.I).rstrip().rstrip(";")
    keys = _CONFLICT_KEYS.get(table)
    if keys is None:                       # unknown table — best-effort plain insert
        return base
    target = "(" + ", ".join(keys) + ")"
    if mode == "IGNORE":
        return base + f" ON CONFLICT {target} DO NOTHING"
    setcols = [c for c in cols if c not in keys] or list(keys[:1])
    setclause = ", ".join(f"{c}=EXCLUDED.{c}" for c in setcols)
    return base + f" ON CONFLICT {target} DO UPDATE SET {setclause}"


def schema_to_postgres(sqlite_sql):
    """Translate the SQLite DDL in `db.SCHEMA` to Postgres. The only SQLite-ism is
    `INTEGER PRIMARY KEY AUTOINCREMENT` (-> `BIGSERIAL PRIMARY KEY`); everything else (TEXT, INTEGER,
    REAL, PRIMARY KEY(...), UNIQUE(...), DEFAULT, CREATE TABLE/INDEX IF NOT EXISTS) is valid PG."""
    out = _re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "BIGSERIAL PRIMARY KEY", sqlite_sql, flags=_re.I)
    out = _re.sub(r"\s+AUTOINCREMENT", "", out, flags=_re.I)   # any stragglers
    return out


def validate_url(u=None):
    """Fail fast with ONE clear line if a Postgres `DATABASE_URL` is malformed (e.g. an empty
    password slot — the exact rough edge that turned a typo into an outage), instead of a deep
    psycopg traceback at connect time. SQLite (always derived from a path) is never rejected."""
    u = u or url()
    scheme = urlparse(u).scheme.split("+")[0].lower()
    if scheme not in ("postgresql", "postgres"):
        return
    from sqlalchemy.engine.url import make_url
    try:
        parsed = make_url(u)
    except Exception as e:
        raise SystemExit(f"DATABASE_URL is not a valid database URL ({e}). "
                         "Check the DATABASE_URL line in .env.")
    masked = u.replace(parsed.password, "***") if parsed.password else u
    if not parsed.password:
        raise SystemExit(
            f"DATABASE_URL points at Postgres but has no password (got '{masked}'). "
            "Set it in .env as postgresql+psycopg://user:PASSWORD@host:5432/db.")
    if not parsed.host or not parsed.database:
        raise SystemExit(f"DATABASE_URL is missing a host or database name (got '{masked}').")


def _postgres_required():
    """True when this process is meant to run on Postgres (prod/agency mode): the agency console is on,
    or REQUIRE_POSTGRES is explicitly set. SQLite is allowed ONLY when neither signal is present
    (explicit dev/test)."""
    if os.environ.get("REQUIRE_POSTGRES", "").strip().lower() in ("1", "true", "on", "yes"):
        return True
    return (os.environ.get("AGENCY_CONSOLE", "").strip().lower() == "on")


def assert_backend():
    """FAIL-CLOSED startup guard (R10.1). In prod/agency mode the app MUST run on a reachable Postgres;
    it REFUSES to start on SQLite or with an unreachable/mis-configured Postgres — no silent fallback
    that would serve production traffic off an empty local SQLite file (the R9.1 deploy incident). In
    dev/test (no AGENCY_CONSOLE / REQUIRE_POSTGRES) SQLite stays the frictionless default."""
    if not _postgres_required():
        return
    if dialect() != "postgresql":
        raise SystemExit(
            "FATAL: prod/agency mode requires Postgres, but DATABASE_URL is absent/blank or not a "
            f"Postgres URL (resolved dialect: '{dialect()}'). Refusing to start on SQLite. Set a valid "
            "postgresql+psycopg://user:PASSWORD@host:5432/db in DATABASE_URL — or unset AGENCY_CONSOLE / "
            "REQUIRE_POSTGRES for an explicit dev/test SQLite run.")
    validate_url()                                   # shape check (raises SystemExit on malformed)
    try:                                             # connectivity check — no silent fallback
        conn = engine().raw_connection()
        try:
            conn.cursor().execute("SELECT 1")
        finally:
            conn.close()
    except SystemExit:
        raise
    except Exception as e:
        raise SystemExit(
            "FATAL: prod/agency mode requires a REACHABLE Postgres, but the connection failed: "
            f"{str(e).splitlines()[0]}. Refusing to start (no SQLite fallback).")


# Launch vars that a stale-backup restore has silently dropped before (R9.1: AGENCY_CONSOLE reverted
# off; the mail incident: MAIL_DRIVER reverted to dev → OTPs went to ./.mailbox instead of SES). In
# prod/agency mode these must be set explicitly, never left to a dev default. MAIL_DRIVER is ABORT-grade
# (its silent 'dev' default is exactly the incident); the addressing vars warn loudly (they have safe
# realifyai.app defaults). Documented in .env.example so a restore can reinstate them.
_REQUIRED_PROD_ENV = ("MAIL_DRIVER",)                       # abort if unset in prod/agency mode
_WARN_PROD_ENV = ("EMAIL_DOMAIN", "REPLY_TO_ADDRESS")       # warn if unset (code defaults apply)


def assert_prod_env(warn=None):
    """ENV-DRIFT GUARD (R11 Part E-c) — extends the R10.1 fail-closed pattern beyond the DB. In
    prod/agency mode, boot-time-validate the required launch vars so a stale-backup restore fails LOUD
    instead of silently falling back to a dev mail driver. `warn` is an injectable sink (defaults to
    stderr) so tests can capture the warnings. ABORTs (SystemExit) on a missing abort-grade var."""
    if not _postgres_required():
        return
    if warn is None:
        import sys as _sys
        def warn(m): print(m, file=_sys.stderr)
    missing = [k for k in _REQUIRED_PROD_ENV if not (os.environ.get(k) or "").strip()]
    if missing:
        raise SystemExit(
            "FATAL: prod/agency mode is missing required launch var(s): " + ", ".join(missing) + ". "
            "Refusing to start on a dev default (e.g. an unset MAIL_DRIVER silently mails to ./.mailbox "
            "instead of SES — the R11 mail incident). Set them in .env (see .env.example prod guidance).")
    for k in _WARN_PROD_ENV:
        if not (os.environ.get(k) or "").strip():
            warn(f"[env-drift] WARNING: {k} is unset in prod/agency mode — using a code default. "
                 f"Set it explicitly in .env (see .env.example) so a stale-backup restore can't drift it.")


class _Row(dict):
    """Dict that also supports positional indexing like ``sqlite3.Row`` (``row[0]``)."""
    def __init__(self, mapping, order):
        super().__init__(mapping)
        self._order = order

    def __getitem__(self, key):
        if isinstance(key, int):
            return super().__getitem__(self._order[key])
        return super().__getitem__(key)


class _PGCursor:
    def __init__(self, cur):
        self._cur = cur

    @property
    def lastrowid(self):
        raise NotImplementedError(
            "lastrowid is unsupported on Postgres — use INSERT ... RETURNING id (1c slice 2)"
        )

    @property
    def rowcount(self):
        return self._cur.rowcount

    def _cols(self):
        return [d.name for d in (self._cur.description or [])]

    def _wrap(self, row):
        if row is None:
            return None
        cols = self._cols()
        return _Row(dict(zip(cols, row)), cols)

    def fetchone(self):
        return self._wrap(self._cur.fetchone())

    def fetchall(self):
        cols = self._cols()
        return [_Row(dict(zip(cols, r)), cols) for r in self._cur.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


class _PGConnection:
    """A psycopg connection adapted to the sqlite3-style API the repositories use."""
    def __init__(self, raw):
        self._raw = raw
        self._total_changes = 0

    def _bump(self, sql, cur):
        # Mirror sqlite3.Connection.total_changes: cumulative rows inserted/updated/deleted.
        if sql.lstrip()[:6].upper() in ("INSERT", "UPDATE", "DELETE"):
            rc = cur.rowcount
            if rc and rc > 0:
                self._total_changes += rc

    @property
    def total_changes(self):
        return self._total_changes

    def execute(self, sql, params=()):
        cur = self._raw.cursor()
        t = translate_placeholders(rewrite_upsert(sql))
        cur.execute(t, tuple(params))
        self._bump(t, cur)
        return _PGCursor(cur)

    def executemany(self, sql, seq_of_params):
        # Same SQL adaptation as execute() (upsert rewrite + ?->%s), applied once to the statement;
        # the rows are passed through as tuples. Empty batch is a no-op, matching sqlite3.
        rows = [tuple(p) for p in seq_of_params]
        cur = self._raw.cursor()
        if rows:
            t = translate_placeholders(rewrite_upsert(sql))
            cur.executemany(t, rows)
            self._bump(t, cur)
        return _PGCursor(cur)

    def executescript(self, script):
        cur = self._raw.cursor()
        for stmt in (s for s in script.split(";") if s.strip()):
            cur.execute(stmt)
        self._raw.commit()

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()

    # sqlite3.Connection supports `with con:` (commit on success / rollback on error); the
    # repositories and routers rely on that. Mirror it here so `with db.connect() as con:` works
    # identically on Postgres. Each db.connect() is a fresh pooled connection not reused after the
    # block, so we also return it to the pool on exit.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._raw.commit()
        else:
            self._raw.rollback()
        self._raw.close()
        return False


def pg_connect():
    """A Postgres connection via the engine's DBAPI (psycopg), wrapped to the sqlite3-style API."""
    return _PGConnection(engine().raw_connection())
