"""Shared explainability-parts producer — the ONE canonical shape for a calculated number's
derivation, consumed by the SAME front-end explain panel (toggle + ⓘ icon + panel) that cards use.

Pure: no I/O, no app imports. A `part` is:

    { label, formula, inputs:[{label, value, unit}], result, provenance, timeframe_basis }

and an `aggregate` additionally carries `n` + `top` (top contributors) with
`formula = "Σ of N SKUs · per-SKU: <per-SKU formula>"`. The front-end renders both with one
primitive, so the card path and the /api/cmaa builder emit the identical shape — no parallel
mechanism. A number that cannot produce a derivation must emit NOTHING here (the caller sets the
field to None and the UI renders honest-empty regardless of the explain toggle).
"""


def _inp(x):
    """Normalize an input to {label, value, unit}. Accepts a (label, value[, unit]) tuple or a dict."""
    if isinstance(x, dict):
        return {"label": x.get("label"), "value": x.get("value"), "unit": x.get("unit")}
    label, value, unit = (list(x) + [None])[:3]
    return {"label": label, "value": value, "unit": unit}


def part(label, formula, inputs, result, provenance=None, timeframe_basis=None, note=None):
    """One calculated number's derivation. `inputs` is a list of (label, value, unit) tuples (or
    dicts). `formula` is the human-readable expression; `result` is the plugged-in output. Returns
    None only if the caller passes result=None with no formula — otherwise always renders."""
    return {
        "label": label,
        "formula": formula,
        "inputs": [_inp(i) for i in (inputs or [])],
        "result": result,
        "provenance": list(provenance or []),
        "timeframe_basis": timeframe_basis,
        "note": note,
    }


def aggregate(label, per_formula, contributors, unit="₹", provenance=None,
              timeframe_basis=None, top_n=3, note=None):
    """Aggregate derivation: the sum of N per-SKU values. `contributors` is a list of
    (sku_label, value) pairs. Renders as "Σ of N SKUs · per-SKU: <formula>" with the running total
    and the top contributors — the same shape a per-SKU `part` uses, so one renderer covers both."""
    vals = [(lbl, v) for (lbl, v) in contributors if v]
    total = round(sum(v for _, v in vals), 2)
    top = sorted(vals, key=lambda kv: -abs(kv[1]))[:top_n]
    return {
        "label": label,
        "formula": f"Σ of {len(vals)} SKUs · per-SKU: {per_formula}",
        "inputs": [{"label": lbl, "value": round(v, 2), "unit": unit} for lbl, v in top],
        "result": total,
        "n": len(vals),
        "top": [{"label": lbl, "value": round(v, 2)} for lbl, v in top],
        "provenance": list(provenance or []),
        "timeframe_basis": timeframe_basis,
        "note": note,
    }


def cmaa_parts(card, sym, ctx):
    """Every calculated Profit & Ads number for ONE SKU, in the shared shape — the single producer
    used by BOTH the /api/cmaa builder and the empty-state sample, so they emit identical derivations.
    `ctx` carries the intermediates the caller already computed:
        gross_unit, gc_after_returns, cmaa_spend, cmaa_units, cmaa_net_rev, be_spend, incr_sales,
        timeframe, certainty, denom_est, max_multiple.
    Every figure the worklist shows has an entry; a number that can't be derived is simply absent
    (the UI renders honest-empty). Returns None when the SKU isn't judged."""
    if not card.get("judged"):
        return None
    g = ctx.get
    prov = [f"margin inputs · {ctx.get('certainty')}", "ad totals · Sponsored Products report"]
    tf = ctx.get("timeframe")
    cnote = ("CMAA % denominator is a monthly estimate — no per-period revenue on file for this SKU."
             if ctx.get("denom_est") else None)
    mult = ctx.get("max_multiple") or 2.0
    ex = {"breakeven_acos": part(
            "Break-even ACoS (= gross contribution margin %)",
            "(price − COGS − referral fee − FBA fee) ÷ price",
            [("Price", card.get("price"), sym), ("COGS", card.get("cogs"), sym),
             ("Referral fee", card.get("referral_fee"), sym), ("FBA fee", card.get("fba_fee"), sym),
             ("Gross contribution / unit",
              round(g("gross_unit"), 2) if g("gross_unit") is not None else None, sym)],
            card.get("breakeven_acos"), prov),
          "recoverable": part(
            "Recoverable (₹ above break-even)",
            "max(ad spend − ad sales × break-even ACoS, 0)",
            [("Ad spend", card.get("ad_spend"), sym), ("Ad sales", card.get("ad_sales"), sym),
             ("Break-even ACoS", card.get("breakeven_acos"), "%"),
             ("Break-even spend (ad sales × break-even)", g("be_spend"), sym)],
            card.get("above_breakeven"), prov, tf),
          "ad_spend": part(
            "Ad spend (bleed you stop if CUT/DIVEST)",
            "Sponsored Products ad spend summed over the window; for a CUT/DIVEST SKU it's the bleed "
            "pulling ads stops (can't be tuned to break-even — margin is at/below zero)",
            [("Ad spend", card.get("ad_spend"), sym)], card.get("ad_spend"), prov, tf)}
    if card.get("actual_acos") is not None:
        ex["actual_acos"] = part(
            "Actual ACoS", "ad spend ÷ ad sales",
            [("Ad spend", card.get("ad_spend"), sym), ("Ad sales", card.get("ad_sales"), sym)],
            card.get("actual_acos"), prov, tf)
    reliable = ctx.get("cmaa_reliable", True)
    cmaa_tf = ctx.get("cmaa_tf") or tf
    if card.get("cmaa") is not None:
        # CMAA note surfaces (in priority) an unreliable settled base, a window basis mismatch, or the
        # monthly-fallback denominator — so the toggle explains exactly why the figure is caveated.
        if not reliable:
            cn = ("CMAA is UNRELIABLE here — settled units (" + str(g("cmaa_units")) + ") lag the ad "
                  "spend, so both the after-ads margin and its % rest on too small a settled base to "
                  "trust. The % is held; verify settled units.")
        elif ctx.get("cmaa_window_mismatch"):
            cn = (f"CMAA spans {cmaa_tf} — only the periods with settled units — a SHORTER window than "
                  f"the recoverable/upside figures (the full ad-report window). Read them on different bases.")
        else:
            cn = cnote
        ex["cmaa"] = part(
            "CMAA (Contribution Margin After Ads, ₹)",
            "gross contribution / unit (incl. returns) × units in window − ad spend (same window)",
            [("Gross contribution / unit (incl. returns)",
              round(g("gc_after_returns"), 2) if g("gc_after_returns") is not None else None, sym),
             ("Units in window", g("cmaa_units"), "u"),
             ("Ad spend" + (" (monthly est.)" if ctx.get("denom_est") else " (settled window)"),
              round(g("cmaa_spend"), 2) if g("cmaa_spend") is not None else None, sym)],
            card.get("cmaa"), prov, cmaa_tf, note=cn)
        if card.get("cmaa_pct") is not None:      # held (None) when unreliable — no % part is emitted
            ex["cmaa_pct"] = part(
                "CMAA % (of net revenue)", "CMAA ÷ net revenue (same window)",
                [("CMAA", card.get("cmaa"), sym),
                 ("Net revenue (window)",
                  round(g("cmaa_net_rev"), 2) if g("cmaa_net_rev") else None, sym)],
                card.get("cmaa_pct"), prov, cmaa_tf, note=cnote)
    # classification: when the SCALE gate held or demoted the SKU, explain the efficient ACoS AND the
    # negative/untrustworthy CMAA that gated it (a held/flagged state is itself explainable).
    reason = ctx.get("gate_reason")
    if reason or ctx.get("cmaa_held"):
        ex["classification"] = part(
            "Why this isn't a clean SCALE",
            "confident SCALE requires ads-efficient (ACoS ≤ break-even) AND trustworthy CMAA AND CMAA ≥ 0",
            [("Actual ACoS", card.get("actual_acos"), "%"),
             ("Break-even ACoS", card.get("breakeven_acos"), "%"),
             ("CMAA", card.get("cmaa"), sym),
             ("CMAA reliable?", "yes" if reliable else "no", None)],
            card.get("quadrant"), prov, cmaa_tf,
            note=reason or "CMAA unreliable — held, not a confident scale call.")
    if card.get("scale_upside"):
        ex["scale_upside"] = part(
            "Scale upside (directional, bounded)",
            f"incremental ad-sales × (break-even ACoS − actual ACoS); "
            f"incremental ad-sales = ad-sales × ({mult:g}× − 1)",
            [("Ad sales (run-rate)", card.get("ad_sales"), sym),
             ("Max scale multiple", mult, "×"),
             ("Incremental ad-sales (capped)", g("incr_sales"), sym),
             ("Break-even ACoS", card.get("breakeven_acos"), "%"),
             ("Actual ACoS", card.get("actual_acos"), "%")],
            card.get("scale_upside"), prov, tf,
            note="Directional ceiling — real ACoS rises as you scale, so treat it as an upper bound.")
    return ex


def window_basis(periods):
    """A human timeframe label from the period keys the ad totals span (the single basis every CMAA
    number is aggregated over). None-safe → 'your full ad-report window' when unknown."""
    ps = sorted(p for p in (periods or []) if p)
    if not ps:
        return "your full ad-report window"
    n = len(ps)
    span = ps[0] if n == 1 else f"{ps[0]} → {ps[-1]}"
    return f"{span} · {n} period{'s' if n != 1 else ''}"
