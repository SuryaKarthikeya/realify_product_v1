"""Profit & Ads: tester gets synthesized ad+revenue (fully working), customer with no data gets a
labeled SAMPLE preview that auto-clears once real data lands."""
import pytest
from starlette.testclient import TestClient
from realify import db


@pytest.fixture
def client():
    import run
    return TestClient(run.make_app())


def _signup(client, email, acct_type, mode):
    from realify import auth as _auth
    _auth.signup(email, "secret123", "X")               # /api/signup back door gated (P0.9)
    client.post("/api/login", json={"email": email, "password": "secret123"})
    with db.connect() as con:
        tid = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()["tenant_id"]
        db.set_account_type(con, tid, acct_type)
        db.set_tenant_provisioned(con, tid, mode)
        con.commit()
    return tid


def test_tester_profit_and_ads_is_synthesized_and_working(client):
    tid = _signup(client, "tester@x.com", "tester", "synthetic")
    from realify.ingest.synthetic import SyntheticSource
    SyntheticSource().provision(tid)
    d = client.get("/api/cmaa").json()
    assert d["ok"] and d["sample"] is False and d["synthetic"] is True
    s = d["summary"]
    assert s["judged"] >= 10                       # many SKUs judged
    assert s["certain_above_breakeven"] > 0        # provenance makes the headline meaningful
    assert (s["quadrants"]["SCALE"] + s["quadrants"]["FIX ADS"]) >= 1
    assert len(s["portfolio_tacos"]) >= 2          # TACoS-over-time present


def test_customer_empty_gets_labeled_sample_with_unlock_list(client):
    _signup(client, "cust@x.com", "customer", "uploaded")
    d = client.get("/api/cmaa").json()
    assert d["ok"] and d["sample"] is True
    assert any("Sponsored Products" in n for n in d["need"])
    assert any("COGS" in n for n in d["need"])
    assert d["have"]["ad_report"] is False
    assert len(d["skus"]) >= 4 and all(s["sku"].startswith("SAMPLE") for s in d["skus"])


def test_customer_sample_auto_clears_when_ad_data_lands(client):
    tid = _signup(client, "cust2@x.com", "customer", "uploaded")
    # seed one judged SKU: seller_skus + provenance + ad + revenue
    from realify.repositories.seller_repo import SellerRepository
    from realify.repositories.ad_performance_repo import AdPerformanceRepository
    from realify.repositories.revenue_period_repo import RevenuePeriodRepository
    from realify.repositories.provenance_repo import ProvenanceRepository
    with db.connect() as con:
        SellerRepository(con).upsert_full(tid, {
            "asin": "B1", "internal_sku": "B1", "title": "Real widget", "price": 1000, "cogs": 400,
            "referral_fee": 100, "fba_fee": 100, "units_month": 100})
        for f, v in (("price", 1000), ("cogs", 400), ("referral_fee", 100), ("fba_fee", 100)):
            ProvenanceRepository(con).set(tid, "B1", f, "seller", source="test", value=v)
        AdPerformanceRepository(con).upsert(tid, "B1", "2026-04-01", "month", 500, 800)
        RevenuePeriodRepository(con).upsert(tid, "B1", "2026-04-01", "month", 100000, 100)
        con.commit()
    d = client.get("/api/cmaa").json()
    assert d["sample"] is False               # real data -> preview gone, no toggle needed
    assert d["summary"]["judged"] >= 1
