"""Tests for the seller / rules / catalog contexts (final 1b increment).

Covers SellerRepository (CRUD, projections, dynamic updates, category aggregate), the
formula-bearing cogs.apply write path (customer COGS recompute), RulesRepository + the
rules.py effective/override round-trip, and CatalogRepository. Hermetic (fixture mode).
"""
import os, tempfile, sys

_TMP = tempfile.mkdtemp(prefix="realify_sr_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, rules, cogs                                  # noqa: E402
from realify.repositories import (                                   # noqa: E402
    UnitOfWork, SellerRepository, RulesRepository, CatalogRepository,
)


def _fresh():
    for sfx in ("", "-wal", "-shm"):
        try: os.remove(os.environ["REALIFY_DB"] + sfx)
        except OSError: pass
    db.init_db()


def _row(asin, **over):
    d = dict(asin=asin, title=f"T {asin}", category="Car Accessories", ptype="Car Cover",
             amazon_cat="Car", price=1000.0, cogs=300.0, referral_fee=155.0, fba_fee=70.0,
             ad_cost_unit=40.0, return_cost_unit=20.0, net_profit_unit=415.0, net_margin_pct=41.5,
             breakeven_floor=600.0, units_month=300, units_year=3600, velocity_day=10.0,
             annual_rev_inr=3600000, stock_on_hand=200, days_of_cover=20.0, buybox_pct=92,
             tacos=8.0, returns_rate=3.0, rating=4.4, review_count=120)
    d.update(over); return d


def test_seller_repository_crud_projection_dynamic():
    _fresh()
    with UnitOfWork() as uow:
        tid = uow.tenants.create("Org")
        s = uow.sellers
        s.insert(tid, _row("A1", category="Car Accessories"), 60.0)
        s.insert(tid, _row("A2", category="Bike Accessories", annual_rev_inr=2400000), 40.0)
        uow.commit()
        assert s.count(tid) == 2
        assert {r["asin"] for r in s.all(tid)} == {"A1", "A2"}
        assert s.by_asin(tid, "A1")["category"] == "Car Accessories"
        assert s.by_asin(tid, "ZZZ") is None
        assert set(s.distinct_categories(tid)) == {"Car Accessories", "Bike Accessories"}
        agg = s.category_aggregate(tid, "Car Accessories")
        assert agg["n"] == 1 and agg["gmv"] == 3600000
        proj = s.select_columns(tid, ["asin", "cogs"])
        assert all(set(r.keys()) == {"asin", "cogs"} for r in proj)
        # dynamic update by asin
        s.update_fields_by_asin(tid, "A1", {"buybox_pct": 55, "tacos": 19.0})
        uow.commit()
        assert s.by_asin(tid, "A1")["buybox_pct"] == 55
        # dynamic update by sku-or-asin + channel link
        s.link_channel(tid, "A2", "SKU-A2", "amazon")
        uow.commit()
        assert s.by_asin(tid, "A2")["internal_sku"] == "SKU-A2"
        s.update_fields_by_sku_or_asin(tid, "SKU-A2", {"returns_rate": 12.0})
        uow.commit()
        assert s.by_asin(tid, "A2")["returns_rate"] == 12.0
        # guard: unknown column rejected
        try:
            s.update_fields_by_asin(tid, "A1", {"; DROP": 1}); raise AssertionError("should reject")
        except ValueError:
            pass


def test_cogs_apply_recomputes_economics():
    _fresh()
    con = db.connect()
    SellerRepository(con).insert(1, _row("A1", price=1000.0, cogs=None, net_profit_unit=None,
                                         net_margin_pct=None, breakeven_floor=None, referral_fee=None), 100.0)
    # pretend tenant 1 exists enough for the write (cogs.apply only touches seller_skus)
    con.commit(); con.close()
    con = db.connect()
    n = cogs.apply(con, 1, [{"sku": "A1", "cogs": 300.0, "currency": "INR"}])
    con.commit(); con.close()
    assert n == 1
    con = db.connect()
    row = SellerRepository(con).by_asin(1, "A1"); con.close()
    # referral = 1000*0.155 = 155; net = 1000-300-155 = 545; margin = 54.5; floor = 300/(1-0.155)=355.03
    assert row["referral_fee"] == 155.0
    assert row["net_profit_unit"] == 545.0
    assert row["net_margin_pct"] == 54.5
    assert abs(row["breakeven_floor"] - 355.03) < 0.05


def test_rules_repository_and_effective_override_roundtrip():
    _fresh()
    rules.seed_catalog()
    with UnitOfWork() as uow:
        all_rules = uow.rules.all_rules()
        assert "C1" in all_rules and uow.rules.count_rules() == len(all_rules)
        assert uow.rules.get_rule("C1")["name"] == "Competitor Move"
        assert uow.rules.get_rule("NOPE") is None
        assert len(uow.rules.surface_map_rows()) == uow.rules.count_rules()
    tid = 1
    # effective starts at default (C1 min_gap_pct = 3.0)
    assert rules.effective_rules(tid)["C1"]["params"]["min_gap_pct"] == 3.0
    # override via the public path -> reflected; then reset clears it
    rules.save_override(tid, "C1", enabled=True, params={"min_gap_pct": 7.5})
    assert rules.effective_rules(tid)["C1"]["params"]["min_gap_pct"] == 7.5
    with UnitOfWork() as uow:
        assert "C1" in uow.rules.tenant_overrides(tid)
    rules.reset_override(tid, "C1")
    assert rules.effective_rules(tid)["C1"]["params"]["min_gap_pct"] == 3.0


def test_catalog_repository():
    _fresh()
    with UnitOfWork() as uow:
        assert uow.catalog.cached_segment(1, "seg") == []
        uow.catalog.insert_product(1, "Car Accessories", "seg", "B1", "Cover", "BrandX", 999.0, 1200, 50, 4.2)
        uow.commit()
        cached = uow.catalog.cached_segment(1, "seg")
        assert len(cached) == 1 and cached[0]["asin"] == "B1"


if __name__ == "__main__":
    for fn in (test_seller_repository_crud_projection_dynamic, test_cogs_apply_recomputes_economics,
               test_rules_repository_and_effective_override_roundtrip, test_catalog_repository):
        fn(); print(f"  PASS  {fn.__name__}")
    print("\n4/4 tests passed")
