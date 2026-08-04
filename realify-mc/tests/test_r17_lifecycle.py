"""R17 Part A — the deletion lifecycle core (SQLite/hermetic): state machine, the billing gate, catalog
capture, and the one destructive Execute routine. Endpoint/queue behavior is covered in the agency suite.
"""
import os, tempfile, sys, time

_TMP = tempfile.mkdtemp(prefix="realify_r17_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, lifecycle                       # noqa: E402
from run import make_app                                # noqa: E402
from fastapi.testclient import TestClient               # noqa: E402


def _provision(email):
    for sfx in ("", "-wal", "-shm"):
        try: os.remove(os.environ["REALIFY_DB"] + sfx)
        except OSError: pass
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup(email, "password1")
    c.post("/api/login", json={"email": email, "password": "password1"})
    c.post("/api/account/type", json={"account_type": "tester"})
    c.post("/api/onboard", json={"mode": "synthetic", "source": "sample", "country": "IN"})
    for _ in range(40):
        if c.get("/api/onboard/status").json().get("pct", 0) >= 100:
            break
        time.sleep(0.5)
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()["tenant_id"]
    return con, tid


def test_transition_graph():
    assert lifecycle.can_transition("requested", "hold")
    assert lifecycle.can_transition("hold", "ready")
    assert lifecycle.can_transition("ready", "wiped")
    assert lifecycle.can_transition("requested", "canceled")
    assert not lifecycle.can_transition("hold", "wiped")     # must pass through ready
    assert not lifecycle.can_transition("wiped", "ready")    # terminal
    assert not lifecycle.can_transition("canceled", "ready")


def test_request_idempotent_and_status_writes():
    con, tid = _provision("r17a@x.com")
    a = lifecycle.create_request(con, "brand", tid, "Brand A", "ops", "customer", status="hold")
    b = lifecycle.create_request(con, "brand", tid, "Brand A", "ops", "customer")
    assert a == b                                            # open request reused, no duplicate
    lifecycle.set_status(con, a, "ready")
    assert lifecycle.get_request(con, a)["status"] == "ready"
    import pytest
    with pytest.raises(lifecycle.TransitionError):
        lifecycle.set_status(con, a, "requested")            # illegal (no backwards)
    con.close()


def test_billing_gate_customer_vs_tester():
    con, tid = _provision("r17b@x.com")
    # tester ⇒ trivially settled regardless of any subscription column
    assert lifecycle.account_type_of(con, tid) == "tester"
    assert lifecycle.billing_settled(con, "brand", tid) is True
    # flip to a real customer with a live subscription ⇒ NOT settled
    con.execute("UPDATE tenants SET account_type='customer', tenant_kind='seller', subscription_status='active' WHERE id=?", (tid,))
    con.commit()
    assert lifecycle.account_type_of(con, tid) == "customer"
    assert lifecycle.billing_settled(con, "brand", tid) is False
    con.execute("UPDATE tenants SET subscription_status='canceled' WHERE id=?", (tid,)); con.commit()
    assert lifecycle.billing_settled(con, "brand", tid) is True   # canceled ⇒ settled
    con.close()


def test_capture_then_execute_wipes_and_is_idempotent():
    con, tid = _provision("r17c@x.com")
    assert lifecycle.catalog_is_capturable(con, tid)         # the synthetic world has a real catalog
    assert lifecycle.capture_catalog(con, tid) is True
    seeds = lifecycle.list_captured_seeds(con)
    assert seeds and seeds[0]["brand_name"] and seeds[0]["sku_count"] >= 5   # R17 dec.2 — real name kept
    got = lifecycle.captured_seed_catalog(con, seeds[0]["id"])
    assert got["catalog"] and all(k in got["catalog"][0] for k in ("asin", "title", "category", "cogs", "price"))
    # Execute = hard wipe
    n_before = con.execute("SELECT count(*) AS n FROM seller_skus WHERE tenant_id=?", (tid,)).fetchone()["n"]
    assert n_before > 0
    r = lifecycle.execute_brand(con, tid, capture_seed=False, deleted_by="test")
    assert r["ok"]
    assert db.get_tenant(con, tid) is None                   # tenant row gone
    assert con.execute("SELECT count(*) AS n FROM seller_skus WHERE tenant_id=?", (tid,)).fetchone()["n"] == 0
    assert con.execute("SELECT count(*) AS n FROM deleted_account_audit WHERE deleted_tenant_id=?", (tid,)).fetchone()["n"] == 1
    assert lifecycle.execute_brand(con, tid, deleted_by="test").get("already")   # idempotent re-run
    con.close()


if __name__ == "__main__":
    test_transition_graph()
    test_request_idempotent_and_status_writes()
    test_billing_gate_customer_vs_tester()
    test_capture_then_execute_wipes_and_is_idempotent()
    print("R17 Part A lifecycle tests passed")
