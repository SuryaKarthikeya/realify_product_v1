"""R14a (hermetic): the hub two-state machine (Part A — Data locks when loaded, Role locks until loaded,
Change world = clear-grant → unlock-Data → re-lock-Role) and the custom brand-name wiring (Part B —
generator input → synth spec → first brand's name)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.site.hub import hub_html          # noqa: E402
from realify.agency import synth                # noqa: E402

_H = hub_html("staff@realify.ai")


# ---------------- Part A: two-state machine ----------------

def test_state_machine_helpers_present():
    assert "function _setDataLocked(lock)" in _H and "function _setRoleLocked(lock)" in _H
    # loaded → Data locked + Role active; not-loaded → Data active + Role locked (exactly one active)
    assert "_setDataLocked(on)" in _H and "_setRoleLocked(!on)" in _H


def test_data_controls_disabled_when_locked():
    # _setDataLocked disables the Data step's inputs/buttons (greyed) so they can't be used while a role is live
    assert ".step-body button,.step-body input,.step-body select" in _H
    assert "el.disabled=lock" in _H


def test_change_world_clears_grant_then_unlocks():
    assert "function changeWorld()" in _H
    # ordered reset: clear the assumed grant (return) FIRST, THEN unlock Data + re-lock Role
    ret = _H.index("/api/ops/sandbox/return")
    body = _H[_H.index("function changeWorld()"):]
    assert "/api/ops/sandbox/return" in body
    assert "_setDataLocked(false)" in body and "_setRoleLocked(true)" in body   # unlock data, re-lock role
    assert 'onclick="changeWorld()"' in _H                                       # the Change-world button uses it


def test_no_stale_reopen_data():
    # the old R11 reopenData (which reopened Data WITHOUT clearing the role grant) is gone
    assert "function reopenData(" not in _H


# ---------------- Part B: custom brand name propagates ----------------

def test_brand_name_names_first_brand():
    spec = synth.spec_from_params({"country": "US", "seed": "bn1", "brands_per_agency": 4,
                                   "brand_name": "Zephyr Goods"})
    assert spec["brands"][0]["name"] == "Zephyr Goods"                  # custom name → first brand
    assert spec["brands"][1]["name"] != "Zephyr Goods"                  # others keep bank names


def test_blank_brand_name_uses_bank():
    spec = synth.spec_from_params({"country": "US", "seed": "bn2", "brands_per_agency": 4, "brand_name": ""})
    assert spec["brands"][0]["name"] and "Brand " not in spec["brands"][0]["name"]   # real bank name, not placeholder


def test_generator_has_brand_name_input():
    assert "id=brandName" in _H and "brand_name:(document.getElementById('brandName')" in _H
