"""R4 — money & evidence surfaces. Rendered-UI + route-reachability. KEK unknowns resolved, reports
gate-blocking, billing page + invoice job, quality UI + mitigation, admin fleet tables, sandbox
controls wired, ROI projected-labeled."""
import os
import secrets

from realify import auth as core_auth, config, scheduler
from realify.agency import (crypto, keyring, tenancy, ops, rollups, db as agency_db)
from realify.pdp import ENVELOPES
from realify.mail import dev

DIRECT = os.environ.get("AGENCY_DATABASE_URL")
_H = {"x-realify-admin": "test-strong-admin-key-xyz"}


def _login(client, email=None):
    email = email or f"r4-{secrets.token_hex(4)}@x.com"
    core_auth.signup(email, "password1", "R4 Org")
    assert client.post("/api/login", json={"email": email, "password": "password1"}).status_code == 200
    return email


def _uid(cur, email):
    cur.execute("SELECT id FROM users WHERE email=%s", (email,)); return cur.fetchone()[0]


def _agency_brand(cur, currency="USD"):
    cur.execute("INSERT INTO agencies(name) VALUES('R4Ag') RETURNING id"); ag = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,tenant_kind) VALUES('R4Br',now()::text,1,'seller') RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status,maker_checker_threshold_usd_minor) "
                "VALUES(%s,%s,'active',1000000) RETURNING id", (ag, t))
    return ag, t, cur.fetchone()[0]


# ---- pre-item (a): KEK unknowns resolved ----
def test_kek_resolve_unknowns_zero(owner_conn, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", DIRECT)
    cur = owner_conn.cursor()
    _ag, tgood, _e = _agency_brand(cur)
    _ag2, tbad, _e2 = _agency_brand(cur)
    tenancy.set_brand_scope(cur, [tgood, tbad])
    keyring.ensure_brand_key(cur, tgood)                       # valid, current KEK
    # a fingerprint-less key wrapped under a DIFFERENT (bad) KEK
    cur.execute("INSERT INTO brand_keys(tenant_id, wrapped_dek, kek_fingerprint) VALUES(%s,%s,NULL)",
                (tbad, b"not-a-valid-wrapped-dek-under-this-kek"))
    cur.execute("UPDATE brand_keys SET kek_fingerprint=NULL WHERE tenant_id=%s", (tgood,))  # make it unknown too
    owner_conn.commit()
    res = keyring.resolve_unknowns(cur)
    owner_conn.commit()
    assert res["backfilled"] >= 1 and res["shredded"] >= 1     # good backfilled, bad shredded
    sweep = keyring.sweep_brand_keys(cur)
    assert sweep["unknown"] == 0                               # invariant


# ---- item 1: reports generate -> gate -> deliver, and corrupted-template blocked ----
def test_report_generate_deliver_and_block(agency_client, owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); monkeypatch.setenv("MAIL_DRIVER", "dev"); dev.clear()
    client, _ = agency_client
    email = _login(client)
    cur = owner_conn.cursor()
    _ag, t, _e = _agency_brand(cur)
    cur.execute("INSERT INTO rollup_cache(tenant_id,currency,gmv_minor,gmv_usd_minor,margin_minor,"
                "margin_usd_minor,tacos_bps) VALUES(%s,'USD',500000,500000,200000,200000,1200)", (t,))
    cur.execute("INSERT INTO users(email,created_at,tenant_id) VALUES(%s,now()::text,%s)",
                (f"brand4-{secrets.token_hex(3)}@x.com", t))
    owner_conn.commit()
    r = client.post(f"/api/agency/reports/{t}/generate", json={})
    assert r.status_code == 200 and r.json()["delivered"] is True
    assert dev.inbox(), "report not emailed"
    # corrupted template (a literal number not from the engine) -> factuality gate BLOCKS, no send
    dev.clear()
    bad = client.post(f"/api/agency/reports/{t}/generate", json={"template": "We made you $999999 extra."})
    assert bad.status_code == 422 and bad.json()["blocked"] is True
    assert dev.inbox() == []                                   # blocked report never sent


# ---- item 2: billing page + CSV + invoice job ----
def test_billing_page_and_invoice_job(agency_client, owner_conn, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", DIRECT)
    client, _ = agency_client
    email = _login(client)
    cur = owner_conn.cursor()
    uid = _uid(cur, email)
    ag, t, eng = _agency_brand(cur)
    ops.grant_role(cur, uid, eng, t, uid, "account_manager")
    cur.execute("INSERT INTO agency_subscriptions(agency_id,per_account_price_minor,platform_fee_minor,"
                "usage_unit_price_minor,decisions_pool,status) VALUES(%s,10000,5000,50,1000,'active')", (ag,))
    owner_conn.commit()
    body = client.get("/agency/billing").text
    assert "Decisions pool" in body and "warn you at 85%" in body
    assert "Value delivered" in body and "/api/agency/billing/export.csv" in body
    assert client.get("/api/agency/billing/export.csv").status_code == 200
    # invoice job builds an invoice for the period
    res = scheduler.run_billing_once(log=lambda *a, **k: None)
    assert res.get("invoices_built", 0) >= 1
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM invoices WHERE agency_id=%s", (str(ag),))
    assert cur.fetchone()[0] >= 1


# ---- item 3: quality UI + mitigation ----
def test_quality_ui_below_gate_and_mitigation(agency_client, owner_conn):
    client, H = agency_client
    email = _login(client)
    cur = owner_conn.cursor()
    uid = _uid(cur, email)
    ag, t, eng = _agency_brand(cur)
    ops.grant_role(cur, uid, eng, t, uid, "account_manager")
    tenancy.set_brand_scope(cur, [t])
    # 2 proposed, 0 executed -> precision 0% (below the 70% gate)
    for s in ("a", "b"):
        cur.execute("INSERT INTO approvals(tenant_id,engagement_id,lens,kind,signal,impact_usd_minor,status) "
                    "VALUES(%s,%s,'ads','bid',%s,1000,'proposed')", (t, eng, s))
    owner_conn.commit()
    body = client.get("/ops/agency/quality", headers=H).text
    assert "Precision by action class" in body and "Acceptance drift" in body
    assert "BELOW GATE" in body                                # coloring/label on the failing class
    assert "Review &amp; Apply" in body or "Review & Apply" in body
    r = client.post("/api/ops/quality/mitigation", headers=H,
                    json={"gate_key": "ads/bid", "change": "suppress below 0.85"})
    assert r.status_code == 200 and r.json()["ledgered"] is True


# ---- item 4: admin fleet tables + set-auto ----
def test_admin_fleet_tables_and_set_auto(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    ag, t, eng = _agency_brand(cur)                            # 1 account, 0 AMs -> leverage 0 < 1.5 gate
    owner_conn.commit()
    body = client.get("/ops/agency/admin", headers=H).text
    assert "Agencies — fleet" in body and "leverage" in body.lower()
    assert "Needs attention" in body and "Gates" in body
    assert "MRR" in body
    r = client.post("/api/ops/gates/set-auto", headers=H, json={"gate_key": "detector.acos", "status": "active"})
    assert r.status_code == 200 and r.json()["gate_id"]


# ---- item 5: sandbox controls wired (preset -> inject -> queue item) ----
def test_sandbox_controls_reachable(agency_client, owner_conn):
    import time
    from realify.agency import queue
    client, H = agency_client
    # R6.1: preset is accept-then-poll — POST returns {started}, then poll the job to done
    p = client.post("/api/ops/sandbox/preset", headers=H).json()
    assert p["ok"] and p["started"] is True
    for _ in range(100):
        if client.get("/api/ops/sandbox/job", headers=H).json()["done"]:   # any running world-job
            break
        time.sleep(0.2)
    st = client.get("/api/ops/sandbox/state", headers=H).json()
    assert st["loaded"] and st["brands"]
    t = st["brands"][0]["tenant_id"]
    inj = client.post(f"/api/ops/sandbox/inject/stockout/{t}", headers=H)
    assert inj.status_code == 200 and inj.json()["kind"] == "stockout"
    cur = owner_conn.cursor()
    owner_conn.rollback()
    tenancy.set_brand_scope(cur, [t])
    assert len(queue.build(cur, [t])) >= 1                     # injector produced queue items


# ---- item 6: ROI projected-labeled ----
def test_roi_projected_labeled(agency_client, owner_conn):
    client, _ = agency_client
    email = _login(client)
    cur = owner_conn.cursor()
    uid = _uid(cur, email)
    ag, t, eng = _agency_brand(cur)
    ops.grant_role(cur, uid, eng, t, uid, "account_manager")
    tenancy.set_brand_scope(cur, [t])
    cur.execute("INSERT INTO approvals(tenant_id,engagement_id,lens,kind,signal,impact_usd_minor,status) "
                "VALUES(%s,%s,'ads','bid','s',150000,'executed')", (t, eng))
    owner_conn.commit()
    body = client.get("/agency/roi").text
    assert "Projected impact of actions taken" in body
    assert "projected" in body.lower() and "not" in body.lower()   # explicit "not a measured counterfactual"
