"""Governance drift check (agency-plan P7 item 6; R1 taxonomy). Every ACTIVE tenant must be EXACTLY
one of:
  1. seller WITH Stripe                         (a paying customer)
  2. seller under an ACTIVE engagement          (agency-managed brand)
  3. agency_workspace                           (an agency-admin login, not a seller)
  4. internal                                   (Realify staff / tester)
  5. sandbox                                    (seeded demo brand)
Drift = a seller tenant (tenant_kind='seller') that is NEITHER (1) nor (2): no Stripe customer and no
active engagement — an orphan. kinds 3/4/5 are non-seller and never drift. Reads engagements
cross-tenant, so run on a trusted connection (owner / row_security off). Pass tenant_ids to scope."""


def drift_count(cur, tenant_ids=None):
    sql = ("SELECT count(*) FROM tenants t WHERE t.tenant_kind='seller' "
           "AND (t.stripe_customer_id IS NULL OR t.stripe_customer_id='') "
           "AND NOT EXISTS (SELECT 1 FROM engagements e WHERE e.tenant_id=t.id AND e.status='active')")
    params = ()
    if tenant_ids is not None:
        sql += " AND t.id = ANY(%s)"
        params = (list(tenant_ids),)
    cur.execute(sql, params)
    return cur.fetchone()[0]
