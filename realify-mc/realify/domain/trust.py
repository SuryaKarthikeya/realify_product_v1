"""Trust layer (Step 4) — pure signals that make the CMAA verdict trustworthy over time.

No I/O, no app imports. Each function returns None when the answer is undecidable (too little
history, missing inputs) rather than guessing — the same discipline as domain/cmaa and economics.
These are the three guards from the plan:

  * TACoS-over-time    — is ad dependence trending up? (needs >=2 periods; time-gated)
  * cannibalization    — are ads capturing demand the seller would win organically? (time-gated)
  * lifecycle guard    — respect the seller's stated intent (launch/clearance/...) so the tab never
                         nags about a "problem" the seller has already accounted for.
"""

# ---- TACoS over time ------------------------------------------------------
def tacos_series(revenue_by_period, spend_by_period):
    """{period: tacos} where tacos = ad_spend / total_revenue, only for periods with revenue > 0.
    TACoS (not ACoS): spend measured against ALL revenue, so it reflects true ad dependence."""
    out = {}
    for p, rev in (revenue_by_period or {}).items():
        sp = (spend_by_period or {}).get(p)
        if rev and rev > 0 and sp is not None:
            out[p] = round(sp / rev, 4)
    return out


def tacos_trend(series, min_periods=2, tol=0.02):
    """'rising' / 'falling' / 'stable' / None from {period: tacos}. Compares earliest to latest over
    the ordered periods. None below min_periods — never call a trend on a single point."""
    if not series or len(series) < min_periods:
        return None
    pts = [series[k] for k in sorted(series)]
    delta = pts[-1] - pts[0]
    if abs(delta) <= tol:
        return "stable"
    return "rising" if delta > 0 else "falling"


# ---- cannibalization (time-gated) -----------------------------------------
def cannibalization_risk(buybox_pct, ad_sales, total_sales, n_periods,
                         min_periods=2, buybox_floor=90.0, ad_share_floor=0.5):
    """Flag likely ad cannibalization: the seller already dominates the Buy Box (organic would win
    the sale anyway) AND a large share of sales is ad-attributed — so ad spend is probably paying
    for demand that would convert without it. Time-gated: None until min_periods of history exist,
    so we never cry cannibalization on one month. Conservative thresholds by design; informs, never
    auto-acts."""
    if n_periods is None or n_periods < min_periods:
        return None
    if buybox_pct is None or total_sales in (None, 0) or ad_sales is None:
        return None
    ad_share = ad_sales / total_sales
    return bool(buybox_pct >= buybox_floor and ad_share >= ad_share_floor)


# ---- lifecycle guard (seller-flagged) -------------------------------------
_PROTECTIVE = {
    "launch": "launch — overspend is expected while gaining rank",
    "clearance": "clearance — thin margin is intentional",
    "seasonal": "seasonal — judge over the full season, not one month",
    "discontinued": "discontinued — winding down",
}
_PROBLEM_QUADRANTS = {"FIX ADS", "CUT/DIVEST", "FIX MARGIN"}


def lifecycle_guard(quadrant, lifecycle_flag):
    """Modulate a raw CMAA verdict with the seller's stated lifecycle intent. Returns
    (guarded: bool, note: str|None). Never flips a good verdict to bad or vice-versa — it only marks
    a 'problem' verdict as expected/accounted-for so the tab de-emphasises it instead of alarming."""
    flag = (lifecycle_flag or "").strip().lower()
    if flag in _PROTECTIVE and quadrant in _PROBLEM_QUADRANTS:
        return True, f"flagged {flag}: {_PROTECTIVE[flag]}"
    return False, None
