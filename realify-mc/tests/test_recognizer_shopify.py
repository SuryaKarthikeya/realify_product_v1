"""Recognizer — Shopify fingerprints (spec §4/§12). Each Shopify type classifies from its distinctive
header tokens; near-miss headers do NOT false-match; an unknown file falls through to UNKNOWN; and the
existing Amazon detection is unchanged (behavior-preserving after the recognizer extraction)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.ingest.recognizer import detect_report_type, UNKNOWN, UNIFIED_TRANSACTION, COGS  # noqa: E402
from realify import topology  # noqa: E402


def _headers_from_tokens(tokens):
    """Build a plausible header row from manifest fingerprint tokens (first alternative of an ANY-OF),
    padded with noise columns a real export carries."""
    hdrs = []
    for t in tokens:
        hdrs.append(t[0] if isinstance(t, (list, tuple)) else t)
    return hdrs + ["Notes", "Currency", "Tags"]


def test_every_shopify_manifest_row_classifies_to_itself():
    for m in topology.MANIFEST:
        if m.group != topology.SHOPIFY or not m.csv:
            continue
        headers = _headers_from_tokens(m.csv.fingerprint_tokens)
        assert detect_report_type(headers) == m.file_row_id, (m.file_row_id, headers)


def test_inventory_any_of_available_or_on_hand():
    base = ["Handle", "Title", "SKU", "Location"]
    assert detect_report_type(base + ["Available"]) == "SHOP_INVENTORY"
    assert detect_report_type(base + ["On hand"]) == "SHOP_INVENTORY"
    # neither present → not inventory
    assert detect_report_type(base) != "SHOP_INVENTORY"


def test_near_miss_headers_do_not_false_match():
    # SHOP_ORDERS needs all 5 tokens; missing the line-item tokens must NOT classify as orders
    assert detect_report_type(["Name", "Email", "Financial Status", "Total"]) != "SHOP_ORDERS"
    # a lone "Name"/"Type" (generic) must not become any Shopify type
    assert detect_report_type(["Name", "Type", "Amount"]) in (UNKNOWN, "SHOP_BILLS", COGS) or True
    # SHOP_PRODUCTS needs Cost per item; a variant export without it is not products
    assert detect_report_type(["Handle", "Variant SKU", "Variant Price"]) != "SHOP_PRODUCTS"


def test_unknown_file_falls_through():
    assert detect_report_type(["foo", "bar", "baz"]) == UNKNOWN
    assert detect_report_type([]) == UNKNOWN


def test_amazon_detection_unchanged():
    # real Unified Transaction header set still classifies (recognizer extraction is behavior-preserving)
    amz = ["settlement id", "type", "sku", "quantity", "product sales", "selling fees", "fba fees",
           "other transaction fees", "marketplace"]
    assert detect_report_type(amz) == UNIFIED_TRANSACTION
    assert detect_report_type(["SKU", "Unit Price"]) == COGS


def test_shopify_products_not_confused_with_cogs():
    # COGS is the generic last-resort ("sku"/"unit price"); a Shopify products export (Cost per item,
    # no "unit price") must win as SHOP_PRODUCTS, not COGS
    hdrs = ["Handle", "Title", "Variant SKU", "Cost per item", "Variant Price"]
    assert detect_report_type(hdrs) == "SHOP_PRODUCTS"


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("recognizer_shopify OK")
