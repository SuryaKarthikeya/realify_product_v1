"""Merged billing funnel (rolled in from the former /beta app): marketing shell at the app root, the
subscription paywall gate on `/`, the /superlogin back door that synthesizes paid access, public-signup
validation (before any Stripe call), and the signed-webhook state machine on the TENANT. Live Stripe
Checkout/portal (network) is covered by manual verification, not here.

DB isolation comes from conftest's autouse `_isolated_db` (fresh alembic DB per test — migration 0011
gives tenants the subscription columns). `_stripe_env` pins dummy Stripe config so enabled()/webhook are
deterministic regardless of the machine's real .env."""
import hashlib
import hmac
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import auth, billing, config, db          # noqa: E402
from run import make_app                                # noqa: E402
from fastapi.testclient import TestClient               # noqa: E402

WH = "whsec_test_dummy_secret"


@pytest.fixture(autouse=True)
def _stripe_env(monkeypatch, _isolated_db):
    monkeypatch.setattr(config, "STRIPE_SECRET_KEY", "sk_test_dummy", raising=False)
    monkeypatch.setattr(config, "STRIPE_PRICE_ID", "price_dummy", raising=False)
    monkeypatch.setattr(config, "STRIPE_WEBHOOK_SECRET", WH, raising=False)


def _client():
    return TestClient(make_app())


def _iso(days):
    import datetime as dt
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)).isoformat()


def _signed(c, evt_type, obj):
    payload = json.dumps({"id": "evt", "object": "event", "api_version": "2025-06-30.basil",
                          "created": int(time.time()), "type": evt_type, "data": {"object": obj}})
    ts = int(time.time())
    sig = hmac.new(WH.encode(), f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
    return c.post("/api/webhooks/stripe", content=payload.encode(),
                  headers={"stripe-signature": f"t={ts},v1={sig}"})


def test_public_pages_render_at_root():
    c = _client()
    assert "coordinated capabilities" in c.get("/").text          # logged-out root -> marketing landing
    assert "Six coordinated capabilities" in c.get("/platform").text
    assert "$20" in c.get("/pricing").text and "30-day free trial" in c.get("/pricing").text
    assert "Duke University" in c.get("/about").text
    assert "/api/login" in c.get("/signin").text                  # sign-in posts to the main login
    assert "/api/billing/signup" in c.get("/signup").text         # signup posts to the Stripe funnel
    assert c.get("/login", follow_redirects=False).headers["location"] == "/signin"
    r = c.get("/superlogin")                                      # gate is public but non-crawlable now
    assert r.status_code == 200 and "noindex" in r.headers.get("x-robots-tag", "").lower()


def test_home_gate_blocks_unsubscribed_and_allows_paid():
    c = _client()
    # a plain account (no subscription) — created via the function, logged in via the existing endpoint
    uid, tid = auth.signup("gate@x.com", "hunter2pw", "Gate")
    assert billing.get_tenant(tid)["subscription_status"] is None
    c.post("/api/login", json={"email": "gate@x.com", "password": "hunter2pw"})
    assert c.get("/", follow_redirects=False).headers["location"] == "/pricing"   # paywall
    # grant paid access -> root now serves the onboarding surface (not provisioned yet)
    billing.synthesize_paid(tid)
    r = c.get("/", follow_redirects=False)
    assert r.status_code == 200
    # once provisioned, root serves the real app shell
    con = db.connect(); db.set_tenant_provisioned(con, tid, "demo"); con.close()
    assert "frontend" in c.get("/").text.lower() or c.get("/").status_code == 200


def test_backdoor_signup_gated_and_still_synthesizes_paid(monkeypatch):
    """P0.9 tourniquet: /api/signup is the account-minting endpoint behind /superlogin. It now requires
    a valid ADMIN_KEY_HASH admin key AND a @realify.ai staff email; with both, it still mints paid."""
    from realify.routers import deps
    KEY = "sl-strong-key-1234"
    monkeypatch.setenv("ADMIN_KEY_HASH", deps.admin_key_hash(KEY))
    c = _client()

    # (1) no admin key -> the endpoint does not exist
    assert c.post("/api/signup", json={"email": "boss@realify.ai", "password": "hunter2pw"}).status_code == 404
    # (2) valid key but non-staff email -> 403 (allowlist)
    r = c.post("/api/signup", json={"email": "boss@x.com", "password": "hunter2pw"},
               headers={"x-realify-admin": KEY})
    assert r.status_code == 403
    # (3) valid key + @realify.ai email -> mints a paid account (no Stripe), as before
    r = c.post("/api/signup", json={"email": "boss@realify.ai", "password": "hunter2pw", "account": "HQ"},
               headers={"x-realify-admin": KEY})
    assert r.status_code == 200 and r.json()["ok"]
    con = db.connect(); tid = db.get_user_by_email(con, "boss@realify.ai")["tenant_id"]; con.close()
    assert billing.get_tenant(tid)["subscription_status"] == "active"     # paid, no Stripe
    assert c.get("/", follow_redirects=False).status_code == 200          # not gated to /pricing


def test_superlogin_page_gate(monkeypatch):
    """The /superlogin gate is served WITHOUT an admin key in the URL (no more double key entry), but is
    non-crawlable. The real control is unchanged: POST /api/superlogin/authenticate still requires the
    admin key + staff email + OTP, and /api/signup (account minting) still 404s without the key."""
    from realify.routers import deps
    KEY = "sl-strong-key-1234"
    monkeypatch.setenv("ADMIN_KEY_HASH", deps.admin_key_hash(KEY))
    c = _client()
    r = c.get("/superlogin")                                              # no key in URL -> still served
    assert r.status_code == 200
    assert "noindex" in r.headers.get("x-robots-tag", "").lower()         # non-crawlable
    assert 'name=robots content="noindex' in r.text                       # + meta robots
    assert "Admin key" in r.text and "One-time code" in r.text            # the form still demands key + OTP
    # the account-minting endpoint behind the gate remains key-gated (unchanged)
    assert c.post("/api/signup", json={"email": "boss@realify.ai", "password": "hunter2pw"}).status_code == 404


def test_public_signup_validation_before_stripe():
    c = _client()
    # password mismatch -> 400 (before enabled()/Stripe)
    assert c.post("/api/billing/signup", json={"name": "A", "email": "a@x.com",
                  "password": "aaaaaa", "confirmPassword": "bbbbbb"}).status_code == 400
    # duplicate email -> 409 (auth.signup raises before any Stripe call)
    auth.signup("dupe@x.com", "hunter2pw", "Dupe")
    assert c.post("/api/billing/signup", json={"name": "A", "email": "dupe@x.com",
                  "password": "hunter2pw", "confirmPassword": "hunter2pw"}).status_code == 409


def test_subscription_status_days_remaining():
    c = _client()
    uid, tid = auth.signup("trial@x.com", "hunter2pw", "Trial")
    c.post("/api/login", json={"email": "trial@x.com", "password": "hunter2pw"})
    billing.set_subscription(tid, subscription_status="trialing", trial_ends_at=_iso(10), current_period_end=_iso(10))
    j = c.get("/api/subscription/status").json()
    assert j["status"] == "trialing" and j["days_remaining"] == 10 and j["has_access"] is True


def test_webhook_state_machine_on_tenant():
    c = _client()
    uid, tid = auth.signup("wh@x.com", "hunter2pw", "WH")
    billing.set_stripe_customer(tid, "cus_main")
    # bad signature -> 400
    assert c.post("/api/webhooks/stripe", content=b"{}",
                  headers={"stripe-signature": "t=1,v1=bad"}).status_code == 400
    # payment_failed -> past_due
    assert _signed(c, "invoice.payment_failed", {"object": "invoice", "customer": "cus_main"}).status_code == 200
    assert billing.get_tenant(tid)["subscription_status"] == "past_due"
    # subscription.updated -> trialing (+ trial_ends_at)
    _signed(c, "customer.subscription.updated", {"id": "sub_m", "object": "subscription", "customer": "cus_main",
            "status": "trialing", "trial_end": int(time.time()) + 30 * 86400,
            "current_period_end": int(time.time()) + 30 * 86400})
    t = billing.get_tenant(tid)
    assert t["subscription_status"] == "trialing" and t["trial_ends_at"]
    # deleted -> canceled; idempotent
    _signed(c, "customer.subscription.deleted", {"id": "sub_m", "object": "subscription", "customer": "cus_main"})
    _signed(c, "customer.subscription.deleted", {"id": "sub_m", "object": "subscription", "customer": "cus_main"})
    assert billing.get_tenant(tid)["subscription_status"] == "canceled"
    # canceled tenant hitting /billing -> the BillingGate
    c.post("/api/login", json={"email": "wh@x.com", "password": "hunter2pw"})
    assert "Your access has ended" in c.get("/billing").text
    # unhandled event -> still 200
    assert _signed(c, "customer.created", {"object": "customer"}).status_code == 200


def test_grandfather_backfill_semantics():
    """The 0011 back-fill grants access to any tenant that predates the paywall (NULL status)."""
    con = db.connect()
    tid = db.create_tenant(con, "legacy org")
    con.execute("UPDATE tenants SET subscription_status='active' WHERE subscription_status IS NULL")
    con.commit(); con.close()
    assert billing.has_access(billing.get_tenant(tid)) is True


if __name__ == "__main__":
    import tempfile
    os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_bill_"), "t.db")
    os.environ.setdefault("MODE", "fixture")
    db.init_db()
    print("run under pytest (needs conftest fixtures)")
