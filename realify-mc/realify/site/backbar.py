"""R9 Part E — the persistent back-to-hub bar shown on every impersonated surface. Reads
request.session['acting_as'] (set by the sandbox impersonate/assume endpoints) and renders the mockup's
.backbar: "acting as: {role} · {tenant} · sandbox [· via {agency}]" + one-click return. Absent when not
impersonating."""
import html as _h

_CSS = ("<style>#r9backbar{background:#1A1A1A;color:#fff;padding:9px 20px;font-size:13px;display:flex;"
        "align-items:center;gap:14px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
        "position:sticky;top:0;z-index:9500}"
        "#r9backbar .bk{background:#333;border:none;color:#fff;border-radius:7px;padding:6px 12px;"
        "font-size:12.5px;cursor:pointer}#r9backbar .who{margin-left:auto;font-family:ui-monospace,Menlo,"
        "monospace;font-size:11.5px;color:#B7AE9E}"
        # R11.1: when the bar is present, offset the seller SPA's sticky masthead AND the fixed SKU
        # detail drawer by the bar height so the drawer's ✕ + header aren't trapped under the bar.
        "#r9backbar~header.mast{top:40px}"
        "#r9backbar~.drawer{top:40px;height:calc(100% - 40px)}</style>")

_JS = ("<script>window._r9return=function(){fetch('/api/ops/sandbox/return',{method:'POST'})"
       ".then(function(r){return r.json();}).then(function(d){location.href=(d&&d.redirect)||'/superlogin/hub';})"
       ".catch(function(){location.href='/superlogin/hub';});};</script>")


_SCOPE_CSS = ("<style>#r9scopebar select{background:#2A2A2A;color:#fff;border:1px solid #444;"
              "border-radius:7px;padding:5px 8px;font-size:12px;font-family:ui-monospace,Menlo,monospace}</style>")


def scope_bar(brand, brand_id, envelope, agency, siblings):
    """R11 Part C — the SCOPE-SWITCHER bar (mockup h8) shown on the brand drill-in: '← Fleet',
    'Portfolio ▸ {Brand} ▾' (the ▾ is a brand picker to hop accounts), and the acting-as line naming
    the operating agency + the granted envelope. Reuses the dark .backbar chrome."""
    opts = "".join(
        f"<option value='/agency/brand/{s['id']}'{' selected' if s['id'] == brand_id else ''}>"
        f"{_h.escape(s['name'])}</option>" for s in siblings)
    return (f'{_CSS}{_SCOPE_CSS}<div id="r9backbar" id2="r9scopebar">'
            f'<button class="bk" onclick="location.href=\'/agency/console\'">← Fleet</button>'
            f'<span style="font-family:ui-monospace,Menlo,monospace;font-size:12.5px">Portfolio ▸ '
            f'<b style="color:#fff">{_h.escape(brand)}</b></span>'
            f'<select onchange="if(this.value)location.href=this.value" title="switch brand">{opts}</select>'
            f'<span class="who">▸ {_h.escape(agency)} operating · envelope: {_h.escape(envelope)}</span></div>')


_GUIDED_CSS = (
    "<style>#r9guided{background:#2A2620;color:#EDE7DB;border-bottom:2px solid #C4785B;padding:8px 18px;"
    "font-size:13px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;position:sticky;top:0;z-index:9700;"
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}"
    "#r9guided .gtag{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;letter-spacing:.08em;"
    "text-transform:uppercase;color:#C4785B;font-weight:700}"
    "#r9guided .gp{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:#B7AE9E}"
    "#r9guided .gi{flex:1;min-width:200px}#r9guided .gdots{display:flex;gap:4px}"
    "#r9guided .gd{width:7px;height:7px;border-radius:50%;background:#4A443B}#r9guided .gd.on{background:#C4785B}"
    "#r9guided button{border:none;border-radius:8px;padding:7px 14px;font-size:12.5px;font-weight:600;cursor:pointer}"
    "#r9guided .gnext{background:#C4785B;color:#fff}#r9guided .gexit{background:#3A342B;color:#CFC8BA}"
    # R11.2: the guided bar STACKS ABOVE any contextual bar (scope/back-to-hub) and rides every surface.
    # body.has-guided drops the contextual bar below it (40px) and offsets the seller SPA's fixed drawer +
    # sticky masthead by BOTH bars, so Next/Exit stay reachable inside the brand drill-in + five-lens app.
    "body.has-guided #r9backbar{top:40px}"
    "body.has-guided .drawer{top:40px;height:calc(100% - 40px)}"
    "body.has-guided #r9backbar~header.mast{top:80px}"
    "body.has-guided #r9backbar~.drawer{top:80px;height:calc(100% - 80px)}</style>")

_GUIDED_JS = (
    "<script>document.body.classList.add('has-guided');"          # marks the surface for the stacked-bar offset
    "window._grNext=function(){fetch('/api/ops/sandbox/guided-run/next',{method:'POST'})"
    ".then(function(r){return r.json();}).then(function(d){if(d&&d.done){location.reload();}"
    "else if(d&&d.redirect){location.href=d.redirect;}else{location.reload();}});};"
    "window._grExit=function(){fetch('/api/ops/sandbox/guided-run/exit',{method:'POST'})"
    ".then(function(){location.reload();});};</script>")


def guided_bar(request):
    """The guided-run teleprompter (R11.1): persona + one-line instruction + Next/Exit + progress, riding
    every surface. Renders purely from session['guided'] (denormalized by the guided routes) — no DB."""
    try:
        g = request.session.get("guided")
    except Exception:
        g = None
    if not g:
        return ""
    i, total = int(g.get("i", 0)), int(g.get("total", 1))
    dots = "".join(f"<span class='gd{' on' if k <= i else ''}'></span>" for k in range(total))
    return (f"{_GUIDED_CSS}<div id=r9guided>"
            f"<span class=gtag>Guided run · {_h.escape(g.get('title','Run'))} · {i+1}/{total}</span>"
            f"<span class=gp>▸ as {_h.escape(g.get('persona','—'))}</span>"
            f"<span class=gi>{_h.escape(g.get('instr',''))}</span>"
            f"<span class=gdots>{dots}</span>"
            f"<button class=gnext onclick=_grNext()>Next →</button>"
            f"<button class=gexit onclick=_grExit()>Exit</button></div>{_GUIDED_JS}")


def _back_bar(request):
    """The back-to-hub bar (or '' when not impersonating). For a REAL agency customer operating one of its
    brands (agency_envelope set, no superlogin session) this is a 'Back to agency home' return to the
    fleet — NOT the tester/superlogin sandbox (those are agency customers, not testers)."""
    try:
        acting = request.session.get("acting_as")
        env = request.session.get("agency_envelope")
    except Exception:
        acting = env = None
    if not acting:
        return ""
    role = _h.escape(str(acting.get("role", "role")))
    tenant = _h.escape(str(acting.get("tenant", "tenant")))
    via = acting.get("via")
    is_tester = False
    if env:
        try:
            from .. import superlogin
            is_tester = bool(superlogin.verify_session(request.cookies.get("superlogin_session") or ""))
        except Exception:
            is_tester = False
    if env and not is_tester:                                # real agency operating one of ITS brands
        who = f"▸ operating: {role} · {tenant}" + (f" · via {_h.escape(str(via))}" if via else "")
        label = "← Back to agency home"
    else:                                                    # sandbox/superlogin impersonation
        who = f"▸ acting as: {role} · {tenant} · sandbox" + (f" · via {_h.escape(str(via))}" if via else "")
        label = "← Back to hub"
    return (f'{_CSS}<div id="r9backbar"><button class="bk" onclick="_r9return()">{label}</button>'
            f'<img src="/assets/Final-logo-full-white-V3.png" alt="Realify" '
            f'style="height:18px;width:auto;vertical-align:middle"><span class="who">{who}</span></div>{_JS}')


def bar(request):
    """The persistent top bar on every impersonated surface. During a guided run the teleprompter STACKS
    ABOVE the contextual back-to-hub bar (R11.2 — it rides every surface, Next/Exit always reachable);
    otherwise just the back-to-hub bar (or '' when not impersonating)."""
    return guided_bar(request) + _back_bar(request)
