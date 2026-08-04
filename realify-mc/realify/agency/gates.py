"""Gates / attestation engine (agency-plan P7, internal admin screens 25-26). Gates carry a provenance:
`auto` (system-derived) or `attested` (a human vouches, with required evidence + validity window).
Attestation writes an IMMUTABLE audit entry; expiry auto-flips the gate to EXPIRED. An `attested` gate
may NEVER overwrite an `auto` one (API attempt => 403). Postgres-only (agency admin)."""
import datetime

from .db import audit


class AttestOverwriteError(Exception):
    """Attempt to attest over an active auto gate — route maps to 403."""


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def set_auto(cur, gate_key, scope="platform", status="active"):
    cur.execute("INSERT INTO gates(gate_key,scope,provenance,status) VALUES(%s,%s,'auto',%s) RETURNING id",
                (gate_key, scope, status))
    return cur.fetchone()[0]


def current(cur, gate_key):
    cur.execute("SELECT id,provenance,status,valid_until FROM gates WHERE gate_key=%s "
                "ORDER BY created_at DESC, id DESC LIMIT 1", (gate_key,))
    r = cur.fetchone()
    return dict(zip(["id", "provenance", "status", "valid_until"], r)) if r else None


def attest(cur, gate_key, scope, evidence_link, valid_until, actor):
    """Attest a gate. evidence_link is required. Refuses to overwrite an ACTIVE auto gate."""
    if not evidence_link:
        raise ValueError("evidence_link is required for an attestation")
    cur_gate = current(cur, gate_key)
    if cur_gate and cur_gate["provenance"] == "auto" and cur_gate["status"] != "EXPIRED":
        raise AttestOverwriteError("an attested gate may not overwrite an auto gate")
    cur.execute("INSERT INTO gates(gate_key,scope,provenance,status,evidence_link,valid_until) "
                "VALUES(%s,%s,'attested','active',%s,%s) RETURNING id",
                (gate_key, scope, evidence_link, valid_until))
    gid = cur.fetchone()[0]
    audit(cur, str(actor), "gate.attest",
          detail={"gate_key": gate_key, "scope": scope, "evidence_link": evidence_link,
                  "valid_until": str(valid_until), "gate_id": gid})     # immutable ledger entry
    return gid


def expire_gates(cur, now=None):
    """Flip attested gates past their validity window to EXPIRED. Returns the count."""
    now = now or _now()
    cur.execute("UPDATE gates SET status='EXPIRED' WHERE provenance='attested' AND status='active' "
                "AND valid_until IS NOT NULL AND valid_until < %s", (now,))
    return cur.rowcount


def fleet_metrics(cur):
    """Fleet metrics computed from config/ledger (screen 25)."""
    m = {}
    cur.execute("SELECT count(*) FROM gates WHERE status='active'")
    m["active_gates"] = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM gates WHERE status='EXPIRED'")
    m["expired_gates"] = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM engagements WHERE status='active'")
    m["active_engagements"] = cur.fetchone()[0]
    return m
