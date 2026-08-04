"""R3 — brand-real data + brand surfaces. Rendered-UI + route-reachability. Covers: KEK guard +
brand-keys sweep, real feeders, data-sources ingest, cosign delivery e2e, brand portal, day-0
baseline, offboarding + deletion certificate."""
import os
import re
import secrets

import pytest

from realify import auth as core_auth, config, scheduler
from realify.agency import (crypto, keyring, tenancy, queue, ops, approvals, mock_marketplace,
                            db as agency_db)
from realify.pdp import ENVELOPES
from realify.mail import dev

DIRECT = os.environ.get("AGENCY_DATABASE_URL")
_ADMIN = {"x-realify-admin": "test-strong-admin-key-xyz"}


def _login(client, email=None):
    email = email or f"r3-{secrets.token_hex(4)}@x.com"
    core_auth.signup(email, "password1", "R3 Org")
    assert client.post("/api/login", json={"email": email, "password": "password1"}).status_code == 200


def _brand(cur, sandbox=0, currency="USD", threshold=1_000_000):
    cur.execute("INSERT INTO agencies(name) VALUES('R3Ag') RETURNING id"); ag = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,sandbox,tenant_kind) "
                "VALUES('R3Br',now()::text,1,%s,%s) RETURNING id",
                (sandbox, "sandbox" if sandbox else "seller"))
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status,maker_checker_threshold_usd_minor) "
                "VALUES(%s,%s,'active',%s) RETURNING id", (ag, t, threshold))
    return ag, t, cur.fetchone()[0]


def _sku(cur, t):
    cur.execute("INSERT INTO seller_skus(tenant_id,asin,internal_sku,channel,title,category,price,cogs,"
                "units_month,days_of_cover,tacos,buybox_pct) "
                "VALUES(%s,'A1','A1','amazon','T','cat',2000,800,100,8,30.0,70)", (t,))


# ---- pre-item (b): KEK fingerprint guard + brand_keys sweep ----
def test_kek_guard_and_sweep(owner_conn, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", DIRECT)
    cur = owner_conn.cursor()
    _ag, t, _e = _brand(cur)
    tenancy.set_brand_scope(cur, [t])
    fp = crypto.kek_fingerprint()
    keyring.ensure_brand_key(cur, t)                      # wraps + fingerprints under current KEK
    owner_conn.commit()
    cur.execute("SELECT kek_fingerprint FROM brand_keys WHERE tenant_id=%s", (t,))
    assert cur.fetchone()[0] == fp                        # fingerprint recorded
    # simulate a key wrapped under a DIFFERENT KEK -> guard raises a clear error (not a cryptic AEAD fail)
    cur.execute("UPDATE brand_keys SET kek_fingerprint='deadbeefdeadbeef' WHERE tenant_id=%s", (t,))
    with pytest.raises(keyring.KekMismatch):
        keyring.brand_dek(cur, t)
    owner_conn.rollback()
    sweep = keyring.sweep_brand_keys(cur)
    assert sweep["current_kek"] == fp and sweep["total"] >= 1 and "mismatched" in sweep


# ---- item 1: real-brand feeders (no sandbox) ----
def test_feeders_generate_queue_items_for_real_brand(owner_conn, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", DIRECT)
    cur = owner_conn.cursor()
    _ag, t, _e = _brand(cur, sandbox=0)                   # NON-sandbox, seller kind
    tenancy.set_brand_scope(cur, [t])
    _sku(cur, t)
    owner_conn.commit()
    res = scheduler.run_feeders_once(log=lambda *a, **k: None)
    assert res.get("decisions", 0) >= 1                   # feeder produced decisions from ingested SKU data
    owner_conn.rollback()
    tenancy.set_brand_scope(cur, [t])
    assert len(queue.build(cur, [t])) >= 1                # queue populated without any sandbox involvement


# ---- item 2: data sources page + ingest route ----
def test_data_sources_redirects_to_wizard_and_ingest(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    _ag, t, _e = _brand(cur)
    owner_conn.commit()
    # R18.9 — the bespoke data-sources page is retired; the agency loads data through the real onboarding
    # wizard reached by drilling into the brand, so this route now redirects there.
    ds = client.get(f"/agency/data-sources/{t}", headers=H, follow_redirects=False)
    assert ds.status_code == 307 and ds.headers["location"] == f"/agency/brand/{t}", ds.status_code
    r = client.post(f"/api/agency/data-sources/{t}/ingest", headers=H, json={   # ingest API still works
        "headers": ["Campaign", "Clicks", "Impressions", "Cost"],
        "rows": [{"Campaign": "c", "Clicks": "10", "Impressions": "100", "Cost": "5"}]})
    assert r.status_code == 200 and r.json()["report_type"] == "google_ads"
    assert r.json()["source_class"] == "csv" and r.json()["tagged_pct"] == 100.0


# ---- item 3: cosign delivery e2e (email -> deep link -> cosign -> executed) ----
def test_cosign_delivery_e2e(agency_client, owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); monkeypatch.setenv("MAIL_DRIVER", "dev"); dev.clear()
    client, _ = agency_client
    email = f"am3-{secrets.token_hex(4)}@x.com"
    _login(client, email)
    cur = owner_conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,)); uid = cur.fetchone()[0]
    _ag, t, eng = _brand(cur)                             # high threshold -> below-threshold path
    ops.grant_role(cur, uid, eng, t, uid, "account_manager")
    ops.publish_envelope(cur, uid, eng, t, ENVELOPES["Full Operate"], {})   # pricing execute-allowed
    cur.execute("INSERT INTO users(email,created_at,tenant_id) VALUES(%s,now()::text,%s) RETURNING id",
                (f"brand3-{secrets.token_hex(3)}@x.com", t))
    brand_uid = cur.fetchone()[0]
    owner_conn.commit()
    # pricing lens -> cosign_required=True -> cosign_pending -> email the brand a deep link
    r = client.post("/api/agency/queue/propose", json={"tenant_id": t, "lens": "pricing", "kind": "set",
                                                       "signal": "price_up", "impact_usd_minor": 1000})
    assert r.status_code == 200 and r.json()["status"] == "cosign_pending"
    box = dev.inbox()
    link = next(m["body"] for m in box if "co-sign" in m["subject"].lower())
    m = re.search(r"/agency/approve/(\d+)\?token=([A-Za-z0-9_-]+)&uid=(\d+)", link)
    aid, token, luid = m.group(1), m.group(2), m.group(3)
    # brand opens the link + co-signs -> approved -> executed
    d = client.post(f"/api/agency/approvals/{aid}/decide", json={"decision": "approve", "token": token, "uid": luid})
    assert d.status_code == 200 and "device_verified" in d.json()        # otp-skip token consulted
    assert d.json()["status"] in ("approved", "executed")
    owner_conn.rollback()
    cur.execute("SELECT status FROM approvals WHERE id=%s", (aid,))
    assert cur.fetchone()[0] in ("approved", "executed")


# ---- item 4: brand portal ----
def test_brand_portal_rendered_and_revoke(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    _ag, t, eng = _brand(cur, currency="INR")
    tenancy.set_brand_scope(cur, [t])
    approvals.propose(cur, t, eng, None, "ads", "bid", "s", 1000, requires_cosign=True)
    cur.execute("UPDATE approvals SET status='cosign_pending', cosign_expires_at=now()+interval '3 days' "
                "WHERE tenant_id=%s", (t,))
    owner_conn.commit()
    body = client.get(f"/brand/portal/{t}", headers=H).text
    assert "Nothing happens without you." in body
    assert "Revoking is immediate. Your data, history, and connections stay with you." in body
    assert "Transparency log" in body and "Approvals inbox" in body
    # revoke wires ops.revoke_engagement
    r = client.post(f"/api/brand/{t}/revoke", headers=H)
    assert r.status_code == 200 and r.json()["revoked"] >= 1
    owner_conn.rollback()
    cur.execute("SELECT status FROM engagements WHERE id=%s", (eng,))
    assert cur.fetchone()[0] == "terminated"


# ---- item 5: day-0 baseline ----
def test_day0_rendered(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    _ag, t, _e = _brand(cur)
    owner_conn.commit()
    body = client.get(f"/brand/day0/{t}", headers=H).text
    assert "Silence never equals consent" in body and "expire in 5 days" in body
    assert "coming soon" in body                          # WhatsApp inert


# ---- item 6: offboarding + deletion certificate ----
def test_offboarding_export_and_delete_certificate(agency_client, owner_conn):
    client, H = agency_client
    cur = owner_conn.cursor()
    _ag, t, eng = _brand(cur)
    tenancy.set_brand_scope(cur, [t])
    from realify.agency import ledger
    ledger.append(cur, t, None, "engagement.start")       # a ledger entry (creates the brand key)
    owner_conn.commit()
    body = client.get(f"/brand/offboarding/{t}", headers=H).text
    assert "What stays with you" in body and "crypto-shred" in body.lower()
    # export
    exp = client.get(f"/api/brand/{t}/export", headers=H)
    assert exp.status_code == 200 and "ledger" in exp.json()
    # delete requires typed confirm + staff co-sign
    assert client.post(f"/api/brand/{t}/delete-certificate", headers=H, json={"confirm": "no"}).status_code == 400
    assert client.post(f"/api/brand/{t}/delete-certificate", json={"confirm": "DELETE"}).status_code == 403  # no staff key
    r = client.post(f"/api/brand/{t}/delete-certificate", headers=H, json={"confirm": "DELETE"})
    assert r.status_code == 200 and r.json()["crypto_shred"] is True and r.json()["chain_verifies"] is True
    assert r.json()["certificate_id"]
