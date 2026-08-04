"""Internal-tenant flag: the ledgered normal<->internal toggle and query-time exclusion helpers.

The flag is evaluated AT QUERY TIME (aggregates filter `WHERE NOT is_internal`), so flipping it is
retroactive — a tenant marked internal today drops out of historical aggregates immediately. Every
toggle is recorded in agency_audit with actor, timestamp and optional reason.
"""


def toggle_internal(conn, actor, tenant_id, to_internal, reason=None):
    """Ops mark/unmark: set tenant_kind ('internal' when marked, else 'seller') and keep the deprecated
    is_internal flag in sync. Append a ledger (agency_audit) entry. Returns the new value."""
    from .db import audit
    kind = "internal" if to_internal else "seller"
    cur = conn.cursor()
    cur.execute("UPDATE tenants SET tenant_kind=%s, is_internal=%s WHERE id=%s",
                (kind, bool(to_internal), tenant_id))
    audit(cur, actor, "tenant.internal_toggle", tenant_id=tenant_id,
          detail={"is_internal": bool(to_internal), "tenant_kind": kind}, reason=reason)
    conn.commit()
    return bool(to_internal)


def list_tenants(cur):
    """Ops tenants list: id, owner email, created, Stripe status, tenant_kind (+ legacy is_internal)."""
    cur.execute(
        "SELECT t.id, u.email, t.created_at, t.subscription_status, t.stripe_customer_id, t.is_internal, "
        "t.tenant_kind FROM tenants t LEFT JOIN LATERAL ("
        "  SELECT email FROM users WHERE tenant_id=t.id ORDER BY id LIMIT 1) u ON true "
        "ORDER BY t.id")
    cols = ["id", "email", "created_at", "subscription_status", "stripe_customer_id", "is_internal",
            "tenant_kind"]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def count_billable_tenants(cur):
    """Billable tenants — the aggregate base: only true seller tenants (kind='seller'); every other
    kind (agency_workspace, internal, sandbox) is excluded. Query-time, so exclusion is retroactive."""
    cur.execute("SELECT count(*) FROM tenants WHERE tenant_kind='seller'")
    return cur.fetchone()[0]


def count_revenue_accounts(cur):
    """Seller tenants with a Stripe customer — real revenue accounts."""
    cur.execute("SELECT count(*) FROM tenants WHERE tenant_kind='seller' "
                "AND stripe_customer_id IS NOT NULL AND stripe_customer_id <> ''")
    return cur.fetchone()[0]


LEVERAGE_GATE = 1.5      # PRD §14: accounts-per-AM leverage ratio gate


def fleet_rows(cur, include_internal=False):
    """Per-agency fleet metrics for the admin overview (screen 25): accounts, AMs, leverage ratio
    (accounts/AMs vs the 1.5× gate), decisions used/pool, acceptance %, MRR. Run on a trusted/scoped
    connection (reads across brands). By default EXCLUDES internal/sandbox agencies (R7 3a) — the
    verification/sandbox cruft — so the default view shows only real agencies."""
    from . import tenancy
    cur.execute("SELECT id FROM tenants")
    ids = [r[0] for r in cur.fetchall()]
    if ids:
        tenancy.set_brand_scope(cur, ids)
    where = "" if include_internal else \
        " WHERE NOT COALESCE(internal, false) AND sandbox_scenario IS NULL"
    cur.execute(f"SELECT id, name FROM agencies{where} ORDER BY name")
    out = []
    for ag, name in cur.fetchall():
        cur.execute("SELECT tenant_id FROM engagements WHERE agency_id=%s AND status='active'", (ag,))
        brands = [r[0] for r in cur.fetchall()]
        accounts = len(brands)
        cur.execute("SELECT count(DISTINCT g.user_id) FROM grants g JOIN engagements e ON e.id=g.engagement_id "
                    "WHERE e.agency_id=%s AND g.role IN ('account_manager','agency_admin')", (ag,))
        ams = cur.fetchone()[0] or 0
        leverage = round(accounts / ams, 2) if ams else 0.0
        acceptance = used = 0
        if brands:
            cur.execute("SELECT count(*), count(*) FILTER (WHERE status='executed') FROM approvals "
                        "WHERE tenant_id = ANY(%s)", (brands,))
            prop, ex = cur.fetchone()
            acceptance = int(round((ex or 0) * 100 / prop)) if prop else 0
            cur.execute("SELECT COALESCE(SUM(qty),0) FROM metering_events WHERE tenant_id = ANY(%s)", (brands,))
            used = cur.fetchone()[0] or 0
        cur.execute("SELECT per_account_price_minor, platform_fee_minor, decisions_pool "
                    "FROM agency_subscriptions WHERE agency_id=%s", (ag,))
        s = cur.fetchone()
        mrr = ((s[0] or 0) * accounts + (s[1] or 0)) if s else 0
        pool = int(s[2]) if s else 0
        out.append({"agency_id": str(ag), "name": name, "accounts": accounts, "ams": ams,
                    "leverage": leverage, "acceptance": acceptance, "mrr_usd_minor": mrr,
                    "pool": pool, "used": used, "needs_attention": bool(ams and leverage < LEVERAGE_GATE)})
    return out
