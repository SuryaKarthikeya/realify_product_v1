"""T-P1-01 rls_lint + live RLS enforcement (USING and WITH CHECK) on the brand-scoped agency tables."""
import os

import psycopg
import pytest

from realify.agency.constants import BRAND_SCOPED_TABLES as BRAND_SCOPED

DIRECT = os.environ.get("AGENCY_DATABASE_URL")
POOLER = os.environ.get("AGENCY_POOLER_URL")


def _dsn(url):
    return url.replace("postgresql+psycopg://", "postgresql://")


# ---- T-P1-01: rls_lint (query pg_catalog) --------------------------------------------------------
def test_rls_enabled_and_forced_on_every_brand_scoped_table():
    with psycopg.connect(_dsn(DIRECT)) as c, c.cursor() as cur:
        cur.execute("SELECT relname, relrowsecurity, relforcerowsecurity "
                    "FROM pg_class WHERE relname = ANY(%s)", (BRAND_SCOPED,))
        got = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    assert set(got) == set(BRAND_SCOPED), f"missing tables: {set(BRAND_SCOPED) - set(got)}"
    for t in BRAND_SCOPED:
        assert got[t] == (True, True), f"{t}: RLS must be ENABLED and FORCED, got {got[t]}"


def test_every_brand_scoped_table_has_a_policy():
    with psycopg.connect(_dsn(DIRECT)) as c, c.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_policies WHERE schemaname='public'")
        policied = {r[0] for r in cur.fetchall()}
    for t in BRAND_SCOPED:
        assert t in policied, f"{t} has no RLS policy"


def test_app_role_has_no_bypassrls_and_is_not_table_owner():
    with psycopg.connect(_dsn(DIRECT)) as c, c.cursor() as cur:
        cur.execute("SELECT count(*) FROM pg_roles WHERE rolname='realify_app' AND rolbypassrls")
        assert cur.fetchone()[0] == 0, "app role must not have BYPASSRLS"
        cur.execute("SELECT c.relname, pg_get_userbyid(c.relowner) FROM pg_class c "
                    "WHERE c.relname = ANY(%s)", (BRAND_SCOPED,))
        for name, owner in cur.fetchall():
            assert owner != "realify_app", f"{name} must not be owned by the app role"


# ---- live enforcement: USING (visibility), WITH CHECK (writes), fail-closed ----------------------
def test_rls_isolates_brands_through_pooler(clean_agency):
    with psycopg.connect(_dsn(POOLER)) as c:
        cur = c.cursor()
        cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('A',now()::text,1) RETURNING id")
        a = cur.fetchone()[0]
        cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('B',now()::text,1) RETURNING id")
        b = cur.fetchone()[0]
        cur.execute("INSERT INTO agencies(name) VALUES('Acme') RETURNING id")
        ag = cur.fetchone()[0]
        c.commit()

        # seed both brands under a scope that covers both
        cur = c.cursor()
        cur.execute("SELECT set_config('app.brand_ids', %s, true)", ("{%d,%d}" % (a, b),))
        cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active')", (ag, a))
        cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active')", (ag, b))
        c.commit()

        # scope to A only -> USING hides B
        cur = c.cursor()
        cur.execute("SELECT set_config('app.brand_ids', %s, true)", ("{%d}" % a,))
        cur.execute("SELECT tenant_id FROM engagements ORDER BY tenant_id")
        assert [r[0] for r in cur.fetchall()] == [a]

        # WITH CHECK blocks writing outside scope
        with pytest.raises(psycopg.errors.Error):
            cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active')", (ag, b))
        c.rollback()

    # fresh connection, no scope set -> fail-closed (zero rows), proving the default denies
    with psycopg.connect(_dsn(POOLER)) as c2, c2.cursor() as cur2:
        cur2.execute("SELECT count(*) FROM engagements")
        assert cur2.fetchone()[0] == 0
