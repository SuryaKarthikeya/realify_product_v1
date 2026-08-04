"""R15 Part K — self-service full-account delete must tear down the WHOLE seller: user row, members,
and ALL seller billing state (which lives on the tenants row: stripe_customer_id / *_subscription_id /
subscription_status) AND the Stripe presence (cancel the subscription + delete the customer, TEST mode),
without ever leaving an orphaned billing row or a dangling Stripe customer. Idempotent.

Stripe is stubbed (no network): we swap billing.stripe for a recorder and pin dummy STRIPE_* config so
enabled() is True and cancel/delete are actually attempted, then assert on what the stub recorded."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import auth, billing, config, db          # noqa: E402
from run import make_app                                # noqa: E402
from fastapi.testclient import TestClient              # noqa: E402


class _FakeStripe:
    """Records cancel/delete calls instead of hitting the network."""
    def __init__(self):
        self.canceled, self.deleted = [], []
        outer = self

        class _Subscription:
            @staticmethod
            def cancel(sub_id):
                outer.canceled.append(sub_id)
                return {"id": sub_id, "status": "canceled"}

        class _Customer:
            @staticmethod
            def delete(cust_id):
                outer.deleted.append(cust_id)
                return {"id": cust_id, "deleted": True}

        self.Subscription = _Subscription
        self.Customer = _Customer


@pytest.fixture
def fake_stripe(monkeypatch, _isolated_db):
    fs = _FakeStripe()
    monkeypatch.setattr(billing, "stripe", fs)
    monkeypatch.setattr(config, "STRIPE_SECRET_KEY", "sk_test_dummy", raising=False)
    monkeypatch.setattr(config, "STRIPE_PRICE_ID", "price_dummy", raising=False)
    return fs


def _client():
    return TestClient(make_app())


def _login(c, email, pw):
    r = c.post("/api/login", json={"email": email, "password": pw})
    assert r.status_code == 200 and r.json()["ok"]


def test_customer_with_balance_queues_then_closeout_wipes(fake_stripe):
    """R17 dec.6 — a customer with an OPEN balance self-deletes into the close-out queue (not an immediate
    wipe); the ops close-out (settle → execute) then does the hard wipe + Stripe teardown."""
    from realify import lifecycle
    c = _client()
    uid, tid = auth.signup("owner@x.com", "hunter2pw", "SoloCo")
    billing.set_stripe_customer(tid, "cus_solo")
    billing.set_subscription(tid, stripe_subscription_id="sub_solo", subscription_status="active")
    _login(c, "owner@x.com", "hunter2pw")
    r = c.post("/api/account/delete", json={"password": "hunter2pw", "confirm": "delete"})
    assert r.status_code == 200 and r.json()["action"] == "pending_closeout"   # queued, NOT wiped
    with db.connect() as con:
        assert db.get_tenant(con, tid) is not None                             # still live pending close-out
        req = lifecycle.open_request_for(con, "brand", tid)
        assert req and req["status"] == "hold"
        lifecycle.settle_billing(con, req)                                      # Mark paid up
        lifecycle.execute_brand(con, tid, capture_seed=False, deleted_by="ops")  # Execute (hard wipe)
        assert db.get_tenant(con, tid) is None
        assert db.get_user_by_email(con, "owner@x.com") is None
        assert con.execute("SELECT COUNT(*) c FROM tenants WHERE id=?", (tid,)).fetchone()["c"] == 0
    # Stripe: subscription canceled AND customer deleted (no dangling customer / live billing)
    assert "sub_solo" in fake_stripe.canceled and "cus_solo" in fake_stripe.deleted
    uid2, tid2 = auth.signup("owner@x.com", "hunter2pw", "Fresh")               # email freed
    assert tid2 != tid


def test_self_delete_tester_wipes_immediately(fake_stripe):
    """R17 dec.6 — a tester (no billing) wipes right away, no queue detour."""
    c = _client()
    uid, tid = auth.signup("t@x.com", "hunter2pw", "TesterCo")
    with db.connect() as con:
        con.execute("UPDATE tenants SET account_type='tester' WHERE id=?", (tid,)); con.commit()
    _login(c, "t@x.com", "hunter2pw")
    r = c.post("/api/account/delete", json={"password": "hunter2pw", "confirm": "delete"})
    assert r.status_code == 200 and r.json()["action"] == "deleted_org"
    with db.connect() as con:
        assert db.get_tenant(con, tid) is None


def test_self_delete_no_stripe_when_no_customer(fake_stripe):
    """A tenant that never paid (no stripe_customer_id) deletes cleanly with zero Stripe calls."""
    c = _client()
    uid, tid = auth.signup("free@x.com", "hunter2pw", "FreeCo")
    _login(c, "free@x.com", "hunter2pw")
    r = c.post("/api/account/delete", json={"password": "hunter2pw", "confirm": "delete"})
    assert r.status_code == 200 and r.json()["ok"]
    assert fake_stripe.canceled == [] and fake_stripe.deleted == []
    with db.connect() as con:
        assert db.get_tenant(con, tid) is None


def test_self_delete_is_idempotent(fake_stripe):
    """Re-running the teardown on an already-deleted tenant is a clean no-op (no exception)."""
    c = _client()
    uid, tid = auth.signup("again@x.com", "hunter2pw", "AgainCo")
    billing.set_stripe_customer(tid, "cus_again")
    billing.set_subscription(tid, stripe_subscription_id="sub_again", subscription_status="active")

    # snapshot the tenant, delete, then re-invoke the Stripe teardown with the STALE snapshot:
    # cancel/delete are best-effort + guarded, so a second run must not raise.
    with db.connect() as con:
        snap = db.get_tenant(con, tid)
        db.delete_tenant(con, tid)
    assert db.get_tenant(db.connect(), tid) is None

    r1 = billing.cancel_and_delete_customer(snap)
    r2 = billing.cancel_and_delete_customer(snap)     # re-run: still fine
    assert r1 == {"canceled": "sub_again", "deleted": "cus_again"}
    assert r2 == {"canceled": "sub_again", "deleted": "cus_again"}
    # a None tenant (fully gone, nothing to snapshot) is also a benign no-op
    assert billing.cancel_and_delete_customer(None) == {"canceled": None, "deleted": None}


def test_teardown_best_effort_never_raises(monkeypatch, _isolated_db):
    """If Stripe is unreachable, the teardown swallows the error and the local wipe still succeeds."""
    class _Boom:
        class Subscription:
            @staticmethod
            def cancel(_):
                raise RuntimeError("stripe down")

        class Customer:
            @staticmethod
            def delete(_):
                raise RuntimeError("stripe down")

    monkeypatch.setattr(billing, "stripe", _Boom)
    monkeypatch.setattr(config, "STRIPE_SECRET_KEY", "sk_test_dummy", raising=False)
    monkeypatch.setattr(config, "STRIPE_PRICE_ID", "price_dummy", raising=False)

    from realify import lifecycle
    c = _client()
    uid, tid = auth.signup("boom@x.com", "hunter2pw", "BoomCo")
    billing.set_stripe_customer(tid, "cus_boom")
    billing.set_subscription(tid, stripe_subscription_id="sub_boom", subscription_status="active")
    _login(c, "boom@x.com", "hunter2pw")
    r = c.post("/api/account/delete", json={"password": "hunter2pw", "confirm": "delete"})
    assert r.status_code == 200 and r.json()["action"] == "pending_closeout"   # open balance ⇒ queued
    # ops Execute with a booming Stripe: the teardown error must NOT block the local wipe
    with db.connect() as con:
        lifecycle.execute_brand(con, tid, capture_seed=False, deleted_by="ops")
        assert db.get_tenant(con, tid) is None


def test_wrong_password_or_confirm_leaves_everything(fake_stripe):
    """Guard intact: a bad password or missing 'delete' confirm makes NO local or Stripe changes."""
    c = _client()
    uid, tid = auth.signup("keep@x.com", "hunter2pw", "KeepCo")
    billing.set_stripe_customer(tid, "cus_keep")
    _login(c, "keep@x.com", "hunter2pw")
    # wrong password -> 403
    assert c.post("/api/account/delete", json={"password": "nope", "confirm": "delete"}).status_code == 403
    # right password, missing confirm -> 400
    assert c.post("/api/account/delete", json={"password": "hunter2pw"}).status_code == 400
    with db.connect() as con:
        assert db.get_tenant(con, tid) is not None
    assert fake_stripe.canceled == [] and fake_stripe.deleted == []
