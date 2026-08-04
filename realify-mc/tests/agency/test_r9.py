"""R9 (Postgres/agency suite): parametric generator (determinism + background job), both single-country
pilots load idempotently, dynamic impersonation authz + ledger, email short-circuit (sandbox-only inline
approve), and the back-to-hub bar on impersonated surfaces."""
import os
import secrets
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from realify import auth as core_auth
from realify.agency import synth, sandbox, consent


def _brands(cur, world_key="us_pilot"):
    st = sandbox.load_preset(cur, world_key)
    return st


# ---- generator determinism (same country+params+seed => byte-identical world) ----
def test_generate_deterministic(owner_conn):
    cur = owner_conn.cursor()
    p = {"country": "US", "categories": ["Home & Kitchen", "Pet Supplies"], "sku_count": 120,
         "brands_per_agency": 4, "direct_brands": 1, "seed": "det-r9", "moments": ["expired_conn"]}
    a = synth.generate_world(cur, p); owner_conn.commit()

    def snap(st):
        out = {}
        for b in st["brands"]:
            cur.execute("SELECT asin,price,cogs,days_of_cover,tacos,buybox_pct FROM seller_skus "
                        "WHERE tenant_id=%s ORDER BY asin", (b["tenant_id"],))
            out[b["name"]] = cur.fetchall()
        return out
    s1 = snap(a)
    b = synth.generate_world(cur, p); owner_conn.commit()      # reload same params = reset
    assert a["country"] == "US" and a["currency"] == "USD" and a["brand_count"] == 4
    assert sorted(x["tenant_id"] for x in a["brands"]) == sorted(x["tenant_id"] for x in b["brands"])
    assert s1 == snap(b)                                        # byte-identical world


def test_both_pilots_load_idempotent(owner_conn):
    cur = owner_conn.cursor()
    us1 = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    us2 = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    inn1 = sandbox.load_preset(cur, "in_pilot"); owner_conn.commit()
    inn2 = sandbox.load_preset(cur, "in_pilot"); owner_conn.commit()
    assert us1["country"] == "US" and us1["currency"] == "USD" and us1["brand_count"] == 8
    assert inn1["country"] == "IN" and inn1["currency"] == "INR" and inn1["brand_count"] == 8
    assert sorted(b["tenant_id"] for b in us1["brands"]) == sorted(b["tenant_id"] for b in us2["brands"])
    assert sorted(b["tenant_id"] for b in inn1["brands"]) == sorted(b["tenant_id"] for b in inn2["brands"])
    # single-country: they never mint extra agencies for their key
    cur.execute("SELECT count(*) FROM agencies WHERE sandbox_scenario='us_pilot'"); assert cur.fetchone()[0] == 1
    cur.execute("SELECT count(*) FROM agencies WHERE sandbox_scenario='in_pilot'"); assert cur.fetchone()[0] == 1


# ---- generation is a BACKGROUND job: POST returns started<3s while a slow gen runs ----
def test_generate_is_background_job(agency_client, owner_conn, monkeypatch):
    client, H = agency_client
    ev = threading.Event()
    orig = synth.generate_world

    def blocking(cur, params):
        ev.wait(timeout=15)
        return orig(cur, params)
    monkeypatch.setattr(synth, "generate_world", blocking)
    body = {"country": "US", "sku_count": 60, "brands_per_agency": 2, "seed": "bg-r9"}
    t0 = time.time()
    r = client.post("/api/ops/sandbox/generate", headers=H, json=body)
    assert r.status_code == 200 and r.json()["started"] is True
    assert time.time() - t0 < 3.0                              # accepted immediately, not blocked
    wk = r.json()["world_key"]
    assert client.get(f"/api/ops/sandbox/job?scenario={wk}", headers=H).json()["state"] == "running"
    ev.set()
    for _ in range(80):
        if client.get(f"/api/ops/sandbox/job?scenario={wk}", headers=H).json()["done"]:
            break
        time.sleep(0.2)
    assert client.get(f"/api/ops/sandbox/job?scenario={wk}", headers=H).json()["state"] == "done"


# ---- dynamic impersonation authz: sandbox tenant ok (+ledgered); non-sandbox 403 ----
def test_impersonation_authz_and_ledger(agency_client, owner_conn):
    client, H = agency_client
    st = sandbox.load_preset(owner_conn.cursor(), "us_pilot"); owner_conn.commit()
    brand = st["brands"][0]["tenant_id"]
    r = client.post("/api/ops/sandbox/impersonate", headers=H,
                    json={"kind": "managed_brand", "tenant_id": brand})
    assert r.status_code == 200 and r.json()["redirect"].startswith("/brand/portal/")
    cur = owner_conn.cursor()
    cur.execute("SELECT count(*) FROM ledger WHERE tenant_id=%s AND action='sandbox.impersonate'", (brand,))
    assert cur.fetchone()[0] >= 1                              # ledgered
    # a non-sandbox (seller) tenant cannot be impersonated
    _uid, seller = core_auth.signup(f"r9s-{secrets.token_hex(3)}@x.com", "password1", "S")
    r2 = client.post("/api/ops/sandbox/impersonate", headers=H,
                     json={"kind": "managed_brand", "tenant_id": seller})
    assert r2.status_code == 403


# ---- email short-circuit: ON => inline approve completes the grant + ledger; non-sandbox 403; OFF 409 ----
def _pending_consent(cur, agency_id, tenant_id):
    token, cid = consent.create_consent(cur, str(agency_id), tenant_id, "Sandbox Agency",
                                        "brand@x.com", "Ads Only", {})
    return cid


def test_short_circuit_sandbox_only(agency_client, owner_conn):
    client, H = agency_client
    st = sandbox.load_preset(owner_conn.cursor(), "us_pilot"); owner_conn.commit()
    cur = owner_conn.cursor()
    brand = st["brands"][1]["tenant_id"]
    client.post("/api/ops/sandbox/shortcircuit", headers=H, json={"on": True})   # ON
    cid = _pending_consent(cur, st["agency_id"], brand); owner_conn.commit()
    r = client.post(f"/api/ops/sandbox/consent/{cid}/approve-inline", headers=H)
    assert r.status_code == 200 and r.json()["status"] == "granted"
    cur.execute("SELECT status FROM brand_consents WHERE id=%s", (cid,)); assert cur.fetchone()[0] == "granted"
    cur.execute("SELECT count(*) FROM ledger WHERE tenant_id=%s AND action='consent.grant.impersonated'", (brand,))
    assert cur.fetchone()[0] >= 1                              # ledgered as impersonated

    # non-sandbox tenant: control is SERVER-ENFORCED off (403) even with short-circuit ON
    _uid, seller = core_auth.signup(f"r9c-{secrets.token_hex(3)}@x.com", "password1", "S")
    cur.execute("SELECT id FROM agencies WHERE sandbox_scenario='us_pilot'"); ag = cur.fetchone()[0]
    cid2 = _pending_consent(cur, ag, seller); owner_conn.commit()
    assert client.post(f"/api/ops/sandbox/consent/{cid2}/approve-inline", headers=H).status_code == 403

    # OFF: inline approve refused (409) — forces the real email round-trip
    client.post("/api/ops/sandbox/shortcircuit", headers=H, json={"on": False})
    cid3 = _pending_consent(cur, st["agency_id"], st["brands"][2]["tenant_id"]); owner_conn.commit()
    assert client.post(f"/api/ops/sandbox/consent/{cid3}/approve-inline", headers=H).status_code == 409


# ---- back-to-hub bar present on each impersonated surface ----
def test_back_to_hub_bar_on_surfaces(agency_client, owner_conn):
    client, H = agency_client
    st = sandbox.load_preset(owner_conn.cursor(), "us_pilot"); owner_conn.commit()
    brand = st["brands"][0]["tenant_id"]
    # agency operator -> queue
    client.post("/api/ops/sandbox/impersonate", headers=H, json={"kind": "agency", "tenant_id": brand})
    q = client.get("/agency/queue").text
    assert "r9backbar" in q and "acting as:" in q and "Back to hub" in q
    # managed brand -> portal
    client.post("/api/ops/sandbox/impersonate", headers=H, json={"kind": "managed_brand", "tenant_id": brand})
    p = client.get(f"/brand/portal/{brand}").text
    assert "r9backbar" in p and "Managed Brand Owner" in p
    # admin -> fleet
    client.post("/api/ops/sandbox/impersonate", headers=H, json={"kind": "admin"})
    a = client.get("/ops/agency/admin", headers=H).text
    assert "r9backbar" in a and "Realify Admin" in a
