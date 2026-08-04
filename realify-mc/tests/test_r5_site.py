"""R5 RENDERED-UI conformance: the marketing design system + For Agencies landing.
Asserts the rendered HTML for each public page carries the shared layout (nav/footer with a permanent
For Agencies entry, local wordmark), the /agencies landing restores the full intake field set, the
truth-guard copy holds in BOTH directions, the pricing polish landed, /reset replaces the old
forgot-password bug, and the confirmation page is restyled while keeping its R1 copy."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import auth                                    # noqa: E402
from realify.site import ui, ui_platform, ui_pricing, ui_about, ui_faq, ui_agencies  # noqa: E402
from realify.agency import funnel                           # noqa: E402
from realify.mail import dev                                # noqa: E402


def _client():
    from run import make_app
    from fastapi.testclient import TestClient
    return TestClient(make_app())


# ---- Item 1: /agencies landing restores the full intake field set ----
def test_agencies_landing_has_full_intake_fieldset():
    body = ui_agencies.agencies_landing()
    assert 'id="apply"' in body
    for field in ("agency_name", "website", "contact_name", "contact_email", "hq_country",
                  "book_size", "am_headcount", "reporting_hours", "marketplaces", "ad_platforms",
                  "current_tool", "target_start", "notes"):
        assert f'name="{field}"' in body, f"missing intake field: {field}"
    # marketplace + ad-platform options must be selectable
    for mk in ("Amazon US", "Walmart", "Shopify", "Flipkart"):
        assert mk in body
    assert "website_hp" in body                             # honeypot present


# ---- Item 1: TRUTH GUARD — required copy present (direction A) ----
def test_agencies_truth_guard_required_copy_present():
    body = ui_agencies.agencies_landing()
    for phrase in ("Reviewed personally", "within 2 business days", "no card, no trial clock",
                   "narrow or revoke", "blocked, not delivered", "never receive an invoice from us",
                   "A human reads this", "Silence never executes"):
        assert phrase in body, f"required truth-guard copy missing: {phrase!r}"


# ---- Item 1: TRUTH GUARD — forbidden claims absent (direction B) ----
def test_agencies_truth_guard_forbidden_claims_absent():
    low = ui_agencies.agencies_landing().lower()
    # no claim of executing ON marketplaces, no benchmarking, no ROI multiples, no leverage statistics
    for bad in ("benchmark", "industry average", "roi multiple", "return on investment",
                "outperform", "x roas guarantee", "guaranteed", "leverage statistic",
                "we execute on amazon", "we run your marketplace"):
        assert bad not in low, f"forbidden claim present: {bad!r}"


# ---- Item 3: For Agencies nav/footer on every public page + local logo ----
def test_for_agencies_and_local_logo_on_all_public_pages():
    ref_status = ui_agencies.status_page("AG-TEST0001", "received", funnel.timeline("received"))
    pages = {
        "platform": ui_platform.platform_page(),
        "pricing": ui_pricing.pricing_page(),
        "about": ui_about.about_page(),
        "faq": ui_faq.faq_page(),
        "agencies": ui_agencies.agencies_landing(),
        "signin": ui.signin_page(),
        "reset": ui.reset_page(),
        "confirmation": ref_status,
    }
    for name, html in pages.items():
        assert "For Agencies" in html, f"{name}: missing For Agencies entry"
        assert "/agencies" in html, f"{name}: missing /agencies link"
        # R11.1: logo is the real wordmark served LOCALLY from /assets — never a hotlinked marketing-domain asset
        assert 'class="logo"' in html, f"{name}: wordmark missing"
        assert 'src="/assets/' in html, f"{name}: logo not served locally from /assets"
        assert "wp-content" not in html, f"{name}: hotlinked marketing-domain asset present"


# ---- Item 5: forgot-password points at /reset, never /pricing ----
def test_forgot_password_points_to_reset_not_pricing():
    signin = ui.signin_page()
    assert 'href="/reset">Forgot password?' in signin
    # the old bug: Forgot password? linked to /pricing. It must not, anywhere in the sign-in flow.
    assert 'href="/pricing">Forgot' not in signin
    # the reset page implements a real reset (posts to the reset API), not a pricing bounce
    reset = ui.reset_page()
    assert "/api/reset/request" in reset
    assert 'href="/pricing">Forgot' not in reset


# ---- Item 5: /reset flow issues a single-use, TTL'd, mailed link that actually resets ----
def test_reset_flow_end_to_end(monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    monkeypatch.setenv("MAIL_DRIVER", "dev")
    dev.clear()
    email = "reset-me@example.com"
    auth.signup(email, "oldpassword", "Reset Co")
    c = _client()

    # request: neutral 200, email carries a /reset/<token> link
    r = c.post("/api/reset/request", json={"email": email})
    assert r.status_code == 200 and r.json()["ok"] is True
    box = dev.inbox(to=email)
    assert box, "reset email not sent"
    link = [w for w in box[-1]["body"].split() if "/reset/" in w][0]
    token = link.rsplit("/reset/", 1)[1]

    # confirm: sets the new password, token is single-use afterwards
    r2 = c.post("/api/reset/confirm", json={"token": token, "password": "newpassword"})
    assert r2.status_code == 200 and r2.json()["ok"] is True
    assert auth.login(email, "newpassword") is not None
    assert auth.login(email, "oldpassword") is None
    # single use: replaying the token now fails
    r3 = c.post("/api/reset/confirm", json={"token": token, "password": "another1"})
    assert r3.status_code == 400


def test_reset_request_is_account_neutral():
    # unknown email -> still 200 (no account enumeration), no token minted
    c = _client()
    r = c.post("/api/reset/request", json={"email": "nobody@nowhere.test"})
    assert r.status_code == 200 and r.json()["ok"] is True


# ---- Item 4: pricing polish — no emoji headers, agencies FAQ + cross-link, no public agency price ----
def test_pricing_polish():
    body = ui_pricing.pricing_page()
    for emoji in ("📊", "🤖", "⚙️", "🔗", "🔒", "💳"):
        assert emoji not in body, f"emoji section header still present: {emoji}"
    assert "pricing is scoped at the pilot call" in body
    assert "For Agencies" in body and "/agencies" in body
    assert "/agencies/apply" not in body                    # cross-link goes to the landing, not the raw form
    # the stray literal "+" accordion artifact is gone (the caret is CSS now)
    assert "<span>+</span>" not in body


# ---- Item 2: confirmation page restyled to the system, R1 copy preserved ----
def test_confirmation_page_restyled_keeps_r1_copy():
    body = ui_agencies.status_page("AG-CONF0001", "in_review", funnel.timeline("in_review"))
    # restyled: renders through the shared layout (nav/footer present)
    assert 'class="nav"' in body and "<footer" in body
    # R1 copy preserved
    assert "AG-CONF0001" in body
    for state in ("received", "in-review", "decision", "live"):
        assert state in body
    assert "within 2 business days" in body and "A human reads this" in body


# ---- Item 6: homepage keeps capability copy, tags illustrative metrics, adds agencies band ----
def test_homepage_illustrative_tags_and_agencies_band():
    body = ui_platform.platform_page()
    assert body.count("illustrative") >= 6                  # one per capability metric panel
    assert "Run client accounts? Realify for Agencies." in body   # agencies band (mockup screen 3)
    # capability copy retained verbatim (spot-check two sections)
    assert "Defend margins and win the buy box on autopilot." in body
    assert "Automation you can audit. Rules you control." in body
