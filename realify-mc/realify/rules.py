"""Rules as data. The default catalog (seeded once, globally) plus a per-tenant
effective-rule resolver that merges tenant overrides over the defaults. The current
detectors read effective params here, so a seller editing a rule in settings changes
their feed immediately. Full 94-rule port is Step 5; these are the live ones today."""
import json
from . import db
from .repositories.rules_repo import RulesRepository

# Each rule: editable_params declares what a seller may tune + bounds (for safe UI + server validation).
CATALOG = [
    dict(rule_id="C1", name="Competitor Move", family="competitive", card_type="C1", tier=1,
         primitive="threshold", action_handler="reprice", severity_default="act", enabled_by_default=1,
         description="A competitor materially undercuts your price above your floor.",
         params_default={"min_gap_pct": 3.0, "min_gap_abs": 50},
         editable_params={"min_gap_pct": {"type":"number","min":0.5,"max":25,"label":"Min undercut %"},
                          "min_gap_abs": {"type":"number","min":0,"max":2000,"label":"Min undercut (₹)"}}),
    dict(rule_id="C2", name="New Entrant", family="competitive", card_type="C2", tier=1,
         primitive="pop_pct", action_handler="monitoring_ticket", severity_default="watch", enabled_by_default=1,
         description="Offer count jumps, signalling a likely new seller.",
         params_default={"offer_jump_pct": 40.0},
         editable_params={"offer_jump_pct": {"type":"number","min":10,"max":200,"label":"Offer-count jump %"}}),
    dict(rule_id="C3", name="Demand Shift", family="demand", card_type="C3", tier=1,
         primitive="ratio_vs_baseline", action_handler="restock_task", severity_default="watch", enabled_by_default=1,
         description="BSR improves well beyond its 30-day average (real demand climb).",
         params_default={"bsr_better_than_avg_pct": 20.0},
         editable_params={"bsr_better_than_avg_pct": {"type":"number","min":5,"max":60,"label":"BSR better-than-avg %"}}),
    dict(rule_id="C4", name="Seasonality Inflection", family="demand", card_type="C4", tier=1,
         primitive="threshold", action_handler="restock_task", severity_default="act", enabled_by_default=1,
         description="Cover/seasonal SKU runs low on days-of-cover ahead of a demand turn.",
         params_default={"days_of_cover_lt": 25, "lead_time_days": 14},
         editable_params={"days_of_cover_lt": {"type":"number","min":5,"max":120,"label":"Days-of-cover below"},
                          "lead_time_days": {"type":"number","min":1,"max":90,"label":"Lead time (days)"}}),
    dict(rule_id="C5", name="Opportunity Surfaced", family="opportunity", card_type="C5", tier=1,
         primitive="threshold", action_handler="monitoring_ticket", severity_default="opp", enabled_by_default=1,
         description="A niche clears the opportunity score threshold.",
         params_default={"min_score": 80},
         editable_params={"min_score": {"type":"number","min":50,"max":99,"label":"Min opportunity score"}}),
    dict(rule_id="C6", name="Assortment Gap Widened", family="opportunity", card_type="C6", tier=1,
         primitive="threshold", action_handler="monitoring_ticket", severity_default="watch", enabled_by_default=1,
         description="Competitors carry materially more SKUs in a segment than you.",
         params_default={"min_gap_skus": 6},
         editable_params={"min_gap_skus": {"type":"number","min":2,"max":50,"label":"Min SKU gap"}}),
    dict(rule_id="C7", name="Category News", family="news", card_type="C7", tier=1,
         primitive="crossing", action_handler="monitoring_ticket", severity_default="watch", enabled_by_default=1,
         description="Relevant category news in your space.", params_default={},
         editable_params={}),
    dict(rule_id="C8", name="Recall / Regulatory", family="news", card_type="C8", tier=1,
         primitive="crossing", action_handler="case_report", severity_default="opp", enabled_by_default=1,
         description="Official recall or rule change touching your products/competitors.", params_default={},
         editable_params={}),
    dict(rule_id="C9", name="Social / Virality", family="news", card_type="C9", tier=1,
         primitive="slope", action_handler="monitoring_ticket", severity_default="watch", enabled_by_default=1,
         description="Buzz/review-theme shift on a relevant product type (low confidence).", params_default={},
         editable_params={}),
    dict(rule_id="BB-OWN", name="Buy Box ownership", family="buybox", card_type="BB-OWN", tier=1,
         primitive="threshold", action_handler="reprice", severity_default="act", enabled_by_default=1,
         description="Your Buy Box win-rate on a SKU falls below your line.",
         params_default={"threshold": 80},
         editable_params={"threshold": {"type":"number","min":50,"max":100,"label":"Buy Box % below"}}),
]

def seed_catalog():
    con = db.connect()
    from . import catalog as catalog_mod
    # C1–C9 group + surface (C1–C4 are your-product Intelligence; C5–C9 are market Research)
    SPECIAL_GROUP = {"C1":"Pricing & Buy Box","C2":"Pricing & Buy Box","C3":"Sales","C4":"Inventory",
                     "C5":"Opportunity","C6":"Opportunity","C7":"News","C8":"Risk","C9":"Demand",
                     "BB-OWN":"Pricing & Buy Box"}
    full = CATALOG + catalog_mod.CATALOG          # 9 special detectors + ~88 data-driven catalog rules
    repo = RulesRepository(con)
    for r in full:
        cond = dict(r.get("cond", {}))
        group = r.get("group") or cond.get("group") or SPECIAL_GROUP.get(r["rule_id"], "Demand")
        surface = r.get("surface") or cond.get("surface") or ("intelligence" if group in catalog_mod.INTEL_GROUPS else "research")
        cond["surface"] = surface; cond["group"] = group
        repo.upsert_rule(
            r["rule_id"], r["name"], r["description"], r["family"], r.get("card_type", r["rule_id"]),
            r.get("tier", 1), r.get("primitive", "special"), json.dumps(cond),
            json.dumps(r["params_default"]), json.dumps(r["editable_params"]),
            "", r["action_handler"], r["severity_default"], r["enabled_by_default"])
    con.commit(); con.close()

def effective_rules(tenant_id):
    """Default catalog merged with this tenant's overrides -> {rule_id: {enabled, params, ...}}."""
    con = db.connect()
    repo = RulesRepository(con)
    cat = repo.all_rules()
    ov = repo.tenant_overrides(tenant_id)
    con.close()
    out = {}
    for rid, r in cat.items():
        params = json.loads(r["params_default"] or "{}")
        enabled = bool(r["enabled_by_default"])
        sev = r["severity_default"]
        o = ov.get(rid)
        if o:
            if o["enabled"] is not None: enabled = bool(o["enabled"])
            if o["params"]: params = {**params, **json.loads(o["params"])}
            if o["severity"]: sev = o["severity"]
        out[rid] = dict(enabled=enabled, params=params, severity=sev,
                        name=r["name"], family=r["family"], tier=r["tier"],
                        editable_params=json.loads(r["editable_params"] or "{}"),
                        params_default=json.loads(r["params_default"] or "{}"),
                        description=r["description"], primitive=r["primitive"],
                        card_type=r["card_type"], action_handler=r["action_handler"],
                        cond=json.loads(r["inputs"] or "{}"),
                        group=(json.loads(r["inputs"] or "{}") or {}).get("group","Demand"))
    return out

def catalog_with_effective(tenant_id):
    """For the settings UI: each rule + its current effective values for this tenant."""
    eff = effective_rules(tenant_id)
    return [dict(rule_id=rid, **v) for rid, v in eff.items()]

def save_override(tenant_id, rule_id, enabled=None, params=None, severity=None, updated_by="seller"):
    """Validate params against editable_params bounds, then upsert the tenant override."""
    con = db.connect()
    repo = RulesRepository(con)
    r = repo.get_rule(rule_id)
    if not r:
        con.close(); return {"ok": False, "error": "unknown rule"}
    editable = json.loads(r["editable_params"] or "{}")
    clean = {}
    for k, v in (params or {}).items():
        if k not in editable:
            continue  # silently drop non-editable params (logic is not seller-editable)
        spec = editable[k]
        try:
            num = float(v)
        except (ValueError, TypeError):
            con.close(); return {"ok": False, "error": f"{k} must be a number"}
        if "min" in spec and num < spec["min"]: num = spec["min"]
        if "max" in spec and num > spec["max"]: num = spec["max"]
        clean[k] = num
    repo.upsert_override(
        tenant_id, rule_id,
        (1 if enabled else 0) if enabled is not None else None,
        json.dumps(clean) if clean else None, severity, updated_by)
    con.commit(); con.close()
    return {"ok": True}

def reset_override(tenant_id, rule_id=None):
    con = db.connect()
    RulesRepository(con).delete_override(tenant_id, rule_id)
    con.commit(); con.close()
    return {"ok": True}
