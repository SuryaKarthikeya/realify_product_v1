"""Brand provider connections (agency-plan P3). Stub OAuth (mock provider) sets a connection
'connected' with an expiry; a health job flips stale -> expired; while any connection is expired the
brand's dependent decisions are PAUSED (never silently computed). Brand-scoped (RLS): callers set the
brand scope; the health job scopes to all tenants (it's a trusted sweep, no BYPASSRLS)."""
import datetime

from . import tenancy

PROVIDERS = ("amazon", "shopify", "amazon_ads", "google_ads", "meta_ads")


class DecisionsPaused(Exception):
    """Raised when a brand's decisions must not be computed (an expired connection)."""


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def upsert_connection(cur, tenant_id, provider, status="connected", expires_at=None):
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute(
        "INSERT INTO connections(tenant_id,provider,status,expires_at) VALUES(%s,%s,%s,%s) "
        "ON CONFLICT (tenant_id,provider) DO UPDATE SET status=EXCLUDED.status, "
        "expires_at=EXCLUDED.expires_at RETURNING id", (tenant_id, provider, status, expires_at))
    return cur.fetchone()[0]


def health_run(cur):
    """Flip every connection whose expiry has passed to 'expired'. Trusted sweep across all tenants
    (scoped to the full tenant set, not BYPASSRLS). Returns the number flipped."""
    cur.execute("SELECT id FROM tenants")
    ids = [r[0] for r in cur.fetchall()]
    if not ids:
        return 0
    tenancy.set_brand_scope(cur, ids)
    cur.execute("UPDATE connections SET status='expired' "
                "WHERE expires_at IS NOT NULL AND expires_at < now() AND status <> 'expired'")
    return cur.rowcount


def decisions_paused(cur, tenant_id):
    """True if the brand has any expired connection (evaluated at query time)."""
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("SELECT EXISTS(SELECT 1 FROM connections WHERE tenant_id=%s AND status='expired')",
                (tenant_id,))
    return cur.fetchone()[0]


def guard_decisions(cur, tenant_id):
    """Call before computing any dependent decision — raises DecisionsPaused instead of computing."""
    if decisions_paused(cur, tenant_id):
        raise DecisionsPaused(f"tenant {tenant_id}: an integration is expired; reconnect to resume")


def compute_decisions_guarded(cur, tenant_id, compute):
    """Representative dependent-decision path: pause instead of silently computing."""
    if decisions_paused(cur, tenant_id):
        return {"paused": True, "decisions": None}
    return {"paused": False, "decisions": compute()}
