"""Model registry for the Ask picker + the monthly usage cap.

Provider-agnostic on purpose: each model names a `provider` that maps to a Narrator implementation
(see narrator.get_narrator). Today only the "stub" provider exists; a self-hosted model is added by
appending an entry with provider "self_hosted" (Realify will host its own model) — no other code changes.
The picker is data-driven off MODELS, so adding a model is a one-list edit.
"""

# 100 queries/month = full usage (per tenant), per the spec. Kept here as the single source of truth.
MONTHLY_QUERY_CAP = 100

MODELS = [
    {
        "id": "realify-pro",
        "label": "Realify Pro",
        "provider": "ria",
        "default": True,
        "description": "Live analyst — writes SQL against your data, then verifies every figure it "
                       "quotes against the result before answering.",
    },
    {
        "id": "realify-fast",
        "label": "Realify Fast",
        "provider": "stub",
        "default": False,
        "description": "Instant read of your open signals, computed directly from the engine — "
                       "no model, no wait.",
    },
]

_BY_ID = {m["id"]: m for m in MODELS}


def default_model_id():
    for m in MODELS:
        if m.get("default"):
            return m["id"]
    return MODELS[0]["id"]


def get_model(model_id):
    """The model dict, or the default model when `model_id` is unknown/None (never fail the turn on a
    stale picker value)."""
    return _BY_ID.get(model_id) or _BY_ID[default_model_id()]


def usage_view(usage):
    """Shape the repo usage dict for the client: overall %, remaining, and the per-model breakdown the
    picker dropdown shows. `usage` = {'total', 'by_model', 'period'}."""
    total = usage.get("total", 0)
    pct = min(100, round(total / MONTHLY_QUERY_CAP * 100)) if MONTHLY_QUERY_CAP else 0
    return {
        "period": usage.get("period"),
        "cap": MONTHLY_QUERY_CAP,
        "used": total,
        "remaining": max(0, MONTHLY_QUERY_CAP - total),
        "pct": pct,
        "by_model": [
            {"id": m["id"], "label": m["label"], "used": usage.get("by_model", {}).get(m["id"], 0)}
            for m in MODELS
        ],
    }
