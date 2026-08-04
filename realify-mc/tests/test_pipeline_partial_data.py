"""The detector pipeline must not crash on report-ingested SKUs that lack fields a full synthetic
row would have (no inventory report -> days_of_cover None; a SKU with no units -> annual_rev None).
Regression for the empty-dashboard bug: onboarding ran ingestion but the pipeline never ran / crashed."""
from realify import db, rules as _rules
from realify.repositories.tenant_repo import TenantRepository
from realify.repositories.seller_repo import SellerRepository
from realify.pipeline.materialize import run_pipeline


def test_pipeline_survives_partial_report_ingested_skus():
    _rules.seed_catalog()          # threshold rules (e.g. PRICE-01 net_margin<12) must be present to fire
    with db.connect() as con:
        tid = TenantRepository(con).create("Partial"); con.commit()
        s = SellerRepository(con)
        # a normal report-ingested SKU: has units + price (so revenue derives) but NO inventory fields
        s.upsert_full(tid, {"asin": "A1", "internal_sku": "A1", "title": "Cover", "ptype": "Bike Cover",
                            "price": 500, "cogs": 200, "units_month": 30, "buybox_pct": 70,
                            "net_margin_pct": 60.0,   # healthy -> does NOT trip the margin rule
                            "annual_rev_inr": 180000, "velocity_day": 1.0, "days_of_cover": None})
        # a pathological SKU: no units, no price -> annual_rev_inr None (must not crash the ranker)
        s.upsert_full(tid, {"asin": "A2", "internal_sku": "A2", "title": "Odd", "ptype": "Other",
                            "price": None, "cogs": None, "units_month": None, "annual_rev_inr": None})
        # a SKU that TRIPS a threshold detector (net_margin_pct 5 < the 12 floor of PRICE-01) as the
        # SOLE match, yet has annual_rev_inr None — so it becomes `best` and reaches the
        # exposure_inr = annual_rev_inr/12 line in detect.py, which crashed on None (the prod scheduler
        # bug: "unsupported operand type(s) for /: 'NoneType' and 'int'").
        s.upsert_full(tid, {"asin": "A3", "internal_sku": "A3", "title": "ThinMargin", "ptype": "Widget",
                            "category": "Widgets", "price": 500, "cogs": 470, "units_month": 20,
                            "buybox_pct": 90, "net_margin_pct": 5.0, "annual_rev_inr": None,
                            "velocity_day": 0.6, "days_of_cover": 20})
        con.commit()
    # must complete without raising (the crash was TypeError: NoneType / int in the detector exposure)
    r = run_pipeline(tid)
    assert r is not None
