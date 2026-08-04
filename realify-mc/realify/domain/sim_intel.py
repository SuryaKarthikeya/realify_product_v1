"""SIMULATE for Intelligence insight cards — dispatch by canonical detector id to an own-data model.

Same contract as the Profit & Ads engine (sim_common): every projected number = a current L1 value ×
a stated, editable assumption, emitted as an explain part and rendered verbatim. Wherever a model needs
a TARGET it defaults to the tenant's OWN detector threshold (their floor / ceiling / line), labelled as
such and flagged when customized. A card whose action has no own-data mechanic degrades to an honest
disclaimer (never a fabricated projection); news/recall/social get no Simulate button at all.

ctx (built by the endpoint, never client-supplied):
  card_type, field, op, sku, asin, title, category, finding, family, exposure_inr,
  threshold, threshold_default, threshold_customized,   # tenant effective threshold for this rule
  row (seller_skus dict + latest sessions/conversion_pct/buybox_pct), portfolio_rev
"""
from . import sim_common as sc
from . import sim_inventory, sim_flow, sim_market
from ..pipeline import interpret


def detector_id(card_type, field=None, op=None):
    """Canonical detector for dispatch. A net-margin rule with op='gt' is a high-margin OPPORTUNITY
    (headroom), not a floor breach — route it to margin-headroom (mirrors interpret.detector_for)."""
    if field == "net_margin_pct" and op == "gt":
        return "margin-headroom"
    if field and field in interpret.FIELD_DETECTOR:
        return interpret.FIELD_DETECTOR[field][0]
    if card_type in interpret.CARDTYPE_DETECTOR:
        return interpret.CARDTYPE_DETECTOR[card_type][0]
    return (card_type or "signal").lower()


# canonical detector id -> intervention model. One model may serve several detectors (same mechanics).
_MODELS = {
    "margin-vs-floor": sim_market.fix_economics, "margin-headroom": sim_market.fix_economics,
    "returns-rate": sim_flow.returns_reduction,
    "revenue-share": sim_flow.concentration,
    "conversion": sim_flow.cvr_lift,
    "velocity": sim_inventory.demand_capture, "rank-movement": sim_inventory.demand_capture,
    "days-of-cover": sim_inventory.reorder, "seasonal-cover": sim_inventory.reorder,
    "stock-level": sim_inventory.reorder,
    "tacos": sim_flow.tacos_arrest,
    "buy-box-ownership": sim_market.buybox_regain,
    "price-competitiveness": sim_market.price_response,
    "competition-density": sim_market.competition_density,      # disclaimer-only (no own-data lever)
    "rating": sim_market.review_recovery, "review-count": sim_market.review_recovery,
    "opportunity": sim_market.gap_capture, "assortment-breadth": sim_market.gap_capture,
}
# context cards: a projection here would be fabricated → no Simulate button in the UI.
NO_BUTTON = {"category-news", "recall-regulatory", "social-signal"}


def simulatable(card_type, field=None, op=None):
    det = detector_id(card_type, field, op)
    return det in _MODELS and det not in NO_BUTTON


def simulate_card(ctx, assumptions=None):
    """Project an Intelligence card's recommendation. Returns the shared Simulation dict (can_simulate
    False + missing for honest-empty; sim_quality 'degraded' + reason when the base is weak; disclaimer_only
    for context cards with no lever)."""
    det = detector_id(ctx.get("card_type"), ctx.get("field"), ctx.get("op"))
    ident = {"sku": ctx.get("sku"), "asin": ctx.get("asin"), "title": ctx.get("title"),
             "bucket": det, "rec_headline": ctx.get("finding", "")}
    fn = _MODELS.get(det)
    if fn is None:
        return {**sc.base_dict(ident), "can_simulate": False,
                "missing": "no simulatable model for this card type (%s)" % det}
    m = fn(ctx, assumptions)
    quality = ("degraded", m["degraded_reason"]) if m.get("degraded_reason") else ("useful", None)
    base = sc.base_dict(ident, quality)
    if m.get("disclaimer_only"):                           # C2: caution banner + monitoring plan, no projection
        return {**base, "can_simulate": False, "disclaimer_only": True,
                "missing": m.get("missing", "no direct action to project"),
                "intervention": m.get("intervention"), "monitoring": m.get("monitoring", [])}
    # honest-empty models return before building a spec; finalize tolerates an empty spec/asm
    return sc.finalize(base, m, m.get("spec", []), m.get("asm", {}), active=(assumptions or {}).get("_preset"))
