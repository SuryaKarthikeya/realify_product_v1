"""Illustrative SAMPLE payload for the Profit & Ads empty state — shown to a CUSTOMER who hasn't yet
supplied the reports that unlock the tab (Sponsored Products + COGS). It renders the full tab so they
see what they'll get, behind an unmistakable 'Sample' banner, and it auto-disappears the moment real
data lands (the API returns sample=False once there's anything to judge). Every SKU here is obviously
fictional ('SAMPLE-…') so it can never be mistaken for the customer's own numbers.

Every derived figure (ACoS, ₹ above break-even, CMAA, scale upside, quadrant) is COMPUTED here by the
same realify.domain.cmaa functions the live tab uses — so the preview is internally consistent (no
'ACoS below break-even yet flagged as overspending' contradictions) and can never drift from the real
math. Only the raw inputs (price/cogs/units, spend/sales, margin floor) are authored.
"""

from . import cmaa, economics, explain

_SKUS = [
    # (sku, title, category, price, cogs, referral, fba, units, spend, sales, floor%, cannibal)
    # Inputs chosen so the COMPUTED quadrant is the intended one — nothing about the verdict is hand-set.
    ("SAMPLE-01", "Sample — Wireless car charger", "Car Chargers",   1299, 520, 195, 120, 380, 8200, 42000,  0, False),  # SCALE  (efficient)
    ("SAMPLE-06", "Sample — Tyre inflator (mini)", "Tyre Care",      2299, 980, 345, 210, 150, 7300, 51000,  0, False),  # SCALE  (efficient)
    ("SAMPLE-02", "Sample — Phone mount (magnetic)", "Phone Mounts",  899, 410, 135,  95, 260, 9900, 22000,  0, True),   # FIX ADS (over break-even)
    ("SAMPLE-03", "Sample — Seat gap organizer", "Car Organizers",    649, 300,  97,  80, 210, 9800, 18000,  0, True),   # FIX ADS (over break-even)
    ("SAMPLE-04", "Sample — Dashboard cam mount", "Phone Mounts",     499, 300,  55,  44, 140,  900,  9000, 25, False),  # FIX MARGIN (ads efficient, 20% margin < 25% floor)
    ("SAMPLE-05", "Sample — LED footwell kit", "Interior Lighting",  1499,1290, 225, 140,  90, 5400,  7200,  0, False),  # CUT/DIVEST (below cost + inefficient)
]


def sample_payload():
    skus = []
    for sku, title, cat, price, cogs, ref, fba, units, spend, sales, floor, cann in _SKUS:
        # per-unit gross contribution the SAME way the SKU tab and live CMAA tab compute it
        gross_unit = economics.per_unit(price, cogs, ref, fba)["gross_contribution_unit"]
        # Illustrative and internally single-period: net_rev, spend and sales all describe ONE period,
        # so CMAA is contribution(one period) − spend(one period) — the period-consistent shape the real
        # tab enforces. By construction sales <= net_rev (an ad window can't out-sell total revenue).
        net_rev = price * units
        # evaluate() takes PER-UNIT revenue (price) so gcm% = per-unit margin — exactly the live tab's
        # call; contribution_after_ads() takes the WINDOW net revenue (price×units) for its % denominator.
        ev = cmaa.evaluate(spend, sales, gross_unit, price, margin_floor=floor / 100.0)
        cm = cmaa.contribution_after_ads(gross_unit, units, spend, net_rev)
        # Same reliability + SCALE gate the live builder applies (sample is single-period & settled, so
        # every row is reliable and no row is gated — but we run it so sample == live logic).
        reliable = cmaa.cmaa_reliable(spend, sales, units, net_rev)
        final_q, held, gate_reason = cmaa.scale_gate(ev["quadrant"], cm["amount"], reliable)
        scale_up = ev["scale_upside"] if (final_q == "SCALE" and not held) else None
        card = {
            "sku": sku, "asin": sku, "title": title, "category": cat, "units_month": units,
            "price": price, "cogs": cogs, "referral_fee": ref, "fba_fee": fba, "margin_floor": floor,
            "gcm_pct": round(ev["gcm_pct"] * 100, 1), "breakeven_acos": round(ev["breakeven_acos"] * 100, 1),
            "ad_spend": spend, "ad_sales": sales,
            "actual_acos": None if ev["actual_acos"] is None else round(ev["actual_acos"] * 100, 1),
            "cmaa": cm["amount"], "cmaa_pct": (None if not reliable else cm["pct"]), "cmaa_denom_est": False,
            "cmaa_reliable": reliable, "cmaa_held": held, "cmaa_window_mismatch": False,
            "scale_gate_reason": gate_reason,
            "above_breakeven": round(ev["wasted_spend"], 2), "scale_upside": scale_up,
            "quadrant": final_q, "margin_certainty": "certain",
            "tacos_trend": "stable", "cannibalization": cann,
            "lifecycle_guarded": False, "lifecycle_note": None, "judged": True, "acted": False,
        }
        card["recommendation"] = cmaa.recommend(card)
        # Same shared producer the live /api/cmaa builder uses — the sample's derivations are identical
        # in shape and computed by the same functions, so the explain toggle behaves the same here.
        card["explain"] = explain.cmaa_parts(card, "₹", {
            "gross_unit": gross_unit, "gc_after_returns": gross_unit,   # sample has no returns
            "cmaa_spend": spend, "cmaa_units": units, "cmaa_net_rev": net_rev,
            "be_spend": round((sales or 0) * ev["breakeven_acos"], 2) if sales else None,
            "incr_sales": round((sales or 0) * (cmaa.SCALE_MAX_MULTIPLE - 1), 2) if sales else None,
            "timeframe": "illustrative sample window", "certainty": "certain",
            "denom_est": False, "max_multiple": cmaa.SCALE_MAX_MULTIPLE,
            "cmaa_reliable": reliable, "cmaa_held": held, "gate_reason": gate_reason,
            "cmaa_window_mismatch": False, "cmaa_tf": "illustrative sample window",
        })
        skus.append(card)
    skus.sort(key=lambda x: x["above_breakeven"], reverse=True)
    quads = {"SCALE": 0, "FIX ADS": 0, "FIX MARGIN": 0, "CUT/DIVEST": 0}
    for s in skus:
        quads[s["quadrant"]] = quads.get(s["quadrant"], 0) + 1
    total_above = sum(s["above_breakeven"] for s in skus)
    tf = "illustrative sample window"
    agg = {
        "total_above_breakeven": explain.aggregate(
            "Recoverable across the portfolio", "max(ad spend − ad sales × break-even ACoS, 0)",
            [(s["sku"], s["above_breakeven"]) for s in skus], timeframe_basis=tf),
        "total_scale_upside": explain.aggregate(
            "Scale upside (directional)",
            f"incremental ad-sales × (break-even − actual ACoS), capped at {cmaa.SCALE_MAX_MULTIPLE:g}× run-rate",
            [(s["sku"], s["scale_upside"]) for s in skus if s["scale_upside"]], timeframe_basis=tf,
            note="Directional — each SKU's upside is a bounded ceiling."),
        "total_cut_bleed": explain.aggregate(
            "Ad bleed you would stop", "ad spend on CUT/DIVEST SKUs (losing on margin and ads)",
            [(s["sku"], s["ad_spend"]) for s in skus if s["quadrant"] == "CUT/DIVEST"], timeframe_basis=tf),
    }
    return {
        "skus": skus,
        "summary": {
            "judged": len(skus), "held_provisional": 0,
            "below_cost": sum(1 for s in skus if s["gcm_pct"] is not None and s["gcm_pct"] < 0),
            "total_above_breakeven": round(total_above, 2), "certain_above_breakeven": round(total_above, 2),
            "estimated_above_breakeven": 0,
            "total_scale_upside": round(sum(s["scale_upside"] or 0 for s in skus), 2),
            "total_cut_bleed": round(sum(s["ad_spend"] for s in skus if s["quadrant"] == "CUT/DIVEST"), 2),
            "quadrants": quads,
            "cannibalization_flags": sum(1 for s in skus if s["cannibalization"]),
            "lifecycle_guarded": 0,
            "portfolio_tacos": {"2026-04-01": 0.081, "2026-05-01": 0.074, "2026-06-01": 0.069},
            "portfolio_tacos_trend": "falling", "explain": agg,
        },
    }
