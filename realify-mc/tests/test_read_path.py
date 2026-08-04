"""Integration test for the card/feed READ path (workstream 1b).

Provisions a real tester tenant, then exercises the read layer (api.get_feed,
briefing_summary, get_categories, explain_card) which now goes through CardRepository.
Confirms the migration is behavior-preserving end to end. Runnable standalone or via pytest.
"""
import os, tempfile, sys

_TMP = tempfile.mkdtemp(prefix="realify_read_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
# Hermetic + deterministic: force fixture mode (no live external calls / token burn) before import.
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, api                                 # noqa: E402
from run import make_app                                    # noqa: E402
from fastapi.testclient import TestClient                   # noqa: E402


def _provision_tester():
    for suffix in ("", "-wal", "-shm"):
        try: os.remove(os.environ["REALIFY_DB"] + suffix)
        except OSError: pass
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup("reader@x.com", "password1")           # /api/signup back door gated (P0.9)
    c.post("/api/login", json={"email": "reader@x.com", "password": "password1"})
    c.post("/api/account/type", json={"account_type": "tester"})
    c.post("/api/onboard", json={"mode": "synthetic", "source": "sample", "country": "IN"})
    import time
    for _ in range(40):
        if c.get("/api/onboard/status").json().get("pct", 0) >= 100:
            break
        time.sleep(0.5)
    # resolve tenant_id
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email='reader@x.com'").fetchone()["tenant_id"]
    con.close()
    return c, tid


def test_read_path_through_card_repository():
    c, tid = _provision_tester()

    # get_feed -> CardRepository.feed + presentation
    feed = api.get_feed(tid)
    assert isinstance(feed, list) and len(feed) > 0, "expected a populated feed"
    # rows are sorted (rank_score, severity, ...) and decorated with surface/group
    assert "surface" in feed[0] and "group" in feed[0]

    # briefing_summary -> CardRepository counts; total must equal non-dismissed feed size
    summ = api.briefing_summary(tid)
    assert summ["total"] == len(feed), f"summary total {summ['total']} != feed {len(feed)}"
    assert summ["new"] >= 0 and summ["action"] >= 0

    # category filter narrows the feed (pick a category present in the feed)
    cats = api.get_categories(tid)
    assert isinstance(cats, list)
    some_cat = feed[0].get("category")
    if some_cat:
        narrowed = api.get_feed(tid, category=some_cat)
        assert all(r["category"] == some_cat for r in narrowed)

    # explain_card -> CardRepository.get + research_payload; returns a trace, not an error
    first_id = feed[0]["id"]
    trace = api.explain_card(tid, first_id)
    assert "error" not in trace, f"explain_card returned error: {trace}"

    # missing card id -> graceful error (CardRepository.get returns None)
    assert api.explain_card(tid, 99999999).get("error") == "card not found"


if __name__ == "__main__":
    test_read_path_through_card_repository()
    print("  PASS  test_read_path_through_card_repository")
    print("\n1/1 tests passed")
