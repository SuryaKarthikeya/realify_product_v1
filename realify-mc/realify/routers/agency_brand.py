"""Brand-facing surfaces (agency-plan R3, mockup screens 13/14/16/17) — behind AGENCY_CONSOLE,
Postgres-only. Data sources (screen 17), brand portal (14), day-0 baseline (13), offboarding (16).
Brand locale (₹/en-IN for INR brands). Authorized for the brand's own users or Realify staff key."""
import html
from realify.site import backbar as _backbar
from realify.site.tokens import state_page as _state_page   # (R11) fixes prior NameError in the 403 paths
import json

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from ..agency import (ingest, connections, ledger, ops, keyring, tenancy, rollups, queue, money,
                      db as agency_db)
from ..agency.guard import require_agency_console
from .deps import current

router = APIRouter()


async def _body(request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


def _brand_authorized(request, tenant_id):
    """Brand's own user (session) OR Realify staff key OR an AGENCY operator whose agency holds an active
    engagement on this brand. The agency arm is what lets the agency connect/upload data ON THE BRAND'S
    BEHALF — R11 engagement-based authz (grant-independent). Without it, the /agency/data-sources page
    403'd for every agency member (only the brand's own user passed), so agencies literally could not use
    it. Returns True/False."""
    from fastapi import HTTPException
    from .deps import require_admin
    try:
        require_admin(request)
        return True
    except HTTPException:
        pass
    uid, tid = current(request)
    if not uid:
        return False
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE id=%s AND tenant_id=%s", (uid, tenant_id))
        if cur.fetchone():
            return True
        from ..agency import fleet_data
        from ..agency.actor import resolve_actor
        ctx = resolve_actor(cur, uid)
        agency_id, _ = fleet_data.resolve_agency(cur, uid, tid, list(ctx.agency_ids))
        return agency_id is not None and tenant_id in fleet_data.agency_brand_ids(cur, agency_id)
    finally:
        conn.close()


def _brand_currency(cur, tenant_id):
    cur.execute("SELECT currency FROM agency_ingest_rows WHERE tenant_id=%s ORDER BY id DESC LIMIT 1",
                (tenant_id,))
    r = cur.fetchone()
    if r and r[0]:
        return r[0]
    cur.execute("SELECT currency FROM rollup_cache WHERE tenant_id=%s", (tenant_id,))
    r = cur.fetchone()
    return (r[0] if r and r[0] else "USD")


_PAGE_CSS = (  # R11 reskin -> warm design system (tokens paper + Georgia headings), layout unchanged
             "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,sans-serif;max-width:920px;"
             "margin:0 auto;padding:26px 22px;background:#F7F4EE;color:#1A1A1A}"
             "h1,h2,h3{font-family:Georgia,'Times New Roman',serif;font-weight:700}a{color:#C4785B}"
             "table{border-collapse:collapse;width:100%;background:#fff;margin-bottom:16px}"
             "th,td{border:1px solid #EFEAE0;padding:8px 12px;text-align:left;font-size:13px}"
             ".card{background:#fff;border:1px solid #DDD5C6;border-radius:12px;padding:18px 22px;margin-bottom:16px}"
             ".badge{font:600 10px/1 ui-monospace,monospace;background:#EAF0F5;color:#3E566A;border-radius:100px;padding:3px 8px}"
             ".danger{color:#B3402E}button{border-radius:8px;border:1px solid #DDD5C6;background:#C4785B;color:#fff;"
             "padding:9px 16px;cursor:pointer;margin:4px 6px 0 0}.ghost{background:#fff;color:#1A1A1A}"
             "input,textarea{padding:8px;border:1px solid #DDD5C6;border-radius:8px;width:100%}")


def _doc(title, body):
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title>"
            f"<style>{_PAGE_CSS}</style></head><body>{body}</body></html>")


# ---------------- screen 17: data sources · CSV · failures ----------------
@router.get("/agency/data-sources/{tenant_id}", dependencies=[Depends(require_agency_console)])
def data_sources_page(tenant_id: int, request: Request):
    # Retired (R18.9): the agency loads a brand's data through the REAL onboarding wizard now, reached by
    # drilling into the brand. Redirect any lingering link there instead of the bespoke paste-JSON page.
    return RedirectResponse(f"/agency/brand/{tenant_id}", status_code=307)


@router.post("/api/agency/data-sources/{tenant_id}/ingest", dependencies=[Depends(require_agency_console)])
async def data_sources_ingest(tenant_id: int, request: Request):
    if not _brand_authorized(request, tenant_id):
        return JSONResponse({"ok": False, "error": "not authorized"}, status_code=403)
    b = await _body(request)
    headers = b.get("headers") or []
    rows = b.get("rows") or []
    if not headers or not rows:
        return JSONResponse({"ok": False, "error": "headers and rows required"}, status_code=400)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        res = ingest.ingest_csv(cur, tenant_id, headers, rows,
                                source_class=b.get("source_class", "csv"), currency=b.get("currency"))
        conn.commit()
        return JSONResponse({"ok": True, "report_type": res["report_type"], "count": res["count"],
                             "currency": res["currency"], "source_class": b.get("source_class", "csv"),
                             "tagged_pct": ingest.source_class_tagged_pct(res["rows"])})
    except ValueError as e:
        conn.rollback()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    finally:
        conn.close()


# ---------------- screen 14: brand portal · transparency + approvals inbox + controls ----------------
@router.get("/brand/portal/{tenant_id}", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console)])
def brand_portal(tenant_id: int, request: Request):
    if not _brand_authorized(request, tenant_id):
        return HTMLResponse(_state_page("Not authorized", "You do not have access to this brand portal.", "Restricted"), status_code=403)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])
        cur.execute("SELECT seq, ts, action, actor_user FROM ledger WHERE tenant_id=%s ORDER BY seq DESC "
                    "LIMIT 30", (tenant_id,))
        log_rows = cur.fetchall()
        cur.execute("SELECT id, lens, kind, impact_usd_minor, cosign_expires_at FROM approvals "
                    "WHERE tenant_id=%s AND status='cosign_pending' ORDER BY cosign_expires_at", (tenant_id,))
        pending = cur.fetchall()
        cur.execute("SELECT id FROM engagements WHERE tenant_id=%s AND status='active' LIMIT 1", (tenant_id,))
        eng = cur.fetchone()
        ccy = _brand_currency(cur, tenant_id)
    finally:
        conn.close()
    locale = "en-IN · IST · ₹" if ccy == "INR" else "en-US · $"
    logh = "".join(f"<tr><td>{s}</td><td>{html.escape(str(ts))}</td><td>{html.escape(a)}</td></tr>"
                   for s, ts, a, _u in log_rows) or "<tr><td colspan=3><i>No activity yet.</i></td></tr>"
    inbox = "".join(
        f"<tr><td>#{i}</td><td>{html.escape(l)}/{html.escape(k)}</td>"
        f"<td>{money.format_money(imp, ccy)}</td><td>expires {html.escape(str(exp))}</td>"
        f"<td><a href='/agency/approve/{i}'>Review</a></td></tr>" for i, l, k, imp, exp in pending) \
        or "<tr><td colspan=5><i>Nothing needs you right now.</i></td></tr>"
    eng_id = eng[0] if eng else ""
    body = (_backbar.bar(request) + f"<h1>Your Realify portal</h1><p class=badge>Locale: {locale}</p>"
            "<div class=card><b>Nothing happens without you.</b> Pending requests below wait for your "
            "co-sign; if you do nothing they expire and are never executed.</div>"
            f"<h3>Approvals inbox</h3><table><tr><th>id</th><th>action</th><th>impact</th><th>expiry</th>"
            f"<th></th></tr>{inbox}</table>"
            f"<h3>Transparency log</h3><table><tr><th>#</th><th>when</th><th>action</th></tr>{logh}</table>"
            "<div class=card><h3>Controls</h3>"
            f"<button onclick='pause()'>Pause all execution</button>"
            f"<button class=ghost onclick='narrow()'>Narrow access (read-only)</button>"
            f"<button class=danger onclick='revoke()'>Revoke agency access</button>"
            "<p>Revoking is immediate. Your data, history, and connections stay with you.</p>"
            "<div id=cmsg></div></div>"
            "<script>"
            f"async function pause(){{await fetch('/api/agency/tenants/{tenant_id}/pause',{{method:'POST'}});cmsg.textContent='Execution paused.';}}"
            f"async function narrow(){{var r=await fetch('/api/brand/{tenant_id}/narrow',{{method:'POST'}});cmsg.textContent=r.ok?'Access narrowed to read-only.':'Failed.';}}"
            f"async function revoke(){{if(!confirm('Revoke agency access now?'))return;var r=await fetch('/api/brand/{tenant_id}/revoke',{{method:'POST'}});cmsg.textContent=r.ok?'Access revoked. Your data stays with you.':'Failed.';}}"
            "</script>")
    return HTMLResponse(_doc("Brand portal", body))


@router.post("/api/brand/{tenant_id}/revoke", dependencies=[Depends(require_agency_console)])
async def brand_revoke(tenant_id: int, request: Request):
    if not _brand_authorized(request, tenant_id):
        return JSONResponse({"ok": False, "error": "not authorized"}, status_code=403)
    uid, _ = current(request)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])
        cur.execute("SELECT id FROM engagements WHERE tenant_id=%s AND status='active'", (tenant_id,))
        rows = cur.fetchall()
        for (eng_id,) in rows:
            ops.revoke_engagement(cur, uid, eng_id, tenant_id)
        agency_db.audit(cur, str(uid or "brand"), "engagement.ended_by_brand", tenant_id=tenant_id)
        conn.commit()
        return JSONResponse({"ok": True, "revoked": len(rows)})
    finally:
        conn.close()


@router.post("/api/brand/{tenant_id}/narrow", dependencies=[Depends(require_agency_console)])
async def brand_narrow(tenant_id: int, request: Request):
    if not _brand_authorized(request, tenant_id):
        return JSONResponse({"ok": False, "error": "not authorized"}, status_code=403)
    from ..pdp import ENVELOPES
    uid, _ = current(request)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])
        cur.execute("SELECT id FROM engagements WHERE tenant_id=%s AND status='active' LIMIT 1", (tenant_id,))
        row = cur.fetchone()
        if not row:
            return JSONResponse({"ok": False, "error": "no active engagement"}, status_code=400)
        ops.publish_envelope(cur, uid, row[0], tenant_id, ENVELOPES["Read-only"], {})   # re-version narrower
        conn.commit()
        return JSONResponse({"ok": True, "narrowed": "Read-only"})
    finally:
        conn.close()


# ---------------- screen 13: day-0 baseline ----------------
def baseline(cur, tenant_id):
    """First-look numbers computed from the brand's ingested/connected data."""
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("SELECT gmv_usd_minor, margin_usd_minor, tacos_bps FROM rollup_cache WHERE tenant_id=%s",
                (tenant_id,))
    roll = cur.fetchone()
    items = queue.build(cur, [tenant_id], top_k=5)
    found = [i for i in items if i["impact_usd_minor"] > 0]
    return {"gmv_usd_minor": (roll[0] if roll else 0), "tacos_bps": (roll[2] if roll else None),
            "found_money": found, "watching": len(items)}


@router.get("/brand/day0/{tenant_id}", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console)])
def day0_page(tenant_id: int, request: Request):
    if not _brand_authorized(request, tenant_id):
        return HTMLResponse(_state_page("Not authorized", "You do not have access to this brand portal.", "Restricted"), status_code=403)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        b = baseline(cur, tenant_id)
    finally:
        conn.close()
    found = "".join(f"<li>{html.escape(i['lens'])}/{html.escape(i['kind'])} — "
                    f"{money.format_money(i['impact_usd_minor'], 'USD')} ({html.escape(i['signal'])})</li>"
                    for i in b["found_money"]) or "<li><i>Hydrating — first items within 24–72h.</i></li>"
    tacos = f"{b['tacos_bps']/100:.1f}%" if b["tacos_bps"] is not None else "—"
    body = (f"<h1>Your first look</h1>"
            "<div class=card>72 hours after granting, Realify has already found money — before your "
            "agency has done anything.</div>"
            f"<div class=card><b>Health</b> · GMV {money.format_money(b['gmv_usd_minor'],'USD')} · TACoS {tacos} · "
            f"watching {b['watching']} items</div>"
            f"<h3>Found money</h3><ul>{found}</ul>"
            "<div class=card><h3>Notifications</h3><label><input type=checkbox checked> Email — on</label><br>"
            "<label><input type=checkbox disabled> WhatsApp — <span class=badge>coming soon</span></label>"
            "<p>Approval requests expire in 5 days. <b>Silence never equals consent</b> — nothing executes "
            "unless you approve.</p></div>")
    return HTMLResponse(_doc("Day-0 baseline", body))


# ---------------- screen 16: offboarding · promise kept ----------------
@router.get("/brand/offboarding/{tenant_id}", response_class=HTMLResponse,
            dependencies=[Depends(require_agency_console)])
def offboarding_page(tenant_id: int, request: Request):
    if not _brand_authorized(request, tenant_id):
        return HTMLResponse(_state_page("Not authorized", "You do not have access to this brand portal.", "Restricted"), status_code=403)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])
        cur.execute("SELECT count(*) FROM agency_audit WHERE tenant_id=%s AND action='engagement.ended_by_brand'",
                    (tenant_id,))
        brand_ended = cur.fetchone()[0] > 0
    finally:
        conn.close()
    continue_directly = ("<div class=card><b>Continue on Realify directly.</b> Because you ended this "
                         "engagement, you can keep using Realify without an agency. "
                         "<a href='/pricing'>See plans →</a></div>") if brand_ended else ""
    body = ("<h1>Offboarding — the promise kept</h1>"
            "<div class=card>Access is closed in seconds and every step is ledgered. <b>What stays with "
            "you:</b> your store data, your full history, and your channel connections — they were always "
            "yours.</div>"
            + continue_directly +
            "<div class=card><h3>Export your data</h3>"
            f"<a href='/api/brand/{tenant_id}/export'><button>Download data + ledger (JSON)</button></a></div>"
            "<div class=card><h3 class=danger>Delete everything (crypto-shred)</h3>"
            "<p>This permanently destroys your brand key so all stored payloads become unreadable. It is "
            "irreversible and issues a signed deletion certificate. Requires a typed confirmation and a "
            "Realify staff co-sign.</p>"
            f"<form onsubmit='return del(event)'><input id=confirm placeholder='type DELETE to confirm'>"
            "<button class=danger type=submit>Delete &amp; issue certificate</button></form><div id=dmsg></div></div>"
            "<script>async function del(e){e.preventDefault();"
            f"var r=await fetch('/api/brand/{tenant_id}/delete-certificate',{{method:'POST',headers:{{'content-type':'application/json'}},"
            "body:JSON.stringify({confirm:document.getElementById('confirm').value})});"
            "var d=await r.json().catch(function(){return{}});dmsg.textContent=r.ok?('Certificate '+d.certificate_id+' issued.'):((d&&d.error)||'Failed / staff co-sign required.');}"
            "</script>")
    return HTMLResponse(_doc("Offboarding", body))


@router.get("/api/brand/{tenant_id}/export", dependencies=[Depends(require_agency_console)])
def brand_export(tenant_id: int, request: Request):
    if not _brand_authorized(request, tenant_id):
        return JSONResponse({"ok": False, "error": "not authorized"}, status_code=403)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])
        cur.execute("SELECT seq, ts, action FROM ledger WHERE tenant_id=%s ORDER BY seq", (tenant_id,))
        led = [{"seq": s, "ts": str(t), "action": a} for s, t, a in cur.fetchall()]
        cur.execute("SELECT report_type, source_class, currency, payload FROM agency_ingest_rows "
                    "WHERE tenant_id=%s", (tenant_id,))
        data = [{"report_type": rt, "source_class": sc, "currency": c, "payload": p}
                for rt, sc, c, p in cur.fetchall()]
    finally:
        conn.close()
    return JSONResponse({"tenant_id": tenant_id, "ledger": led, "data": data,
                         "note": "Your data + activity ledger. Exported on request; yours to keep."},
                        headers={"Content-Disposition": f"attachment; filename=realify-export-{tenant_id}.json"})


@router.post("/api/brand/{tenant_id}/delete-certificate", dependencies=[Depends(require_agency_console)])
async def brand_delete_certificate(tenant_id: int, request: Request):
    """Deletion ceremony: typed confirmation + Realify staff co-sign (admin key). Crypto-shreds the
    brand key (payloads become unreadable; the ledger chain still verifies) and issues a ledgered
    deletion certificate."""
    from .deps import require_admin
    from fastapi import HTTPException
    b = await _body(request)
    if (b.get("confirm") or "").strip() != "DELETE":
        return JSONResponse({"ok": False, "error": "type DELETE to confirm"}, status_code=400)
    try:
        require_admin(request)                     # staff co-sign (admin key)
    except HTTPException:
        return JSONResponse({"ok": False, "error": "staff co-sign required"}, status_code=403)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])
        keyring.crypto_shred(cur, tenant_id)
        chain_ok = ledger.verify_chain(cur, tenant_id)         # chain still verifies post-shred
        cert_id = agency_db.audit(cur, "brand+staff", "brand.deletion_certificate", tenant_id=tenant_id,
                                  detail={"crypto_shred": True, "chain_verifies": chain_ok})
        conn.commit()
        return JSONResponse({"ok": True, "certificate_id": cert_id, "crypto_shred": True,
                             "chain_verifies": chain_ok})
    finally:
        conn.close()
