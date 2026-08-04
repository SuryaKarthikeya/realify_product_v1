"""In-app subscription components: SubscriptionBadge, TrialBanner, PaymentBanner, BillingGate. Rendered
into the auth-gated app chrome (not the marketing nav). Pure view helpers; trial math comes from
realify.billing. billing_gate() is served at /billing for canceled/unpaid tenants."""
from . import ui
from .. import billing

_BANNER = "padding:10px 20px;font-size:13.5px;display:flex;justify-content:space-between;align-items:center;gap:12px"


def subscription_badge(user, days):
    st = (user or {}).get("subscription_status")
    if st == "trialing":
        if days is not None and days <= 7:
            return (f'<a href="/billing" class="badge b-amber">Trial — {days} days left · Upgrade →</a>')
        return f'<span class="badge b-amber">Trial — {days} days left</span>' if days is not None else ''
    if st == "active":
        return ''
    if st == "past_due":
        return '<span class="badge b-red">⚠ Payment failed</span>'
    if st in ("canceled", "unpaid"):
        return '<a href="/pricing" class="badge" style="background:var(--blue);color:#fff">Reactivate</a>'
    return ''


def trial_banner(user, days):
    if (user or {}).get("subscription_status") != "trialing" or days is None or days > 14:
        return ''
    end = ui.esc(user.get("trial_ends_at") or "")
    return (f'<div id="betaTrialBanner" style="{_BANNER};background:#fffbeb;color:#b45309;border-bottom:1px solid #fde68a">'
            f'<span>Your trial ends {end}. After that, $20/month — no action needed if your card is on file.</span>'
            f'<span><a href="#" onclick="betaPortal();return false" style="color:#b45309;font-weight:600">Manage billing</a>'
            f'&nbsp;&nbsp;<a href="#" id="betaTBx" style="color:#b45309;font-weight:700;text-decoration:none">×</a></span></div>'
            f'<script>(function(){{var d={days};var b=document.getElementById("betaTrialBanner");'
            f'var x=document.getElementById("betaTBx");if(x)x.onclick=function(e){{e.preventDefault();b.remove();'
            f'try{{localStorage.setItem("beta_trial_banner_dismissed","1")}}catch(_){{}}}};'
            f'if(d>3){{try{{if(localStorage.getItem("beta_trial_banner_dismissed")==="1")b.remove()}}catch(_){{}}}}}})();</script>')


def payment_banner(user):
    if (user or {}).get("subscription_status") != "past_due":
        return ''
    return (f'<div style="{_BANNER};background:#fef2f2;color:#dc2626;border-bottom:1px solid #fecaca">'
            f'<span>⚠ Your last payment failed. Update your card to avoid losing access.</span>'
            f'<a href="#" onclick="betaPortal();return false" style="color:#dc2626;font-weight:700">Update payment method →</a></div>')


def billing_gate(user):
    body = (f'<div class="authwrap"><div class="authcard" style="text-align:center">'
            f'<div style="margin-bottom:14px">{ui.logo()}</div>'
            f'<h2>Your access has ended.</h2>'
            f'<p style="color:var(--ink2);font-size:14px;margin:12px 0 20px">Reactivate for $20/month to pick up '
            f'where you left off.</p><a href="/pricing" class="btn btn-blue btn-wide">Reactivate →</a></div></div>')
    return ui.doc("Access ended — Realify", body, nav=False)


def _app_topbar(user, days):
    badge = subscription_badge(user, days)
    return (f'<div class="nav"><div class="wrap"><a href="/" style="text-decoration:none">{ui.logo()}</a>'
            f'<div class="cta">{badge}<a href="/billing" class="btn btn-ghost">Billing</a>'
            f'<a href="#" onclick="betaLogout();return false" class="btn btn-ghost">Sign out</a></div></div></div>')


def dashboard_page(user):
    days = billing.days_remaining(user)
    if (user or {}).get("subscription_status") in ("canceled", "unpaid"):
        return billing_gate(user)
    content = (f'<div class="wrap" style="padding:48px 24px">'
               f'<div class="label">Dashboard</div><h2 style="margin-top:6px">Welcome to Realify.</h2>'
               f'<p class="sub">Your operations workspace. Connect a channel to begin — pricing, inventory, '
               f'advertising, intelligence, forecasting, and execution appear here as data flows in.</p>'
               f'<div class="grid g3" style="margin-top:24px">'
               f'<div class="card"><h3>Connect a channel</h3><p style="color:var(--ink2);font-size:14px;margin-top:6px">'
               f'Link your selling account through official APIs — no scraping.</p></div>'
               f'<div class="card"><h3>Your subscription</h3><p style="color:var(--ink2);font-size:14px;margin-top:6px">'
               f'Plan, trial, invoices and cancellation live in <a href="/billing">Billing</a>.</p></div>'
               f'<div class="card"><h3>Full app</h3><p style="color:var(--ink2);font-size:14px;margin-top:6px">'
               f'The operations app mounts here once the beta ports to the main product.</p></div></div></div>')
    scripts = ('<script>async function betaPortal(){var r=await fetch("/api/billing/portal");var j=await r.json();'
               'if(j.portal_url)location.href=j.portal_url;else alert((j&&j.error)||"Billing unavailable.");}'
               'async function betaLogout(){await fetch("/api/logout",{method:"POST"});location.href="/signin";}</script>')
    body = _app_topbar(user, days) + trial_banner(user, days) + payment_banner(user) + content + scripts
    return ui.doc("Dashboard — Realify", body, nav=False)
