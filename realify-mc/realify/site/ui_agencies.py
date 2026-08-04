"""/agencies marketing landing (R5, mockup screen 1) — hero, differentiator band, six feature cards,
pilot-process band, and the full application form at #apply. Renders through the shared marketing
layout (ui.doc). TRUTH-GUARDED: every claim maps to a live feature; no marketplace-execution,
benchmarking, ROI-multiple, or leverage-statistic claims."""
from . import ui

_MARKETPLACES = ["Amazon US", "Amazon IN", "Walmart", "Shopify", "eBay", "Flipkart", "Shopzee"]
_AD_PLATFORMS = ["Amazon Ads", "Google", "Meta"]
_TOOLS = ["Pacvue", "Helium 10", "Perpetua", "Teikametrics", "SellerStack", "Spreadsheets", "Other"]


def _chips(name, options):
    return ('<div class="chips">'
            + "".join(f'<label class="chip"><input type="checkbox" name="{name}" value="{ui.esc(o)}" '
                      f'style="margin-right:7px">{ui.esc(o)}</label>' for o in options) + '</div>')


def agencies_landing():
    feature = lambda ic, h, p: f'<div class="card"><span class="kick">{ic}</span><h3 style="margin:8px 0 8px">{h}</h3><p>{p}</p></div>'
    body = f"""
    <section class="hero"><div class="wrap">
      <span class="kick">Realify for Agencies · Pilot program</span>
      <h1 style="max-width:20ch;margin-top:12px">Run every client's profit decisions from one queue.</h1>
      <p class="sub">One dollar-ranked stream of decisions across your whole book — with client-granted,
      revocable permissions, approval workflows your clients co-sign, and reports whose every number is
      machine-verified before it can send.</p>
      <div class="row"><a class="btn btn-blue btn-big" href="#apply">Request access →</a>
      <span style="font-size:13px;color:var(--muted);margin-left:6px">Reviewed personally · reply within 2 business days · no card, no trial clock</span></div>
    </div></section>

    <section class="dark"><div class="wrap">
      <span class="kick">Why agencies</span>
      <h2>Built around the two things agencies can't buy elsewhere.</h2>
      <div class="grid g2">
        <div class="card"><h3>Your clients grant access — and can see everything</h3>
        <p>No shared logins, no credential spreadsheets. Each client approves a scoped permission
        envelope (down to the lens: ads, inventory, pricing…), sets their own approval ceilings, and
        gets a permanent log of every action your team takes. They can <b>narrow or revoke</b> any
        time — which is exactly why they say yes.</p></div>
        <div class="card"><h3>Numbers your clients can audit</h3>
        <p>Every figure in a client report is checked against the computation engine before the report
        can send — a report with an unverifiable number is <b>blocked, not delivered</b>. When you
        present results, the arithmetic is defensible to the decimal.</p></div>
      </div>
    </div></section>

    <section><div class="wrap">
      <span class="kick">What you get</span>
      <h2>The working day, redesigned.</h2>
      <div class="grid g3">
        {feature('Queue', 'One decision queue', "Opportunities and risks across all clients in a single stream, ranked by monthly profit impact — with the driving signal and confidence on every item. USD and INR books rank together at a locked daily FX rate.")}
        {feature('Approvals', 'Approvals with real rules', "Actions your client's envelope allows, you approve. Sensitive ones route for client co-sign — from their inbox, on their phone. Requests expire in 5 days: <b>Silence never executes</b> anything.")}
        {feature('Ledger', 'An audit trail with undo', "Every action lands in a tamper-evident ledger your client can see, and applied changes carry one-click undo from snapshots.")}
        {feature('Reports', 'Client-ready reports', "Generated per client, in their currency and format (₹ with Indian grouping for INR sellers), with your agency's branding — and the verification gate on every number.")}
        {feature('Billing', 'Billing you can reconcile', "Pooled decision metering with per-client cost allocation — defend your own margins with a books-ready export. Your clients <b>never receive an invoice from us</b>.")}
        {feature('CSV', 'Start with CSVs, today', "No integration project required: onboard a client from their marketplace exports — auto-detected report types, guided column mapping. Data is tagged by source so you always know what you're looking at.")}
      </div>
    </div></section>

    <section class="dark"><div class="wrap">
      <span class="kick">How the pilot works</span>
      <div class="grid g3" style="margin-top:22px">
        <div class="card"><h3>1 · Apply below</h3><p><b>A human reads this</b> — expect a reply within 2 business days.</p></div>
        <div class="card"><h3>2 · Pilot call</h3><p>30 minutes to scope your first clients and pilot
        terms. Pricing is agreed before anything starts — no card at signup, no trial clock.</p></div>
        <div class="card"><h3>3 · First client live</h3><p>Your workspace is provisioned, your team
        invited, and your first client asked for consent — the queue populates from their data.</p></div>
      </div>
    </div></section>

    <section id="apply"><div class="wrap" style="max-width:820px">
      <span class="kick">Request access</span>
      <h2>Tell us about your book.</h2>
      <form id="agform" onsubmit="return agsubmit(event)">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 18px">
          <div class="field"><label>Agency name *</label><input name="agency_name" required placeholder="BrightPeak Commerce"></div>
          <div class="field"><label>Website *</label><input name="website" required placeholder="brightpeak.co"></div>
          <div class="field"><label>Your name *</label><input name="contact_name" required placeholder="Sarah Mitchell"></div>
          <div class="field"><label>Work email *</label><input name="contact_email" type="email" required placeholder="sarah@brightpeak.co"><div class="hint">Becomes the admin account.</div></div>
        </div>
        <div class="field"><label>Where is your agency based? *</label>
          <select name="hq_country"><option value="US">United States</option><option value="IN">India</option></select>
          <div class="hint">Manage brands in either market from either country. Pricing is always in USD.</div></div>
        <div class="field"><label>Brand accounts you manage *</label>
          <select name="book_size"><option>1–5</option><option>6–15</option><option>16–40</option><option>40+</option></select></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 18px">
          <div class="field"><label>Account managers running those accounts *</label>
            <select name="am_headcount"><option>1</option><option>2</option><option>3</option><option>5</option><option>10</option></select></div>
          <div class="field"><label>Hours/month on client reporting</label>
            <select name="reporting_hours"><option>&lt;10</option><option>10–40</option><option>40–100</option><option>100+</option></select></div>
        </div>
        <div class="field"><label>Marketplaces your clients sell on *</label>{_chips("marketplaces", _MARKETPLACES)}</div>
        <div class="field"><label>Ad platforms you run</label>{_chips("ad_platforms", _AD_PLATFORMS)}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 18px">
          <div class="field"><label>Current tool</label>
            <select name="current_tool">{"".join(f"<option>{ui.esc(t)}</option>" for t in _TOOLS)}</select></div>
          <div class="field"><label>Target start</label>
            <select name="target_start"><option>Within 30 days</option><option>1–3 months</option><option>Exploring</option></select></div>
        </div>
        <div class="field"><label>Anything else?</label><textarea name="notes" rows="2" placeholder="Context that helps us help you"></textarea></div>
        <div class="field" style="position:absolute;left:-9999px"><input name="website_hp" tabindex="-1" autocomplete="off"></div>
        <button type="submit" class="btn btn-blue btn-big">Request access →</button>
        <div style="font-size:13px;color:var(--muted);margin-top:12px">No card. No trial clock. A human reads this.</div>
        <div id="agmsg" style="font-size:14px;margin-top:10px"></div>
      </form>
    </div></section>
    <script>
    function agsubmit(e){{e.preventDefault();var f=document.getElementById('agform');var fd=new FormData(f);
      var mk=fd.getAll('marketplaces').join(', '), ad=fd.getAll('ad_platforms').join(', ');
      fd.delete('marketplaces');fd.delete('ad_platforms');fd.set('marketplaces',mk);fd.set('ad_platforms',ad);
      fetch('/api/agencies/intake',{{method:'POST',body:fd}}).then(function(r){{return r.json().catch(function(){{return{{}}}}).then(function(d){{
        if(r.ok&&d.status_url){{location.href=d.status_url;}}
        else{{document.getElementById('agmsg').textContent=(d&&d.error)||'Please check the required fields.';}}}});}});
      return false;}}
    </script>"""
    return ui.doc("Realify for Agencies", body, active="agencies")


# ---- applicant confirmation / status page (mockup screen 2) ----
# Breadcrumb states are hyphenated for reading ("in-review"); the step list + status pill echo the
# raw state-machine values ("in_review") so both the R1 rendered-UI copy and behavior tests hold.
_STEP_LABEL = {"received": "Received", "in_review": "In review", "decision": "Decision", "live": "Live"}


def status_page(ref, status, timeline, decline_reason=None):
    def step(t):
        st = t["state"]
        dot = {"done": "var(--green)", "current": "var(--blue)", "declined": "var(--red)"}.get(st, "var(--line)")
        lab = _STEP_LABEL.get(t["step"], t["step"])
        return (f'<li style="display:flex;align-items:center;gap:12px;padding:10px 0">'
                f'<span style="width:12px;height:12px;border-radius:50%;background:{dot};flex:0 0 auto"></span>'
                f'<b>{lab}</b><span class="tag" style="margin-left:auto">{ui.esc(t["step"])} · {ui.esc(st)}</span></li>')
    steps = "".join(step(t) for t in timeline)
    decline = (f'<div class="err" style="margin-top:18px">Decision: <b>declined</b> — '
               f'{ui.esc(decline_reason or "")}</div>' if status == "declined" else "")
    body = f"""
    <section class="hero"><div class="wrap" style="max-width:720px">
      <span class="kick">Application received</span>
      <h1 style="margin-top:12px">Thanks — it's in.</h1>
      <p class="sub">Reference <b>{ui.esc(ref)}</b> · current status <span class="tag">{ui.esc(status)}</span></p>
      <p style="color:var(--muted);font-size:14px">received &rarr; in-review &rarr; decision &rarr; live</p>
      <div class="card" style="margin-top:22px"><ol style="list-style:none;margin:0;padding:0">{steps}</ol>{decline}</div>
      <p style="margin-top:20px"><b>A human reads this</b> — we'll get back to you within 2 business days.
      No card, no trial clock.</p>
    </div></section>"""
    return ui.doc(f"Application {ref}", body, active="agencies")


def status_not_found():
    body = ('<section class="hero"><div class="wrap" style="max-width:640px">'
            '<span class="kick">Application received</span>'
            "<h1 style='margin-top:12px'>We couldn't find that reference.</h1>"
            '<p class="sub">Check the link from your confirmation email, or '
            '<a href="/agencies#apply">apply again</a>. A human reads this.</p></div></section>')
    return ui.doc("Application not found", body, active="agencies")
