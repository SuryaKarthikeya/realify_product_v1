"""P5 approvals & execution: maker-checker, T-P5-01 co-sign expiry, 02 nudge cap, 03 TOCTOU at
execute, 04 idempotency, 05 throttle, 06 canary breach + rollback, 07 pause-all halt. All against the
in-process mock marketplace (no real API)."""
import pytest

from realify.agency import approvals, execution, ops, tenancy
from realify.agency.mock_marketplace import MockMarketplace
from realify.pdp import ENVELOPES, ROLES, Action
from realify.mail import dev

ADMIN = ROLES["agency_admin"]
EXEC_ADS = Action("ads", "execute")


def _engagement(cur, threshold=0):
    """Returns (tenant_id, engagement_id, maker_user_id, checker_user_id) — real users (ledger FK)."""
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('AP',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO agencies(name) VALUES('APA') RETURNING id")
    ag = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id", (f"maker-{t}@x.com",))
    u1 = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id", (f"checker-{t}@x.com",))
    u2 = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status,maker_checker_threshold_usd_minor) "
                "VALUES(%s,%s,'active',%s) RETURNING id", (ag, t, threshold))
    return t, cur.fetchone()[0], u1, u2


def _ready_engagement(cur, envelope="Full Operate"):
    """Engagement with an active envelope + a proposed approval; returns (t, eng, approval_id)."""
    t, eng, u1, _ = _engagement(cur)
    tenancy.set_brand_scope(cur, [t])
    ops.publish_envelope(cur, None, eng, t, ENVELOPES[envelope], {})
    aid = approvals.propose(cur, t, eng, u1, "ads", "bid", "s", 1000)
    return t, eng, aid


# ---- maker-checker ----
def test_maker_checker_threshold(owner_conn):
    cur = owner_conn.cursor()
    t, eng, u1, u2 = _engagement(cur, threshold=50000)
    aid = approvals.propose(cur, t, eng, maker_user=u1, lens="ads", kind="bid", signal="s",
                            impact_usd_minor=100000)
    owner_conn.commit()
    with pytest.raises(approvals.ApprovalError):
        approvals.approve(cur, aid, checker_user=u1)               # same user, above threshold
    owner_conn.commit()
    assert approvals.approve(cur, aid, checker_user=u2)["status"] == "approved"
    owner_conn.commit()
    # below threshold: maker may self-approve
    aid2 = approvals.propose(cur, t, eng, maker_user=u1, lens="ads", kind="bid", signal="s",
                             impact_usd_minor=10)
    owner_conn.commit()
    assert approvals.approve(cur, aid2, checker_user=u1)["status"] == "approved"
    owner_conn.commit()


# ---- T-P5-01 ----
def test_cosign_expiry_never_executes_and_notifies(owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    cur = owner_conn.cursor()
    t, eng, u1, u2 = _engagement(cur)
    aid = approvals.propose(cur, t, eng, u1, "pricing", "price", "s", 100000, requires_cosign=True)
    approvals.approve(cur, aid, checker_user=u2)
    owner_conn.commit()
    cur.execute("SELECT status FROM approvals WHERE id=%s", (aid,))
    assert cur.fetchone()[0] == "cosign_pending"
    cur.execute("UPDATE approvals SET cosign_expires_at=now()-interval '1 day' WHERE id=%s", (aid,))
    owner_conn.commit()
    assert approvals.expire_cosigns(cur, [t], agency_email="ag@x.com") == 1
    owner_conn.commit()
    cur.execute("SELECT status FROM approvals WHERE id=%s", (aid,))
    assert cur.fetchone()[0] == "expired"
    cur.execute("SELECT count(*) FROM executions WHERE tenant_id=%s", (t,))
    assert cur.fetchone()[0] == 0                                   # expiry NEVER executes
    box = dev.inbox(to="ag@x.com")
    assert len(box) == 1 and "expired" in box[0]["body"].lower()


# ---- T-P5-02 ----
def test_nudge_cap_enforced(owner_conn):
    cur = owner_conn.cursor()
    t, eng, u1, _ = _engagement(cur)
    aid = approvals.propose(cur, t, eng, u1, "ads", "bid", "s", 1000)
    owner_conn.commit()
    assert approvals.nudge(cur, aid)["nudge_count"] == 1
    assert approvals.nudge(cur, aid)["nudge_count"] == 2
    with pytest.raises(approvals.ApprovalError):
        approvals.nudge(cur, aid)                                   # 3rd rejected
    owner_conn.commit()


# ---- T-P5-03 ----
def test_toctou_narrowed_envelope_excludes_at_execution(owner_conn):
    cur = owner_conn.cursor()
    t, eng, u1, _ = _engagement(cur)
    tenancy.set_brand_scope(cur, [t])
    ops.publish_envelope(cur, None, eng, t, ENVELOPES["Full Operate"], {})      # v1: execute allowed
    ops.publish_envelope(cur, None, eng, t, ENVELOPES["Read-only"], {})         # v2: narrowed
    aid = approvals.propose(cur, t, eng, u1, "ads", "bid", "s", 1000)
    owner_conn.commit()
    m = MockMarketplace(capacity=5)
    r = execution.execute_bulk(cur, m, t, aid, eng, composed_version=1, grant_caps=ADMIN,
                               action=EXEC_ADS, accounts=["a1", "a2", "a3"], value_fn=lambda a: "v")
    owner_conn.commit()
    assert r["executed"] == [] and len(r["excluded"]) == 3
    assert m.write_count == 0                                       # nothing written


# ---- T-P5-04 ----
def test_idempotency_zero_duplicate_writes_on_restart(owner_conn):
    cur = owner_conn.cursor()
    t, eng, aid = _ready_engagement(cur)
    owner_conn.commit()
    accts = ["a1", "a2", "a3"]
    m1 = MockMarketplace(capacity=5)
    r1 = execution.execute_bulk(cur, m1, t, aid, eng, 1, ADMIN, EXEC_ADS, accts, lambda a: "v", canary_size=99)
    owner_conn.commit()
    assert len(r1["executed"]) == 3 and m1.write_count == 3
    m2 = MockMarketplace(capacity=5)                                # crash-restart: fresh mock
    r2 = execution.execute_bulk(cur, m2, t, aid, eng, 1, ADMIN, EXEC_ADS, accts, lambda a: "v", canary_size=99)
    owner_conn.commit()
    assert m2.write_count == 0                                      # zero duplicate writes
    cur.execute("SELECT count(*) FROM executions WHERE approval_id=%s AND status='done'", (aid,))
    assert cur.fetchone()[0] == 3


# ---- T-P5-05 ----
def test_throttle_500_accounts_no_violations(owner_conn):
    cur = owner_conn.cursor()
    t, eng, aid = _ready_engagement(cur)
    owner_conn.commit()
    accts = [f"acc{i}" for i in range(500)]
    m = MockMarketplace(capacity=1)
    r = execution.execute_bulk(cur, m, t, aid, eng, 1, ADMIN, EXEC_ADS, accts, lambda a: "v", canary_size=999)
    owner_conn.commit()
    assert len(r["executed"]) == 500 and m.violations == 0
    assert all(v <= 1 for v in m.buckets.values())                 # never exceeded a bucket


# ---- T-P5-06 ----
def test_canary_breach_halts_and_rolls_back(owner_conn):
    cur = owner_conn.cursor()
    t, eng, aid = _ready_engagement(cur)
    owner_conn.commit()
    accts = [f"c{i}" for i in range(10)]
    m = MockMarketplace(capacity=5)
    pre = m.state_hash()
    r = execution.execute_bulk(cur, m, t, aid, eng, 1, ADMIN, EXEC_ADS, accts, lambda a: "v",
                               canary_size=2, breach_fn=lambda res, mock: len(res["executed"]) >= 2)
    owner_conn.commit()
    assert r["halted"] and r["halt_reason"] == "canary_breach"
    assert len(r["rolledback"]) == 2 and r["executed"] == []
    assert m.write_count == 2                                       # no fan-out beyond the canary
    assert m.state_hash() == pre                                    # rollback == snapshot-identical


# ---- T-P5-07 ----
def test_pause_all_halts_in_flight(owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    cur = owner_conn.cursor()
    t, eng, aid = _ready_engagement(cur)
    owner_conn.commit()
    accts = [f"p{i}" for i in range(10)]
    m = MockMarketplace(capacity=5)

    def vf(account):
        if account == "p2":                                        # brand pauses mid-flight
            execution.pause_all(cur, t, agency_email="ag@x.com")
        return "v"

    r = execution.execute_bulk(cur, m, t, aid, eng, 1, ADMIN, EXEC_ADS, accts, vf, canary_size=99)
    owner_conn.commit()
    assert r["halted"] and r["halt_reason"] == "paused"
    assert 0 < len(r["executed"]) < 10                             # in-flight halt, not all processed
    assert r["halt_seconds"] < 5
    cur.execute("SELECT count(*) FROM ledger WHERE tenant_id=%s AND action='execution.pause_all'", (t,))
    assert cur.fetchone()[0] == 1
    assert dev.inbox(to="ag@x.com")                                # agency notified
