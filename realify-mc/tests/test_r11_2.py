"""R11.2 (hermetic): the guided-run bar STACKS above any contextual bar and rides every surface (incl.
the brand drill-in), with content offset for the stacked bars; and the static demo cards localize their
₹ literals to the brand's country. Live persistence across surfaces lives in tests/agency/test_r11_2.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.site import backbar, brandscope         # noqa: E402
from realify.pdp import ENVELOPES                     # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _Req:
    def __init__(self, sess): self.session = sess


# ---------------- guided bar stacks + offsets ----------------

def test_stacked_bar_offset_css_present():
    css = backbar._GUIDED_CSS
    assert "body.has-guided #r9backbar{top:40px}" in css                     # contextual bar drops below guided
    assert "body.has-guided #r9backbar~.drawer{top:80px" in css             # seller drawer clears BOTH bars
    assert "body.has-guided #r9backbar~header.mast{top:80px}" in css
    assert "document.body.classList.add('has-guided')" in backbar._GUIDED_JS  # marks the surface


def test_guided_bar_rides_the_brand_drilldown():
    # the drill-in (scope bar) must ALSO carry the guided bar when a run is active
    caps = {l: dict(c) for l, c in ENVELOPES["Full Operate"].items()}
    g = {"name": "customer", "i": 1, "total": 7, "persona": "Agency AM",
         "instr": "Act on the top decision.", "title": "Customer walkthrough"}
    html = brandscope.brandscope_html(_Req({"guided": g}), "Suncrest", 1, "BrightPeak", "Full Operate",
                                      caps, [], [{"id": 1, "name": "Suncrest"}])
    assert "r9guided" in html and "Next →" in html and "_grExit()" in html   # teleprompter present on the drill-in
    assert "Portfolio ▸" in html                                            # ...stacked above the scope bar
    assert html.index("r9guided") < html.index("r9backbar")                 # guided on top


def test_drilldown_without_run_has_no_guided_bar():
    caps = {l: dict(c) for l, c in ENVELOPES["Full Operate"].items()}
    html = brandscope.brandscope_html(_Req({}), "Suncrest", 1, "BrightPeak", "Full Operate",
                                      caps, [], [{"id": 1, "name": "Suncrest"}])
    assert "r9guided" not in html and "Portfolio ▸" in html                 # just the scope bar, no run active


# ---------------- demo-card locale ----------------

def test_demo_cards_localizer_wired():
    fe = open(os.path.join(_REPO, "frontend.html")).read()
    assert "function _locd(s){" in fe and "if(CUR.country==='IN') return s;" in fe   # IN unchanged; else swap
    assert "return _locd(`<div class=\"dispatch" in fe                       # cardHTML output localized
    assert "s.replace(/₹/g, CUR.symbol)" in fe                              # any ₹ → the brand symbol


def test_intelligence_static_copy_has_no_rupee():
    fe = open(os.path.join(_REPO, "frontend.html")).read()
    # the two static Intelligence-lens copy strings were neutralized (currency-agnostic)
    assert "recovered lost margin this month" in fe and "recovered ₹" not in fe
    assert "Value above break-even" in fe
