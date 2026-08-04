"""Reliability-flag lifecycle (spec §7/§12): armed by an answer AND by detection (idempotent);
AMZ_MCF_FEES satisfies MCF_FEE_REQUIRED; any AD_* satisfies AD_SPEND_ABSENT; the WAIVE path; and the
blocks() mapping matches §7."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.topology_model import (ReliabilityFlag, arm, satisfy_on_receipt,  # noqa: E402
                                     ARMED, SATISFIED, WAIVED,
                                     PROFIT_AFTER_ADS, AD_EFFICIENCY, EVERYTHING, CATEGORY_INTEL)


def test_arm_by_answer_then_detection_is_idempotent():
    flags = []
    arm(flags, "MCF_FEE_REQUIRED", "S1")                 # armed by the S1 answer
    arm(flags, "MCF_FEE_REQUIRED", "detection")          # detection arms the same flag
    assert len(flags) == 1 and flags[0].state == ARMED and flags[0].armed_by == "S1"


def test_arm_by_detection_only():
    flags = []
    f = arm(flags, "SHARED_INVENTORY", "detection")
    assert f.armed_by == "detection" and f.state == ARMED


def test_mcf_fee_file_satisfies_mcf_flag():
    flags = [ReliabilityFlag("MCF_FEE_REQUIRED", armed_by="S1")]
    satisfy_on_receipt(flags, "SHOP_ORDERS")             # unrelated file — no change
    assert flags[0].state == ARMED
    satisfy_on_receipt(flags, "AMZ_MCF_FEES")            # the satisfied_by input lands
    assert flags[0].state == SATISFIED


def test_any_ad_export_satisfies_ad_spend_absent():
    flags = [ReliabilityFlag("AD_SPEND_ABSENT", armed_by="AD1")]
    satisfy_on_receipt(flags, "AD_META")                 # AD_* wildcard
    assert flags[0].state == SATISFIED


def test_waive_path():
    f = ReliabilityFlag("FEE_GAP", armed_by="S3")
    f.waive()
    assert f.state == WAIVED
    # a waived flag is not resurrected by a later arm() on the same id
    flags = [f]
    arm(flags, "FEE_GAP", "detection")
    assert len(flags) == 1 and flags[0].state == WAIVED


def test_blocks_mapping_matches_spec():
    assert set(ReliabilityFlag("MCF_FEE_REQUIRED").blocks()) == {PROFIT_AFTER_ADS, EVERYTHING}
    assert set(ReliabilityFlag("AD_SPEND_ABSENT").blocks()) == {PROFIT_AFTER_ADS, AD_EFFICIENCY, EVERYTHING}
    assert set(ReliabilityFlag("MARGIN_UNAVAILABLE").blocks()) == {PROFIT_AFTER_ADS, EVERYTHING}
    assert set(ReliabilityFlag("FEE_GAP").blocks()) == {PROFIT_AFTER_ADS, EVERYTHING}
    # accuracy-caveat flags block no goal; CATEGORY_INTEL is never blocked by a financial flag
    assert ReliabilityFlag("SHARED_INVENTORY").blocks() == ()
    assert ReliabilityFlag("CROSSWALK_RECONCILE").blocks() == ()
    assert all(CATEGORY_INTEL not in ReliabilityFlag(fid).blocks()
               for fid in ("MCF_FEE_REQUIRED", "AD_SPEND_ABSENT", "MARGIN_UNAVAILABLE", "FEE_GAP"))


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("flags_lifecycle OK")
