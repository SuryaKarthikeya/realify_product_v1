"""A8: the three ad fingerprints classify; near-misses don't false-match; a campaign-only file is
CHANNEL_ONLY / AD_GRANULARITY_INSUFFICIENT (never faked into per-SKU attribution)."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_adr_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.ingest.recognizer import (   # noqa: E402
    detect_report_type, AD_REPORT, SEARCH_TERM, AD_CAMPAIGN, COGS, BUSINESS_REPORT, UNKNOWN)
from realify.domain import ad_fidelity     # noqa: E402

ADVERTISED_PRODUCT = ["Date", "Portfolio name", "Campaign Name", "Ad Group Name", "Advertised SKU",
                      "Advertised ASIN", "Impressions", "Clicks", "Spend", "7 Day Total Sales",
                      "Total Advertising Cost of Sales (ACOS)", "7 Day Total Orders (#)"]
ADVERTISED_PRODUCT_MIN = ["Date", "Advertised ASIN", "Spend", "7 Day Total Sales",
                          "Total Advertising Cost of Sales (ACOS)"]
SEARCH_TERM_COLS = ["Date", "Campaign Name", "Ad Group Name", "Targeting", "Match Type",
                    "Customer Search Term", "Impressions", "Clicks", "Spend", "7 Day Total Sales",
                    "Total Advertising Cost of Sales (ACOS)"]
CAMPAIGN_COLS = ["Date", "Campaign Name", "Spend", "7 Day Total Sales",
                 "Total Advertising Cost of Sales (ACOS)"]


def test_three_fingerprints_classify():
    assert detect_report_type(ADVERTISED_PRODUCT) == AD_REPORT
    assert detect_report_type(SEARCH_TERM_COLS) == SEARCH_TERM
    assert detect_report_type(CAMPAIGN_COLS) == AD_CAMPAIGN


def test_advertised_product_wins_over_campaign_fallback():
    # a full Advertised Product file also carries 'campaign name' — it must NOT downgrade to AD_CAMPAIGN
    assert detect_report_type(ADVERTISED_PRODUCT) == AD_REPORT
    # and the existing minimal Advertised Product shape (no campaign col) still classifies unchanged
    assert detect_report_type(ADVERTISED_PRODUCT_MIN) == AD_REPORT


def test_near_misses_do_not_false_match():
    assert detect_report_type(["sku", "unit price"]) == COGS                 # COGS, not an ad type
    assert detect_report_type(["(child) asin", "sessions - total", "units ordered"]) == BUSINESS_REPORT
    assert detect_report_type(["foo", "bar", "baz"]) == UNKNOWN
    # a search-term file (no 'advertised asin') must not be read as Advertised Product
    assert detect_report_type(SEARCH_TERM_COLS) != AD_REPORT
    # a campaign-summary file (no 'advertised asin', no 'customer search term') is not the granular type
    assert detect_report_type(CAMPAIGN_COLS) not in (AD_REPORT, SEARCH_TERM)


def test_campaign_only_is_granularity_insufficient():
    assert detect_report_type(CAMPAIGN_COLS) == AD_CAMPAIGN
    # only a campaign-summary present -> channel-level, and the explicit insufficiency flag
    assert ad_fidelity.fidelity(has_advertised_product=False, has_search_term=False,
                                has_campaign_only=True) == ad_fidelity.CHANNEL_ONLY
    assert ad_fidelity.granularity_flag(has_advertised_product=False,
                                        has_campaign_only=True) == ad_fidelity.AD_GRANULARITY_INSUFFICIENT
    # once the Advertised Product file arrives, the flag clears
    assert ad_fidelity.granularity_flag(has_advertised_product=True, has_campaign_only=True) is None


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("ad_recognizer OK")
