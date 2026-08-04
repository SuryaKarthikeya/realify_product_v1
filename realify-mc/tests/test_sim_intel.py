"""SIMULATE for Intelligence cards — trust guards across the full detector→model map.

Every simulatable detector must: project only over own L1 data × a stated assumption; keep
expected == the headline point after a re-simulate; never emit NaN / [object Object] / a corrupted
operator; carry a do-nothing baseline; degrade honestly (or show a disclaimer / no button) when it
can't; and default targets to the tenant's own detector threshold.
"""
import os, tempfile, json, math, sys

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_si_"), "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                                        # noqa: E402
from realify.domain import sim_intel as SI                    # noqa: E402
from realify.repositories.seller_repo import SellerRepository # noqa: E402
from realify.repositories.card_repo import CardRepository     # noqa: E402

_ROW = dict(price=500, cogs=200, referral_fee=50, fba_fee=30, return_cost_unit=20, net_margin_pct=24.0,
            units_month=200, velocity_day=6.5, stock_on_hand=40, days_of_cover=6, buybox_pct=62.0,
            rating=3.7, review_count=35, returns_rate=12.0, tacos=22.0, rev_share_pct=9.0,
            annual_rev_inr=500 * 200 * 12, sessions=8000, conversion_pct=6.0)


def _ctx(card_type, field=None, op=None, row=None, **kw):
    return dict(card_type=card_type, field=field, op=op, sku="K1", asin="AS1", title="T", category="Auto",
                finding="finding", family="x", exposure_inr=kw.get("exposure_inr", 230000),
                threshold=kw.get("threshold"), threshold_customized=kw.get("cust", False),
                row=row if row is not None else dict(_ROW), portfolio_rev=kw.get("pr", 2.0e6))


def _n(s):
    return float(str(s).replace("₹", "").replace(",", "").replace("%", "").replace(" units", "").replace(" days", ""))


# card_type, field, op, expected canonical detector
_SIMULATABLE = [
    ("MARGIN-09", "net_margin_pct", "lt", "margin-vs-floor"), ("OPP-04", "net_margin_pct", "gt", "margin-headroom"),
    ("CASH-29", "returns_rate", "gt", "returns-rate"), ("SHARE-02", "rev_share_pct", "gt", "revenue-share"),
    ("SV-01", "conversion_pct", "lt", "conversion"), ("SALES-05", "velocity_day", "gt", "velocity"),
    ("C3", None, None, "rank-movement"), ("INV-17", "days_of_cover", "lt", "days-of-cover"),
    ("INV-19", "stock_on_hand", "lt", "stock-level"), ("ADS-22", "tacos", "gt", "tacos"),
    ("BB-OWN", None, None, "buy-box-ownership"), ("C1", None, None, "price-competitiveness"),
    ("RR-01", "rating", "lt", "rating"), ("RR-02", "review_count", "lt", "review-count"),
    ("C5", None, None, "opportunity"), ("C6", None, None, "assortment-breadth"),
]


def test_detector_dispatch_map():
    for ct, fld, op, det in _SIMULATABLE:
        assert SI.detector_id(ct, fld, op) == det, (ct, det)
    # margin op flips the model: lt = below floor, gt = headroom
    assert SI.detector_id("OPP-01", "net_margin_pct", "gt") == "margin-headroom"


def test_no_button_for_context_cards():
    for ct in ("C7", "C8", "C9"):
        assert not SI.simulatable(ct)
    for ct, fld, op, _ in _SIMULATABLE:
        assert SI.simulatable(ct, fld, op), ct


def test_every_model_traceable_no_nan_no_object_baseline_and_expected_equals_point():
    for ct, fld, op, det in _SIMULATABLE:
        s = SI.simulate_card(_ctx(ct, fld, op), {})
        js = json.dumps(s)
        assert "NaN" not in js and "[object Object]" not in js and "None%" not in js, (ct, js[:200])
        if not s["can_simulate"]:
            continue
        # every projection cell is an explain part rendering a verbatim string result
        for row in s["projection"]:
            assert "now" in row and "do_nothing" in row                       # do-nothing baseline
            for c in row["cells"]:
                p = c["part"]
                assert p["formula"] and isinstance(p["inputs"], list) and isinstance(p["result"], str)
                assert "NaN" not in p["result"]
        hl = s["headline"]
        assert hl["range"]["expected"] == hl["delta"], (ct, hl["range"]["expected"], hl["delta"])
        assert _n(hl["range"]["conservative"]) <= _n(hl["delta"]) <= _n(hl["range"]["optimistic"]) or \
               _n(hl["range"]["conservative"]) == _n(hl["range"]["optimistic"]), (ct, hl["range"])
        assert s["monitoring"] and all(m.get("day") and m.get("tripwire") for m in s["monitoring"])


def test_monitor_explain_matches_displayed_value_every_model():
    """The #014 blocker class: opening a monitoring cell's ⓘ must never contradict the value on screen."""
    for ct, fld, op, _ in _SIMULATABLE + [("C2", None, None, None)]:
        s = SI.simulate_card(_ctx(ct, fld, op), {})
        for m in s.get("monitoring", []):
            if m.get("explain"):
                assert m["explain"]["result"] == m["expected"], (ct, m["day"], m["expected"], m["explain"]["result"])


def test_extreme_rows_never_crash_or_nan():
    """Division-safety: tiny/degenerate own-data must degrade or project cleanly, never NaN/inf/crash."""
    edge = dict(price=1, cogs=0.5, referral_fee=0, fba_fee=0, return_cost_unit=0, net_margin_pct=1.0,
                units_month=1, velocity_day=0.01, stock_on_hand=1, days_of_cover=100, buybox_pct=1.0,
                rating=1.0, review_count=1, returns_rate=0.5, tacos=0.5, rev_share_pct=0.1,
                annual_rev_inr=12, sessions=1, conversion_pct=0.1)
    for ct, fld, op, _ in _SIMULATABLE:
        s = SI.simulate_card(_ctx(ct, fld, op, edge), {})
        js = json.dumps(s)
        assert "NaN" not in js and "Infinity" not in js, (ct, js[:160])


def test_band_re_derives_and_expected_tracks_point_on_re_simulate():
    a = SI.simulate_card(_ctx("MARGIN-09", "net_margin_pct", "lt"), {"demand_elasticity": 0.8})["headline"]
    b = SI.simulate_card(_ctx("MARGIN-09", "net_margin_pct", "lt"), {"demand_elasticity": 2.5})["headline"]
    assert a["range"] != b["range"] and a["range"]["expected"] == a["delta"] and b["range"]["expected"] == b["delta"]


# ---- per-model sanity ------------------------------------------------------
def test_reorder_cover_math_and_overstock_flag():
    s = SI.simulate_card(_ctx("INV-17", "days_of_cover", "lt"), {})
    # days-of-cover row declines by one day per calendar day (now cover ≈ 40/6.5 ≈ 6.2d → stockout inside 90d)
    dc = next(r for r in s["projection"] if r["metric"] == "Days of cover")
    assert dc["cells"][-1]["part"]["result"] == "0 days"                       # stocked out by day 90
    # an oversized reorder trips the overstock (cash-trapped) degrade
    big = SI.simulate_card(_ctx("INV-17", "days_of_cover", "lt"), {"reorder_qty": 100000})
    assert big["sim_quality"] == "degraded" and "overstock" in big["degraded_reason"]


def test_concentration_shock_arithmetic():
    s = SI.simulate_card(_ctx("SHARE-02", "rev_share_pct", "gt"), {"shock_pct": 20})
    this_rev = _ROW["annual_rev_inr"] / 12.0
    assert math.isclose(_n(s["headline"]["delta"]), round(this_rev * 0.20 * 0.24, 2), rel_tol=0.02)


def test_gap_capture_within_gap_times_capture_times_margin():
    s = SI.simulate_card(_ctx("C5", exposure_inr=230000), {"capture_pct": 10, "est_margin_pct": 20})
    assert _n(s["headline"]["delta"]) <= 230000 * 0.10 * 0.20 + 0.5
    assert s["sim_quality"] == "degraded"                                      # estimate · directional


def test_tacos_gain_never_exceeds_spend_saved():
    s = SI.simulate_card(_ctx("ADS-22", "tacos", "gt", threshold=14.0), {"organic_hold": 0.5})
    sales = _ROW["price"] * _ROW["units_month"]
    saved = (_ROW["tacos"] - 14.0) / 100.0 * sales
    assert _n(s["headline"]["delta"]) <= saved + 0.5


# ---- degrade / honest-empty paths -----------------------------------------
def test_missing_data_degrades_honestly():
    assert SI.simulate_card(_ctx("INV-17", "days_of_cover", "lt", {**_ROW, "stock_on_hand": None}), {})["can_simulate"] is False
    assert SI.simulate_card(_ctx("SV-01", "conversion_pct", "lt", {**_ROW, "sessions": None}), {})["can_simulate"] is False
    # reviews are GATED on conversion data — no CVR → honest-empty, never a confident point
    rr = SI.simulate_card(_ctx("RR-01", "rating", "lt", {**_ROW, "sessions": None, "conversion_pct": None}), {})
    assert rr["can_simulate"] is False and "can't be projected" in rr["missing"]


def test_competition_density_is_disclaimer_only():
    s = SI.simulate_card(_ctx("C2"), {})
    assert s["disclaimer_only"] is True and s["can_simulate"] is False and s["monitoring"]
    assert "projection" not in s                                              # never a fabricated projection


def test_zero_volume_degrades_but_still_projects():
    s = SI.simulate_card(_ctx("MARGIN-09", "net_margin_pct", "lt", {**_ROW, "units_month": 0}), {})
    assert s["can_simulate"] and s["sim_quality"] == "degraded" and s["headline"]["delta"] == "₹0"


def test_threshold_sourced_default_uses_tenant_value_and_labels_customization():
    s = SI.simulate_card(_ctx("ADS-22", "tacos", "gt", threshold=11.0, cust=True), {})
    tt = next(a for a in s["assumptions"] if a["name"] == "target_tacos")
    assert tt["value"] == 11.0 and "customized" in tt["source"]


def test_out_of_range_assumptions_clamped_and_malformed_safe():
    s = SI.simulate_card(_ctx("MARGIN-09", "net_margin_pct", "lt"), {"price_change_pct": 99, "demand_elasticity": -5})
    assert s["can_simulate"] and "NaN" not in json.dumps(s)
    for bad in ({"capture_pct": "abc"}, {"capture_pct": ""}, {"capture_pct": None}):
        assert SI.simulate_card(_ctx("C5"), bad)["can_simulate"]


# ---- endpoint: {card_id}, dual-mount, fail-closed --------------------------
def _seed():
    from run import make_app
    from fastapi.testclient import TestClient
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup("si@x.com", "password1")               # /api/signup back door gated (P0.9)
    c.post("/api/login", json={"email": "si@x.com", "password": "password1"})
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email=?", ("si@x.com",)).fetchone()["tenant_id"]
    db.set_account_type(con, tid, "tester")
    SellerRepository(con).upsert_full(tid, {"internal_sku": "SK1", "asin": "AZ1", "channel": "amazon",
        "category": "Auto", "title": "Widget", **_ROW})
    con.execute("INSERT INTO traffic(tenant_id,channel,internal_sku,date,sessions,page_views,conversion_pct,buybox_pct)"
                " VALUES(?,?,?,?,?,?,?,?)", (tid, "amazon", "SK1", "2026-06-01", 8000, 11000, 6.0, 62))
    CardRepository(con).upsert(dict(dedup_key="dk", tenant_id=tid, run_id=1, card_type="INV-17", family="demand",
        type_name="Cover", asin="AZ1", category="Auto", finding="cover low", why="", severity="act", sev_label="Act",
        confidence=70, conf_label="High", exposure_label="rev", exposure_pct=55, exposure_val="x", action="Reorder",
        sources="[]", minis="[]", provenance="[]", is_new=1, rank_score=1, created_at=db.now_iso(), updated_at=db.now_iso()))
    con.commit()
    cid = con.execute("SELECT id FROM cards WHERE tenant_id=? AND card_type='INV-17'", (tid,)).fetchone()["id"]
    con.close()
    return c, cid


def test_endpoint_card_id_dual_mount_and_fail_closed():
    c, cid = _seed()
    for base in ("/api", "/api/v1"):
        d = c.post(base + "/cmaa/simulate", json={"card_id": cid}).json()
        assert d["ok"] and d["simulation"]["can_simulate"] and d["simulation"]["bucket"] == "days-of-cover"
    from run import make_app
    from fastapi.testclient import TestClient
    assert TestClient(make_app()).post("/api/cmaa/simulate", json={"card_id": cid}).status_code == 401
    assert c.post("/api/cmaa/simulate", json={"card_id": 999999}).status_code == 404


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("sim_intel OK")
