"""Pilot conversion (agency-plan P6, screen 24). The conversion summary is assembled ONLY from
ledger-derived numbers (no literals). E-sign records terms_version to the ledger. NO auto-convert: a
day-90 lapse with no signature flips the workspace read-only (+ export offer), and billing then charges
ZERO (see billing_agency.build_invoice)."""
import datetime

from . import tenancy
from .db import audit

LAPSE_DAYS = 90


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def start(cur, agency_id):
    cur.execute("INSERT INTO agency_pilots(agency_id) VALUES(%s) ON CONFLICT (agency_id) DO NOTHING",
                (agency_id,))


def conversion_summary(cur, agency_id, brands):
    """Numbers for the conversion page — every value is a COUNT/SUM over the ledger (ledger-derived)."""
    if not brands:
        return {"executions_ledgered": 0, "approvals_ledgered": 0}
    tenancy.set_brand_scope(cur, brands)
    cur.execute("SELECT count(*) FROM ledger WHERE action='execution.write'")
    executions = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM ledger WHERE action='approval.approve'")
    approvals_ = cur.fetchone()[0]
    return {"executions_ledgered": executions, "approvals_ledgered": approvals_}


def esign(cur, agency_id, terms_version, user):
    """Record the e-signature + terms_version to the ledger (agency audit)."""
    start(cur, agency_id)
    cur.execute("UPDATE agency_pilots SET signed_at=now(), terms_version=%s WHERE agency_id=%s",
                (terms_version, agency_id))
    audit(cur, str(user), "pilot.esign", agency_id=agency_id, detail={"terms_version": terms_version})
    return {"signed": True, "terms_version": terms_version}


def lapse_job(cur, agency_id, now=None):
    """Day-90 lapse: no signature => workspace read-only + export offer (ledgered). Never auto-converts."""
    now = now or _now()
    cur.execute("SELECT started_at, signed_at FROM agency_pilots WHERE agency_id=%s", (agency_id,))
    row = cur.fetchone()
    if not row:
        return {"read_only": False}
    started, signed = row
    if signed is None and (now - started).days >= LAPSE_DAYS:
        cur.execute("UPDATE agency_pilots SET read_only=true WHERE agency_id=%s", (agency_id,))
        audit(cur, "system", "pilot.lapsed_readonly", agency_id=agency_id,
              detail={"export_offer": True})
        return {"read_only": True, "export_offer": True}
    return {"read_only": False}


def is_read_only(cur, agency_id):
    cur.execute("SELECT read_only FROM agency_pilots WHERE agency_id=%s", (agency_id,))
    r = cur.fetchone()
    return bool(r and r[0])
