"""Brand-consent + connections routes (agency-plan P3) — behind AGENCY_CONSOLE, Postgres-only.

Consent invite email (via-Realify From on EMAIL_DOMAIN, Reply-To REPLY_TO_ADDRESS, agency name
leading), OTP-gated single-use consent actions (409 on illegal transitions), agency one-click counter
accept, plus a stub-OAuth mock provider + connect. CSV ingest is domain-tested (realify.agency.ingest).
"""
import html
import os

from fastapi import APIRouter, Request, Depends
from realify.site.tokens import state_page as _state_page
from fastapi.responses import HTMLResponse, JSONResponse

from .. import mail
from ..agency import consent, connections, policy, db as agency_db
from ..agency.guard import require_agency_console
from .deps import require_admin

router = APIRouter()


def _admin(request: Request):
    require_admin(request)
    return True


async def _body(request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


def _email_domain():
    from ..agency import mailcfg
    return mailcfg.email_domain()                       # the SES-verified sending domain


def _reply_to():
    from ..agency import mailcfg
    return mailcfg.reply_to("consent")                  # routed mailbox (agencies@ does not forward)


def _staff_or_agency_authorized(request, agency_id):
    """R2 authz: a Realify staff admin key (ops can still fire invites) OR the caller is an
    agency_admin/account_manager on the TARGET agency. Authorization is by MEMBERSHIP (agency_members) —
    which is what lets a freshly provisioned agency onboard its FIRST client: it has no brands yet, so no
    engagements and no per-brand grants exist, and the old grant-only check 403'd every onboard attempt
    (the chicken-and-egg: the first brand needs an engagement that only onboarding a brand creates). A
    per-engagement grant on the agency is also accepted (an AM whose book was assigned)."""
    from fastapi import HTTPException
    from .deps import require_admin, current
    try:
        require_admin(request)                       # Realify staff key path
        return True
    except HTTPException:
        pass
    uid, _ = current(request)
    if not uid or not agency_id:
        return False
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM agency_members WHERE user_id=%s AND agency_id=%s::uuid "
                    "AND role IN ('agency_admin','account_manager') LIMIT 1", (uid, str(agency_id)))
        if cur.fetchone():
            return True
        cur.execute("SELECT 1 FROM grants g JOIN engagements e ON e.id=g.engagement_id "
                    "WHERE g.user_id=%s AND e.agency_id=%s::uuid AND g.role IN ('agency_admin','account_manager') "
                    "LIMIT 1", (uid, str(agency_id)))
        return cur.fetchone() is not None
    finally:
        conn.close()


# ---------------- consent invite (agency-admin grant OR Realify staff key) ----------------
@router.post("/api/agencies/consent/invite", dependencies=[Depends(require_agency_console)])
async def consent_invite(request: Request):
    b = await _body(request)
    agency_id = b.get("agency_id")
    tenant_id = b.get("tenant_id")
    brand_name = (b.get("brand_name") or "").strip()
    country = b.get("country")                       # US | IN — localizes the managed brand's currency
    agency_name = (b.get("agency_name") or "Your agency").strip()
    email = (b.get("email") or "").strip().lower()
    template = b.get("template") or "Advise"
    ceilings = b.get("ceilings") or {}
    if not _staff_or_agency_authorized(request, agency_id):
        return JSONResponse({"ok": False, "error": "not authorized for this agency"}, status_code=403)
    if not (agency_id and email):
        return JSONResponse({"ok": False, "error": "agency_id, email required"}, status_code=400)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        # Agency-direct onboarding: resolve the brand to invite, CREATING a managed brand tenant when the
        # agency is onboarding a net-new brand (no existing tenant_id). Prevents the FK-500 that ate the
        # invite email when the "Add a client" form had no real tenant id to give.
        tid = consent.resolve_or_create_brand(cur, tenant_id, brand_name, email, country)
        consent.ensure_engagement(cur, agency_id, tid)   # brand joins the book now (no envelope until grant)
        token, cid = consent.create_consent(cur, agency_id, tid, agency_name, email,
                                            template, ceilings)
        self_approve = policy.self_approve_on(cur)        # ON => agency will self-approve; email is an FYI
        conn.commit()
    finally:
        conn.close()
    base = str(request.base_url).rstrip("/")
    link = f"{base}/consent/{token}"
    frm = f"{agency_name} via Realify <consent@{_email_domain()}>"
    if self_approve:
        # FYI notification — the agency operates on the brand's behalf (creds the brand already gave them);
        # no action needed, but the brand can always review or revoke.
        mail.send(email, f"{agency_name} is using Realify to optimize your margin",
                  f"{agency_name} uses Realify to optimize your margin and manage your store, and has "
                  f"connected your account to operate it on your behalf. No action is needed from you — "
                  f"you can review exactly what they can do, or revoke this access at any time, here:\n{link}",
                  from_addr=frm, reply_to=_reply_to())
    else:
        # approval-required — the brand must review + approve via the OTP consent flow.
        mail.send(email, f"{agency_name} would like to operate your Realify account",
                  f"{agency_name} has requested access to manage your Realify account. Review and decide "
                  f"here (single-use, expires in 7 days):\n{link}\n\nYou'll verify your identity with an "
                  f"emailed code.",
                  from_addr=frm, reply_to=_reply_to())
    return JSONResponse({"ok": True, "consent_id": cid, "self_approve": self_approve})


@router.post("/api/agencies/consent/{consent_id}/self-approve",
             dependencies=[Depends(require_agency_console)])
async def consent_self_approve(consent_id: int, request: Request):
    """Agency impersonates the brand's consent click — approve the engagement ON THE BRAND'S BEHALF
    (using the access the brand handed the agency offline). Gated by the platform `agency_self_approve`
    switch (admin fleet screen); when OFF, the brand must approve through the OTP flow. Works on ANY brand
    tenant (no sandbox restriction — that was the old demo-only path). Ledgered as impersonated."""
    from .deps import current
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT agency_id, tenant_id FROM brand_consents WHERE id=%s", (consent_id,))
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return JSONResponse({"ok": False, "error": "no such consent"}, status_code=404)
        agency_id, tenant_id = row
        if not _staff_or_agency_authorized(request, agency_id):
            conn.rollback()
            return JSONResponse({"ok": False, "error": "not authorized for this agency"}, status_code=403)
        if not policy.self_approve_on(cur):
            conn.rollback()
            return JSONResponse({"ok": False, "error": "brand approval required (agency self-approve is off)"},
                                status_code=409)
        uid, _ = current(request)
        res = consent.impersonate_grant(cur, consent_id, actor_user=uid)
        conn.commit()
        # drill straight into the brand — an unprovisioned brand lands on the real onboarding WIZARD, so the
        # agency loads the brand's data there (reusing the seller wizard), not a bespoke data-sources page.
        return JSONResponse({"ok": True, "message": "Approved on the brand's behalf.",
                             "tenant_id": tenant_id, "redirect": f"/agency/brand/{tenant_id}", **res})
    except consent.ConsentStateError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()


# ---------------- consent page + OTP-gated actions (public) ----------------
_ENV_CARDS = [
    ("Full Operate", "Full Operate", "Price, ads, inventory & listings — execute on your behalf."),
    ("Operate ex-Pricing", "Operate ex-Pricing", "Everything except pricing (you keep price control)."),
    ("Ads Only", "Ads Only", "Advertising only; everything else read-only."),
    ("Advise Only", "Advise", "Proposals only — nothing executes without your approval."),
    ("Read-Report Only", "Read-only", "Reporting & visibility only; no changes."),
]


def _consent_page_html(token, ctx):
    from ..pdp import ENVELOPES, LENSES
    ag = html.escape(ctx["agency_name"] or "Your agency")
    env = ENVELOPES.get(ctx["template"], ENVELOPES["Advise"])
    expiry = ctx["expires_at"].date().isoformat() if ctx.get("expires_at") else "—"
    cards = "".join(
        f"<label class='envcard{' sel' if key == ctx['template'] else ''}'>"
        f"<input type=radio name=template value='{html.escape(key)}'{' checked' if key == ctx['template'] else ''}>"
        f"<b>{html.escape(label)}</b><p>{html.escape(desc)}</p></label>"
        for label, key, desc in _ENV_CARDS)
    lens_rows = "".join(
        f"<div class=lensrow><span>{lens}</span>"
        f"<span class=cap>{env[lens]['max_kind'].upper()}</span>"
        f"<span class=dial>autonomy ceiling: <b>{env[lens]['autonomy_ceiling']}</b> "
        f"<input type=range min=0 max=3 value={env[lens]['autonomy_ceiling']} name='ceiling_{lens}'></span>"
        f"</div>" for lens in LENSES)
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'><title>Grant access · Realify</title>"
        "<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:720px;"
        "margin:0 auto;padding:30px 22px;color:#1A1A1A;background:#F4F0E8}"
        ".card{background:#fff;border:1px solid #DDD5C6;border-radius:12px;padding:20px 24px;margin-bottom:16px}"
        ".envcard{display:block;border:1px solid #DDD5C6;border-radius:10px;padding:12px 14px;margin:8px 0;cursor:pointer}"
        ".envcard.sel{border-color:#C4785B;background:#FBF3EE}.envcard p{margin:4px 0 0;color:#6B6459;font-size:13px}"
        ".lensrow{display:grid;grid-template-columns:120px 90px 1fr;gap:10px;align-items:center;padding:6px 0;"
        "border-bottom:1px solid #EFEAE0;font-size:13px}.cap{font-family:ui-monospace,monospace;color:#5B7B94}"
        ".banner{background:#EAF0F5;border:1px solid #C9D6E0;border-radius:10px;padding:12px 16px;font-size:13.5px;"
        "margin-bottom:16px}.who{background:#FBF7EF;border:1px dashed #C4785B;border-radius:10px;padding:14px 16px}"
        "button{border-radius:8px;border:1px solid #DDD5C6;background:#fff;padding:9px 16px;cursor:pointer;margin:4px 6px 0 0}"
        ".primary{background:#C4785B;color:#fff;border:none}.danger{color:#B3402E}input[type=text]{padding:8px;border:1px solid #DDD5C6;border-radius:8px}"
        "</style></head><body>"
        f"<h1>{ag} would like to operate your Realify account</h1>"
        # verification banner: brand email + single-use + expiry
        f"<div class=banner>Signed in as <b>{html.escape(ctx['email'])}</b> · this link is "
        f"<b>single-use</b> and expires on <b>{expiry}</b>. Enter the emailed code to act.</div>"
        # money + revocability copy (exact, required)
        f"<div class=card><p><b>You can narrow or revoke this access at any time.</b></p>"
        f"<p>{ag} pays for Realify. You will never receive an invoice from us.</p></div>"
        # who is realify
        "<div class=card><div class=who><h3>Who is Realify</h3><p>Realify is the autonomous merchandising "
        "platform your agency uses to manage your store. Your credentials stay yours — the agency never "
        "sees them — and every action is logged and reversible.</p></div></div>"
        # envelope template cards
        f"<div class=card><h3>Choose what {ag} may do</h3>{cards}</div>"
        # per-lens read/execute + autonomy dials for the requested envelope
        f"<div class=card><h3>Requested access ({html.escape(ctx['template'])}) — by lens</h3>{lens_rows}</div>"
        # data connection is the AGENCY's job on your behalf — not something the brand does here
        f"<div class=card><h3>Connecting your channels</h3><p>{ag} connects your sales channels for "
        "you — using the access you're granting here — by linking each channel (OAuth, coming soon) or "
        "uploading your reports on your behalf. <b>You don't need to connect anything on this page.</b></p></div>"
        # verify + act
        "<div class=card><h3>Verify &amp; decide</h3>"
        "<button type=button onclick='sendcode()'>Email me a code</button>"
        "<p>Code <input type=text id=code inputmode=numeric placeholder='6-digit code'></p>"
        "<button class=primary onclick=\"act('grant')\">Grant access</button>"
        "<button onclick=\"act('counter')\">Counter-offer</button>"
        "<button class=danger onclick=\"act('decline')\">Decline</button>"
        "<div id=msg style='margin-top:10px;font-size:13px'></div></div>"
        "<script>"
        "function tmpl(){var r=document.querySelector('input[name=template]:checked');return r?r.value:null}"
        "function ceilings(){var o={};document.querySelectorAll('input[name^=ceiling_]').forEach(function(i){"
        "o[i.name.slice(8)]=Number(i.value)});return o}"
        f"async function sendcode(){{var r=await fetch('/api/consent/{token}/otp',{{method:'POST'}});"
        "msg.textContent=r.ok?'Code sent to your email.':'Could not send a code.';}"
        f"async function act(a){{var body={{code:document.getElementById('code').value,template:tmpl(),ceilings:ceilings()}};"
        f"var r=await fetch('/api/consent/{token}/'+a,{{method:'POST',headers:{{'content-type':'application/json'}},"
        "body:JSON.stringify(body)});var d=await r.json().catch(function(){return{}});"
        "if(r.ok){msg.innerHTML='Done: '+(d.status||a)+((d.status==='granted')?"
        "' &mdash; <a href=\"/agency/console\" style=\"color:#C4785B;font-weight:600\">"
        "Go to your Realify console to manage this and your other brands &rarr;</a>':'');}"
        "else{msg.textContent=(d&&d.error)||'Failed.';}}"
        "</script></body></html>")


@router.get("/consent/{token}", response_class=HTMLResponse, dependencies=[Depends(require_agency_console)])
def consent_page(token: str):
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        ctx = consent.page_context(cur, token)
        if ctx:
            consent.seen(cur, token)          # opening the emailed link = viewed (invited -> viewed)
            conn.commit()
    finally:
        conn.close()
    if not ctx:
        return HTMLResponse(_state_page("Link not found", "This consent link is invalid or has expired.", "Consent"), status_code=404)
    return HTMLResponse(_consent_page_html(token, ctx))


def _guard(fn):
    try:
        return JSONResponse(fn())
    except consent.ConsentStateError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)


@router.post("/api/consent/{token}/otp", dependencies=[Depends(require_agency_console)])
def consent_otp(token: str):
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        consent.request_otp(cur, token)               # emails the code; raises 409 if terminal/expired
        conn.commit()
        return JSONResponse({"ok": True})
    except consent.ConsentStateError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()


def _action(token, fn_name, **kw):
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        res = getattr(consent, fn_name)(cur, token, **kw)
        conn.commit()
        return JSONResponse({"ok": True, **(res or {})})
    except consent.ConsentStateError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()


@router.post("/api/consent/{token}/view", dependencies=[Depends(require_agency_console)])
async def consent_view(token: str, request: Request):
    b = await _body(request)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        consent.view(cur, token, b.get("code", ""))
        conn.commit()
        return JSONResponse({"ok": True})
    except consent.ConsentStateError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()


@router.post("/api/consent/{token}/grant", dependencies=[Depends(require_agency_console)])
async def consent_grant(token: str, request: Request):
    b = await _body(request)
    return _action(token, "grant", code=b.get("code", ""), template=b.get("template"),
                   ceilings=b.get("ceilings"))


@router.post("/api/consent/{token}/counter", dependencies=[Depends(require_agency_console)])
async def consent_counter(token: str, request: Request):
    b = await _body(request)
    return _action(token, "counter", code=b.get("code", ""), ceilings=b.get("ceilings") or {})


@router.post("/api/consent/{token}/decline", dependencies=[Depends(require_agency_console)])
async def consent_decline(token: str, request: Request):
    b = await _body(request)
    return _action(token, "decline", code=b.get("code", ""))


@router.post("/api/ops/consent/{consent_id}/accept",
             dependencies=[Depends(require_agency_console), Depends(_admin)])
def consent_accept(consent_id: int):
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        res = consent.accept_counter(cur, consent_id)
        conn.commit()
        return JSONResponse({"ok": True, **res})
    except consent.ConsentStateError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()


# ---------------- stub OAuth: mock provider + connect ----------------
@router.get("/mock-oauth/{provider}/authorize", dependencies=[Depends(require_agency_console)])
def mock_oauth_authorize(provider: str):
    return JSONResponse({"ok": True, "provider": provider, "code": f"mock-code-{provider}"})


@router.post("/api/connections/{tenant_id}/{provider}/connect",
             dependencies=[Depends(require_agency_console), Depends(_admin)])
async def connect_provider(tenant_id: int, provider: str, request: Request):
    if provider not in connections.PROVIDERS:
        return JSONResponse({"ok": False, "error": "unknown provider"}, status_code=400)
    b = await _body(request)
    if not str(b.get("code", "")).startswith("mock-code-"):    # stub OAuth exchange
        return JSONResponse({"ok": False, "error": "bad oauth code"}, status_code=400)
    import datetime
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        connections.upsert_connection(cur, tenant_id, provider, "connected", expires)
        conn.commit()
    finally:
        conn.close()
    return JSONResponse({"ok": True, "provider": provider, "status": "connected"})
