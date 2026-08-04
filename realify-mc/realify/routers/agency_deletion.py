"""R17 — the deletion close-out queue ACTIONS (split from agency_admin.py to stay under the file-length
cap). Request → settle (mark paid up) → execute (hard wipe, gated on billing unless overridden) → cancel.
Admin-gated; every step best-effort-audited. The queue RENDER lives on /ops/agency/admin (agency_admin)."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from .. import db, lifecycle
from ..agency import db as agency_db
from ..agency.guard import require_agency_console
from .agency_admin import _admin, _body

router = APIRouter()


def _deletion_actor(request):
    try:
        return "ops · " + (request.cookies.get("superlogin_session") and "superlogin" or "admin-key")
    except Exception:
        return "ops-console"


def _ops_audit(request, action, req, reason=None):
    """Best-effort append to the agency audit trail (PG-only; survives on the un-FK'd deletion side)."""
    try:
        from .. import dbengine
        if dbengine.dialect() != "postgresql":
            return
        conn = agency_db.agency_connect()
        try:
            agency_db.audit(conn.cursor(), _deletion_actor(request), action,
                            detail={"request_id": req.get("id"), "entity_type": req.get("entity_type"),
                                    "entity_ref": req.get("entity_ref")}, reason=reason)
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


@router.post("/api/ops/deletions/request", dependencies=[Depends(require_agency_console), Depends(_admin)])
async def ops_deletion_request(request: Request):
    """Enqueue an entity for deletion. Brand/agency with an open balance parks in HOLD; anything already
    settled (tester, canceled sub, no invoices) goes straight to READY."""
    b = await _body(request)
    et = (b.get("entity_type") or "").strip()
    ref = str(b.get("entity_ref") or "").strip()
    if et not in ("brand", "user", "agency") or not ref:
        return JSONResponse({"ok": False, "error": "entity_type ∈ brand|user|agency + entity_ref required"}, status_code=400)
    con = db.connect()
    try:
        label = None
        capture = False
        acct = et
        if et == "brand":
            t = db.get_tenant(con, int(ref)) if ref.isdigit() else None
            if not t:
                return JSONResponse({"ok": False, "error": "no such brand"}, status_code=404)
            label = t.get("name"); acct = lifecycle.account_type_of(con, int(ref))
            capture = lifecycle.catalog_is_capturable(con, int(ref))
        settled = lifecycle.billing_settled(con, et, ref)
        rid = lifecycle.create_request(con, et, ref, label, _deletion_actor(request), acct,
                                       status=("ready" if settled else "hold"),
                                       capture_seed=capture, reason=(b.get("reason") or "").strip() or None)
        if settled:
            lifecycle.mark_settled(con, rid)
        return JSONResponse({"ok": True, "id": rid, "status": ("ready" if settled else "hold")})
    finally:
        con.close()


@router.post("/api/ops/deletions/{req_id}/settle", dependencies=[Depends(require_agency_console), Depends(_admin)])
async def ops_deletion_settle(req_id: int, request: Request):
    """Mark paid up: settle billing (cancel the Stripe sub / mark agency invoices paid) → hold→ready."""
    b = await _body(request)
    con = db.connect()
    try:
        req = lifecycle.get_request(con, req_id)
        if not req or req["status"] not in ("requested", "hold"):
            return JSONResponse({"ok": False, "error": "not pending"}, status_code=409)
        lifecycle.settle_billing(con, req)                 # cancels Stripe / marks invoices paid (best-effort)
        lifecycle.mark_settled(con, req_id, override_reason=(b.get("override_reason") or "").strip() or None)
        lifecycle.set_status(con, req_id, "ready")
        _ops_audit(request, "deletion.settled", req)
        return JSONResponse({"ok": True, "status": "ready"})
    finally:
        con.close()


@router.post("/api/ops/deletions/{req_id}/execute", dependencies=[Depends(require_agency_console), Depends(_admin)])
async def ops_deletion_execute(req_id: int, request: Request):
    """Hard wipe. Blocked unless billing is settled, UNLESS an override_reason is supplied (R17 dec.3)."""
    b = await _body(request)
    override = (b.get("override_reason") or "").strip()
    con = db.connect()
    try:
        req = lifecycle.get_request(con, req_id)
        if not req or req["status"] in ("wiped", "canceled"):
            return JSONResponse({"ok": False, "error": "not actionable"}, status_code=409)
        if not req["billing_settled"] and not override:
            return JSONResponse({"ok": False, "error": "billing not settled — settle first or supply an override reason."}, status_code=409)
        if override and not req["billing_settled"]:
            lifecycle.mark_settled(con, req_id, override_reason=override)   # ledger the override; ungate
            _ops_audit(request, "deletion.override", req, reason=override)
        fresh = lifecycle.get_request(con, req_id)
        if fresh["status"] in ("requested", "hold"):                        # advance to ready before the wipe
            lifecycle.set_status(con, req_id, "ready")
        res = lifecycle.execute(con, lifecycle.get_request(con, req_id), deleted_by=_deletion_actor(request))
        lifecycle.set_status(con, req_id, "wiped")
        _ops_audit(request, "deletion.executed", req)
        return JSONResponse({"ok": True, "result": res})
    finally:
        con.close()


@router.post("/api/ops/deletions/{req_id}/cancel", dependencies=[Depends(require_agency_console), Depends(_admin)])
async def ops_deletion_cancel(req_id: int, request: Request):
    con = db.connect()
    try:
        req = lifecycle.get_request(con, req_id)
        if not req or req["status"] in ("wiped", "canceled"):
            return JSONResponse({"ok": False, "error": "not actionable"}, status_code=409)
        lifecycle.set_status(con, req_id, "canceled")
        _ops_audit(request, "deletion.canceled", req)
        return JSONResponse({"ok": True, "status": "canceled"})
    finally:
        con.close()
