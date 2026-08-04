"""T-P7-11 (addendum): EMAIL_DOMAIN default is realifyai.app and no agency/mail code path references
the old unverified sending domain. (The @realify.ai STAFF allowlist in deps.py and the marketing site
links are intentionally out of scope — those are the company's staff/website domain, not mail sending.)"""
import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency import mailcfg      # noqa: E402

# A SENDING use of the old domain: a from/reply mailbox @realify.ai, or realify.ai as EMAIL_DOMAIN.
# (Staff addresses like qa@realify.ai and the @realify.ai staff allowlist are the company domain and
# are intentionally allowed — the addendum is only about the mail SENDING domain.)
_SENDING = re.compile(
    r'(no-?reply|notifications|consent|agencies|ops|security|approvals|hello|support)@realify\.ai'
    r'|EMAIL_DOMAIN[^\n]*realify\.ai|"realify\.ai"|\'realify\.ai\'')


def test_email_domain_default_is_realifyai_app(monkeypatch):
    monkeypatch.delenv("EMAIL_DOMAIN", raising=False)
    monkeypatch.delenv("REPLY_TO_ADDRESS", raising=False)
    assert mailcfg.email_domain() == "realifyai.app"
    assert mailcfg.from_addr() == "no-reply@realifyai.app"
    assert mailcfg.reply_to().endswith("@realifyai.app")


def test_no_legacy_sending_domain_in_agency_mail_surface():
    repo = pathlib.Path(__file__).resolve().parent.parent
    files = list((repo / "realify" / "agency").rglob("*.py")) + list((repo / "realify" / "mail").rglob("*.py"))
    files += [repo / "realify" / "routers" / f for f in
              ("agency.py", "agency_consent.py", "agency_billing.py", "agency_console.py",
               "agency_approvals.py")]
    offenders = []
    for p in files:
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if _SENDING.search(line):
                offenders.append(f"{p.name}:{i}: {line.strip()}")
    assert not offenders, "legacy SENDING domain still referenced:\n" + "\n".join(offenders)


# T-P7-11 (R5 extension): the rendered marketing site must not HOTLINK realify.ai assets (logos, images,
# scripts, fonts) — the logo is served locally now. The ONLY realify.ai references allowed in the site
# layer are the legal documents and the contact mailbox, enumerated here explicitly.
_ALLOWED_REALIFY_AI = (
    "https://realify.ai/terms/",
    "https://realify.ai/privacy-policy/",
    "https://realify.ai/acceptable-use-policy/",
    "mailto:hello@realify.ai",
    "hello@realify.ai",             # the same contact address rendered as visible link text
)


def test_no_realify_ai_asset_hotlinks_in_site_templates():
    repo = pathlib.Path(__file__).resolve().parent.parent
    # hub.py/backbar.py are STAFF sandbox surfaces (behind the superlogin gate), not customer-facing
    # marketing — a staff placeholder email there is not a customer-visible asset hotlink.
    _staff = {"hub.py", "backbar.py"}
    files = [p for p in (repo / "realify" / "site").rglob("*.py") if p.name not in _staff]
    offenders = []
    for p in files:
        for i, line in enumerate(p.read_text().splitlines(), 1):
            # pull the full URL/mailto token wrapping each realify.ai mention (quote/space/paren-delimited)
            for m in re.finditer(r"[^\s\"'<>()]*realify\.ai[^\s\"'<>()]*", line):
                ref = m.group(0).rstrip("/")
                if any(ref == a.rstrip("/") for a in _ALLOWED_REALIFY_AI):
                    continue
                offenders.append(f"{p.name}:{i}: {m.group(0)}")
    assert not offenders, ("realify.ai reference in site templates that isn't an allowed legal/contact "
                           "link (asset hotlinks are forbidden — serve locally):\n" + "\n".join(offenders))
