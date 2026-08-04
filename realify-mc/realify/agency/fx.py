"""Locked FX rate rows (agency-plan P4). Every cross-currency figure references an fx_rates row by id,
so a figure computed today stays reproducible even after the rate moves. Rates are global (no RLS).
rate_ppm = quote units per 1 USD × 1_000_000 (integer)."""
from . import money


def lock_rate(cur, as_of, quote, rate_ppm, base="USD"):
    """Insert/lock a rate; returns (id, rate_ppm)."""
    cur.execute(
        "INSERT INTO fx_rates(as_of, base, quote, rate_ppm) VALUES(%s,%s,%s,%s) "
        "ON CONFLICT (as_of, base, quote) DO UPDATE SET rate_ppm=EXCLUDED.rate_ppm RETURNING id, rate_ppm",
        (as_of, base, quote, int(rate_ppm)))
    return cur.fetchone()


def get_rate(cur, as_of, quote, base="USD"):
    """The locked (id, rate_ppm) for base->quote on as_of. USD identity is auto-locked at 1e6."""
    if quote == base:
        return lock_rate(cur, as_of, base, money.USD_IDENTITY_PPM, base)
    cur.execute("SELECT id, rate_ppm FROM fx_rates WHERE as_of=%s AND base=%s AND quote=%s",
                (as_of, base, quote))
    row = cur.fetchone()
    return row if row else None
