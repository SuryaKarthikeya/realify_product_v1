"""Spec P4.3: a SKU/cohort with zero actionable recommendations is handled honestly:
  - NEVER render "Apply all 0 changes" (the apply-all control + combined projection are hidden).
  - NEVER open a "Connect channels" / upload modal from a per-SKU drill-down (that prompt belongs to the
    NO_ENTITY_DATA list banner, not the SKU modal).
  - SCALE SKUs (upside, not cut-recommendations) show scale guidance, not an empty actionable list + apply.
The payload side is asserted too: a profitable, non-offending SKU yields actionable_count == 0 with an
advisory SCALE_WINNER move (so the modal's zero-actionable path is a real, reachable state).
"""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_zero_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_diagnosis as D, ad_recommend as R, ad_levers as LV   # noqa: E402
from realify.domain.ad_fidelity import CAMPAIGN_SKU                                  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def _fn(name):
    import re
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n\}", _HTML, re.S)
    assert m, f"{name} not found"
    return m.group(0)


def test_footer_never_renders_apply_all_zero():
    op = (_fn("_famOpen") + _fn("_famContentHtml"))
    assert "Apply all 0" not in op
    # the Apply-all control + combined projection are ONLY in the actionable.length truthy branch
    assert "actionable.length" in op
    apply_idx = op.index("Apply all ")
    branch = op[op.rindex("actionable.length", 0, apply_idx):apply_idx]
    assert "?" in branch, "Apply-all must be gated behind actionable.length"


def test_scale_shows_guidance_not_apply():
    op = (_fn("_famOpen") + _fn("_famContentHtml"))
    assert "scaleGuide" in op                                        # scale-guidance branch exists
    assert "room to scale" in op or "efficient with room" in op


def test_drilldown_never_opens_connect_modal():
    # the worklist row-click opens the modal (ad plan or basic rec) — never a connect/upload flow.
    # This covers ALL cohorts incl. FIX MARGIN / CUT·DIVEST: SKUs without a campaign-level ad plan open
    # _cmBasicModal (the control-room recommendation), never a NO_ENTITY_DATA connect prompt.
    assert "_famOpenSku(k.sku)" in _HTML and "_cmBasicModal(k)" in _HTML
    for fn in ("_famOpen", "_cmBasicModal"):
        src = _fn(fn)
        assert "goUpload" not in src and "Connect channel" not in src
    # _cmBasicModal shows the recommendation body, never an apply-all-zero control
    assert "Apply all" not in _fn("_cmBasicModal")


def test_profitable_sku_has_zero_actionable_with_advisory():
    # profitable SKU, no offending campaigns -> SCALE_WINNER advisory, zero actionable (the P4.3 state)
    slices = [{"campaign": "Winner", "ad_group": "AG", "spend": 100.0, "sales": 900.0, "orders": 20}]
    dg = D.diagnose("SKU-WIN", 0.25, slices, {}, CAMPAIGN_SKU)
    rec = R.build("SKU-WIN", {"cmaa_now": 4200.0, "monthly_loss": 0.0, "title": "Winner", "sym": "₹"},
                  dg, CAMPAIGN_SKU, 95.0)
    assert rec["actionable_count"] == 0
    advisory = [a for a in rec["actions"] if a["action_class"] == LV.ADVISORY_ONLY]
    assert any(a["lever_id"] == "SCALE_WINNER" for a in advisory)


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("zero_recommendation_state OK")
