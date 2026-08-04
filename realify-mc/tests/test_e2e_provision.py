"""End-to-end proof that the 1b repository sweep is behavior-preserving through the REAL
provisioning pipeline — not just isolated repo unit tests.

Provisions a synthetic tester tenant SYNCHRONOUSLY (own-data + channel layer + multichannel
+ history backfill + pipeline + market enrichment), then asserts that every table touched by
the sweep is actually populated via the migrated call sites in channels.py / multichannel.py /
seller.py / history.py / materialize.py / detect.py / collectors / api.py. Finally drives a
login + a card action through TestClient to exercise the usage_events + actions_log paths.

The conditional action tables (watchlist / sourcing_list / saved_briefs) are covered by
test_sweep_repos::test_action_repo, which exercises those repo methods directly.

Hermetic + deterministic: throwaway DB + fixture mode forced before importing realify.
Runnable standalone (python3 tests/test_e2e_provision.py) or via pytest.
"""
import os, tempfile, sys

_TMP = tempfile.mkdtemp(prefix="realify_e2e_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, auth, scheduler                      # noqa: E402
from realify.ingest.synthetic import SyntheticSource         # noqa: E402

# tables guaranteed populated by a synthetic provision (own-data + market enrichment)
_PROVISION_TABLES = [
    "seller_skus", "seller_orders", "products", "channel_listings", "traffic", "inventory",
    "returns", "storage_fees", "settlements", "channels", "channel_economics", "metric_history",
    "runs", "cards", "keepa_snapshots", "competitor_offers", "tierc_signals",
]


def _count(con, table, tid):
    return con.execute(f"SELECT COUNT(*) c FROM {table} WHERE tenant_id=?", (tid,)).fetchone()["c"]


def test_e2e_full_provision_populates_every_swept_table():
    for suffix in ("", "-wal", "-shm"):
        try: os.remove(os.environ["REALIFY_DB"] + suffix)
        except OSError: pass
    db.init_db()

    uid, tid = auth.signup("e2e@x.com", "password1")
    con = db.connect()
    db.set_account_type(con, tid, "tester")
    db.set_setting(con, tid, "country", "IN")
    con.commit(); con.close()

    # SYNCHRONOUS full provision: own-data + channel layer + multichannel + history + pipeline + market
    scheduler.provision_tenant(tid, SyntheticSource(seed_skus=None), log=lambda *a, **k: None)

    con = db.connect()
    try:
        missing = [t for t in _PROVISION_TABLES if _count(con, t, tid) == 0]
        assert not missing, f"provisioning left these swept tables empty: {missing}"
        # spot-check the high-volume derived tables really fanned out, not just 1 sentinel row
        assert _count(con, "seller_orders", tid) > 100
        assert _count(con, "settlements", tid) > 100
        assert _count(con, "metric_history", tid) > 100
        # pull_log written by the market enrichment pass (PullLogRepository.record)
        assert con.execute("SELECT COUNT(*) c FROM pull_log WHERE tenant_id=?", (tid,)).fetchone()["c"] > 0
    finally:
        con.close()

    # --- exercise usage_events (login) + actions_log (card action) via the real endpoints ---
    from run import make_app
    from fastapi.testclient import TestClient
    c = TestClient(make_app())
    assert c.post("/api/login", json={"email": "e2e@x.com", "password": "password1"}).json()["ok"]

    feed = c.get("/api/feed").json()
    assert isinstance(feed, list) and feed, "expected a populated feed after provision"
    cid = feed[0]["id"]
    action = (feed[0].get("actions") or [None])[0] or "reprice"
    assert c.post(f"/api/card/{cid}/action", json={"action": action}).status_code == 200

    con = db.connect()
    try:
        assert _count(con, "usage_events", tid) > 0, "login/action did not record usage_events"
        assert _count(con, "actions_log", tid) > 0, "card action did not write actions_log"
    finally:
        con.close()
    print("PASS test_e2e_full_provision_populates_every_swept_table")


if __name__ == "__main__":
    test_e2e_full_provision_populates_every_swept_table()
    print("\nE2E provisioning sweep test passed.")
