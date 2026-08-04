"""R2 — close the action loop. Route-reachability + semantics: agency-scoped invite authz, cosign
derivation + maker-checker matrix, click-to-mock-write e2e, Undo, and the bulk canary/rollback route."""
import secrets

import pytest

from realify import auth as core_auth
from realify.agency import approvals, ops, tenancy, mock_marketplace
from realify.agency.actor import resolve_actor
from realify.pdp import ENVELOPES


def _login(client, email=None):
    email = email or f"r2-{secrets.token_hex(4)}@x.com"
    core_auth.signup(email, "password1", "R2 Org")
    assert client.post("/api/login", json={"email": email, "password": "password1"}).status_code == 200


def _setup(cur, threshold=1_000_000, cosign_thr=0):
    cur.execute("INSERT INTO agencies(name) VALUES('R2Ag') RETURNING id"); ag = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('R2Br',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status,maker_checker_threshold_usd_minor,"
                "brand_cosign_threshold_usd_minor) VALUES(%s,%s,'active',%s,%s) RETURNING id",
                (ag, t, threshold, cosign_thr))
    return ag, t, cur.fetchone()[0]


def _uid(cur, email):
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    return cur.fetchone()[0]


# ---- resolve_actor must work under the NON-BYPASS app role (RLS enforced), not just the harness owner ----
def test_resolve_actor_under_rls_app_role(owner_conn, app_conn):
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('RA') RETURNING id"); ag = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('rb',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active') RETURNING id",
                (ag, t))
    eng = cur.fetchone()[0]
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id",
                (f"ra-{secrets.token_hex(3)}@x.com",))
    u = cur.fetchone()[0]
    ops.grant_role(cur, u, eng, t, u, "account_manager")
    owner_conn.commit()
    # realify_app (NOSUPERUSER/NOBYPASSRLS, RLS FORCED) — resolve_actor must succeed via the selfread policy
    ctx = resolve_actor(app_conn.cursor(), u)
    app_conn.rollback()
    assert t in ctx.allowed_tenant_ids and ag in ctx.agency_ids


# ---- item 0: agency-scoped invite authz ----
def test_invite_authz_grant_isolation_and_staff(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    email = f"admin-{secrets.token_hex(4)}@x.com"
    _login(client, email)
    uid = _uid(cur, email)
    cur.execute("INSERT INTO agencies(name) VALUES('AgA') RETURNING id"); agA = cur.fetchone()[0]
    cur.execute("INSERT INTO agencies(name) VALUES('AgB') RETURNING id"); agB = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('brA',now()::text,1) RETURNING id")
    tA = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active') RETURNING id",
                (agA, tA))
    engA = cur.fetchone()[0]
    ops.grant_role(cur, uid, engA, tA, uid, "agency_admin")
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('newbr',now()::text,1) RETURNING id")
    brand = cur.fetchone()[0]
    owner_conn.commit()

    inv = lambda ag, hdrs=None, e="b@x.com": client.post(
        "/api/agencies/consent/invite", headers=(hdrs or {}),
        json={"agency_id": str(ag), "tenant_id": brand, "agency_name": "X", "email": e, "template": "Advise"})
    assert inv(agA).status_code == 200                       # (a) agency admin invites OWN brand
    assert inv(agB).status_code == 403                       # (b) cannot invite ANOTHER agency's brand
    assert inv(agB, H, "s@x.com").status_code == 200         # (c) Realify staff key path still works
    _login(client, f"plain-{secrets.token_hex(4)}@x.com")    # (d) plain user (no grant) -> 403
    assert inv(agA, None, "p@x.com").status_code == 403


# ---- item 1: cosign derivation + maker-checker matrix ----
def test_cosign_derived_and_maker_checker_matrix(owner_conn):
    cur = owner_conn.cursor()
    _ag, t, eng = _setup(cur, threshold=5000, cosign_thr=8000)
    cur.execute("INSERT INTO users(email,created_at) VALUES(%s,now()::text) RETURNING id",
                (f"u-{secrets.token_hex(3)}@x.com",))
    u = cur.fetchone()[0]
    tenancy.set_brand_scope(cur, [t])
    # cosign derivation (not hardcoded)
    assert approvals.cosign_required(cur, eng, "pricing", "set", 100) is True     # pricing always co-signs
    assert approvals.cosign_required(cur, eng, "ads", "bid", 7000) is False       # below cosign threshold
    assert approvals.cosign_required(cur, eng, "ads", "bid", 9000) is True        # >= brand_cosign_threshold
    # maker-checker: below threshold, same user Approve -> approved
    a1 = approvals.propose(cur, t, eng, u, "ads", "bid", "s", 1000, requires_cosign=False)
    assert approvals.approve(cur, a1, u)["status"] == "approved"
    # at/above threshold, same user -> distinct checker required
    a2 = approvals.propose(cur, t, eng, u, "ads", "bid", "s", 6000, requires_cosign=False)
    with pytest.raises(approvals.ApprovalError):
        approvals.approve(cur, a2, u)
    # cosign-required below threshold -> cosign_pending (waits for the brand; silence never executes)
    a3 = approvals.propose(cur, t, eng, u, "ads", "bid", "s", 1000, requires_cosign=True)
    assert approvals.approve(cur, a3, u)["status"] == "cosign_pending"


# ---- item 2: click -> approved -> executed -> mock write -> Undo ----
def test_click_to_mock_write_and_undo(agency_client, owner_conn):
    client, _ = agency_client
    email = f"amx-{secrets.token_hex(4)}@x.com"
    _login(client, email)
    cur = owner_conn.cursor()
    uid = _uid(cur, email)
    _ag, t, eng = _setup(cur)                                 # high threshold -> below-threshold path
    ops.grant_role(cur, uid, eng, t, uid, "account_manager")
    ops.publish_envelope(cur, uid, eng, t, ENVELOPES["Full Operate"], {})
    owner_conn.commit()
    acct = f"acct-{t}"
    before = mock_marketplace.get_mock().value(acct)
    r = client.post("/api/agency/queue/propose", json={"tenant_id": t, "lens": "ads", "kind": "bid",
                                                       "signal": "undercut", "impact_usd_minor": 1000})
    assert r.status_code == 200 and r.json()["status"] == "executed" and r.json()["executed"] is True
    aid = r.json()["approval_id"]
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM executions WHERE approval_id=%s AND status='done'", (aid,))
    assert cur.fetchone()[0] == 1                             # exactly one write recorded
    tenancy.set_brand_scope(cur, [t])
    cur.execute("SELECT count(*) FROM ledger WHERE action='execution.write' AND tenant_id=%s", (t,))
    assert cur.fetchone()[0] == 1                             # ledger chain has the write
    assert mock_marketplace.get_mock().value(acct) is not None
    # R15 Part 0 — the drill-in now scope-switches into the real five-lens app; the execute + Undo loop
    # is exercised directly against the (unchanged) agency machinery below.
    assert client.get(f"/agency/brand/{t}", follow_redirects=False).status_code == 303
    # Undo -> snapshot restored
    cur.execute("SELECT id FROM executions WHERE approval_id=%s AND status='done'", (aid,))
    xid = cur.fetchone()[0]
    owner_conn.rollback()
    u = client.post(f"/api/agency/executions/{xid}/undo")
    assert u.status_code == 200 and u.json()["undone"] is True
    owner_conn.rollback()
    cur.execute("SELECT status FROM executions WHERE id=%s", (xid,))
    assert cur.fetchone()[0] == "rolledback"
    assert mock_marketplace.get_mock().value(acct) == before  # restored to pre-state


# ---- item 2: bulk route reachability (canary halt + rollback, and clean fan-out) ----
def test_bulk_route_canary_and_clean(agency_client, owner_conn):
    client, _ = agency_client
    email = f"blk-{secrets.token_hex(4)}@x.com"
    _login(client, email)
    cur = owner_conn.cursor()
    uid = _uid(cur, email)
    _ag, t, eng = _setup(cur)
    ops.grant_role(cur, uid, eng, t, uid, "account_manager")
    ops.publish_envelope(cur, uid, eng, t, ENVELOPES["Full Operate"], {})
    owner_conn.commit()
    breach = client.post("/api/agency/queue/bulk", json={
        "tenant_id": t, "lens": "ads", "kind": "bid", "signal": "s", "impact_usd_minor": 1000,
        "accounts": [f"blk-{t}-{i}" for i in range(6)], "canary_size": 2, "breach": True}).json()["result"]
    assert breach["halted"] is True and breach["halt_reason"] == "canary_breach"
    assert breach["rolledback"] == 2 and breach["executed"] == 0
    clean = client.post("/api/agency/queue/bulk", json={
        "tenant_id": t, "lens": "ads", "kind": "bid", "signal": "s", "impact_usd_minor": 1000,
        "accounts": [f"ok-{t}-{i}" for i in range(3)], "canary_size": 1}).json()["result"]
    assert clean["executed"] == 3 and clean["halted"] is False
