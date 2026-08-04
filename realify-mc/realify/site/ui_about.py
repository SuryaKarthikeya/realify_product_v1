"""Beta /about page (spec §7e) — hero, stats, the problem, beliefs, founder card, principles, CTA."""
from . import ui

STATS = [("6+", "Coordinated agents"), ("24/7", "Autonomous monitoring"),
         ("4+", "Marketplaces supported"), ("0%", "GMV or ad spend fees")]

BELIEFS = ["Automation without visibility is a liability, not a feature.",
           "Every action should be explainable, reversible, and logged.",
           "Flat pricing aligns our incentives with yours — we win when you grow.",
           "A system should get smarter the longer you run it.",
           "Operators deserve the same intelligence enterprise brands pay millions for."]

PRINCIPLES = [
    ("🔒", "Absolute operator control", "Nothing executes without your approval. Every automation runs within "
     "rules you define. High-impact decisions queue for explicit greenlight before execution."),
    ("🔍", "Full transparency", "Every autonomous action writes to a single, searchable audit log. Every "
     "decision has a reason. One-click rollback on anything the system has ever done."),
    ("🔗", "Official APIs only", "We connect through authorized OAuth programs only. No scraping, no "
     "workarounds, no shared passwords. Your data flows through verified, official channels."),
    ("📈", "Compounding intelligence", "Every decision feeds the system. Cross-channel patterns emerge over "
     "time. The longer you run Realify, the sharper your operations get."),
]


def about_page():
    stats = "".join(f'<div><div style="font-size:34px;font-weight:800;color:var(--blue)">{ui.esc(n)}</div>'
                    f'<div style="color:var(--ink2);font-size:14px">{ui.esc(l)}</div></div>' for n, l in STATS)
    beliefs = "".join(f"<li>{ui.esc(b)}</li>" for b in BELIEFS)
    principles = "".join(f'<div class="card"><h3>{ui.esc(i)} {ui.esc(t)}</h3>'
                         f'<p style="color:var(--ink2);font-size:14px;margin-top:8px">{ui.esc(d)}</p></div>'
                         for i, t, d in PRINCIPLES)
    body = f"""
    <section class="hero"><div class="wrap">
      <span class="tag">Our story</span>
      <h1 style="margin:18px 0 14px">Built by operators, for operators.</h1>
      <p class="sub">Realify was built because the tools multi-channel brands needed to run a tight operation
      didn't exist. So we built them.</p>
      <div class="card grid g4" style="margin-top:28px;text-align:center">{stats}</div>
    </div></section>

    <section class="soft"><div class="wrap grid g2" style="align-items:start">
      <div><div class="label">The problem we solve</div><h2>Commerce stacks were never built to work together.</h2>
      <p style="color:var(--ink2);font-size:15px;margin-top:10px">You started with one channel and one tool. Then a
      second marketplace. Then a repricer. Then a PPC manager. Then an inventory sheet. Six months later, eight
      tools that don't talk to each other. Every marketplace ships its own dashboard. Every function ships its own
      vendor. Every report ships its own definition of revenue. Your team spends more time reconciling than
      operating. Realify is what you would have built — if you'd had the time, the engineering team, and the data
      science capability to do it.</p></div>
      <div class="card"><h3>What we believe</h3><ul class="feat">{beliefs}</ul></div>
    </div></section>

    <section><div class="wrap"><div class="label">Founder</div>
      <div class="card" style="display:flex;gap:22px;align-items:flex-start;margin-top:16px;flex-wrap:wrap">
        <div style="flex:0 0 84px;width:84px;height:84px;border-radius:50%;background:linear-gradient(135deg,#2563eb,#7c3aed);
          color:#fff;display:flex;align-items:center;justify-content:center;font-size:34px;font-weight:800">S</div>
        <div style="flex:1;min-width:260px">
          <h3 style="font-size:22px">Shiva</h3>
          <div style="color:var(--blue);text-transform:uppercase;font-size:12px;font-weight:700;letter-spacing:.05em;margin:4px 0 12px">Co-Founder · Head of Product</div>
          <p style="color:var(--ink2);font-size:14.5px">20+ years building the systems others rely on at scale — core
          services at AWS, and the AI/ML infrastructure powering Prime Video. At Amazon, Shiva operated as a senior
          leader directing cross-functional teams across product, engineering, operations, and data science, solving
          problems most companies never encounter.</p>
          <p style="color:var(--ink2);font-size:14.5px;margin-top:10px">He co-founded Realify because he kept seeing the
          same problem: brands drowning in data but starving for execution. Disconnected systems, missed signals,
          gut-feel decisions. That's a solvable problem — and Realify is solving it. Not dashboards. Not reports.
          Executable intelligence.</p>
          <div style="color:var(--muted);font-size:13px;margin-top:14px">🎓 MBA · Duke University&nbsp;&nbsp;&nbsp;🎓 MS Information Systems · University of Florida</div>
        </div>
      </div>
    </div></section>

    <section class="soft"><div class="wrap">
      <div class="label">Our principles</div><h2>How we build. How we operate.</h2>
      <div class="grid g2" style="margin-top:22px">{principles}</div>
    </div></section>

    <div class="ctaband"><div class="wrap">
      <h2>Come build the future of commerce operations.</h2>
      <p class="sub" style="margin:0 auto">We're onboarding new teams on a rolling basis. Most connect within a week.</p>
      <div class="row" style="justify-content:center"><a href="/pricing" class="btn btn-blue">Start your free trial</a></div>
    </div></div>"""
    return ui.doc("About — Realify", body, active="about")
