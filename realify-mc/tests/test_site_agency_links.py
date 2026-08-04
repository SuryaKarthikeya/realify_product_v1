"""R5: 'For Agencies' is a permanent entry point on every public page — nav, footer, and a /pricing
cross-link all point at the /agencies marketing landing, which renders regardless of AGENCY_CONSOLE.
Only the functional intake POST stays flag-gated; the marketing surface never depends on the flag."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.site import ui, ui_pricing      # noqa: E402


def _has_agencies_link(html):
    return '/agencies"' in html or "/agencies'" in html or '/agencies#' in html or "/agencies<" in html


def test_agency_links_present_regardless_of_flag(monkeypatch):
    for val in (None, "on"):
        if val is None:
            monkeypatch.delenv("AGENCY_CONSOLE", raising=False)
        else:
            monkeypatch.setenv("AGENCY_CONSOLE", val)
        assert _has_agencies_link(ui._nav()) and "For Agencies" in ui._nav()   # (a) nav/header
        assert _has_agencies_link(ui._footer())                                # (c) footer
        body = ui_pricing.pricing_page()
        assert "/agencies" in body and "For Agencies" in body                  # (b) /pricing cross-link
        # the nav must NOT point at the raw apply endpoint — it links the landing
        assert "/agencies/apply" not in ui._nav()


def test_agencies_landing_renders_regardless_of_flag(monkeypatch):
    from run import make_app
    from fastapi.testclient import TestClient
    for val in (None, "on"):
        if val is None:
            monkeypatch.delenv("AGENCY_CONSOLE", raising=False)
        else:
            monkeypatch.setenv("AGENCY_CONSOLE", val)
        c = TestClient(make_app())
        assert c.get("/agencies").status_code == 200                           # marketing page: always on
        r = c.get("/agencies/apply", follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"] == "/agencies#apply"
