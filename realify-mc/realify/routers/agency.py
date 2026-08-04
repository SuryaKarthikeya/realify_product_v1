"""Agency funnel routes (agency-plan P2) — feature-flagged behind AGENCY_CONSOLE, Postgres-only.

Public: intake form + submit, applicant status page. Internal (admin-key gated): review queue + detail,
approve->provision / decline / retry, ops tenants list + normal<->internal toggle. Provisioning is
idempotent + step-tracked (realify.agency.provision); decline emails a reasoned note to the mailbox.
"""
import html

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .. import mail, config, auth, db
from ..agency import funnel, provision as prov, internal, invites, db as agency_db, mailcfg
from ..site import ui_agencies
from ..agency.guard import require_agency_console
from .deps import require_admin

router = APIRouter()
_ACTOR = "ops"


async def _form_or_json(request: Request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


def _admin(request: Request):
    """Staff gate for the /ops agency-review actions. Operators reach /ops via the 8h superlogin COOKIE,
    so these action endpoints (approve/decline/retry) MUST accept it — not just the admin-key header.
    (Bug: they were key-only, so the review-queue Approve/Reject buttons 403'd silently for a cookie-authed
    operator. Mirrors agency_admin._admin.)"""
    from .. import superlogin
    if superlogin.verify_session(request.cookies.get("superlogin_session") or ""):
        return True
    require_admin(request)
    return True


def _page(title, body):
    return HTMLResponse(f"<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title>"
                        f"<body style='font-family:system-ui;max-width:760px;margin:40px auto;padding:0 16px'>"
                        f"<h1>{html.escape(title)}</h1>{body}</body>")


# ---------------- public: intake ----------------
# The public application form lives on the /agencies marketing landing (#apply); /agencies/apply
# 301s there (see routers.marketing). This router keeps only the flag-gated POST + status pages.
@router.post("/api/agencies/intake", dependencies=[Depends(require_agency_console)])
async def intake(request: Request):
    try:
        form = dict(await request.form())
    except Exception:
        form = {}
    if not form:
        try:
            form = await request.json()
        except Exception:
            form = {}
    try:
        cleaned = funnel.validate_intake(form)
    except funnel.HoneypotError:
        return JSONResponse({"ok": True})          # silent drop — no row, no signal to bots
    except funnel.IntakeError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        ref = funnel.create_request(cur, cleaned)
        conn.commit()
    finally:
        conn.close()
    # Notify the ops inbox (REPLY_TO_ADDRESS) of the new request — best-effort: a mail hiccup must never
    # fail the applicant's submission (the row is already committed) or trigger a duplicate resubmit.
    try:
        base = (config.APP_URL or "https://realifyai.app").rstrip("/")
        # R16 — notify a MONITORED operator inbox (ops_recipient → shiva@, not the no-reply forwarder), with
        # branded HTML + a link to the admin review queue (/ops/agency/admin) where it can be approved.
        subject, body, html_body = funnel.new_request_notification(ref, cleaned, f"{base}/ops/agency/admin")
        mail.send(mailcfg.ops_recipient(), subject, body, from_addr=mailcfg.from_addr(),
                  reply_to=cleaned["contact_email"], html=html_body)
    except Exception as e:                              # pragma: no cover - defensive
        print(f"[agency-intake] new-request notification failed for {ref}: {e}", flush=True)
    # Applicant confirmation email carrying the status-page link (best-effort).
    try:
        base = (config.APP_URL or "https://realifyai.app").rstrip("/")
        mail.send(cleaned["contact_email"], "We received your Realify for Agencies application",
                  f"Thanks — your application (reference {ref}) is in. A human reads this; we'll get back "
                  f"to you within 2 business days.\n\nTrack your status here:\n{base}/agencies/status/{ref}",
                  from_addr=mailcfg.from_addr(), reply_to=mailcfg.reply_to())
    except Exception as e:                              # pragma: no cover - defensive
        print(f"[agency-intake] applicant confirmation failed for {ref}: {e}", flush=True)
    return JSONResponse({"ok": True, "ref": ref, "status_url": f"/agencies/status/{ref}"})


# ---------------- public: status ----------------
@router.get("/agencies/status/{ref}", response_class=HTMLResponse, dependencies=[Depends(require_agency_console)])
def status_page(ref: str):
    conn = agency_db.agency_connect()
    try:
        req = funnel.get_request(conn.cursor(), ref)
    finally:
        conn.close()
    if not req:
        return HTMLResponse(ui_agencies.status_not_found())
    return HTMLResponse(ui_agencies.status_page(
        ref, req["status"], funnel.timeline(req["status"]), req.get("decline_reason")))


# ---------------- public: agency admin invite acceptance ----------------
@router.get("/agency/invite/{token}", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console)])
def invite_page(token: str):
    conn = agency_db.agency_connect()
    try:
        inv = invites.preview(conn.cursor(), token)
    finally:
        conn.close()
    from ..site import ui
    if not inv:
        return HTMLResponse(ui.invite_invalid_page())
    # R17.2 — branded, in-site setup page with an AJAX submit that signs the operator in and lands them
    # in the agency console (was: a bare unstyled page whose plain form POST rendered raw JSON).
    return HTMLResponse(ui.invite_setup_page(inv["email"], token))


@router.post("/api/agency/invite/{token}/accept", dependencies=[Depends(require_agency_console)])
async def invite_accept(token: str, request: Request):
    """Consume the single-use, 7-day invite; create the admin's account (sets password); start a session
    and land in the agency workspace. The invite is consumed only AFTER the account is created, so a bad
    password doesn't burn the link."""
    b = await _form_or_json(request)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        inv = invites.preview(cur, token)
        if not inv:
            return JSONResponse({"ok": False, "error": "invalid or used invite"}, status_code=409)
        cur.execute("SELECT name FROM agencies WHERE id=%s", (inv["agency_id"],))
        row = cur.fetchone()
        agency_name = (row[0] if row else inv["email"].split("@")[0])
        new_user = True
        try:
            uid, tid = auth.signup(inv["email"], b.get("password") or "", agency_name)
        except ValueError as e:
            # Existing Realify account: don't reset their password or auto-login (the token proves email,
            # not intent to change credentials). Just add them to the agency; they sign in as themselves.
            cur.execute("SELECT id FROM users WHERE email=%s", (inv["email"],))
            r = cur.fetchone()
            if not r:
                return JSONResponse({"ok": False, "error": str(e)}, status_code=400)   # genuinely bad password
            uid, tid, new_user = r[0], None, False
        invites.accept(cur, token)                 # single-use: consume now that membership is being created
        # R10/R19: join the EXISTING agency as a member with the invite's role (all-brands agency_admin →
        # sees the whole hub). The FIRST accepter becomes the agency OWNER (may manage the team).
        from ..agency import team
        team.add_member(cur, inv["agency_id"], uid, inv.get("role") or "agency_admin")
        cur.execute("UPDATE agencies SET owner_user_id=%s WHERE id=%s AND owner_user_id IS NULL",
                    (uid, inv["agency_id"]))
        conn.commit()
    finally:
        conn.close()
    if not new_user:                               # existing account → sign in with their own credentials
        return JSONResponse({"ok": True, "existing": True, "redirect": "/signin",
                             "message": "You're on the team — sign in to open the agency console."})
    # The agency-admin login tenant is a workspace, not a seller brand (the agency is billed via
    # agency_subscriptions), so classify it tenant_kind='agency_workspace' — excluded from billable/drift
    # aggregates. is_internal kept in sync (deprecated).
    _c = db.connect()
    try:
        _c.execute("UPDATE tenants SET is_internal=?, tenant_kind=? WHERE id=?",
                   (True, "agency_workspace", tid)); _c.commit()
    finally:
        _c.close()
    request.session["uid"] = uid; request.session["tid"] = tid
    return JSONResponse({"ok": True, "redirect": "/agency/console"})


# ---------------- internal: review queue + detail ----------------
@router.get("/ops/agencies", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console), Depends(_admin)])
def review_queue():
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT ref,agency_name,hq_country,status,created_at FROM agency_requests "
                    "ORDER BY created_at DESC")
        rows = cur.fetchall()
    finally:
        conn.close()
    items = "".join(
        f"<tr><td><a href=/ops/agencies/{html.escape(r[0])}>{html.escape(r[0])}</a></td>"
        f"<td>{html.escape(r[1])}</td><td>{html.escape(r[2])}</td><td>{html.escape(r[3])}</td></tr>"
        for r in rows)
    return _page("Agency review queue",
                 f"<table border=1 cellpadding=6><tr><th>ref</th><th>agency</th><th>hq</th><th>status</th></tr>{items}</table>")


@router.get("/ops/agencies/{ref}", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console), Depends(_admin)])
def review_detail(ref: str):
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        req = funnel.get_request(cur, ref)
        if not req:
            return _page("Not found", "<p>No such request.</p>")
        if req["status"] == "received":               # opening the detail moves it to in-review
            funnel.set_status(cur, req["id"], "in_review")
            conn.commit()
            req["status"] = "in_review"
        cur.execute("SELECT step,status,error FROM agency_provision_steps WHERE request_id=%s ORDER BY step",
                    (req["id"],))
        steps = cur.fetchall()
        # "Invite emailed" is asserted ONLY when the ledgered send exists (agency_audit) — not merely
        # because the admin_invite step ran (the step could complete a re-use path without a send).
        invite_emailed = False
        if req.get("agency_id"):
            cur.execute("SELECT 1 FROM agency_audit WHERE agency_id=%s AND action='agency.invite_emailed' "
                        "LIMIT 1", (req["agency_id"],))
            invite_emailed = cur.fetchone() is not None
    finally:
        conn.close()
    steps_html = "".join(f"<li>{html.escape(s[0])}: <b>{html.escape(s[1])}</b>"
                         f"{(' — ' + html.escape(s[2])) if s[2] else ''}</li>" for s in steps)
    invite_html = (f"<p>✉ Invite emailed to {html.escape(req['contact_email'])}</p>" if invite_emailed
                   else "<p><i>Invite not emailed yet.</i></p>")
    return _page(f"Request {html.escape(ref)}",
        f"<p>{html.escape(req['agency_name'])} · {html.escape(req['contact_email'])} · HQ {html.escape(req['hq_country'])}</p>"
        f"<p>Status: <b>{html.escape(req['status'])}</b></p>"
        f"<ul>{steps_html}</ul>{invite_html}"
        f"<form method=post action=/api/ops/agencies/{html.escape(ref)}/approve><button>Approve &amp; provision</button></form>"
        f"<form method=post action=/api/ops/agencies/{html.escape(ref)}/decline>"
        f"<input name=reason placeholder='reason'><button>Decline</button></form>")


# ---------------- internal: approve / decline / retry ----------------
def _get_or_404(cur, ref):
    req = funnel.get_request(cur, ref)
    return req


@router.post("/api/ops/agencies/{ref}/approve",
             dependencies=[Depends(require_agency_console), Depends(_admin)])
def approve(ref: str):
    conn = agency_db.agency_connect()
    try:
        req = _get_or_404(conn.cursor(), ref)
        if not req:
            return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
        if req["status"] == "declined":
            return JSONResponse({"ok": False, "error": "already declined"}, status_code=409)
        result = prov.provision(conn, req["id"], actor=_ACTOR)
        return JSONResponse({"ok": result["ok"], "status": result["status"],
                             "failed_step": result["failed_step"]})
    finally:
        conn.close()


@router.post("/api/ops/agencies/{ref}/retry",
             dependencies=[Depends(require_agency_console), Depends(_admin)])
def retry(ref: str):
    return approve(ref)


@router.post("/api/ops/agencies/{ref}/decline",
             dependencies=[Depends(require_agency_console), Depends(_admin)])
async def decline(ref: str, request: Request):
    try:
        body = dict(await request.form()) or await request.json()
    except Exception:
        body = {}
    reason = (body.get("reason") or "").strip() or "not a fit at this time"
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        req = _get_or_404(cur, ref)
        if not req:
            return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
        funnel.set_status(cur, req["id"], "declined")
        cur.execute("UPDATE agency_requests SET decline_reason=%s WHERE id=%s", (reason, req["id"]))
        agency_db.audit(cur, _ACTOR, "agency.declined", detail={"ref": ref}, reason=reason)
        conn.commit()
    finally:
        conn.close()
    mail.send(req["contact_email"], "Your Realify for Agencies application",
              f"Thank you for applying. We won't be moving forward right now. Reason: {reason}. "
              f"We've added you to our waitlist and will reach out if that changes.",
              reply_to="notifications@realifyai.app")
    return JSONResponse({"ok": True})


# ---------------- internal: tenants list + toggle ----------------
@router.get("/ops/tenants", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console), Depends(_admin)])
def tenants_list():
    conn = agency_db.agency_connect()
    try:
        rows = internal.list_tenants(conn.cursor())
    finally:
        conn.close()
    items = "".join(
        f"<tr><td>{r['id']}</td><td>{html.escape(r['email'] or '')}</td>"
        f"<td>{html.escape(str(r['created_at']))}</td><td>{html.escape(r['subscription_status'] or '')}</td>"
        f"<td>{'yes' if r['is_internal'] else 'no'}</td>"
        f"<td><form method=post action=/api/ops/tenants/{r['id']}/internal>"
        f"<input type=hidden name=to_internal value={'false' if r['is_internal'] else 'true'}>"
        f"<input name=reason placeholder=reason><button>{'unmark' if r['is_internal'] else 'mark internal'}</button>"
        f"</form></td></tr>" for r in rows)
    return _page("Tenants",
                 f"<table border=1 cellpadding=6><tr><th>id</th><th>email</th><th>created</th>"
                 f"<th>stripe</th><th>internal</th><th></th></tr>{items}</table>")


@router.post("/api/ops/tenants/{tenant_id}/internal",
             dependencies=[Depends(require_agency_console), Depends(_admin)])
async def toggle_tenant_internal(tenant_id: int, request: Request):
    try:
        body = dict(await request.form()) or await request.json()
    except Exception:
        body = {}
    to_internal = str(body.get("to_internal", "true")).strip().lower() in ("true", "1", "yes", "on")
    reason = (body.get("reason") or "").strip() or None
    conn = agency_db.agency_connect()
    try:
        new_val = internal.toggle_internal(conn, _ACTOR, tenant_id, to_internal, reason=reason)
    finally:
        conn.close()
    return JSONResponse({"ok": True, "tenant_id": tenant_id, "is_internal": new_val})
