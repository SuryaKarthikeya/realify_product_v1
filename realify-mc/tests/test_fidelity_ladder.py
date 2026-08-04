"""A8: the fidelity ladder selects KEYWORD / CAMPAIGN_SKU / CHANNEL_ONLY from exactly which reports are
present — both as pure logic and end-to-end through ingest (recorded in the coverage summary)."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_fid_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd                                                        # noqa: E402
from realify import db                                                    # noqa: E402
from realify.domain import ad_fidelity as F                               # noqa: E402
from realify.repositories.seller_repo import SellerRepository             # noqa: E402
from realify.repositories.ad_entity_repo import AdIngestSummaryRepository  # noqa: E402
from realify.ingest.ad_extract import ingest_ad_graph                     # noqa: E402


def test_fidelity_pure_logic():
    assert F.fidelity(True, True) == F.KEYWORD            # advertised product + search term
    assert F.fidelity(True, False) == F.CAMPAIGN_SKU      # advertised product only
    assert F.fidelity(False, False, True) == F.CHANNEL_ONLY   # campaign summary only
    assert F.fidelity(False, False, False) == F.CHANNEL_ONLY  # nothing granular


def _ap():
    return pd.DataFrame([{"Date": "2026-06-01", "Campaign Name": "C", "Ad Group Name": "G",
                          "Advertised SKU": "SKU-A", "Advertised ASIN": "ASIN1", "Spend": 100,
                          "7 Day Total Sales": 120, "Total Advertising Cost of Sales (ACOS)": "83%"}])


def _st():
    return pd.DataFrame([{"Date": "2026-06-01", "Campaign Name": "C", "Ad Group Name": "G",
                          "Targeting": "t", "Match Type": "BROAD", "Customer Search Term": "term",
                          "Spend": 30, "7 Day Total Sales": 0}])


def _camp():
    return pd.DataFrame([{"Date": "2026-06-01", "Campaign Name": "C", "Spend": 100,
                          "7 Day Total Sales": 120, "Total Advertising Cost of Sales (ACOS)": "83%"}])


def _ingest(tid_name, tables):
    con = db.connect()
    tid = db.create_tenant(con, tid_name)
    SellerRepository(con).upsert_full(tid, {"internal_sku": "SKU-A", "asin": "ASIN1", "channel": "amazon"})
    con.commit()
    ingest_ad_graph(con, tid, tables)
    con.commit()
    out = AdIngestSummaryRepository(con).get(tid)
    con.close()
    return out


def test_fidelity_through_ingest():
    assert _ingest("kw", [("ap", _ap()), ("st", _st())])["fidelity"] == F.KEYWORD
    assert _ingest("cs", [("ap", _ap())])["fidelity"] == F.CAMPAIGN_SKU
    only_camp = _ingest("ch", [("camp", _camp())])
    assert only_camp["fidelity"] == F.CHANNEL_ONLY
    assert only_camp["granularity_flag"] == F.AD_GRANULARITY_INSUFFICIENT


if __name__ == "__main__":
    test_fidelity_pure_logic()
    test_fidelity_through_ingest()
    print("fidelity_ladder OK")
