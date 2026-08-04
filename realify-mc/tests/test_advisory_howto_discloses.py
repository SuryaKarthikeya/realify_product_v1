"""Spec FIX 1: the advisory 'How to' control discloses the lever's step-by-step instructions IN-MODAL.
It must be a real keyboard-focusable control (not an inert span), toggle the correct steps block (not a
sibling), never open a window / navigate, source its text from the rules-as-data lever definitions
(ad_levers), and NOT render at all for a lever that carries no how-to data.
"""
import os
import re
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_howto_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_levers as LV                          # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def _fn(name):
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n\}", _HTML, re.S)
    assert m, f"{name} not found"
    return m.group(0)


def _advisory_block():
    # the advisory how-to control is built in the advisory .map() inside _famOpen — grab from the howCtl
    # definition through the advisory card render (covers the control + the steps box).
    op = (_fn("_famOpen") + _fn("_famContentHtml"))
    return op[op.index("const how="):op.index("fam-preview")]


def test_howto_is_a_real_keyboard_control_wired_to_toggle():
    adv = _advisory_block()
    assert 'role="button"' in adv and 'tabindex="0"' in adv          # real control, focusable
    assert "_famToggleHowto(this)" in adv                            # click wired
    assert "event.key==='Enter'||event.key===' '" in adv             # keyboard wired
    # the toggle finds the steps block by its own class, not a fragile nextElementSibling
    tog = _fn("_famToggleHowto")
    assert "closest('.fam-card').querySelector('.fam-howto')" in tog and "toggle('open')" in tog


def test_howto_reveals_in_modal_only_no_popup_or_nav():
    adv = _advisory_block()
    for banned in ("window.open", "alert(", "location.href", "location.assign", 'target="_blank">How to'):
        assert banned not in adv, f"How-to must reveal in-modal, not {banned}"
    assert "fam-howto" in adv                                        # inline steps block


def test_howto_only_renders_when_lever_has_data():
    op = (_fn("_famOpen") + _fn("_famContentHtml"))
    # the control + box are gated on `how` (the lever's how-to text) being present — no dead control
    assert "const how=" in op and "how?" in op


def test_howto_text_comes_from_rules_as_data():
    # advisory levers carry a how_to string in ad_levers; the payload passes it as change.value
    for lid in ("BUDGET_DOWN_PAUSE", "CAMPAIGN_SPLIT", "SCALE_WINNER"):
        assert LV.LEVERS[lid]["how_to"], f"{lid} must have how-to steps in the registry"
        assert LV.LEVERS[lid]["action_class"] == LV.ADVISORY_ONLY


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("advisory_howto_discloses OK")
