"""Tests for the DB engine seam (#005 1c slice 1)."""
import os, tempfile, sys

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_dbe_"), "t.db")
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, dbengine  # noqa: E402


def test_default_url_and_dialect_are_sqlite():
    assert dbengine.url().startswith("sqlite:///")
    assert dbengine.dialect() == "sqlite"


def test_dialect_detection_for_postgres_urls():
    from urllib.parse import urlparse
    for u in ("postgresql://h/db", "postgresql+psycopg://u:p@h:5432/db", "postgres://h/db"):
        scheme = urlparse(u).scheme.split("+")[0].lower()
        assert ("postgresql" if scheme in ("postgresql", "postgres") else scheme) == "postgresql"


def test_placeholder_translation_qmark_to_pyformat():
    assert dbengine.translate_placeholders(
        "SELECT * FROM t WHERE a=? AND b=?") == "SELECT * FROM t WHERE a=%s AND b=%s"
    # any literal % is doubled so psycopg's pyformat doesn't mis-parse it
    assert dbengine.translate_placeholders(
        "WHERE x LIKE '%a%' AND y=?") == "WHERE x LIKE '%%a%%' AND y=%s"


def test_sqlite_connect_is_unchanged_and_row_compatible():
    db.init_db()
    con = db.connect()
    con.execute("CREATE TABLE IF NOT EXISTS _t(a, b)")
    con.execute("INSERT INTO _t(a,b) VALUES(?,?)", (1, "x"))
    con.commit()
    row = con.execute("SELECT a,b FROM _t").fetchone()
    assert row["a"] == 1 and row["b"] == "x"      # name access
    assert row[0] == 1                            # positional access (sqlite3.Row parity)
    assert dict(row)["b"] == "x"                  # dict() conversion
    con.close()


# --- Postgres wrapper validated against a fake DBAPI (real psycopg round-trip happens at RDS) ---
class _FakeCur:
    def __init__(self):
        self.executed = []
        self._rows = []
        self._rowcount = 0
        self.description = None

    def execute(self, sql, params):
        self.executed.append((sql, params))
        if sql.strip().upper().startswith("SELECT"):
            self.description = [type("D", (), {"name": "a"}), type("D", (), {"name": "b"})]
            self._rows = [(1, "x")]; self._rowcount = 1
        else:
            self.description, self._rows = None, []
            self._rowcount = 1                      # one row affected by the write

    def executemany(self, sql, seq):
        seq = list(seq)
        self.executed.append((sql, seq))
        self.description, self._rows = None, []
        self._rowcount = len(seq)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    @property
    def rowcount(self):
        return self._rowcount


class _FakeRaw:
    def __init__(self):
        self.cur = _FakeCur()
        self.committed = False

    def cursor(self):
        return self.cur

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        pass


def test_pg_wrapper_translates_placeholders_and_adapts_rows():
    raw = _FakeRaw()
    con = dbengine._PGConnection(raw)
    con.execute("INSERT INTO t(a,b) VALUES(?,?)", (1, "x"))
    assert raw.cur.executed[-1][0] == "INSERT INTO t(a,b) VALUES(%s,%s)"   # ? -> %s for psycopg
    row = con.execute("SELECT a,b FROM t WHERE a=?", (1,)).fetchone()
    assert row["a"] == 1 and row["b"] == "x"     # name access
    assert row[0] == 1                           # positional access
    assert dict(row) == {"a": 1, "b": "x"}       # dict() conversion
    con.commit()
    assert raw.committed


def test_pg_wrapper_executemany_translates_and_rewrites():
    raw = _FakeRaw()
    con = dbengine._PGConnection(raw)
    # plain batch insert: only placeholder translation
    con.executemany("INSERT INTO settlements(a,b) VALUES(?,?)", [(1, "x"), (2, "y")])
    sql, rows = raw.cur.executed[-1]
    assert sql == "INSERT INTO settlements(a,b) VALUES(%s,%s)"
    assert rows == [(1, "x"), (2, "y")]
    # INSERT OR IGNORE batch: upsert rewrite -> ON CONFLICT ... DO NOTHING, then ?->%s
    con.executemany("INSERT OR IGNORE INTO seller_orders(tenant_id,order_id) VALUES(?,?)",
                    [(1, "o1"), (1, "o2")])
    sql2, _ = raw.cur.executed[-1]
    assert "ON CONFLICT" in sql2 and "DO NOTHING" in sql2 and "?" not in sql2
    # empty batch is a no-op (matches sqlite3) — nothing new recorded
    before = len(raw.cur.executed)
    con.executemany("INSERT INTO settlements(a,b) VALUES(?,?)", [])
    assert len(raw.cur.executed) == before


def test_pg_wrapper_total_changes_counts_writes_only():
    raw = _FakeRaw()
    con = dbengine._PGConnection(raw)
    assert con.total_changes == 0
    con.execute("SELECT a,b FROM t WHERE a=?", (1,))     # reads don't count
    assert con.total_changes == 0
    con.execute("INSERT INTO t(a,b) VALUES(?,?)", (1, "x"))   # +1
    con.execute("UPDATE t SET b=? WHERE a=?", ("y", 1))       # +1
    assert con.total_changes == 2
    con.executemany("INSERT INTO t(a,b) VALUES(?,?)", [(2, "p"), (3, "q")])  # +2
    assert con.total_changes == 4


if __name__ == "__main__":
    test_default_url_and_dialect_are_sqlite()
    test_dialect_detection_for_postgres_urls()
    test_placeholder_translation_qmark_to_pyformat()
    test_sqlite_connect_is_unchanged_and_row_compatible()
    print("dbengine OK")


# ---- slice 2: ON CONFLICT rewrite, schema translation, RETURNING ----
def test_rewrite_upsert_replace_to_on_conflict_do_update():
    out = dbengine.rewrite_upsert(
        "INSERT OR REPLACE INTO card_research(tenant_id,dedup_key,payload,created_at) VALUES(?,?,?,?)")
    assert out == (
        "INSERT INTO card_research(tenant_id,dedup_key,payload,created_at) VALUES(?,?,?,?) "
        "ON CONFLICT (tenant_id, dedup_key) DO UPDATE SET payload=EXCLUDED.payload, created_at=EXCLUDED.created_at")


def test_rewrite_upsert_ignore_to_on_conflict_do_nothing():
    out = dbengine.rewrite_upsert(
        "INSERT OR IGNORE INTO keepa_snapshots(tenant_id,asin,captured_at,price) VALUES(?,?,?,?)")
    assert out == (
        "INSERT INTO keepa_snapshots(tenant_id,asin,captured_at,price) VALUES(?,?,?,?) "
        "ON CONFLICT (tenant_id, asin, captured_at) DO NOTHING")


def test_rewrite_upsert_noop_for_plain_insert():
    sql = "INSERT INTO cards(tenant_id,dedup_key) VALUES(?,?)"
    assert dbengine.rewrite_upsert(sql) == sql


def test_schema_to_postgres_translates_autoincrement():
    from realify import db
    pg = dbengine.schema_to_postgres(db.SCHEMA)
    assert "BIGSERIAL PRIMARY KEY" in pg
    assert "AUTOINCREMENT" not in pg.upper()
    assert pg.count("BIGSERIAL PRIMARY KEY") == 20      # all 20 autoincrement PKs translated


def test_all_upsert_tables_have_conflict_keys():
    """Guard: every table the repos upsert into must have a conflict key, or Postgres breaks."""
    import glob, re as _re2, os as _os
    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    pat = _re2.compile(r"INSERT\s+OR\s+(?:REPLACE|IGNORE)\s+INTO\s+(\w+)", _re2.I)
    tables = set()
    for f in glob.glob(_os.path.join(root, "realify/repositories/*.py")):
        with open(f) as fh:
            tables.update(pat.findall(fh.read()))
    missing = tables - set(dbengine._CONFLICT_KEYS)
    assert not missing, f"upsert tables missing conflict keys: {missing}"


def test_create_returning_id_sqlite():
    db.init_db()
    con = db.connect()
    now = db.now_iso()
    jid = db.create_returning_id(
        con, "INSERT INTO jobs(tenant_id,kind,state,created_at,updated_at) VALUES(?,?,?,?,?)",
        (1, "k", "queued", now, now))
    assert isinstance(jid, int) and jid >= 1
    con.close()
