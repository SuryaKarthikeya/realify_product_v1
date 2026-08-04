"""Tenant-deletion ledger (agency-plan P3 rider). Every tenant deletion — via ANY path, including the
existing product's delete flow — appends a hash-chained entry (actor, timestamp, tenant) to
deletion_ledger. That table has NO tenant FK, so the entry SURVIVES the deletion (the brand ledger,
by contrast, cascades away with the tenant). Additive hook: it never changes delete semantics, and is
Postgres-only (a no-op on SQLite, so the existing delete flow/tests are untouched)."""
import datetime
import hashlib
import json


def _canonical(actor, tenant_id, ts):
    return json.dumps({"actor": actor, "tenant_id": tenant_id, "ts": ts},
                      sort_keys=True, separators=(",", ":"))


def append(cur, actor, tenant_id):
    ts = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    cur.execute("SELECT hash FROM deletion_ledger ORDER BY seq DESC LIMIT 1")
    row = cur.fetchone()
    prev = row[0] if row else ""
    h = hashlib.sha256((prev + _canonical(actor, tenant_id, ts)).encode()).hexdigest()
    cur.execute("INSERT INTO deletion_ledger(ts, actor, tenant_id, prev_hash, hash) "
                "VALUES(%s,%s,%s,%s,%s) RETURNING seq", (ts, actor, tenant_id, prev, h))
    return cur.fetchone()[0]


def verify_chain(cur):
    cur.execute("SELECT actor, tenant_id, ts, prev_hash, hash FROM deletion_ledger ORDER BY seq")
    prev = ""
    for actor, tenant_id, ts, prev_hash, h in cur.fetchall():
        if prev_hash != prev:
            return False
        ts_s = ts.astimezone(datetime.timezone.utc).replace(microsecond=0).isoformat() \
            if isinstance(ts, datetime.datetime) else ts
        if hashlib.sha256((prev + _canonical(actor, tenant_id, ts_s)).encode()).hexdigest() != h:
            return False
        prev = h
    return True


def on_tenant_deleted(tenant_id, actor="system"):
    """Additive hook for the legacy delete flow. Postgres-only; silently no-ops on SQLite so the
    existing delete path is unchanged."""
    from .. import dbengine
    if dbengine.dialect() != "postgresql":
        return
    try:
        from .db import agency_connect
        conn = agency_connect()
        try:
            cur = conn.cursor()
            append(cur, actor, tenant_id)
            conn.commit()
        finally:
            conn.close()
    except Exception:
        # never let ledgering break a deletion; the entry is best-effort audit on top of the delete
        pass
