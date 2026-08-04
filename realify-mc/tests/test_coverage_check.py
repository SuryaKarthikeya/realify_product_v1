"""A8: coverage_pct is correct, unmapped ad spend is BUCKETED (surfaced, never dropped), and no
attribution is fabricated — an advertised ASIN with no resolved SKU stays internal_sku=NULL, never
assigned to some SKU to make the numbers look complete."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_cov_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd                                                         # noqa: E402
from realify import db                                                     # noqa: E402
from realify.repositories.seller_repo import SellerRepository              # noqa: E402
from realify.repositories.ad_entity_repo import AdEntityPerfRepository     # noqa: E402
from realify.ingest.ad_extract import ingest_ad_graph                      # noqa: E402


def _ap(rows):
    return pd.DataFrame([{"Date": "2026-06-05", "Campaign Name": c, "Ad Group Name": g,
                          "Advertised SKU": s, "Advertised ASIN": a, "Spend": spend,
                          "7 Day Total Sales": sales,
                          "Total Advertising Cost of Sales (ACOS)": "50%"}
                         for (c, g, s, a, spend, sales) in rows])


def test_coverage_and_unmapped_bucket():
    con = db.connect()
    tid = db.create_tenant(con, "t")
    # ASIN1 maps to SKU-A; ASIN9 has no SKU (unmapped)
    SellerRepository(con).upsert_full(tid, {"internal_sku": "SKU-A", "asin": "ASIN1", "channel": "amazon"})
    con.commit()
    df = _ap([("Camp A", "AG1", "SKU-A", "ASIN1", 800, 900),
              ("Camp C", "AG3", "SKU-Z", "ASIN9", 200, 50)])   # unmapped
    s = ingest_ad_graph(con, tid, [("ap.csv", df)])
    con.commit()

    assert abs(s["mapped_spend"] - 800.0) < 0.01
    assert abs(s["unmapped_spend"] - 200.0) < 0.01
    assert abs(s["coverage_pct"] - 80.0) < 0.01          # 800 / 1000

    cov = AdEntityPerfRepository(con).coverage(tid)
    assert abs(cov["coverage_pct"] - 80.0) < 0.01 and abs(cov["unmapped_spend"] - 200.0) < 0.01

    # NO fabricated attribution: the ASIN9 row persists with internal_sku NULL, not assigned to any SKU
    rows = con.execute("SELECT advertised_asin, internal_sku, spend FROM ad_entity_perf "
                       "WHERE tenant_id=?", (tid,)).fetchall()
    by_asin = {r["advertised_asin"]: r for r in rows}
    assert by_asin["ASIN1"]["internal_sku"] == "SKU-A"
    assert by_asin["ASIN9"]["internal_sku"] in (None, "")   # surfaced as unmapped, not invented
    # SKU-A only carries its own mapped spend (unmapped $200 not folded in)
    assert abs(AdEntityPerfRepository(con).coverage(tid)["mapped_spend"] - 800.0) < 0.01
    con.close()


def test_full_coverage_when_all_mapped():
    con = db.connect()
    tid = db.create_tenant(con, "t2")
    SellerRepository(con).upsert_full(tid, {"internal_sku": "SKU-A", "asin": "ASIN1", "channel": "amazon"})
    con.commit()
    s = ingest_ad_graph(con, tid, [("ap.csv", _ap([("Camp A", "AG1", "SKU-A", "ASIN1", 500, 700)]))])
    con.commit()
    assert s["coverage_pct"] == 100.0 and s["unmapped_spend"] == 0.0
    con.close()


if __name__ == "__main__":
    test_coverage_and_unmapped_bucket()
    test_full_coverage_when_all_mapped()
    print("coverage_check OK")
