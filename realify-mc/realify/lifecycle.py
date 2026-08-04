"""R17 — the ONE account-deletion lifecycle, shared by the self-serve accounts pane (seller path) and the
ops close-out queue (agency path). Deletion is a state machine, not a button: requests move
requested → hold → ready → wiped, reversible via Cancel until the single irreversible Execute step.

Decisions (R17): hard wipe (no grace/recovery); keep the real brand name in captured seeds; the billing
gate is hard-block WITH an operator override (written reason); agency delete wipes its brands (no detach);
customer self-delete with a balance enters the queue, testers wipe immediately.

This module is connection-AGNOSTIC for the shared tables (`deletion_requests`, `captured_seeds`, `tenants`,
`seller_skus`) — the caller passes its own `con` (seller `db.connect()` or agency owner conn; in prod one
RDS). Agency-only steps (crypto-shred, composite brand enumeration) are best-effort + Postgres-guarded.
"""
import json
from datetime import datetime, timezone

from . import db, billing

# ---- state machine ---------------------------------------------------------
STATUSES = ("requested", "hold", "ready", "wiped", "canceled")
_LEGAL = {
    "requested": {"hold", "ready", "wiped", "canceled"},
    "hold": {"ready", "canceled"},
    "ready": {"wiped", "canceled"},
    "wiped": set(),        # terminal
    "canceled": set(),     # terminal
}
_OPEN = ("requested", "hold", "ready")     # a request still in flight (soft-flagged, reversible)
_CAPTURE_MIN_SKUS = 5                        # a catalog worth rescuing


class TransitionError(Exception):
    pass


def can_transition(frm, to):
    return to in _LEGAL.get(frm, set())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---- deletion_requests repo (works on either engine) -----------------------
def open_request_for(con, entity_type, entity_ref):
    row = con.execute(
        "SELECT * FROM deletion_requests WHERE entity_type=? AND entity_ref=? "
        "AND status IN ('requested','hold','ready') ORDER BY id DESC LIMIT 1",
        (entity_type, str(entity_ref))).fetchone()
    return dict(row) if row else None


def get_request(con, req_id):
    row = con.execute("SELECT * FROM deletion_requests WHERE id=?", (req_id,)).fetchone()
    return dict(row) if row else None


def list_pending(con):
    rows = con.execute(
        "SELECT * FROM deletion_requests WHERE status IN ('requested','hold','ready') "
        "ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def create_request(con, entity_type, entity_ref, label, requested_by, account_type,
                   status="requested", capture_seed=False, reason=None):
    """IDEMPOTENT: a duplicate delete on an entity with an OPEN request reuses that request."""
    dup = open_request_for(con, entity_type, entity_ref)
    if dup:
        return dup["id"]
    con.execute(
        "INSERT INTO deletion_requests(entity_type,entity_ref,label,requested_by,requested_at,status,"
        "account_type,billing_settled,capture_seed,reason) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (entity_type, str(entity_ref), label, requested_by, _now(), status, account_type,
         False, bool(capture_seed), reason))
    con.commit()
    row = con.execute("SELECT id FROM deletion_requests WHERE entity_type=? AND entity_ref=? "
                      "ORDER BY id DESC LIMIT 1", (entity_type, str(entity_ref))).fetchone()
    return row["id"] if row else None


def set_status(con, req_id, to_status):
    cur_row = get_request(con, req_id)
    if not cur_row:
        raise TransitionError(f"no request {req_id}")
    if cur_row["status"] == to_status:
        return
    if not can_transition(cur_row["status"], to_status):
        raise TransitionError(f"illegal transition {cur_row['status']} → {to_status}")
    stamp = _now() if to_status == "wiped" else None
    con.execute("UPDATE deletion_requests SET status=?, executed_at=COALESCE(?,executed_at) WHERE id=?",
                (to_status, stamp, req_id))
    con.commit()


def mark_settled(con, req_id, override_reason=None):
    con.execute("UPDATE deletion_requests SET billing_settled=?, override_reason=? WHERE id=?",
                (True, override_reason, req_id))
    con.commit()


# ---- billing gate ----------------------------------------------------------
def account_type_of(con, tenant_id):
    """customer | tester | managed_brand — the routing hint for a brand tenant."""
    t = db.get_tenant(con, tenant_id) or {}
    kind = t.get("tenant_kind")
    if kind in ("sandbox", "internal"):
        return "tester"
    if db.get_account_type(con, tenant_id) == "tester":
        return "tester"
    if kind == "agency_workspace":
        return "managed_brand"
    return "customer"


def billing_settled(con, entity_type, entity_ref):
    """No money owed / no ongoing billing. Testers, sandbox, managed brands (billed at the agency) are
    trivially settled. A seller customer is settled only once its subscription is canceled/absent."""
    if entity_type != "brand":
        return _agency_billing_settled(entity_ref) if entity_type == "agency" else True
    at = account_type_of(con, int(entity_ref))
    if at != "customer":
        return True
    t = db.get_tenant(con, int(entity_ref)) or {}
    status = t.get("subscription_status")
    return status in (None, "", "canceled")     # active/trialing/past_due/unpaid ⇒ NOT settled


def settle_billing(con, req):
    """Mark paid up (R17 Part B): seller → cancel the Stripe subscription + delete the customer and flip
    the local status to canceled; agency → mark open invoices paid + cancel the sub. Best-effort — the
    billing_settled flag (set by the caller) is the gate; this just closes the money out."""
    et, ref = req["entity_type"], req["entity_ref"]
    if et == "brand":
        t = db.get_tenant(con, int(ref))
        if t:
            try:
                billing.cancel_and_delete_customer(t)
            except Exception:
                pass
            con.execute("UPDATE tenants SET subscription_status='canceled' WHERE id=?", (int(ref),))
            con.commit()
    elif et == "agency":
        try:
            from . import dbengine
            if dbengine.dialect() != "postgresql":
                return
            from .agency.db import agency_connect
            conn = agency_connect()
            try:
                cur = conn.cursor()
                cur.execute("UPDATE invoices SET status='paid' WHERE agency_id=%s AND status='open'", (ref,))
                cur.execute("UPDATE agency_subscriptions SET status='canceled' WHERE agency_id=%s", (ref,))
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass


def _agency_billing_settled(agency_id):
    """PG-only: settled when the agency has no 'open' invoices. Best-effort (True if agency tables absent)."""
    try:
        from . import dbengine
        if dbengine.dialect() != "postgresql":
            return True
        from .agency.db import agency_connect
        conn = agency_connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM invoices WHERE agency_id=%s AND status='open'", (agency_id,))
            n = cur.fetchone()[0]
            conn.rollback()
            return n == 0
        finally:
            conn.close()
    except Exception:
        return True


# ---- catalog rescue (capture) ---------------------------------------------
def catalog_is_capturable(con, tenant_id):
    row = con.execute("SELECT count(*) AS n FROM seller_skus WHERE tenant_id=?", (tenant_id,)).fetchone()
    return bool(row and (row["n"] or 0) >= _CAPTURE_MIN_SKUS)


def capture_catalog(con, tenant_id):
    """Snapshot a brand's catalog into a reusable sandbox seed (minimal seed + country + REAL brand name,
    per R17 decision 2). Returns the captured_seeds id, or None if there's nothing worth keeping."""
    rows = con.execute(
        "SELECT asin,title,category,cogs,price FROM seller_skus WHERE tenant_id=? ORDER BY asin",
        (tenant_id,)).fetchall()
    if len(rows) < _CAPTURE_MIN_SKUS:
        return None
    catalog = [{"asin": r["asin"], "title": r["title"], "category": r["category"],
                "cogs": r["cogs"], "price": r["price"]} for r in rows]
    t = db.get_tenant(con, tenant_id) or {}
    brand = t.get("name") or f"brand {tenant_id}"
    from . import country as _country
    ctry = _country.tenant_country(tenant_id, con)
    con.execute(
        "INSERT INTO captured_seeds(name,country,brand_name,sku_count,catalog,source_ref,created_at) "
        "VALUES(?,?,?,?,?,?,?)",
        (f"{brand} · {len(catalog)} SKUs", ctry, brand, len(catalog),
         json.dumps(catalog), str(tenant_id), _now()))
    con.commit()
    return True


def list_captured_seeds(con):
    rows = con.execute("SELECT id,name,country,brand_name,sku_count FROM captured_seeds "
                       "ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def captured_seed_catalog(con, seed_id):
    row = con.execute("SELECT country,brand_name,catalog FROM captured_seeds WHERE id=?", (seed_id,)).fetchone()
    if not row:
        return None
    cat = row["catalog"]
    return {"country": row["country"], "brand_name": row["brand_name"],
            "catalog": json.loads(cat) if isinstance(cat, str) else (cat or [])}


# ---- the ONE destructive routine ------------------------------------------
def _crypto_shred(tenant_id):
    """Explicit crypto-shred on the delete path (R17 hardening) — PG-only, best-effort."""
    try:
        from . import dbengine
        if dbengine.dialect() != "postgresql":
            return
        from .agency.db import agency_connect
        from .agency import keyring
        conn = agency_connect()
        try:
            cur = conn.cursor()
            keyring.crypto_shred(cur, tenant_id)
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def _clear_user_ledger_footprint(tenant_id):
    """PG-only, best-effort: before a tenant's users are deleted, remove every ledger row they AUTHORED
    (actor_user) anywhere — this tenant AND any other tenant. ledger.actor_user is a RESTRICT FK (and part
    of the hash chain, so it can't be nulled), so on a hard delete these rows must be removed or the users
    delete 500s (ledger_actor_user_fkey). The tenant's own ledger would cascade on the tenant-row delete,
    but that runs AFTER users are deleted, and under the runtime role (realify_app) the in-repo scoped
    delete can't even see other tenants' rows — so we clear them here with the fleet scope set. NOTE: if
    such a user acted on a SURVIVING tenant, that tenant's chain is truncated at those entries — acceptable
    on a hard account wipe (the actor is gone); the common real case (agency operators) already wipes the
    brands via the agency composite, so this mainly covers stray internal/AM accounts."""
    from . import dbengine
    if dbengine.dialect() != "postgresql":
        return
    try:
        from .agency.db import agency_connect
        from .agency import tenancy
        conn = agency_connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE tenant_id=%s", (tenant_id,))
            uids = [r[0] for r in cur.fetchall()]
            if not uids:
                return
            cur.execute("SELECT id FROM tenants")
            tenancy.set_brand_scope(cur, [r[0] for r in cur.fetchall()])   # fleet scope: see/act on every tenant
            cur.execute("DELETE FROM ledger WHERE actor_user = ANY(%s)", (uids,))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def execute_brand(con, tenant_id, capture_seed=True, deleted_by="ops-console"):
    """Hard-wipe one brand tenant: capture (if flagged) → crypto-shred → wipe rows → Stripe teardown →
    surviving audit row. Idempotent (a re-run on a gone tenant is a no-op)."""
    from .repositories.tenant_repo import TenantRepository
    from .repositories.seller_repo import SellerRepository
    from .repositories.card_repo import CardRepository
    from .repositories.audit_repo import DeletedAccountAuditRepository
    t = db.get_tenant(con, tenant_id)
    if not t:
        return {"ok": True, "already": True}
    if capture_seed:
        try:
            capture_catalog(con, tenant_id)
        except Exception:
            pass
    _crypto_shred(tenant_id)
    name = t.get("name") or ""
    # capture the audit facts BEFORE the wipe (unrecoverable after)
    emails = [m.get("email") for m in (db.list_members(con, tenant_id) or []) if m.get("email")]
    acct = TenantRepository(con).get_account_type(tenant_id)
    skus = SellerRepository(con).count(tenant_id)
    cards = CardRepository(con).count_all(tenant_id)
    _clear_user_ledger_footprint(tenant_id)            # unblock: drop ledger rows this tenant's users authored elsewhere
    TenantRepository(con).delete(tenant_id)            # wipe + PG cascade (engagements/grants/ledger/keys) + on_tenant_deleted
    try:
        billing.cancel_and_delete_customer(t)          # Stripe teardown (best-effort)
    except Exception:
        pass
    try:
        DeletedAccountAuditRepository(con).record(
            deleted_tenant_id=tenant_id, tenant_name=name, account_type=acct,
            emails=", ".join(emails), member_count=len(emails), sku_count=skus,
            card_count=cards, deleted_by=deleted_by)
        con.commit()
    except Exception:
        pass
    return {"ok": True, "name": name}


def execute_user(con, user_id, deleted_by="ops-console"):
    """Sole owner of a brand ⇒ escalate to the whole brand's wipe. Otherwise ⇒ leave (delete the user
    row; agency_members/grants cascade from the user on Postgres). Never orphans a brand with no owner."""
    u = db.get_user_by_id(con, user_id)
    if not u:
        return {"ok": True, "already": True}
    tid = u.get("tenant_id")
    if tid and db.count_members(con, tid) <= 1:
        return execute_brand(con, tid, deleted_by=deleted_by)
    db.delete_user(con, user_id)
    con.commit()
    return {"ok": True, "left": True}


def execute_agency(con, agency_id, deleted_by="ops-console"):
    """Composite (R17 decision 4): wipe every managed brand (each cascades its engagements/grants/ledger),
    THEN delete the agency row (cascades members). No detach — a brand that wants to continue re-onboards.
    Postgres-only. Enumerates brands via the fleet pattern (scope to all tenants, then read engagements)."""
    from . import dbengine
    if dbengine.dialect() != "postgresql":
        return {"ok": False, "error": "agency delete is Postgres-only"}
    from .agency.db import agency_connect
    from .agency import tenancy
    aconn = agency_connect()
    try:
        acur = aconn.cursor()
        acur.execute("SELECT id FROM tenants")
        ids = [r[0] for r in acur.fetchall()]
        if ids:
            tenancy.set_brand_scope(acur, ids)          # fleet pattern: engagements are brand-scoped RLS
        acur.execute("SELECT tenant_id FROM engagements WHERE agency_id=%s AND status<>'terminated'",
                     (agency_id,))
        brand_ids = [r[0] for r in acur.fetchall()]
        aconn.rollback()
    finally:
        aconn.close()
    for tid in brand_ids:
        execute_brand(con, tid, capture_seed=True, deleted_by=deleted_by)   # each cascades its agency rows
    # the inbound application record (agency_requests) references agencies WITHOUT a cascade — remove it
    # first, else DELETE FROM agencies 500s on agency_requests_agency_id_fkey.
    con.execute("DELETE FROM agency_requests WHERE agency_id=?", (agency_id,))
    con.execute("DELETE FROM agencies WHERE id=?", (agency_id,))            # cascades members/invites/etc.
    con.commit()
    return {"ok": True, "brands": len(brand_ids)}


def execute_agency_workspace(con, tenant_id, deleted_by="ops-console"):
    """Delete an agency via its WORKSPACE tenant (the ops tenant-delete path lands here for a
    tenant_kind='agency_workspace'). Wipe every managed brand FIRST — each brand's tenant-row delete
    CASCADES its hash-chained ledger, removing the rows whose actor_user points at the agency's owner —
    then delete the agencies row(s) the workspace owners administer, then wipe the workspace tenant + its
    users. Ordering is load-bearing: ledger.actor_user is RESTRICT and part of the chain, so referencing
    rows must be DELETED (never nulled) before the agency user is removed — otherwise deleting the owner
    500s on ledger_actor_user_fkey (the bug this fixes). Postgres-only for the agency step; a workspace
    with no agency simply degrades to a plain tenant wipe."""
    from . import dbengine
    agency_ids = []
    if dbengine.dialect() == "postgresql":
        from realify.agency.db import agency_connect
        aconn = agency_connect()
        try:
            acur = aconn.cursor()
            acur.execute("SELECT DISTINCT agency_id FROM agency_members WHERE user_id IN "
                         "(SELECT id FROM users WHERE tenant_id=%s)", (tenant_id,))
            agency_ids = [r[0] for r in acur.fetchall()]
            aconn.rollback()
        finally:
            aconn.close()
    for aid in agency_ids:
        execute_agency(con, aid, deleted_by=deleted_by)     # wipes its brands (ledger cascades) + agency row
    return execute_brand(con, tenant_id, capture_seed=False, deleted_by=deleted_by)   # then workspace + owner


def execute(con, req, deleted_by="ops-console"):
    """Dispatch a ready/tester request to the right destructive routine."""
    et, ref = req["entity_type"], req["entity_ref"]
    if et == "brand":
        return execute_brand(con, int(ref), capture_seed=bool(req.get("capture_seed", True)), deleted_by=deleted_by)
    if et == "user":
        return execute_user(con, int(ref), deleted_by=deleted_by)
    if et == "agency":
        return execute_agency(con, ref, deleted_by=deleted_by)
    return {"ok": False, "error": f"unknown entity_type {et}"}
