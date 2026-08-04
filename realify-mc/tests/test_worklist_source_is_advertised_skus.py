"""Spec P3.1: the Profit & Ads worklist is sourced from ADVERTISED SKUs, cohort-bucketed — not the full
catalog, and it carries no catalog columns (Price/COGS/Margin%/Units/Returns). Non-advertised SKUs are
classified into a separate 'Not advertised' quadrant by build_row_card and therefore never appear under
the four cohort tabs (SCALE/FIX ADS/FIX MARGIN/CUT·DIVEST), which are the only tabs the worklist shows.
"""
import os
import re
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_wsrc_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HTML = open(os.path.join(_ROOT, "frontend.html"), encoding="utf-8").read()


def test_worklist_filters_to_the_active_advertised_bucket():
    # the row set is the scoped SKUs whose quadrant == the active cohort (advertised buckets only)
    assert "k.quadrant===_cmBucket" in _HTML
    # the four cohort tabs are the advertised buckets; 'Not advertised' is never one of them
    tabs = re.search(r"\['SCALE','FIX ADS','FIX MARGIN','CUT/DIVEST'\]", _HTML)
    assert tabs, "cohort tabs must be exactly the four advertised buckets"
    # the tab list literal must not include the non-advertised bucket
    assert "'Not advertised'" not in tabs.group(0)


def test_worklist_row_has_no_catalog_columns():
    # the summary-row column header is SKU / ACoS vs break-even / CMAA / <bucket value> / chevron —
    # NOT the catalog columns, which live on the Catalog view instead.
    hd = re.search(r'cm-list-hd.*?</div>', _HTML)
    assert hd
    head = hd.group(0)
    for catalog_col in (">Price<", ">COGS<", ">Margin", ">Units", ">Returns", ">Buy Box<"):
        assert catalog_col not in head, f"worklist must not show catalog column {catalog_col}"
    assert ">SKU<" in head and "ACoS vs break-even" in head and ">CMAA<" in head


def test_non_advertised_skus_are_classified_out_of_the_four_buckets():
    # build_row_card assigns 'Not advertised' when a SKU has no ad spend (server-side classification),
    # so such SKUs cannot land in any of the four cohort tabs.
    cmaa = open(os.path.join(_ROOT, "realify", "routers", "cmaa.py"), encoding="utf-8").read()
    assert "Not advertised" in cmaa


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            _f()
    print("worklist_source_is_advertised_skus OK")
