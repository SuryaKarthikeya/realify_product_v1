"""Auth, identity, org members & invites — split from run.py in #005 1a/1f. Handlers moved verbatim; behavior unchanged."""
import os, json
from fastapi import APIRouter, Request, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, PlainTextResponse
from realify import db, config, auth, scheduler, api, statuscheck, opsdoc, analytics, billing
from realify.repositories.card_repo import CardRepository
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.pull_repo import PullLogRepository
from realify.repositories.metrics_repo import MetricsRepository
from realify.repositories.tenant_repo import TenantRepository
from realify.repositories.user_repo import UserRepository
from realify.repositories.channel_repo import ChannelRepository
from realify.repositories.analytics_repo import AnalyticsRepository, SystemRepository
from .deps import current, require_tenant, require_admin, _admin_key_ok, superlogin_key_ok, is_staff_email
from .helpers import page, _track, _log_import, _is_customer, ads_preview_allowed, BASE_DIR as HERE

router = APIRouter()


def mint_operator_tenant(email, password, account):
    """Create an operator/back-door org: no pay funnel, paid access synthesized, and tagged
    is_internal by construction (never billed, excluded from aggregates). Returns (uid, tid)."""
    uid, tid = auth.signup(email, password, account)
    billing.synthesize_paid(tid)                 # back-door accounts are paid (no Stripe)
    _c = db.connect()
    try:                                         # tenant_kind='internal' (is_internal kept in sync, deprecated)
        _c.execute("UPDATE tenants SET is_internal=?, tenant_kind=? WHERE id=?",
                   (True, "internal", tid)); _c.commit()
    finally:
        _c.close()
    return uid, tid


@router.post("/api/signup")
async def signup(request: Request):
    """Operator BACK DOOR account-minting endpoint. GATED (P0.9): requires a valid ADMIN_KEY_HASH admin
    key AND an @realify.ai staff email, else this endpoint does not exist. Public visitors use
    /api/billing/signup. (The hardened, session-based operator surface is /superlogin/operator/*.)"""
    b = await request.json()
    if not superlogin_key_ok(request, b.get("admin_key")):
        return JSONResponse({"ok": False, "error": "Not Found"}, status_code=404)   # no key -> no surface
    if not is_staff_email(b.get("email", "")):
        return JSONResponse({"ok": False, "error": "Back-door signup is limited to @realify.ai staff."},
                            status_code=403)
    try:
        uid, tid = mint_operator_tenant(b.get("email",""), b.get("password",""), b.get("account"))
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    request.session["uid"] = uid; request.session["tid"] = tid
    _track(request, "login", page="signup")
    return JSONResponse({"ok": True, "provisioned": False})


@router.post("/superlogin/operator/create-tenant")
async def operator_create_tenant(request: Request):
    """Legacy operator function (create internal tenant), moved into the hardened hub. Requires the SAME
    superlogin session (the 8h ledgered cookie) — not the raw admin key — and keeps the is_internal
    auto-tag. Without a valid session the surface does not exist (404)."""
    from .. import superlogin
    if not superlogin.verify_session(request.cookies.get("superlogin_session") or ""):
        return JSONResponse({"ok": False, "error": "Not Found"}, status_code=404)
    b = await request.json()
    if not is_staff_email(b.get("email", "")):
        return JSONResponse({"ok": False, "error": "Back-door signup is limited to @realify.ai staff."},
                            status_code=403)
    try:
        _uid, tid = mint_operator_tenant(b.get("email",""), b.get("password",""), b.get("account"))
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return JSONResponse({"ok": True, "tenant_id": tid})

def _agency_login_redirect(uid):
    """R17.2 — the SAME /signin serves brands and agencies: if the signed-in user is an agency team member,
    route them to the agency console (a brand owner falls through to the seller app). Postgres-only +
    best-effort — a lookup hiccup never blocks a normal login."""
    try:
        from .. import dbengine
        if dbengine.dialect() != "postgresql":
            return None
        from ..agency.db import agency_connect
        conn = agency_connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM agency_members WHERE user_id=%s LIMIT 1", (uid,))
            member = cur.fetchone() is not None
            conn.rollback()
            return "/agency/console" if member else None
        finally:
            conn.close()
    except Exception:                                          # pragma: no cover - defensive
        return None


@router.post("/api/login")
async def login(request: Request):
    b = await request.json()
    res = auth.login(b.get("email",""), b.get("password",""))
    if not res: return JSONResponse({"ok": False, "error": "Invalid email or password."}, status_code=401)
    uid, tid = res
    request.session["uid"] = uid; request.session["tid"] = tid
    _track(request, "login", page="login")
    con=db.connect(); t=db.get_tenant(con, tid); con.close()
    out = {"ok": True, "provisioned": bool(t and t["provisioned"])}
    redirect = _agency_login_redirect(uid)                     # agency members → the console, not the seller app
    if redirect:
        out["redirect"] = redirect
    return JSONResponse(out)

@router.post("/api/account/delete")
async def account_delete(request: Request):
    """Self-service deletion. Requires re-entered password. Resolves the action from role +
    member count: single-member org or owner of a multi-member org -> full org delete
    (frees the email for reuse); non-owner of a multi-member org -> leave organization."""
    uid, tid = current(request)
    if not tid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    b = await request.json()
    pw = b.get("password", "")
    confirm = (b.get("confirm") or "").strip().lower()
    con = db.connect()
    try:
        user = db.get_user_by_id(con, uid)
        if not user or not auth.verify_password(pw, user["pw_hash"], user["pw_salt"]):
            return JSONResponse({"ok": False, "error": "Password is incorrect."}, status_code=403)
        members = db.count_members(con, tid)
        role = (user.get("role") or "member")
        full_delete = (members <= 1) or (role == "owner")
        if full_delete:
            if confirm != "delete":
                return JSONResponse({"ok": False, "error": 'Type "delete" to confirm.'}, status_code=400)
            # R17 — route through the ONE deletion lifecycle. Decision 6: a tester (or any zero-balance
            # account) wipes immediately (capture → crypto-shred → wipe → Stripe teardown → audit); a
            # customer with an OPEN balance parks in the ops close-out queue instead of hitting a dead
            # end, and their account stays live until an operator settles + executes it.
            from .. import lifecycle
            if lifecycle.billing_settled(con, "brand", tid):
                lifecycle.execute_brand(con, tid, capture_seed=True, deleted_by="self-serve")
                action = "deleted_org"
            else:
                nm = (db.get_tenant(con, tid) or {}).get("name")
                lifecycle.create_request(con, "brand", tid, nm, (user.get("email") or "self-serve"),
                                         "customer", status="hold",
                                         capture_seed=lifecycle.catalog_is_capturable(con, tid),
                                         reason="self-serve delete (balance open)")
                action = "pending_closeout"
        else:
            db.delete_user(con, uid)
            action = "left_org"
    finally:
        con.close()
    if action != "pending_closeout":                 # a pending close-out keeps the account (and session) live
        request.session.clear()
    return JSONResponse({"ok": True, "action": action})

@router.post("/api/logout")
def logout(request: Request):
    request.session.clear(); return JSONResponse({"ok": True})

# --- organization invites: join flow ---

@router.get("/api/invite/preview")
def invite_preview(request: Request, token: str = ""):
    pv = auth.invite_preview(token)
    if not pv:
        return JSONResponse({"ok": False, "error": "This invite link is invalid, used, or expired."}, status_code=400)
    return JSONResponse({"ok": True, **pv})

@router.post("/api/join")
async def join(request: Request):
    b = await request.json()
    try:
        uid, tid = auth.accept_invite(b.get("password", ""), b.get("token", ""))
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    request.session["uid"] = uid; request.session["tid"] = tid
    _track(request, "login", page="join")
    con = db.connect(); t = db.get_tenant(con, tid); con.close()
    return JSONResponse({"ok": True, "provisioned": bool(t and t["provisioned"])})

@router.post("/api/account/password")
async def account_password(request: Request):
    """Authenticated in-app password change: verify the current password, then set the new one.
    Distinct from the emailed reset flow. Session-identity only — never trusts a client user id."""
    uid, tid = current(request)
    if not uid or not tid:
        return JSONResponse({"ok": False, "error": "Sign in to change your password."}, status_code=401)
    try:
        b = await request.json()
    except Exception:
        b = {}
    cur_pw, new_pw = (b.get("current") or ""), (b.get("new") or "")
    if len(new_pw) < 6:
        return JSONResponse({"ok": False, "error": "New password must be at least 6 characters."}, status_code=400)
    con = db.connect()
    try:
        u = UserRepository(con).get_by_id(uid)
        if not u or not auth.verify_password(cur_pw, u["pw_hash"], u["pw_salt"]):
            return JSONResponse({"ok": False, "error": "Current password is incorrect."}, status_code=400)
        pw_hash, pw_salt = auth.hash_password(new_pw)
        UserRepository(con).set_password(uid, pw_hash, pw_salt)
        con.commit()
    finally:
        con.close()
    return JSONResponse({"ok": True})


@router.post("/api/account/avatar")
async def account_avatar(request: Request):
    """Set the signed-in user's avatar (a small data-URL image). Capped to keep it inline; clears on empty."""
    uid, tid = current(request)
    if not uid or not tid:
        return JSONResponse({"ok": False, "error": "Sign in first."}, status_code=401)
    try:
        b = await request.json()
    except Exception:
        b = {}
    av = b.get("avatar") or ""
    if av and (not av.startswith("data:image/") or len(av) > 400_000):
        return JSONResponse({"ok": False, "error": "Use an image under ~300 KB."}, status_code=400)
    con = db.connect()
    try:
        UserRepository(con).set_avatar(uid, av or None)
        con.commit()
    finally:
        con.close()
    return JSONResponse({"ok": True})


@router.get("/api/me")
def me(request: Request):
    uid, tid = current(request)
    if not tid: return JSONResponse({"authed": False})
    con=db.connect(); t=db.get_tenant(con, tid)
    if not t:
        # Session points to a tenant that no longer exists (deleted account or a reset DB).
        # Treat as logged out: clear the stale session so the client routes to /login,
        # rather than 500ing on a missing tenant.
        con.close()
        try: request.session.clear()
        except Exception: pass
        return JSONResponse({"authed": False})
    from realify import country as country_mod
    from realify import flags as _flags
    prof = country_mod.tenant_profile(tid)
    terms = country_mod.tenant_terms(tid, con)
    acct_type = db.get_account_type(con, tid) if t else None
    me_user = db.get_user_by_id(con, uid) if uid else None
    member_count = db.count_members(con, tid)
    con.close()
    vertical = (terms[0] if terms else "products")
    return JSONResponse({"authed": True, "tenant": t["name"], "provisioned": bool(t and t["provisioned"]),
                         "data_mode": t["data_mode"] if t else None,
                         "account_type": acct_type,
                         # R6: tenant_kind bridges the Sandbox-actions drawer gate. TODO(R7): reconcile
                         # account_type ('tester'|'customer') with tenant_kind ('seller'|'internal'|
                         # 'sandbox'|'agency_workspace') — they overlap and should collapse to one field.
                         "tenant_kind": (t.get("tenant_kind") if t else None),
                         "email": (me_user.get("email") if me_user else None),
                         # R15 Part I — the display name for the 5-lens header greeting ("Good morning, X").
                         # Falls back to the email local-part when no name is stored.
                         "name": ((me_user.get("name") or (me_user.get("email") or "").split("@")[0])
                                  if me_user else None),
                         "role": (me_user.get("role") if me_user else None),
                         "avatar": (me_user.get("avatar") if me_user else None),
                         "is_staff": bool(me_user and is_staff_email(me_user.get("email") or "")),
                         # V4 forward-feature gates (raw operator toggles) — the V4 rail shows Ask/Agents
                         # only when on. Being in V4 already satisfies their app_ui=v4 dependency.
                         "features": {"ask": _flags.feature_gate("ask", tid),
                                      "agents": _flags.feature_gate("agents", tid),
                                      # effective permission, not the raw flag: the UI must not
                                      # re-derive it (client isTester() is TRUE for the demo tenant)
                                      "ads_preview": ads_preview_allowed(tid)},
                         "member_count": member_count,
                         "country": prof["country"], "currency": prof["currency"],
                         "symbol": prof["symbol"], "marketplace": prof["marketplace"],
                         "vertical": vertical})

# --- onboarding (Step 2 expands this; Step 1 wires synthetic + wipe) ---

@router.get("/api/members")
def members(request: Request):
    tid = require_tenant(request)
    con = db.connect()
    try:
        return JSONResponse({"ok": True, "members": db.list_members(con, tid),
                             "invites": db.list_invites(con, tid)})
    finally:
        con.close()

@router.post("/api/invites")
async def create_invite(request: Request):
    """Create an invite into THIS organization and return a ready-to-send email body with a
    single-use join link. We do not send email — the owner sends it however they like.
    The raw token is shown once here and stored only as a hash."""
    import secrets, datetime as _dt
    tid = require_tenant(request)
    uid, _ = current(request)
    b = await request.json()
    email = (b.get("email") or "").lower().strip()
    role = (b.get("role") or "member").strip()
    if not email or "@" not in email:
        return JSONResponse({"ok": False, "error": "A valid email is required."}, status_code=400)
    con = db.connect()
    try:
        if db.get_user_by_email(con, email):
            return JSONResponse({"ok": False, "error": "That email already has an account (a person can belong to one organization for now)."}, status_code=409)
        org = db.get_tenant(con, tid)
        raw = secrets.token_urlsafe(24)
        expires = (_dt.datetime.utcnow() + _dt.timedelta(days=14)).isoformat()
        db.create_invite(con, tid, email, role, auth.hash_token(raw), expires, uid)
    finally:
        con.close()
    base = str(request.base_url).rstrip("/")
    link = f"{base}/join?token={raw}"
    org_name = (org["name"] if org else "our team")
    body = (f"You've been invited to join {org_name} on Realify.\n\n"
            f"Accept your invite and set a password here:\n{link}\n\n"
            f"This link is single-use and expires in 14 days. If you didn't expect this, you can ignore it.")
    return JSONResponse({"ok": True, "email": email, "link": link,
                         "subject": f"Join {org_name} on Realify", "body": body})

@router.post("/api/invites/{invite_id}/revoke")
def revoke_invite(request: Request, invite_id: int):
    tid = require_tenant(request)
    con = db.connect()
    try:
        ok = db.revoke_invite(con, tid, invite_id)
    finally:
        con.close()
    return JSONResponse({"ok": ok})

# --- account type (tester | customer), set once, immutable -------------

@router.get("/api/account/type")
def get_account_type(request: Request):
    tid = require_tenant(request)
    con = db.connect()
    try:
        return JSONResponse({"ok": True, "account_type": db.get_account_type(con, tid)})
    finally:
        con.close()

@router.post("/api/account/type")
async def set_account_type(request: Request):
    tid = require_tenant(request)
    b = await request.json()
    at = (b.get("account_type") or "").strip()
    if at not in ("tester", "customer"):
        return JSONResponse({"ok": False, "error": "Invalid account type."}, status_code=400)
    con = db.connect()
    try:
        if not db.set_account_type(con, tid, at):
            cur = db.get_account_type(con, tid)
            return JSONResponse({"ok": False, "account_type": cur,
                                 "error": f"Account type is locked to '{cur}' now that your data is set up."}, status_code=409)
        return JSONResponse({"ok": True, "account_type": at})
    finally:
        con.close()

# --- COGS template + upload (customer accounts) ------------------------
