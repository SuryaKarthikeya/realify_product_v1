"""Node graph ↔ manifest (spec §6 Table 1 / §12). The graph is DATA; every leaf emits/arms exactly as
tabulated; and referential integrity holds — no emit references a missing manifest row, no arm references
an unknown flag. The emit resolver produces the stated TenantTopology + the union of emitted file_row_ids."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import nodegraph as ng, topology  # noqa: E402
from realify import topology_model as tm  # noqa: E402


def test_referential_integrity_emits_and_arms():
    ids = set(topology.all_ids())
    for n in ng.NODES:
        for fid, _e in n.baseline_emits:
            assert fid in ids, ("baseline emit missing from manifest", n.id, fid)
        for opt in n.options:
            for fid, _e in opt.emits:
                assert fid in ids, ("emit missing from manifest", n.id, opt.label, fid)
            for flag_id in opt.arms:
                assert flag_id in tm.FLAG_SPECS, ("arm references unknown flag", n.id, opt.label, flag_id)


def _resolve(answers):
    topo, emitted = ng.resolve_answers(answers)
    return topo, emitted, set(emitted)


def test_a1_fulfillment_emits_match_table1():
    _, _, fba = _resolve({"A1": "FBA"})
    assert fba == {"AMZ_SETTLEMENT", "AMZ_ORDERS", "AMZ_INV_FBA"}
    _, _, both = _resolve({"A1": "Both"})
    assert both == {"AMZ_SETTLEMENT", "AMZ_ORDERS", "AMZ_INV_FBA", "AMZ_INV_FBM"}
    topo, _, _ = _resolve({"A1": "FBM"})
    assert topo.resolved["amazon_mode"].effective == "FBM" and topo.resolved["amazon_mode"].source == tm.STATED


def test_s1_baseline_plus_mcf_emits_and_arms():
    topo, _, emit = _resolve({"S1": ["Self", "MCF"]})
    assert {"SHOP_ORDERS", "SHOP_INVENTORY", "AMZ_MCF_FEES"} <= emit          # baseline + MCF emit
    armed = {f.id for f in topo.flags}
    assert {"SHIP_COST_ESTIMATED", "SHARED_INVENTORY", "MCF_FEE_REQUIRED"} == armed
    assert set(topo.resolved["shopify_modes"].effective) == {"SELF", "MCF"}   # multi-select set


def test_s2_and_s3_writes_and_arms():
    topo, _, _ = _resolve({"S2": "Mostly", "S3": "Shopify Payments + others"})
    assert topo.resolved["sku_parity"].effective == "MOSTLY"
    assert topo.resolved["gateway"].effective == "SP_PLUS"
    armed = {f.id for f in topo.flags}
    assert "CROSSWALK_RECONCILE" in armed and "FEE_GAP" in armed
    _, _, s3emit = _resolve({"S3": "Shopify Payments only"})
    assert s3emit == {"SHOP_PAYOUTS", "SHOP_PAYOUT_RECON", "SHOP_PAYMENTS_SUMMARY"}


def test_c1_cogs_paths():
    _, _, shop = _resolve({"C1": "In Shopify"})
    assert shop == {"SHOP_PRODUCTS"}
    topo, emitted, notyet = _resolve({"C1": "Not yet"})
    assert notyet == {"COGS_INLINE"} and emitted["COGS_INLINE"]["essentiality"] == topology.OPTIONAL
    assert topo.resolved["cogs_source"].effective == "NONE"
    assert {f.id for f in topo.flags} == {"MARGIN_UNAVAILABLE"}


def test_ad1_multi_and_none_arms_absent():
    topo, _, emit = _resolve({"AD1": ["Amazon Ads", "Meta"]})
    assert emit == {"AD_AMAZON", "AD_META"} and topo.ad_partners == ["AMAZON", "META"]
    topo2, _, _ = _resolve({"AD1": "None yet"})
    assert {f.id for f in topo2.flags} == {"AD_SPEND_ABSENT"}


def test_channels_and_coming_soon():
    topo, _, emit = _resolve({"CHANNELS": ["Amazon", "Shopify", "Walmart"]})
    plats = {c["platform"]: c["status"] for c in topo.channels}
    assert plats["AMAZON"] == "ACTIVE" and plats["SHOPIFY"] == "ACTIVE" and plats["WALMART"] == "COMING_SOON"
    assert emit == {"SHOP_BILLS"}                            # Shopify option emits SHOP_BILLS(O); coming-soon requests nothing


def test_g1_goal_and_optional():
    topo, _, emit = _resolve({"G1": "Profit after ads"})
    assert topo.primary_goal == tm.PROFIT_AFTER_ADS and emit == set()   # goal orders/previews; emits nothing


def test_emitted_by_accumulates_and_dedups():
    # a full answer set; every emitted row records which node(s) emitted it, deduped
    _, emitted = ng.resolve_answers({"CHANNELS": ["Amazon", "Shopify"], "A1": "FBA",
                                     "S1": ["MCF"], "S3": "Shopify Payments only", "C1": "In Shopify"})
    assert emitted["AMZ_MCF_FEES"]["emitted_by"] == ["S1"]
    assert emitted["SHOP_ORDERS"]["emitted_by"] == ["S1"]   # from S1 baseline
    assert all(isinstance(v["emitted_by"], list) and v["emitted_by"] for v in emitted.values())


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("node_emit_resolution OK")
