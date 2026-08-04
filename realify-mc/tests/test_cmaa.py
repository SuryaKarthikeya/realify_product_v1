"""Pure CMAA math (realify/domain/cmaa.py) — break-even, waste, quadrant, and the honest
None-handling (unknown margin is never assumed)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from realify.domain import cmaa  # noqa: E402


def test_gcm_and_breakeven():
    assert cmaa.gcm_pct(30, 100) == 0.3
    assert cmaa.breakeven_acos(0.3) == 0.3
    assert cmaa.gcm_pct(5, 0) is None          # no revenue -> undecidable
    assert cmaa.gcm_pct(5, -10) is None


def test_acos():
    assert abs(cmaa.acos(18, 100) - 0.18) < 1e-9
    assert cmaa.acos(50, 0) is None            # spend, zero attributed sales


def test_wasted_spend():
    assert abs(cmaa.wasted_spend(100, 200, 0.3) - 40) < 1e-9   # 100 - 200*.3
    assert cmaa.wasted_spend(30, 200, 0.3) == 0.0              # below break-even
    assert cmaa.wasted_spend(100, 0, None) == 100             # no sales, unknown margin -> all wasted
    assert cmaa.wasted_spend(100, 50, None) is None           # sales but unknown margin -> undecidable


def test_quadrant():
    assert cmaa.quadrant(0.30, 0.18, 0.30) == "SCALE"
    assert cmaa.quadrant(0.30, 0.40, 0.30) == "FIX ADS"
    assert cmaa.quadrant(0.10, 0.08, 0.10, margin_floor=0.15) == "FIX MARGIN"
    assert cmaa.quadrant(-0.20, 0.50, -0.20) == "CUT/DIVEST"
    assert cmaa.quadrant(None, 0.2, None) is None             # unknown margin -> undecidable
    assert cmaa.quadrant(0.3, None, 0.3) == "FIX ADS"         # no attributed sales = ads not ok


def test_evaluate_endtoend():
    r = cmaa.evaluate(ad_spend=100, ad_sales=200, contribution=30, net_revenue=100)
    assert r["breakeven_acos"] == 0.3 and abs(r["actual_acos"] - 0.5) < 1e-9
    assert abs(r["wasted_spend"] - 40) < 1e-9 and r["quadrant"] == "FIX ADS"
