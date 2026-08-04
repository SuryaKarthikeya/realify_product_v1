"""Per-request brand scoping for RLS. Resolve the actor's allowed brand set (from grants) once, then
call set_brand_scope() INSIDE the request transaction: it issues `set_config('app.brand_ids', ..., true)`
so the RLS policies (tenant_id = ANY(current_brand_ids())) see exactly those brands. Transaction-local
(the `true`) => safe under pgbouncer transaction pooling. Fail-closed: an empty set makes every
brand-scoped table return zero rows.
"""


def _array_literal(tenant_ids):
    # int()-coerce every id, so the value is a safe Postgres array literal with no injection surface.
    return "{" + ",".join(str(int(t)) for t in tenant_ids) + "}"


def set_brand_scope(cur, tenant_ids):
    """Restrict RLS to `tenant_ids` for the current transaction. `cur` is a DB-API cursor on a
    Postgres connection; must be called inside the transaction whose statements need the scope."""
    cur.execute("SELECT set_config('app.brand_ids', %s, true)", (_array_literal(tenant_ids),))


def clear_brand_scope(cur):
    """Explicitly empty the scope (defensive; a new transaction already starts unscoped)."""
    cur.execute("SELECT set_config('app.brand_ids', '', true)")
