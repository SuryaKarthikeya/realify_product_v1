"""Shared per-unit economics (reconciled from the Autofy PoC). Pure: no I/O, no app imports.

This is the single source of per-unit margin math, called by the SKU tab (1b) now and the CMAA
"Profit & Ads" tab (Step 3) later, so the number the PoC produced, the number the tab shows, and
the number a detector reports are computed the same way. Break-even ACoS = gross contribution
margin %, matching realify/domain/cmaa.py. Never fabricates: if price or COGS is unknown, the
margin fields are None and the caller shows a gap.
"""


def _z(x):
    return 0.0 if x is None else float(x)


def per_unit(price, cogs, referral_fee=None, fba_fee=None, return_cost_unit=None, ad_cost_unit=None):
    """Per-unit economics from settled inputs.

    gross_contribution_unit = price − COGS − referral − FBA − returns   (before ads)
    net_profit_unit         = gross_contribution_unit − ad_cost_unit
    net_margin_pct          = net_profit_unit / price
    breakeven_floor         = gross_contribution_unit / price   (= break-even ACoS %, per #004)

    Margin fields require BOTH price and COGS; otherwise they are None (undecidable, never guessed).
    """
    out = {"gross_contribution_unit": None, "net_profit_unit": None,
           "net_margin_pct": None, "breakeven_floor": None}
    if price is None or price <= 0 or cogs is None:
        return out
    gross = price - _z(cogs) - _z(referral_fee) - _z(fba_fee) - _z(return_cost_unit)
    net = gross - _z(ad_cost_unit)
    out["gross_contribution_unit"] = round(gross, 2)
    out["net_profit_unit"] = round(net, 2)
    out["net_margin_pct"] = round(100 * net / price, 2)
    out["breakeven_floor"] = round(100 * gross / price, 2)   # stored as a percentage
    return out


# Which provenance bases count as *certain* (settled/seller-supplied) vs *estimated* (modelled or
# fee-preview). The CMAA tab's robust "certain ₹ above break-even" headline is exactly the subset of
# SKUs whose economics rest only on certain inputs — this is that split, at the schema seam, so the
# tab and any detector classify identically (and the PoC's ₹328k-vs-₹363k distinction is reproduced).
_CERTAIN_BASES = {"actual", "seller"}
_ESTIMATED_BASES = {"estimated", "reported"}
_MARGIN_INPUTS = ("price", "cogs", "referral_fee", "fba_fee")


def certainty(field_basis, inputs=_MARGIN_INPUTS):
    """Given {field: basis} for the economic inputs present, return 'certain' if every present input
    is settled/seller, 'estimated' if any present input is modelled/fee-preview, else None (nothing
    to judge). Missing inputs don't downgrade certainty — absence is handled by per_unit() returning
    None, not by this flag."""
    present = [field_basis.get(f) for f in inputs if field_basis.get(f)]
    if not present:
        return None
    if any(b in _ESTIMATED_BASES for b in present):
        return "estimated"
    if all(b in _CERTAIN_BASES for b in present):
        return "certain"
    return "estimated"
