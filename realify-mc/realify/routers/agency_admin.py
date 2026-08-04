"""Internal admin + quality console + hardened superlogin authenticate (agency-plan P7). Admin surfaces
are behind AGENCY_CONSOLE + the admin key. Superlogin authenticate is the hardened flow (admin key +
@realify.ai + OTP -> 8h ledgered session cookie)."""
import datetime
import html

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from .. import db, superlogin, lifecycle
from ..agency import gates, quality, internal, money, policy, db as agency_db
from ..agency.actor import resolve_actor
from ..agency.guard import require_agency_console
from .deps import require_admin, current
from realify.site import backbar as _backbar

router = APIRouter()


def _admin(request: Request):
    """Staff gate for the ops admin surfaces: the admin key OR a valid superlogin session (the R6
    'Realify Admin' persona doorway lands here from the hub carrying only the 8h superlogin cookie —
    itself a hardened staff gate: key + @realify.ai + OTP + lockout + ledger). Fail-closed otherwise."""
    if superlogin.verify_session(request.cookies.get("superlogin_session") or ""):
        return True
    require_admin(request)
    return True


def _allowed(uid):
    conn = agency_db.agency_connect()
    try:
        ctx = resolve_actor(conn.cursor(), uid)
        conn.rollback()
        return list(ctx.allowed_tenant_ids), ctx.agency_ids
    finally:
        conn.close()


async def _body(request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


# ---- internal admin (screens 25-26) ----
_ADMIN_CSS = (
    # R11 reskin -> warm design system (tokens palette + Georgia headings + terracotta), layout unchanged
    ":root{--muted:#6B6459;--line:#E1D9CB;--sage:#7A9E7E;--amber:#B98A2E;--alert:#B3402E;--slate:#5B7B94;--terra:#C4785B}"
    "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,sans-serif;max-width:1000px;margin:0 auto;"
    "padding:24px;background:#F7F4EE;color:#1A1A1A}h1{font-family:Georgia,'Times New Roman',serif;font-size:24px;"
    "font-weight:700;margin:0 0 2px}h3{font-family:Georgia,serif;font-size:16px;margin:22px 0 8px}a{color:var(--terra)}"
    ".toolbar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}"
    ".kpis{display:flex;gap:12px;margin:14px 0}.kpi{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 16px}"
    ".kpi .v{font-family:ui-monospace,Menlo,monospace;font-size:22px;font-weight:600}.kpi .k{font-size:11px;color:var(--muted)}"
    "table{border-collapse:collapse;width:100%;background:#fff}th,td{border:1px solid #EFEAE0;padding:8px 11px;font-size:13px;text-align:left}"
    "th{font:600 10.5px/1 ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}"
    ".meter{height:7px;border-radius:100px;background:#EDE7DA;overflow:hidden;min-width:70px;display:inline-block;width:80px;vertical-align:middle}"
    ".meter i{display:block;height:100%;border-radius:100px;background:var(--sage)}.meter.warn i{background:var(--amber)}.meter.bad i{background:var(--alert)}"
    ".pass{color:#4E7A52;font-weight:600}.fail{color:var(--alert);font-weight:600}.wait{color:#8A7A55;font-weight:600}"
    ".panelbox{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-top:14px}"
    ".empty{background:#F3EFE5;border:1px dashed var(--slate);border-radius:10px;padding:14px 16px;color:#3E566A;font-size:13.5px}"
    ".gate{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #EFEAE0;font-size:13px}"
    ".gate:last-child{border-bottom:none}.btn{border:1px solid var(--line);background:#fff;border-radius:8px;padding:7px 13px;cursor:pointer;font-size:12.5px}"
    "input,select{border:1px solid var(--line);border-radius:8px;padding:7px 10px;font-size:13px;background:#fff}"
    "a{color:var(--slate)}")


@router.get("/ops/agency/admin", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console), Depends(_admin)])
def admin_page(request: Request):
    include_internal = (request.query_params.get("internal") in ("1", "true", "on"))
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        rows = internal.fleet_rows(cur, include_internal=include_internal)
        billable = internal.count_billable_tenants(cur)
        revenue = internal.count_revenue_accounts(cur)
        cur.execute("SELECT gate_key, provenance, status FROM gates ORDER BY gate_key, id DESC")
        gate_rows = cur.fetchall()
        self_approve = policy.self_approve_on(cur)
        # R16 — the real inbound agency-application review queue, surfaced HERE (was only at the unlinked
        # /ops/agencies): open applications operators can approve→provision or reject, in the console they check.
        cur.execute("SELECT ref,agency_name,contact_name,contact_email,am_headcount,status FROM "
                    "agency_requests WHERE status IN ('received','provisioning') ORDER BY created_at DESC")
        pending = cur.fetchall()
    finally:
        conn.close()
    # R17 — the deletion close-out queue (deletion_requests live on the shared RDS; read via db.connect()).
    dcon = db.connect()
    try:
        dels = lifecycle.list_pending(dcon)
    finally:
        dcon.close()
    g = internal.LEVERAGE_GATE

    def meter(r):
        if not r["ams"]:
            return "<span class=wait>no AMs</span>"
        pct = max(6, min(100, int(r["leverage"] / g * 100)))
        cls = "" if r["leverage"] >= g else ("warn" if r["leverage"] >= g * 0.66 else "bad")
        col = "#4E7A52" if r["leverage"] >= g else "var(--alert)"
        return (f"<span class='meter {cls}'><i style='width:{pct}%'></i></span> "
                f"<span style='color:{col};font-weight:600'>{r['leverage']}×</span> / {g}×")
    frows = "".join(
        f"<tr>"
        f"<td><b>{html.escape(r['name'])}</b></td><td>{r['accounts']}</td><td>{r['ams']}</td><td>{meter(r)}</td>"
        f"<td>{r['used']}/{r['pool']}</td><td>{r['acceptance']}%</td>"
        f"<td>{money.format_money(r['mrr_usd_minor'],'USD')}</td></tr>" for r in rows)
    if not frows:
        frows = ("<tr><td colspan=7><div class=empty>No real agencies yet — this is expected during the "
                 "pilot. Verification &amp; sandbox agencies are hidden; use the toggle to reveal them."
                 "</div></td></tr>")
    attention = "".join(
        f"<div class=gate><span>🟠 <b>{html.escape(r['name'])}</b> — leverage {r['leverage']}× below the "
        f"{g}× gate</span></div>" for r in rows if r["needs_attention"]) \
        or "<div class=gate><span>None — all shown agencies are within the leverage gate.</span></div>"
    grows = "".join(
        f"<div class=gate><span><b>{html.escape(gk)}</b> <span class=note>· {html.escape(prov)}</span></span>"
        f"<span class={'pass' if st == 'active' else ('fail' if st != 'attested' else 'pass')}>"
        f"{'PASS' if st in ('active', 'attested') else html.escape(st.upper())}</span></div>"
        for gk, prov, st in gate_rows) or "<div class=gate><span>No gates set yet.</span></div>"
    _ab = "border:none;border-radius:8px;padding:7px 12px;font-weight:600;cursor:pointer"
    preq_rows = "".join(
        f"<tr><td><b>{html.escape(r[1])}</b></td><td>{html.escape(r[2] or '—')}</td>"
        f"<td>{html.escape(r[3] or '')}</td><td>{html.escape(str(r[4]) if r[4] is not None else '—')}</td>"
        f"<td>{html.escape(r[5])}</td><td style='white-space:nowrap'>"
        f"<button data-approve='{html.escape(r[0])}' style='background:#C4785B;color:#fff;{_ab}'>Approve → provision</button>"
        f"<input data-reason='{html.escape(r[0])}' placeholder='reason' style='width:96px;margin:0 6px;padding:6px'>"
        f"<button data-reject='{html.escape(r[0])}' style='background:#fff;color:#1A1A1A;border:1px solid #E4DDD0;border-radius:8px;padding:7px 12px;cursor:pointer'>Reject</button>"
        f"</td></tr>" for r in pending) or \
        "<tr><td colspan=6><div class=empty>No pending applications — real requests from /agencies appear here.</div></td></tr>"
    preq_section = (
        "<h3>Pending agency requests</h3>"
        "<div class=note style='color:#6B6459;font-size:12px;margin:2px 0 6px'>Real inbound applications from "
        "the /agencies form — Approve provisions the agency (tenant + owner grant); Reject drops it with a reason.</div>"
        "<table><tr><th>agency</th><th>contact</th><th>email</th><th>AMs</th><th>status</th><th>actions</th></tr>"
        f"{preq_rows}</table>")
    preq_js = (
        "<script>"
        "document.querySelectorAll('[data-approve]').forEach(function(b){b.onclick=function(){b.disabled=true;"
        "b.textContent='Provisioning…';fetch('/api/ops/agencies/'+b.dataset.approve+'/approve',{method:'POST',"
        "headers:{'content-type':'application/json'},body:'{}'}).then(function(){location.reload();});};});"
        "document.querySelectorAll('[data-reject]').forEach(function(b){b.onclick=function(){var rs="
        "document.querySelector('[data-reason=\"'+b.dataset.reject+'\"]');fetch('/api/ops/agencies/'+b.dataset.reject"
        "+'/decline',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({reason:(rs&&rs.value)||''})})"
        ".then(function(){location.reload();});};});"
        "</script>")
    # R17 — deletion close-out queue section
    _settled_pill = "<span style='color:#4E7A52;font-weight:600'>settled</span>"
    _hold_pill = "<span style='color:#B0821F;font-weight:600'>hold</span>"
    dq_rows = "".join(
        f"<tr><td><b>{html.escape(d.get('label') or (d['entity_type'] + ' ' + str(d['entity_ref'])))}</b></td>"
        f"<td>{html.escape(d.get('account_type') or d['entity_type'])}</td>"
        f"<td>{_settled_pill if d['billing_settled'] else _hold_pill}</td>"
        f"<td>{'captured' if d['capture_seed'] else '—'}</td>"
        f"<td style='white-space:nowrap'>"
        + ("" if d['billing_settled'] else f"<button data-settle='{d['id']}' style='background:#4E7A52;color:#fff;{_ab}'>Mark paid up</button> ")
        + f"<button data-exec='{d['id']}' style='background:#B3402E;color:#fff;{_ab}'>Execute delete</button> "
        f"<button data-cancel-del='{d['id']}' style='background:#fff;color:#1A1A1A;border:1px solid #E4DDD0;border-radius:8px;padding:7px 12px;cursor:pointer'>Cancel</button>"
        f"</td></tr>" for d in dels) or \
        "<tr><td colspan=5><div class=empty>No accounts pending deletion — requested deletes appear here to close out &amp; wipe.</div></td></tr>"
    dq_section = (
        "<h3>Accounts pending close-out &amp; deletion</h3>"
        "<div class=note style='color:#6B6459;font-size:12px;margin:2px 0 6px'>Mark paid up settles billing "
        "(cancels Stripe / marks invoices paid); Execute is blocked until settled unless you supply an override "
        "reason; Cancel restores the account. Execute is a hard, irreversible wipe.</div>"
        "<table><tr><th>account</th><th>type</th><th>billing</th><th>seed</th><th>actions</th></tr>"
        f"{dq_rows}</table>")
    dq_js = (
        "<script>"
        "function _dp(u,b){return fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b||{})});}"
        "document.querySelectorAll('[data-settle]').forEach(function(b){b.onclick=function(){_dp('/api/ops/deletions/'+b.dataset.settle+'/settle',{}).then(function(){location.reload();});};});"
        "document.querySelectorAll('[data-cancel-del]').forEach(function(b){b.onclick=function(){_dp('/api/ops/deletions/'+b.dataset.cancelDel+'/cancel',{}).then(function(){location.reload();});};});"
        "document.querySelectorAll('[data-exec]').forEach(function(b){b.onclick=function(){var id=b.dataset.exec;"
        "if(!confirm('Permanently delete this account? This cannot be undone.'))return;"
        "_dp('/api/ops/deletions/'+id+'/execute',{}).then(function(r){return r.json();}).then(function(d){"
        "if(d.ok){location.reload();return;}"
        "var reason=prompt('Billing is not settled. Enter an override reason to force-delete:');"
        "if(!reason)return;_dp('/api/ops/deletions/'+id+'/execute',{override_reason:reason}).then(function(){location.reload();});});};});"
        "</script>")
    toggle = ("<a href='/ops/agency/admin'>Hide internal/sandbox</a>" if include_internal
              else "<a href='/ops/agency/admin?internal=1'>Show internal/sandbox</a>")
    rev_line = (f"{revenue}" if revenue else "0 — no paying customers yet (pilot/demo)")
    # R18.1 — platform switch: may agencies impersonate the brand's consent click (self-approve)?
    policy_section = (
        "<h3>Agency policy</h3><div class=panelbox style='margin-top:6px'>"
        "<div class=gate><span><b>Agencies can approve on a brand's behalf</b> "
        "<span class=note>· impersonate the brand's consent click; the brand still gets an email</span></span>"
        f"<span class={'pass' if self_approve else 'fail'}>{'ON' if self_approve else 'OFF'}</span></div>"
        f"<button class=btn id=saToggle data-on='{'1' if self_approve else '0'}' style='margin-top:12px'>"
        f"{'Turn OFF — require brand approval' if self_approve else 'Turn ON — allow self-approve'}</button>"
        "<div class=note style='color:#6B6459;font-size:12px;margin-top:8px'>ON: the agency approves on the "
        "brand&#39;s behalf and the brand gets an FYI email (&quot;using Realify to optimize your margin&quot;). "
        "OFF: the brand must approve via the emailed OTP link.</div></div>")
    policy_js = (
        "<script>var sb=document.getElementById('saToggle');if(sb)sb.onclick=function(){"
        "var want=sb.dataset.on!=='1';sb.disabled=true;"
        "fetch('/api/ops/agency/self-approve',{method:'POST',headers:{'content-type':'application/json'},"
        "body:JSON.stringify({on:want})}).then(function(){location.reload();});};</script>")
    return HTMLResponse(
        "<!doctype html><html lang=en><head><meta charset=utf-8><meta name=robots content='noindex'>"
        "<meta name=viewport content='width=device-width,initial-scale=1'><title>Agencies — fleet</title>"
        f"<style>{_ADMIN_CSS}</style></head><body>" + _backbar.bar(request) +
        "<div class=toolbar><div><h1>Agencies — fleet</h1>"
        "<span class=note style='color:#6B6459;font-size:12.5px'>Internal-ops view · admin key / superlogin"
        "</span></div><span style='font-size:12.5px'>" + toggle + "</span></div>"
        "<div class=kpis>"
        f"<div class=kpi><div class=v>{len(rows)}</div><div class=k>{'all' if include_internal else 'real'} agencies shown</div></div>"
        f"<div class=kpi><div class=v>{billable}</div><div class=k>seller tenants (billable base)</div></div>"
        f"<div class=kpi><div class=v>{rev_line}</div><div class=k>paying accounts (Stripe)</div></div></div>"
        + policy_section + preq_section + dq_section +
        "<h3>Provisioned agencies</h3>"
        "<table><tr><th>agency</th><th>accounts</th><th>AMs</th><th>leverage vs 1.5× gate</th>"
        f"<th>decisions used/pool</th><th>acceptance</th><th>MRR</th></tr>{frows}</table>"
        f"<h3>Needs attention</h3><div class=panelbox style='margin-top:6px'>{attention}</div>"
        f"<h3>Gates</h3><div class=panelbox style='margin-top:6px'>{grows}"
        "<form method=post action=/api/ops/gates/set-auto style='margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center'>"
        "<input name=gate_key placeholder='gate key (e.g. detector.acos)' required style='flex:1;min-width:200px'>"
        "<select name=scope><option value=platform>platform</option><option value=agency>agency</option></select>"
        "<button class=btn>Set auto gate (PASS)</button></form></div>"
        "<p class=note style='color:#6B6459;font-size:12px;margin-top:10px'>Auto gates record provenance "
        "'auto'; attested gates carry an evidence link and can't be overwritten by auto.</p>"
        + policy_js + preq_js + dq_js +
        "</body></html>")


@router.post("/api/ops/agency/self-approve", dependencies=[Depends(require_agency_console), Depends(_admin)])
async def set_self_approve(request: Request):
    """Flip the platform `agency_self_approve` switch (may agencies impersonate the brand's consent
    click). Staff-gated (admin key / superlogin)."""
    b = await _body(request)
    on = b.get("on") in (True, "true", "on", 1, "1")
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        state = policy.set_self_approve(cur, on)
        conn.commit()
        return JSONResponse({"ok": True, "on": state})
    finally:
        conn.close()


@router.post("/api/ops/gates/set-auto", dependencies=[Depends(require_agency_console), Depends(_admin)])
async def gates_set_auto(request: Request):
    b = await _body(request)
    if not b.get("gate_key"):
        return JSONResponse({"ok": False, "error": "gate_key required"}, status_code=400)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        gid = gates.set_auto(cur, b["gate_key"], b.get("scope", "platform"), b.get("status", "active"))
        conn.commit()
        return JSONResponse({"ok": True, "gate_id": gid})
    finally:
        conn.close()


@router.post("/api/ops/gates/attest", dependencies=[Depends(require_agency_console), Depends(_admin)])
async def attest(request: Request):
    b = await _body(request)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        vu = b.get("valid_until")
        gid = gates.attest(cur, b.get("gate_key"), b.get("scope", "platform"),
                           b.get("evidence_link"), vu, actor=b.get("actor", "ops"))
        conn.commit()
        return JSONResponse({"ok": True, "gate_id": gid})
    except gates.AttestOverwriteError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=403)   # attested can't overwrite auto
    except ValueError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    finally:
        conn.close()


# ---- quality console (screen 27) ----
@router.get("/ops/agency/quality", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console), Depends(_admin)])
def quality_page(request: Request):
    uid, _ = current(request)
    allowed, _ = _allowed(uid) if uid else ([], ())
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        prec = quality.precision_by_action(cur, allowed)
        dismiss = quality.dismissal_reasons(cur, allowed)
        drift = quality.acceptance_drift(cur, allowed)
    finally:
        conn.close()
    GATE = 7000            # 70% precision gate (bps)
    top = max((v["precision_bps"] for v in prec.values()), default=0)
    below = sum(1 for v in prec.values() if v["proposed"] and v["precision_bps"] < GATE)
    kpis = ("<div style='display:flex;gap:12px;margin:14px 0'>"
            f"<div class=kpi><div class=v>{top/100:.0f}%</div><div>top precision (gate 70%)</div></div>"
            f"<div class=kpi><div class=v>{below}</div><div>action classes BELOW gate</div></div>"
            f"<div class=kpi><div class=v>{sum(dismiss.values())}</div><div>dismissals</div></div></div>")
    prows = "".join(
        f"<tr class={'below' if (v['proposed'] and v['precision_bps'] < GATE) else ''}><td>{html.escape(k)}</td>"
        f"<td>{v['proposed']}</td><td>{v['realized']}</td>"
        f"<td>{v['precision_bps']/100:.0f}%{' · BELOW GATE' if (v['proposed'] and v['precision_bps']<GATE) else ''}</td></tr>"
        for k, v in prec.items()) or "<tr><td colspan=4><i>No proposals yet.</i></td></tr>"
    drows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v['accepted']}/{v['proposed']}</td>"
                    f"<td>{v['acceptance_bps']/100:.0f}%</td></tr>" for k, v in drift.items()) \
        or "<tr><td colspan=3><i>No data.</i></td></tr>"
    dis = "".join(f"<li>{html.escape(str(r))}: {n}</li>" for r, n in dismiss.items()) or "<li>None</li>"
    return HTMLResponse(
        "<!doctype html><html lang=en><head><meta charset=utf-8><meta name=robots content='noindex'>"
        "<meta name=viewport content='width=device-width,initial-scale=1'><title>Recommendation quality</title>"
        f"<style>{_ADMIN_CSS}tr.below td{{background:#F5E7E4;color:#B3402E}}.kpi{{display:inline-block}}</style></head><body>"
        f"<h1>Recommendation quality</h1>{kpis}"
        f"<h3>Precision by action class</h3><table><tr><th>action</th><th>proposed</th><th>realized</th>"
        f"<th>precision</th></tr>{prows}</table>"
        f"<h3>Acceptance drift (executed÷proposed)</h3><table><tr><th>action</th><th>accepted/proposed</th>"
        f"<th>acceptance</th></tr>{drows}</table>"
        f"<h3>Dismissal reasons</h3><ul>{dis}</ul>"
        "<h3>Mitigation (ledgered config change)</h3>"
        "<form method=post action=/api/ops/quality/mitigation>"
        "<input name=gate_key placeholder='e.g. price_up'> "
        "<input name=change placeholder='e.g. suppress below 0.85 confidence'> "
        "<button>Review &amp; Apply</button></form></body>")


@router.post("/api/ops/quality/mitigation", dependencies=[Depends(require_agency_console), Depends(_admin)])
async def quality_mitigation(request: Request):
    uid, _ = current(request)
    _, agencies = _allowed(uid) if uid else ([], ())
    b = await _body(request)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        res = quality.mitigation(cur, agencies[0] if agencies else None,
                                 {"gate_key": b.get("gate_key"), "change": b.get("change")}, actor=uid)
        conn.commit()
        return JSONResponse({"ok": True, **res})
    finally:
        conn.close()


# ---- hardened superlogin authenticate ----
@router.post("/api/superlogin/authenticate", dependencies=[Depends(require_agency_console)])
async def superlogin_authenticate(request: Request):
    b = await _body(request)
    ip = request.client.host if request.client else "?"
    con = db.connect()
    try:
        res = superlogin.authenticate(con, b.get("admin_key", ""), b.get("email", ""),
                                      b.get("otp_code", ""), ip)
    except superlogin.SuperloginError as e:
        con.close()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=403)
    con.close()
    resp = JSONResponse({"ok": True, "expires_at": res["expires_at"], "redirect": "/superlogin/hub"})
    resp.set_cookie("superlogin_session", res["session"], max_age=superlogin.SESSION_TTL_SECONDS,
                    httponly=True, samesite="lax")
    return resp


@router.post("/api/superlogin/request-otp", dependencies=[Depends(require_agency_console)])
async def superlogin_request_otp(request: Request):
    """Email a one-time superlogin code. Requires a valid admin key + @realify.ai staff email (so the
    gate can trigger a code); otherwise the surface does not exist (404)."""
    from .deps import admin_key_hash_ok, is_staff_email
    b = await _body(request)
    if not (admin_key_hash_ok(b.get("admin_key", "")) and is_staff_email(b.get("email", ""))):
        return JSONResponse({"ok": False, "error": "Not Found"}, status_code=404)
    con = db.connect()
    try:
        superlogin.issue_otp(con, b.get("email", ""))
    finally:
        con.close()
    return JSONResponse({"ok": True})
