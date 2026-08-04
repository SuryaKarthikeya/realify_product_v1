"""Customer-facing detector settings (the reskinned Rules panel).

Rolls the underlying catalog rules up to the canonical detectors the feed uses, and
exposes ONLY the customer-tunable knobs per detector: enable, threshold, severity.
The interpretation layer (gates, priorities, phrasing) is NOT exposed here — only
read-only chips (label + whether it's gated + how many phrasings), so customers see
that Realify tailors the reading without seeing the logic. Writes go back through
rules.save_override to every contributing rule, so the effective threshold changes
regardless of which underlying rule survives collapse.
"""
from . import rules as rules_mod
from .pipeline import interpret

# detector -> plain-English "what it watches" + display group
META = {
    "margin-vs-floor":      ("Net margin falls below your floor", "Margin"),
    "returns-rate":         ("Return rate rises above your ceiling", "Margin"),
    "velocity":             ("Sales velocity crosses your line", "Sales"),
    "revenue-share":        ("A SKU's revenue share crosses your concentration line", "Sales"),
    "conversion":           ("Conversion falls below your line", "Sales"),
    "rank-movement":        ("BSR improves well beyond its 30-day average", "Sales"),
    "days-of-cover":        ("Inventory cover runs below your line", "Inventory"),
    "stock-level":          ("Units on hand fall below your line", "Inventory"),
    "seasonal-cover":       ("A seasonal SKU runs low ahead of a demand turn", "Inventory"),
    "tacos":                ("TACoS rises above your ceiling", "Ads"),
    "buy-box-ownership":    ("Your Buy Box win-rate falls below your line", "Pricing & Buy Box"),
    "price-competitiveness":("A competitor undercuts you beyond your tolerance", "Pricing & Buy Box"),
    "competition-density":  ("Offer count jumps — a likely new entrant", "Pricing & Buy Box"),
    "rating":               ("Rating falls below your line", "Reviews"),
    "review-count":         ("Review count falls below your line", "Reviews"),
    "assortment-breadth":   ("Your SKU breadth in a category is below target", "Opportunity"),
    "opportunity":          ("A niche clears your opportunity score", "Opportunity"),
    "category-news":        ("Relevant category news in your space", "News & Risk"),
    "recall-regulatory":    ("Recall or rule change touching your products", "News & Risk"),
    "social-signal":        ("Buzz / review-theme shift on a relevant product", "News & Risk"),
}
# market/special detectors whose customer threshold is a named rule param (not "threshold")
PRIMARY_PARAM = {
    "price-competitiveness": "min_gap_pct",
    "competition-density":   "offer_jump_pct",
    "rank-movement":         "bsr_better_than_avg_pct",
    "seasonal-cover":        "days_of_cover_lt",
    "opportunity":           "min_score",
}
GROUP_ORDER = ["Margin", "Sales", "Inventory", "Ads", "Pricing & Buy Box", "Reviews", "Opportunity", "News & Risk"]

def _param_for(detector):
    return PRIMARY_PARAM.get(detector, "threshold")

def _rollup(tenant_id):
    """detector_id -> {rule_ids, enabled, severity, threshold spec}."""
    eff = rules_mod.effective_rules(tenant_id)
    out = {}
    for rid, r in eff.items():
        field = (r.get("cond") or {}).get("field")
        det = interpret.card_type_to_detector_id(r["card_type"], field)
        g = out.setdefault(det, {"rule_ids": [], "enabled": False, "severity": None, "threshold": None})
        g["rule_ids"].append(rid)
        if r.get("enabled"):
            g["enabled"] = True
        if g["severity"] is None:
            g["severity"] = r.get("severity")
        # threshold: first contributing rule that exposes this detector's primary param
        if g["threshold"] is None:
            pk = _param_for(det)
            ep = r.get("editable_params") or {}
            if pk in ep:
                spec = ep[pk]
                g["threshold"] = {
                    "key": pk,
                    "value": (r.get("params") or {}).get(pk, (r.get("params_default") or {}).get(pk)),
                    "min": spec.get("min"), "max": spec.get("max"),
                    "label": spec.get("label", pk), "type": spec.get("type", "number"),
                }
    return out

def build(tenant_id):
    roll = _rollup(tenant_id)
    chips = interpret.registry_view()  # {detector: {detector_name, interpretations:[{label,gated,variants}]}}
    detectors = []
    for det, g in roll.items():
        name, group = META.get(det, (det.replace("-", " ").title(), "Other"))
        det_chips = chips.get(det, {}).get("interpretations", [])
        # the base interpretation isn't a "tailoring" — show only the gated ones as chips
        tailorings = [{"label": c["label"], "gated": c["gated"], "variants": c["variants"]}
                      for c in det_chips if c.get("gated")]
        detectors.append({
            "detector": det, "name": name, "group": group,
            "enabled": g["enabled"], "severity": g["severity"],
            "watches": META.get(det, ("", ""))[0],
            "threshold": g["threshold"],          # None for news/risk detectors (no knob)
            "interpretations": tailorings,         # read-only chips; logic stays server-side
            "rule_ids": g["rule_ids"],             # internal write-through targets
        })
    detectors.sort(key=lambda d: (GROUP_ORDER.index(d["group"]) if d["group"] in GROUP_ORDER else 99, d["name"]))
    return detectors

def save(tenant_id, detector, enabled=None, severity=None, threshold=None):
    """Write the customer's knobs back to every contributing rule. Threshold lands on
    each rule that exposes this detector's primary param; enable/severity on all."""
    roll = _rollup(tenant_id)
    g = roll.get(detector)
    if not g:
        return {"ok": False, "error": "unknown detector"}
    pk = _param_for(detector)
    eff = rules_mod.effective_rules(tenant_id)
    for rid in g["rule_ids"]:
        ep = (eff.get(rid, {}).get("editable_params") or {})
        params = {pk: float(threshold)} if (threshold is not None and pk in ep) else None
        rules_mod.save_override(tenant_id, rid, enabled=enabled, params=params, severity=severity)
    return {"ok": True}

def reset(tenant_id, detector):
    roll = _rollup(tenant_id)
    g = roll.get(detector)
    if not g:
        return {"ok": False, "error": "unknown detector"}
    for rid in g["rule_ids"]:
        rules_mod.reset_override(tenant_id, rid)
    return {"ok": True}
