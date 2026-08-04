"""Beta public-shell UI (spec §7) — shared layout (design tokens, nav, footer) + the smaller pages
(signin, signup, welcome, settings/billing). Server-rendered HTML strings in the spec's own marketing
design language (white / #2E68E6), distinct from the app. All internal links are main-app paths."""
import html as _h
from .tokens import TOKENS as _TOKENS

# Real Realify wordmark, served LOCALLY from /assets (R11.1 — never hotlinked from the marketing
# domain). Ink on light surfaces, white on dark. Sized by height (~3.82:1) so it fits nav, not giant.
_WORDMARK_INK = "/assets/Final-logo-full-Dark-V3.png"
_WORDMARK_WHITE = "/assets/Final-logo-full-white-V3.png"


def logo(dark=False):
    src = _WORDMARK_WHITE if dark else _WORDMARK_INK
    return f'<img class="logo" src="{src}" alt="Realify" style="height:24px;width:auto;vertical-align:middle">'


CSS = "\n*{box-sizing:border-box;margin:0;padding:0}\n" + _TOKENS + """
html,body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--blue);text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
.logo{font-family:var(--serif);font-weight:700;font-size:21px;letter-spacing:-.02em}
.logo .dot{color:var(--blue)}
.nav{position:sticky;top:0;z-index:50;background:rgba(247,244,238,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.nav .wrap{display:flex;align-items:center;justify-content:space-between;height:66px}
.nav .links{display:flex;gap:26px}.nav .links a{color:var(--ink2);font-size:14px;font-weight:500}
.nav .links a.on{color:var(--ink);font-weight:700}
.nav .cta{display:flex;gap:10px;align-items:center}
.btn{display:inline-block;border:none;border-radius:9px;padding:11px 20px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
.btn-blue{background:var(--blue);color:#fff}.btn-blue:hover{background:var(--blue-d)}
.btn-ghost{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}
.btn-wide{width:100%}.btn-big{padding:14px 28px;font-size:15.5px}
.kick{display:inline-block;font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--blue)}
.tag{display:inline-block;font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--blue);background:#EAF1FE;border-radius:20px;padding:5px 12px}
.label{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font-family:var(--serif);font-size:46px;line-height:1.12;letter-spacing:-.015em;font-weight:700}
h2{font-family:var(--serif);font-size:30px;line-height:1.14;letter-spacing:-.015em;font-weight:700;margin:12px 0 12px}
h3{font-family:var(--serif);font-size:19px;font-weight:700}
.sub{color:var(--ink2);font-size:17.5px;max-width:62ch}
section{padding:64px 0;border-bottom:1px solid var(--line)}
section.soft{background:var(--soft)}
section.dark{background:var(--ink);color:#D8DCE4;border-color:#2A2E36}
section.dark h1,section.dark h2,section.dark h3{color:#EEF1F5}
section.dark .sub,section.dark .muted{color:#8B93A1}
.hero{padding:88px 0 60px}
.row{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px;align-items:center}
.grid{display:grid;gap:16px}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}.g2{grid-template-columns:repeat(2,1fr)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px}
section.dark .card{background:#22262D;border-color:#2A2E36;color:#D8DCE4}
.card p{color:var(--ink2)}section.dark .card p{color:#8B93A1}
.metric{background:#22262D;color:#D8DCE4;border:1px solid #2A2E36;border-radius:14px;padding:20px}
.metric .mrow{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-top:1px solid #2A2E36;font-size:13.5px}
.metric .mrow:first-of-type{border-top:none}.metric .mk{color:#8B93A1}.metric .mv{font-weight:700;font-family:var(--mono)}.metric .mt{color:var(--slate);font-size:11px;margin-left:8px}
.chip{display:inline-flex;align-items:center;gap:7px;font-size:13px;color:var(--ink2);background:#fff;border:1.5px solid var(--line);border-radius:100px;padding:7px 14px;margin:5px 6px 0 0}
.chip b{color:var(--green)}.chip.sel{background:var(--ink);color:#fff;border-color:var(--ink)}
.feat{list-style:none;margin-top:12px}.feat li{position:relative;padding:6px 0 6px 22px;color:var(--ink2);font-size:14px}
.feat li:before{content:"";position:absolute;left:0;top:12px;width:8px;height:8px;border-radius:2px;background:var(--blue)}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0}
.tabs button{border:1.5px solid var(--line);background:#fff;color:var(--ink2);border-radius:9px;padding:9px 15px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
.tabs button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.tabpane{display:none}.tabpane.on{display:grid;grid-template-columns:1.1fr .9fr;gap:28px;align-items:start}
.pill{display:inline-block;font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;border-radius:100px;padding:3px 10px;background:#EAF1FE;color:#6C7482}
.steps{counter-reset:s}.step .n{font-family:var(--mono);color:var(--blue);font-weight:700}
.ctaband{text-align:center;padding:72px 0}.ctaband h2{margin-bottom:6px}
.authwrap{min-height:calc(100vh - 66px);display:flex;align-items:center;justify-content:center;background:var(--soft);padding:48px 20px}
.authcard{width:100%;max-width:420px;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:34px}
.authcard h2{font-size:26px}.authcard .sub{font-size:14px;margin-bottom:20px}
.field{margin:14px 0}.field label{display:block;font-size:13px;font-weight:600;color:var(--ink);margin-bottom:6px}
.field input,.field select,.field textarea{width:100%;border:1.5px solid var(--line);border-radius:10px;padding:12px 14px;font-size:15px;font-family:inherit;background:#fff;color:var(--ink)}
.field input:focus,.field select:focus{outline:none;border-color:var(--blue)}
.field .hint{font-size:12px;color:var(--muted);margin-top:5px}
.gbtn{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;border:1.5px solid var(--line);background:#fff;border-radius:10px;padding:11px;font-size:14px;font-weight:600;cursor:pointer;color:var(--ink)}
.divider{display:flex;align-items:center;gap:12px;color:var(--muted);font-size:12px;margin:16px 0}.divider:before,.divider:after{content:"";flex:1;height:1px;background:var(--line)}
.err{background:#FBEAE9;color:var(--red);border:1px solid #C9DBF9;border-radius:9px;padding:9px 12px;font-size:13px;margin:12px 0;display:none}
.err.show{display:block}
.foot{display:flex;justify-content:space-between;gap:14px;font-size:13px;color:var(--ink2);margin-top:16px}
.legalnote{font-size:11.5px;color:var(--muted);margin-top:16px;text-align:center}
.faq{border-top:1px solid var(--line)}.faq details{border-bottom:1px solid var(--line);padding:16px 0}
.faq summary{font-weight:600;cursor:pointer;list-style:none;display:flex;justify-content:space-between}
.faq summary::-webkit-details-marker{display:none}.faq p{color:var(--ink2);font-size:14px;margin-top:10px}
.faq summary::after{content:"+";color:var(--blue);font-weight:400;margin-left:16px}.faq details[open] summary::after{content:"–"}
.pricecard{max-width:440px;margin:0 auto;text-align:center;border:2px solid var(--ink);border-radius:18px}
.pricecard .amt{font-family:var(--serif);font-size:52px;font-weight:700;letter-spacing:-.02em}.pricecard .amt span{font-size:18px;color:var(--muted);font-weight:400;font-family:inherit}
.greenbox{background:#EDF1EA;border:1px solid #CBDCC9;color:#456A49;border-radius:10px;padding:12px 14px;font-size:13.5px;margin:16px 0}
footer{background:var(--ink);color:#99A1B0;padding:48px 0;border:none}
footer .cols{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:28px}
footer h4{color:#D8DCE4;font-size:12px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}footer a{color:#D4DAE3;font-size:13px;display:block;padding:3px 0}
footer .copy{border-top:1px solid #2A2E36;margin-top:32px;padding-top:20px;font-size:12px}
.badge{display:inline-block;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px}
.b-amber{background:#EEF1F5;color:var(--amber);border:1px solid #E7EAF0}
.b-green{background:#EDF1EA;color:#456A49;border:1px solid #CBDCC9}
.b-red{background:#FBEAE9;color:var(--red);border:1px solid #C9DBF9}
@media(max-width:820px){.g3,.g4,.g2,.tabpane.on,footer .cols{grid-template-columns:1fr}h1{font-size:34px}h2{font-size:25px}.m-nav .m-links{display:none}}
"""

_GOOGLE_SVG = ('<svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.6'
               'l6.8-6.8C35.9 2.4 30.4 0 24 0 14.6 0 6.4 5.4 2.5 13.3l7.9 6.2C12.2 13.7 17.6 9.5 24 9.5z"/>'
               '<path fill="#4285F4" d="M46.1 24.6c0-1.6-.1-3.1-.4-4.6H24v9.3h12.4c-.5 2.9-2.2 5.3-4.6 7l7.1 5.5'
               'c4.2-3.9 6.6-9.6 6.6-16.2z"/><path fill="#FBBC05" d="M10.4 28.5c-.5-1.4-.8-3-.8-4.5s.3-3.1.8-4.5'
               'l-7.9-6.2C.9 16.5 0 20.1 0 24s.9 7.5 2.5 10.7l7.9-6.2z"/><path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 '
               '15.9-5.8l-7.1-5.5c-2 1.3-4.5 2.1-8.8 2.1-6.4 0-11.8-4.2-13.6-9.9l-7.9 6.2C6.4 42.6 14.6 48 24 48z"/></svg>')


def esc(s):
    return _h.escape(str(s if s is not None else ""))


def _agency_link_on():
    """The public 'For Agencies' entry points are gated by AGENCY_CONSOLE so they vanish on rollback."""
    from ..agency.guard import agency_console_on
    return agency_console_on()


def _nav(active=None):
    # "For Agencies" is ALWAYS present (the /agencies MARKETING page renders regardless of AGENCY_CONSOLE;
    # only the functional form POST is flag-gated). Logo is a local text wordmark — no external asset.
    def lk(href, name, key):
        return f'<a href="{href}" class="{"on" if active==key else ""}">{name}</a>'
    return (f'<div class="nav"><div class="wrap"><a href="/platform" style="text-decoration:none">{logo()}</a>'
            f'<div class="links">{lk("/platform","Platform","platform")}{lk("/pricing","Pricing","pricing")}'
            f'{lk("/agencies","For Agencies","agencies")}{lk("/about","About","about")}{lk("/faq","FAQ","faq")}</div>'
            f'<div class="cta"><a href="/signin" class="btn btn-ghost">Sign in</a>'
            f'<a href="/pricing" class="btn btn-blue">Start free trial</a></div></div></div>')


def _footer():
    return ('<footer><div class="wrap"><div class="cols">'
            f'<div>{logo(dark=True)}<p style="margin-top:12px;max-width:34ch;color:#99A1B0">Profit decisions for '
            'multichannel commerce — for the brands that sell, and the agencies that run them.</p></div>'
            '<div><h4>Product</h4><a href="/platform">Platform</a><a href="/pricing">Pricing</a>'
            '<a href="/agencies">For Agencies</a><a href="/faq">FAQ</a></div>'
            '<div><h4>Legal</h4><a href="https://realify.ai/terms/">Terms of Service</a>'
            '<a href="https://realify.ai/privacy-policy/">Privacy Policy</a>'
            '<a href="https://realify.ai/acceptable-use-policy/">Acceptable Use</a></div>'
            '<div><h4>Contact</h4><a href="mailto:hello@realify.ai">hello@realify.ai</a>'
            '<a href="https://linkedin.com/company/realify-ai">LinkedIn</a></div>'
            '</div><div class="copy">© 2026 Realify.ai — All rights reserved.</div></div></footer>')


def doc(title, body, active=None, nav=True, extra_head=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="icon" type="image/png" href="/assets/Final-logo-VF-white-3.png">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>'
            f'<style>{CSS}</style>{extra_head}</head><body>'
            f'{_nav(active) if nav else ""}{body}{_footer()}</body></html>')


def _legal():
    return ('<div class="legalnote">By continuing you agree to our '
            '<a href="https://realify.ai/terms/">Terms</a> and '
            '<a href="https://realify.ai/privacy-policy/">Privacy Policy</a>.</div>')


def _google_btn():
    # OAuth not yet wired in the beta — visible but inert (TODO: wire to the app's Google OIDC at cutover)
    return f'<button type="button" class="gbtn" onclick="alert(\'Google sign-in is coming soon.\')">{_GOOGLE_SVG} Continue with Google</button>'


def signin_page():
    body = f"""<div class="authwrap"><div class="authcard">
      <a href="/platform" style="text-decoration:none;display:inline-block;margin-bottom:14px" title="Back to home">{logo()}</a>
      <h2>Welcome back</h2><div class="sub">Sign in to your Realify account</div>
      {_google_btn()}<div class="divider">or</div><div id="err" class="err"></div>
      <form id="f" onsubmit="return false">
        <div class="field"><label>Email address</label><input id="email" type="email" placeholder="you@company.com" autocomplete="email"></div>
        <div class="field"><label>Password</label><input id="pw" type="password" placeholder="••••••••" autocomplete="current-password"></div>
        <div class="foot"><label style="color:var(--ink2)"><input type="checkbox"> Remember me</label><a href="/reset">Forgot password?</a></div>
        <button class="btn btn-blue btn-wide" style="margin-top:16px" onclick="go()">Sign in</button>
      </form>
      <div class="foot" style="justify-content:center;gap:6px;margin-top:16px">Don't have an account? <a href="/signup">Start your free trial →</a></div>
      {_legal()}</div></div>
    <script>
    async function go(){{
      var e=document.getElementById('err'); e.classList.remove('show');
      var r=await fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{email:document.getElementById('email').value,password:document.getElementById('pw').value}})}});
      var d=await r.json();
      if(r.ok&&d.ok){{ location.href=d.redirect||'/'; }}
      else {{ e.textContent='Invalid email or password'; e.classList.add('show'); }}
    }}
    document.getElementById('pw').addEventListener('keydown',function(ev){{if(ev.key==='Enter')go();}});
    </script>"""
    return doc("Sign in — Realify", body, nav=False)


def invite_setup_page(email, token):
    """Branded password-setup page for an APPROVED agency clicking their invite link — inside the realify
    site shell (not a bare page). On success the AJAX submit navigates straight into the agency console
    (the accept endpoint sets the session), instead of dumping raw JSON."""
    body = f"""<div class="authwrap"><div class="authcard">
      <a href="/platform" style="text-decoration:none;display:inline-block;margin-bottom:14px" title="Back to home">{logo()}</a>
      <h2>Set up your agency workspace</h2>
      <div class="sub">Welcome, {esc(email)} — choose a password to enter your Realify for Agencies console.</div>
      <div id="err" class="err"></div>
      <form id="f" onsubmit="return false">
        <div class="field"><label>Choose a password</label><input id="pw" type="password" placeholder="at least 6 characters" autocomplete="new-password" minlength="6"></div>
        <button class="btn btn-blue btn-wide" style="margin-top:16px" onclick="go()">Enter workspace →</button>
      </form>
      <div class="foot" style="justify-content:center;gap:6px;margin-top:16px">Already set up? <a href="/signin">Sign in</a></div>
      {_legal()}</div></div>
    <script>
    async function go(){{
      var e=document.getElementById('err'); e.classList.remove('show');
      var pw=document.getElementById('pw').value;
      if(!pw||pw.length<6){{e.textContent='Password must be at least 6 characters';e.classList.add('show');return;}}
      var r=await fetch('/api/agency/invite/{esc(token)}/accept',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{password:pw}})}});
      var d=await r.json().catch(function(){{return {{}};}});
      if(r.ok&&d.ok){{ location.href=d.redirect||'/agency/console'; }}
      else {{ e.textContent=(d&&d.error)||'Could not set up your workspace — the link may be used or expired.'; e.classList.add('show'); }}
    }}
    document.getElementById('pw').addEventListener('keydown',function(ev){{if(ev.key==='Enter')go();}});
    </script>"""
    return doc("Set up your agency workspace — Realify", body, nav=False)


def invite_invalid_page():
    body = ('<div class="authwrap"><div class="authcard">'
            f'<a href="/platform" style="text-decoration:none;display:inline-block;margin-bottom:14px">{logo()}</a>'
            '<h2>Invite link invalid</h2>'
            '<div class="sub">This invite is invalid, already used, or expired. Ask your Realify contact to resend it.</div>'
            '<a class="btn btn-blue btn-wide" href="/signin" style="margin-top:16px">Go to sign in</a>'
            '</div></div>')
    return doc("Invite invalid — Realify", body, nav=False)


def signup_page():
    body = f"""<div class="authwrap"><div class="authcard">
      <h2>Start your free trial</h2><div class="sub">30 days free. No charge until day 31.</div>
      {_google_btn()}<div class="divider">or</div><div id="err" class="err"></div>
      <form id="f" onsubmit="return false">
        <div class="field"><label>Full name</label><input id="name" placeholder="Jane Smith" autocomplete="name"></div>
        <div class="field"><label>Email address</label><input id="email" type="email" placeholder="you@company.com" autocomplete="email"></div>
        <div class="field"><label>Password</label><input id="pw" type="password" placeholder="••••••••" autocomplete="new-password"></div>
        <div class="field"><label>Confirm password</label><input id="pw2" type="password" placeholder="••••••••" autocomplete="new-password"></div>
        <button class="btn btn-blue btn-wide" style="margin-top:8px" onclick="go()">Start free trial</button>
      </form>
      <div class="foot" style="justify-content:center;gap:6px;margin-top:16px">Already have an account? <a href="/signin">Sign in →</a></div>
      {_legal()}</div></div>
    <script>
    async function go(){{
      var e=document.getElementById('err'); e.classList.remove('show');
      var r=await fetch('/api/billing/signup',{{method:'POST',headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{name:document.getElementById('name').value,email:document.getElementById('email').value,
          password:document.getElementById('pw').value,confirmPassword:document.getElementById('pw2').value}})}});
      var d=await r.json();
      if(r.ok&&d.ok&&d.checkout_url){{ location.href=d.checkout_url; }}
      else {{ e.textContent=(d&&d.error)||'Could not start your trial. Please try again.'; e.classList.add('show'); }}
    }}
    </script>"""
    return doc("Start your free trial — Realify", body, nav=False)


def welcome_page(trial_end_text):
    body = f"""<div class="authwrap"><div class="authcard" style="text-align:center">
      <div style="margin-bottom:12px">{logo()}</div>
      <div style="width:56px;height:56px;border-radius:50%;background:#ecfdf5;color:var(--green);display:flex;
        align-items:center;justify-content:center;font-size:30px;margin:14px auto">✓</div>
      <h2>You're in.</h2>
      <p style="color:var(--ink2);font-size:14px;margin:12px 0 20px">Your 30-day free trial has started. You won't be
      charged until <b>{esc(trial_end_text)}</b>. Cancel any time before then.</p>
      <a href="/" class="btn btn-blue btn-wide">Go to your dashboard →</a>
    </div></div>"""
    return doc("Welcome — Realify", body, nav=False)


def reset_page():
    # Request a reset link. Neutral response (never reveals whether an account exists). NO link to /pricing.
    body = f"""<div class="authwrap"><div class="authcard">
      <div style="margin-bottom:14px">{logo()}</div>
      <h2>Reset your password</h2>
      <div class="sub">Enter your account email and we'll send a single-use link. It expires in one hour.</div>
      <div id="err" class="err"></div>
      <form id="f" onsubmit="return false">
        <div class="field"><label>Email address</label><input id="email" type="email" placeholder="you@company.com" autocomplete="email"></div>
        <button class="btn btn-blue btn-wide" style="margin-top:8px" onclick="go()">Send reset link</button>
      </form>
      <div id="ok" style="display:none;color:var(--green);font-size:14px;margin-top:14px">If an account exists for
        that email, a reset link is on its way. Check your inbox.</div>
      <div class="foot" style="justify-content:center;gap:6px;margin-top:16px"><a href="/signin">← Back to sign in</a></div>
      {_legal()}</div></div>
    <script>
    async function go(){{
      var e=document.getElementById('err'); e.classList.remove('show');
      var r=await fetch('/api/reset/request',{{method:'POST',headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{email:document.getElementById('email').value}})}});
      if(r.ok){{ document.getElementById('f').style.display='none'; document.getElementById('ok').style.display='block'; }}
      else {{ e.textContent='Please enter a valid email.'; e.classList.add('show'); }}
    }}
    document.getElementById('email').addEventListener('keydown',function(ev){{if(ev.key==='Enter')go();}});
    </script>"""
    return doc("Reset password — Realify", body, nav=False)


def reset_confirm_page(token, valid=True):
    if not valid:
        body = (f'<div class="authwrap"><div class="authcard"><div style="margin-bottom:14px">{logo()}</div>'
                '<h2>Link expired</h2><div class="sub">This reset link is invalid, already used, or expired.</div>'
                '<a href="/reset" class="btn btn-blue btn-wide" style="margin-top:8px">Request a new link</a>'
                f'{_legal()}</div></div>')
        return doc("Reset password — Realify", body, nav=False)
    body = f"""<div class="authwrap"><div class="authcard">
      <div style="margin-bottom:14px">{logo()}</div>
      <h2>Choose a new password</h2><div class="sub">At least 6 characters.</div>
      <div id="err" class="err"></div>
      <form id="f" onsubmit="return false">
        <div class="field"><label>New password</label><input id="pw" type="password" placeholder="••••••••" autocomplete="new-password"></div>
        <div class="field"><label>Confirm password</label><input id="pw2" type="password" placeholder="••••••••" autocomplete="new-password"></div>
        <button class="btn btn-blue btn-wide" style="margin-top:8px" onclick="go()">Set password & sign in</button>
      </form>{_legal()}</div></div>
    <script>
    var TOKEN={token!r};
    async function go(){{
      var e=document.getElementById('err'); e.classList.remove('show');
      var p=document.getElementById('pw').value, p2=document.getElementById('pw2').value;
      if(p!==p2){{ e.textContent='Passwords do not match.'; e.classList.add('show'); return; }}
      var r=await fetch('/api/reset/confirm',{{method:'POST',headers:{{'Content-Type':'application/json'}},
        body:JSON.stringify({{token:TOKEN,password:p}})}});
      var d=await r.json().catch(function(){{return{{}};}});
      if(r.ok&&d.ok){{ location.href='/signin'; }}
      else {{ e.textContent=(d&&d.error)||'Could not reset your password.'; e.classList.add('show'); }}
    }}
    </script>"""
    return doc("Reset password — Realify", body, nav=False)


def billing_page(user, days_remaining):
    status = (user or {}).get("subscription_status")
    cpe = (user or {}).get("current_period_end") or "—"
    trial = (user or {}).get("trial_ends_at") or "—"
    if status == "trialing":
        line = f'<span class="badge b-amber">Trialing</span> <span style="color:var(--amber)">Trial ends {esc(trial)}' + (f' · {days_remaining} days left' if days_remaining is not None else '') + '</span>'
    elif status == "active":
        line = f'<span class="badge b-green">Active</span> <span style="color:var(--green)">Next billing date: {esc(cpe)}</span>'
    elif status == "past_due":
        line = '<span class="badge b-red">Past due</span> <span style="color:var(--red)">Payment failed — action required</span>'
    else:
        line = f'<span class="badge b-red">{esc(status or "No subscription")}</span>'
    body = f"""<div class="wrap" style="padding:56px 24px;max-width:720px">
      <div class="label">Account</div><h2>Billing</h2>
      <div class="card" style="margin-top:20px">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
          <div><h3>Realify Pro</h3><div style="color:var(--ink2);font-size:14px">$20 / month</div></div><div>{line}</div></div>
        <hr style="border:none;border-top:1px solid var(--line);margin:18px 0">
        <button class="btn btn-blue" onclick="portal()">Manage billing, invoices & cancellation →</button>
      </div>
    </div>
    <script>
    async function portal(){{ var r=await fetch('/api/billing/portal'); var d=await r.json();
      if(d.portal_url) location.href=d.portal_url; else alert((d&&d.error)||'Billing portal unavailable.'); }}
    </script>"""
    return doc("Billing — Realify", body, active=None)
