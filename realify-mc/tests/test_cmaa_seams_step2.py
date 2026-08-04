"""Step 2 — CMAA seams: period-aware ads dimension, certain-vs-estimated separation, collector slot.
These are seams (no user-facing behaviour change); the tests pin the contracts Step 3 will consume.
"""
import pandas as pd

from realify import db
from realify.ingest import report_ingest as ri
from realify.ingest.report_writer import write_ingest
from realify.repositories.ad_performance_repo import AdPerformanceRepository
from realify.domain import economics
from realify.collectors.base import AdvertisedProductCollector


def _ad_df(rows):
    """rows: (date, asin, spend, sales). Includes the TACoS column the AD_REPORT detector keys on."""
    return pd.DataFrame(
        [{"Date": d, "Advertised ASIN": a, "Spend": s, "14 Day Total Sales": sa,
          "Total Advertising Cost of Sales": (s / sa if sa else 0)} for d, a, s, sa in rows])


def _fee_df(rows):
    """Fee-preview identity so ASIN resolves to SKU. rows: (sku, asin)."""
    return pd.DataFrame([{"sku": s, "asin": a, "product-name": s, "your-price": 100,
                          "estimated-referral-fee-per-unit": 10, "estimated-fee-total": 25} for s, a in rows])


# ---- period-aware ad dimension --------------------------------------------
def test_ad_periods_monthly_rollup():
    df = _ad_df([("2026-04-03", "B1", 100, 400), ("2026-04-20", "B1", 50, 150),
                 ("2026-05-05", "B1", 80, 320)])
    periods = ri._ad_periods(df, grain="month")
    by = {p["period_start"]: p for p in periods}
    assert by["2026-04-01"]["spend"] == 150 and by["2026-04-01"]["sales"] == 550
    assert by["2026-05-01"]["spend"] == 80


def test_ad_periods_resolve_sku_and_persist():
    tables = [("Fee.csv", _fee_df([("S1", "B1")])),
              ("SP_Advertised_Product.csv", _ad_df([("2026-04-03", "B1", 100, 400),
                                                    ("2026-05-05", "B1", 80, 320)]))]
    res = ri.ingest_tables(tables)
    # advertised ASIN B1 resolved to S1
    assert any(p["internal_sku"] == "S1" for p in res.ad_periods)
    with db.connect() as con:
        n = write_ingest(con, 1, res)["ad_periods_written"]
        con.commit()
        assert n == 2
        repo = AdPerformanceRepository(con)
        assert repo.periods(1) == ["2026-04-01", "2026-05-01"]
        tot = repo.totals(1)["S1"]
        assert tot["spend"] == 180 and tot["sales"] == 720


# ---- certain vs estimated separation --------------------------------------
def test_certainty_certain_when_all_settled():
    assert economics.certainty(
        {"price": "actual", "cogs": "seller", "referral_fee": "actual", "fba_fee": "actual"}) == "certain"


def test_certainty_estimated_when_any_input_estimated():
    # fee-preview: price reported, fees estimated -> estimated
    assert economics.certainty(
        {"price": "reported", "cogs": "seller", "referral_fee": "estimated", "fba_fee": "estimated"}) == "estimated"
    # one estimated fee is enough to downgrade
    assert economics.certainty(
        {"price": "actual", "cogs": "seller", "fba_fee": "estimated"}) == "estimated"


def test_certainty_none_when_no_inputs():
    assert economics.certainty({}) is None


# ---- AdvertisedProductCollector slot is a safe no-op fixture --------------
def test_advertised_product_collector_slot_is_noop():
    c = AdvertisedProductCollector(tenant_id=1, mode="fixture")
    assert c.source == "ads"
    assert c.fetch_fixture(None, "global", "a", "b") == []
    assert c.persist(None, "global", []) == 0
