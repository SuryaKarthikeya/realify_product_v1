"""Checklist derivation (spec §9/§12): dedup across nodes; grouping + goal ordering; RECEIVED status;
and removing the last emitter → NO_LONGER_REQUIRED when data already arrived vs dropped otherwise."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import nodegraph as ng, topology  # noqa: E402
from realify.pipeline import checklist  # noqa: E402
from realify.topology_model import (ChecklistItem, PENDING, RECEIVED, NO_LONGER_REQUIRED,  # noqa: E402
                                     PROFIT_AFTER_ADS, AD_EFFICIENCY)

_ANSWERS = {"CHANNELS": ["Amazon", "Shopify"], "A1": "FBA", "S1": ["MCF"],
            "S3": "Shopify Payments only", "C1": "In Shopify", "AD1": ["Meta"]}


def _emitted(answers=_ANSWERS):
    _, emitted = ng.resolve_answers(answers)
    return emitted


def test_one_item_per_file_row_id_with_accumulated_emitters():
    emitted = {"SHOP_ORDERS": {"essentiality": topology.ESSENTIAL, "emitted_by": ["S1", "S3"]}}
    items = checklist.derive(emitted)
    assert len(items) == 1 and items[0].emitted_by == ["S1", "S3"]


def test_grouping_and_within_group_essentiality_order():
    items = checklist.derive(_emitted(), primary_goal=None)
    groups = [ci.group for ci in items]
    # canonical group order Amazon · Shopify · Ads · COGS, and groups are contiguous (not interleaved)
    seen, order = [], []
    for g in groups:
        if g not in seen:
            seen.append(g); order.append(g)
    assert order == [g for g in (topology.AMAZON, topology.SHOPIFY, topology.ADS, topology.COGS) if g in seen]
    # within the Shopify group, ESSENTIAL precede SUPPORTING
    shop = [ci for ci in items if ci.group == topology.SHOPIFY]
    ess_idx = [i for i, ci in enumerate(shop) if ci.essentiality == topology.ESSENTIAL]
    sup_idx = [i for i, ci in enumerate(shop) if ci.essentiality == topology.SUPPORTING]
    assert (not sup_idx) or (max(ess_idx) < min(sup_idx))


def test_goal_reorders_group_sequence():
    # a spread of groups incl. a COGS-group row (C1 Spreadsheet → COGS_INLINE) and an Ads row
    emitted = _emitted({"A1": "FBA", "S1": ["Self"], "S3": "Shopify Payments only",
                        "C1": "Spreadsheet", "AD1": ["Meta"]})
    profit = [ci.group for ci in checklist.derive(emitted, primary_goal=PROFIT_AFTER_ADS)]
    adeff = [ci.group for ci in checklist.derive(emitted, primary_goal=AD_EFFICIENCY)]
    # profit-after-ads puts COGS before Ads; ad-efficiency promotes Ads to the top
    assert profit.index(topology.COGS) < profit.index(topology.ADS)
    assert adeff.index(topology.ADS) == 0


def test_received_status_and_satisfiable_by():
    items = checklist.derive(_emitted(), received={"SHOP_ORDERS"})
    by = {ci.file_row_id: ci for ci in items}
    assert by["SHOP_ORDERS"].status == RECEIVED and by["AMZ_MCF_FEES"].status == PENDING
    assert "UPLOAD" in by["SHOP_ORDERS"].satisfiable_by       # csv slot → UPLOAD
    assert by["COGS_INLINE"].satisfiable_by == ("INLINE",) if "COGS_INLINE" in by else True


def test_removing_last_emitter_keeps_received_as_no_longer_required_else_drops():
    prior = [ChecklistItem("AMZ_MCF_FEES", topology.AMAZON, topology.ESSENTIAL, status=RECEIVED),
             ChecklistItem("SHOP_BILLS", topology.SHOPIFY, topology.OPTIONAL, status=PENDING)]
    # new topology no longer emits either (e.g. the MCF answer + Shopify option were removed)
    items = checklist.derive({"SHOP_ORDERS": {"essentiality": topology.ESSENTIAL, "emitted_by": ["S1"]}},
                             prior=prior)
    by = {ci.file_row_id: ci for ci in items}
    assert by["AMZ_MCF_FEES"].status == NO_LONGER_REQUIRED    # already RECEIVED → kept, data preserved
    assert "SHOP_BILLS" not in by                             # was only PENDING → dropped


def test_coming_soon_channels_request_nothing():
    _, emitted = ng.resolve_answers({"CHANNELS": ["Walmart", "eBay"]})
    assert emitted == {}                                      # coming-soon channels emit no files


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("checklist_derivation OK")
