"""Execution write path (agency-plan P5) against the IN-PROCESS mock marketplace only — no real API.

Per-account at execution time: (1) TOCTOU re-check against the CURRENT envelope (narrowed => excluded
with reason); (2) durable idempotency (executions.idempotency_key UNIQUE + a done check, so a
crash-restart re-run writes nothing twice); (3) throttle — never exceed an account's token bucket;
(4) pre-state snapshot for rollback. Canary rollout: after the canary slice, a breach halts fan-out
and rolls the canary back to a snapshot-identical state. Brand pause-all halts in-flight between items.
Every write, rollback, halt and pause is ledgered."""
import json
import time

from . import toctou, ledger, tenancy
from .mock_marketplace import ThrottleExceeded
from .. import mail


def set_pause(cur, tenant_id, paused, reason=None):
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("INSERT INTO brand_pause(tenant_id,paused,reason) VALUES(%s,%s,%s) "
                "ON CONFLICT (tenant_id) DO UPDATE SET paused=EXCLUDED.paused, reason=EXCLUDED.reason,"
                " updated_at=now()", (tenant_id, bool(paused), reason))


def is_paused(cur, tenant_id):
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("SELECT paused FROM brand_pause WHERE tenant_id=%s", (tenant_id,))
    row = cur.fetchone()
    return bool(row and row[0])


def pause_all(cur, tenant_id, agency_email="agency@example.com", actor=None):
    """Brand pause-all: set the flag (in-flight execution halts on its next item), ledger, notify."""
    set_pause(cur, tenant_id, True, "brand pause-all")
    ledger.append(cur, tenant_id, actor, "execution.pause_all", payload={"paused": True})
    mail.send(agency_email, "Execution paused by the brand",
              "The brand paused all execution on their account. In-flight work is halting.",
              reply_to="notifications@realifyai.app")


def _exec_row(cur, tenant_id, approval_id, account, status, idem=None, excluded_reason=None,
              pre_state=None, result=None):
    key = idem or f"{approval_id}:{account}:{status}"
    cur.execute(
        "INSERT INTO executions(tenant_id,approval_id,account,idempotency_key,status,excluded_reason,"
        "pre_state,result) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb) "
        "ON CONFLICT (idempotency_key) DO NOTHING RETURNING id",
        (tenant_id, approval_id, account, key, status, excluded_reason,
         json.dumps(pre_state), json.dumps(result) if result is not None else None))
    row = cur.fetchone()
    return row[0] if row else None


def maker_grant_caps(cur, user_id, engagement_id):
    """The user's grant caps on the engagement (fallback to the role template) — used for the execution
    TOCTOU re-check."""
    from ..pdp import ROLES
    cur.execute("SELECT caps, role FROM grants WHERE user_id=%s AND engagement_id=%s ORDER BY id DESC "
                "LIMIT 1", (user_id, engagement_id))
    g = cur.fetchone()
    return g[0] if g and g[0] else ROLES.get((g[1] if g else None) or "account_manager",
                                             ROLES["account_manager"])


def execute_approval(cur, mock, approval_id, account=None):
    """Single-item path: execute ONE approved approval against the mock with the full P5 guardrails
    (TOCTOU re-check, idempotency, token bucket, snapshot, ledger, metering). Marks the approval
    'executed' on a write. Raises ApprovalError unless the approval is 'approved'."""
    from . import approvals as _appr
    from ..pdp import Action
    cur.execute("SELECT tenant_id,engagement_id,maker_user,status,envelope_version,lens,kind,signal "
                "FROM approvals WHERE id=%s", (approval_id,))
    row = cur.fetchone()
    if not row:
        raise _appr.ApprovalError("no such approval")
    tenant_id, eng, maker, status, env_ver, lens, kind, signal = row
    if status != "approved":
        raise _appr.ApprovalError(f"cannot execute from {status}")
    grant_caps = maker_grant_caps(cur, maker, eng)
    acct = account or f"acct-{tenant_id}"
    res = execute_bulk(cur, mock, tenant_id, approval_id, eng, composed_version=env_ver,
                       grant_caps=grant_caps, action=Action(lens, "execute"), accounts=[acct],
                       value_fn=lambda a: {"lens": lens, "kind": kind, "signal": signal}, canary_size=1)
    if res["executed"]:
        cur.execute("UPDATE approvals SET status='executed', updated_at=now() WHERE id=%s", (approval_id,))
        ledger.append(cur, tenant_id, None, "approval.executed",
                      payload={"approval_id": approval_id}, engagement_id=eng)
    return res


def undo_execution(cur, execution_id, actor=None):
    """Per-item Undo: restore the pre-execution snapshot on the mock, mark the execution rolledback,
    ledger it. Uses the existing rollback snapshot (executions.pre_state)."""
    from .mock_marketplace import get_mock
    cur.execute("SELECT tenant_id, account, pre_state, status FROM executions WHERE id=%s", (execution_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError("no such execution")
    tenant_id, account, pre_state, status = row
    if status != "done":
        raise ValueError(f"cannot undo from {status}")
    tenancy.set_brand_scope(cur, [tenant_id])
    get_mock().restore(account, pre_state)
    cur.execute("UPDATE executions SET status='rolledback' WHERE id=%s", (execution_id,))
    ledger.append(cur, tenant_id, actor, "execution.rollback",
                  payload={"execution_id": execution_id, "account": account, "undo": True})
    return {"undone": True, "account": account}


def execute_bulk(cur, mock, tenant_id, approval_id, engagement_id, composed_version, grant_caps,
                 action, accounts, value_fn, canary_size=1, breach_fn=None):
    """Execute `action` across `accounts` on the mock. Returns a result dict:
    {executed, excluded:[{account,reason}], rolledback, halted, halt_reason, halt_seconds}."""
    tenancy.set_brand_scope(cur, [tenant_id])
    res = {"executed": [], "excluded": [], "rolledback": [], "halted": False, "halt_reason": None}
    processed = []                                  # (account, exec_id, pre_state)
    start = time.monotonic()
    for account in accounts:
        if is_paused(cur, tenant_id):               # pause-all halts in-flight (checked each item)
            res["halted"], res["halt_reason"] = True, "paused"
            ledger.append(cur, tenant_id, None, "execution.halted",
                          payload={"reason": "paused", "approval_id": approval_id}, engagement_id=engagement_id)
            break
        chk = toctou.check_at_execute(cur, engagement_id, composed_version, grant_caps, action)
        if not chk["allow"]:                         # envelope narrowed since compose -> exclude
            _exec_row(cur, tenant_id, approval_id, account, "excluded", excluded_reason=chk["reason"])
            res["excluded"].append({"account": account, "reason": chk["reason"]})
            continue
        idem = f"{approval_id}:{account}"
        cur.execute("SELECT status FROM executions WHERE idempotency_key=%s", (idem,))
        ex = cur.fetchone()
        if ex and ex[0] == "done":                  # durable idempotency: already executed
            continue
        if not mock.has_tokens(account):            # never exceed the token bucket
            _exec_row(cur, tenant_id, approval_id, account, "excluded", excluded_reason="throttled")
            res["excluded"].append({"account": account, "reason": "throttled"})
            continue
        pre = mock.value(account)
        try:
            out = mock.write(account, idem, value_fn(account))
        except ThrottleExceeded:
            _exec_row(cur, tenant_id, approval_id, account, "excluded", excluded_reason="throttled")
            res["excluded"].append({"account": account, "reason": "throttled"})
            continue
        exid = _exec_row(cur, tenant_id, approval_id, account, "done", idem=idem, pre_state=pre, result=out)
        ledger.append(cur, tenant_id, None, "execution.write",
                      payload={"account": account, "approval_id": approval_id}, engagement_id=engagement_id)
        from . import metering
        metering.record(cur, tenant_id, approval_id=approval_id, execution_id=exid)   # one event per executed decision
        processed.append((account, exid, pre))
        res["executed"].append(account)
        if breach_fn and len(processed) >= canary_size and breach_fn(res, mock):
            for acc, xid, prev in processed:        # canary breach -> rollback, no further fan-out
                mock.restore(acc, prev)
                if xid is not None:
                    cur.execute("UPDATE executions SET status='rolledback' WHERE id=%s", (xid,))
                ledger.append(cur, tenant_id, None, "execution.rollback",
                              payload={"account": acc, "approval_id": approval_id}, engagement_id=engagement_id)
                res["rolledback"].append(acc)
            res["executed"] = []
            res["halted"], res["halt_reason"] = True, "canary_breach"
            break
    res["halt_seconds"] = round(time.monotonic() - start, 3)
    return res
