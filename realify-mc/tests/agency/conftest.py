"""The agency suite is Postgres+PgBouncer-only (agency-plan §1c-2). It is NOT collected in the default
SQLite run (`make test` / `pytest tests/`) — collecting it there would show skips and break the
`allowed_skips: 1` invariant. It runs only when the harness env is present (`make test-agency` /
`make verify-p1`), where these fixtures build the schema once and give tests owner + app-role handles.
"""
import os

import pytest

POOLER = os.environ.get("AGENCY_POOLER_URL")
DIRECT = os.environ.get("AGENCY_DATABASE_URL")

if not POOLER:
    collect_ignore_glob = ["*"]
else:
    if not os.environ.get("STRIPE_LIVE_TEST"):
        # opt-in only: the real Stripe test-mode API test is not collected in CI (keeps skipped==0)
        collect_ignore = ["test_stripe_integration.py"]
    # keep dev-driver mail out of the repo cwd during the agency suite
    os.environ.setdefault("MAILBOX_DIR", os.path.join(os.path.expanduser("~/.realify-agency-harness"), "mailbox"))


def _dsn(url):
    # psycopg wants a libpq URL; strip SQLAlchemy's +psycopg driver tag.
    return (url or "").replace("postgresql+psycopg://", "postgresql://")


@pytest.fixture(scope="session", autouse=True)
def _agency_schema():
    """Build the full schema (base + agency tables + RLS + grants) once, as owner, on the harness PG."""
    from realify import config, db
    saved = config.DATABASE_URL
    config.DATABASE_URL = DIRECT                      # dbengine.url() reads config.DATABASE_URL
    try:
        con = db.connect()
        con.execute("DROP SCHEMA public CASCADE")
        con.execute("CREATE SCHEMA public")
        con.commit()
        con.close()
        db.init_db()                                  # alembic upgrade head -> 0015 agency core + RLS
    finally:
        config.DATABASE_URL = saved
    yield


@pytest.fixture
def clean_agency():
    """Truncate agency tables before a test (owner; TRUNCATE is not row-filtered by RLS)."""
    import psycopg
    with psycopg.connect(_dsn(DIRECT)) as c, c.cursor() as cur:
        cur.execute("TRUNCATE ledger, grants, envelopes, engagements, brand_keys, "
                    "agency_members, agencies RESTART IDENTITY CASCADE")
        c.commit()
    yield


@pytest.fixture
def app_conn():
    """A psycopg connection as the NON-owner app role, through PgBouncer (RLS in force)."""
    import psycopg
    c = psycopg.connect(_dsn(POOLER))
    try:
        yield c
    finally:
        c.close()


_ADMIN_KEY = "test-strong-admin-key-xyz"
_FUNNEL_TABLES = ("agency_provision_steps", "agency_invites", "agency_audit", "agency_requests",
                  "brand_consents", "connections", "agency_ingest_rows", "report_column_mappings",
                  "deletion_ledger", "agency_otp",
                  "metering_events", "invoice_lines", "invoices", "agency_subscriptions",
                  "suppression_list", "agency_pilots", "approvals", "executions", "brand_pause",
                  "gates",
                  "decisions", "rollup_cache",
                  "engagements", "envelopes", "grants", "brand_keys", "ledger", "agencies")


@pytest.fixture
def owner_conn():
    """Direct psycopg connection as the owner (for test setup/assertions), funnel tables truncated."""
    import psycopg
    c = psycopg.connect(_dsn(DIRECT))
    with c.cursor() as cur:
        cur.execute("TRUNCATE " + ", ".join(_FUNNEL_TABLES) + " RESTART IDENTITY CASCADE")
        c.commit()
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def agency_client(monkeypatch, owner_conn):
    """TestClient with the app pointed at the harness (owner) + AGENCY_CONSOLE on + admin key set.
    Returns (client, admin_headers). owner_conn (also injected) has already truncated funnel tables."""
    from realify import config
    monkeypatch.setattr(config, "DATABASE_URL", DIRECT, raising=False)
    monkeypatch.setenv("AGENCY_CONSOLE", "on")
    monkeypatch.setenv("REALIFY_ADMIN_KEY", _ADMIN_KEY)
    from run import make_app
    from fastapi.testclient import TestClient
    return TestClient(make_app()), {"x-realify-admin": _ADMIN_KEY}
