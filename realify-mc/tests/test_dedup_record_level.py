"""Record-level dedup + SKU crosswalk auto-map (spec §4/§5/§12). Overlapping/wider re-exports of
SHOP_ORDERS must NOT double-count (upsert on the manifest's natural keys); an identical re-export
collapses to the same rows (file-hash stays advisory). Auto-map matches shared SKUs, parks blank/bundle
SKUs, and arms reconcile on a stated-identical mismatch."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.ingest.crosswalk import auto_map, dedupe_records, MAPPED, UNMAPPED, PARKED  # noqa: E402
from realify import topology  # noqa: E402


def _order_rows(names_and_lines):
    return [{"order_name": n, "lineitem_id": li, "sku": sku, "qty": q}
            for (n, li, sku, q) in names_and_lines]


def test_overlapping_re_export_does_not_double_count():
    keys = topology.by_id("SHOP_ORDERS").natural_keys      # ("order_name", "lineitem_id")
    assert keys == ("order_name", "lineitem_id")
    batch1 = _order_rows([("#1001", "L1", "W1", 2), ("#1001", "L2", "W2", 1), ("#1002", "L1", "W1", 3)])
    batch2 = _order_rows([("#1002", "L1", "W1", 3), ("#1003", "L1", "W3", 5)])  # wider re-export overlaps #1002
    deduped = dedupe_records(batch1 + batch2, keys)
    ids = {(r["order_name"], r["lineitem_id"]) for r in deduped}
    assert len(deduped) == 4 and len(ids) == 4                 # 4 unique line items, #1002/L1 not doubled
    assert sum(r["qty"] for r in deduped if r["order_name"] == "#1002") == 3


def test_identical_re_export_collapses_to_same_rows():
    keys = topology.by_id("SHOP_ORDERS").natural_keys
    batch = _order_rows([("#1", "L1", "A", 1), ("#1", "L2", "B", 2)])
    assert len(dedupe_records(batch + batch, keys)) == len(dedupe_records(batch, keys)) == 2


def test_last_write_wins_on_upsert():
    keys = ("order_name", "lineitem_id")
    recs = [{"order_name": "#9", "lineitem_id": "L", "financial_status": "pending"},
            {"order_name": "#9", "lineitem_id": "L", "financial_status": "paid"}]      # corrected re-export
    out = dedupe_records(recs, keys)
    assert len(out) == 1 and out[0]["financial_status"] == "paid"


def test_records_without_keys_are_kept():
    out = dedupe_records([{"x": 1}, {"x": 2}], ("order_name", "lineitem_id"))
    assert len(out) == 2                                       # can't dedup without identity → keep both


def test_auto_map_shared_sku_matches():
    variants = [{"sku": "W1", "variant_id": "v1"}, {"sku": "W2", "variant_id": "v2"}]
    entries, summary, arm = auto_map(variants, {"W1", "W2"}, store_id="store-1", parity="IDENTICAL")
    assert summary["mapped"] == 2 and arm is False
    assert all(e["status"] == MAPPED and e["canonical_sku_id"] == e["external_sku"] for e in entries)


def test_blank_and_bundle_skus_are_parked():
    variants = [{"sku": "", "variant_id": "v1"}, {"sku": "KIT-9", "variant_id": "v2"}]
    entries, summary, arm = auto_map(variants, {"W1"}, bundle_skus={"KIT-9"})
    by_id = {e["external_variant_id"]: e for e in entries}
    assert by_id["v1"]["status"] == UNMAPPED and by_id["v1"]["canonical_sku_id"] is None
    assert by_id["v2"]["status"] == PARKED
    assert summary["unmapped_blank"] == 1 and summary["parked_bundle"] == 1


def test_stated_identical_mismatch_parks_and_arms_reconcile():
    variants = [{"sku": "W1", "variant_id": "v1"}, {"sku": "SHOP-ONLY-7", "variant_id": "v2"}]
    entries, summary, arm = auto_map(variants, {"W1", "W2"}, parity="IDENTICAL")
    by_id = {e["external_variant_id"]: e for e in entries}
    assert by_id["v1"]["status"] == MAPPED                    # the shared one maps
    assert by_id["v2"]["status"] == PARKED and summary["unmatched"] == 1 and arm is True  # mismatch → reconcile


def test_distinct_skus_map_to_own_canonical_when_not_identical():
    variants = [{"sku": "SHOP-ONLY-7", "variant_id": "v2"}]
    entries, summary, arm = auto_map(variants, {"W1"}, parity="NONE")
    assert entries[0]["status"] == MAPPED and entries[0]["canonical_sku_id"] == "SHOP-ONLY-7" and arm is False


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("dedup_record_level OK")
