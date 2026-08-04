"""Step 5: the full 94-rule catalog as DATA.

Each rule from the consolidated catalog is given a machine-evaluable `cond` — a
(scope, field, op, param) spec over the synthesized facts — plus an editable
threshold param (so it is tunable in ⚙ Rules and the server can validate edits).
A generic evaluator (pipeline/detect.py) runs these; the richer market/tier-C
detectors stay as `primitive='special'` and are handled by dedicated code.

This is the literal "rules as data" port: detection logic for the bulk of the
catalog is a declarative condition, not 94 bespoke functions."""
import json, os

_RAW = json.load(open(os.path.join(os.path.dirname(__file__), "catalog94.json")))

# Per-AREA default condition over available SKU/traffic facts.
# (scope, field, op, default, lo, hi, label)  op: lt | gt
AREA_COND = {
    "Share":               ("sku", "rev_share_pct",  "gt", 8.0,  1, 40,  "Revenue-share above %"),
    "Price":               ("sku", "net_margin_pct", "lt", 12.0, 0, 40,  "Net margin below %"),
    "Assortment":          ("category", "own_skus",  "lt", 6,    1, 50,  "Own SKUs in category below"),
    "Demand":              ("sku", "velocity_day",   "gt", 20.0, 1, 500, "Units/day above"),
    "Opportunity":         ("sku", "net_margin_pct", "gt", 28.0, 5, 60,  "High-margin above %"),
    "Buy Box & Seller":    ("sku", "buybox_pct",     "lt", 90,   40, 99, "Buy Box % below"),
    "Search & Visibility": ("sku", "conversion_pct", "lt", 9.0,  1, 30,  "Conversion % below"),
    "Content & Listing":   ("sku", "conversion_pct", "lt", 7.0,  1, 30,  "Conversion % below"),
    "Ratings & Reviews":   ("sku", "rating",         "lt", 4.0,  1, 5,   "Rating below"),
    "Promotions & Deals":  ("sku", "net_margin_pct", "lt", 15.0, 0, 40,  "Net margin below %"),
    "Competitive Threats": ("sku", "buybox_pct",     "lt", 85,   40, 99, "Buy Box % below"),
    "Sales Intelligence":  ("sku", "velocity_day",   "gt", 15.0, 1, 500, "Units/day above"),
    "Margin Intelligence": ("sku", "net_margin_pct", "lt", 14.0, 0, 40,  "Net margin below %"),
    "Inventory Intelligence": ("sku", "days_of_cover", "lt", 25, 5, 400, "Days-of-cover below"),
    "Ads Intelligence":    ("sku", "tacos",          "gt", 14.0, 2, 50,  "TACoS above %"),
    "Cash Intelligence":   ("sku", "days_of_cover",  "gt", 120,  30, 500,"Days-of-cover above"),
}
# ID-level overrides where the area default would be the wrong direction/field.
ID_COND = {
    "INV-17": ("sku", "days_of_cover", "lt", 21,  5, 200, "Days-of-cover below (stockout)"),
    "INV-18": ("sku", "days_of_cover", "gt", 150, 40, 500, "Days-of-cover above (overstock)"),
    "INV-19": ("sku", "stock_on_hand", "lt", 30,  0, 500, "Units on hand below"),
    "INV-20": ("sku", "days_of_cover", "lt", 30,  5, 200, "Days-of-cover below"),
    "INV-21": ("sku", "days_of_cover", "gt", 180, 60, 600, "Aged days-of-cover above"),
    "CASH-29":("sku", "returns_rate",  "gt", 8.0, 1, 40, "Return rate above %"),
    "MARGIN-12":("sku","net_margin_pct","lt", 8.0, 0, 30, "Net margin below %"),
    "MARGIN-16":("sku","net_margin_pct","lt", 3.0,-10, 20, "Net margin below % (loss risk)"),
    "RR-02":  ("sku", "review_count",  "lt", 40,  0, 2000, "Review count below"),
    "RR-04":  ("sku", "rating",        "lt", 3.8, 1, 5,    "Rating below"),
    "SALES-04":("sku","days_of_cover", "lt", 28,  5, 200, "Days-of-cover below"),
    "SALES-07":("sku","days_of_cover", "lt", 25,  5, 200, "Days-of-cover below"),
    "CASH-27":("sku", "days_of_cover", "gt", 140, 40, 500, "Days-of-cover above"),
    "CASH-31":("sku", "days_of_cover", "gt", 160, 40, 600, "Days-of-cover above"),
    "OPP-04": ("sku", "net_margin_pct","gt", 30.0, 5, 60, "High-margin above %"),
}
# These 6 catalog concepts are already implemented as the prototype's special
# detectors C1–C6 (rich market/tier-C cards), so they're represented there, not
# re-seeded generically. C7/C8/C9 (news/recall/social) likewise have no catalog row.
SKIP = {"PRICE-02","PRICE-04","DMND-02","DMND-05","OPP-05","ASST-01"}
SEV = {"reprice":"act","restock_task":"act","case_report":"act","ad_action":"opp",
       "listing_update":"opp","review_request":"watch","monitoring_ticket":"watch"}

def _cond_for(r):
    spec = ID_COND.get(r["rule_id"]) or AREA_COND.get(r["area"])
    if not spec:
        return None
    scope, field, op, default, lo, hi, label = spec
    return {"primitive": "threshold", "scope": scope, "field": field, "op": op,
            "param": "threshold", "params_default": {"threshold": default},
            "editable_params": {"threshold": {"type": "number", "min": lo, "max": hi, "label": label}}}

# Group taxonomy. Group drives surface so the two stay consistent.
#   Intelligence (your products): Sales, Margin, Cash, Inventory, Ads, Pricing & Buy Box
#   Research (market/category):   Competitive, Demand, Opportunity, News, Risk
INTEL_GROUPS = {"Sales","Margin","Cash","Inventory","Ads","Pricing & Buy Box"}
AREA_GROUP = {
    "Sales Intelligence":"Sales", "Margin Intelligence":"Margin", "Cash Intelligence":"Cash",
    "Inventory Intelligence":"Inventory", "Ads Intelligence":"Ads",
    "Price":"Pricing & Buy Box", "Buy Box & Seller Landscape":"Pricing & Buy Box",
    "Competitive Threats & Anomalies":"Competitive", "Promotions & Deals":"Competitive",
    "Assortment":"Opportunity", "Opportunity":"Opportunity", "Content & Listing Quality":"Opportunity",
    "Share":"Demand", "Demand":"Demand", "Search & Visibility":"Demand",
    "Ratings & Reviews":"Risk",
}
def _group_for(r):
    return AREA_GROUP.get(r["area"], "Demand")
def _surface_for_group(group):
    return "intelligence" if group in INTEL_GROUPS else "research"

def build_catalog():
    """Return the catalog rules that are NOT already covered by the C1–C9 detectors,
    each as a data-driven threshold rule (≈88 rules)."""
    # The 3 own-data rules that shipped as bare "monitoring" get concrete handlers so
    # Intelligence cards are actionable rather than passive.
    ACTION_REMAP = {"SALES-03":"ad_action", "SALES-06":"ad_action", "MARGIN-15":"reprice"}
    out = []
    for r in _RAW:
        if r["rule_id"] in SKIP:
            continue
        c = _cond_for(r)
        if not c:
            continue
        group = _group_for(r)
        surface = _surface_for_group(group)
        c["surface"] = surface; c["group"] = group
        handler = ACTION_REMAP.get(r["rule_id"], r["action_handler"])
        out.append(dict(
            rule_id=r["rule_id"], name=r["name"], description=r["problem"] or r["delivered"],
            family=r["family"], card_type=r["rule_id"], tier=1, primitive="threshold",
            cond=c, action_handler=handler, surface=surface, group=group,
            severity_default=SEV.get(handler, "watch"), enabled_by_default=1,
            params_default=c["params_default"], editable_params=c["editable_params"],
            area=r["area"], narrative=r["narrative"], action=r["action"], own=r["own"]))
    return out

CATALOG = build_catalog()
