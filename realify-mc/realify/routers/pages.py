"""Static page + asset routes — split from run.py in #005 1a/1f. Handlers moved verbatim; behavior unchanged."""
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
from realify.site.busy_modal import SNIPPET as _BUSY_MODAL

router = APIRouter()


@router.get("/assets/logo.png")
def logo():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(HERE, "realify", "assets", "logo.png"), media_type="image/png")

# --- auth pages + handlers ---
# Public visitors go through the marketing funnel: / (landing) -> /signup -> Stripe -> onboarding.
# The classic login/create-user shell (login.html) is the operator BACK DOOR at /superlogin — accounts
# created/authenticated there get paid access synthesized (see routers/auth.signup + billing).

@router.get("/login")
def login_page():
    return RedirectResponse("/signin")           # legacy path -> public sign-in

@router.get("/superlogin", response_class=HTMLResponse)
def superlogin_page(request: Request):
    # A valid superlogin session lands on the tester hub. Otherwise we serve the AUTH GATE (staff email +
    # admin key + OTP). The gate itself is public but non-crawlable — no admin key in the URL: the real
    # control is server-side at POST /api/superlogin/authenticate (key + @realify.ai email + OTP + 8h
    # ledgered session + 3-fail lockout), which is unchanged. The legacy operator shell (login.html) is
    # not reachable as a bare destination; its functions live inside the session-gated hub.
    from .. import superlogin
    if superlogin.verify_session(request.cookies.get("superlogin_session") or ""):
        return RedirectResponse("/superlogin/hub")
    return HTMLResponse(_superlogin_gate_html(), headers={"X-Robots-Tag": "noindex, nofollow"})


@router.get("/superlogin/hub", response_class=HTMLResponse)
def superlogin_hub(request: Request):
    """Tester & sandbox hub — the post-auth landing (per the tester-sandbox mockup): persona picker,
    sandbox control, and a separated Operator actions section. Requires the SAME superlogin session
    minted by /api/superlogin/authenticate; without it the surface does not exist (404)."""
    from .. import superlogin, lifecycle, db
    from realify.site import hub
    email = superlogin.verify_session(request.cookies.get("superlogin_session") or "")
    if not email:
        raise HTTPException(status_code=404, detail="Not Found")
    con = db.connect()                                # R17 Part D: rescued catalogs as a first-class pick
    try:
        seeds = lifecycle.list_captured_seeds(con)
    except Exception:
        seeds = []
    finally:
        con.close()
    return HTMLResponse(hub.hub_html(email, captured_seeds=seeds))

@router.get("/join", response_class=HTMLResponse)
def join_page(): return page("login.html")   # the page detects ?token= and switches to join mode

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    from realify import billing
    from realify.site import ui_platform
    uid, tid = current(request)
    if not tid:
        return HTMLResponse(ui_platform.platform_page())     # public marketing front door
    con = db.connect()
    t = db.get_tenant(con, tid)
    # A brand that already has a real catalog must never loop back to the onboarding wizard, even if its
    # provisioned flag is (wrongly) unset — treat it as onboarded (R19.1: gogodolls had data but was
    # mistakenly flipped to provisioned=0, sending the agency back to "upload data").
    has_data = bool(t) and SellerRepository(con).count(tid) > 0
    try:
        brand_country = db.get_setting(con, tid, "country")     # so add-data mode pre-selects the RIGHT marketplace
    except Exception:
        brand_country = None
    con.close()
    if not t:                                                # stale session (deleted/reset tenant)
        try: request.session.clear()
        except Exception: pass
        return HTMLResponse(ui_platform.platform_page())
    # Agency users are NOT seller/Stripe customers — the agency's billing is separate — so they must never
    # be routed into the seller pay wall (/pricing). An agency member sitting on their workspace tenant
    # (no subscription) used to trip has_access() -> /pricing and get trapped (root AND /signin both bounce
    # there). Route them to their console. A drilled-in agency operator (acting_as set, session scoped to a
    # brand) falls through and gets the brand's seller app, bypassing the brand's own billing gate.
    try:
        acting = bool(request.session.get("acting_as"))
    except Exception:
        acting = False
    from realify.site import backbar as _backbar
    if not acting:
        from .auth import _agency_login_redirect
        ar = _agency_login_redirect(uid)
        if ar:
            return RedirectResponse(ar)                      # agency member (not drilled in) -> the console
        if not billing.has_access(t):                        # seller with no live subscription -> pay wall
            return RedirectResponse("/pricing")
    # add-data mode: the in-app "Add / replace reports" buttons (SKU page + account drawer) route here with
    # ?add-data=1 so an ALREADY-provisioned brand re-uploads through the SAME full onboarding pipeline
    # (/api/onboard/reports = report recognizer + write_ingest + safe_ingest_ad_graph + run_pipeline),
    # instead of the lesser in-app /api/skus/upload path that skipped the campaign ad-graph. The uploader is
    # additive (dedup / take-latest per period), so a provisioned brand's data is merged, never wiped.
    try:
        add_data = request.query_params.get("add-data") == "1"
    except Exception:
        add_data = False
    # Onboarding WIZARD until the brand has data — for a seller AND for a drilled-in agency operator. This
    # is what keeps an empty managed brand on the wizard instead of a fabricated interior (sample Profit&Ads
    # / hash-synthesized analyst / seeded demo categories). A drilled-in operator gets the agency bar too so
    # they can return to the fleet.
    if (not t["provisioned"] and not has_data) or add_data:
        onb = page("login.html")
        if acting or add_data:
            # The operator/seller is already signed in, so hide the sign-in box AND the "choose a different
            # account type" (tester) switcher server-side — no flash. Flag the page so login.html routes
            # straight to Connect-your-data. Agency drill-in also gets the back-to-fleet bar; add-data mode
            # (a provisioned brand adding/replacing reports) gets the brand's real country pre-selected +
            # a Cancel-back-to-dashboard control (wired in login.html on window.__addData).
            onb = onb.replace("</head>",
                              "<style>#auth,.backLink[data-back]{display:none!important}</style></head>", 1)
            flags = "window.__agencyBrand=1;" if acting else ""
            if add_data:
                flags += "window.__addData=1;"
                if brand_country:
                    flags += "window.__brandCountry=" + json.dumps(str(brand_country)) + ";"
            bar = _backbar.bar(request) if acting else ""
            onb = onb.replace("<body>",
                              "<body>" + bar + "<script>" + flags + "</script>", 1)
        return HTMLResponse(onb)
    # Parallel-skin switch (zero-risk rollout): serve the V4 SPA only when the skin resolves to 'v4'
    # AND the parallel template actually exists. Until frontend_v4.html lands this is a pure no-op —
    # legacy is served unchanged. The flag is DB-backed + read per request (instant flip, no redeploy);
    # net-new BEHAVIOR (agents acting, etc.) is gated separately via flags.feature_enabled, never by skin.
    from .. import flags
    if flags.resolve_skin(request, tid) == "v4":
        import os as _os
        _v4 = _os.path.join(HERE, "frontend_v4.html")
        if _os.path.exists(_v4):
            return HTMLResponse(page("frontend_v4.html").replace("<!--BUSY_MODAL-->",
                                _BUSY_MODAL + _backbar.bar(request)))
    # Inject the shared busy-modal + (when acting) the back-to-hub bar at serve time.
    return HTMLResponse(page("frontend.html").replace("<!--BUSY_MODAL-->", _BUSY_MODAL + _backbar.bar(request)))

# --- data endpoints (all tenant-scoped) ---

@router.get("/analytics", response_class=HTMLResponse)
def analytics_page():
    return page("analytics.html")

@router.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    # keep operator surfaces out of crawlers / sitemaps (not a security control)
    return "User-agent: *\nDisallow: /ops\nDisallow: /analytics\nDisallow: /superlogin\n"


# ---- superlogin gate + tester/sandbox hub (post-launch fix 1) ----
_SL_CSS = """body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;background:#F4F0E8;color:#1A1A1A;margin:0;font-size:15px}
.wrap{max-width:960px;margin:0 auto;padding:26px 24px 60px}.card{background:#fff;border:1px solid #DDD5C6;border-radius:14px;padding:30px 34px;margin-bottom:18px}
.wm{font-weight:700;font-size:18px}.wm .d{color:#C4785B}.tag{font:600 10px/1 ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;background:#F5E7E4;color:#7A3527;border-radius:100px;padding:4px 10px;margin-left:8px}
h2{font-size:22px;margin:14px 0 4px}h4{font:600 12px/1 ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#6B6459;margin:0 0 12px}
label{display:block;font-size:12.5px;font-weight:600;margin:14px 0 5px}input{width:100%;border:1px solid #DDD5C6;border-radius:9px;padding:9px 12px;font-size:14px;background:#FDFCF9}
button{background:#C4785B;color:#fff;border:none;border-radius:9px;padding:10px 18px;font-size:14px;font-weight:600;cursor:pointer}.ghost{background:none;color:#1A1A1A;border:1px solid #DDD5C6}.slate{background:#5B7B94}
.msg{font-size:13px;margin-top:12px;min-height:18px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.persona{border:1px solid #DDD5C6;border-radius:14px;padding:18px;background:#FDFCF9}.persona .role{font:600 10px/1 ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;color:#C4785B;margin-bottom:6px}.persona h5{margin:0 0 4px;font-size:15px}.persona p{margin:0;font-size:12.5px;color:#6B6459}
.row{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #EFEAE0;font-size:13.5px}.row:last-child{border-bottom:none}
.sandbar{background:repeating-linear-gradient(-45deg,#F3E2C6,#F3E2C6 12px,#EED7B2 12px,#EED7B2 24px);border:1px solid #DDC391;border-radius:10px;padding:8px 14px;font-size:12px;color:#6B5320;margin-bottom:18px}
.op{border:2px solid #B3402E33;background:#FBF3F1}small{color:#6B6459}
.shead{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:14px}
.shead .cell{background:#FDFCF9;border:1px solid #DDD5C6;border-radius:10px;padding:12px 14px}
.shead .k{font:600 10px/1 ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#6B6459}
.shead .v{font-size:15px;font-weight:600;margin-top:6px;word-break:break-word}
.emptyhead{background:#F3EFE5;border:1px dashed #C4785B;border-radius:10px;padding:14px 16px;color:#7A5A47;font-size:13.5px;margin-top:12px}
.persona.disabled{opacity:.5;cursor:not-allowed}.persona.doorway{cursor:pointer}.persona.doorway:hover{border-color:#C4785B}
.persona .lock{font-size:11px;color:#9C4F30;margin-top:8px;display:none}.persona.disabled .lock{display:block}
.stepper{display:flex;gap:6px;margin:12px 0}.step{flex:1;text-align:center;font-size:11px;padding:7px 4px;border-radius:8px;background:#F1ECE1;color:#6B6459}
.step.on{background:#1A1A1A;color:#fff;font-weight:600}.step.done{background:#E8DFD0;color:#6B5B3E}
.stepbody{background:#FDFCF9;border:1px solid #DDD5C6;border-radius:10px;padding:12px 14px;font-size:13.5px;min-height:40px}
.stepbody .who{font:600 10px/1 ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;color:#6B6459;margin-right:8px}"""


def _superlogin_gate_html():
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8><link rel='icon' type='image/png' href='/assets/Final-logo-VF-white-3.png'><meta name=viewport content="width=device-width,initial-scale=1">
<meta name=robots content="noindex, nofollow">
<title>Realify · Sandbox superlogin</title><style>{_SL_CSS}</style></head><body><div class=wrap style="max-width:440px">
<div class=card><div class=wm><img src="/assets/Final-logo-full-Dark-V3.png" alt="Realify" style="height:22px;width:auto;vertical-align:middle"> <span class=tag>restricted &middot; staff only</span></div>
<h2>Sandbox superlogin</h2>
<label>Realify staff email</label><input id=email type=email placeholder="you@realify.ai">
<label>Admin key</label><input id=key type=password>
<label>One-time code</label><input id=otp inputmode=numeric placeholder="6-digit code">
<div style="margin-top:16px"><button onclick=reqotp()>Send code</button> <button class=ghost onclick=enter()>Enter sandbox &rarr;</button></div>
<div class=msg id=msg></div>
<ul style="font-size:12.5px;color:#6B6459;margin-top:20px"><li>Key + staff email + OTP; every session is <b>ledgered</b> (who/when/IP).</li>
<li>Sessions expire after <b>8 hours</b>; 3 failures &rarr; lockout + alert.</li>
<li>Reaches <b>sandbox tenants only</b> &mdash; production data is not routable here.</li></ul></div></div>
<script>function j(){{return{{admin_key:document.getElementById('key').value,email:document.getElementById('email').value,otp_code:document.getElementById('otp').value}}}}
async function reqotp(){{msg.textContent='Sending…';let r=await fetch('/api/superlogin/request-otp',{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify(j())}});msg.textContent=r.ok?'Code sent — check your email.':'Could not send a code.';}}
async function enter(){{msg.textContent='Verifying…';let r=await fetch('/api/superlogin/authenticate',{{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify(j())}});let d=await r.json().catch(()=>({{}}));if(r.ok&&d.redirect){{location.href=d.redirect;}}else{{msg.textContent=(d&&d.error)||'Denied.';}}}}</script></body></html>"""
