"""/faq page — the product FAQs ported from the former login-flow landing (login.html). Rendered in the
marketing site's accordion style. Answers are trusted static HTML (kept the <b> emphasis); the small
muted line under some answers preserves the original visual's caption."""
from . import ui

# (question, answer_html, optional caption). Answer HTML is static/trusted — the <b> tags are intentional.
FAQ = [
    ("I sell on Amazon, Shopify, Walmart, and more. How does Realify help me?",
     "You already have the data — it's just scattered across a dozen dashboards and exports, and the signal "
     "that matters is buried in it. Realify reads your channels and surfaces the handful of things worth acting "
     "on <b>today</b>: a SKU quietly slipping below its margin floor, buy box you're losing, inventory about to "
     "stock out before your next reorder lands, returns creeping up, ad spend outrunning its return. Each issue "
     "arrives as a prioritized card with the numbers behind it and a recommended move. It's the difference "
     "between <b>reacting</b> to last month's report and <b>acting</b> on this week's risk — across every "
     "channel, in one place.",
     "A prioritized feed — most material issue first."),
    ("How does Realify work?",
     "Two layers, deliberately separated. A <b>deterministic engine does the math — and uses ML models — on your "
     "numbers</b> against your thresholds (margins, cover, buy box, velocity, returns, ad efficiency) to decide "
     "what's worth flagging and to forecast where each metric is heading. Then a language layer explains each "
     "finding in plain English and drafts the action. The decisions are never guessed by an AI; they come from "
     "rules and models you can see and tune. You connect your data, Realify computes the signals, and you get a "
     "ranked feed — each card openable to show exactly <b>why</b> it fired, down to the rule and the value that "
     "tripped it. Nothing is a black box.",
     "Math &amp; models decide · language only phrases."),
    ("How is Realify different from the others?",
     "Most tools are single-purpose: one for keywords, one for repricing, one for ads — each sees a slice. "
     "Realify's advantage is <b>cross-signal</b>: it reasons about margin, inventory, buy box, and ad efficiency "
     "together, because in reality those decisions are entangled (dropping price to win buy box can quietly sink "
     "margin; a stockout warps your ad ROI). And unlike bolting a chatbot onto your data, every number is "
     "deterministic and <b>auditable</b> — you can trace any insight to the rule and figure behind it, so you can "
     "trust it enough to act. It compounds, too: the longer it watches your operation, the better it understands "
     "what \"normal\" looks like for your catalog.",
     "Every card opens to its full reasoning trace."),
    ("How do I try Realify before onboarding my real data?",
     "Start as a <b>Tester</b> — no real data required. Load the built-in demo catalog, or just paste an ASIN "
     "list and Realify generates a realistic dataset so you can explore the full product: the feed, the insight "
     "cards, the explainability, the works. When you're convinced, create a <b>Customer</b> account and connect "
     "your real reports and costs. Testing is risk-free and reversible — your real data only enters when you choose.",
     None),
    ("Is my data private and secure?",
     "Your data is isolated to your organization and never shared or pooled with other sellers. Realify reads "
     "only what you connect, and you can <b>permanently delete</b> your account and all its data at any time, "
     "from the account settings.",
     None),
    ("Does Realify scrape Amazon or risk my marketplace account?",
     "No. Realify uses <b>official APIs and licensed market data</b> (Keepa) — never scraping. It's built to keep "
     "you compliant, not to put your seller account at risk.",
     None),
    ("What do I need to get started?",
     "At minimum, a product/catalog export and your cost-of-goods (COGS) — that's enough to start surfacing "
     "margin insights. From there, every additional report you connect (sales, inventory, returns, ads) lights up "
     "more of the engine. You see exactly what's active and what each new upload unlocks.",
     "3 of 5 detectors active — add inventory to unlock cover alerts."),
    ("Does Realify make changes to my store on its own?",
     "No — you stay in control. Realify surfaces decisions and drafts the recommended action, but <b>you approve "
     "what happens</b>. It's a co-pilot for your merchandising and ops team, not an autopilot acting behind your back.",
     None),
    ("Can my whole team use one account?",
     "Yes. Create an organization and invite teammates — everyone works from the same data and the same "
     "prioritized feed. Generate an invite, send it, and they join your organization in a couple of clicks.",
     None),
]


def _answer(html, cap):
    note = (f'<span style="display:block;margin-top:10px;font-size:12px;color:var(--muted)">{cap}</span>'
            if cap else '')
    return f"{html}{note}"


def faq_page():
    items = "".join(
        f'<details{" open" if i == 0 else ""}><summary>{ui.esc(q)}<span>+</span></summary>'
        f'<p>{_answer(a, cap)}</p></details>'
        for i, (q, a, cap) in enumerate(FAQ))
    body = f"""
    <section class="hero"><div class="wrap" style="text-align:center">
      <span class="tag">FAQ</span>
      <h1 style="margin:18px 0 14px">Questions? Answers.</h1>
      <p class="sub" style="margin:0 auto">What Realify does, how it works, and how to try it before you
      commit your data.</p>
    </div></section>

    <section><div class="wrap" style="max-width:820px">
      <div class="faq">{items}</div>
    </div></section>

    <div class="ctaband"><div class="wrap">
      <h2>Still have questions?</h2>
      <p class="sub" style="margin:0 auto">Start a 30-day free trial and see it on your own data, or reach us
      at <a href="mailto:hello@realify.ai">hello@realify.ai</a>.</p>
      <div class="row" style="justify-content:center"><a href="/signup" class="btn btn-blue">Start your free trial</a></div>
    </div></div>"""
    return ui.doc("FAQ — Realify", body, active="faq")
