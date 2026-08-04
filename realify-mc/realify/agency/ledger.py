"""Append-only, per-brand, hash-chained ledger (agency-plan §1b non-negotiable): every mutating agency
operation writes exactly ONE entry. hash = sha256(prev_hash ‖ canonical(row)); the chain is per brand
(prev_hash links the brand's previous entry). Payloads are encrypted with the brand DEK, so the hash is
over ciphertext — crypto-shred leaves the chain verifiable but the payloads unreadable.

Raw psycopg cursor in/out (agency paths are Postgres); the caller must have set the brand scope first
(ledger is RLS-scoped), so an actor can only append/read entries for brands they hold.
"""
import datetime
import hashlib
import json

from . import keyring


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def _ts_norm(v):
    """Normalise a ts (str at write, datetime at read) to one canonical UTC-seconds ISO string."""
    if isinstance(v, datetime.datetime):
        return v.astimezone(datetime.timezone.utc).replace(microsecond=0).isoformat()
    return v


def _canonical(core):
    return json.dumps(core, sort_keys=True, separators=(",", ":"), default=str)


def _core(tenant_id, actor_user, action, grant_id, engagement_id, envelope_version, payload_enc, ts):
    return {
        "tenant_id": tenant_id, "actor_user": actor_user, "action": action,
        "grant_id": str(grant_id) if grant_id else None,
        "engagement_id": str(engagement_id) if engagement_id else None,
        "envelope_version": envelope_version,
        "payload_enc": bytes(payload_enc).hex() if payload_enc is not None else None,
        "ts": _ts_norm(ts),
    }


def append(cur, tenant_id, actor_user, action, payload=None, grant_id=None,
           engagement_id=None, envelope_version=None):
    """Write exactly one ledger entry for `tenant_id`; returns its seq. payload (a dict) is JSON-canon
    + AES-GCM encrypted with the brand DEK."""
    ts = _now_iso()
    payload_enc = None
    if payload is not None:
        from . import crypto
        dek = keyring.ensure_brand_key(cur, tenant_id)
        payload_enc = crypto.encrypt(dek, _canonical(payload).encode())
    cur.execute("SELECT hash FROM ledger WHERE tenant_id=%s ORDER BY seq DESC LIMIT 1", (tenant_id,))
    row = cur.fetchone()
    prev = row[0] if row else ""
    core = _core(tenant_id, actor_user, action, grant_id, engagement_id, envelope_version, payload_enc, ts)
    h = hashlib.sha256((prev + _canonical(core)).encode()).hexdigest()
    cur.execute(
        "INSERT INTO ledger(ts,actor_user,tenant_id,grant_id,engagement_id,envelope_version,action,"
        "payload_enc,prev_hash,hash) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING seq",
        (ts, actor_user, tenant_id, grant_id, engagement_id, envelope_version, action, payload_enc, prev, h))
    return cur.fetchone()[0]


def verify_chain(cur, tenant_id):
    """Recompute the brand's chain; True iff every link and hash is intact."""
    cur.execute(
        "SELECT ts,actor_user,grant_id,engagement_id,envelope_version,action,payload_enc,prev_hash,hash "
        "FROM ledger WHERE tenant_id=%s ORDER BY seq", (tenant_id,))
    prev = ""
    for ts, actor, gid, eid, ev, action, penc, prev_hash, h in cur.fetchall():
        if prev_hash != prev:
            return False
        core = _core(tenant_id, actor, action, gid, eid, ev, penc, ts)
        if hashlib.sha256((prev + _canonical(core)).encode()).hexdigest() != h:
            return False
        prev = h
    return True


def read_payload(cur, tenant_id, seq):
    """Decrypt one entry's payload, or None if there is no payload / the brand key was shredded."""
    cur.execute("SELECT payload_enc FROM ledger WHERE tenant_id=%s AND seq=%s", (tenant_id, seq))
    row = cur.fetchone()
    if not row or row[0] is None:
        return None
    dek = keyring.brand_dek(cur, tenant_id)
    if dek is None:
        return None
    from . import crypto
    return json.loads(crypto.decrypt(dek, bytes(row[0])).decode())
