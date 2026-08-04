"""Shopify commit (spec §5): recognized Shopify reports populate seller_skus for Shopify-only SKUs
(COGS/price/units/stock + provenance) and persist the crosswalk; a SKU that maps to an existing Amazon
SKU is linked in the crosswalk but does NOT overwrite the Amazon row; MCF inventory isn't double-counted;
overlapping order re-exports don't inflate units."""
import os
import sys
import tempfile

import pandas as pd

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_sc_"), "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db  # noqa: E402
from realify.ingest import shopify_commit as sc  # noqa: E402
from realify.repositories.seller_repo import SellerRepository  # noqa: E402
from realify.repositories.topology_repo import SkuCrosswalkRepository  # noqa: E402


def _tables(products=None, orders=None, inv=None):
    t = []
    if products is not None:
        t.append(("products.csv", pd.DataFrame(products)))
    if orders is not None:
        t.append(("orders.csv", pd.DataFrame(orders)))
    if inv is not None:
        t.append(("inv.csv", pd.DataFrame(inv)))
    return t


def test_shopify_only_skus_become_seller_rows_with_cogs_and_units():
    db.init_db(); con = db.connect(); tid = 7001
    tables = _tables(
        products=[{"Handle": "widget", "Variant SKU": "SW1", "Cost per item": "120", "Variant Price": "499"}],
        orders=[{"Name": "#1", "Lineitem sku": "SW1", "Lineitem quantity": 2, "Financial Status": "paid",
                 "Fulfillment Status": "fulfilled"},
                {"Name": "#1", "Lineitem sku": "SW1", "Lineitem quantity": 1, "Financial Status": "paid",
                 "Fulfillment Status": "fulfilled"}])
    out = sc.commit(con, tid, tables, parity="NONE"); con.commit()
    row = SellerRepository(con).by_asin(tid, "SW1")
    assert row and row["cogs"] == 120 and row["price"] == 499 and row["units_month"] == 3 and row["channel"] == "shopify"
    assert out["shopify_skus"] == 1 and SkuCrosswalkRepository(con).resolve(tid, "shopify", "SW1") == "SW1"
    con.close()


def test_mapped_sku_links_crosswalk_but_does_not_overwrite_amazon():
    db.init_db(); con = db.connect(); tid = 7002
    SellerRepository(con).upsert_full(tid, {"internal_sku": "AZ1", "asin": "B00AZ1", "channel": "amazon",
                                            "cogs": 300, "price": 999, "units_month": 50}); con.commit()
    tables = _tables(products=[{"Handle": "az", "Variant SKU": "AZ1", "Cost per item": "111", "Variant Price": "888"}],
                     orders=[{"Name": "#9", "Lineitem sku": "AZ1", "Lineitem quantity": 5}])
    out = sc.commit(con, tid, tables, parity="IDENTICAL"); con.commit()
    amazon = SellerRepository(con).by_asin(tid, "B00AZ1")
    assert amazon["cogs"] == 300 and amazon["units_month"] == 50          # Amazon economics untouched
    assert SkuCrosswalkRepository(con).resolve(tid, "shopify", "AZ1") == "AZ1"   # linked in the crosswalk
    assert out["shopify_skus"] == 0                                       # no new/overwritten seller row
    con.close()


def test_mcf_inventory_not_written_as_shopify_stock():
    db.init_db(); con = db.connect(); tid = 7003
    tables = _tables(
        products=[{"Handle": "w", "Variant SKU": "MW1", "Cost per item": "10", "Variant Price": "50"}],
        inv=[{"SKU": "MW1", "Location": "Amazon Fulfillment", "Available": 40}])   # MCF pool, not Shopify stock
    sc.commit(con, tid, tables, parity="NONE"); con.commit()
    row = SellerRepository(con).by_asin(tid, "MW1")
    assert row and not row["stock_on_hand"]                               # MCF units are Amazon-owned, not counted here
    con.close()


def test_blank_sku_products_parked_not_written():
    db.init_db(); con = db.connect(); tid = 7004
    tables = _tables(products=[{"Handle": "x", "Variant SKU": "", "Cost per item": "5", "Variant Price": "20"}])
    out = sc.commit(con, tid, tables, parity="NONE"); con.commit()
    assert out["shopify_skus"] == 0 and out["unmapped"] == 1              # blank SKU parked, never fabricated
    con.close()


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("shopify_commit OK")
