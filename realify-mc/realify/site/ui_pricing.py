"""Beta /pricing page (spec §7d) — hero, price anchor card, six feature-group cards, FAQ, CTA."""
from . import ui

# (name, kicker, items) — kicker is a mono uppercase eyebrow (design system), replacing the old emoji headers.
GROUPS = [
    ("Market Intelligence", "Intel",
     ["24/7 competitor price monitoring across connected marketplaces", "Buy box win/loss tracking per ASIN",
      "Listing change detection — title, images, bullets, price", "Competitor promotion and coupon detection",
      "Share-of-voice tracking in sponsored and organic search"]),
    ("Autonomous Agents", "Agents",
     ["Pricing Agent — repricing within margin floors and ceilings you set",
      "Instock Agent — monitors velocity and lead times, drafts POs",
      "Ads Optimizer — margin-ROAS bid management across campaigns",
      "Forecast Engine — SKU-level demand forecasting with confidence intervals",
      "Seasonality and promotional uplift modeling"]),
    ("Execution & Control", "Control",
     ["Command Center — approval queue for high-impact decisions",
      "Execution Dial — set autonomy per agent from manual to fully auto",
      "Rule builder — thresholds, exclusions, approval gates, schedules",
      "Full audit log — every action, every reason, searchable", "1-click rollback on any automated action"]),
    ("Data & Channels", "Data",
     ["Official OAuth API connections — no scraping, no workarounds",
      "Unified inventory view across warehouses and 3PLs", "Single data layer across all connected channels",
      "Real-time sync — catalog, pricing, inventory, ad data", "Multi-channel execution from one interface"]),
    ("Security & Compliance", "Security",
     ["TLS 1.2+ encryption in transit", "AES-256 encryption at rest",
      "Account-level data isolation — never shared across sellers", "GDPR, CCPA, and DPDPA compliant",
      "Role-based access controls"]),
    ("Billing & Account", "Billing",
     ["30-day free trial — full access, no sandbox", "Flat $20/month — no GMV or ad spend percentage",
      "Cancel anytime from self-serve billing portal", "Email reminder 3 days before trial ends",
      "Access continues through end of billing period on cancel"]),
]

FAQ = [
    ("Is there really a 30-day free trial?",
     "Yes — full access, your actual marketplace data, not a sandbox. Your card is required at signup but "
     "won't be charged until day 31. Cancel any time before then and you'll never be billed."),
    ("Why do you require a card for the trial?",
     "It removes friction at the end of your trial and ensures uninterrupted access on day 31. We send a "
     "reminder 3 days before your trial ends, and you can cancel in one click from your account settings at any time."),
    ("Do you charge a percentage of GMV or ad spend?",
     "No. $20/month is your total Realify cost. We don't take a cut of your revenue, advertising spend, or "
     "managed GMV — ever."),
    ("Are all features available during the trial?",
     "Yes. There's no feature gating between the trial and paid plan. You get the full system from day one — "
     "every agent, every capability, real data."),
    ("Can I cancel anytime?",
     "Yes — one click from your billing settings. Your access continues until the end of the current billing "
     "period. No questions, no cancellation fees."),
    ("What counts as a SKU?",
     "Each unique product variant across all connected channels. A shirt in 3 sizes and 2 colours is 6 SKUs. "
     "The same SKU sold on Shopify and Amazon counts as one SKU, not two."),
    ("Do you have pricing for agencies?",
     "Realify for Agencies is a separate pilot program for teams running multiple brand accounts. There's no "
     "public agency price — pricing is scoped at the pilot call, after we understand your book. Tell us about "
     "your agency on the For Agencies page."),
]


def pricing_page():
    groups = "".join(
        f'<div class="card"><span class="kick">{ui.esc(kick)}</span>'
        f'<h3 style="margin:8px 0 10px">{ui.esc(name)}</h3>'
        f'<ul class="feat">{"".join(f"<li>{ui.esc(x)}</li>" for x in items)}</ul></div>'
        for name, kick, items in GROUPS)
    # No literal "+" marker — the accordion's disclosure caret is drawn by CSS (.faq summary).
    faq = "".join(f'<details><summary>{ui.esc(q)}</summary><p>{ui.esc(a)}</p></details>' for q, a in FAQ)
    # "For Agencies" cross-link — always present (the /agencies marketing page renders regardless of the
    # AGENCY_CONSOLE flag). No public agency price: pricing is scoped at the pilot call.
    agencies = """
    <section class="soft"><div class="wrap" style="max-width:760px;text-align:center">
      <span class="kick">For Agencies</span><h2>Run a book of client accounts?</h2>
      <p class="sub">Realify for Agencies is a separate pilot program — manage multiple brand accounts under one
      console, with client-granted permissions and verified reporting. There's no public agency price;
      pricing is scoped at the pilot call. <a href="/agencies">See Realify for Agencies →</a></p>
    </div></section>"""
    body = f"""
    <section class="hero"><div class="wrap">
      <span class="tag">Simple pricing</span>
      <h1 style="margin:18px 0 14px">Everything included. 30 days free.</h1>
      <p class="sub">One plan. Every feature. No usage fees, no GMV cut, no ad spend percentage. Try free for
      30 days — your card won't be charged until day 31.</p>
    </div></section>

    <section><div class="wrap">
      <div class="card pricecard">
        <span class="tag">Full access</span>
        <div class="amt" style="margin-top:14px">$20 <span>/ month</span></div>
        <div class="greenbox"><b>30-day free trial included</b> — Card required at signup · charged only if you stay past day 31</div>
        <a href="/signup" class="btn btn-blue btn-wide">Start free trial →</a>
        <div style="color:var(--muted);font-size:13px;margin-top:12px">Cancel anytime. No questions. No fees.</div>
      </div>
    </div></section>

    <section class="soft"><div class="wrap">
      <div class="label">What's included</div><h2>Every feature. From day one.</h2>
      <p class="sub">No feature gating between trial and paid. You get the full system on day one and keep it as
      long as you subscribe.</p>
      <div class="grid g3" style="margin-top:24px">{groups}</div>
    </div></section>

    <section><div class="wrap" style="max-width:760px">
      <div class="label">FAQ</div><h2>Pricing questions, answered.</h2>
      <div class="faq" style="margin-top:16px">{faq}</div>
    </div></section>
    {agencies}
    <div class="ctaband"><div class="wrap">
      <h2>Everything. 30 days free.</h2>
      <p class="sub" style="margin:0 auto">Full access from day one. Card won't be charged until day 31.</p>
      <div class="row" style="justify-content:center"><a href="/signup" class="btn btn-blue">Start your free trial</a></div>
    </div></div>"""
    return ui.doc("Pricing — Realify", body, active="pricing")
