"""realify/ingest/upload_parse.py: column-alias matching must prefer the correct identifier
column over a longer-but-wrong one, and header-row detection must skip banner/legend text —
both regressions found via real Amazon FBA report exports (Storage Fee report, FBA Customer
Returns report, Unified Transaction report) that were silently ingesting zero rows."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from realify.ingest import upload_parse as U  # noqa: E402
from realify.ingest import report_parse  # noqa: E402
from realify import cogs  # noqa: E402


def _csv_bytes(text):
    return text.encode()


# --- Bug 1: fnsku must not shadow asin/sku --------------------------------

def test_build_colmap_prefers_asin_over_fnsku_report_parse():
    # Real FBA Storage Fee report shape: sku column is 'asin', but 'fnsku' is present too and
    # is a longer string — the old length-sort bug bound to fnsku, which never matches a
    # tenant's known SKUs.
    headers = ["asin", "fnsku", "product-name", "average-quantity-on-hand"]
    cm = U._build_colmap(headers, report_parse.A)
    assert headers[cm["sku"]] == "asin"


def test_build_colmap_prefers_sku_over_fnsku_report_parse():
    # Real FBA Customer Returns report shape: both 'sku' and 'asin' columns exist, plus 'fnsku'.
    headers = ["return-date", "order-id", "sku", "asin", "fnsku", "quantity"]
    cm = U._build_colmap(headers, report_parse.A)
    assert headers[cm["sku"]] in ("sku", "asin")
    assert headers[cm["sku"]] != "fnsku"


def test_build_colmap_prefers_asin_over_fnsku_upload_parse():
    headers = ["asin", "fnsku", "title", "price"]
    cm = U._build_colmap(headers, U._ALIASES)
    assert headers[cm["asin"]] == "asin"


def test_build_colmap_cogs_prefers_specific_over_bare():
    # A file with both a specific 'cost of goods' column and a generic 'cost' column should
    # bind the 'cogs' field to the specific one, not whichever is declared/matched first by
    # accident.
    headers = ["sku", "cost of goods", "cost"]
    cm = U._build_colmap(headers, cogs._ALIASES)
    assert headers[cm["cogs"]] == "cost of goods"


# --- Bug 2: CSV banner/legend rows before the real header must be skipped -

def _unified_transaction_like_csv():
    lines = [
        '"Includes Amazon Marketplace, Fulfillment by Amazon (FBA), and Amazon Webstore transactions"',
        '"All amounts in USD, unless specified"',
        '"Definitions:"',
        '"Date/Time: Posted date/time of the transaction"',
        '"Selling fees: Amazon referral fee charged per transaction"',
        '"FBA fees: Fulfillment by Amazon pick, pack, and shipping fees"',
        '"Total: Net amount credited or debited for this transaction"',
        '',
        '',
        '"date/time","settlement id","type","order id","sku","product sales","selling fees","fba fees","total"',
        '"01 Aug 2026","123","Order","111-222","S1","100","-10","-5","85"',
    ]
    return _csv_bytes("\n".join(lines))


def test_read_table_skips_banner_rows_to_find_real_header():
    data = _unified_transaction_like_csv()
    headers, body = U.read_table("unified_transaction.csv", data, report_parse.A)
    assert headers[0] == "date/time"
    assert "settlement id" in headers
    assert len(body) == 1
    assert body[0][headers.index("sku")] == "S1"


def test_read_table_does_not_false_positive_on_single_alias_in_prose():
    # A banner line defining "Date/Time" contains the bare substring "date" — a naive
    # any-single-hit detector mistakes it for the header row. Regression guard for exactly
    # that failure mode (caught while implementing the fix).
    data = _unified_transaction_like_csv()
    headers, _ = U.read_table("unified_transaction.csv", data, report_parse.A)
    assert headers != ["Date/Time: Posted date/time of the transaction"]


def test_read_table_no_banner_still_works():
    # A normal, banner-free export (row 1 is the real header) must keep working unchanged.
    data = _csv_bytes('"sku","fnsku","asin"\n"S1","F1","A1"\n')
    headers, body = U.read_table("plain.csv", data, report_parse.A)
    assert headers == ["sku", "fnsku", "asin"]
    assert len(body) == 1
