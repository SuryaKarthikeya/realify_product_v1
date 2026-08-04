"""The tool layer — the agent's hands.

Each Ask category (and a freeform question) routes to a domain "tool" that reads the tenant's REAL data
via the same materialized cards the app already shows (`api.get_feed`), plus light direct reads. Tools
return structured FACTS (headline + tiles + items + actions + sources) — never prose. The narrator turns
facts into an answer. Designed as the tool-router a real model would call via tool-use: swap the narrator,
keep these tools. Every tool is defensive — on missing data it returns an honest empty, never fabricates.
"""

# Ask category -> the card `group`s that answer it (groups come from api.get_feed).
CATEGORY_GROUPS = {
    "performance": ["Margin", "Sales"],
    "cash": ["Cash", "Inventory"],
    "ads": ["Ads"],
    "forecasts": ["Demand", "Opportunity"],
    "competition": ["Competitive", "Pricing & Buy Box"],
}

CATEGORY_LABEL = {
    "performance": "Performance", "cash": "Cash", "ads": "Ads",
    "forecasts": "Forecasts", "competition": "Competition",
}

# Curated seed questions (v1). Static now; the API is shaped so these can become data-generated later.
CATEGORY_QUESTIONS = {
    "performance": [
        "Which SKUs are quietly losing money after fees and ads?",
        "What's driving my margin change versus last month?",
        "Which products grew fastest this week — and why?",
        "Where am I leaving profit on the table right now?",
        "Is my overall profitability trending up or down?",
    ],
    "cash": [
        "Which SKUs are about to stock out?",
        "Where is my cash tied up in slow-moving inventory?",
        "What should I reorder this week, and how much?",
        "Which products are overstocked and bleeding storage fees?",
        "How many days of cover do I have across the catalog?",
    ],
    "ads": [
        "Where am I wasting ad spend right now?",
        "Which campaigns are below break-even ACoS?",
        "Which SKUs have room to scale spend profitably?",
        "What keywords drain budget without converting?",
        "How is my ROAS trending, and what's moving it?",
    ],
    "forecasts": [
        "What will sales look like over the next 30 days?",
        "Which products are trending up in demand?",
        "Am I stocked for the demand I'm forecasting?",
        "What's my projected revenue this month at current pace?",
        "Which SKUs face a seasonal drop soon?",
    ],
    "competition": [
        "Who's undercutting me on price right now?",
        "Where am I losing the Buy Box — and why?",
        "How does my pricing compare to the market?",
        "Which competitors are gaining share in my categories?",
        "What should I reprice to win back sales?",
    ],
}

# keyword -> category, for routing a freeform (typed) question when no category chip was used.
_KEYWORDS = {
    "performance": ["margin", "profit", "profitab", "revenue", "grew", "growth", "losing money"],
    "cash": ["stock out", "stockout", "inventory", "reorder", "restock", "cash", "days of cover", "doc"],
    "ads": ["ad spend", "ads", "acos", "roas", "campaign", "keyword", "bid", "ppc"],
    "forecasts": ["forecast", "next 30", "trend", "seasonal", "projected", "demand"],
    "competition": ["competitor", "competition", "buy box", "buybox", "undercut", "price", "reprice"],
}


def route_category(text):
    """Best-effort category for a freeform question; None if nothing matches (→ general summary)."""
    t = (text or "").lower()
    for cat, keys in _KEYWORDS.items():
        if any(k in t for k in keys):
            return cat
    return None


def _feed(tenant_id):
    try:
        from realify import api
        return api.get_feed(tenant_id) or []
    except Exception:
        return []


def _num_exposure(card):
    # exposure_pct is the reliable numeric magnitude for ranking; exposure_val is display text (₹1.8L/mo).
    try:
        return int(card.get("exposure_pct") or 0)
    except Exception:
        return 0


def gather(tenant_id, category=None, question=None, limit=4):
    """Return FACTS for the turn. `category` is a chip id (performance/cash/…) or None for freeform.
    Facts = {category, headline, count, items[], tiles[], actions[], sources[]}."""
    cat = category or route_category(question)
    groups = set(CATEGORY_GROUPS.get(cat, [])) if cat else None
    cards = _feed(tenant_id)
    if groups is not None:
        cards = [c for c in cards if c.get("group") in groups]
    cards.sort(key=_num_exposure, reverse=True)
    top = cards[:limit]

    items, sources = [], set()
    for c in top:
        items.append({
            "finding": c.get("finding") or c.get("type_name") or "",
            "exposure_label": c.get("exposure_label"),
            "exposure_val": c.get("exposure_val"),
            "severity": c.get("severity"),
            "sev_label": c.get("sev_label"),
            "asin": c.get("asin"),
            "surface": c.get("surface"),
            "action": c.get("action"),
            "card_id": c.get("id"),
        })
        for s in (c.get("sources") or []):
            name = s.get("name") if isinstance(s, dict) else str(s)
            if name:
                sources.add(name)

    label = CATEGORY_LABEL.get(cat, "your business")
    tiles = [{"label": "Signals", "value": str(len(cards)), "tone": "neutral"}]
    urgent = sum(1 for c in cards if c.get("severity") in ("crit", "act"))
    if urgent:
        tiles.append({"label": "Need attention", "value": str(urgent), "tone": "critical"})

    actions = []
    for c in top:
        if c.get("action") and c.get("id") is not None:
            actions.append({"label": c["action"], "surface": c.get("surface") or "intelligence",
                            "card_id": c["id"]})

    return {
        "category": cat,
        "label": label,
        "headline": f"{len(cards)} {label.lower()} signal{'' if len(cards)==1 else 's'} on your data",
        "count": len(cards),
        "urgent": urgent,
        "items": items,
        "tiles": tiles,
        "actions": actions[:3],
        "sources": sorted(sources),
    }
