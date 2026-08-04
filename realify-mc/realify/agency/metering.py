"""Decision metering (agency-plan P6): one event per executed decision, per client. Feeds usage
records + per-client cost allocation. Brand-scoped (RLS)."""
from . import tenancy


def record(cur, tenant_id, approval_id=None, execution_id=None, event_type="decision.executed", qty=1):
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("INSERT INTO metering_events(tenant_id,approval_id,execution_id,event_type,qty) "
                "VALUES(%s,%s,%s,%s,%s) RETURNING id", (tenant_id, approval_id, execution_id, event_type, qty))
    return cur.fetchone()[0]


def per_client_qty(cur, tenant_ids, period_start=None, period_end=None):
    """{tenant_id: total qty} over the (optional) period, for the actor's brands (RLS-scoped)."""
    if not tenant_ids:
        return {}
    tenancy.set_brand_scope(cur, tenant_ids)
    sql = "SELECT tenant_id, COALESCE(SUM(qty),0) FROM metering_events"
    params, where = [], []
    if period_start is not None:
        where.append("created_at >= %s"); params.append(period_start)
    if period_end is not None:
        where.append("created_at < %s"); params.append(period_end)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY tenant_id"
    cur.execute(sql, tuple(params))
    return {tid: int(q) for tid, q in cur.fetchall()}
