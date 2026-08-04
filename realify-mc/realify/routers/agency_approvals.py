"""Approvals cockpit + mobile approval routes (agency-plan P5, screens 22 & 15) — behind
AGENCY_CONSOLE, Postgres-only. Mobile approval: one decision per page, safe outcome stated,
device-remembered OTP (30-day cookie), decision ledgered. Cockpit: pending across the book with
days-to-expiry, nudge (Realify-delivered, cap 2), escalate. Brand pause-all halts in-flight execution."""
import html

from fastapi import APIRouter, Request, Depends
from realify.site.tokens import state_page as _state_page
from fastapi.responses import HTMLResponse, JSONResponse

from ..agency import approvals, execution, ledger, db as agency_db
from ..agency.actor import resolve_actor
from ..agency.guard import require_agency_console
from .deps import current, require_admin

router = APIRouter()
_DEVICE_COOKIE = "agency_device_otp"
_DEVICE_TTL = 30 * 24 * 3600


def _admin(request: Request):
    require_admin(request)
    return True


def _allowed(uid):
    conn = agency_db.agency_connect()
    try:
        ctx = resolve_actor(conn.cursor(), uid)
        conn.rollback()
        return list(ctx.allowed_tenant_ids)
    finally:
        conn.close()


async def _body(request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


@router.get("/agency/cockpit", response_class=HTMLResponse, dependencies=[Depends(require_agency_console)])
def cockpit(request: Request):
    uid, _ = current(request)
    if not uid:
        return HTMLResponse(_state_page("Sign in required", "This surface needs a signed-in session.", "Restricted"), status_code=401)
    conn = agency_db.agency_connect()
    try:
        items = approvals.pending(conn.cursor(), _allowed(uid))
    finally:
        conn.close()
    blocked = sum(i["impact_usd_minor"] for i in items)   # $/mo blocked across the book

    def chip(d):
        if d is None:
            return "<span class=chip>no expiry</span>"
        cls = "chip danger" if d <= 1 else ("chip warn" if d <= 2 else "chip")
        return f"<span class='{cls}'>{d}d to expiry</span>"
    rows = "".join(
        f"<tr><td>{i['id']}</td><td>{html.escape(i['lens'])}/{html.escape(i['kind'])}</td>"
        f"<td>${i['impact_usd_minor']/100:,.0f}</td><td>{chip(i['days_to_expiry'])}</td>"
        f"<td>{'viewed' if i['viewed'] else '<b>not viewed</b>'}</td>"
        f"<td>{i['nudge_count']}/2</td>"
        f"<td><button onclick=\"nudge({i['id']})\">Nudge</button>"
        f"<button onclick=\"escalate({i['id']})\">Escalate</button></td></tr>" for i in items)
    return HTMLResponse(
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'><title>Approvals cockpit</title>"
        "<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:900px;margin:0 auto;"
        "padding:26px 22px;background:#F4F0E8;color:#1A1A1A}table{border-collapse:collapse;width:100%;background:#fff}"
        "th,td{border:1px solid #EFEAE0;padding:9px 12px;text-align:left;font-size:13px}.chip{font-family:ui-monospace,"
        "monospace;font-size:11px;border-radius:100px;padding:2px 9px;background:#EAF0F5;color:#3E566A}"
        ".chip.warn{background:#F3EFE5;color:#8A7A55}.chip.danger{background:#F5E7E4;color:#B3402E}"
        "button{border-radius:8px;border:1px solid #DDD5C6;background:#fff;padding:6px 12px;cursor:pointer;margin-right:4px}"
        "</style></head><body><h1>Approvals cockpit</h1>"
        f"<p><b>${blocked/100:,.0f}/mo blocked</b> across {len(items)} pending approvals, sorted by expiry.</p>"
        "<p><b>Expired = not executed, ever.</b> The brand's 5-day clock protects brands; this view protects "
        "your velocity.</p>"
        "<table><tr><th>id</th><th>action</th><th>impact</th><th>expiry</th><th>viewed</th><th>nudges</th>"
        f"<th>do</th></tr>{rows}</table>"
        "<script>async function nudge(id){var r=await fetch('/api/agency/approvals/'+id+'/nudge',{method:'POST'});"
        "alert(r.ok?'Nudged.':'Nudge cap reached.');}"
        "async function escalate(id){await fetch('/api/agency/approvals/'+id+'/escalate',{method:'POST'});"
        "alert('Escalated.');}</script></body></html>")


@router.get("/agency/approve/{approval_id}", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console)])
def approve_page(approval_id: int, request: Request, token: str = ""):
    # `token` arrives on the emailed deep link; carry it into the form so the decision posts it back.
    # The signed token IS the verification — it is bound to (approval, user) and validated server-side.
    conn = agency_db.agency_connect()
    try:
        approvals.mark_viewed(conn.cursor(), approval_id)      # cockpit viewed/not-viewed signal
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()
    return HTMLResponse(
        f"<!doctype html><meta charset=utf-8><title>Approve</title><body style='font-family:system-ui;"
        f"max-width:520px;margin:40px auto'><h1>Approval #{approval_id}</h1>"
        f"<p><b>Safe outcome:</b> if you do nothing, this expires and is NOT executed.</p>"
        f"<form method=post action=/api/agency/approvals/{approval_id}/decide>"
        f"<input type=hidden name=token value='{html.escape(token)}'>"
        f"<button name=decision value=approve>Approve</button> "
        f"<button name=decision value=reject>Reject</button></form></body>")


@router.post("/api/agency/approvals/{approval_id}/decide", dependencies=[Depends(require_agency_console)])
async def decide(approval_id: int, request: Request):
    from ..agency import execution, mock_marketplace, tenancy
    b = await _body(request)
    decision = (b.get("decision") or "").strip()
    token = (b.get("token") or request.query_params.get("token") or "").strip()
    uid_hint = (b.get("uid") or request.query_params.get("uid") or "").strip()
    # Consult (not just set) the signed device token: is this device already OTP-verified?
    device_verified = approvals.verify_otp_skip_token(request.cookies.get(_DEVICE_COOKIE) or "")
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        # Set the actor GUC so the approvals deep-link self-read policy (migration 0029) lets a brand
        # co-signer (who holds no agency grant) read THIS approval under RLS.
        if uid_hint:
            cur.execute("SELECT set_config('app.actor_user_id', %s, true)", (uid_hint,))
        # Verification: the deep-link token must match the issued (approval, user) hash. Absent/wrong
        # token -> 403 (no free-pass). The acting user is the one the link was issued to.
        actor_uid = approvals.resolve_deeplink(cur, approval_id, token)
        if not actor_uid:
            conn.rollback()
            return JSONResponse({"ok": False, "error": "invalid or expired approval link"}, status_code=403)
        a = approvals._load(cur, approval_id)
        tenancy.set_brand_scope(cur, [a["tenant_id"]])       # scope for the write path
        if decision == "approve":
            if a["status"] == "cosign_pending":
                res = approvals.cosign(cur, approval_id, actor_uid)     # brand co-sign
            else:
                res = approvals.approve(cur, approval_id, actor_uid)    # maker-checker
            if res["status"] == "approved":                            # reaching approved -> execute
                ex = execution.execute_approval(cur, mock_marketplace.get_mock(), approval_id)
                if ex["executed"]:
                    res = {"status": "executed"}
        elif decision == "reject":
            cur.execute("UPDATE approvals SET status='rejected', updated_at=now() WHERE id=%s", (approval_id,))
            ledger.append(cur, a["tenant_id"], actor_uid, "approval.reject", payload={"approval_id": approval_id})
            res = {"status": "rejected"}
        else:
            conn.rollback()
            return JSONResponse({"ok": False, "error": "decision must be approve|reject"}, status_code=400)
        conn.commit()
    except approvals.ApprovalError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()
    resp = JSONResponse({"ok": True, "device_verified": device_verified, **res})
    resp.set_cookie(_DEVICE_COOKIE, approvals.make_otp_skip_token(), max_age=_DEVICE_TTL,
                    httponly=True, samesite="lax")
    return resp


@router.post("/api/agency/approvals/{approval_id}/nudge", dependencies=[Depends(require_agency_console)])
def nudge(approval_id: int):
    conn = agency_db.agency_connect()
    try:
        res = approvals.nudge(conn.cursor(), approval_id)
        conn.commit()
        return JSONResponse({"ok": True, **res})
    except approvals.ApprovalError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()


@router.post("/api/agency/approvals/{approval_id}/escalate", dependencies=[Depends(require_agency_console)])
def escalate(approval_id: int):
    conn = agency_db.agency_connect()
    try:
        res = approvals.escalate(conn.cursor(), approval_id)
        conn.commit()
        return JSONResponse({"ok": True, **res})
    finally:
        conn.close()


@router.post("/api/agency/tenants/{tenant_id}/pause",
             dependencies=[Depends(require_agency_console), Depends(_admin)])
def pause_all(tenant_id: int):
    conn = agency_db.agency_connect()
    try:
        execution.pause_all(conn.cursor(), tenant_id)
        conn.commit()
        return JSONResponse({"ok": True, "tenant_id": tenant_id, "paused": True})
    finally:
        conn.close()
