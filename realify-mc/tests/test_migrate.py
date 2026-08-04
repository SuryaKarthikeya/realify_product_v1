"""Tests for the 1g SQLite->Postgres data migration. The Postgres dest is faked (the sandbox has no
Postgres); the real round-trip happens at cutover against RDS. These validate the orchestration:
table discovery, truncate-then-copy, and catalog-driven serial-sequence resets."""
import os, sqlite3, sys, tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_mig_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import migrate_sqlite_to_pg as mig  # noqa: E402


class _FakeCursor:
    def __init__(self):
        self.executemany_calls = []
        self.execute_calls = []
        self._last = ""
        self._last_params = ()
    def execute(self, sql, params=()):
        self.execute_calls.append((sql, tuple(params) if params else ()))
        self._last = sql.lower()
        self._last_params = tuple(params) if params else ()
        return self
    def executemany(self, sql, rows):
        self.executemany_calls.append((sql, list(rows)))
        return self
    def fetchall(self):
        # information_schema serial-column lookup: 'jobs' has a serial 'id', others don't
        if "information_schema.columns" in self._last:
            tbl = self._last_params[0]
            return [("id",)] if tbl == "jobs" else []
        return []
    def fetchone(self):
        if "pg_get_serial_sequence" in self._last:
            tbl = self._last_params[0]
            return (f"{tbl}_id_seq" if tbl == "jobs" else None,)
        if "count(*)" in self._last:
            return (3,)
        return (None,)


class _FakeDest:
    def __init__(self):
        self.cur = _FakeCursor()
        self.commits = 0
    def cursor(self):
        return self.cur
    def commit(self):
        self.commits += 1
    def close(self):
        pass


def _make_source():
    path = os.path.join(tempfile.mkdtemp(prefix="realify_src_"), "src.db")
    s = sqlite3.connect(path)
    s.executescript(
        "CREATE TABLE jobs(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT);"
        "CREATE TABLE seller_skus(tenant_id INTEGER, asin TEXT, PRIMARY KEY(tenant_id, asin));")
    s.execute("INSERT INTO jobs(kind) VALUES('a')")
    s.execute("INSERT INTO jobs(kind) VALUES('b')")
    s.execute("INSERT INTO seller_skus VALUES(1,'B001')")
    s.commit(); s.close()
    return path


def test_migrate_truncates_copies_and_resets_only_serial_tables():
    src = _make_source()
    dest = _FakeDest()
    report = mig.migrate(dry_run=False, ensure_schema=False, source_path=src, dest=dest)

    by_table = {r[0]: r for r in report}
    assert by_table["jobs"][1] == 2 and by_table["seller_skus"][1] == 1   # source counts

    # every table is truncated then re-inserted (idempotent regardless of constraints)
    truncates = [c for c in dest.cur.execute_calls if c[0].startswith("TRUNCATE TABLE")]
    assert {"TRUNCATE TABLE jobs", "TRUNCATE TABLE seller_skus"} <= {c[0] for c in truncates}
    inserts = "\n".join(sql for sql, _ in dest.cur.executemany_calls)
    assert "%s" in inserts and "ON CONFLICT" not in inserts          # plain INSERT, psycopg paramstyle

    # serial reset happens for jobs (has serial id), NOT for seller_skus (composite PK, no serial) —
    # this is the exact crash that's now fixed
    setvals = [c for c in dest.cur.execute_calls if "setval" in c[0]]
    assert len(setvals) == 1                                          # only jobs
    assert "FROM jobs" in setvals[0][0]


def test_dry_run_writes_nothing():
    src = _make_source()
    dest = _FakeDest()
    report = mig.migrate(dry_run=True, ensure_schema=False, source_path=src, dest=dest)
    assert dest.cur.executemany_calls == []
    assert not any(c[0].startswith("TRUNCATE") for c in dest.cur.execute_calls)
    assert all(r[2] is None for r in report)


if __name__ == "__main__":
    test_migrate_truncates_copies_and_resets_only_serial_tables()
    test_dry_run_writes_nothing()
    print("migrate OK")
