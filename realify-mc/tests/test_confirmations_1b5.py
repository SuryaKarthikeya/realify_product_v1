"""1b.5 — Confirmations registry + channel scoping tests.

Covers: registry defaults, seller-override resolver, the 'both sides of every ratio' rule
(channel-scoped refunds), detection of unknown channels, provisional held-out units, and the
interpretation repositories.
"""
import pandas as pd
import pytest

from realify import db
from realify.ingest import report_ingest as ri
from realify.ingest import marketplace_registry as reg
from realify.ingest.report_writer import write_ingest
from realify.repositories.interpretation_repo import InterpretationRepository, ConfirmationRepository
from realify.repositories.seller_repo import SellerRepository


def _txn(rows):
    """Build a Unified-Transaction-shaped frame. rows: (sku, type, marketplace, product_sales, qty)."""
    cols = ["settlement id", "type", "marketplace", "Sku", "product sales", "quantity",
            "selling fees", "fba fees", "other transaction fees"]
    data = []
    for sku, typ, mp, ps, qty in rows:
        data.append([1, typ, mp, sku, ps, qty, -0.1 * ps, -20 * qty, 0])
    return pd.DataFrame(data, columns=cols)


# ---- registry defaults ----------------------------------------------------
def test_registry_defaults():
    assert reg.default_treatment("amazon.in")[0] == reg.AMAZON_DIRECT
    assert reg.default_treatment("si-prod-in.stores.amazon.in")[0] == reg.OFF_AMAZON_MCF
    assert reg.default_treatment("amazon.com")[0] == reg.AMAZON_DIRECT
    assert reg.default_treatment("")[0] == reg.AMAZON_DIRECT           # single-channel export
    assert reg.default_treatment("weirdmart.xyz")[0] == reg.UNKNOWN


# ---- resolver: seller confirmation overrides the default ------------------
def test_resolver_seller_override():
    with db.connect() as con:
        interp = InterpretationRepository(con)
        r = interp.resolver(1)
        assert r("si-prod-in.stores.amazon.in") == reg.OFF_AMAZON_MCF   # registry default
        interp.set_rule(1, "channel_map", "si-prod-in.stores.amazon.in", reg.AMAZON_DIRECT, "seller")
        con.commit()
        r2 = interp.resolver(1)
        assert r2("si-prod-in.stores.amazon.in") == reg.AMAZON_DIRECT   # seller wins


# ---- MCF orders never inflate Amazon units/ASP ----------------------------
def test_mcf_excluded_from_amazon_units():
    df = _txn([
        ("S1", "Order", "amazon.in", 500, 5),                    # Amazon paid
        ("S1", "Order", "si-prod-in.stores.amazon.in", 0, 3),    # Shopify/MCF
        ("S1", "Order", "amazon.in", 0, 1),                      # true free replacement
    ])
    res = ri.ingest_tables([("MonthlyUnifiedTransaction.csv", df)])
    f = res.skus["S1"]
    assert f["units_month"].value == 5                # MCF + free excluded from velocity
    assert f["price"].value == 100.0                  # 500/5, MCF ₹0 rows not in denominator
    assert f["mcf_units"].value == 3
    assert f["replacement_units"].value == 1


# ---- the "both sides of every ratio" rule: refunds are channel-scoped -----
def test_refunds_channel_scoped():
    df = _txn([
        ("S1", "Order", "amazon.in", 1000, 10),                       # 10 Amazon paid
        ("S1", "Refund", "amazon.in", -100, 1),                       # 1 Amazon refund
        ("S1", "Refund", "si-prod-in.stores.amazon.in", 0, 4),        # MCF refunds must NOT count
    ])
    res = ri.ingest_tables([("MonthlyUnifiedTransaction.csv", df)])
    # returns_rate = Amazon refunds (1) / Amazon paid (10) = 0.1, NOT (1+4)/10
    assert res.skus["S1"]["returns_rate"].value == pytest.approx(0.1)


# ---- unknown channel -> provisional, not silently counted as Amazon -------
def test_unknown_channel_held_provisional():
    df = _txn([
        ("S1", "Order", "amazon.in", 400, 4),
        ("S1", "Order", "mystery-market.io", 999, 9),   # unknown -> must not join Amazon paid
    ])
    res = ri.ingest_tables([("MonthlyUnifiedTransaction.csv", df)])
    f = res.skus["S1"]
    assert f["units_month"].value == 4                  # unknown units excluded
    assert f["price"].value == 100.0                    # unknown ₹999 not in ASP
    assert f["provisional_units"].value == 9


# ---- detect_channels surfaces the unknown leg for confirmation ------------
def test_detect_channels():
    df = _txn([
        ("S1", "Order", "amazon.in", 400, 4),
        ("S1", "Order", "mystery-market.io", 999, 9),
    ])
    chans = {c["marketplace"]: c for c in ri.detect_channels([("MonthlyUnifiedTransaction.csv", df)])}
    assert chans["amazon.in"]["treatment"] == reg.AMAZON_DIRECT
    assert chans["mystery-market.io"]["treatment"] == reg.UNKNOWN
    assert chans["mystery-market.io"]["units"] == 9


# ---- confirmation repo: won't clobber a resolved confirmation -------------
def test_confirmation_lifecycle():
    with db.connect() as con:
        conf = ConfirmationRepository(con)
        conf.upsert(1, "channel_map:x.io", "channel_map", "Unknown x.io", "9 units", "off_amazon_mcf", 9)
        con.commit()
        assert len(conf.pending(1)) == 1
        conf.resolve(1, "channel_map:x.io", "confirmed")
        con.commit()
        assert len(conf.pending(1)) == 0
        conf.upsert(1, "channel_map:x.io", "channel_map", "Unknown x.io", "9 units", "off_amazon_mcf", 9)
        con.commit()
        assert len(conf.pending(1)) == 0   # resolved stays resolved


# ---- confirming a rule changes how the next ingest scopes the channel -----
def test_confirm_then_reingest_reclassifies():
    df = _txn([
        ("S1", "Order", "amazon.in", 400, 4),
        ("S1", "Order", "mystery-market.io", 600, 6),
    ])
    with db.connect() as con:
        interp = InterpretationRepository(con)
        # before: unknown -> provisional
        res = ri.ingest_tables([("MonthlyUnifiedTransaction.csv", df)], interp.resolver(1))
        assert res.skus["S1"]["provisional_units"].value == 6
        # seller confirms it's a direct Amazon leg
        interp.set_rule(1, "channel_map", "mystery-market.io", reg.AMAZON_DIRECT, "seller")
        con.commit()
        res2 = ri.ingest_tables([("MonthlyUnifiedTransaction.csv", df)], interp.resolver(1))
        assert res2.skus["S1"]["units_month"].value == 10        # now counted
        assert "provisional_units" not in res2.skus["S1"] or res2.skus["S1"].get("provisional_units") is None


# ---- report-overlap detection (hardening: same-type files that overlap in time) ----
def test_detect_overlaps_ad_reports():
    ad = lambda month: pd.DataFrame([
        {"Date": f"2026-{month}-05", "Advertised ASIN": "B1", "Spend": 10,
         "14 Day Total Sales": 40, "Total Advertising Cost of Sales": 0.25}])
    # two ad reports both covering April -> overlap
    ovs = ri.detect_overlaps([("ad_apr_a.xlsx", ad("04")), ("ad_apr_b.xlsx", ad("04"))])
    assert len(ovs) == 1 and ovs[0]["report_type"] == "ad_report"
    assert ovs[0]["shared_periods"] == ["2026-04"]
    # ad reports for different months -> no overlap
    assert ri.detect_overlaps([("ad_apr.xlsx", ad("04")), ("ad_may.xlsx", ad("05"))]) == []


def test_detect_overlaps_ignores_distinct_transaction_months():
    tx = lambda dt: pd.DataFrame([{
        "settlement id": 1, "type": "Order", "marketplace": "amazon.in", "Sku": "S1",
        "product sales": 100, "quantity": 1, "selling fees": -10, "fba fees": -20,
        "other transaction fees": 0, "date/time": dt}])
    # 3 distinct months -> no overlap findings (this is the normal multi-month upload)
    assert ri.detect_overlaps([("mar.csv", tx("15 Mar 2026 1:00:00 pm UTC")),
                               ("apr.csv", tx("15 Apr 2026 1:00:00 pm UTC")),
                               ("may.csv", tx("15 May 2026 1:00:00 pm UTC"))]) == []
    # same month twice -> flagged
    ovs = ri.detect_overlaps([("apr1.csv", tx("15 Apr 2026 1:00:00 pm UTC")),
                              ("apr2.csv", tx("20 Apr 2026 1:00:00 pm UTC"))])
    assert len(ovs) == 1 and ovs[0]["shared_periods"] == ["2026-04"]


def test_detect_overlaps_ignores_boundary_spillover():
    # a mostly-April file with a couple of March-dated boundary rows must NOT overlap a March file
    def tx_rows(dates):
        return pd.DataFrame([{
            "settlement id": 1, "type": "Order", "marketplace": "amazon.in", "Sku": "S1",
            "product sales": 100, "quantity": 1, "selling fees": -10, "fba fees": -20,
            "other transaction fees": 0, "date/time": d} for d in dates])
    april = tx_rows(["15 Apr 2026 1:00:00 pm UTC"] * 50 + ["31 Mar 2026 6:00:00 pm UTC"])  # 1/51 in March
    march = tx_rows(["15 Mar 2026 1:00:00 pm UTC"] * 50)
    assert ri.detect_overlaps([("apr.csv", april), ("mar.csv", march)]) == []
