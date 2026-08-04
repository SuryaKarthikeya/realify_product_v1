"""Spec: guard against the first-match/shared-target scoping bug on ALL repeated per-card modal controls.
Each per-card control must resolve its target within the clicked card's `.closest('.fam-card')`, never a
modal-wide/document-wide first match or a shared id. (The ƒ toggle behavioural test lives in
test_explainability_ftag_scoped.py; this file is the source-level guard across every repeated control.)

Preview / Apply-this intentionally render into the SINGLE shared `.fam-preview` panel (one per modal,
showing the whole SKU change set) — acting on any card cannot alter another card, so there is nothing to
scope; this test asserts there is exactly one such panel.
"""
import os
import re
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_pcc_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def _fn(name):
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n\}", _HTML, re.S)
    assert m, f"{name} not found"
    return m.group(0)


def test_toggle_controls_scope_to_their_card():
    # Why / Simulate / How-to / ƒ all resolve inside the clicked control's own card
    assert "el.closest('.fam-card').querySelector('[data-why]')" in _fn("_famToggleWhy")
    assert "el.closest('.fam-card').querySelector('.fam-simbox')" in _fn("_famToggleSim")
    assert "el.closest('.fam-card').querySelector('.fam-howto')" in _fn("_famToggleHowto")
    assert "el.closest('.fam-card')" in _fn("_famTf")


def test_resimulate_and_cardgain_scope_to_their_card():
    fn = _fn("_famResim")
    assert "btn.closest('.fam-simbox')" in fn and "btn.closest('.fam-card')" in fn
    assert "card.querySelector('.fam-cardgain')" in fn        # headline gain updates only the clicked card


def test_no_modal_or_document_wide_first_match_in_per_card_toggles():
    for name in ("_famTf", "_famToggleWhy", "_famToggleSim", "_famToggleHowto"):
        fn = _fn(name)
        assert "document.querySelector" not in fn, f"{name} must not use a document-wide first match"
        # a bare modal-wide querySelector (without first narrowing to .fam-card) is the defect we fixed
        assert "closest('.fam-card')" in fn, f"{name} must narrow to the clicked card"


def test_preview_is_a_single_shared_panel():
    # exactly one .fam-preview container is created per modal (Preview/Apply write into it by design)
    op = (_fn("_famOpen") + _fn("_famContentHtml"))
    assert op.count('class="fam-preview"') == 1
    assert "querySelector('.fam-modal .fam-preview')" in _fn("_famPreview")


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("per_card_controls_scoped OK")
