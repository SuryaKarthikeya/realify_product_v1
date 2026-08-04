"""A8: per-SKU break-even ACoS from COGS + settled revenue. The locked identity (#004) is
break-even ACoS = gross contribution margin % = contribution_before_ads / net_settled_revenue. Never
fabricated: an unknown margin yields None so the caller excludes the SKU."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_be_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.domain import economics, cmaa   # noqa: E402


def test_breakeven_from_cogs_and_price():
    # price 100, COGS 40, referral 15, FBA 10 -> gross contribution 35/unit
    e = economics.per_unit(price=100, cogs=40, referral_fee=15, fba_fee=10)
    gross = e["gross_contribution_unit"]
    assert abs(gross - 35.0) < 1e-9
    be = cmaa.breakeven_acos(cmaa.gcm_pct(gross, 100))     # net settled revenue/unit == price here
    assert abs(be - 0.35) < 1e-9                            # 35% ACoS is break-even for this SKU


def test_breakeven_uses_settled_revenue_denominator():
    # same contribution but net settled revenue/unit is higher than list price (e.g. bundled/settled)
    be = cmaa.breakeven_acos(cmaa.gcm_pct(35.0, 140.0))
    assert abs(be - 0.25) < 1e-9                            # 35/140
    # break-even is exactly the identity contribution / net settled revenue
    assert cmaa.breakeven_acos(cmaa.gcm_pct(35.0, 140.0)) == cmaa.gcm_pct(35.0, 140.0)


def test_unknown_margin_never_fabricated():
    assert cmaa.gcm_pct(None, 100) is None                 # missing contribution
    assert cmaa.gcm_pct(35.0, 0) is None                   # no revenue (all-refunded)
    assert cmaa.breakeven_acos(None) is None               # -> caller excludes the SKU, no guess


if __name__ == "__main__":
    test_breakeven_from_cogs_and_price()
    test_breakeven_uses_settled_revenue_denominator()
    test_unknown_margin_never_fabricated()
    print("breakeven_acos OK")
