"""Portfolio console + work queue routes (agency-plan P4, mockup screens 18-19) — behind
AGENCY_CONSOLE, Postgres-only. Grant-scoped: the actor's allowed brand set is resolved on a trusted
bootstrap connection (row_security off, its own transaction), then all data queries run RLS-scoped to
exactly that set. Brands with an expired connection are shown paused (P3)."""
import html

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from ..agency import (queue, rollups, connections, money, approvals, execution, toctou, tenancy,
                      mock_marketplace, fleet_data, policy, db as agency_db)
from ..agency.actor import resolve_actor
from ..agency.guard import require_agency_console
from ..pdp import Action
from .deps import current
from realify.site.busy_modal import SNIPPET as _BUSY_MODAL
from realify.site import backbar as _backbar
from realify.site import fleet as _fleet
from realify.site.tokens import state_page as _state_page   # (R11) fixes prior NameError in the 401 path

router = APIRouter()
_PILOT_CAP = 10

async def _qbody(request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


def _email_cosign_link(cur, approval_id, tenant_id):
    """On cosign_pending, issue a (approval,brand-user)-bound deep link and email it to the brand — the
    'nothing happens without you' step. Best-effort; a mail hiccup must not fail the action."""
    from .. import mail, config
    from ..agency import mailcfg
    cur.execute("SELECT id, email FROM users WHERE tenant_id=%s ORDER BY id LIMIT 1", (tenant_id,))
    row = cur.fetchone()
    if not row:
        return
    brand_uid, brand_email = row
    token = approvals.create_deeplink(cur, approval_id, brand_uid)
    base = (config.APP_URL or "https://realifyai.app").rstrip("/")
    link = f"{base}/agency/approve/{approval_id}?token={token}&uid={brand_uid}"
    mail.send(brand_email, "A change needs your co-sign",
              f"Your agency proposed a change that needs your approval. Review and co-sign (or do "
              f"nothing — it expires in 5 days and never executes without you):\n{link}",
              from_addr=mailcfg.from_addr(), reply_to=mailcfg.reply_to())


def _actor(uid):
    conn = agency_db.agency_connect()
    try:
        ctx = resolve_actor(conn.cursor(), uid)
        conn.rollback()
        return list(ctx.allowed_tenant_ids), list(ctx.agency_ids)
    finally:
        conn.close()


def _allowed(uid):
    """Actor's allowed brand ids via the trusted resolver (own connection/txn; row_security off does
    NOT leak into the scoped query connection below)."""
    conn = agency_db.agency_connect()
    try:
        ctx = resolve_actor(conn.cursor(), uid)
        conn.rollback()
        return list(ctx.allowed_tenant_ids)
    finally:
        conn.close()


def _uid_or_401(request):
    uid, _ = current(request)
    return uid


def _permitted_brand(uid, tid, tenant_id):
    """May the actor act on this brand? True if it's in their grants OR in their agency's engagements —
    so an agency operator drilled into a brand (scope-switcher) can act, not only per-brand grant holders.
    Envelope⊗grant limits still apply downstream (toctou); this is only brand-scope authz (R11)."""
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        ctx = resolve_actor(cur, uid)
        if tenant_id in ctx.allowed_tenant_ids:
            conn.rollback(); return True
        agency_id, _ = fleet_data.resolve_agency(cur, uid, tid, list(ctx.agency_ids))
        ok = agency_id is not None and tenant_id in fleet_data.agency_brand_ids(cur, agency_id)
        conn.rollback(); return ok
    finally:
        conn.close()


@router.get("/api/agency/queue", dependencies=[Depends(require_agency_console)])
def api_queue(request: Request, top_k: int = 50):
    uid = _uid_or_401(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    allowed = _allowed(uid)
    conn = agency_db.agency_connect()
    try:
        items = queue.build(conn.cursor(), allowed, top_k=top_k)
    finally:
        conn.close()
    return JSONResponse({"ok": True, "count": len(items), "items": items})


def _console(uid):
    allowed = _allowed(uid)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        port = rollups.portfolio(cur, allowed)
        brands = rollups.per_brand(cur, allowed)
        for b in brands:
            b["paused"] = connections.decisions_paused(cur, b["tenant_id"])   # expired connection -> paused
    finally:
        conn.close()
    return allowed, port, brands


@router.get("/api/agency/console", dependencies=[Depends(require_agency_console)])
def api_console(request: Request):
    uid = _uid_or_401(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    _, port, brands = _console(uid)
    return JSONResponse({"ok": True,
                         "portfolio": {**port,
                                       "gmv_display": money.format_money(port["gmv_usd_minor"], "USD"),
                                       "margin_display": money.format_money(port["margin_usd_minor"], "USD")},
                         "brands": brands})


def _add_client_panel(agency_id, agency_name, pending, self_approve=True):
    """h5 Add-client panel: consent invite form + pending-consent rows. When the platform
    `agency_self_approve` switch is ON, each pending row carries an 'Approve on brand's behalf' button
    (POST /api/agencies/consent/{id}/self-approve — impersonates the brand's consent click, any tenant).
    When OFF, the row shows 'awaiting brand approval' instead (the brand approves via the OTP flow)."""
    aid = html.escape(str(agency_id or ""))
    an = html.escape(agency_name or "Your agency")
    _approve_btn = (lambda p: f"<button class='btn dark sm ac-approve' data-cid={p['id']}>✓ Approve on brand's behalf</button>") \
        if self_approve else (lambda p: "<span class=note-s>awaiting brand approval</span>")
    rows = "".join(
        f"<div class=seedrow><span><b>{html.escape(p['email'])}</b>"
        f"<div class=meta>{html.escape(p['template'])} · {html.escape(p['status'])} · ✉ email sent</div></span>"
        f"{_approve_btn(p)}"
        "</div>" for p in pending) or "<p class=note-s>No pending consents.</p>"
    st_note = "self-approve ON" if self_approve else "brand approval required"
    return (
        "<div class='step done' style='margin-top:20px'>"
        "<div class=step-h><span class=step-n>+</span><h3>Add a client</h3>"
        f"<span class=st-note>{st_note}</span></div><div class=step-body>"
        "<div class=cols2>"
        "<div class=field><label>Brand name</label><input id=acBrand placeholder='e.g. Acme Coffee Co.'></div>"
        "<div class=field><label>Brand owner email</label><input id=acEmail type=email placeholder='owner@brand.com'></div>"
        "</div>"
        "<div class=cols2>"
        "<div class=field><label>Market</label><select id=acCountry>"
        "<option value=US>United States (USD)</option><option value=IN>India (INR)</option></select></div>"
        "<div class=field><label>Access requested</label><select id=acTmpl>"
        "<option>Operate ex-Pricing</option><option>Full Operate</option><option>Ads Only</option>"
        "<option>Advise</option><option>Read-only</option></select></div></div>"
        "<button class='btn p' id=btnInvite>Send consent request →</button>"
        f"<div style='margin-top:16px'>{rows}</div>"
        f"<input type=hidden id=acAgency value='{aid}'><input type=hidden id=acAgencyName value='{an}'>"
        "</div></div>"
        "<script>"
        "function _p(u,b){return fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b||{})});}"
        "var bi=document.getElementById('btnInvite');if(bi)bi.addEventListener('click',function(){"
        "_p('/api/agencies/consent/invite',{agency_id:acAgency.value,brand_name:acBrand.value,"
        "email:acEmail.value,template:acTmpl.value,country:acCountry.value,agency_name:acAgencyName.value})"
        ".then(function(r){return r.json();}).then(function(d){if(d.ok)location.reload();else alert(d.error||'Failed');});});"
        "document.querySelectorAll('.ac-approve').forEach(function(b){b.addEventListener('click',function(){"
        "_p('/api/agencies/consent/'+b.dataset.cid+'/self-approve',{}).then(function(r){return r.json();})"
        # on approve, go straight to onboarding the brand (connect its data), not back to the fleet
        ".then(function(d){if(d.ok)location.href=(d.redirect||'/agency/console');else alert(d.error||'Could not approve');});});});"
        "</script>")


@router.get("/agency/console", response_class=HTMLResponse, dependencies=[Depends(require_agency_console)])
def console_page(request: Request):
    """R11 Part B: the FLEET GRID (mockup h7) — the agency's triage home. Brands resolved from
    engagements (grant-independent — fixes the '0 clients' bug), each card carrying health, top signal/
    action, and the load-bearing $-at-stake; sorted by it. My-book vs All-accounts filter + Add-client."""
    uid, tid = current(request)
    if not uid:
        return HTMLResponse(_state_page("Agency sign-in required",
                                        "This surface needs an agency session.", "Restricted"), status_code=401)
    book_mode = "all" if request.query_params.get("book") == "all" else "mine"
    # Ensure a synthesized SAMPLE brand sits in this (real) agency's fleet so they can see a populated
    # brand before onboarding real data. Own committed txn — the fleet read below rolls back. Best-effort.
    try:
        dconn = agency_db.agency_connect()
        try:
            dcur = dconn.cursor()
            _ctx = resolve_actor(dcur, uid)                              # sets the actor GUC for RLS
            _aid, _ = fleet_data.resolve_agency(dcur, uid, tid, list(_ctx.agency_ids))
            _demo_res = None
            if _aid is not None:
                from ..agency import demo as _demo
                _demo_res = _demo.ensure_demo_brand(dcur, _aid)
                dconn.commit()
            else:
                dconn.rollback()
        finally:
            dconn.close()
        # populate the demo brand's OTHER lenses (Profit&Ads, ad-graph→ƒ, Channels, Intelligence cards)
        # AFTER the seed commits — finalize_world opens its own connections and can't see uncommitted rows.
        if _demo_res and _demo_res[1]:
            from ..agency import lens_synth as _lens
            _lens.finalize_world([_demo_res[0]])
    except Exception:
        pass
    conn = agency_db.agency_connect()
    try:
        # ONE transaction: resolve_actor sets the app.actor_user_id GUC (transaction-local) that the
        # engagements/brand_consents RLS actor-selfread policies need — a rollback in between would clear
        # it and RLS would return 0 under realify_app (the R2 lesson; not visible under the owner test role).
        cur = conn.cursor()
        ctx = resolve_actor(cur, uid)
        agency_id, agency_name = fleet_data.resolve_agency(cur, uid, tid, list(ctx.agency_ids))
        if agency_id is None:
            conn.rollback()
            return HTMLResponse(_state_page("No agency in scope",
                                            "Impersonate an agency operator from the hub to see the fleet.",
                                            "Restricted"), status_code=200)
        all_ids = fleet_data.agency_brand_ids(cur, agency_id)
        grant_ids = set(ctx.allowed_tenant_ids)
        mine_ids = sorted(grant_ids & set(all_ids))
        if not mine_ids:                    # operator with no per-brand grant (fresh impersonation) → show all
            book_mode = "all"
        show_ids = all_ids if book_mode == "all" else mine_ids
        cards = fleet_data.brand_cards(cur, show_ids, grant_ids)
        pending = fleet_data.pending_consents(cur, agency_id)
        self_approve = policy.self_approve_on(cur)
        conn.rollback()
    finally:
        conn.close()
    add_panel = _add_client_panel(agency_id, agency_name, pending, self_approve)
    return HTMLResponse(_fleet.fleet_html(request, agency_name, cards, book_mode,
                                          len(mine_ids), len(all_ids), add_form_html=add_panel))


@router.post("/api/agency/queue/propose", dependencies=[Depends(require_agency_console)])
async def queue_propose(request: Request):
    """Act on a queue item. Co-sign is DERIVED (approvals.cosign_required), not hardcoded. On an
    execute-allowed lens BELOW the maker-checker threshold with no co-sign, the proposing user's Approve
    advances straight to approved and executes (single-item path, mock marketplace). Otherwise it stays
    'proposed' (needs a distinct checker) or 'cosign_pending' (needs the brand). Silence never executes."""
    uid, tid = current(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    b = await _qbody(request)
    tenant_id = int(b.get("tenant_id") or 0)
    if not _permitted_brand(uid, tid, tenant_id):
        return JSONResponse({"ok": False, "error": "not permitted for this brand"}, status_code=403)
    lens, kind, signal = b.get("lens", ""), b.get("kind", ""), b.get("signal", "")
    impact = int(b.get("impact_usd_minor") or 0)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])                  # RLS: scope before brand-table reads
        cur.execute("SELECT id FROM engagements WHERE tenant_id=%s AND status='active' LIMIT 1", (tenant_id,))
        row = cur.fetchone()
        if not row:
            return JSONResponse({"ok": False, "error": "no active engagement"}, status_code=400)
        eng = row[0]
        version, caps = toctou.current_envelope(cur, eng)
        maxk = (caps or {}).get(lens, {}).get("max_kind", "propose")
        requires_cosign = approvals.cosign_required(cur, eng, lens, kind, impact)
        aid = approvals.propose(cur, tenant_id, eng, uid, lens, kind, signal, impact,
                                requires_cosign=requires_cosign, envelope_version=version)
        status, executed = "proposed", False
        if maxk == "execute" and impact < approvals._threshold(cur, eng):
            status = approvals.approve(cur, aid, uid)["status"]        # 'approved' or 'cosign_pending'
            if status == "approved":
                res = execution.execute_approval(cur, mock_marketplace.get_mock(), aid)
                executed = bool(res["executed"])
                status = "executed" if executed else "approved"
            elif status == "cosign_pending":
                try:
                    _email_cosign_link(cur, aid, tenant_id)            # deliver the brand co-sign deep link
                except Exception as e:                                 # pragma: no cover - defensive
                    print(f"[queue] cosign email failed for approval {aid}: {e}", flush=True)
        conn.commit()
        return JSONResponse({"ok": True, "approval_id": aid, "status": status, "executed": executed})
    except approvals.ApprovalError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=409)
    finally:
        conn.close()


@router.post("/api/agency/queue/dismiss", dependencies=[Depends(require_agency_console)])
async def queue_dismiss(request: Request):
    """Dismiss a queue item with a reason — feeds the existing dismissal-reason store
    (executions.excluded_reason, read by quality.dismissal_reasons)."""
    uid, tid = current(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    b = await _qbody(request)
    tenant_id = int(b.get("tenant_id") or 0)
    if not _permitted_brand(uid, tid, tenant_id):
        return JSONResponse({"ok": False, "error": "not permitted for this brand"}, status_code=403)
    reason = (b.get("reason") or "dismissed").strip()
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])
        cur.execute("INSERT INTO executions(tenant_id,approval_id,account,idempotency_key,status,"
                    "excluded_reason) VALUES(%s,NULL,'queue',%s,'excluded',%s) "
                    "ON CONFLICT (idempotency_key) DO UPDATE SET excluded_reason=EXCLUDED.excluded_reason",
                    (tenant_id, f"dismiss:{tenant_id}:{b.get('signal','')}", reason))
        conn.commit()
        return JSONResponse({"ok": True, "dismissed": True, "reason": reason})
    finally:
        conn.close()
