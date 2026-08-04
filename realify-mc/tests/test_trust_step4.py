"""Step 4 — trust layer: TACoS-over-time, cannibalization (time-gated), lifecycle guard."""
import pandas as pd

from realify import db
from realify.domain import trust
from realify.ingest import report_ingest as ri
from realify.ingest.report_writer import write_ingest
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.revenue_period_repo import RevenuePeriodRepository
from realify.repositories.ad_performance_repo import AdPerformanceRepository


# ---- pure: TACoS trend ----------------------------------------------------
def test_tacos_series_and_trend():
    rev = {"2026-04-01": 1000, "2026-05-01": 1000, "2026-06-01": 1000}
    spend = {"2026-04-01": 100, "2026-05-01": 200, "2026-06-01": 300}
    ser = trust.tacos_series(rev, spend)
    assert ser == {"2026-04-01": 0.1, "2026-05-01": 0.2, "2026-06-01": 0.3}
    assert trust.tacos_trend(ser) == "rising"
    assert trust.tacos_trend({"2026-04-01": 0.2, "2026-05-01": 0.1}) == "falling"
    assert trust.tacos_trend({"2026-04-01": 0.2, "2026-05-01": 0.21}) == "stable"


def test_tacos_trend_time_gated():
    # one period is not a trend
    assert trust.tacos_trend({"2026-04-01": 0.3}) is None
    assert trust.tacos_trend({}) is None


# ---- pure: cannibalization is time-gated + conservative -------------------
def test_cannibalization_time_gated():
    # dominant Buy Box + high ad share, but only 1 period -> withhold judgment
    assert trust.cannibalization_risk(95, 800, 1000, n_periods=1) is None
    # enough history -> fires
    assert trust.cannibalization_risk(95, 800, 1000, n_periods=3) is True
    # low Buy Box -> ads are winning genuinely contested demand, not cannibalizing
    assert trust.cannibalization_risk(60, 800, 1000, n_periods=3) is False
    # missing inputs -> None
    assert trust.cannibalization_risk(None, 800, 1000, n_periods=3) is None


# ---- pure: lifecycle guard softens but never flips -------------------------
def test_lifecycle_guard():
    g, note = trust.lifecycle_guard("FIX ADS", "launch")
    assert g is True and "launch" in note
    # a good verdict is never guarded into looking bad
    assert trust.lifecycle_guard("SCALE", "launch") == (False, None)
    # no flag -> no guard
    assert trust.lifecycle_guard("CUT/DIVEST", None) == (False, None)


# ---- integration: revenue periods persist + portfolio TACoS ----------------
def _tx(rows):
    cols = ["settlement id", "type", "marketplace", "Sku", "product sales", "quantity",
            "selling fees", "fba fees", "other transaction fees", "date/time"]
    return pd.DataFrame([[1, t, mp, sku, ps, q, -0.1 * ps, -20 * q, 0, dt] for sku, t, mp, ps, q, dt in rows],
                        columns=cols)


def test_revenue_periods_persist_and_scope():
    df = _tx([
        ("S1", "Order", "amazon.in", 1000, 10, "15 Apr 2026 1:00:00 pm UTC"),
        ("S1", "Order", "amazon.in", 500, 5, "10 May 2026 1:00:00 pm UTC"),
        ("S1", "Order", "si-prod-in.stores.amazon.in", 0, 3, "12 May 2026 1:00:00 pm UTC"),  # MCF excluded
    ])
    res = ri.ingest_tables([("MonthlyUnifiedTransaction.csv", df)])
    with db.connect() as con:
        n = write_ingest(con, 1, res)["revenue_periods_written"]
        con.commit()
        assert n == 2
        rev = RevenuePeriodRepository(con).for_sku(1, "S1")
        assert rev == {"2026-04-01": 1000.0, "2026-05-01": 500.0}   # MCF ₹0 row not counted


def test_cmaa_tab_exposes_trust_signals():
    from realify.routers import cmaa as C
    import realify.routers.deps as deps
    tid = 7
    with db.connect() as con:
        SellerRepository(con).upsert_full(tid, {
            "internal_sku": "S1", "asin": "S1", "channel": "amazon",
            "price": 1000, "cogs": 400, "referral_fee": 100, "fba_fee": 100,
            "buybox_pct": 95, "lifecycle_flag": "launch"})
        for p, sp in [("2026-04-01", 300), ("2026-05-01", 500)]:
            AdPerformanceRepository(con).upsert(tid, "S1", p, "month", sp, 900)  # ACoS 44% > BE 40% -> FIX ADS
            RevenuePeriodRepository(con).upsert(tid, "S1", p, "month", 1000, 10)
        con.commit()
    deps.require_tenant = lambda request: tid
    C.require_tenant = lambda request: tid
    import json

    class R:
        pass
    d = json.loads(bytes(C.cmaa_tab(R()).body).decode())
    s = next(x for x in d["skus"] if x["sku"] == "S1")
    assert s["tacos_trend"] == "rising"          # 0.10 -> 0.30
    assert s["lifecycle_guarded"] is True        # launch softens the FIX ADS verdict
    assert "portfolio_tacos" in d["summary"]
