"""Shared non-route helpers for the API routers.

BASE_DIR is the repository root (this file is realify/api/helpers.py, so three dirnames up), used
to load the served HTML shells and docs/ regardless of which module imports it.
"""
import os
from realify import db
from realify.repositories.pull_repo import PullLogRepository
from .deps import current

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def page(name):
    return open(os.path.join(BASE_DIR, name), encoding="utf-8").read()


def _track(request, event, **kw):
    """Best-effort server-side funnel emit, attributed from the session."""
    try:
        uid, tid = current(request)
        from realify import analytics
        analytics.record(tid, uid, event, **kw)
    except Exception:
        pass


def _log_import(con, tenant_id, scope, filename, applied=0, rejects=None):
    """Record an import result (COGS / report) in pull_log so the Log tab can show it,
    including rejected rows with reasons. status: ok | partial | rejected."""
    import json as _j
    rejects = rejects or []
    status = "ok" if not rejects else ("partial" if applied else "rejected")
    note = filename + (("  |  rejects: " + _j.dumps(rejects[:50])) if rejects else "")
    try:
        PullLogRepository(con).log_import(tenant_id, "import", scope, db.now_iso(), db.now_iso(), status, applied, note)
        con.commit()
    except Exception:
        pass


def _is_customer(tid):
    con = db.connect()
    try:
        return db.get_account_type(con, tid) == "customer"
    finally:
        con.close()


def _is_seller(tid):
    """Customer OR tester — both own a seller catalog and may upload/replace real reports + COGS through
    the same recognizer + full pipeline (full parity, per Shiva). A tester uploading real reports gets
    real 'uploaded' data via the same path; account_type is left unchanged. Non-seller accounts (e.g. an
    agency workspace) are excluded."""
    con = db.connect()
    try:
        return db.get_account_type(con, tid) in ("customer", "tester")
    finally:
        con.close()


def agency_caps(request):
    """R15 Part 0 — the acting agency operator's per-PDP-lens envelope caps (lens → max_kind), or None
    for a direct owner / real-customer session (no envelope bound → full owner powers). Used to gate
    in-lens execute vs propose in the real five-lens app when an agency has drilled into a brand."""
    try:
        env = request.session.get("agency_envelope")
    except Exception:
        return None
    if not env:
        return None
    return {l: (c or {}).get("max_kind", "read") for l, c in (env.get("caps") or {}).items()}


def ads_preview_allowed(tid):
    """ALLOWLIST gate for the HELD ads model's internal preview. Fails CLOSED. Both must hold:
      1. the `ads_preview` operator flag is on, AND
      2. account_type == 'tester'.

    Deliberately NOT the usual tester test (`account_type=='tester' OR tenant_kind in
    {internal,sandbox}`): the DEMO tenant 12 carries tenant_kind='internal', so that form is TRUE for
    the account we demo with and would show unvalidated ad numbers to an audience. account_type is the
    safe boundary — tenant 12 is a `customer`.

    Single source of truth: the API gate (routers/intelligence.run_model) and the UI capability flag
    (/api/me features.ads_preview) both call this, so they cannot disagree.

    Two independent ways in, both explicit:
      * a PER-TENANT grant (`reg.ads_preview.gate='on'` on that tenant) - surgical: it unlocks this
        one inspector for one account and nothing else. No account_type change, so no Tester-tools
        tab and no destructive-op surface rides along. This is how tenant 12 (aatish) gets access
        without turning the demo account into a tester.
      * the GLOBAL flag + account_type=='tester' - the fleet-wide internal path.
    """
    try:
        from realify import flags
        if (flags._get(tid, "reg.ads_preview.gate") or "").lower() == "on":
            return True                                  # explicit per-tenant grant
        if (flags._get(0, "reg.ads_preview.gate") or "").lower() != "on":
            return False                                 # global flag off -> nobody else
        con = db.connect()
        try:
            return db.get_account_type(con, tid) == "tester"
        finally:
            con.close()
    except Exception:
        return False


def _synth_ops_allowed(tid):
    """ALLOWLIST gate for destructive synthetic-data ops (resynthesize). Fail CLOSED — permit ONLY when
    data_mode=='synthetic' AND (account_type=='tester' OR tenant_kind in {internal,sandbox}) AND the
    account is not a CUSTOMER.

    That last clause is the fix for a real near-miss. The original formula permitted
    `account_type='customer'` whenever tenant_kind was 'internal' — which is exactly the demo tenant 12,
    holding 690 REAL Autofy orders, 691 real ad-days and 44 real SKUs. Its data_mode was still the stale
    'synthetic' from before real reports were promoted, so Resynthesize was ARMED on real production
    data, and `scheduler.resynthesize(mode='full')` regenerates economics from the catalog.

    account_type is the safe boundary here for the SAME reason ads_preview_allowed already uses it:
    tenant_kind='internal' is TRUE for the account we demo with. Two independent things now have to be
    wrong before real data can be overwritten, instead of one."""
    con = db.connect()
    try:
        t = db.get_tenant(con, tid) or {}
        at = db.get_account_type(con, tid)
    finally:
        con.close()
    if t.get("data_mode") != "synthetic":
        return False
    if at == "customer":                    # never on a paying/real-data account, whatever its kind
        return False
    return at == "tester" or t.get("tenant_kind") in ("internal", "sandbox")
