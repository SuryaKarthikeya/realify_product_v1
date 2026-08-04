"""The specialist roster + the autonomy ladder + guardrail templates — the framework, as data.

One place to add a specialist or a guardrail. The flagship Pricing specialist carries the full
four-clocks / five-signals spec; the other four are onboarding-catalog entries for now.
"""

# autonomy ladder (order matters: promotion goes left→right; new hires start at 'observe')
AUTONOMY = [
    {"id": "observe", "label": "Observe", "desc": "sees and logs, acts on nothing"},
    {"id": "suggest", "label": "Suggest", "desc": "recommends; you approve each"},
    {"id": "assist",  "label": "Assist",  "desc": "handles routine, escalates big calls"},
    {"id": "act",     "label": "Act",     "desc": "executes within guardrails"},
]

# guardrail templates (enforced server-side before any Act; params are per-agent)
GUARDRAILS = [
    {"kind": "contribution_floor", "label": "Contribution floor, per SKU", "default": None,
     "desc": "Blocks any price below the SKU's margin floor."},
    {"kind": "max_change_pct", "label": "Max price change per move", "default": 15,
     "desc": "Caps how far a single move can swing."},
    {"kind": "inventory_first", "label": "Inventory-first gate", "default": "cover<7d",
     "desc": "Pauses price increases when stock is tight."},
    {"kind": "buybox_floor", "label": "Buy Box — never cede below floor", "default": True,
     "desc": "Won't chase the Buy Box into a loss."},
    {"kind": "change_freq", "label": "Change frequency cap", "default": "1/SKU/day",
     "desc": "Prevents thrash on any single SKU."},
    {"kind": "blast_radius", "label": "Blast radius per batch", "default": 20,
     "desc": "Limits how many SKUs one run can touch."},
    {"kind": "escalate", "label": "Escalate to human", "default": "conf<0.6 / >$500",
     "desc": "Low-confidence or high-impact moves need you."},
]

SPECIALISTS = [
    {
        "id": "pricing", "name": "Pricing & Margin Specialist", "flagship": True,
        "tagline": "Sets a profit-maximizing price for every SKU, defends the Buy Box, never crosses your "
                   "margin floor — deferring to Inventory when stock runs tight.",
        "clocks": ["Annual — roles, CM3 targets, markdown budgets, MAP, calendar",
                   "Seasonal — per-archetype build/manage/exit curves + ladders",
                   "Monthly — margin close, budget burn, elasticity refit, CPS re-baseline",
                   "Daily — runs the five-signal loop within the plane"],
        "signals": ["Competitor price", "Margin compression", "Sell-through", "Promo events",
                    "In-stock (hard cover-block gate)"],
        "default_tasks": [
            {"name": "Signal sweep & reprice", "clock": "day", "cadence": "daily", "autonomy": "suggest"},
            {"name": "Sell-through vs curve check", "clock": "day", "cadence": "daily", "autonomy": "observe"},
            {"name": "Elasticity refit & CPS re-baseline", "clock": "month", "cadence": "weekly", "autonomy": "observe"},
        ],
    },
    {"id": "discovery", "name": "Discovery — Category Analyst",
     "tagline": "Finds the next product worth launching — with modeled Year-1 upside and go/no-go gates.",
     "default_tasks": [{"name": "Refresh opportunity pipeline", "cadence": "daily", "autonomy": "observe"}]},
    {"id": "campaign", "name": "Campaign Manager",
     "tagline": "Cross-channel campaigns, tied to true contribution margin.",
     "default_tasks": [{"name": "Ad efficiency sweep", "cadence": "daily", "autonomy": "observe"}]},
    {"id": "fulfillment", "name": "Fulfillment Analyst",
     "tagline": "Cuts shipping cost, placement, and returns.",
     "default_tasks": [{"name": "Placement & returns review", "cadence": "weekly", "autonomy": "observe"}]},
    {"id": "channel", "name": "Channel Strategist",
     "tagline": "Scores channels on true margin.",
     "default_tasks": [{"name": "Channel margin scan", "cadence": "weekly", "autonomy": "observe"}]},
]

_BY_ID = {s["id"]: s for s in SPECIALISTS}


def specialist(sid):
    return _BY_ID.get(sid)


def default_guardrails():
    return [{"kind": g["kind"], "label": g["label"], "value": g["default"]} for g in GUARDRAILS]
