"""Spec P4.4: the Open-in-Amazon control never emits a URL that dead-ends (the audit found a Fix-Ads deep
link resolving to advertising.amazon.com/404). Since there is no live-write access, the control is gated:
a live link is emitted ONLY when a valid named campaign target exists; otherwise it renders disabled with
an explanatory tooltip. Server-built deep links point at the campaign manager, never a /404 path.
"""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_amz_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_recommend as R                        # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def _fn(name):
    import re
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n\}", _HTML, re.S)
    assert m, f"{name} not found"
    return m.group(0)


def test_amazon_button_gates_on_valid_target():
    fn = _fn("_famAmazonBtn")
    assert "tr.campaign" in fn                                       # valid only when a named campaign exists
    assert "aria-disabled" in fn and "cursor:not-allowed" in fn      # disabled affordance when no target
    # the disabled branch must NOT emit an href (no dead-end URL)
    disabled = fn[:fn.index("return `<a")]
    assert "href=" not in disabled


def test_no_hardcoded_404_link():
    assert "advertising.amazon.com/404" not in _HTML
    # every modal Open-in-Amazon goes through the gated helper, not a raw <a href>
    for fn in ("_famActCard",):
        assert "_famAmazonBtn(a" in _fn(fn)


def test_server_deeplink_points_at_campaign_manager():
    # the server builds the deep link to the SP campaign manager, never a /404
    assert "advertising.amazon.com/cb/campaigns" in R.ADS_CONSOLE
    assert "/404" not in R.ADS_CONSOLE


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("open_in_amazon_no_404 OK")
