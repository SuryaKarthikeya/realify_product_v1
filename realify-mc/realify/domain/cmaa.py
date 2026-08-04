"""CMAA — Contribution Margin After Ads.

Pure decision logic: no I/O, no pandas, no app imports. This is the single source of the CMAA
math, shared by the Phase-0 proof harness (`tools/cmaa_poc.py`) today and the in-app detector
later, so the number Autofy is shown and the number the product shows are computed by identical
code.

Core identity (locked in #004): **break-even ACoS = gross contribution margin %.** Ad spend above
that line is *certain* waste. The functions never fabricate: an unknown input returns None and the
caller excludes the row rather than guessing.
"""


def gcm_pct(contribution, net_revenue):
    """Gross contribution margin as a fraction of net revenue. None if revenue is non-positive
    (all-refunded or no sales) or contribution is unknown — undecidable, never assumed."""
    if net_revenue is None or net_revenue <= 0 or contribution is None:
        return None
    return contribution / net_revenue


def breakeven_acos(gcm_pct_val):
    """Break-even ACoS = gross contribution margin %. None if margin is unknown."""
    return gcm_pct_val


def acos(ad_spend, ad_sales):
    """Actual ACoS = spend / attributed sales. None if attributed sales are missing or non-positive
    (undefined/infinite — spending with zero return), or if spend itself is unknown. The <= 0 guard
    (not just falsy) also rejects a negative attributed-sales figure, which is nonsensical for a
    denominator — the caller then shows '—', never a bogus ratio."""
    if ad_spend is None or ad_sales is None or ad_sales <= 0:
        return None
    return ad_spend / ad_sales


def wasted_spend(ad_spend, ad_sales, gcm_pct_val):
    """Ad spend above break-even (the *certain* dollars): max(spend - sales * GCM%, 0).

    If the margin is unknown, this is only computable when there are no attributed sales at all
    (break-even spend is then 0, so every rupee spent is above it). With sales but no margin the
    row is undecidable -> None (caller excludes it)."""
    if ad_spend is None:
        return None
    sales = max(ad_sales or 0.0, 0.0)          # clamp: a negative attributed-sales can't lift break-even
    if gcm_pct_val is None:
        return ad_spend if sales <= 0 else None
    breakeven = sales * gcm_pct_val
    return max(ad_spend - breakeven, 0.0)


# A single SCALE SKU's ad-driven sales can't be scaled without limit — bound the incremental
# ad-sales at this multiple of today's run-rate (2.0 ⇒ "at most double"). Named so the explain
# panel can state the assumption, and so the invariant test (upside ≤ ad-sales headroom) holds.
SCALE_MAX_MULTIPLE = 2.0


def scale_upside(ad_spend, ad_sales, gcm_pct_val, actual_acos, max_multiple=SCALE_MAX_MULTIPLE):
    """DIRECTIONAL, BOUNDED net-new contribution upside for an EFFICIENT (SCALE) SKU.

    The prior method — headroom × (break-even/actual_acos − 1) — was UNBOUNDED: the factor blows up
    as actual_acos → 0, so a very efficient SKU produced upside far exceeding its own revenue (the
    ₹50L-per-SKU / ₹90L-portfolio nonsense). This replaces it with a bounded model:

        incremental_ad_sales = ad_sales × (max_multiple − 1)      (capped headroom — you can't scale
                                                                    one SKU's ad demand without limit)
        upside               = incremental_ad_sales × (break-even ACoS − actual_acos)
                                                                   (contribution per ₹ of incremental
                                                                    ad-sales, at today's efficiency)

    Bounded BY CONSTRUCTION: since (be − actual_acos) < 1, upside < incremental_ad_sales — i.e. the
    per-SKU upside never exceeds its ad-sales headroom. Still DIRECTIONAL (real ACoS rises as you
    scale, so this is an optimistic ceiling) — the caller badges it. `ad_spend` is accepted for the
    caller's explain context (incremental spend ≈ incremental_ad_sales × actual_acos) but not needed
    for the figure. Returns None when undecidable (margin/ACoS/ad-sales unknown or non-positive) or
    not efficient (break-even ≤ actual_acos). Fractions in (0.41), matching the domain layer."""
    if (gcm_pct_val is None or gcm_pct_val <= 0 or actual_acos is None or actual_acos <= 0
            or ad_sales is None or ad_sales <= 0):
        return None
    be = gcm_pct_val
    if be <= actual_acos:                          # not efficient — no scaling upside
        return None
    incremental_ad_sales = ad_sales * (max_multiple - 1)
    upside = incremental_ad_sales * (be - actual_acos)
    return round(upside, 2) if upside > 0 else None


def contribution_after_ads(gross_contribution_unit, units, ad_spend, net_revenue):
    """CMAA — Contribution Margin After Ads — as a currency amount and a % of net revenue.

    amount = (per-unit gross contribution × units) − ad spend
           = revenue − COGS − fees − returns − ad_spend   (the per-unit contribution already nets
             COGS, referral, FBA and returns, per economics.per_unit).

    PERIOD CONSISTENCY (caller's contract): `units`, `ad_spend` and `net_revenue` MUST all cover the
    SAME time window. Pairing a single month's `units` with an `ad_spend` accumulated over several
    months (or a `net_revenue` from a different span) produces a nonsensical figure — the tell is
    ad_sales exceeding `net_revenue`, which cannot happen when both cover one window. This helper does
    no windowing itself; it trusts the caller to pass window-consistent inputs.

    This is the *bottom line after ads* in rupees, distinct from break-even ACoS (= contribution-
    margin %, a pre-ad ratio). Returns {amount, pct} with amount None when the pre-ad contribution or
    the unit count is unknown (never fabricated), and pct None when net revenue is unknown/non-positive.
    ad_spend absent counts as 0 — CMAA with no ads is simply the pre-ad contribution."""
    if gross_contribution_unit is None or units is None:
        return {"amount": None, "pct": None}
    amount = gross_contribution_unit * units - (ad_spend or 0.0)
    pct = (amount / net_revenue * 100) if (net_revenue and net_revenue > 0) else None
    return {"amount": round(amount, 2), "pct": (round(pct, 1) if pct is not None else None)}


def quadrant(gcm_pct_val, actual_acos, be_acos, margin_floor=0.0):
    """The action quadrant for an advertised SKU:
        SCALE       margin ok  & ads ok      -> profitable and efficient; spend more
        FIX ADS     margin ok  & ads not     -> good product, overspending on ads
        FIX MARGIN  margin not & ads ok       -> efficient ads, product barely profits (price/cost)
        CUT/DIVEST  neither                   -> losing on both

    `margin_ok = gcm_pct >= margin_floor` (floor is customer-tunable; default 0 = "profitable at
    all before ads"). `ads_ok = actual_acos <= break-even`. Returns None if margin is unknown
    (undecidable). No attributed sales counts as ads-not-ok (spending, zero return)."""
    if gcm_pct_val is None:
        return None
    margin_ok = gcm_pct_val >= margin_floor
    ads_ok = actual_acos is not None and be_acos is not None and actual_acos <= be_acos
    if margin_ok and ads_ok:
        return "SCALE"
    if margin_ok and not ads_ok:
        return "FIX ADS"
    if not margin_ok and ads_ok:
        return "FIX MARGIN"
    return "CUT/DIVEST"


def evaluate(ad_spend, ad_sales, contribution, net_revenue, margin_floor=0.0):
    """Convenience: run the full per-SKU evaluation from raw economics + ad totals.
    Returns a dict of every derived field, with None where a value is undecidable."""
    g = gcm_pct(contribution, net_revenue)
    be = breakeven_acos(g)
    ac = acos(ad_spend, ad_sales)
    quad = quadrant(g, ac, be, margin_floor)
    return {
        "gcm_pct": g,
        "breakeven_acos": be,
        "actual_acos": ac,
        "wasted_spend": wasted_spend(ad_spend, ad_sales, g),
        "quadrant": quad,
        # Directional scale upside is only meaningful for a SCALE SKU (margin ok AND ads efficient).
        # A below-floor-but-efficient SKU (FIX MARGIN) has headroom too, but scaling ads there is the
        # wrong move — so gate on the quadrant, not just headroom.
        "scale_upside": scale_upside(ad_spend, ad_sales, g, ac) if quad == "SCALE" else None,
    }


# --- CMAA reliability + the SCALE profitability gate (Fix 1 & 3) ---------------------------------
# CMAA = contribution/unit × settled units_in_window − ad spend. When the SETTLED base is tiny next
# to ad activity (few settled units, or ad-attributed sales far above settled revenue), CMAA and its
# % are nonsensical (e.g. −2276.5% off 1 settled unit vs ₹58,971 ad spend). We flag that rather than
# trust the figure, and never call a money-losing or unverifiable SKU "SCALE" (advice that loses money).
CMAA_MATERIAL_SPEND = 1000.0     # ad spend below this is immaterial — CMAA stands regardless
CMAA_MIN_SETTLED_UNITS = 2       # settled units below this, under material spend, is untrustworthy
CMAA_SALES_MULT = 1.5            # ad-attributed sales may exceed settled window revenue by at most this


def cmaa_reliable(ad_spend, ad_sales, settled_units, settled_net_rev):
    """Is CMAA trustworthy for this SKU? UNreliable when ad spend is MATERIAL and the settled base is
    implausibly small relative to ad activity: settled units below the floor, or ad-attributed sales
    exceeding settled window revenue by more than CMAA_SALES_MULT×. True when ad activity is immaterial
    or the settled base can support the figure. (Threshold defaults are tunable — see module consts.)"""
    if not ad_spend or ad_spend < CMAA_MATERIAL_SPEND:
        return True
    if settled_units is not None and settled_units < CMAA_MIN_SETTLED_UNITS:
        return False
    if (settled_net_rev is not None and settled_net_rev > 0 and ad_sales is not None
            and ad_sales > CMAA_SALES_MULT * settled_net_rev):
        return False
    return True


def scale_gate(quadrant_val, cmaa_amount, cmaa_is_reliable):
    """Profitability gate on SCALE. quadrant() already decided ads-efficiency + margin-floor; a
    CONFIDENT scale call additionally requires a trustworthy, non-negative CMAA. Returns
    (final_quadrant, held, reason):
        efficient + reliable + CMAA >= 0  -> SCALE, not held (unchanged)
        efficient + reliable + CMAA <  0  -> FIX MARGIN (losing money after ads — fix economics, don't scale)
        efficient + UNreliable CMAA       -> SCALE but HELD (not a confident call — verify units first)
    Only touches SCALE; every other quadrant passes through unchanged."""
    if quadrant_val != "SCALE":
        return quadrant_val, False, None
    if not cmaa_is_reliable:
        return "SCALE", True, ("CMAA can't be trusted here — settled units lag ad spend — so this isn't a "
                               "confident scale call. Verify settled units before raising budget.")
    if cmaa_amount is not None and cmaa_amount < 0:
        return "FIX MARGIN", False, ("Ads are efficient (ACoS below break-even) but CMAA is negative — "
                                     "you're losing money after ads. Fix unit economics (price / COGS / "
                                     "returns) before scaling; don't raise budget yet.")
    return "SCALE", False, None


# ---- recommended action (explainable, deterministic) ----------------------
_PROBLEM = {"FIX ADS", "FIX MARGIN", "CUT/DIVEST"}


def _inr_group(n):
    """Indian digit grouping (…,##,##,###) for readable ₹ amounts in the recommendation prose,
    matching the table's en-IN formatting. Assumes INR-style grouping (the current marketplace)."""
    n = int(round(n)); neg = n < 0; s = str(abs(n))
    if len(s) <= 3:
        out = s
    else:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        out = ",".join(parts) + "," + tail
    return ("-" if neg else "") + out


def price_for_floor(cogs, referral_fee, fba_fee, margin_floor_pct):
    """Price that would clear the margin floor: unit_cost / (1 - floor). None if COGS is unknown
    (the load-bearing input — never guessed) or the floor is degenerate (>=100%). margin_floor_pct
    is a percentage number (10 => 10%)."""
    if cogs is None:
        return None
    unit_cost = cogs + (referral_fee or 0) + (fba_fee or 0)
    f = (margin_floor_pct or 0) / 100.0
    if f >= 1:
        return None
    return round(unit_cost / (1 - f), 0)


def _evidence(gcm, be, ac, spend, sales, above, est_note, m, p):
    """The number->threshold chain behind the verdict — every line traces to a computed figure."""
    ev = [f"Margin: {p(gcm)}{est_note}" + (" — below cost" if (gcm is not None and gcm < 0) else "")]
    ev.append(f"Break-even ACoS = margin % = {p(be)}")
    if ac is not None:
        ev.append(f"Actual ACoS = ad spend {m(spend)} \u00f7 ad sales {m(sales)} = {p(ac)}")
    elif spend:
        ev.append(f"Ad sales are {m(0)} while {m(spend)} was spent — ACoS is undefined, so all of it is above break-even.")
    if gcm is not None and gcm <= 0 and spend:
        ev.append(f"Margin \u2264 0, so break-even ACoS \u2264 0 — all {m(spend)} of ad spend is above break-even.")
    elif above:
        ev.append(f"Spend above break-even = spend \u2212 (ad sales \u00d7 margin %) = {m(above)}")
    return ev


def recommend(row, symbol="\u20b9"):
    """Deterministic, explainable recommended action for a problem-quadrant SKU.

    Pure: derives only from the figures already computed for the row — the same numbers behind the
    verdict — never a model or a guess. Returns {headline, steps, evidence, recoverable, guarded}
    for FIX ADS / FIX MARGIN / CUT/DIVEST, else None. If the seller has flagged the SKU's lifecycle
    (launch/clearance/…), the guard LEADS and no cut is recommended — stated intent is respected.
    """
    quad = row.get("quadrant")
    if quad not in _PROBLEM and quad != "SCALE":
        return None

    gcm = row.get("gcm_pct"); be = row.get("breakeven_acos"); ac = row.get("actual_acos")
    spend = row.get("ad_spend"); sales = row.get("ad_sales"); above = row.get("above_breakeven")
    floor = row.get("margin_floor") or 0
    est_note = " (rests on estimated inputs)" if row.get("margin_certainty") == "estimated" else ""

    def m(x):
        return f"{symbol}{_inr_group(x)}" if x is not None else "n/a"
    p = lambda x: f"{x:.1f}%" if x is not None else "undefined"
    evidence = _evidence(gcm, be, ac, spend, sales, above, est_note, m, p)

    if quad == "SCALE" and row.get("cmaa_held"):
        # Efficient on ads, but CMAA rests on a settled base too small to trust — held, NOT scaled.
        ev = list(evidence)
        ev.append(f"Ads are efficient (ACoS {p(ac)} ≤ break-even {p(be)}), but CMAA ({m(row.get('cmaa'))}) "
                  f"rests on too few settled units vs ad spend to trust — held, not a scale call.")
        return {
            "guarded": False, "held": True,
            "headline": "Efficient on ads, but CMAA is unreliable — verify settled units before scaling.",
            "steps": [
                "Don't raise budget yet — settled units are too few relative to ad spend to trust the "
                "after-ads margin (CMAA).",
                "Confirm settled units/revenue for this SKU; once the settled base catches up it re-judges "
                "as SCALE or FIX MARGIN on real economics.",
            ],
            "evidence": ev, "recoverable": None, "upside": None,
        }

    if quad == "SCALE":
        # The one non-problem action: efficient SKU with room to spend more. The upside is DIRECTIONAL
        # and BOUNDED (incremental ad-sales capped at a multiple of today's run-rate) — the flag lets
        # the UI badge it, and the number is the L1 scale_upside on the row, never re-derived client-side.
        up = row.get("scale_upside")
        ev = list(evidence)
        if up:
            ev.append(f"Directional upside = incremental ad-sales (capped at "
                      f"{SCALE_MAX_MULTIPLE:g}× today's run-rate) × (break-even {p(be)} − ACoS {p(ac)}) "
                      f"= {m(up)} (bounded estimate — not settled like the recoverable figure).")
        return {
            "guarded": False, "directional": True,
            "headline": f"Efficient — room to scale. ACoS {p(ac)} is below your {p(be)} break-even.",
            "steps": [
                f"Raise budget or bids while ACoS stays at or below break-even ({p(be)}) — you're under "
                f"it now, so there's profitable room.",
                (f"Directional upside from growing ad-sales up to {SCALE_MAX_MULTIPLE:g}× at today's "
                 f"efficiency: {m(up)}. It's a bounded estimate — ACoS rises as you scale, so step up "
                 f"gradually and watch it."
                 if up else
                 "Step budget up gradually and hold ACoS at or below break-even."),
            ],
            "evidence": ev, "recoverable": None, "upside": up,
        }

    if row.get("lifecycle_guarded"):
        note = row.get("lifecycle_note") or "flagged lifecycle"
        return {
            "guarded": True,
            "headline": f"You flagged this SKU — {note}. Profit & Ads isn't treating it as a problem.",
            "steps": [
                "No action recommended while the lifecycle flag stands — this spend/margin is intentional.",
                "Figures are shown so you can watch it; clear the lifecycle flag on the SKU tab to have it judged normally.",
            ],
            "evidence": evidence, "recoverable": None,
        }

    pff = price_for_floor(row.get("cogs"), row.get("referral_fee"), row.get("fba_fee"), floor)

    if quad == "FIX ADS":
        steps = [
            f"Lower bids or pause non-converting terms until ACoS is at or below your break-even of {p(be)} "
            f"(break-even ACoS = your {p(gcm)} margin).",
            f"Spend above break-even right now is {m(above)} — that's what cutting to break-even recovers.",
        ]
        if row.get("cannibalization"):
            steps.append(
                "Buy Box and ad share are both high, so some ad sales may be organic demand you'd keep without "
                "ads — true recoverable may be higher. Trim spend and watch total units to test.")
        return {
            "guarded": False,
            "headline": f"Good product, overspending on ads — bring ACoS from {p(ac)} down to {p(be)}.",
            "steps": steps, "evidence": evidence, "recoverable": above or None,
        }

    if quad == "FIX MARGIN" and row.get("scale_gate_reason"):
        # Demoted from SCALE by the profitability gate: ads efficient, margin fine pre-ads, but CMAA<0.
        # The problem is after-ads economics, NOT a below-floor pre-ad margin — so give a distinct action.
        ev = list(evidence)
        ev.append(f"Ads are efficient (ACoS {p(ac)} ≤ break-even {p(be)}) but CMAA is negative "
                  f"({m(row.get('cmaa'))}) — you lose money after ads.")
        return {
            "guarded": False,
            "headline": "Efficient on ads, but losing money after ads (CMAA < 0) — fix the economics, don't scale.",
            "steps": [
                # NB: don't cite price_for_floor here — the margin already clears its floor (this was a
                # SCALE candidate); the gap is AFTER ad spend, a different (un-computed) breakeven price.
                "Raise price or cut COGS / fees / returns so the SKU clears its costs AFTER ad spend, "
                "not just its pre-ad margin.",
                "Do NOT raise ad budget yet — spending more efficiently on a unit that loses money after "
                "ads just loses money faster.",
            ],
            "evidence": ev, "recoverable": None,
        }

    if quad == "FIX MARGIN":
        lift = (f"Raise price to about {m(pff)}, or cut COGS/fees, to lift margin above your {floor:.0f}% floor."
                if pff is not None else
                f"Lift margin above your {floor:.0f}% floor by raising price or cutting COGS/fees "
                f"(add COGS on the SKU tab to size the exact price).")
        return {
            "guarded": False,
            "headline": f"Ads are efficient — the margin is the problem ({p(gcm)}, below your {floor:.0f}% floor).",
            "steps": [
                lift,
                f"Ads are already efficient (ACoS {p(ac)} \u2264 break-even {p(be)}) — the fix is unit economics, "
                f"not ad spend. Don't cut ads.",
            ],
            "evidence": evidence, "recoverable": None,
        }

    # CUT/DIVEST
    steps = [
        (f"Fix the unit economics first: raise price to about {m(pff)} (or cut COGS/fees) to clear your "
         f"{floor:.0f}% floor. Ads can't rescue a unit that loses money before ad spend."
         if pff is not None else
         "Fix the unit economics first — ads can't rescue a unit that loses money before ad spend. "
         "Add COGS on the SKU tab to size the price that would clear your floor.")
    ]
    if spend:
        steps.append(f"If price/cost can't move, stop ads here — saves {m(spend)}/period — and let it sell "
                     f"organically or wind it down.")
    return {
        "guarded": False,
        "headline": "Losing on both margin and ads — fix the economics or stop spending.",
        "steps": steps, "evidence": evidence, "recoverable": above or None,
    }
