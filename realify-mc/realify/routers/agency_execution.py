"""Agency execution-control routes (R2/R3): bulk canary rollout + halt/rollback, and per-item Undo.
Split from agency_console to stay under the file-line cap. Behind AGENCY_CONSOLE, Postgres-only."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from ..agency import approvals, execution, toctou, tenancy, mock_marketplace, db as agency_db
from ..agency.guard import require_agency_console
from ..pdp import Action
from .agency_console import _qbody, _allowed, _uid_or_401

router = APIRouter()


@router.post("/api/agency/queue/bulk", dependencies=[Depends(require_agency_console)])
async def queue_bulk(request: Request):
    """Bulk execution across accounts with canary rollout + halt/rollback (P5). Only proceeds when the
    lens is execute-allowed, no co-sign, and below threshold; otherwise returns 'proposed'."""
    uid = _uid_or_401(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    b = await _qbody(request)
    tenant_id = int(b.get("tenant_id") or 0)
    if tenant_id not in _allowed(uid):
        return JSONResponse({"ok": False, "error": "not permitted for this brand"}, status_code=403)
    lens, kind, signal = b.get("lens", ""), b.get("kind", ""), b.get("signal", "")
    impact = int(b.get("impact_usd_minor") or 0)
    accounts = list(b.get("accounts") or [])
    canary_size = int(b.get("canary_size") or 1)
    force_breach = bool(b.get("breach"))              # canary-breach test hook
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])                  # RLS: scope before brand-table reads
        cur.execute("SELECT id FROM engagements WHERE tenant_id=%s AND status='active' LIMIT 1", (tenant_id,))
        row = cur.fetchone()
        if not row:
            return JSONResponse({"ok": False, "error": "no active engagement"}, status_code=400)
        eng = row[0]
        version, caps = toctou.current_envelope(cur, eng)
        maxk = (caps or {}).get(lens, {}).get("max_kind", "propose")
        requires_cosign = approvals.cosign_required(cur, eng, lens, kind, impact)
        aid = approvals.propose(cur, tenant_id, eng, uid, lens, kind, signal, impact,
                                requires_cosign=requires_cosign, envelope_version=version)
        if maxk != "execute" or requires_cosign or impact >= approvals._threshold(cur, eng):
            conn.commit()
            return JSONResponse({"ok": True, "approval_id": aid, "status": "proposed"})
        approvals.approve(cur, aid, uid)
        breach_fn = (lambda res, mock: len(res["executed"]) >= canary_size) if force_breach else None
        res = execution.execute_bulk(cur, mock_marketplace.get_mock(), tenant_id, aid, eng, version,
                                     execution.maker_grant_caps(cur, uid, eng), Action(lens, "execute"),
                                     accounts, value_fn=lambda a: {"lens": lens, "kind": kind},
                                     canary_size=canary_size, breach_fn=breach_fn)
        if res["executed"] and not res["halted"]:
            cur.execute("UPDATE approvals SET status='executed', updated_at=now() WHERE id=%s", (aid,))
        conn.commit()
        return JSONResponse({"ok": True, "approval_id": aid, "result": {
            "executed": len(res["executed"]), "excluded": len(res["excluded"]),
            "rolledback": len(res["rolledback"]), "halted": res["halted"],
            "halt_reason": res["halt_reason"]}})
    except approvals.ApprovalError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()


@router.post("/api/agency/executions/{execution_id}/undo", dependencies=[Depends(require_agency_console)])
async def execution_undo(execution_id: int, request: Request):
    """Per-item Undo — restore the execution's pre-state snapshot on the mock, mark it rolledback,
    ledger it. Scoped: the execution's brand must be in the actor's allowed set."""
    uid = _uid_or_401(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    allowed = _allowed(uid)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        if allowed:
            tenancy.set_brand_scope(cur, allowed)
        cur.execute("SELECT tenant_id FROM executions WHERE id=%s", (execution_id,))
        row = cur.fetchone()
        if not row or row[0] not in allowed:
            return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
        res = execution.undo_execution(cur, execution_id, actor=uid)
        conn.commit()
        return JSONResponse({"ok": True, **res})
    except ValueError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()
