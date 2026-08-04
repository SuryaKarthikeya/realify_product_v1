"""Reconcile prompts (spec §8/§12): each RC trigger fires the right prompt and its effective resolution
applies the right topology change + flags. Detection wins the number."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import nodegraph as ng  # noqa: E402
from realify.pipeline import reconcile as R  # noqa: E402
from realify import topology_model as tm  # noqa: E402


def _topo(answers):
    topo, _ = ng.resolve_answers(answers)
    return topo


def _fired(topo, detected):
    return {p["id"] for p in R.evaluate(topo, detected)}


def test_rc1_detected_mcf_under_stated_self():
    topo = _topo({"CHANNELS": ["Amazon", "Shopify"], "A1": "FBA", "S1": ["Self"]})
    detected = {"mcf_location": True}
    assert "RC-1" in _fired(topo, detected)
    R.apply(topo, "RC-1", detected)
    assert "MCF" in set(topo.resolved["shopify_modes"].effective)
    armed = {f.id for f in topo.flags if f.state == tm.ARMED}
    assert {"SHARED_INVENTORY", "MCF_FEE_REQUIRED"} <= armed


def test_rc2_stated_mcf_no_evidence():
    topo = _topo({"CHANNELS": ["Amazon", "Shopify"], "A1": "FBA", "S1": ["MCF"]})
    detected = {"mcf_location": False, "has_amz_mcf_fees": False}
    assert "RC-2" in _fired(topo, detected) and "RC-1" not in _fired(topo, detected)
    R.apply(topo, "RC-2", detected)
    assert topo.flag("MCF_FEE_REQUIRED") is not None


def test_rc3_amazon_mode_mismatch_detected_wins():
    topo = _topo({"CHANNELS": ["Amazon"], "A1": "FBA"})
    detected = {"detected_amazon_mode": "FBM"}
    assert "RC-3" in _fired(topo, detected)
    R.apply(topo, "RC-3", detected)
    assert topo.resolved["amazon_mode"].effective == "FBM" and topo.resolved["amazon_mode"].conflict is True


def test_rc4_identical_but_unmatched_arms_reconcile():
    topo = _topo({"CHANNELS": ["Amazon", "Shopify"], "A1": "FBA", "S2": "Identical"})
    detected = {"unmatched_shopify_skus": 3}
    assert "RC-4" in _fired(topo, detected)
    R.apply(topo, "RC-4", detected)
    assert topo.flag("CROSSWALK_RECONCILE") is not None


def test_rc5_sp_only_but_other_gateway_arms_fee_gap():
    topo = _topo({"CHANNELS": ["Shopify"], "S3": "Shopify Payments only"})
    detected = {"non_sp_gateway_orders": 12}
    assert "RC-5" in _fired(topo, detected)
    R.apply(topo, "RC-5", detected)
    assert topo.flag("FEE_GAP") is not None


def test_rc6_detected_channel_not_added():
    topo = _topo({"CHANNELS": ["Amazon"], "A1": "FBA"})
    detected = {"extra_channels": ["SHOPIFY"]}
    assert "RC-6" in _fired(topo, detected)
    R.apply(topo, "RC-6", detected)
    assert any(c["platform"] == "SHOPIFY" and c.get("source") == tm.DETECTED for c in topo.channels)


def test_rc7_blank_costs_arm_margin_unavailable():
    topo = _topo({"CHANNELS": ["Shopify"], "C1": "In Shopify"})
    detected = {"blank_cost_skus": 5}
    assert "RC-7" in _fired(topo, detected)
    R.apply(topo, "RC-7", detected)
    assert topo.flag("MARGIN_UNAVAILABLE") is not None


def test_rc8_raw_path_confirm_sets_detected():
    topo = tm.TenantTopology(tenant_id=1, entry_path=tm.RAW)
    topo.resolved["amazon_mode"] = tm.Resolved.from_detected("FBA")   # detected, nothing stated
    detected = {"raw_path": True}
    assert "RC-8" in _fired(topo, detected)
    R.apply(topo, "RC-8", detected)
    assert topo.resolved["amazon_mode"].source == tm.DETECTED


def test_no_false_fires_on_clean_stated_topology():
    topo = _topo({"CHANNELS": ["Amazon"], "A1": "FBA", "C1": "In Shopify"})
    assert _fired(topo, {}) == set()      # nothing detected → no reconcile prompts


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("reconcile_prompts OK")
