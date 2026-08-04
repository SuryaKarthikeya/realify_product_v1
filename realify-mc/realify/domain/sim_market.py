"""Margin / pricing / competitive / reviews / opportunity SIMULATE models.

FIX-ECONOMICS   — margin-vs-floor & margin-headroom: raise price (± cut COGS/returns) vs elasticity.
BUY-BOX-REGAIN  — buy-box-ownership: lift win-rate to the tenant's line; sales follow BB share.
PRICE-RESPONSE  — price-competitiveness (C1): respond to an undercut vs hold; heavily range-based.
competition_density — C2: NO own-data lever → disclaimer + monitoring plan only (never a fabricated number).
REVIEW-RECOVERY — rating / review-count: gated on conversion data (the rating→sales link is the softest
                  assumption in the product); wide range, degraded, or honest-empty when no CVR on file.
GAP-CAPTURE     — opportunity / assortment-breadth: capture a share of a stated gap at an est. margin.
"""
from . import sim_common as sc

BB_FLOOR, BB_CAP = 20.0, 1.0    # Buy-Box sales-follow: floor the ratio denominator + cap incremental units at +100%


# --------------------------------------------------------------- FIX-ECONOMICS
def fix_economics(ctx, assumptions):
    r = ctx["row"]
    price = r.get("price"); u = r.get("units_month"); gcm = (r.get("net_margin_pct") or 0) / 100.0
    if not price or u is None:
        return {"missing": "price / units for this SKU"}
    headroom = ctx.get("op") == "gt"                       # margin-headroom (already above the line)
    floor = ctx.get("threshold")
    gap = max(0.0, (floor - r.get("net_margin_pct", 0)) / 100.0) if (floor is not None and not headroom) else 0.05
    spec = [
        ("price_change_pct", round(gap or 0.05, 3), 0.0, 0.40, "frac", "Price increase applied to lift margin.",
         ("gap to %s" % sc.src_line(ctx, "margin floor")) if not headroom else "conservative constant (~5%)",
         (round((gap or 0.05) * 0.6, 3), round(gap or 0.05, 3), round((gap or 0.05) * 1.4, 3))),
        ("demand_elasticity", 1.2, 0.0, 3.0, "e", "% units lost per % price up (>1 = elastic).",
         "conservative constant", (1.6, 1.2, 0.8)),
        ("cogs_change_pct", 0.0, 0.0, 0.30, "frac", "Margin points added by cutting COGS (no demand effect).",
         "labeled constant (0 = price-only)", (0.0, 0.0, 0.05)),
        ("returns_change_pct", 0.0, 0.0, 0.20, "frac", "Margin points added by cutting returns (no demand effect).",
         "labeled constant (0 = price-only)", (0.0, 0.0, 0.03)),
        ("ramp_days", 45, 14, 120, "days", "Days for demand to settle after the change.",
         "conservative constant", (60, 45, 30)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    inc = asm["price_change_pct"]; e = asm["demand_elasticity"]; R = asm["ramp_days"]
    new_margin = gcm + inc + asm["cogs_change_pct"] + asm["returns_change_pct"]
    base_contrib = round(price * gcm * u, 2)

    def _delta(el):
        nu = u * (1 - min(inc * el, 1.0))
        return round(price * new_margin * nu - base_contrib, 2)
    delta = _delta(e)
    new_units = u * (1 - min(inc * e, 1.0))
    band = sc.band(_delta, e, 0.0, 3.0, 0.40, decreasing=True)
    proj = [
        sc.row("Net margin %", "%", sc.pctf(gcm * 100), (new_margin - gcm) * 100, gcm * 100, sc.pctf, R,
               "margin lifts by price increase + COGS/returns cuts (cost side), ramped",
               lambda h, rf, v: [("Now", round(gcm * 100, 1), "%"), ("Price increase", round(inc * 100, 1), "%"),
                                 ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        sc.row("Units / mo", "units", sc.units(u), -(u * min(inc * e, 1.0)), u, sc.units, R,
               "units fall by price increase × elasticity (demand response), ramped",
               lambda h, rf, v: [("Units now", u, "units"), ("Price increase", round(inc * 100, 1), "%"),
                                 ("Elasticity", e, "e"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Net contribution gain / mo", "do_nothing": sc.money(0), "do_this": sc.money(delta),
                "delta": sc.money(delta), "range": band,
                "explain": sc.cell("Net contribution gain / mo", "price × new margin × units after elasticity − baseline",
                                   [("Price", price, "₹"), ("New margin", round(new_margin * 100, 1), "%"),
                                    ("Units after elasticity", round(new_units, 1), "units"),
                                    ("Baseline contribution", base_contrib, "₹")], sc.money(delta))}
    risks = [
        {"title": "Elasticity worse than assumed", "assumption": "demand_elasticity",
         "magnitude": "each +0.4 elasticity ≈ %s fewer units/mo" % sc.units(u * inc * 0.4),
         "mechanism": "If buyers are more price-sensitive than assumed, volume falls further and the lift is eaten."},
        {"title": "Buy Box loss on a price rise", "assumption": "price_change_pct", "magnitude": None,
         "mechanism": "Pricing above competitors can cost the Buy Box — check the Buy-Box detector alongside this."},
    ]
    monitor = [sc.monitor_line(d, "Units / mo", sc.units(u - (u * min(inc * e, 1.0)) * sc.reached(d, R)),
               "units fall below %s (90%% of projected) — elasticity worse than modeled; reconsider the price"
               % sc.units(new_units * 0.9),
               sc.cell("Expected units · day %d" % d, "units − (units × price-increase × elasticity) × ramp",
                       [("Units now", u, "units"), ("Price increase", round(inc * 100, 1), "%"),
                        ("Elasticity", e, "e"), ("Ramp fraction", round(sc.reached(d, R), 2), "×")],
                       sc.units(u - (u * min(inc * e, 1.0)) * sc.reached(d, R)))) for d in sc.CHECKPOINTS]
    reason = "this SKU has no recorded sales volume this period, so the projected contribution is ₹0" if not u else None
    verb = "capture pricing headroom" if headroom else "lift margin toward your floor"
    return {"spec": spec, "asm": asm, "degraded_reason": reason,
            "intervention": ("Raise price ~%d%% (or cut COGS/returns) to %s. Elasticity %.1f means volume falls ~%d%%."
                             % (int(inc * 100), verb, e, int(min(inc * e, 1.0) * 100))),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}


# --------------------------------------------------------------- BUY-BOX-REGAIN
def buybox_regain(ctx, assumptions):
    r = ctx["row"]
    bb = r.get("buybox_pct"); price = r.get("price"); u = r.get("units_month")
    gcm = (r.get("net_margin_pct") or 0) / 100.0
    if bb is None or not price or u is None:
        return {"missing": "Buy Box % / price / units for this SKU"}
    line = ctx.get("threshold") or 80.0
    spec = [
        ("buy_box_target_pct", round(line, 1), 40.0, 100.0, "%", "Buy Box win-rate you're recovering to.",
         sc.src_line(ctx, "Buy Box line"), (round(max(bb, line - 10), 1), round(line, 1), round(min(line + 10, 100), 1))),
        ("price_change_pct", 0.0, 0.0, 0.20, "frac", "Price cut used to win the Buy Box (lowers margin).",
         "conservative constant (0 = non-price fix)", (0.05, 0.02, 0.0)),
        ("bb_to_sales_factor", 1.0, 0.2, 1.5, "×", "How proportionally sales follow Buy Box share (1 = fully).",
         "labeled directional constant", (0.7, 1.0, 1.2)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    tgt = asm["buy_box_target_pct"]; pc = asm["price_change_pct"]; f = asm["bb_to_sales_factor"]
    cu_now = round(price * gcm, 2)

    def _recovery(factor):   # bounded sales-follow: floor the ratio denominator + cap the uplift at +100%
        return min(max(0.0, tgt - bb) / max(bb, BB_FLOOR) * factor, BB_CAP)

    def _gain(factor):
        cu_new = round(price * (gcm - pc), 2)              # new price − cogs (cogs fixed; a pc cut drops margin by pc)
        return round(u * (1 + _recovery(factor)) * cu_new - u * cu_now, 2)
    gain = _gain(f)
    band = sc.band(_gain, f, 0.2, 1.5, 0.3)
    new_units = u * (1 + _recovery(f))
    proj = [
        sc.row("Buy Box %", "%", sc.pctf(bb), tgt - bb, bb, sc.pctf, 30,
               "Buy Box win-rate ramps toward your line as the fix lands",
               lambda h, rf, v: [("Now", round(bb, 1), "%"), ("Target", round(tgt, 1), "%"),
                                 ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        sc.row("Contribution gain / mo", "₹", sc.money(0), gain, 0.0, sc.money, 30,
               "units scaled by Buy Box recovery × new unit contribution − baseline, ramped",
               lambda h, rf, v: [("Units now", u, "units"), ("BB recovery", round((tgt - bb), 1), "pts"),
                                 ("Sales factor", f, "×"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Contribution gain / mo from regaining Buy Box", "do_nothing": sc.money(0),
                "do_this": sc.money(gain), "delta": sc.money(gain), "range": band,
                "explain": sc.cell("Contribution gain / mo", "units × (1 + BB recovery × sales factor) × new unit contribution − baseline",
                                   [("Now BB", round(bb, 1), "%"), ("Target BB", round(tgt, 1), "%"),
                                    ("Sales factor", f, "×"), ("Unit contribution", cu_now, "₹")], sc.money(gain))}
    risks = [
        {"title": "Price cut erodes margin faster than volume gained", "assumption": "price_change_pct", "magnitude": None,
         "mechanism": "Winning the Buy Box by cutting price can lose more on margin than it gains on units."},
        {"title": "Competitor re-undercuts", "assumption": "bb_to_sales_factor", "magnitude": None,
         "mechanism": "A price-based BB win invites a counter-move; the recovery may not hold."},
    ]
    monitor = [sc.monitor_line(d, "Buy Box %", sc.pctf(bb + (tgt - bb) * sc.reached(d, 30)),
               "Buy Box not recovering toward %s by day 15 — the fix isn't working; re-check price/fulfillment" % sc.pctf(tgt),
               sc.cell("Expected Buy Box · day %d" % d, "BB + (target − BB) × ramp fraction",
                       [("Now", round(bb, 1), "%"), ("Target", round(tgt, 1), "%"),
                        ("Ramp fraction", round(sc.reached(d, 30), 2), "×")],
                       sc.pctf(bb + (tgt - bb) * sc.reached(d, 30)))) for d in sc.CHECKPOINTS]
    reason = ("Buy Box is already at or above your line — little to regain" if bb >= line
              else ("Buy Box (%s) is too low to project how reliably sales follow a recovery" % sc.pctf(bb)
                    if bb < BB_FLOOR else None))
    return {"spec": spec, "asm": asm, "degraded_reason": reason,
            "intervention": ("Win the Buy Box back from %s toward your %s line (price/fulfillment/health). Sales are "
                             "assumed to follow BB share at %.1f×." % (sc.pctf(bb), sc.pctf(line), f)),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}


# --------------------------------------------------------------- PRICE-RESPONSE (C1)
def price_response(ctx, assumptions):
    r = ctx["row"]
    price = r.get("price"); u = r.get("units_month"); gcm = (r.get("net_margin_pct") or 0) / 100.0
    if not price or u is None:
        return {"missing": "price / units for this SKU"}
    spec = [
        ("price_response_pct", 0.03, 0.0, 0.30, "frac", "Price cut to close (part of) the competitor gap.",
         "conservative constant (~3%)", (0.05, 0.03, 0.01)),
        ("units_retained_if_no_action_pct", 70.0, 0.0, 100.0, "%",
         "Units you keep if you DON'T respond (the honest unknown — competitor pull).",
         "conservative constant · directional", (55.0, 70.0, 90.0)),
        ("demand_elasticity", 1.5, 0.0, 3.0, "e", "% units gained per % price cut when you respond.",
         "conservative constant", (1.0, 1.5, 2.0)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    pc = asm["price_response_pct"]; ret = asm["units_retained_if_no_action_pct"] / 100.0; e = asm["demand_elasticity"]
    cu_now = round(price * gcm, 2)
    do_nothing = round(u * ret * cu_now, 2)                # keep price, lose share at the retained rate

    def _respond(retention):                               # respond: cut price, regain units at lower margin
        new_units = u * min(1.0 + pc * e, 1.0 / max(ret, 1e-9))
        cu_new = round(price * (gcm - pc), 2)              # new price − cogs (cogs fixed; the cut drops margin by pc)
        return round(new_units * cu_new, 2)
    respond = _respond(ret)
    delta = round(respond - do_nothing, 2)
    band = sc.band(lambda rr: round(_respond(rr) - round(u * rr * cu_now, 2), 2), ret, 0.0, 1.0, 0.15, decreasing=True)
    proj = [
        sc.row("Contribution / mo (respond)", "₹", sc.money(round(u * cu_now, 2)), respond - round(u * cu_now, 2),
               round(u * cu_now, 2), sc.money, 30, "units after price response × new unit contribution",
               lambda h, rf, v: [("Price cut", round(pc * 100, 1), "%"), ("Elasticity", e, "e"),
                                 ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Contribution vs doing nothing / mo", "do_nothing": sc.money(do_nothing),
                "do_this": sc.money(respond), "delta": sc.money(delta), "range": band,
                "explain": sc.cell("Respond − do-nothing / mo", "units after response × new contribution − units retained × current contribution",
                                   [("Price cut", round(pc * 100, 1), "%"), ("Retained if no action", round(ret * 100, 1), "%"),
                                    ("Elasticity", e, "e"), ("Unit contribution", cu_now, "₹")], sc.money(delta))}
    risks = [
        {"title": "Competitor reaction is not your data", "assumption": "units_retained_if_no_action_pct", "magnitude": None,
         "mechanism": "How much share you'd lose without acting is a guess — this whole projection is directional."},
        {"title": "Price war spiral", "assumption": "price_response_pct", "magnitude": None,
         "mechanism": "Matching a cut can trigger a further undercut, eroding margin across the category."},
    ]
    monitor = [sc.monitor_line(d, "Units / mo", sc.units(u),
               "units keep sliding despite the response — the competitor is pulling share; re-evaluate the gap",
               sc.cell("Watch units · day %d" % d, "actual units vs the response assumption (directional)",
                       [("Units now", u, "units")], sc.units(u))) for d in sc.CHECKPOINTS]
    reason = ("competitor price/gap isn't on file for this SKU, so retention is a stated assumption — treat this "
              "as directional only")
    return {"spec": spec, "asm": asm, "degraded_reason": reason,
            "intervention": ("Respond to the undercut with a ~%d%% price move vs holding. Do-nothing assumes you keep "
                             "%d%% of units as share erodes — competitor reaction is not your data, so this is directional."
                             % (int(pc * 100), int(ret * 100))),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}


# --------------------------------------------------------------- competition-density (C2): disclaimer only
def competition_density(ctx, assumptions):
    r = ctx["row"]
    watch = []
    for d in sc.CHECKPOINTS:
        watch.append(sc.monitor_line(d, "Share · Buy Box · price", "watch for movement",
                     "share or Buy Box drops, or you're forced to discount — the entrant is taking hold; act then",
                     sc.cell("What to watch · day %d" % d, "monitor own-data signals a new entrant would move first",
                             [("Buy Box now", round(r.get("buybox_pct") or 0, 1), "%"),
                              ("Revenue share", round(r.get("rev_share_pct") or 0, 1), "%")], "watch for movement")))
    return {"disclaimer_only": True,
            "degraded_reason": ("a new-entrant signal has no direct action to project — watch share, Buy Box, and price "
                                "over the next 30 days"),
            "missing": "a new-entrant signal has no direct action to project",
            "intervention": ("A new competitor entered this space. There's no own-data lever to simulate yet — the value "
                             "here is the watch plan below."),
            "monitoring": watch}


# --------------------------------------------------------------- REVIEW-RECOVERY (gated)
def review_recovery(ctx, assumptions):
    r = ctx["row"]
    rating = r.get("rating"); sessions = r.get("sessions"); cvr = r.get("conversion_pct"); cu = sc.contrib_unit(r)
    if sessions is None or cvr is None or cu is None:
        return {"missing": "rating-to-sales impact can't be projected from your data yet (no conversion data on file)"}
    base_rating = rating if rating is not None else 4.0
    spec = [
        ("rating_target", round(min(base_rating + 0.3, 5.0), 1), 1.0, 5.0, "★", "Rating you aim to recover to.",
         "current + 0.3 (conservative)", (round(min(base_rating + 0.1, 5.0), 1), round(min(base_rating + 0.3, 5.0), 1),
                                          round(min(base_rating + 0.5, 5.0), 1))),
        ("cvr_sensitivity", 1.5, 0.0, 5.0, "%/★", "CVR points gained per rating point (SOFT — rating→sales is weak).",
         "soft assumption · clearly labeled", (0.8, 1.5, 2.5)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    tgt = asm["rating_target"]; sens = asm["cvr_sensitivity"]

    def _gain(s):
        new_cvr = cvr + max(0.0, tgt - base_rating) * s
        return round(max(0.0, sessions * (new_cvr - cvr) / 100.0) * cu, 2)
    gain = _gain(sens)
    band = sc.band(_gain, sens, 0.0, 5.0, 1.0)             # wide by design — the soft assumption
    proj = [
        sc.row("Contribution gain / mo", "₹", sc.money(0), gain, 0.0, sc.money, 60,
               "sessions × (rating lift × CVR-sensitivity) × unit contribution, ramped — WIDE range (soft link)",
               lambda h, rf, v: [("Sessions", round(sessions), ""), ("Rating lift", round(max(0.0, tgt - base_rating), 1), "★"),
                                 ("CVR sensitivity", sens, "%/★"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Contribution gain / mo from rating recovery (wide range)", "do_nothing": sc.money(0),
                "do_this": sc.money(gain), "delta": sc.money(gain), "range": band,
                "explain": sc.cell("Contribution gain / mo", "sessions × rating-lift × CVR-sensitivity × unit contribution",
                                   [("Sessions", round(sessions), ""), ("Rating", round(base_rating, 1), "★"),
                                    ("Target", round(tgt, 1), "★"), ("CVR sensitivity", sens, "%/★")], sc.money(gain))}
    risks = [
        {"title": "The rating→sales link is weak", "assumption": "cvr_sensitivity", "magnitude": None,
         "mechanism": "Rating may not move conversion at all — this is the softest assumption in the product; treat as directional."},
        {"title": "Rating recovery is slow", "assumption": "rating_target", "magnitude": None,
         "mechanism": "New reviews dilute the average slowly — the lift, if real, takes months."},
    ]
    monitor = [sc.monitor_line(d, "Rating / CVR", "%s / %s" % (sc.pctf(base_rating).replace("%", "★"), sc.pctf(cvr)),
               "rating recovers but CVR doesn't follow — the rating→sales assumption isn't holding; stop projecting gains",
               sc.cell("Watch rating & CVR · day %d" % d, "track whether CVR actually moves with rating",
                       [("Rating", round(base_rating, 1), "★"), ("CVR", round(cvr, 1), "%")],
                       "%.1f★ / %s" % (base_rating, sc.pctf(cvr)))) for d in sc.CHECKPOINTS]
    return {"spec": spec, "asm": asm,
            "degraded_reason": ("the rating→sales link is the softest assumption in the product — this is a wide, "
                                "directional range, never a confident point"),
            "intervention": ("Recover rating from %.1f★ toward %.1f★ (fix the driver, generate reviews). The CVR uplift "
                             "is a SOFT assumption — the range is deliberately wide." % (base_rating, tgt)),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}


# --------------------------------------------------------------- GAP-CAPTURE
def gap_capture(ctx, assumptions):
    gap = ctx.get("exposure_inr")
    if not gap:
        return {"missing": "the opportunity/gap value for this card isn't quantified yet"}
    r = ctx["row"]
    est_margin = r.get("net_margin_pct") if r.get("net_margin_pct") else 20.0    # category-median margin not on file
    est_src = ("this SKU's net margin (category-median not on file)" if r.get("net_margin_pct")
               else "labeled constant (20% — category-median margin not on file)")
    spec = [
        ("capture_pct", 10.0, 0.0, 100.0, "%", "Share of the gap you expect to capture.",
         "conservative constant (10%)", (5.0, 10.0, 20.0)),
        ("est_margin_pct", round(est_margin, 1), 0.0, 80.0, "%", "Estimated margin on the captured revenue.",
         est_src, (round(est_margin * 0.7, 1), round(est_margin, 1), round(est_margin * 1.2, 1))),
        ("ramp_days", 90, 30, 240, "days", "Launch ramp to reach the captured run-rate (longer than ad levers).",
         "conservative constant (90d launch)", (150, 90, 60)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    cap = asm["capture_pct"] / 100.0; em = asm["est_margin_pct"] / 100.0; R = asm["ramp_days"]

    def _contrib(c):
        return round(gap * c * em, 2)
    contrib = _contrib(cap)
    band = sc.band(_contrib, cap, 0.0, 1.0, 0.05)
    proj = [
        sc.row("Contribution from captured gap / mo", "₹", sc.money(0), contrib, 0.0, sc.money, R,
               "gap value × capture share × est. margin, ramped over the launch",
               lambda h, rf, v: [("Gap value / mo", round(gap, 2), "₹"), ("Capture", round(cap * 100, 1), "%"),
                                 ("Est. margin", round(em * 100, 1), "%"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Contribution from capturing the gap / mo", "do_nothing": sc.money(0),
                "do_this": sc.money(contrib), "delta": sc.money(contrib), "range": band,
                "explain": sc.cell("Contribution from gap / mo", "gap value × capture share × est. margin",
                                   [("Gap value / mo", round(gap, 2), "₹"), ("Capture", round(cap * 100, 1), "%"),
                                    ("Est. margin", round(em * 100, 1), "%")], sc.money(contrib),
                                   prov=["estimate · directional (the gap itself is an estimate)"])}
    risks = [
        {"title": "Entry costs not modeled", "assumption": "capture_pct", "magnitude": None,
         "mechanism": "Launch ads, inventory, and content spend aren't in this figure — net capture is lower."},
        {"title": "Capture slower/smaller than assumed", "assumption": "capture_pct", "magnitude": None,
         "mechanism": "A new listing ramps slowly and may take less of the gap than 10%."},
    ]
    monitor = [sc.monitor_line(d, "New-SKU velocity", "vs assumption",
               "capture tracking below the assumed share by day 60 — re-scope or exit the opportunity",
               sc.cell("Watch capture · day %d" % d, "new listing velocity vs the capture assumption",
                       [("Capture assumed", round(cap * 100, 1), "%")], "vs assumption")) for d in sc.CHECKPOINTS]
    return {"spec": spec, "asm": asm,
            "degraded_reason": "the gap and its margin are estimates — this is directional, and entry costs aren't modeled",
            "intervention": ("Enter/extend assortment to capture ~%d%% of a ~%s/mo gap at ~%d%% margin. Directional — the "
                             "gap and entry costs are estimates." % (int(cap * 100), sc.money(gap), int(em * 100))),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}
