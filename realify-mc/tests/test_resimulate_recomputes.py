"""Spec FIX 2: Re-simulate actually recomputes. Changing the bid parameter and re-running re-invokes the
project() seam and updates the recommendation's 30/60/90 + probabilities, its headline +₹/mo, and the
footer combined projection. The live defect was duplicate element ids across a SKU's multiple actionable
cards (getElementById/querySelector always hit the first card); the controls are now class-scoped so each
card's Re-simulate operates on its own simbox.
"""
import os
import re
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_resim_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_simulate as AS                        # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def _fn(name):
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n\}", _HTML, re.S)
    assert m, f"{name} not found"
    return m.group(0)


def test_project_seam_recomputes_for_a_changed_bid():
    base = AS.project(10000, 90, "KEYWORD", bid_change_pct=0.30)
    changed = AS.project(10000, 90, "KEYWORD", bid_change_pct=0.50)
    assert [h["delta"] for h in base["horizons"]] != [h["delta"] for h in changed["horizons"]]
    # a shallower cut also differs (monotonic, not a no-op)
    shallow = AS.project(10000, 90, "KEYWORD", bid_change_pct=0.10)
    assert [h["delta"] for h in shallow["horizons"]] != [h["delta"] for h in base["horizons"]]
    assert base["formula_id"] == "cmaa_projection"                  # goes through the ads project() seam


def test_resim_handler_scoped_and_updates_all_targets():
    fn = _fn("_famResim")
    # scoped to the clicked card's simbox — no global getElementById of a duplicated id
    assert "btn.closest('.fam-simbox')" in fn and "btn.closest('.fam-card')" in fn
    assert "box.querySelector('.fam-bid')" in fn
    assert "box.querySelector(`[data-simd=" in fn and "box.querySelector(`[data-simp=" in fn   # 30/60/90 + prob
    assert "fam-cardgain" in fn and "hz[0].delta" in fn             # headline +₹/mo recomputes
    assert "fam-combo" in fn                                         # footer recomputes
    # it re-invokes the seam endpoint, not a bespoke client recompute
    assert "/api/ads/simulate?sku=" in fn and "bid=" in fn


def test_no_duplicate_ids_for_simbox_controls():
    # the old defect: id="fam-bid"/"fam-tacos"/"fam-bidval" duplicated across cards. They must be classes now.
    for dead in ('id="fam-bid"', 'id="fam-tacos"', 'id="fam-bidval"'):
        assert dead not in _HTML, f"{dead} must be class-scoped, not a duplicated id"
    assert 'class="fam-bid"' in _HTML and 'class="fam-tacos"' in _HTML


def test_footer_sums_current_card_gains():
    fn = _fn("_famResim")
    assert "querySelectorAll('.fam-modal .fam-cardgain')" in fn and "g.dataset.gain" in fn


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("resimulate_recomputes OK")
