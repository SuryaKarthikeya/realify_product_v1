"""SIMULATE — trust guards. A projected number without a working explain, a lone point where an
assumption drives it, a missing do-nothing baseline, a fabricated value on a missing input, or a
projection exceeding its computed ceiling — any of these breaks the feature's whole purpose.
"""
import os, tempfile, sys, json

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_sim_"), "test.db")
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                                    # noqa: E402
from realify.domain import simulate as S                  # noqa: E402
from realify.repositories.seller_repo import SellerRepository            # noqa: E402
from realify.repositories.provenance_repo import ProvenanceRepository    # noqa: E402
from realify.repositories.ad_performance_repo import AdPerformanceRepository  # noqa: E402
from realify.repositories.revenue_period_repo import RevenuePeriodRepository  # noqa: E402

_FIXADS = {"sku": "K1", "asin": "AS1", "title": "Storm Cover", "quadrant": "FIX ADS",
           "ad_spend": 9800, "ad_sales": 18000, "actual_acos": 54.4, "breakeven_acos": 26.5,
           "gcm_pct": 26.5, "above_breakeven": 5030, "cmaa": 26320, "units_month": 210,
           "recommendation": {"headline": "Good product, overspending on ads"}}
_SCALE = {"sku": "S1", "quadrant": "SCALE", "ad_sales": 42000, "actual_acos": 19.5,
          "breakeven_acos": 41.0, "scale_upside": 9030, "cmaa": 168120, "units_month": 380,
          "recommendation": {"headline": "Efficient — room to scale"}}
_CUT = {"sku": "C1", "quadrant": "CUT/DIVEST", "ad_spend": 5400, "cmaa": -16000, "units_month": 90,
        "recommendation": {"headline": "Losing on both — stop ads"}}
_FIXM = {"sku": "M1", "quadrant": "FIX MARGIN", "price": 499, "units_month": 140, "gcm_pct": 20.0,
         "recommendation": {"headline": "Fix the economics"}}


def _cells(sim):
    return [c for row in sim["projection"] for c in row["cells"]]


def test_every_projection_cell_has_explain_and_verbatim_result():
    for row in (_FIXADS, _SCALE, _CUT, _FIXM):
        sim = S.simulate(row, {})
        assert sim["can_simulate"], row["quadrant"]
        for c in _cells(sim):
            p = c["part"]
            assert p.get("formula") and isinstance(p.get("inputs"), list) and p["inputs"], p
            assert isinstance(p["result"], str) and "NaN" not in p["result"], p       # verbatim string, no NaN
        # the headline number is itself explainable
        assert sim["headline"]["explain"]["formula"] and "NaN" not in sim["headline"]["delta"]


def test_do_nothing_baseline_present():
    sim = S.simulate(_FIXADS, {})
    for row in sim["projection"]:
        assert "now" in row and "do_nothing" in row
    assert sim["headline"]["do_nothing"] and sim["headline"]["do_this"]


def test_assumption_edit_moves_dependent_projection():
    hi = S.simulate(_FIXADS, {"organic_hold": 0.9})["headline"]["delta"]
    lo = S.simulate(_FIXADS, {"organic_hold": 0.5})["headline"]["delta"]
    n = lambda s: float(s.replace("₹", "").replace(",", ""))
    assert n(hi) > n(lo), "higher organic-hold must project a larger CMAA gain"
    # a projection CELL also moves
    cell_hi = S.simulate(_FIXADS, {"organic_hold": 0.9})["projection"][2]["cells"][-1]["part"]["result"]
    cell_lo = S.simulate(_FIXADS, {"organic_hold": 0.5})["projection"][2]["cells"][-1]["part"]["result"]
    assert cell_hi != cell_lo


def test_ranges_present_where_assumption_driven():
    for row in (_FIXADS, _SCALE, _FIXM):
        rng = S.simulate(row, {})["headline"]["range"]
        assert set(rng) == {"conservative", "expected", "optimistic"} and all(rng.values())


def test_missing_input_degrades_honestly():
    sim = S.simulate({"sku": "X", "quadrant": "FIX ADS", "ad_spend": None,
                      "recommendation": {}}, {})
    assert sim["can_simulate"] is False and sim["missing"]
    assert "projection" not in sim                                      # never a fabricated projection


def test_fix_ads_90day_within_recoverable_ceiling():
    sim = S.simulate(_FIXADS, {"organic_hold": 1.0})                    # best case = full recoverable
    n = lambda s: float(s.replace("₹", "").replace(",", ""))
    assert n(sim["headline"]["delta"]) <= _FIXADS["above_breakeven"] + 0.5


def test_scale_gain_within_bounded_upside_ceiling():
    sim = S.simulate(_SCALE, {"acos_drift": 0.0})                       # best case
    n = lambda s: float(s.replace("₹", "").replace(",", ""))
    assert n(sim["headline"]["delta"]) <= _SCALE["scale_upside"] + 0.5


def test_monitor_explain_matches_displayed_value():
    """Blocker guard: for EVERY lever + checkpoint, the monitoring cell's explain.result must equal the
    displayed `expected` (opening the ⓘ must never contradict the number on screen)."""
    for row in (_FIXADS, _SCALE, _CUT, _FIXM):
        for m in S.simulate(row, {})["monitoring"]:
            if m.get("explain"):
                assert m["explain"]["result"] == m["expected"], (row["quadrant"], m["day"], m["expected"], m["explain"]["result"])


def test_assumptions_clamped_and_malformed_safe():
    # out-of-range max_multiple is clamped → SCALE gain still within the bounded ceiling
    sim = S.simulate(_SCALE, {"max_multiple": 99, "acos_drift": -5})
    n = lambda s: float(s.replace("₹", "").replace(",", ""))
    assert sim["can_simulate"] and n(sim["headline"]["delta"]) <= _SCALE["scale_upside"] + 0.5
    # the echoed assumption reflects the clamp (≤ declared max 2.0)
    mm = next(a for a in sim["assumptions"] if a["name"] == "max_multiple")
    assert mm["value"] <= mm["max"]
    # malformed / empty / NaN values never crash — they fall back to the sourced default
    for bad in ({"organic_hold": "abc"}, {"organic_hold": ""}, {"organic_hold": None}, {"ramp_days": float("nan")}):
        s = S.simulate(_FIXADS, bad)
        assert s["can_simulate"] and "NaN" not in s["headline"]["delta"]


def test_confidence_band_brackets_point_and_re_derives():
    """Bug 1 guard: the range is a LIVE function of the current assumptions. `expected` must equal the
    headline point on every simulate, the point must sit within [conservative, optimistic], and editing
    the key assumption must move the whole band (not just the point) — the honesty band can't decouple."""
    n = lambda s: float(s.replace("₹", "").replace(",", ""))
    for row in (_FIXADS, _SCALE, _CUT, _FIXM):
        hl = S.simulate(row, {})["headline"]
        r = hl["range"]
        assert r["expected"] == hl["delta"], (row["quadrant"], r["expected"], hl["delta"])   # expected == point
        assert n(r["conservative"]) <= n(hl["delta"]) <= n(r["optimistic"]), (row["quadrant"], r)
    # re-simulate with an edited assumption → the band moves AND expected tracks the new point
    a = S.simulate(_FIXADS, {"organic_hold": 0.7})["headline"]
    b = S.simulate(_FIXADS, {"organic_hold": 0.4})["headline"]
    assert a["range"] != b["range"], "band must move when the assumption changes, not stay frozen"
    for hl in (a, b):
        assert hl["range"]["expected"] == hl["delta"]
        assert n(hl["range"]["conservative"]) <= n(hl["delta"]) <= n(hl["range"]["optimistic"])
    # generalise to a second lever + assumption (SCALE / acos_drift)
    c = S.simulate(_SCALE, {"acos_drift": 0.2})["headline"]
    d = S.simulate(_SCALE, {"acos_drift": 0.8})["headline"]
    assert c["range"] != d["range"] and c["range"]["expected"] == c["delta"] and d["range"]["expected"] == d["delta"]


def test_header_field_is_recommendation_string_not_object():
    """Bug 2 guard: the header subtitle field (`rec_headline`) is the L2 recommendation STRING; the
    headline comparison OBJECT lives under a separate key. Interpolating the string can't yield
    '[object Object]', and the two keys never collide."""
    sim = S.simulate(_FIXADS, {})
    assert isinstance(sim["rec_headline"], str) and sim["rec_headline"] == _FIXADS["recommendation"]["headline"]
    assert isinstance(sim["headline"], dict) and "delta" in sim["headline"]      # the object, under its own key
    assert "[object Object]" not in json.dumps(sim)                              # fully JSON-serialisable, no stray objects


def test_sim_quality_degrade_classification():
    """Part A: a healthy row is 'useful'; a projection built on a null/weak base is 'degraded' with an
    L1-owned reason (the client pins a caution banner, still shows the projection), and a null base dims
    the headline point."""
    assert S.simulate(_FIXADS, {})["sim_quality"] == "useful"
    # SCALE with an undefined CMAA base → degraded + null_base flag (headline point dims to "—")
    sc = {**_SCALE, "cmaa": None, "units_month": None}
    r = S.simulate(sc, {})
    assert r["sim_quality"] == "degraded" and "undefined baseline" in r["degraded_reason"]
    assert r["headline"].get("null_base") is True and r["can_simulate"] is True     # projection still renders
    # FIX MARGIN with no volume → degraded, projects ₹0 (honest), not honest-empty
    r2 = S.simulate({**_FIXM, "units_month": 0}, {})
    assert r2["sim_quality"] == "degraded" and r2["can_simulate"] and r2["headline"]["delta"] == "₹0"
    # unreliable CMAA base → degraded but no null_base (a real base, just not trustworthy yet)
    r3 = S.simulate({**_FIXADS, "cmaa_reliable": False}, {})
    assert r3["sim_quality"] == "degraded" and not r3["headline"].get("null_base")


def test_simulation_carries_everything_the_csv_needs():
    sim = S.simulate(_FIXADS, {})
    assert sim["assumptions"] and all(a.get("name") and a.get("value") is not None for a in sim["assumptions"])
    assert all(row["cells"][0]["part"]["formula"] for row in sim["projection"])   # formula travels
    assert sim["monitoring"] and all(m.get("day") and m.get("tripwire") for m in sim["monitoring"])
    assert sim["disclaimer"] and sim["badge"] == "L1 · projection · directional"


# ---- endpoint: dual-mount, tenant-scoped, fail-closed ----------------------
def _seed_client(email="sim@x.com"):
    from run import make_app
    from fastapi.testclient import TestClient
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup(email, "password1")                    # /api/signup back door gated (P0.9)
    assert c.post("/api/login", json={"email": email, "password": "password1"}).json()["ok"]
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()["tenant_id"]
    db.set_account_type(con, tid, "tester")
    SellerRepository(con).upsert_full(tid, {"internal_sku": "K1", "asin": "AS1", "channel": "amazon",
        "category": "Auto", "price": 1000, "cogs": 400, "referral_fee": 100, "fba_fee": 100, "units_month": 20})
    ProvenanceRepository(con).set(tid, "K1", "price", "actual", "txn", 1000)
    ProvenanceRepository(con).set(tid, "K1", "cogs", "seller", "seller", 400)
    AdPerformanceRepository(con).upsert(tid, "K1", "2026-04-01", "month", 600, 1000)   # FIX ADS
    RevenuePeriodRepository(con).upsert(tid, "K1", "2026-04-01", "month", 20000, 20)
    con.commit(); con.close()
    return c


def test_simulate_endpoint_ok_and_dual_mount():
    c = _seed_client()
    for base in ("/api", "/api/v1"):
        d = c.post(base + "/cmaa/simulate", json={"sku": "K1"}).json()
        assert d["ok"] and d["simulation"]["can_simulate"] and d["simulation"]["projection"]


def test_simulate_fail_closed():
    from run import make_app
    from fastapi.testclient import TestClient
    db.init_db()
    assert TestClient(make_app()).post("/api/cmaa/simulate", json={"sku": "K1"}).status_code == 401


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
    print("simulate OK")
