"""R11 Part C — the SCOPE-SWITCHER drill-in (mockup h8). The agency clicks a fleet brand and lands
here, scoped to that ONE brand and bounded by the granted envelope: the five lens tabs (with any
envelope-locked lens rendered 🔒 read-only), the per-brand DECISIONS panel where the agency now ACTS
(this replaces the retired cross-brand queue), and a deep-link into the brand's real five-lens seller
app. Envelope enforcement is real, not cosmetic: the act buttons post to the same envelope⊗grant-checked
/api/agency/queue/propose path — a suggest-only lens offers 'Propose to brand →', never an Approve."""
import html as _h

from . import hubkit
from . import backbar as _backbar
from .busy_modal import SNIPPET as _BUSY_MODAL

# UX lens → PDP lens (templates.py LENSES = pricing/ads/inventory/listings/reporting).
_UX_LENSES = [("Product Catalog", "listings"), ("Profit & Ads", "ads"),
              ("Intelligence", "reporting"), ("Category Analyst", "reporting"), ("Pricing", "pricing")]


def _locked(caps, pdp_lens):
    mk = (caps or {}).get(pdp_lens, {}).get("max_kind", "read")
    return mk in ("read", "none")                # can't propose/execute → read-only lens


def _lens_tabs(caps):
    out, first_open = [], True
    for label, pdp in _UX_LENSES:
        locked = _locked(caps, pdp)
        cls = "lenstab"
        if locked:
            cls += " locked"
        elif first_open:
            cls += " on"; first_open = False
        out.append(f"<span class='{cls}'>{_h.escape(label)}{' 🔒 read-only' if locked else ''}</span>")
    return "".join(out)


def _drow(i, caps):
    mk = (caps or {}).get(i["lens"], {}).get("max_kind", "propose")
    dat = (f"data-t={i['tenant_id']} data-lens='{_h.escape(i['lens'])}' data-kind='{_h.escape(i['kind'])}' "
           f"data-signal='{_h.escape(i['signal'])}' data-impact={i['rank_usd_minor']}")
    if mk == "execute":
        act = f"<button class='btn dark sm act-approve' {dat}>Approve</button>"
    else:                                        # suggest-only under the envelope → propose, never execute
        act = f"<button class='btn g sm act-approve' {dat}>Propose to brand →</button>"
    rankusd = f"${i['rank_usd_minor']/100:,.0f}"
    if i["impact_currency"] != "USD":
        amt = f"{_h.escape(i.get('display',''))}/mo ≈ {rankusd}"
        fx = f" <span class=note-s>· locked FX {_h.escape(i.get('fx_date','—'))}</span>"
    else:
        amt = f"{rankusd}/mo"; fx = ""
    return (f"<div class=drow><div class=sig><span class=lens>{_h.escape(i['lens'])}</span> "
            f"{_h.escape(i['signal'])} <span class=note-s>· confidence {i['confidence']}%</span>{fx}</div>"
            f"<div style='display:flex;gap:8px;align-items:center'><span class=amt>{amt}</span>{act}</div></div>")


def _executed_section(executed):
    """Recent executions on THIS brand + Undo (reversible) — the act surface shows what it did (R11)."""
    rows = "".join(
        f"<div class=drow><div class=sig>Execution #{xid} · <b>{_h.escape(str(acct))}</b> "
        f"(from approval #{apid})</div><button class='btn g sm act-undo' data-x={xid}>Undo</button></div>"
        for xid, acct, apid in executed)
    return ("<div style='margin-top:18px'><div class=note-s style='margin-bottom:6px'>"
            "<b>Executed / auto-cleared</b> — reversible</div>"
            f"<div class=dpanel>{rows or '<div class=drow><div class=sig>Nothing executed yet.</div></div>'}</div></div>")


def brandscope_html(request, brand, brand_id, agency, envelope_name, caps, items, siblings, paused=False,
                    executed=None):
    # R11.2: during a guided run the teleprompter stacks ABOVE the scope bar so Next/Exit ride the drill-in too
    bar = _backbar.guided_bar(request) + _backbar.scope_bar(brand, brand_id, envelope_name, agency, siblings)
    tabs = _lens_tabs(caps)
    locked_lenses = [lbl for lbl, pdp in _UX_LENSES if _locked(caps, pdp)]
    locknote = (f"<div class=locknote>🔒 <b>{_h.escape(', '.join(sorted(set(locked_lenses))))}</b> "
                f"read-only under this brand's envelope (<b>{_h.escape(envelope_name)}</b>) — enforced "
                f"server-side, so those actions can only be <i>proposed</i>, never executed.</div>"
                if locked_lenses else "")
    if paused:
        panel = ("<div class=locknote>⚠ This brand's connection is expired — decisions are paused. "
                 "Fix the connection to resume recommendations.</div>")
    else:
        rows = "".join(_drow(i, caps) for i in items) or \
            "<div class=drow><div class=sig>No open decisions for this brand right now.</div></div>"
        panel = (f"<div class=dpanel>{rows}</div>")
    inner = (
        f"<h2 class=htitle>{_h.escape(brand)}</h2>"
        f"<p class=hsub>Operating inside this account, scoped to it and bounded by the "
        f"<b>{_h.escape(envelope_name)}</b> envelope.</p>"
        f"<div class=lenstabs style='margin-top:14px'>{tabs}</div>"
        f"{locknote}"
        "<div class=note-s style='margin:2px 0 10px'>Per-brand decisions — this is where the agency "
        "acts (the cross-brand queue is retired). Approve executes; a locked lens can only be proposed.</div>"
        f"{panel}"
        f"{_executed_section(executed or [])}"
        "<div style='margin-top:16px'><a class='btn dark sm' href='/'>Open the full five-lens seller app "
        "for this brand →</a> <span class=note-s>(the same product the brand's own owner uses, scoped here)</span></div>")
    body = hubkit.frame(inner, sandbar_left=f"<b>SANDBOX</b> · {_h.escape(agency)} operating {_h.escape(brand)}",
                        sandbar_right="env: staging")
    js = ("<script>"
          "function _pp(u,b){return fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b||{})});}"
          "function _dd(e){var x=e.currentTarget.dataset;return {tenant_id:+x.t,lens:x.lens,kind:x.kind,signal:x.signal,impact_usd_minor:+x.impact};}"
          "document.querySelectorAll('.act-approve').forEach(function(b){b.addEventListener('click',function(e){var p=_dd(e);"
          "RealifyBusy.run(e.currentTarget,{title:'Submitting decision',refresh:function(){location.reload();}},"
          "function(){return _pp('/api/agency/queue/propose',p);});});});"
          "document.querySelectorAll('.act-undo').forEach(function(b){b.addEventListener('click',function(e){"
          "RealifyBusy.run(e.currentTarget,{title:'Undoing — restoring snapshot',refresh:function(){location.reload();}},"
          "function(){return _pp('/api/agency/executions/'+e.currentTarget.dataset.x+'/undo',{});});});});"
          "</script>")
    return hubkit.doc("Realify · " + _h.escape(brand), hubkit.AGENCY_CSS,
                      _BUSY_MODAL + bar + body + js)
