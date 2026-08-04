"""Stripe billing for the main app — the subscription lives on the TENANT (the billing entity).

Rolled in from the former standalone beta. Reads keys from config (STRIPE_*). Empty keys mean billing
is effectively disabled: the marketing funnel still renders, but checkout/portal calls will error out
loudly rather than silently pretend. The webhook looks tenants up by stripe_customer_id /
stripe_subscription_id and every handler sets a computed state (idempotent).
"""
from datetime import datetime, timezone

from . import config, db
from .repositories.tenant_repo import TenantRepository

try:
    import stripe
    stripe.api_key = config.STRIPE_SECRET_KEY
    try:
        stripe.api_version = "2025-06-30.basil"     # pin the version the integration was built against
    except Exception:
        pass
except Exception:                                   # stripe not installed (e.g. minimal CI) — funnel still renders
    stripe = None

STATUSES = ("trialing", "active", "past_due", "canceled", "unpaid")
ACCESS_STATUSES = ("trialing", "active", "past_due")   # past_due keeps access during the retry window


def enabled():
    return bool(stripe and config.STRIPE_SECRET_KEY and config.STRIPE_PRICE_ID)


def app_base(request=None):
    """Base URL for building Stripe redirect URLs. Prefer the configured APP_URL; else derive from the
    request so the same code works on localhost and realifyai.app without hardcoding."""
    if config.APP_URL:
        return config.APP_URL
    if request is not None:
        return str(request.base_url).rstrip("/")
    return ""


# ---- tenant subscription state (thin wrappers that open their own connection) ----

def _with_repo(fn):
    con = db.connect()
    try:
        return fn(TenantRepository(con))
    finally:
        con.close()


def get_tenant(tid):
    return _with_repo(lambda r: r.get(tid))


def set_stripe_customer(tid, customer_id):
    _with_repo(lambda r: r.set_stripe_customer(tid, customer_id))


def set_subscription(tid, **fields):
    _with_repo(lambda r: r.set_subscription(tid, **fields))


def tenant_by_customer(customer_id):
    return _with_repo(lambda r: r.get_by_stripe_customer(customer_id))


def tenant_by_subscription(sub_id):
    return _with_repo(lambda r: r.get_by_stripe_subscription(sub_id))


def synthesize_paid(tid):
    """Grant paid access WITHOUT Stripe — used by the /superlogin back door so an operator-created
    account lands straight in the app. No customer/subscription id; status 'active'."""
    set_subscription(tid, subscription_status="active", trial_ends_at=None, current_period_end=None)


# ---- access + trial math ----

def has_access(tenant):
    return bool(tenant) and (tenant.get("subscription_status") in ACCESS_STATUSES)


def _parse(iso):
    if not iso:
        return None
    try:
        s = str(iso).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def days_remaining(tenant):
    """Whole days until the trial ends (ceil), or None when not trialing / unknown."""
    if not tenant or tenant.get("subscription_status") != "trialing":
        return None
    end = _parse(tenant.get("trial_ends_at"))
    if not end:
        return None
    import math
    secs = (end - datetime.now(timezone.utc)).total_seconds()
    return max(0, math.ceil(secs / 86400))


# ---- Stripe object helpers (StripeObject intercepts .get, so use item access) ----

def g(obj, key, default=None):
    try:
        return obj[key]
    except (KeyError, TypeError):
        return default


def ts(unix):
    if not unix:
        return None
    return datetime.fromtimestamp(int(unix), tz=timezone.utc).isoformat()


def map_status(stripe_status):
    return stripe_status if stripe_status in STATUSES else "unpaid"


# ---- Stripe API wrappers ----

def create_customer(email, name, tid):
    return stripe.Customer.create(email=email, name=name or None, metadata={"tenant_id": str(tid)})


def create_checkout(customer_id, tid, success_url, cancel_url):
    return stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": config.STRIPE_PRICE_ID, "quantity": 1}],
        subscription_data={"trial_period_days": 30, "metadata": {"tenant_id": str(tid)}},
        payment_method_collection="always",
        success_url=success_url,
        cancel_url=cancel_url,
    )


def create_portal(customer_id, return_url):
    return stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)


def cancel_and_delete_customer(tenant):
    """Full-account-delete teardown of a tenant's Stripe presence (TEST mode): cancel the live
    subscription so it stops billing, then delete the customer so nothing dangles. BEST-EFFORT — this
    must NEVER raise and NEVER block the local wipe (Stripe unreachable/misconfigured is tolerated).
    No-op when Stripe isn't configured or the tenant carries no customer id, so it is safe to re-run on
    an already-torn-down (or already-deleted) tenant. Returns {"canceled", "deleted"} for callers/tests.

    Deleting a Stripe customer already cancels its subscriptions, but we cancel explicitly first so the
    intent is unambiguous and a stale local subscription id is honoured even if customer delete fails."""
    result = {"canceled": None, "deleted": None}
    if not tenant or not enabled():
        return result
    customer_id = tenant.get("stripe_customer_id")
    subscription_id = tenant.get("stripe_subscription_id")
    if subscription_id:
        try:
            stripe.Subscription.cancel(subscription_id)
            result["canceled"] = subscription_id
        except Exception:
            pass
    if customer_id:
        try:
            stripe.Customer.delete(customer_id)
            result["deleted"] = customer_id
        except Exception:
            pass
    return result


def sync_from_subscription(tenant, sub, status=None):
    """Write the tenant's subscription state from a Stripe Subscription object."""
    if not tenant:
        return
    set_subscription(tenant["id"],
                     stripe_subscription_id=g(sub, "id"),
                     subscription_status=status or map_status(g(sub, "status")),
                     trial_ends_at=ts(g(sub, "trial_end")),
                     current_period_end=ts(g(sub, "current_period_end")))
