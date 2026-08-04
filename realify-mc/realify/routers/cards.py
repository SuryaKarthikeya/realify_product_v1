"""Card action sub-API (partner-facing, /api/v1) — split from run.py in #005 1a/1f. Handlers moved verbatim; behavior unchanged."""
import os, json
from fastapi import APIRouter, Request, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, PlainTextResponse
from realify import db, config, auth, scheduler, api, statuscheck, opsdoc, analytics
from realify.repositories.card_repo import CardRepository
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.pull_repo import PullLogRepository
from realify.repositories.metrics_repo import MetricsRepository
from realify.repositories.tenant_repo import TenantRepository
from realify.repositories.user_repo import UserRepository
from realify.repositories.channel_repo import ChannelRepository
from realify.repositories.analytics_repo import AnalyticsRepository, SystemRepository
from .deps import current, require_tenant, require_admin, _admin_key_ok
from .helpers import page, _track, _log_import, _is_customer, agency_caps, BASE_DIR as HERE

router = APIRouter()


@router.get("/card/{card_id}/explain")
def explain(card_id: int, request: Request):
    return JSONResponse(api.explain_card(require_tenant(request), card_id))

@router.get("/card/{card_id}/research")
def research(request: Request, card_id: int, force: bool = False):
    from realify.pipeline.research import research_card
    tid = require_tenant(request)
    _track(request, "research", card_id=card_id)
    return JSONResponse(research_card(tid, card_id, force=force))

@router.get("/card/{card_id}/why")
def card_why(request: Request, card_id: int):
    from realify.pipeline.research import why_for_card
    return JSONResponse(why_for_card(require_tenant(request), card_id))

@router.post("/card/{card_id}/ask")
async def ask(request: Request, card_id: int):
    from realify.pipeline.research import ask_card
    b = await request.json()
    return JSONResponse(ask_card(require_tenant(request), card_id, b.get("question","")))

@router.post("/card/{card_id}/action")
async def action(request: Request, card_id: int):
    from realify import tasks; b = await request.json()
    tid = require_tenant(request)
    _track(request, "action_clickout", card_id=card_id, meta={"kind": "action", "action": b.get("action")})
    return JSONResponse(tasks.do_action(tid, card_id, b.get("action"), actor_caps=agency_caps(request)))

@router.post("/card/{card_id}/sourcing")
async def sourcing_add(request: Request, card_id: int):
    from realify import tasks; b = await request.json()
    return JSONResponse(tasks.add_to_sourcing(require_tenant(request), card_id, b.get("picks", [])))

@router.post("/card/{card_id}/save_brief")
def save_brief(request: Request, card_id: int):
    from realify import tasks
    return JSONResponse(tasks.save_brief(require_tenant(request), card_id))

@router.post("/card/{card_id}/watch")
def watch(request: Request, card_id: int):
    from realify import tasks
    return JSONResponse(tasks.add_watch(require_tenant(request), card_id))

@router.post("/card/{card_id}/dismiss")
def dismiss(request: Request, card_id: int, done: bool = False):
    from realify import tasks
    return JSONResponse(tasks.dismiss(require_tenant(request), card_id, done=done))

@router.get("/card/{card_id}/clickout")
def clickout(request: Request, card_id: int, kind: str = "amazon"):
    from realify import tasks
    tid = require_tenant(request)
    _track(request, "action_clickout", card_id=card_id, meta={"kind": kind})
    return JSONResponse(tasks.clickout(tid, card_id, kind))
