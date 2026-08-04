"""R9 (hermetic): locale correctness (US vs India), deterministic spec building, money formatting
goldens, and hub mockup-conformance (the hub lifts the reimagined-hub mockup's classes/tokens). The
Postgres world-generation / impersonation / short-circuit behavior lives in tests/agency/test_r9.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency import synth, locale, money            # noqa: E402
from realify.site.hub import hub_html                       # noqa: E402


def test_locale_us_correct():
    loc = locale.get("US")
    assert loc["currency"] == "USD" and loc["symbol"] == "$"
    assert "Walmart" in loc["channels"] and "Shopify" in loc["channels"] and "Amazon US" in loc["channels"]
    spec = synth.spec_from_params({"country": "US", "seed": "s", "brands_per_agency": 3})
    chans = [c for c, _ in spec["connections"]]
    assert "walmart" in chans and "shopify" in chans and "amazon_ads" in chans   # US channel set
    assert all(b["currency"] == "USD" for b in spec["brands"])


def test_locale_india_correct():
    loc = locale.get("IN")
    assert loc["currency"] == "INR" and loc["symbol"] == "₹"
    assert "Flipkart" in loc["channels"] and "Shopzee" in loc["channels"]
    spec = synth.spec_from_params({"country": "IN", "seed": "s", "brands_per_agency": 3})
    chans = [c for c, _ in spec["connections"]]
    assert "flipkart" in chans and "shopzee" in chans                            # India channel set
    assert all(b["currency"] == "INR" for b in spec["brands"])


def test_cogs_bands_differ_by_country():
    us = synth.spec_from_params({"country": "US", "seed": "s"})
    ind = synth.spec_from_params({"country": "IN", "seed": "s"})
    assert (us["cogs_lo"], us["cogs_hi"]) == (0.28, 0.50)
    assert (ind["cogs_lo"], ind["cogs_hi"]) == (0.35, 0.60)
    assert ind["cogs_lo"] > us["cogs_lo"] and ind["cogs_hi"] > us["cogs_hi"]     # India runs higher


def test_money_formatting_goldens():
    assert money.format_money(156000, "USD") == "$1,560"                         # Western grouping
    assert money.format_money(13100000, "INR") == "₹1,31,000"                    # en-IN lakh grouping


def test_spec_is_deterministic():
    p = {"country": "US", "categories": ["Home & Kitchen"], "sku_count": 200,
         "brands_per_agency": 4, "direct_brands": 1, "seed": "det-x", "moments": ["expired_conn"]}
    assert synth.spec_from_params(p) == synth.spec_from_params(p)                 # pure function
    # 2 brands flagged expired when the moment is on; none when off
    assert sum(1 for b in synth.spec_from_params(p)["brands"] if b["expired_conn"]) == 2
    p2 = dict(p, moments=[])
    assert sum(1 for b in synth.spec_from_params(p2)["brands"] if b["expired_conn"]) == 0


def test_unknown_country_rejected():
    import pytest
    with pytest.raises(ValueError):
        synth.spec_from_params({"country": "FR", "seed": "s"})


# ---- hub conforms to the reimagined-hub mockup (classes/tokens lifted) ----
def test_hub_conforms_to_mockup():
    h = hub_html("staff@realify.ai")
    for cls in ("ordertoggle", "step-n", "subtab", "roles", "r-role", "sandbar", "htitle", "rangeval",
                "toggle", "seedrow"):
        assert cls in h, f"hub missing mockup class: {cls}"
    for tok in ("--terra:#C4785B", "--paper:#F4F0E8", "--ink:#1A1A1A", "border-radius:9px",
                "border-radius:14px"):
        assert tok in h, f"hub missing mockup token: {tok}"
    # the two steps + order toggle + generator + pickers are all present
    assert "Data first" in h and "Role first" in h
    assert "Generate &amp; load world" in h and "Pick existing seed" in h
    assert "Email short-circuit" in h
