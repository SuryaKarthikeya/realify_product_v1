"""1b ingestion writer + provenance + sticky seller edits (DB-backed; the autouse fixture in
conftest gives each test a fresh migrated DB, so the 0003 columns/table exist)."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from realify import db  # noqa: E402
from realify.ingest import report_ingest as ri, report_writer  # noqa: E402
from realify.repositories.seller_repo import SellerRepository  # noqa: E402
from realify.repositories.provenance_repo import ProvenanceRepository  # noqa: E402

TID = 2


def _ingest(con, cogs_val=100.0):
    cogs = pd.DataFrame({"SKU": ["S1"], "Unit Price": [cogs_val]})
    fee = pd.DataFrame({"sku": ["S1"], "asin": ["A1"], "product-name": ["Widget"], "product-group": ["Auto"],
                        "your-price": [500.0], "estimated-referral-fee-per-unit": [50.0], "estimated-fee-total": [90.0]})
    txn = pd.DataFrame({"date/time": ["x"], "settlement id": ["s"], "type": ["Order"], "Sku": ["S1"],
                        "product sales": [2000.0], "quantity": [10.0], "selling fees": [-160.0],
                        "fba fees": [-240.0], "other transaction fees": [0.0], "total": [1]})
    res = ri.ingest_tables([("c", cogs), ("f", fee), ("t", txn)])
    report_writer.write_ingest(con, TID, res)
    con.commit()


def test_write_values_and_economics():
    con = db.connect(); _ingest(con)
    r = SellerRepository(con).get_full(TID, "S1")
    assert r["price"] == 200.0          # paid ASP = 2000/10, not the ₹500 estimate
    assert r["cogs"] == 100.0
    assert r["referral_fee"] == 16.0 and r["fba_fee"] == 24.0   # actual per-unit
    assert r["net_margin_pct"] == 30.0 and r["breakeven_floor"] == 30.0


def test_actual_vs_estimated_provenance_pair():
    con = db.connect(); _ingest(con)
    pv = ProvenanceRepository(con).for_sku(TID, "S1")
    assert "actual" in pv["fba_fee"] and "estimated" in pv["fba_fee"]   # both kept for the tab


def test_no_fabricated_cogs_or_margin():
    con = db.connect()
    fee = pd.DataFrame({"sku": ["S9"], "asin": ["A9"], "product-name": ["X"], "product-group": ["G"],
                        "your-price": [200.0], "estimated-referral-fee-per-unit": [20.0], "estimated-fee-total": [35.0]})
    report_writer.write_ingest(con, TID, ri.ingest_tables([("f", fee)])); con.commit()
    r = SellerRepository(con).get_full(TID, "S9")
    assert r["cogs"] is None and r["net_margin_pct"] is None   # missing COGS stays missing


def test_sticky_seller_edit_survives_reupload():
    con = db.connect(); _ingest(con)
    SellerRepository(con).update_fields_by_sku_or_asin(TID, "S1", {"cogs": 120.0})
    ProvenanceRepository(con).set(TID, "S1", "cogs", "seller", "seller-entered", 120.0, edited=1)
    con.commit()
    _ingest(con, cogs_val=105.0)                       # re-upload with a different report COGS
    assert SellerRepository(con).get_full(TID, "S1")["cogs"] == 120.0   # seller value held
