"""Workspace KPI cards — two-layer read surface: 5 main KPIs, then 5 inner substat cards per
domain on drill-in. Plus Actions: the rule/card feed projected into per-domain action rows (see
realify/actions.py). Tables/charts/insights stay on their existing read paths; this only serves
the card + action layers."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from realify import api, actions as actions_mod, brief as brief_mod
from .deps import require_tenant

router = APIRouter()

_DOMAINS = ("revenue", "margin", "inventory", "ads", "cash")


@router.get("/workspace")
def workspace_summary(request: Request, window: int = 30, limit: int = actions_mod.DEFAULT_LIMIT):
    tid = require_tenant(request)
    k = api.kpis(tid, window)
    rows, total = actions_mod.actions(tid, limit=limit)
    return JSONResponse({
        "brief": brief_mod.compute_brief(tid, window),
        "kpis": [{"id": d, "title": k[d]["label"], "value": k[d]["value"]} for d in _DOMAINS],
        "actions": rows, "actions_total": total,
    })


@router.get("/workspace/{domain}")
def workspace_domain(domain: str, request: Request, window: int = 30):
    tid = require_tenant(request)
    k = api.kpis(tid, window)
    if domain not in k:
        return JSONResponse({"ok": False, "error": "unknown domain"}, status_code=404)
    return JSONResponse({"cards": k[domain]["substats"]})


@router.get("/workspace/{domain}/actions")
def workspace_domain_actions(domain: str, request: Request, limit: int = actions_mod.DEFAULT_LIMIT):
    tid = require_tenant(request)
    if domain not in actions_mod.DOMAIN_GROUPS:
        return JSONResponse({"ok": False, "error": "unknown domain"}, status_code=404)
    rows, total = actions_mod.actions(tid, actions_mod.DOMAIN_GROUPS[domain], limit=limit)
    return JSONResponse({"actions": rows, "actions_total": total})
