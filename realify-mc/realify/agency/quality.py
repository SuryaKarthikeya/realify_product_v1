"""Quality console (agency-plan P7, screen 27). Precision by action class = realized (executed) ÷
proposed, from ledgered approvals/executions; aggregated dismissal reasons; per-agency drift. All
metrics are deterministic recomputations (reproducible: recompute == displayed). Mitigations (e.g.
raising a confidence gate) are LEDGERED config changes — never hand-edits."""
from .db import audit
from . import tenancy


def precision_by_action(cur, brands):
    """{'lens/kind': {proposed, realized, precision_bps}} across the actor's brands (RLS-scoped)."""
    if not brands:
        return {}
    tenancy.set_brand_scope(cur, brands)
    cur.execute("SELECT lens, kind, count(*) FROM approvals GROUP BY lens, kind")
    proposed = {(l, k): n for l, k, n in cur.fetchall()}
    cur.execute("SELECT a.lens, a.kind, count(DISTINCT e.approval_id) FROM executions e "
                "JOIN approvals a ON a.id = e.approval_id WHERE e.status='done' GROUP BY a.lens, a.kind")
    realized = {(l, k): n for l, k, n in cur.fetchall()}
    out = {}
    for key, p in sorted(proposed.items()):
        r = realized.get(key, 0)
        out[f"{key[0]}/{key[1]}"] = {"proposed": p, "realized": r,
                                     "precision_bps": int(round(r * 10000 / p)) if p else 0}
    return out


def dismissal_reasons(cur, brands):
    if not brands:
        return {}
    tenancy.set_brand_scope(cur, brands)
    cur.execute("SELECT excluded_reason, count(*) FROM executions "
                "WHERE status='excluded' AND excluded_reason IS NOT NULL GROUP BY excluded_reason")
    return {r: n for r, n in cur.fetchall()}


def mitigation(cur, agency_id, change, actor):
    """Record a mitigation (e.g. confidence-gate raise) as a LEDGERED config change, not a hand-edit."""
    audit(cur, str(actor), "quality.mitigation", agency_id=agency_id, detail=change)
    return {"ledgered": True, "change": change}


def acceptance_drift(cur, brands):
    """Recommendation-quality signal (distinct from governance drift.py): per-action acceptance =
    executed ÷ proposed, from queue-sourced approvals. v1 is the standing ratio by action class;
    trend/drift over windows is a straightforward extension."""
    if not brands:
        return {}
    tenancy.set_brand_scope(cur, brands)
    cur.execute("SELECT lens, kind, count(*), count(*) FILTER (WHERE status='executed') "
                "FROM approvals GROUP BY lens, kind ORDER BY lens, kind")
    out = {}
    for lens, kind, total, ex in cur.fetchall():
        out[f"{lens}/{kind}"] = {"proposed": total, "accepted": ex,
                                 "acceptance_bps": int(round(ex * 10000 / total)) if total else 0}
    return out
