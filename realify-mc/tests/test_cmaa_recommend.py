"""Unit tests for the explainable recommended-action logic (domain/cmaa.recommend).

Pure — no DB, no app. Locks the contract the Profit & Ads tab renders on click:
  * problem quadrants produce a recommendation; SCALE gets a DIRECTIONAL scale action; everything
    else (Not advertised / Needs COGS) returns None,
  * FIX ADS surfaces the recoverable (= ₹ above break-even) and the ACoS→break-even chain,
  * FIX MARGIN / CUT/DIVEST offer the price-to-floor lever and never fabricate it without COGS,
  * a lifecycle-flagged SKU leads with the guard and is NOT told to cut (stated intent respected).
"""
from realify.domain import cmaa


def _row(**kw):
    base = dict(quadrant="FIX ADS", gcm_pct=40.0, breakeven_acos=40.0, actual_acos=60.0,
                ad_spend=600.0, ad_sales=1000.0, above_breakeven=200.0, margin_floor=0,
                margin_certainty="certain", cannibalization=False,
                lifecycle_guarded=False, lifecycle_note=None,
                price=1000.0, cogs=400.0, referral_fee=100.0, fba_fee=100.0)
    base.update(kw)
    return base


def test_only_advertised_judged_quadrants_recommend():
    # Non-advertised / undecidable rows never get an action.
    assert cmaa.recommend(_row(quadrant="Not advertised")) is None
    assert cmaa.recommend(_row(quadrant="Needs COGS")) is None


def test_scale_returns_directional_upside_action():
    # SCALE is the one non-problem quadrant with an action: a DIRECTIONAL raise-budget play whose
    # upside is the L1 scale_upside on the row (never re-derived here), flagged so the UI can badge it.
    rec = cmaa.recommend(_row(quadrant="SCALE", actual_acos=20.0, above_breakeven=0.0, scale_upside=33.33))
    assert rec is not None and rec["directional"] is True
    assert rec["upside"] == 33.33 and rec["recoverable"] is None
    assert "scale" in rec["headline"].lower()


def test_fix_ads_recoverable_and_evidence_chain():
    r = cmaa.recommend(_row())
    assert r["guarded"] is False
    assert r["recoverable"] == 200.0
    # headline names the actual and target ACoS
    assert "60.0%" in r["headline"] and "40.0%" in r["headline"]
    # evidence traces spend/sales -> ACoS and the waste figure
    joined = " ".join(r["evidence"])
    assert "Actual ACoS" in joined and "above break-even" in joined
    assert any("₹200" in s for s in r["evidence"])


def test_fix_ads_cannibalization_adds_caveat():
    r = cmaa.recommend(_row(cannibalization=True))
    assert any("organic demand" in s for s in r["steps"])


def test_fix_margin_offers_price_and_does_not_cut_ads():
    # margin below a 25% floor, ads efficient
    r = cmaa.recommend(_row(quadrant="FIX MARGIN", gcm_pct=10.0, actual_acos=8.0,
                            breakeven_acos=10.0, above_breakeven=0.0, margin_floor=25))
    assert r["recoverable"] is None
    assert any("Don't cut ads" in s for s in r["steps"])
    # price to clear 25% floor = (400+100+100)/(1-0.25) = 800
    assert any("₹800" in s for s in r["steps"])


def test_cut_divest_below_cost_flags_all_spend_as_waste():
    r = cmaa.recommend(_row(quadrant="CUT/DIVEST", gcm_pct=-5.0, cogs=1100.0,
                            actual_acos=None, ad_sales=0.0, above_breakeven=600.0))
    assert "Losing on both" in r["headline"]
    joined = " ".join(r["evidence"])
    assert "below cost" in joined
    assert any("stop ads" in s for s in r["steps"])


def test_price_for_floor_needs_cogs():
    assert cmaa.price_for_floor(None, 100, 100, 0) is None
    assert cmaa.price_for_floor(400, 100, 100, 0) == 600
    assert cmaa.price_for_floor(400, 100, 100, 25) == 800


def test_lifecycle_guard_leads_and_never_recommends_cutting():
    r = cmaa.recommend(_row(quadrant="CUT/DIVEST", gcm_pct=-5.0,
                            lifecycle_guarded=True,
                            lifecycle_note="flagged launch: launch — overspend is expected"))
    assert r["guarded"] is True
    assert "launch" in r["headline"]
    assert r["recoverable"] is None
    steps = " ".join(r["steps"]).lower()
    assert "no action" in steps and "stop ads" not in steps and "wind it down" not in steps


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("all recommend tests passed")
