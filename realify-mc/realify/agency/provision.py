"""Approve -> provision: idempotent, step-tracked, resumable. The 6 steps run in order; each is
idempotent (find-or-create / set); each step's status is committed as it completes, so a failure leaves
a VISIBLE failed step (no silent partial) and a retry resumes and completes. The request only becomes
'live' when all 6 steps are done.

`fault_step` (tests only) makes one step raise once, to exercise the failed-step-visible + retry path.
"""
import json

from . import funnel, invites, mailcfg, db as agency_db
from .. import mail, config

STEPS = ["create_org", "plan_params", "admin_invite", "billing_stub", "ledger_entry", "slack_webhook"]


def _step_status(cur, request_id):
    cur.execute("SELECT step, status FROM agency_provision_steps WHERE request_id=%s", (request_id,))
    return {s: st for s, st in cur.fetchall()}


def _ensure_steps(cur, request_id):
    for step in STEPS:
        cur.execute("INSERT INTO agency_provision_steps(request_id, step) VALUES(%s,%s) "
                    "ON CONFLICT (request_id, step) DO NOTHING", (request_id, step))


def _mark(cur, request_id, step, status, error=None):
    cur.execute("UPDATE agency_provision_steps SET status=%s, error=%s, updated_at=now() "
                "WHERE request_id=%s AND step=%s", (status, error, request_id, step))


def _run_step(cur, step, req, actor):
    rid, agency_id = req["id"], req["agency_id"]
    if step == "create_org":
        if not agency_id:
            cur.execute("INSERT INTO agencies(name, hq_country) VALUES(%s,%s) RETURNING id",
                        (req["agency_name"], req["hq_country"]))
            agency_id = cur.fetchone()[0]
            cur.execute("UPDATE agency_requests SET agency_id=%s WHERE id=%s", (agency_id, rid))
            req["agency_id"] = agency_id
    elif step == "plan_params":
        params = {"am_headcount": req["am_headcount"], "reporting_hours": req["reporting_hours"],
                  "plan": "pilot"}
        cur.execute("UPDATE agencies SET plan_params=%s::jsonb WHERE id=%s",
                    (json.dumps(params), req["agency_id"]))
    elif step == "admin_invite":
        token, _iid = invites.create_agency_invite(cur, req["agency_id"], req["contact_email"])
        if token:                     # new invite -> email the link; reuse (None) was already emailed once
            base = (config.APP_URL or "https://realifyai.app").rstrip("/")
            link = f"{base}/agency/invite/{token}"
            # If this send raises, the step fails visibly (no silent partial) and no invite_emailed audit
            # is written — so the "invite emailed" label only renders when the ledgered send exists.
            mail.send(req["contact_email"], "Your Realify for Agencies workspace is ready",
                      f"You've been invited to set up {req['agency_name']} on Realify.\n\n"
                      f"Set your password and enter your workspace (single-use link, expires in 7 days):\n"
                      f"{link}\n\nThis is a pilot — no charge during the pilot window.",
                      from_addr=mailcfg.from_addr(), reply_to=mailcfg.reply_to())
            agency_db.audit(cur, actor, "agency.invite_emailed", agency_id=req["agency_id"],
                            detail={"email": req["contact_email"]})
    elif step == "billing_stub":
        cur.execute("UPDATE agencies SET billing_status='stub' WHERE id=%s", (req["agency_id"],))
    elif step == "ledger_entry":
        agency_db.audit(cur, actor, "agency.provisioned", agency_id=req["agency_id"],
                        detail={"ref": req["ref"]})
    elif step == "slack_webhook":
        _post_slack_stub(req)          # stub — no external call; the step status is the record


def _post_slack_stub(req):
    return True


def provision(conn, request_id, actor="ops", fault_step=None):
    """Run/resume provisioning. Returns {"ok": bool, "failed_step": str|None, "status": str}."""
    cur = conn.cursor()
    cur.execute("SELECT status FROM agency_requests WHERE id=%s", (request_id,))
    if (cur.fetchone() or [None])[0] == "live":
        return {"ok": True, "failed_step": None, "status": "live"}   # idempotent: already provisioned
    req = _load(cur, request_id)
    _ensure_steps(cur, request_id)
    funnel.set_status(cur, request_id, "provisioning")
    conn.commit()

    done = _step_status(cur, request_id)
    for step in STEPS:
        if done.get(step) == "done":
            continue
        try:
            if fault_step == step:
                raise RuntimeError(f"injected fault at {step}")
            _run_step(cur, step, req, actor)
            _mark(cur, request_id, step, "done")
            conn.commit()
        except Exception as e:
            conn.rollback()
            cur = conn.cursor()
            _mark(cur, request_id, step, "failed", error=str(e))
            conn.commit()
            return {"ok": False, "failed_step": step, "status": "provisioning"}
    funnel.set_status(cur, request_id, "live")
    conn.commit()
    return {"ok": True, "failed_step": None, "status": "live"}


def _load(cur, request_id):
    cur.execute(
        "SELECT id,ref,agency_name,contact_email,hq_country,am_headcount,reporting_hours,agency_id "
        "FROM agency_requests WHERE id=%s", (request_id,))
    row = cur.fetchone()
    cols = ["id", "ref", "agency_name", "contact_email", "hq_country", "am_headcount",
            "reporting_hours", "agency_id"]
    return dict(zip(cols, row))
