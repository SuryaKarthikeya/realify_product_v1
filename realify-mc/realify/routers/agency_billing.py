"""Reporting / billing / pilot routes (agency-plan P6) — behind AGENCY_CONSOLE, Postgres-only.
SES bounce/complaint webhook (suppression), agency ROI page (screen 20), pilot conversion (screen 24,
ledger-derived) + e-sign. Stripe calls live in realify.agency.billing_agency (test mode only, mockable)."""
import html
import json

from fastapi import APIRouter, Request, Depends
from realify.site.tokens import state_page as _state_page
from fastapi.responses import HTMLResponse, JSONResponse

from .. import mail, config
from ..agency import (suppression, pilots, rollups, money, reports, billing_agency, metering, ledger,
                      tenancy, mailcfg, db as agency_db)
from ..agency.actor import resolve_actor
from ..agency.guard import require_agency_console
from .deps import current

router = APIRouter()


def _allowed(uid):
    conn = agency_db.agency_connect()
    try:
        ctx = resolve_actor(conn.cursor(), uid)
        conn.rollback()
        return list(ctx.allowed_tenant_ids), ctx.agency_ids
    finally:
        conn.close()


@router.post("/api/ses/notifications")
async def ses_notifications(request: Request):
    """SES bounce/complaint webhook via SNS. **Flag-INDEPENDENT by design** (no require_agency_console):
    AWS must be able to reach it — to complete the subscription handshake and to deliver feedback — no
    matter whether AGENCY_CONSOLE is on. Its ONLY protection is SNS signature verification (sns.verify);
    unsigned / invalid / non-AWS payloads are rejected before anything else runs. A SubscriptionConfirmation
    is auto-confirmed (by GETting the signed SubscribeURL) so no human is needed to finish the handshake."""
    raw = await request.body()
    try:
        payload = json.loads(raw or b"{}")
    except Exception:
        return JSONResponse({"ok": False, "error": "bad json"}, status_code=400)
    # Provenance log: proves whether the request traversed Cloudflare (cf-ray / CF-Connecting-IP) and
    # what SNS message type/signature version AWS actually sent. Greppable: "[ses-webhook]".
    print(f"[ses-webhook] cf-ray={request.headers.get('cf-ray')} "
          f"cf-ip={request.headers.get('cf-connecting-ip')} "
          f"type={payload.get('Type')} sigver={payload.get('SignatureVersion')}", flush=True)
    from ..agency import sns
    try:
        sns.verify(payload)                         # reject unsigned/invalid/non-AWS payloads (P7 rider)
    except sns.SNSVerificationError as e:
        return JSONResponse({"ok": False, "error": f"SNS verification failed: {e}"}, status_code=403)
    # Subscription handshake: confirm (or unsubscribe-confirm) by visiting the signed AWS SubscribeURL.
    if payload.get("Type") in ("SubscriptionConfirmation", "UnsubscribeConfirmation"):
        try:
            sns.confirm_subscription(payload.get("SubscribeURL"))
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"confirm failed: {e}"}, status_code=502)
        return JSONResponse({"ok": True, "confirmed": True})
    msg = payload.get("Message")                    # SNS wraps the SES notification as a JSON string
    if isinstance(msg, str):
        try:
            payload = json.loads(msg)
        except Exception:
            pass
    try:                                            # suppression write needs the PG backend; ack if absent
        conn = agency_db.agency_connect()
    except Exception:
        return JSONResponse({"ok": True, "suppressed": []})
    try:
        added = suppression.handle_ses_notification(conn.cursor(), payload)
        conn.commit()
    finally:
        conn.close()
    return JSONResponse({"ok": True, "suppressed": added})


@router.get("/agency/roi", response_class=HTMLResponse, dependencies=[Depends(require_agency_console)])
def roi_page(request: Request):
    uid, _ = current(request)
    if not uid:
        return HTMLResponse(_state_page("Sign in required", "This surface needs a signed-in session.", "Restricted"), status_code=401)
    allowed, _ = _allowed(uid)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        port = rollups.portfolio(cur, allowed)
        brands = rollups.per_brand(cur, allowed)
        roi = rollups.roi_projected(cur, allowed)
    finally:
        conn.close()
    rows = "".join(f"<tr><td>{b['tenant_id']}</td><td>{html.escape(b['gmv_display'])}</td>"
                   f"<td>{money.format_money(b['gmv_usd_minor'], 'USD')}</td></tr>" for b in brands)
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8><title>ROI</title><body style='font-family:system-ui'>"
        f"<h1>Your Realify impact</h1>"
        f"<p><b>Projected impact of actions taken:</b> "
        f"{money.format_money(roi['projected_impact_usd_minor'], 'USD')} across {roi['executed']} executed "
        f"decisions. <i>Projected</i> — the sum of each executed decision's projected impact; this is "
        f"<b>not</b> a measured vs. do-nothing counterfactual (realized reconciliation is future work).</p>"
        f"<p>Portfolio USD GMV: {money.format_money(port['gmv_usd_minor'], 'USD')}</p>"
        f"<table border=1 cellpadding=6><tr><th>brand</th><th>GMV (selling)</th><th>GMV (USD)</th></tr>"
        f"{rows}</table></body>")


@router.get("/agency/convert", response_class=HTMLResponse, dependencies=[Depends(require_agency_console)])
def convert_page(request: Request):
    uid, _ = current(request)
    if not uid:
        return HTMLResponse(_state_page("Sign in required", "This surface needs a signed-in session.", "Restricted"), status_code=401)
    allowed, agencies = _allowed(uid)
    conn = agency_db.agency_connect()
    try:
        s = pilots.conversion_summary(conn.cursor(), agencies[0] if agencies else None, allowed)
    finally:
        conn.close()
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8><title>Convert</title><body style='font-family:system-ui'>"
        f"<h1>Your pilot</h1><p>Decisions executed: {s['executions_ledgered']}</p>"
        f"<p>Approvals: {s['approvals_ledgered']}</p>"
        "<form method=post action=/api/agency/pilot/esign><input name=terms_version value='v1'>"
        "<button>E-sign &amp; convert</button></form></body>")


@router.post("/api/agency/pilot/esign", dependencies=[Depends(require_agency_console)])
async def esign(request: Request):
    uid, _ = current(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    try:
        b = dict(await request.form()) or await request.json()
    except Exception:
        b = {}
    _, agencies = _allowed(uid)
    if not agencies:
        return JSONResponse({"ok": False, "error": "no agency"}, status_code=400)
    conn = agency_db.agency_connect()
    try:
        res = pilots.esign(conn.cursor(), agencies[0], (b.get("terms_version") or "v1"), uid)
        conn.commit()
    finally:
        conn.close()
    return JSONResponse({"ok": True, **res})


async def _body(request):
    try:
        return dict(await request.form()) or await request.json()
    except Exception:
        try:
            return await request.json()
        except Exception:
            return {}


# ---------------- reports: generate -> factuality gate -> deliver (screen 20 report) ----------------
@router.post("/api/agency/reports/{tenant_id}/generate", dependencies=[Depends(require_agency_console)])
async def generate_report(tenant_id: int, request: Request):
    """Agency-triggered white-label report for one client/period. The factuality gate BLOCKS delivery:
    a failing report returns an internal error state and is NEVER emailed. On pass: email to the brand
    + a ledger entry. A `template` may be posted (used to exercise the corrupted-template block)."""
    uid, _ = current(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    b = await _body(request)
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        tenancy.set_brand_scope(cur, [tenant_id])
        cur.execute("SELECT gmv_minor, currency FROM rollup_cache WHERE tenant_id=%s", (tenant_id,))
        r = cur.fetchone()
        gmv_minor, ccy = (r[0], r[1]) if r else (0, "USD")
        roi = rollups.roi_projected(cur, [tenant_id])
        cur.execute("SELECT a.name FROM agencies a JOIN engagements e ON e.agency_id=a.id "
                    "WHERE e.tenant_id=%s LIMIT 1", (tenant_id,))
        arow = cur.fetchone()
        agency_name = arow[0] if arow else "Your agency"
        figures = {"gmv": money.format_money(gmv_minor, ccy),                 # brand selling currency
                   "impact": money.format_money(roi["projected_impact_usd_minor"], "USD"),
                   "executed": str(roi["executed"])}
        template = b.get("template") or (
            "This period your store did {{gmv}} in sales. Realify's actions delivered {{impact}} in "
            "projected impact across {{executed}} executed decisions.")
        wl = {"agency_name": agency_name, "color": "#1A1A1A", "logo": ""}
        try:
            html_report = reports.generate(template, figures, white_label=wl)
        except reports.FactualityError as e:
            agency_db.audit(cur, str(uid), "report.blocked", tenant_id=tenant_id, detail={"reason": str(e)})
            conn.commit()
            return JSONResponse({"ok": False, "blocked": True, "error": str(e)}, status_code=422)
        cur.execute("SELECT email FROM users WHERE tenant_id=%s ORDER BY id LIMIT 1", (tenant_id,))
        urow = cur.fetchone()
        brand_email = urow[0] if urow else None
        if brand_email:
            mail.send(brand_email, f"{agency_name}: your Realify report", html_report,
                      from_addr=mailcfg.from_addr(), reply_to=mailcfg.reply_to())
        ledger.append(cur, tenant_id, uid, "report.published",
                      payload={"gmv": figures["gmv"], "impact": figures["impact"]})
        conn.commit()
        return JSONResponse({"ok": True, "delivered": bool(brand_email), "currency": ccy})
    finally:
        conn.close()


# ---------------- billing: Plan & billing page (screen 21) ----------------
@router.get("/agency/billing", response_class=HTMLResponse, dependencies=[Depends(require_agency_console)])
def billing_page(request: Request):
    import datetime
    uid, _ = current(request)
    if not uid:
        return HTMLResponse(_state_page("Sign in required", "This surface needs a signed-in session.", "Restricted"), status_code=401)
    allowed, agencies = _allowed(uid)
    ag = agencies[0] if agencies else None
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT per_account_price_minor,platform_fee_minor,usage_unit_price_minor,decisions_pool,"
                    "status FROM agency_subscriptions WHERE agency_id=%s", (str(ag),))
        sub = cur.fetchone()
        pool = int(sub[3]) if sub else 1000
        cur.execute("SELECT hq_country FROM agencies WHERE id=%s", (str(ag),))
        hq = (cur.fetchone() or [None])[0]
        qtys = metering.per_client_qty(cur, allowed) if allowed else {}
        used = sum(qtys.values())
        per_client_value = {b: rollups.roi_projected(cur, [b])["projected_impact_usd_minor"] for b in allowed}
        cur.execute("SELECT id,period_start,period_end,total_usd_minor,status FROM invoices WHERE agency_id=%s "
                    "ORDER BY id DESC LIMIT 12", (str(ag),))
        invoices = cur.fetchall()
    finally:
        conn.close()
    dom = datetime.date.today().day
    projected = int(used / max(dom, 1) * 30)
    pct = int(used * 100 / pool) if pool else 0
    warn = " style='color:#B3402E'" if pct >= 85 else ""
    alloc_rows = "".join(
        f"<tr><td>{b}</td><td>{qtys.get(b,0)}</td><td>{money.format_money(per_client_value.get(b,0),'USD')}</td></tr>"
        for b in allowed) or "<tr><td colspan=3><i>No client usage yet.</i></td></tr>"
    inv_rows = "".join(
        f"<tr><td>#{i}</td><td>{html.escape(str(ps))}–{html.escape(str(pe))}</td>"
        f"<td>{money.format_money(tot,'USD')}</td><td>{html.escape(stt)}</td></tr>"
        for i, ps, pe, tot, stt in invoices) or "<tr><td colspan=4><i>No invoices yet.</i></td></tr>"
    gst = ("<p class=note>India-HQ agency: invoiced in USD with an INR reference; GST is your entity's "
           "responsibility on the INR-equivalent.</p>") if hq == "IN" else ""
    return HTMLResponse(
        "<!doctype html><meta charset=utf-8><title>Plan &amp; billing</title><body style='font-family:system-ui;"
        "max-width:880px;margin:0 auto;padding:26px'><h1>Plan &amp; billing</h1>"
        f"<p>Subscription status: <b>{html.escape(sub[4]) if sub else 'none'}</b></p>"
        f"<div style='border:1px solid #DDD5C6;border-radius:12px;padding:16px'><h3>Decisions pool</h3>"
        f"<p{warn}>Used <b>{used}</b> of {pool} this month ({pct}%); on pace for ~<b>{projected}</b>.</p>"
        "<p><b>We'll warn you at 85% — never surprise-bill.</b></p></div>"
        f"<h3>Per-client cost allocation</h3><table border=1 cellpadding=6>"
        f"<tr><th>brand</th><th>decisions</th><th>Value delivered (projected)</th></tr>{alloc_rows}</table>"
        f"<h3>Invoices</h3><table border=1 cellpadding=6><tr><th>#</th><th>period</th><th>total</th>"
        f"<th>status</th></tr>{inv_rows}</table>"
        "<p><a href='/api/agency/billing/export.csv'>Download invoices (CSV)</a></p>" + gst + "</body>")


@router.get("/api/agency/billing/export.csv", dependencies=[Depends(require_agency_console)])
def billing_export(request: Request):
    uid, _ = current(request)
    if not uid:
        return JSONResponse({"ok": False, "error": "auth required"}, status_code=401)
    _, agencies = _allowed(uid)
    ag = agencies[0] if agencies else None
    conn = agency_db.agency_connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id,period_start,period_end,currency,usage_usd_minor,base_usd_minor,"
                    "total_usd_minor,status FROM invoices WHERE agency_id=%s ORDER BY id", (str(ag),))
        rows = cur.fetchall()
    finally:
        conn.close()
    from fastapi.responses import PlainTextResponse
    lines = ["invoice_id,period_start,period_end,currency,usage_usd_minor,base_usd_minor,total_usd_minor,status"]
    lines += [",".join(str(x) for x in r) for r in rows]
    return PlainTextResponse("\n".join(lines),
                             headers={"Content-Disposition": "attachment; filename=invoices.csv"})
