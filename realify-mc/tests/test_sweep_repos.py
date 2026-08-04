"""Tests for the 1b-2 repository sweep — orders / fact tables / channel layer / market /
actions / analytics. Hermetic: a throwaway DB is set before importing realify, and a tenant
is created so tenant_id FKs are satisfied.

Runnable two ways:
  * standalone:  python3 tests/test_sweep_repos.py
  * pytest:      pytest tests/test_sweep_repos.py
"""
import os, tempfile, sys

_TMP = tempfile.mkdtemp(prefix="realify_sweep_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
os.environ.setdefault("MODE", "fixture")
for s in ("KEEPA", "NEWS", "RECALLS", "TRENDS"):
    os.environ.setdefault(f"MODE_{s}", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                                                      # noqa: E402
from realify.repositories import (                                          # noqa: E402
    TenantRepository, OrderRepository, TrafficRepository, InventoryRepository,
    SettlementRepository, ProductRepository, ChannelListingRepository,
    ReturnsRepository, StorageFeeRepository, ChannelRepository,
    ChannelEconomicsRepository, MarketRepository, ActionRepository,
    AnalyticsRepository, SystemRepository,
)


def _fresh():
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(os.environ["REALIFY_DB"] + suffix)
        except OSError:
            pass
    db.init_db()
    con = db.connect()
    tid = TenantRepository(con).create("sweeptest")
    con.commit()
    return con, tid


def test_order_repo():
    con, tid = _fresh()
    o = OrderRepository(con)
    # synthetic batch (15-col tuples): one short-paid, one review-eligible
    batch = [
        (tid, "ORD-1", "ASIN1", "2026-06-01", 2, 1000, 100, 50, 900, 800, "2026-06-05", "2026-06-03", 0, 1, "settled"),
        (tid, "ORD-2", "ASIN2", "2026-06-02", 1, 500, 50, 25, 450, 450, "2026-06-06", "2026-06-04", 0, 0, "settled"),
    ]
    o.insert_many_synthetic(batch); con.commit()
    assert o.count(tid) == 2
    assert o.count_short_paid(tid) == 1          # ORD-1: 800 < 900*0.99
    assert o.count_review_eligible(tid) == 1     # ORD-1
    assert len(o.window_rows(tid, "2026-01-01")) == 2
    assert len(o.settled(tid)) == 2
    assert len(o.short_paid_detail(tid)) == 1
    assert len(o.short_paid_detail(tid, "ASIN1")) == 1
    assert len(o.short_paid_detail(tid, "ASINX")) == 0
    assert len(o.review_eligible_detail(tid)) == 1
    o.link_channel(tid, "ASIN1", "SKU-ASIN1", "amazon"); con.commit()
    roll = o.channel_rollup(tid, "SKU-ASIN1")
    assert roll[0]["channel"] == "amazon" and roll[0]["units"] == 2
    o.delete_by_channel(tid, "amazon"); con.commit()
    assert o.count(tid) == 0          # schema defaults channel='amazon' for both rows
    o.insert_imported(tid, "ORD-3", "ASIN3", "2026-06-03", 1, 600, "flipkart", "SKU-3"); con.commit()
    assert o.count(tid) == 1
    o.delete_all(tid); con.commit()
    assert o.count(tid) == 0
    print("PASS test_order_repo")


def test_fact_repos():
    con, tid = _fresh()
    t = TrafficRepository(con); inv = InventoryRepository(con); se = SettlementRepository(con)
    t.insert(tid, "amazon", "SKU-A", "2026-06-01", 100, 150, 8.0, 90.0)
    t.insert(tid, "amazon", "SKU-B", "2026-06-01", 50, 70, None, 80.0); con.commit()
    assert t.count(tid) == 2
    assert t.count_with_conversion(tid) == 1
    assert t.internal_skus_ordered(tid) == ["SKU-A", "SKU-B"]
    t.set_conversion(tid, "SKU-B", 5.0); con.commit()
    assert t.count_with_conversion(tid) == 2
    inv.insert(tid, "amazon", "SKU-A", "2026-06-01", 100, 10, 5, 1, 30.0)
    inv.insert(tid, "amazon", "SKU-B", "2026-06-01", 8, 0, 0, 0, 7.0); con.commit()
    assert inv.count(tid) == 2
    assert inv.count_low_cover(tid) == 1
    assert inv.sum_by_sku(tid, "SKU-A")["oh"] == 100
    se.insert(tid, "amazon", "SKU-A", "ORD-1", "2026-06-05", 1000, 150, 800, 0)
    se.insert_many([(tid, "amazon", "SKU-B", "ORD-2", "2026-06-06", 500, 75, 400, 0)]); con.commit()
    assert se.count(tid) == 2
    ws = se.window_summary(tid, "2026-01-01")
    assert ws["payout"] == 1200 and ws["short"] == (1000 - 150 - 800) + (500 - 75 - 400)
    assert se.sum_fees_by_sku(tid, "SKU-A") == 150
    print("PASS test_fact_repos")


def test_channel_repos():
    con, tid = _fresh()
    p = ProductRepository(con); cl = ChannelListingRepository(con)
    r = ReturnsRepository(con); sf = StorageFeeRepository(con)
    ch = ChannelRepository(con); ce = ChannelEconomicsRepository(con)
    p.upsert(tid, "SKU-A", "Widget", "Car Accessories", "Autofy", 300, db.now_iso()); con.commit()
    assert p.count(tid) == 1 and p.all(tid)[0]["title"] == "Widget"
    cl.upsert(tid, "SKU-A", "amazon", "ASIN1", "ASIN1", "active", "confirmed", 1000, "http://x"); con.commit()
    assert cl.count(tid) == 1 and cl.by_sku(tid, "SKU-A")[0]["channel"] == "amazon"
    r.insert(tid, "amazon", "SKU-A", "2026-06-01", "ORD-1", 1, "defective", 950.0); con.commit()
    assert r.count(tid) == 1
    sf.insert(tid, "amazon", "SKU-A", "2026-06", 50.0, 0.0, 0.3, 30); con.commit()
    assert sf.count(tid) == 1
    ch.upsert(tid, "amazon", "Amazon", 1, 0.15, "FBA", "INR"); con.commit()
    assert ch.active(tid)[0]["channel"] == "amazon"
    ce.insert_present(tid, "SKU-A", "ASIN1", "Widget", "Car Accessories", "amazon", 1000, 50, 0.15,
                      150, 30, 300, 520, 52.0, 50000, 100, 60.0, "FBA")
    ce.insert_absent(tid, "SKU-A", "ASIN1", "Widget", "Car Accessories", "flipkart", 0.12, 300, "self"); con.commit()
    assert ce.count_present(tid, "amazon") == 1 and ce.count_present(tid, "flipkart") == 0
    assert len(ce.all(tid)) == 2
    # conversion_by_asin JOIN (traffic + channel_listings)
    TrafficRepository(con).insert(tid, "amazon", "SKU-A", "2026-06-01", 100, 150, 8.0, 90.0); con.commit()
    cba = {row["asin"]: row["conv"] for row in TrafficRepository(con).conversion_by_asin(tid)}
    assert cba.get("ASIN1") == 8.0
    print("PASS test_channel_repos")


def test_market_repo():
    con, tid = _fresh()
    m = MarketRepository(con)
    m.insert_snapshot(tid, "ASIN1", "2026-06-01T00:00:00", 1000, 5000, 5200, 4.4, 120, 7, 990, "sellerX", "{}")
    m.insert_snapshot(tid, "ASIN1", "2026-06-02T00:00:00", 980, 4800, 5100, 4.4, 121, 6, 970, "sellerY", "{}"); con.commit()
    assert len(m.recent_snapshots(tid, "ASIN1", 2)) == 2
    assert m.latest_bsr(tid, "ASIN1")["bsr"] == 4800
    m.insert_offer(tid, "ASIN1", "2026-06-02T00:00:00", "compA", 950, 1, 1, 1, "new")
    m.insert_offer(tid, "ASIN1", "2026-06-02T00:00:00", "compB", 900, 0, 1, 1, "new"); con.commit()
    offers = m.latest_offers(tid, "ASIN1")
    assert offers[0]["price"] == 900               # ORDER BY price ASC
    m.insert_signal(tid, "news", "trend", db.now_iso(), "2026-05-30", "Car Accessories",
                    "trend title", "http://t", "summary", 0.8, "{}", "dedup1"); con.commit()
    assert len(m.trends(tid, 3)) == 1
    sig = m.latest_signal(tid, "trend")            # returns a list (LIMIT 1)
    assert isinstance(sig, list) and len(sig) == 1
    assert m.latest_trend(tid)["title"] == "trend title"
    print("PASS test_market_repo")


def test_action_repo():
    con, tid = _fresh()
    a = ActionRepository(con)
    card = {"tenant_id": tid, "id": 1, "card_type": "C2"}
    lid = a.log_action(tid, db.now_iso(), 1, "C2", "reprice", "Reprice", "sum", "expl", "deep-link", "#", "{}")
    con.commit()
    assert isinstance(lid, int) and lid > 0
    assert len(a.recent(tid, 10)) == 1
    a.add_watchlist(tid, db.now_iso(), 1, "competitor", "label", "Car Accessories", ""); con.commit()
    assert len(a.list_watchlist(tid)) == 1
    a.add_sourcing(tid, db.now_iso(), 1, "seg", "ASIN9", "title", "brand", 100, 5000, 50, 4.2, 80, ""); con.commit()
    assert len(a.list_sourcing(tid)) == 1
    a.add_brief(tid, db.now_iso(), 1, "C2", "Car Accessories", "the brief"); con.commit()
    rid = a.start_run(tid, db.now_iso()); con.commit()
    assert isinstance(rid, int)
    a.finish_run(rid, db.now_iso(), 3, 2); con.commit()
    row = con.execute("SELECT status,cards_new,cards_updated FROM runs WHERE id=?", (rid,)).fetchone()
    assert row["status"] == "ok" and row["cards_new"] == 3 and row["cards_updated"] == 2
    print("PASS test_action_repo")


def test_analytics_repo():
    con, tid = _fresh()
    ar = AnalyticsRepository(con)
    now = db.now_iso()
    for ev in ("login", "page_view", "page_view", "insight_click", "research", "action_clickout"):
        ar.record(tid, 1, now, now[:10], ev, "dashboard", None, None, None)
    con.commit()
    tot = ar.totals(tid, 30)
    assert tot["page_views"] == 2 and tot["events"] == 6 and tot["active_users"] == 1
    assert len(ar.daily_summary(tid, 30)) == 1
    top = ar.top_users(tid, 30, 10)
    assert top and top[0]["events"] == 6
    assert ar.last_activity(tid) == now[:10]
    counts = SystemRepository(con).entity_counts()
    assert counts["tenants"] >= 1 and set(counts) == {"tenants", "users", "cards", "seller_skus", "invites"}
    print("PASS test_analytics_repo")


def _run_all():
    for fn in (test_order_repo, test_fact_repos, test_channel_repos, test_market_repo,
               test_action_repo, test_analytics_repo):
        fn()
    print("\nAll sweep-repo tests passed.")


if __name__ == "__main__":
    _run_all()
