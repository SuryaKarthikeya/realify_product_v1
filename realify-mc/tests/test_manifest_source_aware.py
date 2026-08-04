"""Manifest is source-aware (spec §4.1/§12): every row exposes csv/inline/api slots; each v1 row is
satisfiable by csv OR inline; natural_keys are present and shared across acquisition modes; the api slot
may be dormant but is well-formed where declared; and ChecklistItem.satisfiable_by derives from which
non-null slots exist."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import topology  # noqa: E402
from realify.topology import CsvSlot, InlineSlot, ApiSlot  # noqa: E402


def test_every_row_exposes_the_three_slots():
    for m in topology.MANIFEST:
        assert hasattr(m, "csv") and hasattr(m, "inline") and hasattr(m, "api")
        assert m.csv is None or isinstance(m.csv, CsvSlot)
        assert m.inline is None or isinstance(m.inline, InlineSlot)
        assert m.api is None or isinstance(m.api, ApiSlot)


def test_every_v1_row_is_satisfiable_by_csv_or_inline():
    for m in topology.MANIFEST:
        assert m.csv is not None or m.inline is not None, ("no live acquisition slot", m.file_row_id)


def test_natural_keys_present_and_nonempty():
    for m in topology.MANIFEST:
        assert isinstance(m.natural_keys, tuple) and len(m.natural_keys) >= 1, m.file_row_id
        assert all(isinstance(k, str) and k for k in m.natural_keys), m.file_row_id


def test_satisfiable_by_derives_from_non_null_slots():
    for m in topology.MANIFEST:
        modes = m.satisfiable_by()
        assert ("UPLOAD" in modes) == (m.csv is not None)
        assert ("INLINE" in modes) == (m.inline is not None)
        assert ("CONNECT" in modes) == (m.api is not None)     # dormant but derivable now (forward-compat)
    # a fingerprinted Shopify file supports UPLOAD (+ CONNECT once wired); COGS_INLINE is INLINE-only
    assert "UPLOAD" in topology.by_id("SHOP_ORDERS").satisfiable_by()
    assert topology.by_id("COGS_INLINE").satisfiable_by() == ("INLINE",)


def test_api_slot_well_formed_where_declared():
    for m in topology.MANIFEST:
        if m.api is not None:
            assert m.api.provider and m.api.pull, m.file_row_id     # dormant, but not empty


def test_csv_slot_well_formed_where_declared():
    for m in topology.MANIFEST:
        if m.csv is not None:
            assert m.csv.fingerprint_tokens and m.csv.where_to_find
            assert m.csv.arrival_hint in ("INSTANT", "EMAILED"), m.file_row_id


def test_ids_unique_and_groups_valid():
    ids = [m.file_row_id for m in topology.MANIFEST]
    assert len(ids) == len(set(ids)), "duplicate file_row_id"
    for m in topology.MANIFEST:
        assert m.group in (topology.AMAZON, topology.SHOPIFY, topology.ADS, topology.COGS)
        assert m.essentiality in (topology.ESSENTIAL, topology.SUPPORTING, topology.OPTIONAL)


def test_recognizer_shopify_signatures_come_from_manifest():
    # the recognizer's Shopify signature source is the manifest (single source of truth for fingerprints)
    fp = topology.csv_fingerprints()
    shop_rows = [m.file_row_id for m in topology.MANIFEST if m.group == topology.SHOPIFY and m.csv]
    assert set(fp) == set(shop_rows) and all(fp[r] for r in shop_rows)


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("manifest_source_aware OK")
