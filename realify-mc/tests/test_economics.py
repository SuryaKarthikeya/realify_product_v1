"""Shared per-unit economics (realify/domain/economics.py) + parity with the CMAA break-even so the
PoC, the SKU tab, and the future CMAA tab compute the same number."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from realify.domain import economics, cmaa  # noqa: E402


def test_per_unit_basic():
    e = economics.per_unit(500, 100, 50, 40, 10, 0)
    assert e["gross_contribution_unit"] == 300     # 500 - 100 - 50 - 40 - 10
    assert e["net_profit_unit"] == 300
    assert e["net_margin_pct"] == 60.0
    assert e["breakeven_floor"] == 60.0


def test_ad_cost_reduces_net_only():
    e = economics.per_unit(500, 100, 50, 40, 10, 30)
    assert e["gross_contribution_unit"] == 300 and e["net_profit_unit"] == 270


def test_missing_inputs_never_fabricated():
    assert economics.per_unit(None, 100)["net_margin_pct"] is None
    assert economics.per_unit(500, None)["net_margin_pct"] is None      # no COGS -> no margin guess
    assert economics.per_unit(0, 100)["breakeven_floor"] is None


def test_parity_with_cmaa_breakeven():
    """economics break-even % must equal cmaa break-even ACoS on the same per-unit basis."""
    e = economics.per_unit(500, 100, 50, 40, 10, 0)
    units = 7
    gcm = cmaa.gcm_pct(e["gross_contribution_unit"] * units, 500 * units)
    assert abs(cmaa.breakeven_acos(gcm) * 100 - e["breakeven_floor"]) < 1e-9
