"""Ads-specific re-simulation behind the deterministic project() seam (spec §5).

The Fix-Ads modal's Simulate lets the customer edit the bid change (and optionally a target ACoS) and
Re-simulate; that re-invokes project() with the customer's params and re-renders 30/60/90 + a per-horizon
probability + the tripwire. Every projected figure is `formula_id = cmaa_projection` in the admin registry.

Deterministic (same inputs -> same projection) and honest-empty (nothing recoverable -> None). A more
aggressive bid cut captures more of the certain waste but is less certain (units-at-risk), so probability
decays as the cut deepens — the projection never pretends a bigger cut is free.
"""
DEFAULT_BID_PCT = 0.30           # matches ad_recommend.BID_DOWN_PCT (the starting ask)
CAPTURE_CAP = 1.4                # a cut beyond the default can capture a little more, bounded (no free lunch)
RAMP = [(30, 0.85), (60, 1.85), (90, 2.85)]   # first month partial ramp, then full months (cumulative)
BASE_P = [0.72, 0.66, 0.60]      # confidence decays with the horizon


def _conf(coverage_pct, fidelity):
    return max(0.0, min((coverage_pct or 0) / 100.0, 1.0)) * (
        1.0 if fidelity == "KEYWORD" else 0.9 if fidelity == "CAMPAIGN_SKU" else 0.75)


def project(recoverable_monthly, coverage_pct, fidelity, bid_change_pct=DEFAULT_BID_PCT, target_acos=None):
    """project() seam — 30/60/90 recoverable CMAA under a customer-chosen bid cut. bid_change_pct is a
    magnitude in [0.05, 0.60]; target_acos (fraction) is an optional refinement that trims capture toward
    the ACoS gap. Returns {horizons:[{days,delta,prob}], tripwire, params, formula_id}. None if nothing
    to recover (honest-empty)."""
    if not recoverable_monthly or recoverable_monthly <= 0:
        return None
    bid = max(0.05, min(abs(bid_change_pct or DEFAULT_BID_PCT), 0.60))
    capture = min(bid / DEFAULT_BID_PCT, CAPTURE_CAP)         # 30% cut -> full recoverable; deeper -> capped
    if target_acos is not None and 0 < target_acos < 1:
        capture *= min(1.0, max(0.5, target_acos / 0.30))    # a tighter target trims what's realistically captured
    conf = _conf(coverage_pct, fidelity)
    aggressive = max(0.0, bid - DEFAULT_BID_PCT) * 0.9        # extra cut costs certainty (units at risk)
    horizons = [{"days": d, "delta": round(recoverable_monthly * capture * r),
                 "prob": round(max(0.30, min(0.9, BASE_P[i] * (0.7 + 0.3 * conf) - aggressive)), 2)}
                for i, (d, r) in enumerate(RAMP)]
    return {"horizons": horizons, "formula_id": "cmaa_projection", "tripwire_formula_id": "tripwire_units",
            "tripwire": "if units/week fall >15% after the bid cut, auto-revert and flag",
            "params": {"bid_change_pct": round(bid, 2), "target_acos": target_acos}}
