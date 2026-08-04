"""Billing API + billing page (rolled in from the former /beta app; now tenant-scoped on the main app).

  POST /api/billing/signup        — PUBLIC front-door signup: create account, Stripe customer + Checkout
                                     (30-day trial, card required), land at /welcome.
  GET  /api/subscription/status   — the signed-in tenant's subscription state + trial days remaining.
  GET  /api/billing/portal        — Stripe billing portal (manage card / invoices / cancel).
  POST /api/webhooks/stripe       — Stripe webhook: verify raw-body signature, then idempotently sync
                                     the tenant's state (looked up by customer / subscription id).
  GET  /billing                   — billing management page (or the BillingGate for canceled/unpaid).
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from realify import auth, billing, config, db
from realify.site import ui, components
from .deps import current, require_tenant

router = APIRouter()


@router.post("/api/billing/signup")
async def billing_signup(request: Request):
    b = await request.json()
    name = (b.get("name") or "").strip()
    email = (b.get("email") or "").strip().lower()
    pw = b.get("password") or ""
    confirm = b.get("confirmPassword") or b.get("confirm_password") or ""
    if pw != confirm:
        return JSONResponse({"ok": False, "error": "Passwords don't match."}, status_code=400)
    if not billing.enabled():
        return JSONResponse({"ok": False, "error": "Billing is not configured yet. Please try again later."},
                            status_code=503)
    try:
        uid, tid = auth.signup(email, pw, account_name=name or None)     # PBKDF2 + duplicate-email guard
    except ValueError as e:
        code = 409 if "already exists" in str(e).lower() else 400
        return JSONResponse({"ok": False, "error": str(e)}, status_code=code)
    request.session["uid"] = uid
    request.session["tid"] = tid
    # a public signup is a paying customer -> pre-set account type so onboarding skips the tester/customer chooser
    try:
        con = db.connect(); db.set_account_type(con, tid, "customer"); con.close()
    except Exception:
        pass
    # Stripe customer + Checkout. A failure here shouldn't strand the user (they exist + are logged in);
    # surface it so the client can retry from /pricing.
    try:
        customer = billing.create_customer(email, name, tid)
        billing.set_stripe_customer(tid, customer.id)
        base = billing.app_base(request)
        # Land back on the onboarding SPA's root ("/" = ROUTES.ONBOARDING),
        # not a /welcome page that doesn't exist in realifyAi — OnboardingLayout
        # reads the `billing` query param to resume the wizard at Step 2.
        session = billing.create_checkout(
            customer.id, tid,
            success_url=f"{base}/?billing=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/?billing=cancelled")
    except Exception as e:
        return JSONResponse({"ok": False, "error": "Could not start checkout: %s" % e}, status_code=502)
    return JSONResponse({"ok": True, "checkout_url": session.url})


@router.get("/api/subscription/status")
def subscription_status(request: Request):
    tid = require_tenant(request)
    t = billing.get_tenant(tid) or {}
    return JSONResponse({
        "status": t.get("subscription_status"),
        "trial_ends_at": t.get("trial_ends_at"),
        "current_period_end": t.get("current_period_end"),
        "days_remaining": billing.days_remaining(t),
        "has_access": billing.has_access(t),
    })


@router.get("/api/billing/portal")
def billing_portal(request: Request):
    tid = require_tenant(request)
    t = billing.get_tenant(tid) or {}
    cid = t.get("stripe_customer_id")
    if not cid or not billing.stripe:
        return JSONResponse({"ok": False, "error": "No billing account on file."}, status_code=400)
    session = billing.create_portal(cid, return_url=f"{billing.app_base(request)}/billing")
    return JSONResponse({"portal_url": session.url})


@router.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    raw = await request.body()                          # RAW body — never parse before verifying
    sig = request.headers.get("stripe-signature")
    if not billing.stripe:
        return JSONResponse({"error": "billing disabled"}, status_code=400)
    try:
        event = billing.stripe.Webhook.construct_event(raw, sig, config.STRIPE_WEBHOOK_SECRET)
    except Exception:
        return JSONResponse({"error": "Signature verification failed"}, status_code=400)

    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        t = billing.tenant_by_customer(billing.g(obj, "customer"))
        sub_id = billing.g(obj, "subscription")
        if t and sub_id:
            sub = billing.stripe.Subscription.retrieve(sub_id)
            billing.sync_from_subscription(t, sub, status="trialing")

    elif etype == "customer.subscription.updated":
        t = billing.tenant_by_subscription(billing.g(obj, "id")) or billing.tenant_by_customer(billing.g(obj, "customer"))
        billing.sync_from_subscription(t, obj)

    elif etype == "customer.subscription.deleted":
        t = billing.tenant_by_subscription(billing.g(obj, "id")) or billing.tenant_by_customer(billing.g(obj, "customer"))
        if t:
            billing.set_subscription(t["id"], subscription_status="canceled")

    elif etype == "invoice.payment_succeeded":
        t = billing.tenant_by_customer(billing.g(obj, "customer"))
        if t:
            cpe = None
            if billing.g(obj, "subscription"):
                cpe = billing.ts(billing.g(billing.stripe.Subscription.retrieve(billing.g(obj, "subscription")),
                                           "current_period_end"))
            billing.set_subscription(t["id"], subscription_status="active", current_period_end=cpe)

    elif etype == "invoice.payment_failed":
        t = billing.tenant_by_customer(billing.g(obj, "customer"))
        if t:
            billing.set_subscription(t["id"], subscription_status="past_due")

    # customer.subscription.trial_will_end + everything else: acknowledged, no state change
    return JSONResponse({"received": True})


@router.get("/billing", response_class=HTMLResponse)
def billing_home(request: Request):
    uid, tid = current(request)
    if not tid:
        return RedirectResponse("/signin")
    t = billing.get_tenant(tid)
    if (t or {}).get("subscription_status") in ("canceled", "unpaid"):
        return HTMLResponse(components.billing_gate(t))
    return HTMLResponse(ui.billing_page(t, billing.days_remaining(t)))
