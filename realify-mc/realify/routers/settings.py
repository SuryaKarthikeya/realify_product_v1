"""Operator settings, detectors, models, rules — split from run.py in #005 1a/1f. Handlers moved verbatim; behavior unchanged."""
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
from .deps import current, require_tenant, require_admin, _admin_key_ok, effective_admin_key
from .helpers import page, _track, _log_import, _is_customer, _synth_ops_allowed, BASE_DIR as HERE

router = APIRouter()


@router.get("/api/settings/interpretations")
def get_interpretations(request: Request):
    tid = require_tenant(request)
    from realify.pipeline import interpret
    con = db.connect()
    try:
        view = interpret.registry_view(con, tid)
    finally:
        con.close()
    return JSONResponse({"ok": True, "registry": view})

@router.post("/api/settings/interpretations")
async def set_interpretations(request: Request):
    """ADMIN ONLY. The interpretation layer (gates, priorities, phrasing) is Realify-
    confidential; customers cannot edit it. Requires the X-Realify-Admin header to
    match REALIFY_ADMIN_KEY. Body = {detector_id: [{id, enabled?, priority?, label?,
    action?, severity?}]} — merged over built-in defaults; gates/pools stay in code."""
    tid = require_tenant(request)
    admin_key = effective_admin_key()
    if not admin_key or request.headers.get("x-realify-admin") != admin_key:
        return JSONResponse({"ok": False, "error": "Interpretations are managed by Realify and aren't customer-editable."},
                            status_code=403)
    body = await request.json()
    con = db.connect()
    try:
        db.set_setting(con, tid, "interpretations", json.dumps(body or {}))
    finally:
        con.close()
    return JSONResponse({"ok": True})

@router.get("/api/settings/detectors")
def get_detectors(request: Request):
    """Customer-facing detector settings: enable / threshold / severity per detector,
    plus read-only interpretation chips. The reskinned Rules panel reads this."""
    tid = require_tenant(request)
    from realify import detector_settings
    return JSONResponse({"ok": True, "detectors": detector_settings.build(tid),
                         "groups": detector_settings.GROUP_ORDER})

@router.post("/api/settings/detectors")
async def set_detector(request: Request):
    tid = require_tenant(request)
    b = await request.json()
    from realify import detector_settings
    res = detector_settings.save(tid, b.get("detector"),
                                 enabled=b.get("enabled"), severity=b.get("severity"),
                                 threshold=b.get("threshold"))
    return JSONResponse(res, status_code=200 if res.get("ok") else 400)

@router.post("/api/settings/detectors/reset")
async def reset_detector(request: Request):
    tid = require_tenant(request)
    b = await request.json()
    from realify import detector_settings
    return JSONResponse(detector_settings.reset(tid, b.get("detector")))

@router.get("/api/metrics/history")
def metrics_history(request: Request):
    """Stage 2 Phase 0: time series for one SKU+metric (drives trends / sparklines)."""
    tid = require_tenant(request)
    asin = request.query_params.get("asin"); metric = request.query_params.get("metric")
    if not asin or not metric:
        return JSONResponse({"ok": False, "error": "asin and metric are required"}, status_code=400)
    con = db.connect()
    try:
        series = db.metric_series(con, tid, asin, metric)
    finally:
        con.close()
    return JSONResponse({"ok": True, "asin": asin, "metric": metric,
                         "series": [{"t": t, "v": v} for t, v in series]})

@router.get("/api/models")
def list_models(request: Request):
    """Stage 2: registered models, their detector coverage, and per-tenant enabled state."""
    tid = require_tenant(request)
    from realify import models
    con = db.connect()
    try:
        view = models.registry_view(con, tid)
    finally:
        con.close()
    return JSONResponse({"ok": True, "models": view})

@router.post("/api/settings/models")
async def set_model(request: Request):
    """Enable/disable a model for this tenant. Disabled models contribute no forecasts."""
    tid = require_tenant(request)
    b = await request.json()
    mid = b.get("model"); enabled = b.get("enabled")
    from realify import models
    con = db.connect()
    try:
        disabled = models.disabled_ids(con, tid)
        if enabled is False: disabled.add(mid)
        else: disabled.discard(mid)
        db.set_setting(con, tid, "models_disabled", json.dumps(sorted(disabled)))
    finally:
        con.close()
    return JSONResponse({"ok": True, "model": mid, "enabled": enabled is not False})

@router.post("/api/models/wipe")
def wipe_models(request: Request):
    """Reset model state for a clean demo: clear metric history, reseed the synthetic
    backfill, and re-run the pipeline. Does NOT touch the tenant's catalog/cards data."""
    tid = require_tenant(request)
    if _is_customer(tid):
        return JSONResponse({"ok": False, "error": "Forecast reset is disabled for customer accounts."}, status_code=403)
    from realify import history
    from realify.pipeline import materialize
    con = db.connect()
    try:
        MetricsRepository(con).delete_history(tid)
        con.commit()
        history.backfill_synthetic(con, tid)
    finally:
        con.close()
    materialize.run_pipeline(tid)
    return JSONResponse({"ok": True})

@router.get("/api/models/predict")
def model_predict(request: Request):
    tid = require_tenant(request)
    asin = request.query_params.get("asin")
    det = request.query_params.get("detector", "days-of-cover")
    if not asin:
        return JSONResponse({"ok": False, "error": "asin is required"}, status_code=400)
    from realify import models
    con = db.connect()
    try:
        preds = models.predict_for(con, tid, asin, det)
    finally:
        con.close()
    return JSONResponse({"ok": True, "asin": asin, "detector": det, "predictions": preds})

@router.get("/api/settings/app")
def get_app_settings(request: Request):
    tid = require_tenant(request)
    con = db.connect()
    em = db.get_setting(con, tid, "explain_mode", "0")
    con.close()
    return JSONResponse({"explain_mode": em == "1"})

@router.post("/api/settings/app")
async def set_app_settings(request: Request):
    tid = require_tenant(request)
    b = await request.json()
    con = db.connect()
    if "explain_mode" in b:
        db.set_setting(con, tid, "explain_mode", "1" if b["explain_mode"] else "0")
    con.close()
    return JSONResponse({"ok": True})

@router.get("/api/settings/rules")
def get_rules(request: Request):
    from realify import rules as rules_mod
    return JSONResponse(rules_mod.catalog_with_effective(require_tenant(request)))

@router.post("/api/settings/rules")
async def save_rule(request: Request):
    from realify import rules as rules_mod
    tid = require_tenant(request); b = await request.json()
    return JSONResponse(rules_mod.save_override(tid, b.get("rule_id"),
        enabled=b.get("enabled"), params=b.get("params"), severity=b.get("severity")))

@router.post("/api/settings/rules/reset")
async def reset_rules(request: Request):
    from realify import rules as rules_mod
    tid = require_tenant(request); b = await request.json()
    return JSONResponse(rules_mod.reset_override(tid, b.get("rule_id")))

@router.post("/api/settings/rebuild")
def rebuild(request: Request):
    """Kick off the detection rebuild in the BACKGROUND so Apply returns instantly;
    the browser polls /api/settings/rebuild/status."""
    tid = require_tenant(request)
    scheduler.start_rebuild(tid)
    return JSONResponse({"ok": True, "started": True})

@router.get("/api/settings/rebuild/status")
def rebuild_status(request: Request):
    tid = require_tenant(request)
    job = scheduler.get_rebuild(tid)
    if not job:
        return JSONResponse({"done": True, "idle": True})
    return JSONResponse(job)

@router.post("/api/settings/refresh_market")
def refresh_market(request: Request):
    """Force-refresh all market sources now (Keepa/recalls/news/trends), in the
    background. Browser polls /api/settings/refresh_market/status for per-source results."""
    tid = require_tenant(request)
    scheduler.start_market_refresh(tid)
    return JSONResponse({"ok": True, "started": True})

@router.get("/api/settings/refresh_market/status")
def refresh_market_status(request: Request):
    tid = require_tenant(request)
    job = scheduler.get_market_refresh(tid)
    if not job:
        return JSONResponse({"done": True, "idle": True})
    return JSONResponse(job)

@router.post("/api/settings/resynthesize")
async def resynth(request: Request):
    from realify import inflight
    tid = require_tenant(request); b = await request.json()
    # R6 B4: ALLOWLIST, fail-closed. Permit only synthetic tester/sandbox/internal; NULL account_type
    # on a seller tenant is now denied (was a fail-open hole).
    if not _synth_ops_allowed(tid):
        return JSONResponse({"ok": False, "error": "Resynthesize is only available on synthetic "
                             "tester/sandbox accounts."}, status_code=403)
    mode = b.get("mode", "reroll")
    if mode not in ("reroll", "full", "coverage"):
        mode = "reroll"
    with inflight.Guard("resynthesize", tid) as ok:
        if not ok:
            return JSONResponse({"ok": False, "error": "A resynthesize is already in progress for this "
                                 "account."}, status_code=409)
        # optional ad-graph scenario switch (only rebuilt on a 'full' resynth); persisted for future runs
        from realify.ingest.synth_ad_graph import AD_SCENARIOS
        if b.get("scenario") in AD_SCENARIOS:
            con = db.connect(); db.set_setting(con, tid, "ad_scenario", b["scenario"]); con.close()
        return JSONResponse(scheduler.resynthesize(tid, mode))

@router.get("/api/settings/coverage")
def coverage(request: Request):
    from realify import synth_conditions
    return JSONResponse(synth_conditions.coverage(require_tenant(request)))

# --- usage analytics ---------------------------------------------------
