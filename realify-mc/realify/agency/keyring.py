"""Per-brand key management on top of realify.agency.crypto. brand_keys is RLS-scoped, so the caller
must have set the brand scope (app.brand_ids) to include tenant_id before calling these. All take a
raw psycopg cursor (agency paths are Postgres/psycopg).

KEK guard (R3): each wrapped DEK records the fingerprint of the KEK it was wrapped under. A mismatch
against the current KEK raises KekMismatch (a clear error, not a cryptic AEAD failure). Rows predating
the fingerprint column backfill lazily on the next successful unwrap."""
from . import crypto, tenancy


class KekMismatch(Exception):
    """The brand key was wrapped under a different KEK than the one currently configured."""


def _unwrap(cur, tenant_id, wrapped, stored_fp):
    cur_fp = crypto.kek_fingerprint()
    if stored_fp and stored_fp != cur_fp:
        raise KekMismatch(f"tenant {tenant_id}: key wrapped under KEK {stored_fp}, current is {cur_fp}")
    dek = crypto.unwrap_dek(bytes(wrapped))                 # raises on a genuine AEAD failure
    if stored_fp is None:                                   # lazy backfill for pre-0028 keys
        cur.execute("UPDATE brand_keys SET kek_fingerprint=%s WHERE tenant_id=%s", (cur_fp, tenant_id))
    return dek


def ensure_brand_key(cur, tenant_id):
    """Return the brand DEK, creating + wrapping a fresh one (fingerprinted) on first use."""
    cur.execute("SELECT wrapped_dek, kek_fingerprint FROM brand_keys WHERE tenant_id=%s", (tenant_id,))
    row = cur.fetchone()
    if row and row[0] is not None:
        return _unwrap(cur, tenant_id, row[0], row[1])
    dek = crypto.new_dek()
    cur.execute(
        "INSERT INTO brand_keys(tenant_id, wrapped_dek, kek_fingerprint) VALUES(%s,%s,%s) "
        "ON CONFLICT (tenant_id) DO UPDATE SET wrapped_dek=EXCLUDED.wrapped_dek, "
        "kek_fingerprint=EXCLUDED.kek_fingerprint",
        (tenant_id, crypto.wrap_dek(dek), crypto.kek_fingerprint()))
    return dek


def brand_dek(cur, tenant_id):
    """The brand DEK, or None if there is no key or it has been crypto-shredded."""
    cur.execute("SELECT wrapped_dek, kek_fingerprint FROM brand_keys WHERE tenant_id=%s", (tenant_id,))
    row = cur.fetchone()
    if not row or row[0] is None:
        return None
    return _unwrap(cur, tenant_id, row[0], row[1])


def crypto_shred(cur, tenant_id):
    """Destroy the wrapped DEK — payloads for this brand become permanently unreadable. The ledger
    hash chain (over ciphertext) still verifies."""
    cur.execute("UPDATE brand_keys SET wrapped_dek=NULL WHERE tenant_id=%s", (tenant_id,))


def resolve_unknowns(cur):
    """Ops one-shot: classify every fingerprint-less key. A key that unwraps under the current KEK is
    backfilled with the current fingerprint; an unrecoverable key (wrong/lost KEK) is crypto-shredded
    (it was never readable). Returns counts. After this, sweep_brand_keys reports unknown == 0."""
    cur.execute("SELECT id FROM tenants")
    ids = [r[0] for r in cur.fetchall()]
    if ids:
        tenancy.set_brand_scope(cur, ids)
    cur.execute("SELECT tenant_id, wrapped_dek FROM brand_keys "
                "WHERE kek_fingerprint IS NULL AND wrapped_dek IS NOT NULL")
    res = {"backfilled": 0, "shredded": 0, "shredded_tenants": []}
    for tid, wd in cur.fetchall():
        try:
            crypto.unwrap_dek(bytes(wd))
            cur.execute("UPDATE brand_keys SET kek_fingerprint=%s WHERE tenant_id=%s",
                        (crypto.kek_fingerprint(), tid))
            res["backfilled"] += 1
        except Exception:
            cur.execute("UPDATE brand_keys SET wrapped_dek=NULL WHERE tenant_id=%s", (tid,))
            res["shredded"] += 1
            res["shredded_tenants"].append(tid)
    return res


def sweep_brand_keys(cur):
    """Ops sweep across ALL brand keys: how many are wrapped under the current KEK, mismatched,
    shredded, or not-yet-fingerprinted. Report-only (never decrypts). Returns a count dict."""
    cur.execute("SELECT id FROM tenants")
    ids = [r[0] for r in cur.fetchall()]
    if ids:
        tenancy.set_brand_scope(cur, ids)
    cur.execute("SELECT tenant_id, wrapped_dek, kek_fingerprint FROM brand_keys")
    cur_fp = crypto.kek_fingerprint()
    out = {"total": 0, "ok": 0, "mismatched": 0, "shredded": 0, "unknown": 0, "current_kek": cur_fp,
           "mismatched_tenants": []}
    for tid, wd, fp in cur.fetchall():
        out["total"] += 1
        if wd is None:
            out["shredded"] += 1
        elif fp is None:
            out["unknown"] += 1
        elif fp == cur_fp:
            out["ok"] += 1
        else:
            out["mismatched"] += 1
            out["mismatched_tenants"].append(tid)
    return out
