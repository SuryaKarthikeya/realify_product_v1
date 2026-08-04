"""Public marketing shell + auth pages (rolled in from the former /beta app). These render the
server-side HTML site (realify.site) at the app's root paths:
  /platform /pricing /about  — marketing
  /signin /signup            — auth pages (post to /api/login and /api/billing/signup)
  /welcome                   — post-Stripe-checkout confirmation (syncs the trial, lands in onboarding)
The gated app itself lives at / (see pages.home)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from realify import billing, auth, config, mail
from realify.site import ui, ui_platform, ui_pricing, ui_about, ui_faq, ui_agencies
from .deps import current

router = APIRouter()


@router.get("/platform", response_class=HTMLResponse)
def platform():
    return HTMLResponse(ui_platform.platform_page())


@router.get("/agencies", response_class=HTMLResponse)
def agencies():
    # MARKETING page — renders regardless of AGENCY_CONSOLE (only the form POST is flag-gated).
    return HTMLResponse(ui_agencies.agencies_landing())


@router.get("/agencies/apply")
def agencies_apply_redirect():
    return RedirectResponse("/agencies#apply", status_code=301)


@router.get("/pricing", response_class=HTMLResponse)
def pricing():
    return HTMLResponse(ui_pricing.pricing_page())


@router.get("/about", response_class=HTMLResponse)
def about():
    return HTMLResponse(ui_about.about_page())


@router.get("/faq", response_class=HTMLResponse)
def faq():
    return HTMLResponse(ui_faq.faq_page())


@router.get("/signin", response_class=HTMLResponse)
def signin(request: Request):
    if current(request)[1]:                         # already signed in -> let / route them
        return RedirectResponse("/")
    return HTMLResponse(ui.signin_page())


@router.get("/signup", response_class=HTMLResponse)
def signup(request: Request):
    if current(request)[1]:
        return RedirectResponse("/")
    return HTMLResponse(ui.signup_page())


@router.get("/reset", response_class=HTMLResponse)
def reset(request: Request):
    if current(request)[1]:
        return RedirectResponse("/")
    return HTMLResponse(ui.reset_page())


@router.get("/reset/{token}", response_class=HTMLResponse)
def reset_confirm(token: str):
    return HTMLResponse(ui.reset_confirm_page(token, valid=bool(auth.preview_reset(token))))


@router.post("/api/reset/request")
async def reset_request(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = dict(await request.form())
    email = (body.get("email") or "").strip()
    if "@" not in email:
        return JSONResponse({"ok": False, "error": "A valid email is required."}, status_code=400)
    # Neutral response either way — never disclose whether the account exists.
    token = auth.request_reset(email)
    if token:
        base = (config.APP_URL or "https://realifyai.app").rstrip("/")
        try:
            mail.send(email, "Reset your Realify password",
                      f"We received a request to reset your Realify password.\n\n"
                      f"Set a new password (this link is single-use and expires in one hour):\n"
                      f"{base}/reset/{token}\n\nIf you didn't ask for this, you can ignore this email.")
        except Exception as e:                          # pragma: no cover - defensive
            print(f"[reset] mail send failed for {email}: {e}", flush=True)
    return JSONResponse({"ok": True})


@router.post("/api/reset/confirm")
async def reset_confirm_post(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = dict(await request.form())
    try:
        auth.confirm_reset(body.get("token") or "", body.get("password") or "")
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return JSONResponse({"ok": True})


@router.get("/welcome", response_class=HTMLResponse)
def welcome(request: Request, session_id: str = ""):
    """Confirm the just-completed Checkout server-side so the tenant is 'trialing' immediately (closes
    the race with the async webhook), then send them into onboarding."""
    uid, tid = current(request)
    if not tid:
        return RedirectResponse("/signin")
    t = billing.get_tenant(tid)
    trial_txt = (t or {}).get("trial_ends_at") or "day 31"
    if session_id and billing.stripe:
        try:
            cs = stripe_retrieve_checkout(session_id)
            sub_id = billing.g(cs, "subscription")
            if sub_id:
                sub = billing.stripe.Subscription.retrieve(sub_id)
                billing.sync_from_subscription(t, sub, status="trialing")
                te = billing.g(sub, "trial_end")
                if te:
                    trial_txt = datetime.fromtimestamp(int(te), tz=timezone.utc).strftime("%B %d, %Y")
        except Exception:
            pass
    return HTMLResponse(ui.welcome_page(trial_txt))


def stripe_retrieve_checkout(session_id):
    return billing.stripe.checkout.Session.retrieve(session_id)
