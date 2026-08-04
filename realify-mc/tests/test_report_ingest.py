"""Report-aware ingestion (realify/ingest/report_ingest.py): type detection by column signature,
actual-beats-estimated precedence, additive aggregation, and no-fabrication of missing fields."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from realify.ingest import report_ingest as ri  # noqa: E402


def test_detection_by_signature():
    assert ri.detect_report_type(["date/time", "settlement id", "type", "Sku", "product sales",
                                  "selling fees", "fba fees", "total"]) == ri.UNIFIED_TRANSACTION
    assert ri.detect_report_type(["(Parent) ASIN", "(Child) ASIN", "Title", "Sessions - Total",
                                  "Units Ordered"]) == ri.BUSINESS_REPORT
    assert ri.detect_report_type(["sku", "asin", "your-price", "estimated-fee-total",
                                  "estimated-referral-fee-per-unit"]) == ri.FEE_PREVIEW
    assert ri.detect_report_type(["asin", "average-quantity-on-hand", "month-of-charge",
                                  "estimated-monthly-storage-fee"]) == ri.STORAGE_FEE
    assert ri.detect_report_type(["return-date", "sku", "asin", "detailed-disposition", "reason"]) == ri.FBA_RETURNS
    assert ri.detect_report_type(["Date", "Advertised ASIN", "Spend",
                                  "Total Advertising Cost of Sales (ACOS) "]) == ri.AD_REPORT
    assert ri.detect_report_type(["SKU", "Unit Price"]) == ri.COGS
    assert ri.detect_report_type(["foo", "bar", "baz"]) == ri.UNKNOWN


def test_actual_beats_estimated_and_keeps_alternate():
    cogs = pd.DataFrame({"SKU": ["S1"], "Unit Price": [100.0]})
    fee = pd.DataFrame({"sku": ["S1"], "asin": ["A1"], "product-name": ["Widget"],
                        "product-group": ["Auto"], "your-price": [500.0],
                        "estimated-referral-fee-per-unit": [50.0], "estimated-fee-total": [90.0]})
    txn = pd.DataFrame({
        "date/time": ["x"], "settlement id": ["s"], "type": ["Order"], "Sku": ["S1"],
        "product sales": [1000.0], "quantity": [10.0], "selling fees": [-80.0],
        "fba fees": [-120.0], "other transaction fees": [0.0], "total": [800.0]})
    res = ri.ingest_tables([("cogs", cogs), ("fee", fee), ("txn", txn)])
    rec = res.skus["S1"]
    assert rec["cogs"].value == 100.0 and rec["cogs"].basis == "seller"
    # actual price (ASP 1000/10=100) wins over estimated 500, which is retained as an alternate
    assert rec["price"].value == 100.0 and rec["price"].basis == "actual"
    assert any(v == 500.0 for v, b in rec["price"].alternates)
    # actual referral (80/10=8) wins over estimated 50
    assert rec["referral_fee"].value == 8.0 and rec["referral_fee"].basis == "actual"


def test_additive_aggregation_across_months():
    def txn(units, sku="S1"):
        return pd.DataFrame({"date/time": ["x"], "settlement id": ["s"], "type": ["Order"],
                             "Sku": [sku], "product sales": [units * 100.0], "quantity": [float(units)],
                             "selling fees": [-units * 8.0], "fba fees": [-units * 5.0],
                             "other transaction fees": [0.0], "total": [1.0]})
    # three monthly transaction files -> units summed (300) then /3 months = 100/mo
    res = ri.ingest_tables([("m1", txn(90)), ("m2", txn(120)), ("m3", txn(90))])
    assert res.skus["S1"]["units_month"].value == 100


def test_missing_field_is_absent_never_fabricated():
    fee = pd.DataFrame({"sku": ["S9"], "asin": ["A9"], "product-name": ["X"], "product-group": ["G"],
                        "your-price": [200.0], "estimated-referral-fee-per-unit": [20.0],
                        "estimated-fee-total": [35.0]})
    res = ri.ingest_tables([("fee", fee)])          # no COGS file provided
    row = ri.to_seller_sku_rows(res)[0]
    assert row["cogs"] is None                       # absent, not derived from price
