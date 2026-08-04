"""Regression cover for the ad-sales ₹0 fix + CMAA column + June-overlap dedupe.

The bug: the SP "Advertised Product" report's money columns arrive rupee-formatted ('₹4,000.00');
_num() stripped commas but not the ₹, so pd.to_numeric returned NaN and summed ad sales collapsed to
0 → ACoS undefined for every advertised SKU → 100% of spend flagged above break-even. These tests
pin the coercion, the populated sales, the ACoS guard, the CMAA-in-₹ math, and the overlap dedupe.
All are pure / ingest-level (no DB), so they run identically on SQLite and Postgres.
"""
import pandas as pd

from realify.ingest import report_ingest as ri
from realify.ingest.periods import _ad_periods, dedupe_ad_periods
from realify.domain import cmaa


_AD_COLS = ["Date", "Advertised ASIN", "Spend", "7 Day Total Sales",
            "Total Advertising Cost of Sales (ACOS) "]


def _ad_frame(rows):
    return pd.DataFrame(rows, columns=_AD_COLS)


# ---- 1. the coercion itself (root cause) ----------------------------------
def test_num_strips_currency_commas_and_whitespace():
    got = {k: (None if pd.isna(v) else round(float(v), 4))
           for k, v in zip(["a", "b", "c", "d", "e", "f", "g"],
                            ri._num(pd.Series(["₹1,234.50", "Rs. 1,234", "INR 999",
                                               "$12.50", "1,00,000", "(500)", "4000"])))}
    assert got == {"a": 1234.5, "b": 1234.0, "c": 999.0, "d": 12.5,
                   "e": 100000.0, "f": -500.0, "g": 4000.0}


def test_num_leaves_unparseable_as_nan():
    out = ri._num(pd.Series(["—", "", "n/a", "nan"]))
    assert out.isna().all()


# ---- 2. sales is populated from a ₹-formatted report (was 0) --------------
def test_ad_periods_populate_rupee_sales():
    df = _ad_frame([["2026-06-01", "B0AUTOFY01", "₹1,200.50", "₹4,000.00", "30.0%"],
                    ["2026-06-02", "B0AUTOFY01", "₹800.00", "₹2,500.00", "32.0%"]])
    recs = _ad_periods(df)
    assert len(recs) == 1
    r = recs[0]
    assert r["asin"] == "B0AUTOFY01" and r["period_start"] == "2026-06-01"
    assert r["spend"] == 2000.5           # 1200.50 + 800.00, ₹ stripped
    assert r["sales"] == 6500.0           # 4000 + 2500 — the field that used to be 0


def test_ad_sales_col_ignores_the_acos_column():
    # the ACoS column must never be picked as the attributed-sales column
    cols = ["date", "advertised asin", "spend", "total advertising cost of sales (acos)"]
    assert ri._ad_sales_col(cols) is None
    cols2 = cols + ["7 day total sales"]
    assert ri._ad_sales_col(cols2) == "7 day total sales"


def test_extract_ad_report_coerces_rupees():
    # the seller_skus-aggregate path (_extract) must also coerce, not concatenate strings
    df = _ad_frame([["2026-06-01", "B0X", "₹1,000", "₹5,000", "20%"],
                    ["2026-06-02", "B0X", "₹1,000", "₹5,000", "20%"]])
    recs = ri._extract(ri.AD_REPORT, df)
    fields = {fname: val for _kind, _key, fname, val, _basis in recs}
    assert fields["ad_spend"] == 2000.0 and fields["ad_sales"] == 10000.0


# ---- 3. June-overlap dedupe (take latest, don't sum) ----------------------
def test_overlapping_month_reports_are_not_double_counted():
    a = _ad_frame([["2026-06-01", "B0X", "₹1,000", "₹3,000", "33%"],
                   ["2026-06-15", "B0X", "₹500", "₹1,500", "33%"]])
    b = _ad_frame([["2026-06-02", "B0X", "₹1,000", "₹3,000", "33%"],
                   ["2026-06-20", "B0X", "₹500", "₹1,500", "33%"]])
    deduped = dedupe_ad_periods([a, b])
    assert len(deduped) == 1
    # each file totals ₹1,500 for June; take-latest keeps 1,500 — NOT 3,000
    assert deduped[0]["spend"] == 1500.0
    assert deduped[0]["sales"] == 4500.0


def test_distinct_months_still_kept_across_files():
    may = _ad_frame([["2026-05-10", "B0X", "₹700", "₹2,000", "35%"]])
    jun = _ad_frame([["2026-06-10", "B0X", "₹900", "₹3,000", "30%"]])
    deduped = {(r["period_start"]): r["spend"] for r in dedupe_ad_periods([may, jun])}
    assert deduped == {"2026-05-01": 700.0, "2026-06-01": 900.0}


def test_ingest_tables_uses_dedupe_for_ad_periods():
    a = _ad_frame([["2026-06-01", "B0X", "₹1,000", "₹3,000", "33%"]])
    b = _ad_frame([["2026-06-02", "B0X", "₹1,000", "₹3,000", "33%"]])
    res = ri.ingest_tables([("ad_v1.csv", a), ("ad_v2.csv", b)])
    total_spend = sum(r["spend"] for r in res.ad_periods)
    assert total_spend == 1000.0          # one June, not two summed


# ---- 4. ACoS guard: <= 0 attributed sales -> None (not "all above BE") ----
def test_acos_guards_nonpositive_sales():
    assert cmaa.acos(500, 2000) == 0.25
    assert cmaa.acos(500, 0) is None
    assert cmaa.acos(500, None) is None
    assert cmaa.acos(500, -10) is None    # negative denominator is nonsensical -> undefined
    assert cmaa.acos(None, 2000) is None


def test_wasted_spend_formula_and_guards():
    # spend above break-even = max(0, spend - sales*margin%)
    assert cmaa.wasted_spend(100, 200, 0.30) == 40.0     # 100 - 200*0.3 = 40
    assert cmaa.wasted_spend(50, 200, 0.30) == 0.0       # 50 - 60 -> clamped to 0
    assert cmaa.wasted_spend(100, 0, None) == 100.0      # no sales, unknown margin -> all above
    assert cmaa.wasted_spend(100, 50, None) is None      # sales but unknown margin -> undecidable
    assert cmaa.wasted_spend(100, -5, 0.30) == 100.0     # negative sales clamped to 0


# ---- 5. CMAA in ₹ + % (the new column) ------------------------------------
def test_contribution_after_ads_amount_and_pct():
    # gross contribution/unit 30, 100 units, ₹500 ad spend, ₹10,000 net revenue
    r = cmaa.contribution_after_ads(30, 100, 500, 10000)
    assert r["amount"] == 2500.0          # 30*100 - 500
    assert r["pct"] == 25.0               # 2500 / 10000


def test_contribution_after_ads_no_ads_is_pread_contribution():
    r = cmaa.contribution_after_ads(30, 100, None, 10000)
    assert r["amount"] == 3000.0          # ad_spend absent counts as 0
    assert r["pct"] == 30.0


def test_contribution_after_ads_can_be_negative():
    r = cmaa.contribution_after_ads(10, 100, 2000, 12000)
    assert r["amount"] == -1000.0         # 1000 contribution - 2000 ads -> loss after ads
    assert r["pct"] == round(-1000 / 12000 * 100, 1)


def test_contribution_after_ads_never_fabricates():
    assert cmaa.contribution_after_ads(None, 100, 500, 10000) == {"amount": None, "pct": None}
    assert cmaa.contribution_after_ads(30, None, 500, 10000) == {"amount": None, "pct": None}
    # amount computable, but % undecidable without net revenue
    assert cmaa.contribution_after_ads(30, 100, 500, None) == {"amount": 2500.0, "pct": None}


# ---- 6. end-to-end: ₹ report -> ACoS is now DEFINED, spend NOT all-above --
def test_defined_acos_after_fix():
    df = _ad_frame([["2026-06-01", "B0X", "₹1,000", "₹5,000", "20%"]])
    rec = _ad_periods(df)[0]
    # margin 40% -> break-even ACoS 0.40; actual ACoS = 1000/5000 = 0.20 <= 0.40 -> ads OK
    ev = cmaa.evaluate(rec["spend"], rec["sales"], contribution=40, net_revenue=100, margin_floor=0.0)
    assert ev["actual_acos"] == 0.20      # DEFINED (was None when sales coerced to 0)
    assert ev["wasted_spend"] == 0.0      # not "all above break-even"
    assert ev["quadrant"] == "SCALE"
