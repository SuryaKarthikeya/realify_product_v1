"""Onboarding upload redesign — recognition + report-aware commit (integration through the HTTP app).

Drives the real endpoints via a test client: sign up, become a customer, identify dropped files
(green-check recognition), commit through the report-aware engine, and confirm the account is
provisioned and Profit & Ads is populated from the onboarding upload alone.
"""
import io

import pytest
from starlette.testclient import TestClient

from realify import db
from realify.ingest import report_catalog as cat
from realify.ingest.report_ingest import UNIFIED_TRANSACTION, COGS, FEE_PREVIEW, AD_REPORT


@pytest.fixture
def client():
    import run
    return TestClient(run.make_app())


# --- tiny synthetic Amazon exports -----------------------------------------
def _txn_csv():
    rows = ["settlement id,type,marketplace,Sku,product sales,quantity,selling fees,fba fees,other transaction fees,date/time"]
    for i in range(6):
        rows.append(f"1,Order,amazon.in,S1,1000,1,-100,-100,0,{15+i} Apr 2026 1:00:00 pm UTC")
    return "\n".join(rows).encode()


def _cogs_csv():
    return b"sku,unit price\nS1,400\n"


def _fee_csv():
    return (b"sku,asin,product-name,your-price,estimated-referral-fee-per-unit,estimated-fee-total\n"
            b"S1,B1,Widget,1000,100,200\n")


def _ad_csv():
    return (b"Date,Advertised ASIN,Spend,14 Day Total Sales,Total Advertising Cost of Sales\n"
            b"2026-04-10,B1,600,1000,0.6\n")


def _files():
    return [
        ("f0", ("2026AprMonthlyUnifiedTransaction.csv", _txn_csv(), "text/csv")),
        ("f1", ("Autofy_COGS_Data.csv", _cogs_csv(), "text/csv")),
        ("f2", ("439433020633.csv", _fee_csv(), "text/csv")),
        ("f3", ("Sponsored_Products.csv", _ad_csv(), "text/csv")),
    ]


def _make_customer(client, email="cust@example.com"):
    from realify import auth as _auth
    _auth.signup(email, "secret123", "Autofy Test")     # /api/signup back door gated (P0.9)
    r = client.post("/api/login", json={"email": email, "password": "secret123"})
    assert r.status_code == 200, r.text
    with db.connect() as con:
        row = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()
        tid = row["tenant_id"]
        db.set_account_type(con, tid, "customer")
        con.commit()
    return tid


def test_identify_recognizes_and_checklists(client):
    _make_customer(client)
    r = client.post("/api/ingest/identify", files=_files())
    assert r.status_code == 200, r.text
    d = r.json()
    present = {c["type"] for c in d["checklist"] if c["present"]}
    assert {UNIFIED_TRANSACTION, COGS, FEE_PREVIEW, AD_REPORT}.issubset(present)
    assert d["ready"] is True and d["has_cogs"] is True
    # every dropped file was recognized
    assert all(f["recognized"] for f in d["files"])


def test_report_aware_commit_provisions_and_populates_profit_and_ads(client):
    tid = _make_customer(client)
    r = client.post("/api/onboard/reports", data={"country": "IN"}, files=_files())
    assert r.status_code == 200, r.text
    assert r.json()["provisioned"] is True
    assert r.json()["skus_written"] >= 1
    with db.connect() as con:
        t = db.get_tenant(con, tid)
        assert t["provisioned"] == 1
    # onboarding upload alone should light up Profit & Ads
    cm = client.get("/api/cmaa").json()
    assert cm["ok"] and cm["summary"]["judged"] >= 1


def test_catalog_endpoint_lists_amazon_reports(client):
    _make_customer(client)
    d = client.get("/api/ingest/catalog").json()
    amazon = next(c for c in d["channels"] if c["channel"] == "amazon")
    assert amazon["active"] is True
    labels = {r["label"] for r in amazon["reports"]}
    assert "Monthly Unified Transaction" in labels and "COGS / unit costs" in labels


def test_onboard_reports_with_overlapping_reports_does_not_crash(client):
    """Two same-type reports covering the same month must raise a report_overlap confirmation and
    still provision — not 500 on the confirmation upsert (regression: missing 'suggested' arg)."""
    tid = _make_customer(client, email="overlap@x.com")
    ad2 = (b"Date,Advertised ASIN,Spend,14 Day Total Sales,Total Advertising Cost of Sales\n"
           b"2026-04-12,B1,300,900,0.33\n")
    files = _files() + [("f4", ("Sponsored_Products_2.csv", ad2, "text/csv"))]  # 2nd ad report, same month
    r = client.post("/api/onboard/reports", data={"country": "IN"}, files=files)
    assert r.status_code == 200, r.text
    assert r.json()["provisioned"] is True
    # the overlap was recorded as a pending confirmation, not swallowed
    ic = client.get("/api/interpretation").json()
    kinds = {c.get("kind") for c in ic.get("pending", [])}
    assert "report_overlap" in kinds
