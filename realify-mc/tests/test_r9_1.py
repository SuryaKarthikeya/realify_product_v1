"""R9.1 (hermetic): realistic vocabularies (products/people/agencies), the no-placeholder guarantee at
the spec/vocab layer, sane decision-rule magnitudes, styled unauth states, and the hub flow-advance +
currency-sync JS. Postgres behavior (impacts/mix/paused/currency-in-surfaces) lives in
tests/agency/test_r9_1.py."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency import locale, synth, decisions       # noqa: E402
from realify.site import tokens                            # noqa: E402
from realify.site.hub import hub_html                      # noqa: E402

_PLACEHOLDER = re.compile(r"Brand \d+|Direct brand \d+|Agency \(\d+ brands\)|sandbox[-_][a-z0-9_]+@")


def test_real_product_names_per_category():
    for country, cat in [("US", "Home & Kitchen"), ("US", "Pet Supplies"), ("IN", "Dashcam")]:
        names = [locale.product_name(country, cat, i) for i in range(8)]
        assert len(set(names)) >= 6                          # real variety, not "SB-004"
        assert all("SB-" not in n and cat + " " not in n for n in names)
    assert locale.product_name("US", "Home & Kitchen", 0) == "Stainless Steel Garlic Press"


def test_real_people_and_agency_banks():
    assert locale.person_name("US", 0) == "Sarah Mitchell"
    assert locale.person_name("IN", 0) == "Priya Sharma"
    assert locale.agency_name("US", "us-pilot-v1") in locale.AGENCIES["US"]
    for i in range(5):
        assert not _PLACEHOLDER.search(locale.person_name("US", i))


def test_generated_spec_has_no_placeholder_names():
    spec = synth.spec_from_params({"country": "US", "seed": "np", "brands_per_agency": 6})
    assert not _PLACEHOLDER.search(spec["agency_name"])
    for b in spec["brands"]:
        assert not _PLACEHOLDER.search(b["name"]) and "Brand " not in b["name"]


def test_decision_rules_sane_and_named():
    # a stocked-out SKU with a real title -> named signal, believable impact
    out = decisions._rules("SB-002", price=40, cogs=18, units=200, days_of_cover=7, tacos=12, buybox=95,
                           title="No-Pull Dog Harness")
    assert out and out[0][0] == "inventory"
    lens, kind, signal, impact_minor, conf = out[0]
    assert "No-Pull Dog Harness" in signal and "SB-002" not in signal   # NAMES the product
    assert 0 < impact_minor / 100 < 5000                                # low thousands, not $578k
    # a healthy SKU yields nothing (selective firing keeps paused counts small)
    assert decisions._rules("SB-010", 40, 18, 200, days_of_cover=60, tacos=10, buybox=96,
                            title="Bamboo Cutting Board") == []


def test_unauth_state_page_styled():
    p = tokens.state_page("Agency admin required", "Sign in as an agency admin.", "Staff only")
    assert "Agency admin required" in p and "var(--blue)" in p and ":root{" in p   # uses the design system
    assert p.startswith("<!doctype html>") and "class=sc" in p and tokens.SHELL_CSS in p  # full styled doc, not a bare <h1>


def test_hub_flow_advance_and_currency_sync():
    h = hub_html("staff@realify.ai")
    # flow: on load, lock the Data step + scroll to the Role step (no data re-prompt). R14 restructured
    # the R9.1 collapse into the _setDataLocked state-machine helper (which sets .collapsed + hides body).
    assert "scrollIntoView" in h and "_setDataLocked(on)" in h and "classList.toggle('collapsed',lock)" in h
    # currency↔world sync: the form country reflects the loaded world
    assert "if(on&&st.country)setCountry(st.country)" in h
