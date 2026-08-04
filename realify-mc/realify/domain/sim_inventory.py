"""Inventory / demand-capture SIMULATE models (own-data arithmetic — the exemplary clean case).

REORDER      — days-of-cover / seasonal-cover / stock-level: reorder N units, project cover + the
               contribution protected from a stockout, warn on overstock (cash trapped).
DEMAND-CAPTURE — velocity / rank-movement: a demand surge; project the run-rate contribution and the
               slice at risk if you stock out before restocking.
Both are pure own-data: stock on hand, daily velocity, and the tenant's own unit economics.
"""
from . import sim_common as sc

HORIZON = 90              # projection window (days) the protected-contribution math spans
OVERSTOCK_DAYS = 150      # cover above this after a reorder = cash trapped in inventory (warn)


# --------------------------------------------------------------- REORDER
def reorder(ctx, assumptions):
    r = ctx["row"]
    stock = r.get("stock_on_hand"); vel = r.get("velocity_day"); cu = sc.contrib_unit(r)
    if not vel or stock is None or cu is None:
        return {"missing": "stock on hand / daily velocity / unit economics for this SKU"}
    cover_line = ctx.get("threshold") or 21                # tenant days-of-cover line (target)
    cover_now = stock / vel
    tgt_qty = max(round(vel * cover_line - stock), 0)      # units to reach the cover line
    spec = [
        ("reorder_qty", tgt_qty, 0, max(round(vel * 365), 1), "units", "Units to reorder now.",
         "qty to reach %s (%d days)" % (sc.src_line(ctx, "days-of-cover line"), cover_line),
         (max(round(tgt_qty * 0.6), 0), tgt_qty, round(tgt_qty * 1.5))),
        ("lead_time_days", 14, 1, 90, "days", "Days from placing the PO to receiving stock.",
         "labeled constant (14 days)", (21, 14, 7)),
        ("expected_velocity", round(vel, 2), 0.0, round(vel * 4, 2) or 1.0, "u/day",
         "Daily sales you expect to sustain through the lead time.", "your current velocity",
         (round(vel * 0.7, 2), round(vel, 2), round(vel * 1.3, 2))),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    q = asm["reorder_qty"]; lt = asm["lead_time_days"]; v = asm["expected_velocity"] or vel

    lost_units = v * max(0.0, HORIZON - stock / v)         # units lost to a 90-day stockout at expected velocity
    def _protected(qq):                                    # ₹ contribution kept — capped by what you actually reorder
        return round(min(lost_units, qq) * cu, 2)
    protected = _protected(q)
    band = sc.band(_protected, q, 0.0, max(round(vel * 365), 1.0), max(round(q * 0.4), 1.0))
    cover_after = (stock + q) / v
    proj = [
        {"metric": "Days of cover", "unit": "days", "now": sc.days(cover_now), "do_nothing": sc.days(cover_now),
         "cells": [{"horizon": h, "reached": 1.0,
                    "part": sc.cell("Days of cover · day %d" % h, "current cover − days elapsed (do nothing)",
                                    [("Cover now", round(cover_now, 1), "days"), ("Days elapsed", h, "days")],
                                    sc.days(max(0.0, cover_now - h)),
                                    note=("Stockout around day %d if you don't reorder." % int(cover_now))
                                    if cover_now < HORIZON else None)} for h in sc.HORIZONS]},
        sc.row("Contribution protected", "₹", sc.money(0), protected, 0.0, sc.money, lt,
               "min(units lost to stockout, reorder qty) × unit contribution, ramped as stock arrives",
               lambda h, rf, val: [("Reorder qty", q, "units"), ("Unit contribution", cu, "₹"),
                                   ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    headline = {"label": "Contribution protected by reordering now (90d)", "do_nothing": sc.money(0),
                "do_this": sc.money(protected), "delta": sc.money(protected), "range": band,
                "explain": sc.cell("Contribution protected", "min(units lost to stockout, reorder qty) × unit contribution",
                                   [("Cover now", round(cover_now, 1), "days"), ("Velocity", round(v, 2), "u/day"),
                                    ("Reorder qty", q, "units"), ("Unit contribution", cu, "₹")], sc.money(protected))}
    risks = [
        {"title": "Demand shifts during the lead time", "assumption": "expected_velocity", "magnitude": None,
         "mechanism": "If velocity fades before stock lands you protect less; what you can protect is capped by the reorder quantity."},
        {"title": "Lead time slips", "assumption": "lead_time_days", "magnitude": None,
         "mechanism": "A late PO means the stockout still happens — the protection assumes on-time receipt."},
    ]
    monitor = [sc.monitor_line(d, "Days of cover", sc.days(max(0.0, cover_now - d)),
               "cover falls below the lead time (%d days) — place the PO now or you'll stock out" % int(lt),
               sc.cell("Expected cover · day %d" % d, "current cover − days elapsed",
                       [("Cover now", round(cover_now, 1), "days"), ("Days elapsed", d, "days")],
                       sc.days(max(0.0, cover_now - d)))) for d in sc.CHECKPOINTS]
    reason = None
    if cover_now >= HORIZON:
        reason = ("you already hold %d days of cover — there's no near-term stockout to avert, so the "
                  "protected figure is ₹0" % int(cover_now))
    elif cover_after > OVERSTOCK_DAYS:
        reason = ("this reorder quantity lifts cover to ~%d days (over the %d-day overstock line) — cash "
                  "would sit trapped in inventory; consider a smaller order" % (int(cover_after), OVERSTOCK_DAYS))
    return {"spec": spec, "asm": asm, "degraded_reason": reason,
            "intervention": ("Reorder ~%d units to lift days-of-cover from %d to your %d-day line before a "
                             "stockout costs you sales." % (int(q), int(cover_now), int(cover_line))),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}


# --------------------------------------------------------------- DEMAND-CAPTURE
def demand_capture(ctx, assumptions):
    r = ctx["row"]
    vel = r.get("velocity_day"); price = r.get("price"); cu = sc.contrib_unit(r)
    if not vel or price is None or cu is None:
        return {"missing": "daily velocity / price / unit economics for this SKU"}
    stock = r.get("stock_on_hand")
    spec = [
        ("sustained_velocity", round(vel, 2), 0.0, round(vel * 4, 2) or 1.0, "u/day",
         "Daily sales you expect this surge to sustain.", "your current velocity",
         (round(vel * 0.7, 2), round(vel, 2), round(vel * 1.3, 2))),
        ("lead_time_days", 14, 1, 90, "days", "Days to get more stock in if you need to restock.",
         "labeled constant (14 days)", (21, 14, 7)),
    ]
    asm = sc.validate_clamp(spec, assumptions)
    v = asm["sustained_velocity"] or vel
    monthly = round(v * 30 * cu, 2)                        # contribution/mo at the sustained run-rate
    cover_now = (stock / v) if stock else None

    def _at_risk(vv):                                      # contribution lost to a stockout over the month
        if not stock:
            return 0.0
        kept_days = min(stock / vv, 30.0)
        return round(vv * cu * (30.0 - kept_days), 2)
    at_risk = _at_risk(v)
    band = sc.band(_at_risk, v, 0.01, round(vel * 4, 2) or 1.0, round(vel * 0.3, 2) or 0.1)
    proj = [
        sc.row("Contribution / mo at run-rate", "₹", sc.money(round(vel * 30 * cu, 2)),
               monthly - round(vel * 30 * cu, 2), round(vel * 30 * cu, 2), sc.money, 30,
               "sustained velocity × 30 × unit contribution",
               lambda h, rf, val: [("Velocity", round(v, 2), "u/day"), ("Unit contribution", cu, "₹"),
                                   ("Ramp fraction (day %d)" % h, round(rf, 2), "×")]),
    ]
    if stock:
        proj.append({"metric": "Days of cover", "unit": "days", "now": sc.days(cover_now),
                     "do_nothing": sc.days(cover_now),
                     "cells": [{"horizon": h, "reached": 1.0,
                                "part": sc.cell("Days of cover · day %d" % h, "stock ÷ velocity − days elapsed",
                                                [("Cover now", round(cover_now, 1), "days"), ("Days elapsed", h, "days")],
                                                sc.days(max(0.0, cover_now - h)))} for h in sc.HORIZONS]})
    headline = {"label": "Contribution at risk if the surge stocks out (per mo)", "do_nothing": sc.money(at_risk),
                "do_this": sc.money(0), "delta": sc.money(at_risk), "range": band,
                "explain": sc.cell("Contribution at risk", "velocity × unit contribution × days out of stock this month",
                                   [("Velocity", round(v, 2), "u/day"), ("Unit contribution", cu, "₹"),
                                    ("Cover now", round(cover_now, 1) if cover_now else 0, "days")], sc.money(at_risk))}
    risks = [
        {"title": "The surge fades", "assumption": "sustained_velocity", "magnitude": None,
         "mechanism": "A rank/seasonal spike can revert; sustaining supply for demand that doesn't last ties up cash."},
        {"title": "Stockout mid-surge", "assumption": "lead_time_days",
         "magnitude": (sc.money(at_risk) + "/mo at risk") if stock else None,
         "mechanism": "Running out during the surge hands the demand to competitors and can cost rank."},
    ]
    vstr = "%.1f u/day" % v
    monitor = [sc.monitor_line(d, "Velocity", vstr,
               "velocity drops below %.1f u/day — the surge is fading; hold off on further restock" % (vel * 0.8),
               sc.cell("Expected velocity · day %d" % d, "assumed sustained velocity (watch vs actual)",
                       [("Sustained velocity", round(v, 2), "u/day")], vstr)) for d in sc.CHECKPOINTS]
    reason = None if stock else "no stock-on-hand on file for this SKU, so the stockout risk can't be quantified"
    return {"spec": spec, "asm": asm, "degraded_reason": reason,
            "intervention": ("Sustain supply for the demand surge (~%s/mo of contribution at this run-rate). "
                             "Keep stock ahead of velocity so you don't hand the surge to competitors." % sc.money(monthly)),
            "headline": headline, "projection": proj, "risks": risks, "monitoring": monitor}
