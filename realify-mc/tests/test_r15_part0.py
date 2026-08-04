"""R15 Part 0 — DRILL-IN UNIFICATION, server-side envelope gate (SQLite/hermetic).

When an agency operator drills into a brand (fleet "Open brand →"), they land in the REAL five-lens
app bounded by the brand's envelope. The security invariant tested here: an in-lens card action can
only EXECUTE when the acting envelope grants 'execute' for that action's PDP lens; a suggest-only /
locked lens is returned as `proposal_required` and the handler never runs. A direct owner (no
envelope) executes normally. (The route-level redirect + /api/scope live in the agency/PG suite.)
"""
import os, tempfile, sys, time

_TMP = tempfile.mkdtemp(prefix="realify_r15p0_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, api, tasks                          # noqa: E402
from run import make_app                                    # noqa: E402
from fastapi.testclient import TestClient                   # noqa: E402

_PDP = ("pricing", "ads", "inventory", "listings", "reporting")


def _provision():
    for suffix in ("", "-wal", "-shm"):
        try: os.remove(os.environ["REALIFY_DB"] + suffix)
        except OSError: pass
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup("r15p0@x.com", "password1")
    c.post("/api/login", json={"email": "r15p0@x.com", "password": "password1"})
    c.post("/api/account/type", json={"account_type": "tester"})
    c.post("/api/onboard", json={"mode": "synthetic", "source": "sample", "country": "IN"})
    for _ in range(40):
        if c.get("/api/onboard/status").json().get("pct", 0) >= 100:
            break
        time.sleep(0.5)
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email='r15p0@x.com'").fetchone()["tenant_id"]
    con.close()
    return c, tid


def test_locked_lens_cannot_execute_returns_proposal_required():
    _c, tid = _provision()
    feed = api.get_feed(tid); assert feed, "no cards to act on"
    cid = feed[0]["id"]
    locked = {l: "read" for l in _PDP}                        # every lens read-only under this envelope
    r = tasks.do_action(tid, cid, None, actor_caps=locked)
    assert r.get("ok") is False and r.get("proposal_required") is True
    assert r.get("lens") in _PDP                              # the action was mapped to a governed lens
    # the card was NOT acted on (handler never ran) — still in the live feed
    assert any(card["id"] == cid for card in api.get_feed(tid)), "locked action leaked an execution"


def test_execute_capable_envelope_runs_the_handler():
    _c, tid = _provision()
    feed = api.get_feed(tid); assert feed
    cid = feed[0]["id"]
    openc = {l: "execute" for l in _PDP}                      # full-operate envelope
    r = tasks.do_action(tid, cid, None, actor_caps=openc)
    assert not (isinstance(r, dict) and r.get("proposal_required")), "execute envelope was wrongly blocked"


def test_no_envelope_direct_owner_executes():
    _c, tid = _provision()
    feed = api.get_feed(tid); assert feed
    r = tasks.do_action(tid, feed[0]["id"], None, actor_caps=None)   # direct owner: full powers
    assert not (isinstance(r, dict) and r.get("proposal_required"))


if __name__ == "__main__":
    test_locked_lens_cannot_execute_returns_proposal_required()
    test_execute_capable_envelope_runs_the_handler()
    test_no_envelope_direct_owner_executes()
    print("R15 Part 0 gate tests passed")
