"""Flow SIMULATE models — ads / cash / conversion / concentration, all over own L1 data.

TACOS-ARREST  — tacos: pull TACoS to the tenant's ceiling; project spend saved net of held sales.
RETURNS-REDUCTION — returns-rate: cut returns toward the tenant's ceiling; refund cost recovered.
CVR-LIFT      — conversion: lift CVR to the tenant's line; incremental units × unit contribution.
CONCENTRATION — revenue-share: this card's action is "diversify" (no direct lever), so we simulate the
                RISK honestly — if this SKU's sales drop X%, the portfolio revenue/contribution at risk.
"""
from . import sim_common as sc

AD_MATERIALITY = 100.0    # ₹/mo ad spend below which there's nothing material to arrest


# --------------------------------------------------------------- TACOS-ARREST
def tacos_arrest(ctx, assumptions):
    r = ctx["row"]
    price = r.get("price"); un = r.get("units_month"); tacos = r.get("tacos")
    margin = (r.get("net_margin_pct") or 0) / 100.0
    if not (price and un) or tacos is None:
        return {"missing": "price / units / TACoS for this SKU"}
    sales = price * un
    target = ctx.get("threshold") or 14.0                  # tenant TACoS ceiling
    spend_now = tacos / 100.0 * sales
    saved = round(max(0.0, (tacos - target) / 100.0 * sales), 2)
    spec = [
        ("target_tacos", round(target, 1), 2.0, 50.0, "%", "TACoS you're pulling spend efficiency down to.",
         sc.src_line(ctx, "TACoS ceiling"), (round(target + 3, 1), round(target, 1), round(max(target - 3, 2), 1))),
        ("organic_hold", 0.70, 0.0, 1.0, "frac", "Share of the trimmed ad-sales that hold organically.",
         "conservative constant (category norm ~0.6–0.8)", (0.50, 0.70, 0.90)),
        ("ramp_days", 60, 21, 120, "days", "Days for the spend change to reach steady state.",
         "conservative constant", (90, 60, 45)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    tgt = asm["target_tacos"]; H = asm["organic_hold"]; R = asm["ramp_days"]
    saved = round(max(0.0, (tacos - tgt) / 100.0 * sales), 2)
    bought = (saved / (tacos / 100.0)) if tacos else 0.0   # sales attributable to the trimmed spend (spend ÷ TACoS)

    def _gain(hh):
        return round(min(max(saved - (1 - hh) * bought * margin, 0.0), saved), 2)
    gain = _gain(H)
    band = sc.band(_gain, H, 0.0, 1.0, 0.20)
    proj = [
        sc.row("TACoS", "%", sc.pctf(tacos), tgt - tacos, tacos, sc.pctf, R,
               "TACoS ramps down toward your ceiling as spend efficiency improves",
               lambda h, rf, v: [("Now", round(tacos, 1), "%"), ("Target", round(tgt, 1), "%"),
                                 ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        sc.row("Monthly contribution gain", "₹", sc.money(0), gain, 0.0, sc.money, R,
               "spend saved − (1−organic_hold) × ad-sales bought by that spend × margin, ramped",
               lambda h, rf, v: [("Spend saved", saved, "₹"), ("Organic-hold", H, "frac"),
                                 ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Monthly contribution gain from arresting TACoS", "do_nothing": sc.money(0),
                "do_this": sc.money(gain), "delta": sc.money(gain), "range": band,
                "explain": sc.cell("Contribution gain / mo", "spend saved − (1−organic_hold) × attributable sales × margin",
                                   [("Spend saved", saved, "₹"), ("Organic-hold", H, "frac"),
                                    ("Attributable sales (spend ÷ TACoS)", round(bought, 2), "₹"),
                                    ("Margin", round(margin * 100, 1), "%")], sc.money(gain))}
    risks = [
        {"title": "Trimmed sales don't hold organically", "assumption": "organic_hold",
         "magnitude": _money_at_risk(saved, bought, margin, H),
         "mechanism": "If the ad-sales you cut were incremental (not organic), you lose that contribution."},
        {"title": "Cutting spend costs rank", "assumption": "organic_hold", "magnitude": None,
         "mechanism": "Lower ad presence can erode organic rank, compounding the volume loss."},
    ]
    monitor = _tacos_monitor(tacos, tgt, R)
    reason = None
    if spend_now < AD_MATERIALITY:
        reason = "ad spend on this SKU is negligible, so there's little TACoS to arrest"
    elif tacos <= target:
        reason = "TACoS is already at or under your ceiling, so there's no excess spend to trim"
    return {"spec": spec, "asm": asm, "degraded_reason": reason,
            "intervention": ("Trim spend/negative-target the wasteful terms so TACoS falls from %s to your "
                             "%s ceiling — ~%s/mo of spend, %d%% of it assumed to hold organically."
                             % (sc.pctf(tacos), sc.pctf(tgt), sc.money(saved), int(H * 100))),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}


def _money_at_risk(saved, bought, margin, H):
    return sc.money(round((1 - H) * bought * margin, 2)) + "/mo of contribution at risk"


def _tacos_monitor(tacos, tgt, R):
    out = []
    for d in sc.CHECKPOINTS:
        rf = sc.reached(d, R)
        exp = tacos + (tgt - tacos) * rf
        out.append(sc.monitor_line(d, "TACoS", sc.pctf(exp),
                   "TACoS not falling toward %s — the spend trim isn't taking; revisit the campaigns" % sc.pctf(tgt),
                   sc.cell("Expected TACoS · day %d" % d, "TACoS + (target − TACoS) × ramp fraction",
                           [("Now", round(tacos, 1), "%"), ("Target", round(tgt, 1), "%"),
                            ("Ramp fraction", round(rf, 2), "×")], sc.pctf(exp))))
    return out


# --------------------------------------------------------------- RETURNS-REDUCTION
def returns_reduction(ctx, assumptions):
    r = ctx["row"]
    un = r.get("units_month"); rr = r.get("returns_rate"); cu = sc.contrib_unit(r)
    rcu = r.get("return_cost_unit") or 0.0
    if not un or rr is None or cu is None:
        return {"missing": "units / returns rate / unit economics for this SKU"}
    ceiling = ctx.get("threshold") or 8.0                  # tenant returns-rate ceiling
    cost_per_return = round(cu + rcu, 2)                   # contribution lost + reverse-logistics handling
    spec = [
        ("target_return_rate", round(ceiling, 1), 0.0, 40.0, "%", "Return rate the fix brings you down to.",
         sc.src_line(ctx, "returns-rate ceiling"),
         (round(min(rr, ceiling + 2), 1), round(ceiling, 1), round(max(ceiling - 2, 0), 1))),
        ("fix_ramp_days", 45, 14, 120, "days", "Days for the listing/quality fix to move the return rate.",
         "conservative constant", (60, 45, 30)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    tgt = asm["target_return_rate"]; R = asm["fix_ramp_days"]

    def _recovered(t):
        return round(max(0.0, (rr - t) / 100.0 * un) * cost_per_return, 2)
    recovered = _recovered(tgt)
    band = sc.band(_recovered, tgt, 0.0, 40.0, 2.0, decreasing=True)  # a higher target recovers less
    proj = [
        sc.row("Return rate", "%", sc.pctf(rr), tgt - rr, rr, sc.pctf, R,
               "return rate ramps down toward your ceiling as the fix lands",
               lambda h, rf, v: [("Now", round(rr, 1), "%"), ("Target", round(tgt, 1), "%"),
                                 ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        sc.row("Refund cost recovered / mo", "₹", sc.money(0), recovered, 0.0, sc.money, R,
               "returns avoided × (unit contribution + handling), ramped",
               lambda h, rf, v: [("Returns avoided / mo", round(max(0.0, (rr - tgt) / 100.0 * un), 1), "units"),
                                 ("Cost per return", cost_per_return, "₹"),
                                 ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Refund cost recovered / mo", "do_nothing": sc.money(0), "do_this": sc.money(recovered),
                "delta": sc.money(recovered), "range": band,
                "explain": sc.cell("Refund cost recovered / mo", "(return rate − target) × units × cost per return",
                                   [("Return rate", round(rr, 1), "%"), ("Target", round(tgt, 1), "%"),
                                    ("Units / mo", un, "units"), ("Cost per return", cost_per_return, "₹")],
                                   sc.money(recovered))}
    risks = [
        {"title": "Root cause isn't fixable by the listing", "assumption": "target_return_rate", "magnitude": None,
         "mechanism": "If returns stem from a product defect, listing/packaging changes won't hit the target."},
        {"title": "Returns lag the fix", "assumption": "fix_ramp_days", "magnitude": None,
         "mechanism": "In-flight orders keep returning at the old rate for weeks — recovery ramps slowly."},
    ]
    monitor = [sc.monitor_line(d, "Return rate", sc.pctf(rr + (tgt - rr) * sc.reached(d, R)),
               "return rate not trending toward %s by day 30 — the fix isn't working; re-diagnose" % sc.pctf(tgt),
               sc.cell("Expected return rate · day %d" % d, "rate + (target − rate) × ramp fraction",
                       [("Now", round(rr, 1), "%"), ("Target", round(tgt, 1), "%"),
                        ("Ramp fraction", round(sc.reached(d, R), 2), "×")],
                       sc.pctf(rr + (tgt - rr) * sc.reached(d, R)))) for d in sc.CHECKPOINTS]
    reason = "return rate is already at or under your ceiling — little to recover" if rr <= ceiling else None
    return {"spec": spec, "asm": asm, "degraded_reason": reason,
            "intervention": ("Fix the return driver (listing accuracy, packaging, sizing) to bring returns from "
                             "%s toward your %s ceiling — ~%s/mo of refund cost recovered."
                             % (sc.pctf(rr), sc.pctf(tgt), sc.money(recovered))),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}


# --------------------------------------------------------------- CVR-LIFT
def cvr_lift(ctx, assumptions):
    r = ctx["row"]
    sessions = r.get("sessions"); cvr = r.get("conversion_pct"); cu = sc.contrib_unit(r)
    if sessions is None or cvr is None or cu is None:
        return {"missing": "conversion inputs (sessions / CVR) aren't on file for this SKU"}
    line = ctx.get("threshold") or 9.0                     # tenant conversion line
    spec = [
        ("target_cvr", round(line, 1), 0.0, 40.0, "%", "Conversion rate the listing fix lifts you to.",
         sc.src_line(ctx, "conversion line"),
         (round(max(cvr, line - 1.5), 1), round(line, 1), round(line + 1.5, 1))),
        ("sessions_held_pct", 100.0, 20.0, 150.0, "%", "Share of today's sessions you keep after the change.",
         "conservative constant (100% = sessions unchanged)", (85.0, 100.0, 110.0)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    tgt = asm["target_cvr"]; held = asm["sessions_held_pct"] / 100.0
    units_now = sessions * cvr / 100.0

    def _gain(t):
        return round(max(0.0, sessions * held * t / 100.0 - units_now) * cu, 2)
    gain = _gain(tgt)
    band = sc.band(_gain, tgt, 0.0, 40.0, 1.5)
    proj = [
        sc.row("Conversion", "%", sc.pctf(cvr), tgt - cvr, cvr, sc.pctf, 45,
               "conversion ramps toward your line as the content/price fix lands",
               lambda h, rf, v: [("Now", round(cvr, 1), "%"), ("Target", round(tgt, 1), "%"),
                                 ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
        sc.row("Contribution gain / mo", "₹", sc.money(0), gain, 0.0, sc.money, 45,
               "(sessions × held × target CVR − current units) × unit contribution, ramped",
               lambda h, rf, v: [("Sessions", round(sessions), ""), ("Target CVR", round(tgt, 1), "%"),
                                 ("Unit contribution", cu, "₹"), ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Contribution gain / mo from lifting conversion", "do_nothing": sc.money(0),
                "do_this": sc.money(gain), "delta": sc.money(gain), "range": band,
                "explain": sc.cell("Contribution gain / mo", "(sessions × held × target CVR − current units) × unit contribution",
                                   [("Sessions", round(sessions), ""), ("Current CVR", round(cvr, 1), "%"),
                                    ("Target CVR", round(tgt, 1), "%"), ("Unit contribution", cu, "₹")], sc.money(gain))}
    risks = [
        {"title": "Sessions fall as you change price/content", "assumption": "sessions_held_pct", "magnitude": None,
         "mechanism": "A price rise or content edit can cost traffic — fewer sessions offsets the CVR lift."},
        {"title": "The CVR lift doesn't materialize", "assumption": "target_cvr", "magnitude": None,
         "mechanism": "Reaching your line assumes the fix addresses the real conversion blocker."},
    ]
    monitor = [sc.monitor_line(d, "Conversion", sc.pctf(cvr + (tgt - cvr) * sc.reached(d, 45)),
               "conversion not climbing toward %s (and sessions holding) — the fix isn't landing" % sc.pctf(tgt),
               sc.cell("Expected conversion · day %d" % d, "CVR + (target − CVR) × ramp fraction",
                       [("Now", round(cvr, 1), "%"), ("Target", round(tgt, 1), "%"),
                        ("Ramp fraction", round(sc.reached(d, 45), 2), "×")],
                       sc.pctf(cvr + (tgt - cvr) * sc.reached(d, 45)))) for d in sc.CHECKPOINTS]
    reason = "conversion is already at or above your line — little headroom to capture" if cvr >= line else None
    return {"spec": spec, "asm": asm, "degraded_reason": reason,
            "intervention": ("Fix the listing (images/A+/price/reviews) to lift conversion from %s to your %s line — "
                             "~%s/mo of contribution at today's sessions." % (sc.pctf(cvr), sc.pctf(line), sc.money(gain))),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}


# --------------------------------------------------------------- CONCENTRATION STRESS-TEST
def concentration(ctx, assumptions):
    r = ctx["row"]
    share = r.get("rev_share_pct"); margin = (r.get("net_margin_pct") or 0) / 100.0
    this_rev = (r.get("annual_rev_inr") / 12.0) if r.get("annual_rev_inr") else (
        (r.get("price") or 0) * (r.get("units_month") or 0) or None)
    if share is None or not this_rev:
        return {"missing": "revenue share / monthly revenue for this SKU"}
    portfolio = ctx.get("portfolio_rev") or (this_rev / (share / 100.0) if share else None)
    spec = [
        ("shock_pct", 20.0, 0.0, 100.0, "%", "Hypothetical drop in this SKU's sales to stress-test.",
         "conservative constant (20% shock)", (30.0, 20.0, 10.0)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    shock = asm["shock_pct"]

    def _rev_risk(s):
        return round(this_rev * s / 100.0, 2)

    def _contrib_risk(s):                                  # the headline is CONTRIBUTION at risk — band matches it
        return round(this_rev * s / 100.0 * margin, 2)
    rev_risk = _rev_risk(shock)
    contrib_risk = _contrib_risk(shock)
    band = sc.band(_contrib_risk, shock, 0.0, 100.0, 10.0)
    impact_pct = round(rev_risk / portfolio * 100.0, 1) if portfolio else None
    proj = [
        {"metric": "Portfolio revenue at risk (cumulative)", "unit": "₹", "now": sc.money(0), "do_nothing": sc.money(0),
         "cells": [{"horizon": h, "reached": 1.0,
                    "part": sc.cell("Revenue at risk · day %d" % h, "this SKU's revenue × shock × (days ÷ 30)",
                                    [("Monthly revenue", round(this_rev, 2), "₹"), ("Shock", round(shock, 1), "%"),
                                     ("Days", h, "")], sc.money(round(rev_risk * h / 30.0, 2)))} for h in sc.HORIZONS]},
        {"metric": "Contribution at risk (cumulative)", "unit": "₹", "now": sc.money(0), "do_nothing": sc.money(0),
         "cells": [{"horizon": h, "reached": 1.0,
                    "part": sc.cell("Contribution at risk · day %d" % h, "revenue at risk × margin",
                                    [("Revenue at risk", round(rev_risk * h / 30.0, 2), "₹"),
                                     ("Margin", round(margin * 100, 1), "%")],
                                    sc.money(round(contrib_risk * h / 30.0, 2)))} for h in sc.HORIZONS]},
    ]
    headline = {"label": "Monthly contribution at risk from this concentration", "do_nothing": sc.money(contrib_risk),
                "do_this": sc.money(0), "delta": sc.money(contrib_risk), "range": band,
                "explain": sc.cell("Contribution at risk / mo", "this SKU's revenue × shock × margin",
                                   [("Monthly revenue", round(this_rev, 2), "₹"), ("Shock", round(shock, 1), "%"),
                                    ("Margin", round(margin * 100, 1), "%"),
                                    ("Portfolio impact", impact_pct if impact_pct is not None else 0, "%")],
                                   sc.money(contrib_risk))}
    risks = [
        {"title": "Over-reliance on one SKU", "assumption": "shock_pct",
         "magnitude": ("%s%% of portfolio revenue rides on this SKU" % round(share, 1)),
         "mechanism": "A stockout, suspension, or competitor hit here flows straight to the portfolio total."},
        {"title": "Diversification takes time", "assumption": None, "magnitude": None,
         "mechanism": "Standing up alternative SKUs/channels is a multi-month effort — the exposure persists meanwhile."},
    ]
    monitor = [sc.monitor_line(d, "Revenue share", sc.pctf(share),
               "share climbs above %s — concentration risk rising; accelerate diversification" % sc.pctf(share + 2),
               sc.cell("Revenue share · day %d" % d, "this SKU's revenue ÷ portfolio revenue (watch the trend)",
                       [("Share now", round(share, 1), "%")], sc.pctf(share))) for d in sc.CHECKPOINTS]
    return {"spec": spec, "asm": asm, "degraded_reason": None,
            "intervention": ("This SKU carries %s of your revenue. Stress-test: a %d%% sales drop puts ~%s/mo of "
                             "contribution at risk. Diversify to reduce the single-SKU dependency."
                             % (sc.pctf(share), int(shock), sc.money(contrib_risk))),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}
