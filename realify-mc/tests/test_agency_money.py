"""T-P4-06 formatting goldens + integer-minor FX seam (banker's rounding). Pure, default suite."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify.agency import money      # noqa: E402


def test_format_goldens():
    assert money.format_money(156000, "USD") == "$1,560"
    assert money.format_money(13100000, "INR") == "₹1,31,000"
    assert money.format_money(-156000, "USD") == "$-1,560"


def test_fx_usd_identity_is_passthrough():
    assert money.to_usd_minor(12345, money.USD_IDENTITY_PPM) == 12345


def test_fx_bankers_rounding_at_seam():
    # 5 / 2 = 2.5 -> even -> 2 ; 15 / 2 = 7.5 -> even -> 8
    assert money.to_usd_minor(5, 2_000_000) == 2
    assert money.to_usd_minor(15, 2_000_000) == 8
    # 1000 INR-minor at 83.5 INR/USD -> 1000*1e6/83_500_000 = 11.97 -> 12
    assert money.to_usd_minor(1000, 83_500_000) == 12
