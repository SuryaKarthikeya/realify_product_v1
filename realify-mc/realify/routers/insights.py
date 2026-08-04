"""Read surface — feed, KPIs, channels (partner-facing, /api/v1) — split from run.py in #005 1a/1f. Handlers moved verbatim; behavior unchanged."""
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
from .helpers import page, _track, _log_import, _is_customer, BASE_DIR as HERE

router = APIRouter()


@router.get("/data/completeness")
def data_completeness(request: Request):
    tid = require_tenant(request)
    return JSONResponse({"ok": True, **api.data_completeness(tid)})

@router.get("/feed")
def feed(request: Request, category: str = "all", family: str = "all", new_only: bool = False, surface: str = None):
    return JSONResponse(api.get_feed(require_tenant(request), category, family, new_only, surface))

@router.get("/categories")
def categories(request: Request): return JSONResponse(api.get_categories(require_tenant(request)))

@router.get("/summary")
def summary(request: Request):
    tid = require_tenant(request)
    return JSONResponse(dict(briefing=api.briefing_summary(tid), sources=api.source_health(tid)))

@router.get("/headline")
def headline(request: Request, surface: str = "intelligence", family: str = "all",
             category: str = "all", new_only: bool = False):
    """Dynamic action-summary headline for the current surface + filter (deterministic + L2)."""
    from realify import headline as hl
    return JSONResponse(hl.compute(require_tenant(request), surface, family, category, new_only))

@router.get("/status")
def status(request: Request):
    return JSONResponse(api.load_status(require_tenant(request)))

@router.get("/channels/cross")
def channels_cross(request: Request):
    from realify import multichannel
    return JSONResponse(multichannel.cross_channel(require_tenant(request)))

@router.get("/channels/list")
def channels_list(request: Request):
    tid = require_tenant(request)
    con = db.connect()
    rows = ChannelRepository(con).active(tid)
    con.close()
    return JSONResponse({"channels": rows})

@router.get("/kpis")
def kpis(request: Request, window: int = 30):
    return JSONResponse(api.kpis(require_tenant(request), window))

@router.get("/log")
def log(request: Request, limit: int = 100):
    from realify import tasks
    return JSONResponse(tasks.get_log(require_tenant(request), limit))

@router.get("/sourcing")
def sourcing(request: Request):
    from realify import tasks
    return JSONResponse(tasks.get_sourcing(require_tenant(request)))

@router.get("/sourcing/export")
def sourcing_export(request: Request):
    from realify import tasks
    return PlainTextResponse(tasks.sourcing_csv(require_tenant(request)), media_type="text/csv",
                             headers={"Content-Disposition":"attachment; filename=sourcing_list.csv"})

@router.get("/watchlist")
def watchlist(request: Request):
    from realify import tasks
    return JSONResponse(tasks.get_watchlist(require_tenant(request)))
# ---- Step 3: reconciled cross-channel products ----

@router.get("/products")
def products(request: Request):
    from realify import channels
    return JSONResponse(channels.reconciled_products(require_tenant(request)))
# ---- Step 3: seller-editable rules (settings) ----
