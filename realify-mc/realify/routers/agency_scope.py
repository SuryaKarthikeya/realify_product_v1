"""R11 Part C — the scope-switcher drill-in route (mockup h8). GET /agency/brand/{tenant_id}: the agency
operator drills into ONE brand. Authz is engagement-based (the actor's agency must hold an active
engagement on the brand — grant-independent). Sets the session to scope the real seller app to this
brand, reads the brand's ACTIVE envelope (so the locked lens + suggest-only acts are envelope-driven),
and renders the h8 operate surface with the per-brand decisions panel."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from ..agency import toctou, tenancy, fleet_data, db as agency_db
from ..agency.actor import resolve_actor
from ..agency.guard import require_agency_console
from ..pdp import ENVELOPES
from .deps import current
from realify.site.tokens import state_page as _state_page

router = APIRouter()

# R15 Part 0 — the real app's five lenses (as named in the seller SPA) → the PDP lens whose envelope
# cap governs them. Drives read-only lens marking + in-lens Approve/Propose gating in the real app.
_UX_TO_PDP = {"Product Catalog": "listings", "Profit & Ads": "ads", "Intelligence": "reporting",
              "Category Analyst": "reporting", "Channels": "pricing"}


def _envelope_name(caps):
    """Friendly name for a caps dict — match it to a known ENVELOPES template, else 'Custom'."""
    for name, spec in ENVELOPES.items():
        if {l: dict(c) for l, c in spec.items()} == {l: dict(c) for l, c in (caps or {}).items()}:
            return name
    return "Custom"


@router.get("/agency/brand/{tenant_id}", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console)])
def brand_scope(tenant_id: int, request: Request):
    uid, tid = current(request)
    if not uid:
        return HTMLResponse(_state_page("Agency sign-in required",
                                        "This surface needs an agency session.", "Restricted"), status_code=401)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        ctx = resolve_actor(cur, uid)
        agency_id, agency_name = fleet_data.resolve_agency(cur, uid, tid, list(ctx.agency_ids))
        if agency_id is None:
            conn.rollback()
            return HTMLResponse(_state_page("No agency in scope",
                                            "Impersonate an agency operator from the hub first.", "Restricted"),
                                status_code=200)
        all_ids = fleet_data.agency_brand_ids(cur, agency_id)
        if tenant_id not in all_ids:                     # engagement-based authz (grant-independent)
            conn.rollback()
            return HTMLResponse(_state_page("Not in your book",
                                            "This brand is not one of your agency's accounts.", "Restricted"),
                                status_code=403)
        tenancy.set_brand_scope(cur, [tenant_id])
        cur.execute("SELECT name, tenant_kind FROM tenants WHERE id=%s", (tenant_id,))
        r = cur.fetchone(); brand = r[0] if r else f"brand {tenant_id}"
        is_sandbox = bool(r and r[1] in ("sandbox", "internal"))   # gate the seller-access grant below
        cur.execute("SELECT id FROM engagements WHERE tenant_id=%s AND status='active' LIMIT 1", (tenant_id,))
        er = cur.fetchone()
        caps = {}
        if er:
            _, caps = toctou.current_envelope(cur, er[0])
        env_name = _envelope_name(caps)
        conn.rollback()
    finally:
        conn.close()
    # R15 Part 0 — DRILL-IN UNIFICATION: the fleet "Open brand →" no longer renders a bespoke wrapper.
    # It scope-switches the operator INTO the real five-lens seller app (served at /), bounded by this
    # brand's envelope. The envelope caps ride in the session so the real app gates in-lens Approve
    # (execute-capable lens) vs Propose-to-brand (suggest-only / locked lens) — decisions live inside
    # the lenses, not a separate flat list. Grant sandbox seller access so / renders the real app for
    # this managed brand (SANDBOX/internal only — never fake a tester billing state on a real brand).
    if is_sandbox:
        try:
            from .agency_sandbox import _grant_seller_access
            _grant_seller_access(tenant_id)
        except Exception:
            pass
    request.session["tid"] = tenant_id
    request.session["acting_as"] = {"role": "Agency operator", "tenant": brand, "via": agency_name,
                                    "scope": "account"}
    request.session["agency_envelope"] = {"caps": {l: dict(c) for l, c in (caps or {}).items()},
                                          "env": env_name, "agency": agency_name, "brand": brand,
                                          "tenant_id": tenant_id}
    return RedirectResponse("/", status_code=303)


@router.get("/api/scope")
def api_scope(request: Request):
    """R15 Part 0/I — expose the agency-scoped drill-in context to the real five-lens app: the operating
    identity (agency › brand) for the header, and per-PDP-lens envelope caps so the client renders
    Approve (execute) vs 'Propose to brand →' (suggest-only) and marks read-only lenses. Null for a
    direct/owner session (full powers, no envelope bound)."""
    try:
        env = request.session.get("agency_envelope")
    except Exception:
        env = None
    if not env:
        return JSONResponse({"agency_scope": None})
    caps = env.get("caps") or {}
    return JSONResponse({"agency_scope": {
        "agency": env.get("agency"), "brand": env.get("brand"), "envelope": env.get("env"),
        "tenant_id": env.get("tenant_id"),
        "caps": {l: (c or {}).get("max_kind", "read") for l, c in caps.items()},
        "lens_caps": {ux: (caps.get(pdp) or {}).get("max_kind", "read")
                      for ux, pdp in _UX_TO_PDP.items()}}})
