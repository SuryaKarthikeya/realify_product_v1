"""Phase-1 inline conflict resolution: structured conflict objects + resolver.

Covers the detection matrix (duplicate/high, overlap-equal/high, overlap-differ/medium+delta,
disjoint/no-conflict), the four resolve choices, the no-regression invariant (default keep_latest ==
today's dedupe_ad_periods), and a DB-backed end-to-end through ingest_tables -> write_ingest ->
ad_performance on both SQLite and Postgres (via conftest).
"""
import pandas as pd

from realify import db
from realify.repositories.tenant_repo import TenantRepository
from realify.repositories.ad_performance_repo import AdPerformanceRepository
from realify.repositories.seller_repo import SellerRepository
from realify.ingest import conflicts as C
from realify.ingest import report_ingest, report_writer
from realify.ingest.periods import dedupe_ad_periods

_COLS = ["Date", "Advertised ASIN", "Spend", "7 Day Total Sales",
         "Total Advertising Cost of Sales (ACOS)"]


def ad(rows):
    """rows: list of [date, asin, spend, sales] -> a valid SP Advertised-Product frame."""
    return pd.DataFrame([r + [0.25] for r in rows], columns=_COLS)


# ---- detection matrix ------------------------------------------------------
def test_overlap_differ_is_medium_keep_latest_with_delta():
    a = ad([["2026-06-01", "B1", "₹1,000", "₹3,000"]])
    b = ad([["2026-06-15", "B1", "₹1,800", "₹3,000"]])
    (c,) = C.detect_conflicts([("MarToJun.csv", a), ("JuneOnly.csv", b)])
    assert c["type"] == "period_overlap" and c["report_type"] == "ad_report" and c["period"] == "2026-06"
    assert c["confidence"] == "medium" and c["recommended"] == "keep_latest"
    assert c["impact"]["keep_latest"]["ad_spend"] == 1800.0     # take-latest, not summed
    assert c["impact"]["sum"]["ad_spend"] == 2800.0
    assert c["impact"]["delta_vs_recommended"]["ad_spend"] == 1000.0
    assert c["impact"]["delta_vs_recommended"]["pct_of_total"] == 55.6
    assert set(c["options"]) == {"keep_latest", "keep_file", "sum", "skip_period"}
    assert [s["file"] for s in c["sides"]] == ["MarToJun.csv", "JuneOnly.csv"]


def test_overlap_equal_is_high_confidence():
    a = ad([["2026-06-01", "B1", "₹1,000", "₹3,000"]])
    b = ad([["2026-06-20", "B1", "₹1,000", "₹3,000"]])
    (c,) = C.detect_conflicts([("x.csv", a), ("y.csv", b)])
    assert c["confidence"] == "high" and "keep either" in c["auto_reason"]
    # values are identical, but summing still double-counts -> delta is one file's spend, not 0
    assert c["impact"]["keep_latest"]["ad_spend"] == 1000.0
    assert c["impact"]["delta_vs_recommended"]["ad_spend"] == 1000.0


def test_disjoint_months_raise_no_conflict():
    a = ad([["2026-04-01", "B1", "100", "300"]])
    b = ad([["2026-05-01", "B1", "100", "300"]])
    assert C.detect_conflicts([("apr.csv", a), ("may.csv", b)]) == []


def test_duplicate_file_is_high_confidence():
    (c,) = C.detect_conflicts([], [("dup.csv", "orig.csv", "2026-05-01T10:00:00")])
    assert c["type"] == "duplicate_file" and c["confidence"] == "high"
    assert c["recommended"] == "keep_latest" and "identical" in c["auto_reason"]


def test_conflict_id_stable_and_order_independent():
    assert C.period_conflict_id("2026-06", ["a.csv", "b.csv"]) == \
           C.period_conflict_id("2026-06", ["b.csv", "a.csv"])


# ---- resolver: the four choices + no-regression invariant ------------------
def _spend(recs):
    return round(sum(r["spend"] for r in recs), 2)


def test_default_keep_latest_equals_dedupe_ad_periods():
    # THE no-regression invariant: skipping resolution reproduces today's numbers exactly.
    a = ad([["2026-06-01", "B1", "₹1,000", "₹3,000"], ["2026-06-02", "B2", "₹500", "₹1,500"]])
    b = ad([["2026-06-03", "B1", "₹1,200", "₹3,600"]])
    key = lambda rs: sorted((r["asin"], r["period_start"], r["spend"], r["sales"]) for r in rs)
    assert key(C.resolve_ad_frames([("a.csv", a), ("b.csv", b)])) == key(dedupe_ad_periods([a, b]))


def test_resolve_choices():
    a = ad([["2026-06-01", "B1", "₹1,000", "₹3,000"]])
    b = ad([["2026-06-15", "B1", "₹1,800", "₹3,000"]])
    named = [("MarToJun.csv", a), ("JuneOnly.csv", b)]
    cid = C.period_conflict_id("2026-06", ["MarToJun.csv", "JuneOnly.csv"])
    assert _spend(C.resolve_ad_frames(named, {cid: "keep_latest"})) == 1800.0
    assert _spend(C.resolve_ad_frames(named, {cid: "sum"})) == 2800.0
    assert _spend(C.resolve_ad_frames(named, {cid: "keep_file:MarToJun.csv"})) == 1000.0
    assert _spend(C.resolve_ad_frames(named, {cid: "skip_period:JuneOnly.csv"})) == 1000.0


def test_parse_resolutions_is_tolerant():
    assert C.parse_resolutions(None) == {}
    assert C.parse_resolutions("") == {}
    assert C.parse_resolutions("not json") == {}
    assert C.parse_resolutions('{"cf_x":"sum"}') == {"cf_x": "sum"}
    assert C.parse_resolutions({"cf_y": "keep_latest"}) == {"cf_y": "keep_latest"}


# ---- end-to-end through ingest_tables -> write_ingest -> ad_performance -----
def _june_ad_tables():
    # same ASIN advertised in June by two overlapping files (spend differs materially); a listings
    # file establishes the ASIN->SKU identity so the ad periods resolve to a real internal_sku.
    a = ad([["2026-06-01", "B0J", "₹1,000", "₹3,000"]])
    b = ad([["2026-06-15", "B0J", "₹1,800", "₹3,000"]])
    listings = pd.DataFrame([["B0J", "B0J"]], columns=["seller-sku", "asin1"])
    return [("MarToJun.csv", a), ("JuneOnly.csv", b), ("listings.csv", listings)], \
        C.period_conflict_id("2026-06", ["MarToJun.csv", "JuneOnly.csv"])


def _june_spend(con, tid):
    return AdPerformanceRepository(con).totals(tid).get("B0J", {}).get("spend")


def test_e2e_skip_and_resolve_match_expectations():
    tables, cid = _june_ad_tables()
    with db.connect() as con:
        tid = TenantRepository(con).create("conflict e2e")
        SellerRepository(con).upsert_full(tid, {"internal_sku": "B0J", "asin": "B0J", "channel": "amazon"})
        # (a) skip resolution -> today's take-latest -> June NOT doubled
        report_writer.write_ingest(con, tid, report_ingest.ingest_tables(tables))
        con.commit()
        assert _june_spend(con, tid) == 1800.0
        # (b) "use recommended for all" == keep_latest -> still take-latest
        report_writer.write_ingest(con, tid, report_ingest.ingest_tables(tables, resolutions={cid: "keep_latest"}))
        con.commit()
        assert _june_spend(con, tid) == 1800.0
        # (c) user picks SUM -> June spend is summed across the two files
        report_writer.write_ingest(con, tid, report_ingest.ingest_tables(tables, resolutions={cid: "sum"}))
        con.commit()
        assert _june_spend(con, tid) == 2800.0


# ---- HTTP end-to-end: conflicts reach the client + resolutions flow through ----
import json  # noqa: E402

import pytest  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402


@pytest.fixture
def client():
    import run
    return TestClient(run.make_app())


def _customer(client, email):
    from realify import auth as _auth
    _auth.signup(email, "secret123", "Autofy")          # /api/signup back door gated (P0.9)
    assert client.post("/api/login", json={"email": email, "password": "secret123"}).status_code == 200
    with db.connect() as con:
        tid = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()["tenant_id"]
        db.set_account_type(con, tid, "customer")
        con.commit()
    return tid


_AD_HDR = b"Date,Advertised ASIN,Spend,14 Day Total Sales,Total Advertising Cost of Sales\n"
_JUNE_A = _AD_HDR + b"2026-06-05,B1,1000,3000,0.33\n"
_JUNE_B = _AD_HDR + b"2026-06-20,B1,1800,3000,0.60\n"
_CID = C.period_conflict_id("2026-06", ["ad_jun_a.csv", "ad_jun_b.csv"])


def _commit_files(resolutions=None):
    files = [("f0", ("Autofy_COGS_Data.csv", b"sku,unit price\nS1,400\n", "text/csv")),
             ("f1", ("439433020633.csv",
                     b"sku,asin,product-name,your-price,estimated-referral-fee-per-unit,estimated-fee-total\n"
                     b"S1,B1,Widget,1000,100,200\n", "text/csv")),
             ("f2", ("ad_jun_a.csv", _JUNE_A, "text/csv")),
             ("f3", ("ad_jun_b.csv", _JUNE_B, "text/csv"))]
    data = {"country": "IN"}
    if resolutions is not None:
        data["resolutions"] = json.dumps(resolutions)
    return data, files


def _june(tid):
    with db.connect() as con:
        return AdPerformanceRepository(con).totals(tid).get("S1", {}).get("spend")


def test_identify_returns_structured_conflicts(client):
    _customer(client, "cf-identify@x.com")
    d = client.post("/api/ingest/identify", files=[
        ("f0", ("ad_jun_a.csv", _JUNE_A, "text/csv")),
        ("f1", ("ad_jun_b.csv", _JUNE_B, "text/csv"))]).json()
    conflicts = d.get("conflicts", [])
    assert len(conflicts) == 1                       # the card appears
    c = conflicts[0]
    assert c["type"] == "period_overlap" and c["period"] == "2026-06"
    assert c["recommended"] == "keep_latest" and c["id"] == _CID
    assert c["impact"]["keep_latest"]["ad_spend"] == 1800.0
    assert c["impact"]["sum"]["ad_spend"] == 2800.0


def test_commit_skip_reproduces_take_latest(client):
    tid = _customer(client, "cf-skip@x.com")
    data, files = _commit_files(resolutions=None)    # skip resolution => today's default
    assert client.post("/api/onboard/reports", data=data, files=files).json()["provisioned"] is True
    assert _june(tid) == 1800.0                       # take-latest, NOT doubled


def test_commit_sum_choice_flows_through(client):
    tid = _customer(client, "cf-sum@x.com")
    data, files = _commit_files(resolutions={_CID: "sum"})
    assert client.post("/api/onboard/reports", data=data, files=files).json()["provisioned"] is True
    assert _june(tid) == 2800.0                       # user chose "add them up"


def _skus_files(resolutions=None):
    files = [("f0", ("439433020633.csv",
                     b"sku,asin,product-name,your-price,estimated-referral-fee-per-unit,estimated-fee-total\n"
                     b"S1,B1,Widget,1000,100,200\n", "text/csv")),
             ("f1", ("Autofy_COGS_Data.csv", b"sku,unit price\nS1,400\n", "text/csv")),
             ("f2", ("ad_jun_a.csv", _JUNE_A, "text/csv")),
             ("f3", ("ad_jun_b.csv", _JUNE_B, "text/csv"))]
    data = {} if resolutions is None else {"resolutions": json.dumps(resolutions)}
    return data, files


def test_skus_reimport_applies_resolution(client):
    """The Channels/Catalog 'Apply changes & re-import' path: re-POSTing the SAME (already-fingerprinted)
    files with a resolutions map MUST re-ingest with the choice — not be silently eaten by the dedupe
    guard. Regression for the critical review finding."""
    tid = _customer(client, "cf-reimport@x.com")
    data, files = _skus_files()
    r1 = client.post("/api/skus/upload", data=data, files=files).json()
    assert r1["ok"]
    assert any(c["type"] == "period_overlap" and c["id"] == _CID for c in r1.get("conflicts", []))
    assert _june(tid) == 1800.0                       # first upload: take-latest (today's default)
    # re-import identical files with the user's SUM choice
    data2, files2 = _skus_files(resolutions={_CID: "sum"})
    r2 = client.post("/api/skus/upload", data=data2, files=files2).json()
    assert r2["ok"]
    assert _june(tid) == 2800.0                       # resolution applied, NOT dropped as duplicate
