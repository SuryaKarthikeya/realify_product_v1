"""MCF shared-inventory + booked/settled normalization (spec §5/§12). Amazon FBA + Shopify(MCF) must
NOT sum inventory; MCF-SKU margin stays partial until AMZ_MCF_FEES; booked orders and settled payouts
coexist with unmatched orders held as not-yet-paid-out."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.ingest.normalize_finance import (inventory_allocation, combined_on_hand,  # noqa: E402
                                               mcf_margin_status, settle_orders,
                                               SETTLED, NOT_YET_PAID_OUT)


def test_amazon_fulfillment_location_is_the_shared_pool_not_shopify_stock():
    inv = [{"sku": "W1", "location": "Amazon Fulfillment", "available": 40},
           {"sku": "W2", "location": "Main Warehouse", "available": 30},
           {"sku": "W2", "location": "Amazon Fulfillment", "on_hand": 10}]   # W2 also has MCF units
    alloc = inventory_allocation(inv)
    assert alloc["mcf_detected"] is True and alloc["mcf_skus"] == {"W1", "W2"}
    assert alloc["shopify_own"] == {"W2": 30}                 # W1 has no own stock; W2 own = 30 (Amazon line excluded)


def test_mcf_inventory_does_not_sum_across_channels():
    mcf = {"W1"}
    # W1 is MCF: Amazon FBA 50 + a Shopify "Amazon Fulfillment" 50 is the SAME pool → NOT 100
    assert combined_on_hand("W1", amazon_fba_on_hand=50, shopify_own_on_hand=50, mcf_skus=mcf) == 50
    # W2 self-fulfilled: genuinely separate pools → they add
    assert combined_on_hand("W2", amazon_fba_on_hand=0, shopify_own_on_hand=30, mcf_skus=mcf) == 30
    assert combined_on_hand("W3", amazon_fba_on_hand=20, shopify_own_on_hand=15, mcf_skus=mcf) == 35


def test_mcf_margin_partial_until_fee_arrives():
    mcf = {"W1"}
    assert mcf_margin_status("W1", mcf, has_mcf_fee=False) == "partial"   # no AMZ_MCF_FEES yet
    assert mcf_margin_status("W1", mcf, has_mcf_fee=True) == "complete"   # fee landed → true margin
    assert mcf_margin_status("W2", mcf, has_mcf_fee=False) == "complete"  # non-MCF unaffected


def test_no_mcf_when_no_amazon_location():
    inv = [{"sku": "W2", "location": "Main Warehouse", "available": 30}]
    alloc = inventory_allocation(inv)
    assert alloc["mcf_detected"] is False and alloc["mcf_skus"] == set() and alloc["shopify_own"] == {"W2": 30}


def test_booked_and_settled_coexist_and_join():
    booked = [{"order_id": "#1", "gross": 100}, {"order_id": "#2", "gross": 50}, {"order_id": "#3", "gross": 80}]
    payouts = [{"order_id": "#1", "net": 92}, {"order_id": "#2", "net": 46}]   # #3 not paid out yet
    settled = settle_orders(booked, payouts)
    by = {r["order_id"]: r for r in settled}
    assert by["#1"]["settled_net"] == 92 and by["#1"]["state"] == SETTLED
    assert by["#3"]["settled_net"] is None and by["#3"]["state"] == NOT_YET_PAID_OUT
    assert by["#1"]["gross"] == 100                           # booked value coexists (not overwritten)


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("shared_inventory_mcf OK")
