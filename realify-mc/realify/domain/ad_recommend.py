"""Prescriptive Fix-Ads payload (spec A6) — the recommendation structure SHARED by Part A (deliver as
instruction + deep link) and Part B (execute on one click). Nothing here executes; it emits Actions, each
stamped with its lever's action_class (read from ad_levers — the hard boundary, never hardcoded). A given
Action is REALIFY_ACTIONABLE only if its lever is one of the three; everything else is ADVISORY_ONLY and
carries no executable value (change.type == ADVISORY_TEXT).

Deep-link honesty: a CSV export carries campaign/ad-group NAMES, not Amazon entity IDs, so a link can only
open the campaign manager — the exact entity is named in the instruction. Part B (API) fills the *_id
fields under the same target_ref shape and deep-links to the exact entity.
"""
from realify.domain import ad_levers as LV
from realify.domain import formula_registry as FR
from realify.domain import ad_simulate as AS

ADS_CONSOLE = "https://advertising.amazon.com/cb/campaigns"   # SP campaign manager (name-scoped for CSV)

BID_DOWN_PCT = -0.30          # starting bid reduction (reports carry no current bid; % is the honest ask)
REMOVE_MULT = 2.0             # ACOS beyond this multiple of break-even -> bid-down won't save it
TOP_OFFENDERS = 3             # cap actions to the worst-N campaigns so the panel stays actionable


def _deep_link(target_ref):
    return ADS_CONSOLE        # CSV: campaign named in the instruction; API (Part B) → exact-entity link


def _action(lever_id, target_ref, change, rationale, est_impact):
    return {"lever_id": lever_id, "action_class": LV.action_class_of(lever_id),
            "target_ref": target_ref, "change": change, "rationale": rationale,
            "deep_link": _deep_link(target_ref), "est_impact": round(est_impact or 0.0, 2)}


def _ref(sku, campaign=None, ad_group=None, target=None, asin=None):
    # Shared A/B shape: *_id are None from CSV; Part B fills them from the API under the same keys.
    return {"campaign_id": None, "campaign": campaign, "ad_group_id": None, "ad_group": ad_group,
            "target_id": None, "target": target, "asin": asin, "sku": sku}


def _pct(x):
    return "—" if x is None else f"{round(x * 100)}%"


_FIDELITY_LABEL = {"KEYWORD": "keyword-level", "CAMPAIGN_SKU": "campaign-level"}


def _projection(recoverable_monthly, coverage_pct, fidelity):
    """Default 30/60/90 projection at the starting bid ask — behind the deterministic project() seam
    (domain/ad_simulate). Re-simulate re-invokes the same seam with the customer's edited params."""
    return AS.project(recoverable_monthly, coverage_pct, fidelity)


def _why(be, current, offending, coverage_pct):
    top = offending[:2]
    share = round(sum(c.get("spend_share", 0) for c in top) * 100)
    camp_note = (f"Campaigns {', '.join(c['campaign'] for c in top)} are ~{share}% of its ad spend and "
                 "both sit above break-even." if top else "")
    unmapped = round(100 - coverage_pct) if coverage_pct is not None else None
    unmapped_note = (f"{unmapped}% of spend is on unmapped search terms and is excluded from the fix."
                     if unmapped else "")
    return {"break_even_acos": be, "current_acos": current,
            "derivation": "contribution ÷ net settled revenue, from your COGS",
            "campaigns_note": camp_note, "unmapped_note": unmapped_note}


def _formulas(context, diagnosis, be, recoverable, coverage_pct):
    """Every header/footer number the modal shows, each tagged with its registry formula_id + a
    substituted string built from THIS SKU's real inputs (spec §4). The registry is the single source —
    tag() raises if any id here is unregistered, so a rendered number can never lack a formula."""
    sym = context.get("sym") or "₹"
    def m(v):
        return "—" if v is None else f"{sym}{round(v):,.0f}"
    cur = diagnosis.get("sku_acos"); tsp = diagnosis.get("total_ad_spend"); tsa = diagnosis.get("total_ad_sales")
    cmaa_now = context.get("cmaa_now")
    cov = None if coverage_pct is None else f"{round(coverage_pct)}%"
    return {
        "break_even_acos": FR.tag("break_even_acos", f"gross contribution margin = {_pct(be)}", _pct(be)),
        "acos": FR.tag("acos", f"{m(tsp)} ÷ {m(tsa)} = {_pct(cur)}", _pct(cur)),
        "cmaa": FR.tag("cmaa", f"settled − cogs − fees − {m(tsp)} = {m(cmaa_now)}/mo", f"{m(cmaa_now)}/mo"),
        "recoverable": FR.tag("recoverable",
                              f"max({m(tsp)} − {m(tsa)} × {_pct(be)}, 0) = {m(recoverable)}/mo", f"{m(recoverable)}/mo"),
        "ad_coverage": FR.tag("ad_coverage", f"{cov} of ad spend mapped to SKUs" if cov else "—", cov or "—"),
    }


def build(sku, context, diagnosis, fidelity, coverage_pct):
    """context = {cmaa_now, monthly_loss}. Returns the Recommendation dict (spec A6)."""
    be = diagnosis.get("break_even_acos")
    actions = []
    offenders = diagnosis.get("offending_campaigns", [])[:TOP_OFFENDERS]
    terms = diagnosis.get("offending_terms", [])

    for c in offenders:
        camp, ac, waste = c["campaign"], c["acos_for_sku"], c["wasted_spend"]
        ag = c["ad_groups"][0][1] if c["ad_groups"] else None
        base_reason = (f"Campaign '{camp}' spends {_pct(c['spend_share'])} of this SKU's ad budget at "
                       f"{_pct(ac)} ACOS on the SKU vs its {_pct(be)} break-even.")
        # KEYWORD: negatives for the no-conversion terms in this campaign (offending_terms is only
        # populated at KEYWORD fidelity, so this naturally no-ops otherwise)
        camp_terms = [t for t in terms if t["campaign"] == camp and t["no_conversion"]]
        if camp_terms:
            names = [t["customer_search_term"] for t in camp_terms][:10]
            spend = sum(t["spend"] for t in camp_terms)
            actions.append(_action(
                "NEGATIVE_KEYWORD", _ref(sku, camp, ag),
                {"type": LV.NEGATIVE_ADD, "value": names},
                base_reason + f" These search terms spent with no orders: {', '.join(names)}.", spend))
        # bid-down (or remove, if the SKU bleeds beyond rescue by bidding) on this campaign
        if ac is not None and be is not None and ac > be * REMOVE_MULT:
            actions.append(_action(
                "REMOVE_PRODUCT_AD", _ref(sku, camp, ag, asin=None),
                {"type": LV.REMOVE_AD, "value": True},
                base_reason + " That's beyond what a bid cut fixes — remove this SKU's product ad from "
                "the campaign.", waste))
        else:
            actions.append(_action(
                "BID_DOWN", _ref(sku, camp, ag),
                {"type": LV.BID_PCT, "value": BID_DOWN_PCT},
                base_reason + f" Lower the bid ~{abs(int(BID_DOWN_PCT * 100))}% to pull spend back toward "
                "break-even.", waste))
        # advisory: a campaign with (near) zero attributed sales on this SKU is pure waste -> pause
        if (c["sales"] or 0.0) <= 0 and (c["spend"] or 0.0) > 0:
            actions.append(_action(
                "BUDGET_DOWN_PAUSE", _ref(sku, camp),
                {"type": LV.ADVISORY_TEXT,
                 "value": LV.LEVERS["BUDGET_DOWN_PAUSE"]["how_to"]},
                base_reason + " No attributed sales on this SKU — consider pausing/reducing the campaign.",
                c["spend"]))

    # advisory: if the SKU is spread across several campaigns, isolating it is a structural fix
    if len([c for c in diagnosis.get("campaigns", []) if (c["spend"] or 0) > 0]) >= 3:
        actions.append(_action(
            "CAMPAIGN_SPLIT", _ref(sku),
            {"type": LV.ADVISORY_TEXT, "value": LV.LEVERS["CAMPAIGN_SPLIT"]["how_to"]},
            "This SKU's spend is spread across several campaigns — a dedicated campaign would let its "
            "bids/budget be tuned without side effects.", 0.0))

    # a profitable SKU with headroom -> advisory scale (never an execute path)
    if (context.get("cmaa_now") or 0) > 0 and not offenders:
        best = min(diagnosis.get("campaigns", []),
                   key=lambda c: (c["acos_for_sku"] if c["acos_for_sku"] is not None else 9), default=None)
        if best:
            actions.append(_action(
                "SCALE_WINNER", _ref(sku, best["campaign"]),
                {"type": LV.ADVISORY_TEXT, "value": LV.LEVERS["SCALE_WINNER"]["how_to"]},
                f"Campaign '{best['campaign']}' runs at {_pct(best['acos_for_sku'])} ACOS, well under the "
                f"{_pct(be)} break-even — room to scale.", 0.0))

    bid_downs = [a for a in actions if a["change"].get("type") == LV.BID_PCT]
    max_bid = max((abs(a["change"]["value"]) for a in bid_downs), default=0)
    guardrails = ((f"max −{round(max_bid * 100)}% bid · " if bid_downs else "")
                  + "budget floor on · rollback ready")
    recoverable = diagnosis.get("wasted_spend_total", 0.0)
    formulas = _formulas(context, diagnosis, be, recoverable, coverage_pct)
    for a in actions:                       # each rec's +₹/mo is a CMAA projection (mockup ƒ tag)
        if a["action_class"] == LV.REALIFY_ACTIONABLE:
            a["formula_id"] = "cmaa_projection"
    sim = _projection(recoverable, coverage_pct, fidelity)
    if sim:
        sim["formula_id"] = "cmaa_projection"
        sim["tripwire_formula_id"] = "tripwire_units"
    return {
        "id": f"{sku}:AMAZON",
        "sku": sku, "title": context.get("title") or sku, "channel": "AMAZON", "fidelity": fidelity,
        "fidelity_label": _FIDELITY_LABEL.get(fidelity, "SKU-only"),
        "campaigns": len(diagnosis.get("campaigns", [])),
        "has_search_terms": fidelity == "KEYWORD",
        "problem": {"cmaa_now": context.get("cmaa_now"), "monthly_loss": context.get("monthly_loss"),
                    "break_even_acos": be, "current_acos_for_sku": diagnosis.get("sku_acos")},
        "actions": actions,
        "actionable_count": sum(1 for a in actions if a["action_class"] == LV.REALIFY_ACTIONABLE),
        "est_recovery_monthly": recoverable,
        "why": _why(be, diagnosis.get("sku_acos"), diagnosis.get("offending_campaigns", []), coverage_pct),
        "simulate": sim,
        "formulas": formulas,                                  # header/footer numbers, each ƒ-tagged (spec §4)
        "combined_formula_id": "combined_projection",          # footer "Projected if all applied" ƒ
        "guardrails": guardrails,
        "confidence": {"coverage_pct": coverage_pct, "fidelity": fidelity, "derived_source": True},
    }
