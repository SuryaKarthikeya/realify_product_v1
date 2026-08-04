"""Work queue (agency-plan P4). Grant-scoped via RLS (the caller passes the actor's allowed brand
set); ranked by impact_usd_minor desc with a stable tiebreak so ordering is byte-identical run to run.
Items render in the brand's selling currency with the USD-normalized rank value exposed. Optional
per-account fairness weighting prevents any account being starved out of the top-K."""
from . import tenancy, money

_COLS = ["tenant_id", "lens", "kind", "impact_minor", "impact_currency", "fx_rate_id", "impact_usd_minor",
         "confidence", "signal", "status"]


def _item(r):
    return {**r, "rank_usd_minor": r["impact_usd_minor"],
            "display": money.format_money(r["impact_minor"], r["impact_currency"])}


def build(cur, allowed_tenant_ids, top_k=None):
    """Ranked open decisions across the actor's allowed brands (RLS-enforced). Deterministic order."""
    if not allowed_tenant_ids:
        return []
    tenancy.set_brand_scope(cur, allowed_tenant_ids)
    # Explicit tenant filter IN ADDITION to RLS (R2/R11 lesson: never rely on RLS alone — the harness
    # owner bypasses it, so a route/aggregate scope bug only surfaces live; the explicit ANY() keeps
    # per-brand queries correct under both the owner and the runtime realify_app role).
    cur.execute("SELECT tenant_id,lens,kind,impact_minor,impact_currency,fx_rate_id,impact_usd_minor,"
                "confidence,signal,status FROM decisions WHERE status='open' AND tenant_id = ANY(%s) "
                "ORDER BY impact_usd_minor DESC, tenant_id, signal", (list(allowed_tenant_ids),))
    items = [_item(dict(zip(_COLS, r))) for r in cur.fetchall()]
    return items[:top_k] if top_k else items


def fair_select(accounts_best, top_k, day, last_shown):
    """Least-recently-shown-first selection of accounts for a synthetic `day` (fairness weighting):
    staler accounts first, then higher impact, then id. Updates last_shown in place. Guarantees each
    account is shown at least every ceil(#accounts / top_k) days — so no account starves."""
    accts = sorted(accounts_best,
                   key=lambda a: (-(day - last_shown.get(a, -10 ** 9)),
                                  -accounts_best[a]["impact_usd_minor"], a))
    chosen = accts[:top_k]
    for a in chosen:
        last_shown[a] = day
    return chosen
