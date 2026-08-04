"""Pytest-only test isolation.

Each test file sets os.environ["REALIFY_DB"] to its own tempdir at import time, but
config.DB_PATH is captured ONCE when realify.config is first imported (during collection),
so in a single pytest process every test actually shares the first-imported file while each
file's _fresh helper wipes a stale env path — leaking state across files.

This autouse fixture gives every test a unique throwaway DB and keeps BOTH the env var and
config.DB_PATH pointed at it, so db.connect() and the per-file _fresh helpers always agree.
Touches no production code; standalone `python3 tests/test_x.py` runs are unaffected.
"""
import os, tempfile
import pytest


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch):
    from realify import config, db, dbengine
    for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
        monkeypatch.setenv(_k, "fixture")

    # Postgres smoke (`run.py doctor --postgres` / `make smoke-pg`): DATABASE_URL overrides DB_PATH,
    # so all tests share ONE database. Give each test a clean slate by recreating the schema and
    # re-running migrations. This branch only fires when DATABASE_URL names Postgres — the default
    # SQLite file-per-test path below is completely untouched, so normal/CI runs are unaffected.
    if os.environ.get("DATABASE_URL") and dbengine.dialect() == "postgresql":
        con = db.connect()
        con.execute("DROP SCHEMA IF EXISTS public CASCADE")
        con.execute("CREATE SCHEMA public")
        con.commit()
        con.close()
        db.init_db()
        yield
        return

    # default: a unique throwaway SQLite file per test (fast, hermetic)
    path = os.path.join(tempfile.mkdtemp(prefix="realify_ci_"), "test.db")
    monkeypatch.setenv("REALIFY_DB", path)
    monkeypatch.setattr(config, "DB_PATH", path, raising=False)
    db.init_db()
    yield
