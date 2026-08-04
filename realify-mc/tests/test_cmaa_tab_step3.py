"""Step 3 — CMAA 'Profit & Ads' tab: confirmed-only, shared economics, certain/estimated split."""
import asyncio
import json

import pandas as pd

from realify import db
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.provenance_repo import ProvenanceRepository
from realify.repositories.ad_performance_repo import AdPerformanceRepository
from realify.repositories.revenue_period_repo import RevenuePeriodRepository
from realify.domain import cmaa, economics
from realify.routers import cmaa as cmaa_router


class _Req:
    """Minimal stand-in carrying the tenant the way require_tenant reads it."""
    def __init__(self, tid):
        self.state = type("S", (), {"tenant_id": tid})()
        self.session = {"tenant_id": tid}
        self.headers = {}
        self.cookies = {}


def _seed(con, tid, sku, **cols):
    seller = SellerRepository(con)
    row = {"internal_sku": sku, "asin": sku, "channel": "amazon"}
    row.update(cols)
    seller.upsert_full(tid, row)


def _call(tid):
    # require_tenant resolves from request; seed a session tenant
    import realify.routers.deps as deps
    orig = deps.require_tenant
    deps.require_tenant = lambda request: tid
    cmaa_router.require_tenant = lambda request: tid
    try:
        resp = cmaa_router.cmaa_tab(_Req(tid))
        return json.loads(bytes(resp.body).decode())
    finally:
        deps.require_tenant = orig
        cmaa_router.require_tenant = orig


class _PostReq(_Req):
    def __init__(self, tid, body):
        super().__init__(tid)
        self._body = body

    async def json(self):
        return self._body


def _post_action(tid, body):
    orig = cmaa_router.require_tenant
    cmaa_router.require_tenant = lambda request: tid
    try:
        resp = asyncio.run(cmaa_router.cmaa_action(_PostReq(tid, body)))
        return json.loads(bytes(resp.body).decode())
    finally:
        cmaa_router.require_tenant = orig


# ---- the tab agrees with domain math (PoC = tab = detector) ----------------
def test_tab_matches_domain_math():
    with db.connect() as con:
        _seed(con, 1, "S1", price=1000, cogs=400, referral_fee=100, fba_fee=100, units_month=50)
        ProvenanceRepository(con).set(1, "S1", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(1, "S1", "cogs", "seller", "seller", 400)
        AdPerformanceRepository(con).upsert(1, "S1", "2026-04-01", "month", 300, 1000)
        con.commit()
    d = _call(1)
    s = next(x for x in d["skus"] if x["sku"] == "S1")
    # gross unit = 1000-400-100-100 = 400 -> gcm 40%; ACoS = 300/1000 = 30%; margin ok, ads ok-ish
    assert s["gcm_pct"] == 40.0
    assert s["breakeven_acos"] == 40.0
    assert s["actual_acos"] == 30.0
    # wasted = max(300 - 1000*0.4, 0) = 0 -> efficient
    assert s["above_breakeven"] == 0.0
    assert s["quadrant"] == "SCALE"
    assert s["judged"] is True


def test_above_breakeven_and_quadrant():
    with db.connect() as con:
        # margin ok (40%) but overspending: ACoS 60% > breakeven 40%
        _seed(con, 2, "S2", price=1000, cogs=400, referral_fee=100, fba_fee=100, units_month=20)
        ProvenanceRepository(con).set(2, "S2", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(2, "S2", "cogs", "seller", "seller", 400)
        AdPerformanceRepository(con).upsert(2, "S2", "2026-04-01", "month", 600, 1000)
        con.commit()
    d = _call(2)
    s = next(x for x in d["skus"] if x["sku"] == "S2")
    assert s["quadrant"] == "FIX ADS"
    assert s["above_breakeven"] == 200.0     # 600 - 1000*0.4
    assert d["summary"]["total_above_breakeven"] == 200.0


# ---- period consistency: CMAA sums units/revenue over the SAME window as ad spend ----
def test_cmaa_window_consistent_across_multiple_ad_periods():
    """The bug: CMAA paired ONE month's units with ad spend summed over ALL ad periods (cumulative),
    driving CMAA wildly negative and letting ad_sales exceed the % denominator. Fix: contribution and
    net-revenue are summed over the SAME periods the ad totals span."""
    with db.connect() as con:
        # gross unit = 1000-400-100-100 = 400. One month = 50 units; advertised across 3 months.
        _seed(con, 7, "M1", price=1000, cogs=400, referral_fee=100, fba_fee=100, units_month=50)
        ProvenanceRepository(con).set(7, "M1", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(7, "M1", "cogs", "seller", "seller", 400)
        for per in ("2026-04-01", "2026-05-01", "2026-06-01"):
            AdPerformanceRepository(con).upsert(7, "M1", per, "month", 100, 800)   # S=300, AS=2400
            RevenuePeriodRepository(con).upsert(7, "M1", per, "month", 50000, 50)  # rev 150k, units 150
        con.commit()
    d = _call(7)
    s = next(x for x in d["skus"] if x["sku"] == "M1")
    # CMAA = gc_unit(400) × window units(150) − cumulative spend(300) = 59,700
    #   — NOT 400 × one_month(50) − 300 = 19,700 (the mismatched figure).
    assert s["cmaa"] == 59700.0
    assert s["cmaa"] != 19700.0
    # Invariant: net-revenue denominator ≥ ad_sales (impossible under the old mismatch).
    net_rev = s["cmaa"] / (s["cmaa_pct"] / 100.0)
    assert net_rev >= s["ad_sales"]
    assert s["ad_spend"] == 300.0 and s["ad_sales"] == 2400.0    # cumulative totals unchanged
    assert s["cmaa_pct"] == round(59700 / 150000 * 100, 1)       # 39.8%


# ---- confirmed-only: provisional SKUs are held out of the numbers ----------
def test_provisional_held_out():
    with db.connect() as con:
        _seed(con, 3, "S3", price=1000, cogs=400, referral_fee=100, fba_fee=100, provisional_units=9)
        AdPerformanceRepository(con).upsert(3, "S3", "2026-04-01", "month", 600, 1000)
        con.commit()
    d = _call(3)
    assert d["summary"]["held_provisional"] == 1
    assert d["summary"]["judged"] == 0
    assert d["summary"]["total_above_breakeven"] == 0.0


# ---- certain vs estimated split ------------------------------------------
def test_certain_vs_estimated_split():
    with db.connect() as con:
        # certain SKU (settled inputs)
        _seed(con, 4, "C1", price=1000, cogs=400, referral_fee=100, fba_fee=100)
        ProvenanceRepository(con).set(4, "C1", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(4, "C1", "cogs", "seller", "seller", 400)
        ProvenanceRepository(con).set(4, "C1", "referral_fee", "actual", "txn", 100)
        ProvenanceRepository(con).set(4, "C1", "fba_fee", "actual", "txn", 100)
        AdPerformanceRepository(con).upsert(4, "C1", "2026-04-01", "month", 600, 1000)
        # estimated SKU (fee-preview basis)
        _seed(con, 4, "E1", price=1000, cogs=400, referral_fee=100, fba_fee=100)
        ProvenanceRepository(con).set(4, "E1", "price", "reported", "fee", 1000)
        ProvenanceRepository(con).set(4, "E1", "cogs", "seller", "seller", 400)
        ProvenanceRepository(con).set(4, "E1", "fba_fee", "estimated", "fee", 100)
        AdPerformanceRepository(con).upsert(4, "E1", "2026-04-01", "month", 600, 1000)
        con.commit()
    d = _call(4)
    total = d["summary"]["total_above_breakeven"]
    certain = d["summary"]["certain_above_breakeven"]
    assert total == 400.0                       # 200 each
    assert certain == 200.0                     # only the certain SKU
    assert d["summary"]["estimated_above_breakeven"] == 200.0


# ---- scale upside: directional, SCALE-gated, BOUNDED (capped at a run-rate multiple) ---------
def test_scale_upside_domain_math():
    """Bounded: incremental ad-sales (capped at 2× run-rate) × (break-even − actual ACoS).
    be=0.41, acos=0.195: incremental = 42000×(2−1)=42000; upside = 42000×(0.41−0.195)=9030.0."""
    assert cmaa.scale_upside(8200, 42000, 0.41, 0.195) == 9030.0
    # not efficient (ACoS 60% ABOVE break-even 40%) -> None
    assert cmaa.scale_upside(600, 1000, 0.40, 0.60) is None
    # undecidable inputs never fabricate
    assert cmaa.scale_upside(300, 1000, None, 0.30) is None
    assert cmaa.scale_upside(300, 0, 0.40, None) is None
    assert cmaa.scale_upside(300, 1000, -0.10, 0.30) is None   # below cost, no upside


def test_scale_upside_bounded_invariant():
    """The load-bearing fix: per-SKU upside must never exceed its ad-sales headroom (ad_sales ×
    (multiple − 1)) — that's what the old headroom×(be/acos−1) method violated (₹50L on one SKU)."""
    cap = cmaa.SCALE_MAX_MULTIPLE - 1
    for spend, sales, be, ac in [(1000, 500000, 0.45, 0.02),   # tiny ACoS — the explosive case
                                 (200, 30000, 0.30, 0.05), (5000, 80000, 0.55, 0.20)]:
        u = cmaa.scale_upside(spend, sales, be, ac)
        assert u is not None and 0 < u <= sales * cap, (spend, sales, be, ac, u)


def test_scale_upside_in_tab_and_rollup():
    with db.connect() as con:
        # SCALE SKU: gcm 40%, ACoS 30% (efficient). incremental = 1000×(2−1)=1000;
        #   upside = 1000×(0.40−0.30) = 100.0.
        _seed(con, 8, "U1", price=1000, cogs=400, referral_fee=100, fba_fee=100, units_month=50)
        ProvenanceRepository(con).set(8, "U1", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(8, "U1", "cogs", "seller", "seller", 400)
        AdPerformanceRepository(con).upsert(8, "U1", "2026-04-01", "month", 300, 1000)
        # FIX ADS SKU (overspending) — must NOT get a scale upside.
        _seed(con, 8, "U2", price=1000, cogs=400, referral_fee=100, fba_fee=100, units_month=20)
        ProvenanceRepository(con).set(8, "U2", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(8, "U2", "cogs", "seller", "seller", 400)
        AdPerformanceRepository(con).upsert(8, "U2", "2026-04-01", "month", 600, 1000)
        con.commit()
    d = _call(8)
    u1 = next(x for x in d["skus"] if x["sku"] == "U1")
    u2 = next(x for x in d["skus"] if x["sku"] == "U2")
    assert u1["quadrant"] == "SCALE" and u1["scale_upside"] == 100.0
    assert u2["quadrant"] == "FIX ADS" and u2["scale_upside"] is None   # SCALE-gated
    assert d["summary"]["total_scale_upside"] == 100.0                  # directional roll-up
    assert d["summary"]["total_cut_bleed"] == 0.0                       # no CUT/DIVEST SKU


def test_every_number_emits_explain_shape_and_single_sourced():
    """Every calculated Ads number emits the shared explain shape, and each part's `result` equals
    the exact figure the worklist column shows (single-sourced → no expand-vs-column mismatch)."""
    with db.connect() as con:
        _seed(con, 11, "X1", price=1000, cogs=400, referral_fee=100, fba_fee=100, units_month=20)
        ProvenanceRepository(con).set(11, "X1", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(11, "X1", "cogs", "seller", "seller", 400)
        AdPerformanceRepository(con).upsert(11, "X1", "2026-04-01", "month", 600, 1000)  # FIX ADS
        RevenuePeriodRepository(con).upsert(11, "X1", "2026-04-01", "month", 20000, 20)
        con.commit()
    d = _call(11)
    k = next(x for x in d["skus"] if x["sku"] == "X1")
    ex = k["explain"]
    for key in ("breakeven_acos", "actual_acos", "recoverable", "ad_spend", "cmaa", "cmaa_pct"):
        p = ex[key]
        assert set(("label", "formula", "inputs", "result")).issubset(p), (key, p)
        assert isinstance(p["inputs"], list) and p["inputs"]
    # single-sourced: explain result == the displayed column figure
    assert ex["recoverable"]["result"] == k["above_breakeven"]
    assert ex["breakeven_acos"]["result"] == k["breakeven_acos"]
    assert ex["actual_acos"]["result"] == k["actual_acos"]
    assert ex["cmaa"]["result"] == k["cmaa"]
    # aggregates carry the shared shape too, with top contributors
    agg = d["summary"]["explain"]
    for key in ("total_above_breakeven", "total_scale_upside", "total_cut_bleed"):
        assert set(("formula", "result", "n", "top")).issubset(agg[key]), (key, agg[key])
    assert agg["total_above_breakeven"]["result"] == d["summary"]["total_above_breakeven"]


def test_cut_bleed_rollup():
    with db.connect() as con:
        # below cost (gcm negative) + spending -> CUT/DIVEST; bleed = the ad spend stopped.
        _seed(con, 9, "C9", price=1000, cogs=900, referral_fee=100, fba_fee=100, units_month=30)
        ProvenanceRepository(con).set(9, "C9", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(9, "C9", "cogs", "seller", "seller", 900)
        AdPerformanceRepository(con).upsert(9, "C9", "2026-04-01", "month", 500, 1000)
        con.commit()
    d = _call(9)
    c9 = next(x for x in d["skus"] if x["sku"] == "C9")
    assert c9["quadrant"] == "CUT/DIVEST"
    assert d["summary"]["total_cut_bleed"] == 500.0
    assert c9["scale_upside"] is None


# ---- decision→outcome loop: a recorded Move sticks (no Amazon write) --------
def test_action_records_move_and_sticks():
    with db.connect() as con:
        _seed(con, 10, "A1", price=1000, cogs=400, referral_fee=100, fba_fee=100, units_month=20)
        ProvenanceRepository(con).set(10, "A1", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(10, "A1", "cogs", "seller", "seller", 400)
        AdPerformanceRepository(con).upsert(10, "A1", "2026-04-01", "month", 600, 1000)
        con.commit()
    before = next(x for x in _call(10)["skus"] if x["sku"] == "A1")
    assert before["acted"] is False
    r = _post_action(10, {"sku": "A1", "action": "fix_ads", "summary": "pull ACoS to break-even",
                          "recoverable": 200.0})
    assert r["ok"] and r["recorded"] == 1
    after = next(x for x in _call(10)["skus"] if x["sku"] == "A1")
    assert after["acted"] is True                       # the Move is remembered on reload
    # an unknown action is rejected (fail closed)
    assert _post_action(10, {"sku": "A1", "action": "delete_everything"})["ok"] is False


# ---- SCALE profitability gate + CMAA reliability (Fix 1/2/3) -----------------
def test_scale_reliability_domain():
    # material spend + tiny settled base -> unreliable; healthy base or immaterial spend -> reliable
    assert cmaa.cmaa_reliable(58971, 170000, 1, 2000) is False        # 1 settled unit < floor
    assert cmaa.cmaa_reliable(6000, 90000, 5, 3000) is False          # ad-sales ≫ settled revenue
    assert cmaa.cmaa_reliable(5400, 7200, 90, 134910) is True         # healthy settled base
    assert cmaa.cmaa_reliable(200, 100, 0, 0) is True                 # immaterial ad spend
    # the gate
    assert cmaa.scale_gate("SCALE", -1000, True) == ("FIX MARGIN", False,
        cmaa.scale_gate("SCALE", -1000, True)[2])                     # efficient + CMAA<0 + reliable
    assert cmaa.scale_gate("SCALE", -1, False)[0:2] == ("SCALE", True)  # unreliable -> held
    assert cmaa.scale_gate("SCALE", 5, True) == ("SCALE", False, None)  # clean SCALE


def test_golden_afwcleaner0008_efficient_but_unreliable_cmaa_is_held():
    """Golden: efficient ACoS (SCALE pre-class) but 1 settled unit vs material ad spend across a
    3-period ad window with settled units in ONE period → CMAA<0 + unreliable → HELD, not a clean
    SCALE; CMAA% held; window-basis mismatch flagged; the reason is explainable."""
    with db.connect() as con:
        _seed(con, 20, "G8", price=2000, cogs=800, referral_fee=100, fba_fee=100, units_month=1)
        ProvenanceRepository(con).set(20, "G8", "price", "actual", "txn", 2000)
        ProvenanceRepository(con).set(20, "G8", "cogs", "seller", "seller", 800)
        for per in ("2026-04-01", "2026-05-01", "2026-06-01"):
            AdPerformanceRepository(con).upsert(20, "G8", per, "month", 19657, 56667)   # Σ≈58971 / 170001
        RevenuePeriodRepository(con).upsert(20, "G8", "2026-06-01", "month", 2000, 1)   # 1 settled unit, 1 period
        con.commit()
    g = next(x for x in _call(20)["skus"] if x["sku"] == "G8")
    assert g["actual_acos"] < g["breakeven_acos"]          # efficient — would be SCALE pre-gate
    assert g["cmaa_reliable"] is False                     # settled units lag ad spend
    assert g["cmaa_held"] is True and g["scale_upside"] is None    # not a confident SCALE, no upside surfaced
    assert g["cmaa_pct"] is None                           # CMAA % HELD (never −2276.5%)
    assert g["cmaa_window_mismatch"] is True               # CMAA window ⊊ recoverable window
    assert (g["explain"] or {}).get("classification")      # held reason is explainable on click
    assert "unreliable" in g["recommendation"]["headline"].lower()


def test_scale_gate_efficient_negative_cmaa_becomes_fix_margin():
    """Efficient ACoS + a RELIABLE settled base + CMAA<0 → demoted SCALE → FIX MARGIN with the
    fix-economics recommendation (don't scale a money-losing SKU)."""
    with db.connect() as con:
        _seed(con, 21, "M9", price=1000, cogs=500, referral_fee=0, fba_fee=0, units_month=10)
        ProvenanceRepository(con).set(21, "M9", "price", "actual", "txn", 1000)
        ProvenanceRepository(con).set(21, "M9", "cogs", "seller", "seller", 500)
        AdPerformanceRepository(con).upsert(21, "M9", "2026-04-01", "month", 6000, 13000)
        RevenuePeriodRepository(con).upsert(21, "M9", "2026-04-01", "month", 10000, 10)
        con.commit()
    m = next(x for x in _call(21)["skus"] if x["sku"] == "M9")
    assert m["actual_acos"] < m["breakeven_acos"] and m["cmaa_reliable"] is True and m["cmaa"] < 0
    assert m["quadrant"] == "FIX MARGIN" and m["scale_upside"] is None
    assert "losing money after ads" in m["recommendation"]["headline"].lower()
    assert _call(21)["summary"]["quadrants"]["FIX MARGIN"] >= 1
