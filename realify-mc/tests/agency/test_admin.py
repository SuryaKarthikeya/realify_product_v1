"""P7 agency-suite: T-P7-01 attest-vs-auto, T-P7-02 attestation expiry, T-P7-03 exclusion (both
classes), T-P7-05 quality reproducible, T-P7-07 sandbox deterministic + guided steps, T-P7-08 drift +
direct-brand persona."""
import datetime
import os

import psycopg
import pytest

from realify.agency import gates, quality, drift, sandbox, internal, queue, tenancy

_POOLER = os.environ.get("AGENCY_POOLER_URL", "").replace("postgresql+psycopg://", "postgresql://")


def _queue_via_app(tenant_id):
    """Build the queue through the NON-superuser app role so RLS scoping actually applies (owner_conn
    is a harness superuser and would bypass RLS, returning every tenant's decisions)."""
    app = psycopg.connect(_POOLER, prepare_threshold=None)
    try:
        rows = queue.build(app.cursor(), [tenant_id])
        return [(i["signal"], i["impact_usd_minor"], i["lens"], i["kind"]) for i in rows]
    finally:
        app.close()


# ---- T-P7-01 ----
def test_attested_cannot_overwrite_auto_gate(owner_conn):
    cur = owner_conn.cursor()
    gates.set_auto(cur, "detector.acos", "platform")
    owner_conn.commit()
    with pytest.raises(gates.AttestOverwriteError):
        gates.attest(cur, "detector.acos", "platform", "https://evidence/1", None, actor="ops")
    owner_conn.commit()
    with pytest.raises(ValueError):                         # evidence is required
        gates.attest(cur, "detector.new", "platform", None, None, actor="ops")
    owner_conn.commit()


# ---- T-P7-02 ----
def test_attestation_expiry_flips_gate(owner_conn):
    cur = owner_conn.cursor()
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    gates.attest(cur, "detector.qa", "agency", "https://evidence/2", past, actor="ops")
    owner_conn.commit()
    assert gates.current(cur, "detector.qa")["status"] == "active"
    assert gates.expire_gates(cur) >= 1
    owner_conn.commit()
    assert gates.current(cur, "detector.qa")["status"] == "EXPIRED"


# ---- T-P7-03 (R1: aggregates key off tenant_kind; spec-driven update, not a weakening) ----
def test_aggregates_exclude_nonseller_kinds(owner_conn):
    cur = owner_conn.cursor()
    before = internal.count_billable_tenants(cur)
    # every non-seller kind is excluded from the billable base
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,is_internal,tenant_kind) "
                "VALUES('i',now()::text,1,true,'internal')")
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,sandbox,tenant_kind) "
                "VALUES('s',now()::text,1,1,'sandbox')")
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,is_internal,tenant_kind) "
                "VALUES('w',now()::text,1,true,'agency_workspace')")
    owner_conn.commit()
    assert internal.count_billable_tenants(cur) == before          # all non-seller kinds excluded
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,stripe_customer_id) "
                "VALUES('c',now()::text,1,'cus_x')")               # tenant_kind defaults 'seller'
    owner_conn.commit()
    assert internal.count_billable_tenants(cur) == before + 1       # a seller tenant does count


# ---- T-P7-05 ----
def test_quality_metrics_reproducible(owner_conn):
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('Q',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO agencies(name) VALUES('QA') RETURNING id"); ag = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active') RETURNING id",
                (ag, t))
    eng = cur.fetchone()[0]
    tenancy.set_brand_scope(cur, [t])
    cur.execute("INSERT INTO approvals(tenant_id,engagement_id,lens,kind,impact_usd_minor,status) "
                "VALUES(%s,%s,'ads','bid',1000,'approved') RETURNING id", (t, eng))
    aid = cur.fetchone()[0]
    cur.execute("INSERT INTO executions(tenant_id,approval_id,account,idempotency_key,status) "
                "VALUES(%s,%s,'a1','k1','done')", (t, aid))
    owner_conn.commit()
    p1 = quality.precision_by_action(cur, [t])
    p2 = quality.precision_by_action(cur, [t])
    assert p1 == p2 and p1["ads/bid"]["proposed"] == 1 and p1["ads/bid"]["realized"] == 1


# ---- T-P7-07 (R6: pilot preset, idempotent, guided steps reference a decision OR reachable surface) ----
def test_sandbox_preset_deterministic_and_guided_refs_decisions(owner_conn):
    cur = owner_conn.cursor()
    p = sandbox.load_preset(cur)                                            # default scenario = us_pilot
    owner_conn.commit()
    assert p["brand_count"] == 8 and p["usd_count"] == 8 and p["inr_count"] == 0   # US pilot (single-country)
    brand_ids_1 = sorted(b["tenant_id"] for b in p["brands"])
    q1 = _queue_via_app(p["tenant_id"])
    from realify.agency import guided
    steps = guided.build_run(cur, None, "customer")            # R11.1 teleprompter script
    # every guided step drives a REAL surface (nav URL); the script hops personas (cross-persona walkthrough)
    assert steps and all(s.get("nav") for s in steps)
    assert len({s["persona"] for s in steps}) >= 2             # flips persona (AM ↔ brand owner)
    assert any(f"/agency/brand/{b['tenant_id']}" == s["nav"] for s in steps for b in p["brands"])  # drills into a real brand
    p2 = sandbox.load_preset(cur)                                           # reload = reset to seed
    owner_conn.commit()
    brand_ids_2 = sorted(b["tenant_id"] for b in p2["brands"])
    q2 = _queue_via_app(p2["tenant_id"])
    assert brand_ids_1 == brand_ids_2                                       # IDEMPOTENT: same tenant set, no extras
    assert q1 == q2 and q1                                                  # same seed => byte-identical queue


# ---- T-P7-08 ----
def test_direct_brand_persona_and_drift(owner_conn):
    cur = owner_conn.cursor()
    setup = sandbox.personas(cur)
    owner_conn.commit()
    direct, managed = setup["direct_tenant"], setup["managed_tenant"]
    cur.execute("SELECT COALESCE(sandbox,0) FROM tenants WHERE id=%s", (direct,))
    assert cur.fetchone()[0] in (1, True)                                   # direct brand is sandbox
    cur.execute("SELECT count(*) FROM engagements WHERE tenant_id=%s", (direct,))
    assert cur.fetchone()[0] == 0                                           # no engagement -> agency features absent
    cur.execute("SELECT count(*) FROM engagements WHERE tenant_id=%s AND status='active'", (managed,))
    assert cur.fetchone()[0] == 1                                           # managed brand is engaged
    assert drift.drift_count(cur, [direct, managed]) == 0                   # neither is an orphan
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('orphan',now()::text,1) RETURNING id")
    orphan = cur.fetchone()[0]
    owner_conn.commit()
    assert drift.drift_count(cur, [orphan]) == 1                            # orphan (seller) flagged
    # R1: drift keys off tenant_kind — reclassifying out of 'seller' clears drift (spec-driven update)
    cur.execute("UPDATE tenants SET tenant_kind='internal', is_internal=true WHERE id=%s", (orphan,))
    owner_conn.commit()
    assert drift.drift_count(cur, [orphan]) == 0                            # reclassified -> not drift
