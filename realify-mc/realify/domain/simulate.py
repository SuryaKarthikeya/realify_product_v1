"""SIMULATE — deterministic SCENARIO PROJECTION for Profit & Ads. NOT a prediction engine.

North star: win trust by showing the math, the failure modes, and exactly what to watch. So every
projected figure = a CURRENT-STATE L1 value (already on the /api/cmaa row) transformed by an
EXPLICIT, NAMED assumption — emitted as a realify.domain.explain `part` (formula + inputs + the
assumption used + result), rendered on the SAME explain_mode spine as everything else. L1 owns the
numbers; L2 phrases; the client renders the result string and NEVER recomputes.

Five parts (each fully explainable): intervention model · 30/60/90 projection (with a DO-NOTHING
baseline) · what-could-go-wrong · 7/15/30/60 monitoring plan (the hero) · editable assumptions
(clamped to declared ranges server-side; a lever missing a required input degrades to an honest
"can't simulate", never a fabricated number). Badged `L1 · projection · directional`; ranges over presets.
"""
from . import cmaa, sim_common as sc

# shared spine (sim_common): formatting, ramp curve, explain-cell/row builders, assumption plumbing
HORIZONS, CHECKPOINTS, PROV, BADGE, DISCLAIMER, _PRESETS = (
    sc.HORIZONS, sc.CHECKPOINTS, sc.PROV, sc.BADGE, sc.DISCLAIMER, sc.PRESETS)
_money, _pctf, _units, _reached, _cell, _row = sc.money, sc.pctf, sc.units, sc.reached, sc.cell, sc.row
# named monitoring/risk sensitivity factors — NOT hidden inline magic; each is a stated, conservative
# tolerance used only to place a tripwire, documented in the tripwire text so it's inspectable.
TRIPWIRE_TOL = 0.5        # tripwire = midpoint of now→expected; above it = lagging the glide path
RETENTION_TRIP = 0.8      # CUT: units below 80% of the retained floor = organic not holding
MARGIN_TRIP = 0.9         # FIX MARGIN: units below 90% of projected = elasticity worse than modeled
MARGIN_RISK_STEP = 0.4    # FIX MARGIN risk: units lost per +0.4 of elasticity (illustrative step)
AD_MATERIALITY = 100.0    # ₹/mo: ad spend below this = nothing material to recover or scale (degrade)
# confidence-band half-width on each lever's KEY uncertainty assumption (≈ the declared preset spread).
# The band re-derives AROUND the CURRENT value every simulate: expected == the point, the point always
# falls within [conservative, optimistic], and the whole band moves when you re-simulate.
BAND_H, BAND_DRIFT, BAND_E = 0.20, 0.25, 0.40   # ± on organic_hold / acos_drift / elasticity

# ---- assumptions per bucket: name, default, min, max, unit, description, source, presets(cons/exp/opt)
# ramp_days = linear days to steady state (effect lands over time; day 90 ≈ steady). Documented + editable.
_ASSUMPTIONS = {
    "FIX ADS": [
        ("organic_hold", 0.70, 0.0, 1.0, "frac",
         "Share of ad-attributed sales that are really organic demand and HOLD when you cut bids.",
         "conservative constant (category norm ~0.6–0.8)", (0.50, 0.70, 0.90)),
        ("ramp_days", 60, 21, 120, "days",
         "Days for the bid cut to reach steady state (ACoS settles, rank/organic adjust).",
         "conservative constant", (90, 60, 45)),
    ],
    "SCALE": [
        ("max_multiple", 2.0, 1.2, 2.0, "×",
         "Cap on ad-driven sales growth vs today's run-rate (diminishing returns bound). Capped at "
         "the L1 bounded-upside multiple so the projection can never exceed the computed ceiling.",
         "same bounded ceiling the upside uses (cmaa.SCALE_MAX_MULTIPLE)", (1.6, 1.8, 2.0)),
        ("acos_drift", 0.5, 0.0, 1.0, "frac",
         "How far incremental ACoS drifts from today toward break-even as you scale (diminishing returns).",
         "conservative constant", (0.8, 0.5, 0.25)),
        ("ramp_days", 60, 21, 120, "days", "Days for the budget raise to reach steady state.",
         "conservative constant", (90, 60, 45)),
    ],
    "CUT/DIVEST": [
        ("organic_retention", 0.40, 0.0, 1.0, "frac",
         "Share of ad-driven units retained organically after ads stop.",
         "conservative constant (weak for a losing SKU)", (0.20, 0.40, 0.60)),
        ("ramp_days", 30, 7, 90, "days", "Days for volume to settle after pulling ads.",
         "conservative constant", (45, 30, 21)),
    ],
    "FIX MARGIN": [
        ("price_increase", 0.08, 0.0, 0.40, "frac", "Price increase applied to lift margin.",
         "conservative constant (~8%)", (0.05, 0.08, 0.12)),
        ("elasticity", 1.2, 0.0, 3.0, "e",
         "Demand elasticity: % units lost per % price up (>1 = elastic, volume-sensitive).",
         "conservative constant", (1.6, 1.2, 0.8)),
        ("ramp_days", 45, 14, 120, "days", "Days for demand to settle after the price change.",
         "conservative constant", (60, 45, 30)),
    ],
}
def _defaults(bucket):
    return sc.defaults(_ASSUMPTIONS.get(bucket, []))


def _assumption_meta(bucket, asm):
    return sc.assumption_meta(_ASSUMPTIONS.get(bucket, []), asm)


def _presets(bucket):
    return sc.presets(_ASSUMPTIONS.get(bucket, []))


# ------------------------------------------------------------------ FIX ADS
def _fix_ads(row, asm):
    S, Sa = row.get("ad_spend"), row.get("ad_sales")
    A = (row.get("actual_acos") or 0) / 100.0
    B = (row.get("breakeven_acos") or 0) / 100.0
    gcm = (row.get("gcm_pct") or 0) / 100.0
    Rec = row.get("above_breakeven") or 0
    C = row.get("cmaa")
    if not (S and Sa and A > 0 and Rec > 0):
        return {"missing": "ad spend / ad sales / recoverable ₹ for this SKU"}
    H = asm["organic_hold"]; R = asm["ramp_days"]
    lost_sales = Rec / A                                   # sales the wasted spend bought (spend ÷ ACoS)
    at_risk = round((1 - H) * lost_sales * gcm, 2)         # contribution lost if organic doesn't hold

    def _g(hh):                                            # steady CMAA gain at organic-hold hh (≤ Rec ceiling)
        return round(Rec - (1 - hh) * lost_sales * gcm, 2)
    gain = _g(H)                                           # POINT at current organic_hold; band ±BAND_H around it
    band = {"conservative": _money(_g(max(H - BAND_H, 0.0))), "expected": _money(gain),
            "optimistic": _money(_g(min(H + BAND_H, 1.0)))}
    proj = [
        _row("Wasted ad spend removed / mo", "₹", _money(0), Rec, 0.0, _money, R,
             "recoverable ceiling × ramp fraction (spend above break-even you stop wasting)",
             lambda h, rf, v: [("Recoverable ceiling", Rec, "₹"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        _row("Actual ACoS", "%", _pctf(A * 100), (B - A) * 100, A * 100, _pctf, R,
             "actual ACoS ramps down toward break-even as bids settle",
             lambda h, rf, v: [("Now", round(A*100, 1), "%"), ("Break-even (target)", round(B*100, 1), "%"),
                               ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        _row("CMAA / mo", "₹", _money(C), gain, (C or 0), _money, R,
             "current CMAA + net gain × ramp; net gain = recoverable − (1−organic_hold) × (recoverable ÷ ACoS) × margin",
             lambda h, rf, v: [("Current CMAA", C, "₹"), ("Steady net gain", gain, "₹"),
                               ("Organic-hold H", H, "frac"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "CMAA gain / mo at steady state", "do_nothing": _money(C or 0),
                "do_this": _money((C or 0) + gain), "delta": _money(gain), "range": band,
                "explain": _cell("CMAA gain / mo", "recoverable − (1−H) × (recoverable ÷ ACoS) × margin",
                                 [("Recoverable", Rec, "₹"), ("Organic-hold H", H, "frac"),
                                  ("ACoS", round(A*100, 1), "%"), ("Margin", round(gcm*100, 1), "%"),
                                  ("Contribution at risk", at_risk, "₹")], _money(gain))}
    risks = [
        {"title": "Organic demand doesn't hold", "assumption": "organic_hold",
         "magnitude": _money(at_risk) + "/mo of contribution at risk",
         "mechanism": ("Ad sales may have propped rank/organic. If less than %d%% holds, you lose the "
                       "margin on the sales the cut removes." % int(H * 100))},
        {"title": "Volume drops more than proportionally", "assumption": "organic_hold", "magnitude": None,
         "mechanism": "Cutting bids can cost rank, which compounds into lower organic — a non-linear dip."},
        {"title": "Competitors fill the vacated ad slots", "assumption": None, "magnitude": None,
         "mechanism": "Your lower bids free impressions competitors can take, slowing the organic hold."},
    ]
    monitor = _monitor_acos(A, B, R)
    return {"intervention": ("Lower bids/pause non-converting terms so actual ACoS (%s) falls to your "
            "break-even (%s). Ad-attributed sales scale down with spend; %d%% of them are assumed "
            "organic and hold." % (_pctf(A*100), _pctf(B*100), int(H*100))),
            "projection": proj, "headline": headline, "risks": risks, "monitoring": monitor}


def _monitor_acos(A, B, R):
    out = []
    for d in CHECKPOINTS:
        rf = _reached(d, R)
        exp = A * 100 + (B * 100 - A * 100) * rf
        trip = round(exp + (A * 100 - exp) * TRIPWIRE_TOL, 1)   # midpoint of now→expected; above it = lagging
        out.append({"day": d, "metric": "Actual ACoS", "expected": _pctf(exp),
                    "tripwire": "still > %s (the %d%% midpoint of now→expected) — the bid cut isn't taking; revert or investigate"
                    % (_pctf(trip), int(TRIPWIRE_TOL * 100)),
                    "explain": _cell("Expected ACoS · day %d" % d, "ACoS + (break-even − ACoS) × ramp fraction",
                                     [("ACoS", round(A*100, 1), "%"), ("Break-even", round(B*100, 1), "%"),
                                      ("Ramp fraction", round(rf, 2), "×")], _pctf(exp))})
    return out


# ------------------------------------------------------------------ SCALE
def _scale(row, asm):
    Sa = row.get("ad_sales"); A = (row.get("actual_acos") or 0) / 100.0
    B = (row.get("breakeven_acos") or 0) / 100.0
    up = row.get("scale_upside"); C = row.get("cmaa")
    if not (Sa and A > 0 and up):
        return {"missing": "ad sales / scale upside for this SKU"}
    M = asm["max_multiple"]; drift = asm["acos_drift"]; R = asm["ramp_days"]
    incr_sales = Sa * (M - 1)
    ceiling = up

    def _g(dr):                                            # steady gain at acos_drift dr, ≤ bounded ceiling
        return round(min(max(incr_sales * (B - A) * (1 - dr), 0), ceiling), 2)
    gain = _g(drift)                                       # POINT at current drift; band ±BAND_DRIFT (more drift ⇒ lower)
    band = {"conservative": _money(_g(min(drift + BAND_DRIFT, 1.0))), "expected": _money(gain),
            "optimistic": _money(_g(max(drift - BAND_DRIFT, 0.0)))}
    proj = [
        _row("Incremental ad-sales / mo", "₹", _money(0), incr_sales, 0.0, _money, R,
             "ad-sales × (max multiple − 1), ramped",
             lambda h, rf, v: [("Ad-sales run-rate", Sa, "₹"), ("Max multiple", M, "×"),
                               ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        _row("CMAA / mo", "₹", _money(C), gain, (C or 0), _money, R,
             "current CMAA + incremental ad-sales × (break-even − ACoS) × (1 − acos_drift), ramped",
             lambda h, rf, v: [("Current CMAA", C, "₹"), ("Steady gain", gain, "₹"),
                               ("ACoS drift", drift, "frac"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "CMAA gain / mo at steady state", "do_nothing": _money(C or 0),
                "do_this": _money((C or 0) + gain), "delta": _money(gain), "range": band,
                "explain": _cell("Scale CMAA gain / mo (directional, bounded)",
                                 "incremental ad-sales × (break-even − ACoS) × (1 − acos_drift); ≤ bounded upside",
                                 [("Incremental ad-sales", round(incr_sales, 2), "₹"),
                                  ("Break-even", round(B*100, 1), "%"), ("ACoS", round(A*100, 1), "%"),
                                  ("ACoS drift", drift, "frac"), ("Bounded ceiling", ceiling, "₹")],
                                 _money(gain), note="Capped at the bounded scale-upside ceiling.")}
    risks = [
        {"title": "Returns diminish faster than modeled", "assumption": "acos_drift", "magnitude": None,
         "mechanism": "Incremental ACoS can rise faster than assumed as you bid up — later spend buys less."},
        {"title": "ACoS blows past break-even", "assumption": "acos_drift",
         "magnitude": "gain → 0 if incremental ACoS reaches break-even",
         "mechanism": "If the incremental sale's ACoS exceeds break-even, added spend loses money."},
    ]
    monitor = []
    for d in CHECKPOINTS:
        rf = _reached(d, R)
        out_acos = (A + (B - A) * drift) * 100              # steady incremental ACoS as you scale
        exp = out_acos * rf + A * 100 * (1 - rf)            # ramp-blended: today's ACoS → steady, over the ramp
        monitor.append({"day": d, "metric": "Incremental ACoS", "expected": _pctf(exp),
                        "tripwire": "incremental ACoS > break-even (%s) — stop raising budget" % _pctf(B*100),
                        "explain": _cell("Expected incremental ACoS · day %d" % d,
                                         "ACoS + (steady incremental ACoS − ACoS) × ramp fraction",
                                         [("ACoS", round(A*100, 1), "%"), ("Break-even", round(B*100, 1), "%"),
                                          ("Drift", drift, "frac"), ("Ramp fraction", round(rf, 2), "×")],
                                         _pctf(exp))})   # displayed value == explain result (the blocker fix)
    return {"intervention": ("Raise budget/bids while ACoS stays at/under break-even (%s). Incremental "
            "ad-sales capped at %g× today's run-rate; incremental ACoS drifts %d%% of the way toward "
            "break-even (diminishing returns)." % (_pctf(B*100), M, int(drift*100))),
            "projection": proj, "headline": headline, "risks": risks, "monitoring": monitor}


# ------------------------------------------------------------------ CUT/DIVEST
def _cut(row, asm):
    S = row.get("ad_spend"); C = row.get("cmaa"); u = row.get("units_month")
    if not S:
        return {"missing": "ad spend for this SKU"}
    Rt = asm["organic_retention"]; R = asm["ramp_days"]
    saved = round(S, 2)                                    # bleed stops immediately
    units_at_risk = round((u or 0) * (1 - Rt), 1) if u else None
    proj = [
        _row("Ad spend / mo", "₹", _money(S), -S, S, _money, R,
             "ad spend falls to 0 once ads are pulled (bleed stops)",
             lambda h, rf, v: [("Current spend", S, "₹"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    if u is not None:
        lost = (u or 0) * (1 - Rt)
        proj.append(_row("Units / mo at risk", "units", _units(u), -lost, u, _units, R,
                    "units that don't retain organically after ads stop = units × (1 − organic_retention)",
                    lambda h, rf, v: [("Units / mo now", u, "units"), ("Organic retention", Rt, "frac"),
                                      ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]))
    headline = {"label": "Ad bleed stopped / mo", "do_nothing": _money(0), "do_this": _money(saved),
                "delta": _money(saved),
                "range": {"conservative": _money(saved), "expected": _money(saved), "optimistic": _money(saved)},
                "explain": _cell("Ad bleed stopped / mo", "your ad spend on this losing SKU, stopped",
                                 [("Ad spend", S, "₹")], _money(saved),
                                 note="Bleed stops immediately; organic-volume risk is the trade-off.")}
    risks = [
        {"title": "Organic falls more than retained", "assumption": "organic_retention",
         "magnitude": (_units(units_at_risk) + "/mo at risk") if units_at_risk is not None else None,
         "mechanism": ("If less than %d%% of ad-driven units retain organically, you lose more volume "
                       "than the bleed you saved warrants." % int(Rt * 100))},
    ]
    monitor = []
    if u is not None:
        for d in CHECKPOINTS:
            rf = _reached(d, R)
            exp = u - (u * (1 - Rt)) * rf
            monitor.append({"day": d, "metric": "Units / mo", "expected": _units(exp),
                            "tripwire": "units fall below %s (%d%% of the retained floor) — organic isn't holding; consider re-enabling ads"
                            % (_units(u * Rt * RETENTION_TRIP), int(RETENTION_TRIP * 100)),
                            "explain": _cell("Expected units · day %d" % d,
                                             "units − (units × (1 − retention)) × ramp",
                                             [("Units now", u, "units"), ("Retention", Rt, "frac"),
                                              ("Ramp fraction", round(rf, 2), "×")], _units(exp))})
    return {"intervention": ("Stop ads on this loss-making SKU — bleed of %s/mo stops immediately. "
            "Organic volume assumed to retain %d%% of ad-driven units." % (_money(S), int(Rt * 100))),
            "projection": proj, "headline": headline, "risks": risks, "monitoring": monitor}


# ------------------------------------------------------------------ FIX MARGIN
def _fix_margin(row, asm):
    price = row.get("price"); u = row.get("units_month"); gcm = (row.get("gcm_pct") or 0) / 100.0
    if not (price and u is not None):
        return {"missing": "price / units for this SKU"}
    inc = asm["price_increase"]; e = asm["elasticity"]; R = asm["ramp_days"]
    new_margin = gcm + inc                                 # margin lifts ~ by the price increase fraction
    units_lost_frac = min(inc * e, 1.0)
    new_units = u * (1 - units_lost_frac)
    base_contrib = round(price * gcm * u, 2)
    new_contrib = round(price * new_margin * new_units, 2)

    def _g(el):                                            # net contribution DELTA at elasticity el
        nu = u * (1 - min(inc * el, 1.0))
        return round(price * new_margin * nu - base_contrib, 2)
    delta = _g(e)                                          # POINT at current elasticity; band ±BAND_E (more elastic ⇒ lower)
    band = {"conservative": _money(_g(min(e + BAND_E, 3.0))), "expected": _money(delta),
            "optimistic": _money(_g(max(e - BAND_E, 0.0)))}
    proj = [
        _row("Net margin %", "%", _pctf(gcm * 100), inc * 100, gcm * 100, _pctf, R,
             "margin lifts by the price-increase fraction (price up, cost flat), ramped",
             lambda h, rf, v: [("Now", round(gcm*100, 1), "%"), ("Price increase", round(inc*100, 1), "%"),
                               ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        _row("Units / mo", "units", _units(u), -(u * units_lost_frac), u, _units, R,
             "units fall by price-increase × elasticity (demand response), ramped",
             lambda h, rf, v: [("Units now", u, "units"), ("Price increase", round(inc*100, 1), "%"),
                               ("Elasticity", e, "e"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Net contribution / mo", "do_nothing": _money(base_contrib),
                "do_this": _money(new_contrib), "delta": _money(delta), "range": band,
                "explain": _cell("Net contribution / mo", "price × new margin × units after elasticity",
                                 [("Price", price, "₹"), ("New margin", round(new_margin*100, 1), "%"),
                                  ("Units after elasticity", round(new_units, 1), "units"),
                                  ("Baseline contribution", base_contrib, "₹")], _money(new_contrib))}
    risks = [
        {"title": "Elasticity worse than assumed", "assumption": "elasticity",
         "magnitude": "each +%g elasticity ≈ %s fewer units/mo" % (MARGIN_RISK_STEP, _units(u * inc * MARGIN_RISK_STEP)),
         "mechanism": "If buyers are more price-sensitive than assumed, volume falls further and the margin lift is eaten."},
    ]
    monitor = []
    for d in CHECKPOINTS:
        rf = _reached(d, R)
        exp = u - (u * units_lost_frac) * rf
        monitor.append({"day": d, "metric": "Units / mo", "expected": _units(exp),
                        "tripwire": "units fall below %s (%d%% of projected) — elasticity worse than modeled; reconsider the price"
                        % (_units(new_units * MARGIN_TRIP), int(MARGIN_TRIP * 100)),
                        "explain": _cell("Expected units · day %d" % d,
                                         "units − (units × price-increase × elasticity) × ramp",
                                         [("Units now", u, "units"), ("Price increase", round(inc*100, 1), "%"),
                                          ("Elasticity", e, "e"), ("Ramp fraction", round(rf, 2), "×")], _units(exp))})
    return {"intervention": ("Raise price ~%d%% (or cut COGS/returns equivalently) to lift margin. Demand "
            "elasticity %.1f means volume falls ~%d%%." % (int(inc*100), e, int(units_lost_frac*100))),
            "projection": proj, "headline": headline, "risks": risks, "monitoring": monitor}


_MODELS = {"FIX ADS": _fix_ads, "SCALE": _scale, "CUT/DIVEST": _cut, "FIX MARGIN": _fix_margin}


def _pa_quality(row, bucket):
    """L1-owned degrade classification for a Profit & Ads row → (sim_quality, reason, null_base). The
    projection still renders (baseline + editable assumptions); the client just pins a caution banner and
    dims a headline built on a null base. Triggers enumerated (non-exhaustive), from the live audit."""
    cmaa_v, un = row.get("cmaa"), row.get("units_month")
    if bucket == "SCALE" and (cmaa_v is None or not un):
        return ("degraded", "this SKU's CMAA can't be computed reliably yet, so the projected gain rests "
                "on an undefined baseline", cmaa_v is None)
    if bucket == "FIX MARGIN" and not un:
        return ("degraded", "this SKU has no recorded sales volume this period, so the projected "
                "contribution is ₹0", True)
    if row.get("cmaa_reliable") is False or row.get("cmaa_held"):
        return ("degraded", "your CMAA for this SKU isn't reliable yet (short or uneven ad window), so "
                "treat the projected gain as directional only", False)
    if bucket in ("FIX ADS", "SCALE") and (row.get("ad_spend") or 0) < AD_MATERIALITY:
        return ("degraded", "ad spend on this SKU is negligible, so there's little to recover or scale", False)
    return ("useful", None, False)


def simulate(row, assumptions=None):
    """Project the row's recommendation. Returns a Simulation dict (can_simulate False + missing when a
    required input is absent — honest-empty, never fabricated; sim_quality 'degraded' + reason when a
    projection is possible but rests on a weak/undefined base)."""
    bucket = row.get("quadrant")
    ident = {"sku": row.get("sku"), "asin": row.get("asin"), "title": row.get("title"), "bucket": bucket,
             "rec_headline": (row.get("recommendation") or {}).get("headline", "")}
    if bucket not in _MODELS:
        base = sc.base_dict(ident)
        return {**base, "can_simulate": False, "missing": "no simulatable recommendation for this bucket"}
    spec = _ASSUMPTIONS.get(bucket, [])
    asm = sc.validate_clamp(spec, assumptions)
    sq, reason, null_base = _pa_quality(row, bucket)
    base = sc.base_dict(ident, (sq, reason))
    m = _MODELS[bucket](row, asm)
    if "missing" not in m and reason and null_base:
        m["headline"]["null_base"] = True                 # client shows "—" for a point built on a null base
    return sc.finalize(base, m, spec, asm, active=(assumptions or {}).get("_preset"))
