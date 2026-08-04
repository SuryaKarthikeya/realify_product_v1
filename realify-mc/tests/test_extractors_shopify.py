"""Shopify extractors (spec §5): parse recognized Shopify DataFrames into the record shapes the crosswalk
+ normalization consume, and confirm they compose end-to-end (orders→dedup, products→auto_map,
inventory→MCF pool, payouts→settle)."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.ingest import extractors_shopify as ex  # noqa: E402
from realify.ingest.crosswalk import auto_map, dedupe_records, MAPPED  # noqa: E402
from realify.ingest.normalize_finance import inventory_allocation, settle_orders, SETTLED  # noqa: E402
from realify import topology  # noqa: E402


def test_products_parse_cost_and_variants():
    df = pd.DataFrame({"Handle": ["widget", "gadget"], "Variant SKU": ["W1", "G1"],
                       "Cost per item": ["₹120.50", ""], "Variant Price": ["499", "0"]})
    recs = ex.products(df)
    assert recs[0] == {"variant_id": "", "sku": "W1", "handle": "widget", "cost": 120.5, "price": 499.0}
    assert recs[1]["sku"] == "G1" and recs[1]["cost"] is None            # blank cost → None, never fabricated
    # feeds the crosswalk
    entries, summary, _ = auto_map(recs, {"W1"}, parity="NONE")
    assert summary["mapped"] == 2 and any(e["status"] == MAPPED for e in entries)


def test_orders_line_items_and_name_forward_fill():
    df = pd.DataFrame({
        "Name": ["#1001", "", "#1002"],                                  # blank continuation row → forward-fill
        "Lineitem sku": ["W1", "W2", "W1"], "Lineitem quantity": [2, 1, 3],
        "Financial Status": ["paid", "paid", "pending"], "Fulfillment Status": ["fulfilled", "", ""]})
    recs = ex.orders(df)
    assert [r["order_name"] for r in recs] == ["#1001", "#1001", "#1002"]
    assert recs[0]["lineitem_id"] == "#1001#0" and recs[1]["lineitem_id"] == "#1001#1"
    # stable line ids → a re-export of the same rows dedups to the same count
    keys = topology.by_id("SHOP_ORDERS").natural_keys
    assert len(dedupe_records(recs + recs, keys)) == 3


def test_inventory_feeds_mcf_pool_detection():
    df = pd.DataFrame({"SKU": ["W1", "W2"], "Location": ["Amazon Fulfillment", "Main Warehouse"],
                       "Available": [40, 30]})
    recs = ex.inventory(df)
    alloc = inventory_allocation(recs)
    assert alloc["mcf_detected"] is True and "W1" in alloc["mcf_skus"] and alloc["shopify_own"] == {"W2": 30}


def test_payouts_settle_against_orders():
    pdf = pd.DataFrame({"Payout Date": ["2026-06-01", "2026-06-01"], "Type": ["charge", "charge"],
                        "Order": ["#1001", "#1002"], "Fee": ["3.00", "1.50"], "Net": ["97.00", "48.50"]})
    payout_recs = ex.payouts(pdf)
    assert payout_recs[0]["order_id"] == "#1001" and payout_recs[0]["net"] == 97.0
    booked = [{"order_id": "#1001", "gross": 100}, {"order_id": "#1003", "gross": 80}]
    settled = settle_orders(booked, payout_recs)
    by = {r["order_id"]: r for r in settled}
    assert by["#1001"]["state"] == SETTLED and by["#1001"]["settled_net"] == 97.0
    assert by["#1003"]["settled_net"] is None                            # no payout → not-yet-paid-out


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("extractors_shopify OK")
