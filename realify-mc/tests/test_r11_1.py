"""R11.1 (hermetic): seller-app locale/fee realism (country.estimate_fees + the CUR-aware frontend
formatters), the banner↔panel offset, the guided-run teleprompter bar + scripts, and the real local
logo (ink/white variants + favicon + no marketing-domain hotlinks). Postgres behaviors (brand country
setting, drill-in locale, guided routes) live in tests/agency/test_r11_1.py."""
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import country                                  # noqa: E402
from realify.site import backbar, ui                         # noqa: E402


_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------- G2: fee / margin realism ----------------

def test_estimate_fees_scale_with_price():
    for cc, prices in [("US", [11, 29, 79]), ("IN", [299, 999, 3299])]:
        prof = country.profile(cc)
        for p in prices:
            ref, fba = country.estimate_fees(p, prof, random.Random(1))
            assert ref + fba < p, f"{cc} {p}: per-unit fees {ref}+{fba} exceed price"
            cogs = p * 0.4
            margin = (p - cogs - ref - fba - p * 0.07) / p * 100
            assert -20 <= margin <= 80, f"{cc} {p}: implausible margin {margin:.0f}%"


def test_us_fba_not_india_scale():
    # the Alpine Kitchen bug: a US ($29) product must NOT carry the IN flat FBA (~₹115)
    ref, fba = country.estimate_fees(29, country.profile("US"), random.Random(2))
    assert fba < 12 and ref < 6                               # US-scale fees, not IN-scale


# ---------------- G1: seller-app locale inheritance (frontend formatters) ----------------

def test_frontend_formatters_are_cur_aware():
    fe = open(os.path.join(_REPO, "frontend.html")).read()
    assert "function _cur(v)" in fe and "function _curK(v)" in fe      # CUR-aware helpers exist
    assert "CUR.country==='IN'?'en-IN':'en-US'" in fe                 # grouping follows the brand country
    # the money formatters delegate to _cur / _curK (no hardcoded ₹/en-IN in their bodies)
    assert "const _cmInr=v=>_cur(v);" in fe
    assert "function catINR(v){ return (v==null||v==='')?'—':_cur(Math.round(v)); }" in fe
    assert "function catK(v){ return v==null?'—':_curK(v); }" in fe
    assert "const inr = v => _cur(v);" in fe


# ---------------- G3: banner ↔ SKU panel offset ----------------

def test_backbar_offsets_drawer_and_mast():
    css = backbar._CSS
    assert "#r9backbar~.drawer{top:40px" in css and "height:calc(100% - 40px)" in css
    assert "#r9backbar~header.mast{top:40px}" in css


# ---------------- F: guided-run teleprompter ----------------

class _Req:
    def __init__(self, sess): self.session = sess

def test_guided_bar_renders_from_session():
    g = {"name": "customer", "i": 1, "total": 7, "persona": "Agency AM",
         "instr": "Drill into Suncrest — its five-lens account.", "title": "Customer walkthrough"}
    html = backbar.bar(_Req({"guided": g}))
    assert "Guided run · Customer walkthrough · 2/7" in html         # N/total
    assert "▸ as Agency AM" in html and "Drill into Suncrest" in html
    assert "_grNext()" in html and "_grExit()" in html               # Next + Exit wired
    assert "guided-run/next" in html and "guided-run/exit" in html   # to the real routes
    # progress dots: 2 lit of 7
    assert html.count("class='gd on'") == 2 and html.count("class='gd'") == 5


def test_guided_bar_stacks_above_backbar():
    # R11.2: during a run the teleprompter STACKS ABOVE the back-to-hub bar (rides every surface) — both render
    html = backbar.bar(_Req({"guided": {"name": "vc", "i": 0, "total": 5, "persona": "Realify Admin",
                                        "instr": "Fleet metrics.", "title": "Investor walkthrough"},
                             "acting_as": {"role": "Realify Admin", "tenant": "fleet", "via": None}}))
    assert "r9guided" in html and "Back to hub" in html          # both bars present, stacked
    assert html.index("r9guided") < html.index("r9backbar")      # guided is on top


def test_guided_scripts_two_and_cross_persona():
    from realify.agency import guided
    for name, mn in [("customer", 5), ("vc", 4)]:
        steps = guided._steps(name, 101, "Suncrest", 102, "Meridian")
        assert len(steps) >= mn
        personas = {s[0] for s in steps}
        assert len(personas) >= 2, f"{name} must hop personas, got {personas}"
        assert all(s[2].startswith("/") for s in steps)              # every step has a real nav URL
        assert any("/agency/brand/101" == s[2] for s in steps)       # drills into the real brand
    # the customer script fires an injector inline on the real world
    cust = guided._steps("customer", 101, "Suncrest", 102, "Meridian")
    assert any(s[4] for s in cust), "customer script must include an injector step"


# ---------------- LOGO: real local logo, variants, favicon, no hotlink ----------------

def test_logo_local_ink_and_white():
    assert 'src="/assets/Final-logo-full-Dark-V3.png"' in ui.logo(dark=False)   # ink on light
    assert 'src="/assets/Final-logo-full-white-V3.png"' in ui.logo(dark=True)   # white on dark
    assert 'alt="Realify"' in ui.logo() and "height:24px" in ui.logo()          # sized by height


def test_logo_assets_present_locally():
    ad = os.path.join(_REPO, "realify", "assets")
    for f in ("Final-logo-full-Dark-V3.png", "Final-logo-full-white-V3.png", "Final-logo-VF-white-3.png"):
        p = os.path.join(ad, f)
        assert os.path.exists(p) and os.path.getsize(p) > 2000, f"{f} missing/empty"


def test_favicon_set_on_key_surfaces():
    from realify.site.hub import hub_html
    from realify.site import hubkit
    fav = "/assets/Final-logo-VF-white-3.png"
    assert fav in hub_html("s@realify.ai")
    assert fav in hubkit.doc("t", hubkit.AGENCY_CSS, "<div></div>")


def test_no_marketing_domain_asset_hotlinks():
    """Extend the no-legacy-domain guard to img src/href: no realify.ai (or wp-content) ASSET URLs."""
    from realify.site import ui_platform, ui_pricing
    from realify.routers import pages
    surfaces = [ui_platform.platform_page(), ui_pricing.pricing_page(), pages._superlogin_gate_html()]
    for html in surfaces:
        assert "wp-content" not in html                              # no marketing-domain asset path
        # no <img>/<link> whose src/href points at realify.ai
        for m in re.finditer(r'(?:src|href)=["\']([^"\']+)["\']', html):
            assert "realify.ai" not in m.group(1) or m.group(1).startswith("mailto:") \
                or "/terms" in m.group(1) or "/privacy" in m.group(1) or "/acceptable" in m.group(1), \
                f"asset hotlink to realify.ai: {m.group(1)}"
        assert 'src="/assets/' in html                               # logo served locally
