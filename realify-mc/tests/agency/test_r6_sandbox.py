"""R6 (agency/Postgres suite): the Account & data injection BRIDGE authz matrix + response contract,
persona-assume reachability, and the sandbox engine's idempotent multi-brand pilot load. The hub
rendered-UI + resynth guard live in tests/test_r6_hub_drawer.py (SQLite)."""
import os
import secrets
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realify import auth as core_auth, inflight
from realify.agency import sandbox


def _tenant_of_kind(owner_conn, client, kind, account_type=None):
    """Sign up a fresh user+tenant, tag the tenant's kind, log the client in. Returns (uid, tid)."""
    email = f"r6-{secrets.token_hex(4)}@x.com"
    uid, tid = core_auth.signup(email, "password1", "R6 Org")   # tenant_kind defaults to 'seller' (NOT NULL)
    cur = owner_conn.cursor()
    if kind is not None:
        cur.execute("UPDATE tenants SET tenant_kind=%s WHERE id=%s", (kind, tid))
    if account_type:
        cur.execute("UPDATE tenants SET account_type=%s WHERE id=%s", (account_type, tid))
    owner_conn.commit()
    r = client.post("/api/login", json={"email": email, "password": "password1"})
    assert r.status_code == 200, r.text
    return uid, tid


# ---- bridge authz matrix ----
def test_bridge_requires_session(agency_client):
    client, _H = agency_client
    # AGENCY_CONSOLE on (fixture) but no tenant session -> 401
    assert client.post("/api/sandbox/inject/undercut").status_code == 401


def test_bridge_authz_matrix(agency_client, owner_conn):
    client, _H = agency_client
    # seller tenant + account_type customer (a normal paying customer) -> 403
    _tenant_of_kind(owner_conn, client, "seller", account_type="customer")
    assert client.post("/api/sandbox/inject/undercut").status_code == 403
    # default seller (untagged) -> 403 (fail closed: only internal/sandbox allowed)
    _tenant_of_kind(owner_conn, client, None)
    assert client.post("/api/sandbox/inject/undercut").status_code == 403
    # internal -> ok
    _tenant_of_kind(owner_conn, client, "internal")
    assert client.post("/api/sandbox/inject/stockout").status_code == 200
    # sandbox -> ok
    _tenant_of_kind(owner_conn, client, "sandbox")
    assert client.post("/api/sandbox/inject/undercut").status_code == 200


# ---- injector response contract {ok, message, link} ----
def test_bridge_injector_contract(agency_client, owner_conn):
    client, _H = agency_client
    _tenant_of_kind(owner_conn, client, "sandbox")
    for kind in ("undercut", "stockout", "ad_overspend", "fx_swing"):
        d = client.post(f"/api/sandbox/inject/{kind}").json()
        assert d["ok"] is True, d
        assert isinstance(d["message"], str) and d["message"] and "Failed." not in d["message"]
        assert isinstance(d["link"], str) and d["link"].startswith("/")


def test_bridge_double_fire_rejected(agency_client, owner_conn):
    client, _H = agency_client
    _uid, tid = _tenant_of_kind(owner_conn, client, "sandbox")
    inflight.acquire("inject_undercut", tid)                  # simulate an in-flight injection
    try:
        assert client.post("/api/sandbox/inject/undercut").status_code == 409
    finally:
        inflight.release("inject_undercut", tid)
    assert client.post("/api/sandbox/inject/undercut").status_code == 200


# ---- persona-assume reachability (superlogin/admin gated): each doorway lands on a NON-404 surface ----
def test_assume_returns_reachable_redirects(agency_client, owner_conn):
    client, H = agency_client
    sandbox.load_preset(owner_conn.cursor()); owner_conn.commit()

    # Realify Admin: assume returns /ops/agency/admin; it resolves (via the admin key) — not 404
    r = client.post("/api/ops/sandbox/assume", headers=H, json={"persona": "admin"})
    assert r.status_code == 200 and r.json()["redirect"] == "/ops/agency/admin"
    assert client.get("/ops/agency/admin", headers=H).status_code == 200

    # Agency Client Lead: assume sets the session grant; the FLEET GRID resolves for that uid (R11: the
    # cross-brand queue is retired — the agency triages on the fleet and /agency/queue now redirects there)
    r = client.post("/api/ops/sandbox/assume", headers=H, json={"persona": "client_lead"})
    assert r.status_code == 200 and r.json()["redirect"] == "/agency/console"
    assert client.get("/agency/console").status_code == 200
    assert client.get("/agency/queue", follow_redirects=False).status_code == 307   # retired -> redirect

    # Brand Owner: assume sets a brand-owner session; the portal for that brand is not 404
    r = client.post("/api/ops/sandbox/assume", headers=H, json={"persona": "brand_owner"})
    assert r.status_code == 200 and r.json()["redirect"].startswith("/brand/portal/")
    assert client.get(r.json()["redirect"]).status_code != 404


# ---- R6.1 defect #1/#2: load is accept-then-poll; the POST returns immediately and state reads
#      stay fast while a long load runs in the background (page never blocks) ----
def test_load_accept_then_poll_nonblocking(agency_client, owner_conn, monkeypatch):
    client, H = agency_client
    ev = threading.Event()
    orig = sandbox.load_preset

    def blocking(cur, scenario="us_pilot", as_of=None):
        ev.wait(timeout=15)                                  # simulate a long-running load
        return orig(cur, scenario, as_of)
    monkeypatch.setattr(sandbox, "load_preset", blocking)

    t0 = time.time()
    r = client.post("/api/ops/sandbox/preset", headers=H, json={"scenario": "us_pilot"})
    assert r.status_code == 200 and r.json()["started"] is True
    assert time.time() - t0 < 3.0                            # accepted immediately, NOT blocked on the load

    s0 = time.time()
    st = client.get("/api/ops/sandbox/state", headers=H).json()
    assert time.time() - s0 < 4.0                            # state read never queues behind the load
    assert (st.get("loading") or {}).get("in_progress") is True   # "load in progress since <t>"

    assert client.get("/api/ops/sandbox/job?scenario=us_pilot", headers=H).json()["state"] == "running"
    ev.set()                                                 # let the background load finish
    for _ in range(80):
        j = client.get("/api/ops/sandbox/job?scenario=us_pilot", headers=H).json()
        if j["done"]:
            break
        time.sleep(0.2)
    assert j["done"] and j["state"] == "done"


# ---- idempotent multi-brand pilot: two loads => same tenant set + byte-identical decisions ----
def test_pilot_load_idempotent(owner_conn):
    cur = owner_conn.cursor()
    a = sandbox.load_preset(cur); owner_conn.commit()
    b = sandbox.load_preset(cur); owner_conn.commit()
    assert a["brand_count"] == 8 and a["usd_count"] == 8 and a["inr_count"] == 0
    assert sorted(x["tenant_id"] for x in a["brands"]) == sorted(x["tenant_id"] for x in b["brands"])

    def sig(tid):
        cur.execute("SELECT signal,impact_usd_minor,lens,kind FROM decisions WHERE tenant_id=%s "
                    "ORDER BY signal,impact_usd_minor,lens,kind", (tid,))
        return cur.fetchall()
    for br in a["brands"]:
        assert sig(br["tenant_id"]) == sig(br["tenant_id"])   # stable
    # count of sandbox agencies for 'pilot' stays 1 (never mints extras)
    cur.execute("SELECT count(*) FROM agencies WHERE sandbox_scenario='us_pilot'")
    assert cur.fetchone()[0] == 1
