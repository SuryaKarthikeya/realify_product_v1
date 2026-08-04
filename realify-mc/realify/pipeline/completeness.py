"""Goal completeness (spec §7/§9). Per goal → AVAILABLE | PARTIAL(reasons) | UNAVAILABLE, computed from
ARMED reliability flags (their blocks() mapping) + pending essential checklist items. A HARD input
missing (COGS for a margin goal, ad spend for ad-efficiency) makes the goal UNAVAILABLE; a soft caveat
(MCF fee, gateway fee gap) or a pending essential file makes it PARTIAL; otherwise AVAILABLE.

`preview_line` composes the single honest sentence shown above the checklist (§9)."""
from .. import topology
from ..topology_model import (ARMED, GOALS, PROFIT_AFTER_ADS, AD_EFFICIENCY, CATEGORY_INTEL, EVERYTHING)

AVAILABLE, PARTIAL, UNAVAILABLE = "AVAILABLE", "PARTIAL", "UNAVAILABLE"

# a flag that removes a goal's CORE input makes it UNAVAILABLE (not merely partial)
_HARD = {
    PROFIT_AFTER_ADS: {"MARGIN_UNAVAILABLE"},
    AD_EFFICIENCY:    {"AD_SPEND_ABSENT"},
    EVERYTHING:       {"MARGIN_UNAVAILABLE", "AD_SPEND_ABSENT"},
    CATEGORY_INTEL:   set(),
}
# human reason per soft-blocking flag
_FLAG_REASON = {
    "MCF_FEE_REQUIRED":  "Amazon MCF fees pending — Shopify margin excludes fulfilment cost",
    "FEE_GAP":           "some orders used another gateway — those fees are estimated",
    "AD_SPEND_ABSENT":   "no ad export yet — margin is shown pre-ad",
    "MARGIN_UNAVAILABLE": "product cost (COGS) is missing",
}
# short label for a pending essential file (else the manifest data_need)
_SHORT = {"AMZ_MCF_FEES": "Amazon MCF fees", "AD_META": "Meta ad export", "AD_AMAZON": "Amazon ad export",
          "AD_GOOGLE": "Google ad export", "AD_TIKTOK": "TikTok ad export", "AD_WALMART": "Walmart ad export",
          "SHOP_PAYOUTS": "Shopify payouts", "SHOP_PRODUCTS": "Shopify product costs",
          "AMZ_SETTLEMENT": "Amazon settlement"}


def _pending_essential(emitted, received):
    received = set(received or ())
    return [fid for fid, info in emitted.items()
            if info.get("essentiality") == topology.ESSENTIAL and fid not in received]


def compute(topo, emitted, received=None):
    """Returns {goal: {'state', 'reasons': [...]}}. Soft caveats + pending essentials → PARTIAL; a hard
    missing input → UNAVAILABLE; clear → AVAILABLE."""
    armed = [f for f in topo.flags if f.state == ARMED]
    pending = _pending_essential(emitted, received)
    out = {}
    for goal in GOALS:
        blocking = [f.id for f in armed if goal in f.blocks()]
        hard = [b for b in blocking if b in _HARD.get(goal, set())]
        pend_reasons = ["%s pending" % _SHORT.get(fid, (topology.by_id(fid).data_need if topology.by_id(fid) else fid))
                        for fid in pending] if goal != CATEGORY_INTEL else []
        soft = [_FLAG_REASON.get(b, b) for b in blocking if b not in hard]
        if hard:
            out[goal] = {"state": UNAVAILABLE, "reasons": [_FLAG_REASON.get(h, h) for h in hard]}
        elif blocking or pend_reasons:
            out[goal] = {"state": PARTIAL, "reasons": soft + pend_reasons}
        else:
            out[goal] = {"state": AVAILABLE, "reasons": []}
    return out


def preview_line(goal, completeness):
    """The one honest line for a goal (§9)."""
    e = completeness.get(goal) or {"state": AVAILABLE, "reasons": []}
    name = {PROFIT_AFTER_ADS: "Profit-after-ads", AD_EFFICIENCY: "Ad efficiency",
            CATEGORY_INTEL: "Category intel", EVERYTHING: "The full picture"}.get(goal, goal)
    if e["state"] == AVAILABLE:
        return "%s is ready with the files you've provided." % name
    reasons = e["reasons"] or ["some inputs are still missing"]
    verb = "can't be computed" if e["state"] == UNAVAILABLE else "unlocks once we have"
    if e["state"] == UNAVAILABLE:
        return "%s %s yet — %s." % (name, verb, "; ".join(reasons))
    return "%s %s %s." % (name, verb, "; ".join(reasons))
