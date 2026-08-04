"""Beta /platform page (spec §7c) — hero, six capability tabs with live metric panels, how-it-works,
security, and the CTA band."""
from . import ui

# (name, description, [features], metric_label, [(k, v, tag)])
TABS = [
    ("Pricing",
     "Defend margins and win the buy box on autopilot. Monitors competing brands 24/7, adjusting prices "
     "within your guardrails to maximize profit.",
     ["Real-time competitor price monitoring across every connected marketplace",
      "Rules-based repricing with configurable margin floors, ceilings, and exclusions",
      "Promotional price scheduling and campaign overrides",
      "Full audit log per SKU, per channel, per minute"],
     "Live pricing snapshot",
     [("ASIN B08XYZ · Buy Box", "$34.99", "Won"), ("Competitor floor", "$33.20", "Monitoring"),
      ("Your margin floor", "$29.50", "Guardrail"), ("Price actions today", "14", "Auto"),
      ("Margin preserved", "+$412", "↑8.2%")]),
    ("Inventory",
     "Logistics with financial precision. Monitors sales velocity and lead times to draft purchase orders "
     "before SKUs stock out.",
     ["Unified stock view across every connected warehouse and 3PL",
      "Demand-weighted replenishment recommendations per SKU per location",
      "Stockout risk alerts with lead-time context",
      "Slow-moving stock identification and reallocation suggestions"],
     "Inventory health",
     [("Total SKUs tracked", "847", "Live"), ("At-risk stockouts", "3", "Action needed"),
      ("POs drafted this week", "7", "Pending review"), ("Overstock flagged", "12 SKUs", "Realloc. ready")]),
    ("Advertising",
     "Paid acquisition that scales profit, not traffic. Tracks margin-adjusted ROAS to scale converting "
     "campaigns and eliminate waste.",
     ["Search, sponsored, and display campaigns managed across all connected ad platforms",
      "Profitability-weighted bid adjustments per keyword per SKU",
      "Automatic search term harvesting and negative-keyword curation",
      "Budget pacing that accounts for stock — no spend on out-of-stock SKUs"],
     "Ad performance this week",
     [("Total ad spend", "$4,820", "On pace"), ("Margin-ROAS", "3.8×", "↑ vs last week"),
      ("Campaigns optimized", "24", "Auto"), ("Wasted spend eliminated", "$640", "Saved")]),
    ("Intelligence",
     "Competitive signals before they cost you. Surfaces competitor pricing changes, listing edits, and "
     "promotions on the SKUs and brands you track.",
     ["Tracking on competitors you select, per listing, per marketplace",
      "Price, imagery, title, and bullet change detection",
      "Promotion and coupon detection on tracked competitors",
      "Share-of-voice tracking in sponsored and organic search"],
     "Competitor activity — last 24h",
     [("Brands monitored", "18", "Active"), ("Price changes detected", "34", "Flagged"),
      ("New promotions", "5", "Watch"), ("Listing edits tracked", "11", "Logged")]),
    ("Forecasting",
     "Demand forecasts you can actually plan against — combining sales velocity, search trends, "
     "seasonality, ad spend, and competitive dynamics.",
     ["SKU-level demand forecasts with confidence intervals",
      "Seasonality modeling based on your category, not category averages",
      "Promotional uplift forecasting for planned campaigns",
      "Lead-time-aware reorder point recommendations"],
     "Q3 forecast preview",
     [("Units forecast (30d)", "2,840", "High confidence"), ("Seasonal uplift expected", "+22%", "Jul–Aug"),
      ("Reorder point — top SKU", "Aug 4", "Act soon"), ("Stockout risk prevented", "6 SKUs", "Covered")]),
    ("Execution",
     "Automation you can audit. Rules you control. Every action writes to a log and is reversible. "
     "High-impact decisions queue for your approval.",
     ["Rule builder with thresholds, exclusions, approval gates, and schedules",
      "Command Center approval queue for high-impact decisions",
      "Complete audit log — every action, every reason",
      "Execution Dial — set agent autonomy per capability, from manual to fully autonomous"],
     "Command Center",
     [("Actions executed (7d)", "1,204", "Auto-approved"), ("Pending your review", "3", "In queue"),
      ("Rollbacks this month", "0", "Clean"), ("Audit log entries", "8,410", "Searchable")]),
]

STEPS = [
    ("01", "Connect your channels", "Connect your selling account in minutes. Realify ingests your catalog, "
     "inventory, pricing, and ad data through official APIs — no scraping."),
    ("02", "Your business, mapped", "Realify learns how your business operates — products, margins, "
     "competitive context, seasonal patterns. Initial insights surface within 24 hours."),
    ("03", "Recommendations, then action", "AI surfaces opportunities and risks. You review, approve, or "
     "adjust from a single queue. Actions execute across channels automatically."),
    ("04", "Compounding intelligence", "Every decision feeds the system. Cross-channel patterns emerge. "
     "The system gets better the longer you use it."),
]

BADGES = ["Official API access only", "TLS 1.2+ in transit", "AES-256 at rest",
          "GDPR · CCPA · DPDPA ready", "Full audit trail + 1-click rollback"]


def _tabs():
    btns, panes = [], []
    for i, (name, desc, feats, mlabel, rows) in enumerate(TABS):
        on = " on" if i == 0 else ""
        btns.append(f'<button class="{on.strip()}" data-t="{i}" onclick="pt({i})">{ui.esc(name)}</button>')
        fl = "".join(f"<li>{ui.esc(f)}</li>" for f in feats)
        mr = "".join(f'<div class="mrow"><span class="mk">{ui.esc(k)}</span>'
                     f'<span class="mv">{ui.esc(v)}<span class="mt">{ui.esc(t)}</span></span></div>' for k, v, t in rows)
        panes.append(f'<div class="tabpane{on}" id="tp{i}">'
                     f'<div><h3>{ui.esc(name)}</h3><p class="sub" style="font-size:15px;margin-top:8px">{ui.esc(desc)}</p>'
                     f'<ul class="feat">{fl}</ul></div>'
                     f'<div class="metric"><div class="label" style="color:#64748b;margin-bottom:8px">{ui.esc(mlabel)}</div>{mr}'
                     f'<div style="margin-top:10px"><span class="pill">illustrative</span></div></div></div>')
    return f'<div class="tabs">{"".join(btns)}</div>{"".join(panes)}'


def platform_page():
    steps = "".join(f'<div class="card step"><div class="n">{n}</div><h3 style="margin:8px 0 6px">{ui.esc(t)}</h3>'
                    f'<p style="color:var(--ink2);font-size:14px">{ui.esc(d)}</p></div>' for n, t, d in STEPS)
    chips = "".join(f'<span class="chip"><b>✓</b> {ui.esc(b)}</span>' for b in BADGES)
    body = f"""
    <section class="hero-video" style="margin:14px 0 0;padding:0 24px;line-height:0">
      <div style="position:relative;max-width:1080px;margin:0 auto;border-radius:14px 14px 0 0;overflow:hidden">
        <video src="/assets/realify_hero_v3.mp4" autoplay muted loop playsinline preload="auto"
               aria-label="Realify"
               style="width:100%;height:auto;max-height:52vh;object-fit:cover;display:block"></video>
        <div style="position:absolute;left:0;right:0;bottom:-1px;height:96px;pointer-events:none;
                    background:linear-gradient(to bottom,rgba(244,246,249,0),var(--bg))"></div>
      </div>
    </section>

    <section class="hero" style="padding-top:0;margin-top:-30px;border-bottom:none;position:relative;
             background:radial-gradient(130% 72% at 50% -8%, rgba(46,104,230,.09), rgba(244,246,249,0) 62%)">
      <div class="wrap">
      <span class="tag" style="background:#fff;border:1px solid var(--line);box-shadow:0 6px 18px rgba(18,28,48,.12);
            position:relative;z-index:2;color:var(--blue)">Autonomous Merchandising System</span>
      <h1 style="margin:18px 0 14px;max-width:820px">One platform. Six coordinated capabilities.</h1>
      <p class="sub">Realify unifies pricing, inventory, advertising, intelligence, forecasting, and execution
      on a single data layer — across every channel you sell on.</p>
      <div class="row"><a href="/pricing" class="btn btn-blue">Start 30-day free trial</a>
      <a href="mailto:hello@realify.ai" class="btn btn-ghost">Request demo</a></div>
    </div></section>

    <section class="soft"><div class="wrap">
      <div class="label">Capabilities</div><h2>Everything your operations need. Nothing it doesn't.</h2>
      {_tabs()}
    </div></section>

    <section><div class="wrap">
      <div class="label">How it works</div><h2>Connected in minutes. Compounding in weeks.</h2>
      <div class="grid g4" style="margin-top:22px">{steps}</div>
    </div></section>

    <section class="soft"><div class="wrap">
      <div class="label">Security &amp; Trust</div><h2>Built for operators who can't afford surprises.</h2>
      <p class="sub">Realify connects through official marketplace APIs only. Your data is encrypted, isolated at
      the account level, and never shared with other sellers.</p>
      <div style="margin-top:18px">{chips}</div>
    </div></section>

    <section><div class="wrap">
      <div class="card" style="display:flex;justify-content:space-between;align-items:center;gap:30px;flex-wrap:wrap">
        <div>
          <span class="kick">New · Pilot program</span>
          <h3 style="font-family:var(--serif);font-size:24px;margin:8px 0 6px">Run client accounts? Realify for Agencies.</h3>
          <p style="margin:0;color:var(--ink2);font-size:14.5px;max-width:60ch">One decision queue across your
          whole book, client-granted permissions, and reports whose numbers verify themselves. In pilot with
          selected partners.</p>
        </div>
        <a class="btn btn-blue" href="/agencies">See Realify for Agencies →</a>
      </div>
    </div></section>

    <div class="ctaband"><div class="wrap">
      <h2>Ready to stop reconciling and start operating?</h2>
      <p class="sub" style="margin:0 auto">30 days free. Your actual marketplace data. No sandbox.</p>
      <div class="row" style="justify-content:center"><a href="/pricing" class="btn btn-blue">Start your free trial</a></div>
    </div></div>
    <script>function pt(i){{document.querySelectorAll('.tabs button').forEach(function(b){{b.classList.toggle('on',b.dataset.t==i);}});
      document.querySelectorAll('.tabpane').forEach(function(p,j){{p.classList.toggle('on',j==i);}});}}</script>"""
    return ui.doc("Platform — Realify", body, active="platform")
