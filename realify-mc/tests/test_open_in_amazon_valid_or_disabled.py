"""Spec VERIFY 3: Open-in-Amazon is either an ACTIVE link to a well-formed Amazon Ads console URL (when a
valid named campaign target exists) or a DISABLED control with a tooltip — never a bare/404 URL. The deep
link is built server-side.
"""
import os
import re
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_amzv_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_diagnosis as D, ad_recommend as R, ad_levers as LV   # noqa: E402
from realify.domain.ad_fidelity import KEYWORD                                      # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def _fn(name):
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n\}", _HTML, re.S)
    assert m, f"{name} not found"
    return m.group(0)


def test_active_link_uses_wellformed_console_url():
    # a FIX-ADS action targets a named campaign -> the gated helper emits an active <a href=console-url>
    slices = [{"campaign": "Campaign A", "ad_group": "AG1", "spend": 800.0, "sales": 300.0, "orders": 5}]
    terms = {("Campaign A", "AG1"): [{"customer_search_term": "x", "targeting": "t", "match_type": "BROAD",
                                      "spend": 250.0, "sales": 0.0, "orders": 0.0}]}
    dg = D.diagnose("SKU-A", 0.22, slices, terms, KEYWORD)
    rec = R.build("SKU-A", {"cmaa_now": -900.0, "monthly_loss": 900.0, "title": "A", "sym": "₹"}, dg, KEYWORD, 92.0)
    actionable = [a for a in rec["actions"] if a["action_class"] == LV.REALIFY_ACTIONABLE]
    assert actionable and actionable[0]["target_ref"]["campaign"]     # a resolvable named target exists
    assert actionable[0]["deep_link"].startswith("https://advertising.amazon.com/")
    assert "/404" not in actionable[0]["deep_link"]


def test_helper_active_and_disabled_branches():
    fn = _fn("_famAmazonBtn")
    # valid -> active <a href>; invalid -> disabled span with tooltip and NO href
    assert "return `<a class=" in fn and "href=" in fn
    disabled = fn[:fn.index("return `<a")]
    assert "aria-disabled" in disabled and "title=" in disabled and "href=" not in disabled
    assert "tr.campaign" in fn                                        # gating predicate = a named target


def test_no_bare_404_url_anywhere():
    assert "advertising.amazon.com/404" not in _HTML


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("open_in_amazon_valid_or_disabled OK")
