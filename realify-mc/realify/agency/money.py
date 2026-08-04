"""Money helpers for the agency console (agency-plan P4). Amounts are INTEGER minor units end to end;
the only place a non-integer appears is the FX conversion seam, which uses Decimal with banker's
rounding (§1c-4) — never float. Display grouping reuses the Indian-grouping helper from domain.cmaa
(country.py's fmt_money abbreviates to L/cr, which doesn't match the full-grouping goldens)."""
from decimal import Decimal, ROUND_HALF_EVEN

from ..domain.cmaa import _inr_group

USD_IDENTITY_PPM = 1_000_000
_SYMBOL = {"USD": "$", "INR": "₹"}


def to_usd_minor(amount_minor, rate_ppm):
    """Convert selling-currency minor units to USD minor units via a locked rate_ppm (quote-per-USD
    × 1e6). Banker's rounding at the seam. USD identity (rate_ppm == 1e6) returns the input."""
    rate_ppm = int(rate_ppm)
    if rate_ppm <= 0:
        return 0
    if rate_ppm == USD_IDENTITY_PPM:
        return int(amount_minor)
    q = (Decimal(int(amount_minor)) * Decimal(USD_IDENTITY_PPM) / Decimal(rate_ppm)).quantize(
        Decimal(1), rounding=ROUND_HALF_EVEN)
    return int(q)


def usd_to_quote_minor(usd_minor, rate_ppm):
    """Convert USD minor units to quote-currency minor units via rate_ppm (quote-per-USD × 1e6).
    Banker's rounding. Used for the INR reference total on IN-agency invoices (exact vs the rate row)."""
    q = (Decimal(int(usd_minor)) * Decimal(int(rate_ppm)) / Decimal(USD_IDENTITY_PPM)).quantize(
        Decimal(1), rounding=ROUND_HALF_EVEN)
    return int(q)


def format_money(minor, currency):
    """Full en-IN / Western digit grouping of whole units (goldens: $1,560 / ₹1,31,000)."""
    units = int(minor) // 100
    sym = _SYMBOL.get(currency, "")
    if currency == "INR":
        return f"{sym}{_inr_group(units)}"
    neg = units < 0
    return f"{sym}{'-' if neg else ''}{abs(units):,}"
