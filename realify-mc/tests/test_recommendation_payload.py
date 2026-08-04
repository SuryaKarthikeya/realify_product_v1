"""A8: every Action carries a valid lever + its lever's action_class; ADVISORY_ONLY actions carry NO
execute affordance (change.type == ADVISORY_TEXT); REALIFY_ACTIONABLE is limited to exactly the three
allowed levers. Guards the §0 hard boundary at the payload layer."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_pay_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import ad_levers as LV, ad_diagnosis, ad_recommend    # noqa: E402
from realify.domain.ad_fidelity import KEYWORD                            # noqa: E402

EXECUTABLE_CHANGE = {"BID_PCT", "NEGATIVE_ADD", "REMOVE_AD"}


def test_lever_taxonomy_integrity():
    # exactly the three actionable levers, forever (spec §0)
    assert LV.ACTIONABLE_LEVERS == {"BID_DOWN", "NEGATIVE_KEYWORD", "REMOVE_PRODUCT_AD"}
    assert all(LV.action_class_of(l) == LV.ADVISORY_ONLY
               for l in ("BUDGET_DOWN_PAUSE", "CAMPAIGN_SPLIT", "SCALE_WINNER"))
    assert LV.needs_search_term("NEGATIVE_KEYWORD") and not LV.needs_search_term("BID_DOWN")


def _rec():
    slices = [{"campaign": "Camp A", "ad_group": "AG1", "spend": 800.0, "sales": 300.0, "orders": 5},
              {"campaign": "Camp B", "ad_group": "AG2", "spend": 400.0, "sales": 200.0, "orders": 2},
              {"campaign": "Camp C", "ad_group": "AG3", "spend": 300.0, "sales": 150.0, "orders": 1}]
    terms = {("Camp A", "AG1"): [
        {"customer_search_term": "junk term", "targeting": "loose", "match_type": "BROAD",
         "spend": 250.0, "sales": 0.0, "orders": 0.0}]}
    dg = ad_diagnosis.diagnose("SKU-A", 0.25, slices, terms, KEYWORD)
    return ad_recommend.build("SKU-A", {"cmaa_now": -900.0, "monthly_loss": 900.0}, dg, KEYWORD, 92.0)


def test_every_action_valid_and_class_matches_lever():
    rec = _rec()
    assert rec["actions"], "expected actions for a bleeding SKU"
    for a in rec["actions"]:
        assert LV.is_valid(a["lever_id"]), a["lever_id"]
        assert a["action_class"] == LV.action_class_of(a["lever_id"])   # class comes from the lever, not the caller
        assert a.get("deep_link")                                        # instruction-mode always carries a link


def test_actionable_limited_to_three_and_carry_executable_change():
    rec = _rec()
    for a in rec["actions"]:
        if a["action_class"] == LV.REALIFY_ACTIONABLE:
            assert a["lever_id"] in LV.ACTIONABLE_LEVERS
            assert a["change"]["type"] in EXECUTABLE_CHANGE


def test_advisory_never_carries_execute_affordance():
    rec = _rec()
    for a in rec["actions"]:
        if a["action_class"] == LV.ADVISORY_ONLY:
            assert not LV.is_actionable(a["lever_id"])
            assert a["change"]["type"] == LV.ADVISORY_TEXT          # text only — no BID_PCT/NEGATIVE_ADD/REMOVE_AD
            assert a["change"]["type"] not in EXECUTABLE_CHANGE


def test_confidence_flags_derived_csv():
    rec = _rec()
    assert rec["confidence"]["derived_source"] is True and rec["confidence"]["fidelity"] == KEYWORD
    assert rec["fidelity"] == KEYWORD and rec["channel"] == "AMAZON"


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("recommendation_payload OK")
