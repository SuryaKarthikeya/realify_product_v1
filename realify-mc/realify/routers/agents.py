"""Agents API — the workforce surface. Reads are open (tenant-scoped); any ACT is gated by
flags.feature_enabled('agents') + autonomy + guardrails (enforced later, when the RIA models are live).
Hiring an agent (created in Observe) and pausing are configuration, not autonomous action, so they're
allowed — the agent still can't DO anything until the feature gate + Act autonomy are on.

  GET  /api/agents                 — roster + specialist catalog + autonomy ladder + guardrail templates
  POST /api/agents                 — hire a specialist (starts in Observe)
  GET  /api/agents/ledger          — the Autonomy Ledger (hash-chained decisions) + intact flag
  GET  /api/agents/{id}            — one agent's detail (tabs: overview/instructions/guardrails/tasks/…)
  POST /api/agents/{id}/pause      — pause / resume
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from realify.agents import service
from .deps import require_tenant

router = APIRouter()


async def _body(request):
    try:
        return await request.json()
    except Exception:
        return {}


@router.get("/agents")
def agents_list(request: Request):
    return JSONResponse({"ok": True, **service.roster(require_tenant(request))})


@router.post("/agents")
async def agents_hire(request: Request):
    tid = require_tenant(request)
    b = await _body(request)
    aid = service.hire(tid, b.get("specialist"), name=b.get("name"), autonomy="observe")
    if not aid:
        return JSONResponse({"ok": False, "error": "Unknown specialist."}, status_code=400)
    return JSONResponse({"ok": True, "agent_id": aid})


@router.get("/agents/ledger")
def agents_ledger(request: Request):
    tid = require_tenant(request)
    state = request.query_params.get("state")
    return JSONResponse({"ok": True, **service.ledger(tid, state=state)})


@router.get("/agents/{agent_id}")
def agent_detail(request: Request, agent_id: str):
    tid = require_tenant(request)
    d = service.agent_detail(tid, agent_id)
    if not d:
        return JSONResponse({"ok": False, "error": "Agent not found."}, status_code=404)
    return JSONResponse({"ok": True, "agent": d})


@router.post("/agents/{agent_id}/pause")
async def agent_pause(request: Request, agent_id: str):
    tid = require_tenant(request)
    b = await _body(request)
    service.set_status(tid, agent_id, "paused" if b.get("pause", True) else "active")
    return JSONResponse({"ok": True})
