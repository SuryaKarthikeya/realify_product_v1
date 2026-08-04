"""Agency-suite smoke test: proves the Postgres+PgBouncer(transaction) harness is wired correctly —
the foundation every P1 RLS/pooler gate stands on. Skipped unless AGENCY_POOLER_URL is set (i.e. only
runs under `make test-agency` / docker-compose), so the default SQLite suite is unaffected.

Asserts: (1) queries round-trip through PgBouncer; (2) the app role is NOSUPERUSER and NOBYPASSRLS, so
FORCE ROW LEVEL SECURITY will actually bind to it; (3) `SET LOCAL` is transaction-scoped and does NOT
leak to the next transaction on a pooled server connection (the crux of T-P1-02)."""
import os

import pytest

POOLER = os.environ.get("AGENCY_POOLER_URL")
pytestmark = pytest.mark.skipif(not POOLER, reason="agency harness not up (set AGENCY_POOLER_URL)")


def _dsn():
    # psycopg wants a libpq DSN/URL; strip SQLAlchemy's +psycopg driver tag.
    return POOLER.replace("postgresql+psycopg://", "postgresql://")


def test_pooler_roundtrip_and_app_role_privileges():
    import psycopg
    with psycopg.connect(_dsn()) as c, c.cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
        is_super, bypass = cur.fetchone()
        assert is_super is False, "app role must not be SUPERUSER (RLS would be bypassed)"
        assert bypass is False, "app role must not have BYPASSRLS"


def test_set_local_is_transaction_scoped_through_pgbouncer():
    import psycopg
    with psycopg.connect(_dsn()) as c:
        with c.cursor() as cur:
            cur.execute("SET LOCAL app.brand_ids = 'brand-abc'")
            cur.execute("SELECT current_setting('app.brand_ids', true)")
            assert cur.fetchone()[0] == "brand-abc"
        c.commit()
        with c.cursor() as cur:
            cur.execute("SELECT current_setting('app.brand_ids', true)")
            leaked = cur.fetchone()[0]
            # Empty ('') if the next txn reused the same backend, NULL (None) if it landed on a
            # different pooled backend that never saw the GUC — either way it must NOT still be set.
            assert not leaked, f"SET LOCAL leaked across transactions ({leaked!r}) — pooler is unsafe"
        c.commit()
