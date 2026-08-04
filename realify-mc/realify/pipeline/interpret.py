"""Detector -> Interpretation layer (Build 1b).

Runs on collapsed signals BEFORE generation. Three jobs, none of which touch the
locked numbers (math stays in detect.py):

  1. Canonical detector: map each card to its 1:1-named detector (the registry).
  2. Interpretation: pick the highest-priority interpretation whose DATA GATE is
     true for this SKU (e.g. "Returns eroding margin" only when returns are high),
     else the base reading. The interpretation supplies the display name, action
     and severity.
  3. Non-duplicate language: each interpretation carries a POOL of finding
     phrasings; a card deterministically picks one via hash(asin+detector+interp),
     with a render-time collision guard so two visible cards never read alike.

Interpretations are CONFIGURABLE: the defaults below can be overridden per-tenant
via the 'interpretations' setting (same edit/reset pattern as rule thresholds).
"""
import hashlib, json

# ---- canonical detectors (the 1:1 names from the registry redesign) ----
FIELD_DETECTOR = {
    "net_margin_pct": ("margin-vs-floor",     "Margin vs floor"),
    "velocity_day":   ("velocity",            "Sales velocity"),
    "days_of_cover":  ("days-of-cover",       "Days of cover"),
    "stock_on_hand":  ("stock-level",         "Stock level"),
    "rev_share_pct":  ("revenue-share",       "Revenue concentration"),
    "own_skus":       ("assortment-breadth",  "Assortment breadth"),
    "conversion_pct": ("conversion",          "Conversion"),
    "tacos":          ("tacos",               "Ad efficiency (TACoS)"),
    "rating":         ("rating",              "Rating"),
    "review_count":   ("review-count",        "Review count"),
    "returns_rate":   ("returns-rate",        "Returns rate"),
    "buybox_pct":     ("buy-box-ownership",   "Buy Box ownership"),
}
CARDTYPE_DETECTOR = {
    "C1": ("price-competitiveness", "Price competitiveness"),
    "C2": ("competition-density",   "Competition density"),
    "C3": ("rank-movement",         "Rank movement"),
    "C4": ("seasonal-cover",        "Seasonal restock"),
    "C5": ("opportunity",           "Opportunity"),
    "C6": ("assortment-breadth",    "Assortment breadth"),
    "C7": ("category-news",         "Category news"),
    "C8": ("recall-regulatory",     "Recall / regulatory"),
    "C9": ("social-signal",         "Social signal"),
    "BB-OWN": ("buy-box-ownership", "Buy Box ownership"),
}

def detector_for(sig):
    nums = sig.get("nums") or {}
    fld = nums.get("field")
    # A net-margin rule with op="gt" is a HIGH-margin OPPORTUNITY (margin ABOVE a target), NOT a
    # floor breach. Route it away from margin-vs-floor (whose pool hard-codes "under the floor") so
    # generate.py phrases it with the correct relation ("above your … line"). Only op="lt" (margin
    # below a floor) uses the below-floor detector. This is the shared-pipeline root fix (Feed/P&A too).
    if fld == "net_margin_pct" and nums.get("op") == "gt":
        return ("margin-headroom", "Margin headroom")
    if fld and fld in FIELD_DETECTOR:
        return FIELD_DETECTOR[fld]
    ct = sig.get("card_type", "")
    if ct in CARDTYPE_DETECTOR:
        return CARDTYPE_DETECTOR[ct]
    return (ct.lower() or "signal", sig.get("type_name") or ct or "Signal")

# Migration map: old card_type prefix family is preserved via dedup_key (we keep
# dedup on card_type so existing dismissals don't churn). This dict documents the
# old->new naming for any downstream consumer that wants the canonical id.
def card_type_to_detector_id(card_type, field=None):
    if field and field in FIELD_DETECTOR:
        return FIELD_DETECTOR[field][0]
    if card_type in CARDTYPE_DETECTOR:
        return CARDTYPE_DETECTOR[card_type][0]
    return (card_type or "signal").lower()

# ---- interpretation gates (data conditions, evaluated against the SKU row) ----
# Each gate is (sku_dict, nums_dict) -> bool. Gates use only locked data, never copy.
def _g_returns_high(s, n):   return bool(s) and (s.get("returns_rate") or 0) > 8
def _g_tacos_high(s, n):     return bool(s) and (s.get("tacos") or 0) > 12
def _g_box_low(s, n):        return bool(s) and (s.get("buybox_pct") or 100) < 75
def _g_fast_mover(s, n):     return bool(s) and (s.get("velocity_day") or 0) >= 8
def _g_deep_overstock(s, n): return bool(s) and (s.get("days_of_cover") or 0) > 120
def _g_cover_low(s, n):      return (n or {}).get("op") == "lt"
def _g_cover_high(s, n):     return (n or {}).get("op") == "gt"

# ---- interpretation registry (defaults; per-tenant override merges over this) ----
# detector_id -> ordered list of interpretations. First entry is the base (gate
# always true, lowest priority). Higher 'priority' wins when multiple gates pass.
# 'pool' = finding phrasings with {ent} {ev} {tv} {expph} placeholders.
INTERP = {
    "margin-vs-floor": [
        {"id": "margin-below-floor", "label": "Margin below floor", "priority": 0,
         "gate": None, "action": "Reprice or trim cost", "severity": "act", "pool": [
            "{ent} is netting <b>{ev}%</b> margin, below your {tv}% floor{expph}.",
            "Margin on {ent} has slipped to <b>{ev}%</b>, under the {tv}% floor you set{expph}.",
            "{ent} clears just <b>{ev}%</b> after fees \u2014 beneath your {tv}% floor{expph}.",
            "After fees and ads, {ent} keeps only <b>{ev}%</b>, under your {tv}% line{expph}.",
        ]},
        {"id": "returns-eroding-margin", "label": "Returns eroding margin", "priority": 20,
         "gate": _g_returns_high, "action": "Investigate returns driver", "severity": "act", "pool": [
            "{ent} nets <b>{ev}%</b> margin, and a high return rate is the leak pulling it under your {tv}% floor{expph}.",
            "Returns are draining {ent}: margin sits at <b>{ev}%</b>, below your {tv}% floor, with returns well above norm{expph}.",
            "{ent}'s <b>{ev}%</b> margin is being eaten by returns \u2014 under your {tv}% floor once reverse logistics land{expph}.",
        ]},
        {"id": "ad-spend-eroding-margin", "label": "Ad spend below breakeven", "priority": 15,
         "gate": _g_tacos_high, "action": "Trim ad spend", "severity": "act", "pool": [
            "{ent} nets <b>{ev}%</b> margin, but heavy ad spend is pushing it under your {tv}% floor{expph}.",
            "Ad load is the drag on {ent}: <b>{ev}%</b> margin, below your {tv}% floor, with TACoS running hot{expph}.",
            "{ent} clears <b>{ev}%</b> \u2014 below your {tv}% floor \u2014 largely because ad cost is too high{expph}.",
        ]},
        {"id": "margin-thin-losing-box", "label": "Margin thin while losing Buy Box", "priority": 18,
         "gate": _g_box_low, "action": "Reprice to defend Buy Box", "severity": "act", "pool": [
            "{ent} is squeezed both ways \u2014 <b>{ev}%</b> margin (under your {tv}% floor) and slipping Buy Box share{expph}.",
            "{ent} nets <b>{ev}%</b>, below your {tv}% floor, while also losing the Buy Box \u2014 a double hit{expph}.",
        ]},
    ],
    "days-of-cover": [
        {"id": "cover-low", "label": "Inventory running low", "priority": 0,
         "gate": _g_cover_low, "action": "Restock", "severity": "act", "pool": [
            "{ent} has only <b>{ev} days</b> of cover left, under your {tv}-day line{expph}.",
            "Cover on {ent} is down to <b>{ev} days</b>, below the {tv}-day line you set{expph}.",
            "{ent} will run dry in about <b>{ev} days</b> \u2014 under your {tv}-day floor{expph}.",
        ]},
        {"id": "fast-mover-stockout", "label": "Fast mover running out", "priority": 20,
         "gate": _g_fast_mover, "action": "Expedite restock", "severity": "act", "pool": [
            "{ent} is a fast mover with just <b>{ev} days</b> of cover \u2014 well under your {tv}-day line{expph}.",
            "High velocity is burning {ent} down to <b>{ev} days</b> of cover, below your {tv}-day floor{expph}.",
        ]},
        {"id": "cover-high", "label": "Cash trapped in overstock", "priority": 10,
         "gate": _g_cover_high, "action": "Run a clearance", "severity": "watch", "pool": [
            "{ent} is sitting on <b>{ev} days</b> of cover, over your {tv}-day line \u2014 capital and storage tied up{expph}.",
            "Overstock on {ent}: <b>{ev} days</b> of cover, above your {tv}-day line{expph}.",
        ]},
    ],
    "buy-box-ownership": [
        {"id": "buy-box-low", "label": "Losing the Buy Box", "priority": 0,
         "gate": None, "action": "Reprice / check eligibility", "severity": "act", "pool": [
            "{ent} holds the Buy Box only <b>{ev}%</b> of the time, under your {tv}% line{expph}.",
            "Buy Box share on {ent} has fallen to <b>{ev}%</b>, below your {tv}% line{expph}.",
            "{ent} is winning the Buy Box just <b>{ev}%</b> of the time \u2014 under your {tv}% floor{expph}.",
        ]},
        {"id": "ads-out-of-box", "label": "Paying for ads while out of the Buy Box", "priority": 20,
         "gate": _g_tacos_high, "action": "Pause ads until box recovers", "severity": "act", "pool": [
            "{ent} holds the Buy Box only <b>{ev}%</b> of the time \u2014 yet ad spend keeps running, so you're paying for clicks that may not convert{expph}.",
            "Ad budget is burning on {ent} while it owns the Buy Box just <b>{ev}%</b> of the time, under your {tv}% line{expph}.",
        ]},
    ],
}

# generic base interpretation for detectors without a bespoke entry
def _base_for(detector_id, detector_name, op):
    rel = "below" if op == "lt" else "above"
    return {"id": detector_id + "-base", "label": detector_name, "priority": 0,
            "gate": None, "action": None, "severity": None,
            "pool": ["{ent}'s " + detector_name.lower() + " is <b>{ev}</b>, " + rel + " your {tv} line{expph}."]}

def load_interpretations(con=None, tenant_id=None):
    """Built-in defaults, optionally overridden by the tenant's 'interpretations'
    setting (a JSON of {detector_id: [{id, enabled, priority, label, action, severity}]}).
    Overrides are shallow-merged by interpretation id; gates/pools stay code-defined."""
    reg = {k: [dict(i) for i in v] for k, v in INTERP.items()}
    if con is not None and tenant_id is not None:
        try:
            from .. import db
            raw = db.get_setting(con, tenant_id, "interpretations")
            ov = json.loads(raw) if raw else {}
            for det, items in (ov or {}).items():
                by_id = {i["id"]: i for i in reg.get(det, [])}
                for o in items:
                    tgt = by_id.get(o.get("id"))
                    if tgt:
                        for k in ("enabled", "priority", "label", "action", "severity"):
                            if k in o:
                                tgt[k] = o[k]
        except Exception:
            pass
    return reg

def select(sig, sku, registry):
    """Pick the canonical detector + best interpretation for this card.
    Returns dict(detector, detector_name, interp_id, label, action, severity, pool)."""
    det_id, det_name = detector_for(sig)
    nums = sig.get("nums") or {}
    candidates = registry.get(det_id)
    if not candidates:
        # no bespoke interpretation: keep the canonical name, but let generate.py's
        # unit-aware FIELD_FIND template render the finding (pool=None => no override).
        return {"detector": det_id, "detector_name": det_name, "interp_id": det_id + "-base",
                "label": det_name, "action": sig.get("action"), "severity": sig.get("severity"),
                "pool": None}
    best = None
    for it in candidates:
        if it.get("enabled") is False:
            continue
        g = it.get("gate")
        ok = True if g is None else False
        if g is not None:
            try: ok = bool(g(sku, nums))
            except Exception: ok = False
        if ok and (best is None or it.get("priority", 0) > best.get("priority", 0)):
            best = it
    if best is None:
        best = candidates[0]
    return {"detector": det_id, "detector_name": det_name, "interp_id": best["id"],
            "label": best.get("label", det_name),
            "action": best.get("action") or sig.get("action"),
            "severity": best.get("severity") or sig.get("severity"),
            "pool": best.get("pool") or [det_name]}

def _phrasing_index(asin, detector, interp_id, pool_len, used):
    """Deterministic, stable per card; collision-guarded across the visible set."""
    if pool_len <= 1:
        return 0
    key = f"{asin or ''}:{detector}:{interp_id}"
    base = int(hashlib.md5(key.encode()).hexdigest(), 16) % pool_len
    idx = base
    for _ in range(pool_len):
        if (detector, interp_id, idx) not in used:
            break
        idx = (idx + 1) % pool_len
    used.add((detector, interp_id, idx))
    return idx

def registry_view(con=None, tenant_id=None):
    """Serializable view of the (effective) interpretation registry for the config UI/API."""
    reg = load_interpretations(con, tenant_id)
    out = {}
    for det, items in reg.items():
        name = next((dn for (di, dn) in list(FIELD_DETECTOR.values()) + list(CARDTYPE_DETECTOR.values()) if di == det), det)
        out[det] = {"detector_name": name, "interpretations": [
            {"id": it["id"], "label": it.get("label"), "priority": it.get("priority", 0),
             "enabled": it.get("enabled", True), "gated": it.get("gate") is not None,
             "action": it.get("action"), "severity": it.get("severity"),
             "variants": len(it.get("pool") or [])}
            for it in items]}
    return out

def annotate(signals, by_asin, con=None, tenant_id=None):
    """Mutate each signal in place with canonical detector + chosen interpretation +
    a non-duplicate finding template. Returns the same list for chaining."""
    registry = load_interpretations(con, tenant_id)
    used = set()
    for sig in signals:
        sku = by_asin.get(sig.get("asin"))
        chosen = select(sig, sku, registry)
        sig["detector"] = chosen["detector"]
        sig["detector_name"] = chosen["detector_name"]
        sig["interpretation"] = chosen["interp_id"]
        # honest 1:1 / interpretation title (overrides the loose rule name)
        sig["type_name"] = chosen["label"]
        if chosen["action"]:   sig["action"] = chosen["action"]
        if chosen["severity"]: sig["severity"] = chosen["severity"]
        # non-duplicate phrasing: only when the interpretation supplies a bespoke pool;
        # otherwise leave unset so generate.py uses its unit-aware FIELD_FIND template.
        pool = chosen["pool"]
        if pool:
            idx = _phrasing_index(sig.get("asin"), chosen["detector"], chosen["interp_id"], len(pool), used)
            sig["_finding_tmpl"] = pool[idx]
    return signals
