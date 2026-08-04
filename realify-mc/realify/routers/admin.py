"""Admin console, analytics & ops docs — split from run.py in #005 1a/1f. Handlers moved verbatim; behavior unchanged."""
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
from realify.repositories.audit_repo import DeletedAccountAuditRepository
from .deps import current, require_tenant, require_admin, _admin_key_ok
from .helpers import page, _track, _log_import, _is_customer, BASE_DIR as HERE

router = APIRouter()


@router.post("/api/track")
async def track(request: Request):
    """Frontend funnel events (page_view, insight_click). Identity comes from the
    session, never the body. Best-effort; always returns ok."""
    uid, tid = current(request)
    if not tid:
        return JSONResponse({"ok": False}, status_code=401)
    try:
        b = await request.json()
    except Exception:
        b = {}
    from realify import analytics
    analytics.record(tid, uid, b.get("event"), page=b.get("page"),
                     card_id=b.get("card_id"), card_type=b.get("card_type"), meta=b.get("meta"))
    return JSONResponse({"ok": True})

@router.get("/api/admin/rollout")
def admin_rollout_get(request: Request):
    """The Feature/Version Registry state for the Ops catalog — every feature, its versions, the
    selected build, rollout scope, and gate states."""
    require_admin(request)
    from realify import flags
    return JSONResponse({"ok": True, "features": flags.list_state()})


@router.post("/api/admin/rollout")
async def admin_rollout_set(request: Request):
    """Ops-driven rollout / rollback — instant, no redeploy. Body targets one feature:
      version feature: {feature, version} (pick the build) and/or {feature, scope: off|internal|on}
      gate feature:    {feature, on: bool}
    Everything is reversible: rollback = POST a previous version or scope 'off'."""
    require_admin(request)
    from realify import flags
    try:
        b = await request.json()
    except Exception:
        b = {}
    key = b.get("feature")
    if key in flags.FEATURES:
        if "version" in b:
            flags.set_selected(key, b["version"])
        if "scope" in b:
            flags.set_scope(key, b["scope"])
        if "on" in b:
            flags.set_feature(key, bool(b["on"]))
    return JSONResponse({"ok": True, "features": flags.list_state()})


@router.get("/api/admin/analytics/summary")
def admin_analytics_summary(request: Request, days: int = 14):
    require_admin(request)
    from realify import analytics
    days = max(1, min(int(days), 90))
    return JSONResponse({"ok": True, "days": days,
                         "totals": analytics.totals(None, days),
                         "daily": analytics.daily_summary(None, days)})

@router.get("/api/admin/analytics/top_users")
def admin_analytics_top_users(request: Request, days: int = 14, limit: int = 10):
    require_admin(request)
    from realify import analytics
    days = max(1, min(int(days), 90))
    return JSONResponse({"ok": True, "users": analytics.top_users(None, days, limit)})

# ===================== ADMIN OPERATOR CONSOLE (/ops) =====================

@router.get("/ops", response_class=HTMLResponse)
def ops_page():
    return HTMLResponse(page("admin.html"), headers={"X-Robots-Tag": "noindex, nofollow"})

@router.get("/ops/architecture", response_class=HTMLResponse)
def ops_architecture(k: str = ""):
    if not _admin_key_ok(k):
        return HTMLResponse("<h3 style='font-family:sans-serif'>Admin key required.</h3>", status_code=403,
                            headers={"X-Robots-Tag": "noindex, nofollow"})
    try:
        html = open(os.path.join(HERE, "docs", "Realify-Architecture.html"), encoding="utf-8").read()
    except FileNotFoundError:
        html = "<h3>Architecture document not found.</h3>"
    return HTMLResponse(html, headers={"X-Robots-Tag": "noindex, nofollow"})

@router.get("/ops/logbook", response_class=HTMLResponse)
def ops_logbook(k: str = ""):
    if not _admin_key_ok(k):
        return HTMLResponse("<h3 style='font-family:sans-serif'>Admin key required.</h3>", status_code=403,
                            headers={"X-Robots-Tag": "noindex, nofollow"})
    try:
        md = open(os.path.join(HERE, "docs", "Realify-Logbook.md"), encoding="utf-8").read()
    except FileNotFoundError:
        md = "Logbook not found."
    import html as _h
    body = ("<body style='font-family:ui-monospace,Menlo,monospace;max-width:900px;margin:40px auto;"
            "padding:0 20px;line-height:1.5;color:#1F3864;white-space:pre-wrap'>"
            + _h.escape(md) + "</body>")
    return HTMLResponse("<!doctype html><meta name='robots' content='noindex'>" + body,
                        headers={"X-Robots-Tag": "noindex, nofollow"})

@router.get("/ops/formulas", response_class=HTMLResponse)
def ops_formulas(k: str = ""):
    if not _admin_key_ok(k):
        return HTMLResponse("<h3 style='font-family:sans-serif'>Admin key required.</h3>", status_code=403,
                            headers={"X-Robots-Tag": "noindex, nofollow"})
    try:
        md = open(os.path.join(HERE, "docs", "FORMULAS.md"), encoding="utf-8").read()
    except FileNotFoundError:
        md = "Formulas reference not found."
    # Fix-Ads formula registry — generated from the single programmatic source (domain/formula_registry)
    # so the admin page and the numbers the surface renders can never drift (spec §4 backfill).
    from realify.domain import formula_registry as _fr
    md += ("\n\n## Fix-Ads formula registry (`formula_id` → expression)\n\n"
           "The single source the Fix-Ads surface renders — every number there carries its `formula_id`, "
           "revealed with the SKU's own inputs when explainability is on.\n\n| `formula_id` | Formula |\n|---|---|\n"
           + "\n".join(f"| `{fid}` | `{_fr.FORMULAS[fid]['expression']}` |" for fid in _fr.all_ids()))
    return HTMLResponse(opsdoc.render_page("Deterministic Math Reference", md),
                        headers={"X-Robots-Tag": "noindex, nofollow"})

@router.get("/ops/integration", response_class=HTMLResponse)
def ops_integration(k: str = ""):
    if not _admin_key_ok(k):
        return HTMLResponse("<h3 style='font-family:sans-serif'>Admin key required.</h3>", status_code=403,
                            headers={"X-Robots-Tag": "noindex, nofollow"})
    try:
        md = open(os.path.join(HERE, "docs", "INTEGRATION-GUIDE.md"), encoding="utf-8").read()
    except FileNotFoundError:
        md = "Integration guide not found."
    return HTMLResponse(opsdoc.render_page("Integration Guide — Partner Teams", md),
                        headers={"X-Robots-Tag": "noindex, nofollow"})

@router.get("/ops/onboarding", response_class=HTMLResponse)
def ops_onboarding(k: str = ""):
    if not _admin_key_ok(k):
        return HTMLResponse("<h3 style='font-family:sans-serif'>Admin key required.</h3>", status_code=403,
                            headers={"X-Robots-Tag": "noindex, nofollow"})
    try:
        md = open(os.path.join(HERE, "docs", "ONBOARDING.md"), encoding="utf-8").read()
    except FileNotFoundError:
        md = "Onboarding guide not found."
    return HTMLResponse(opsdoc.render_page("Onboarding — Building on Realify", md),
                        headers={"X-Robots-Tag": "noindex, nofollow"})

@router.get("/api/admin/tenants")
def admin_tenants(request: Request):
    require_admin(request)
    con = db.connect()
    try:
        rows = TenantRepository(con).list_all()
        out = []
        for r in rows:
            d = dict(r); tid = d["id"]
            d["members"] = UserRepository(con).count_members(tid)
            d["skus"] = SellerRepository(con).count(tid)
            d["cards"] = CardRepository(con).count_all(tid)
            la = AnalyticsRepository(con).last_activity(tid)
            d["last_activity"] = la
            out.append(d)
        return JSONResponse({"ok": True, "tenants": out})
    finally:
        con.close()

@router.post("/api/admin/tenants/{tenant_id}/delete")
async def admin_delete_tenant(tenant_id: int, request: Request):
    """FULLY delete an account: wipe every tenant-scoped row + its users + the tenant itself (frees the
    email so it can re-signup through the normal flow), then write one surviving audit row. Guarded by
    the admin key AND a typed name confirmation to prevent a wrong-account delete."""
    require_admin(request)
    try:
        b = await request.json()
    except Exception:
        b = {}
    confirm = (b.get("confirm") or "").strip()
    deleted_by = (b.get("by") or "ops-console").strip()[:80]
    con = db.connect()
    try:
        t = TenantRepository(con).get(tenant_id)
        if not t:
            return JSONResponse({"ok": False, "error": "No such account."}, status_code=404)
        name = t.get("name") or ""
        if confirm != name:
            return JSONResponse({"ok": False, "error": "Type the exact account name to confirm deletion."},
                                status_code=400)
        emails = [m.get("email") for m in db.list_members(con, tenant_id) if m.get("email")]
        summary = {"tenant_id": tenant_id, "name": name,
                   "account_type": TenantRepository(con).get_account_type(tenant_id),
                   "emails": emails, "members": len(emails),
                   "skus": SellerRepository(con).count(tenant_id),
                   "cards": CardRepository(con).count_all(tenant_id)}
        # R17 — route the destructive step through the ONE lifecycle: capture (rescue a good catalog) →
        # crypto-shred → wipe + free the email(s) → Stripe teardown (the ops path was missing this) →
        # surviving audit row. Idempotent.
        from .. import lifecycle
        # An agency's workspace tenant can't be wiped in isolation — its owner is the actor_user on ledger
        # rows in the agency's brand tenants (RESTRICT FK). Route it through the composite: brands first
        # (their ledger cascades away), then the agency, then the workspace + owner.
        if (t.get("tenant_kind") == "agency_workspace"):
            lifecycle.execute_agency_workspace(con, tenant_id, deleted_by=deleted_by)
        else:
            lifecycle.execute_brand(con, tenant_id, capture_seed=True, deleted_by=deleted_by)
        return JSONResponse({"ok": True, "deleted": summary})
    finally:
        con.close()

@router.get("/api/admin/deletions")
def admin_deletions(request: Request):
    require_admin(request)
    con = db.connect()
    try:
        return JSONResponse({"ok": True, "deletions": DeletedAccountAuditRepository(con).list_all()})
    finally:
        con.close()

@router.get("/api/admin/system")
def admin_system(request: Request):
    require_admin(request)
    con = db.connect()
    try:
        counts = SystemRepository(con).entity_counts()
        # last pull per source (Keepa / news / recalls / imports)
        srcs = PullLogRepository(con).sources_last_global()
        sources = []
        for s in srcs:
            d = dict(s)
            last = PullLogRepository(con).last_global_by_source(d["source"])
            ld = dict(last) if last else {}
            sources.append({"source": d["source"], "last_at": d["last_at"],
                            "status": ld.get("status"), "note": (ld.get("note") or "")[:80]})
    finally:
        con.close()
    dbpath = os.environ.get("REALIFY_DB", "realify_mc.db")
    try:
        db_bytes = os.path.getsize(dbpath)
    except OSError:
        db_bytes = None
    mode = os.environ.get("MODE", "fixture")
    keys = {"anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "keepa": bool(os.environ.get("KEEPA_KEY")),
            "news": bool(os.environ.get("NEWS_API_KEY"))}
    return JSONResponse({"ok": True, "counts": counts, "sources": sources,
                         "db_bytes": db_bytes, "mode": mode, "keys": keys})
