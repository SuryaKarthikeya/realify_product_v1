"""Marketplace registry (1b.5) — default channel *treatments* so the common structural patterns
classify with zero seller input. Per-account confirmations (account_interpretation) override these.

A treatment decides how a marketplace's rows are scoped across ALL metrics (orders, refunds,
returns, fees) — the "both sides of every ratio" rule. An UNKNOWN marketplace is never silently
counted as Amazon; it is held provisional and raised as a pending confirmation.
"""
import re

AMAZON_DIRECT = "amazon_direct"     # counts in Amazon paid units / ASP / fees / returns (both sides)
OFF_AMAZON_MCF = "off_amazon_mcf"   # sold off-Amazon, fulfilled from FBA — Amazon revenue is ₹0 here
EXCLUDE = "exclude"                  # ignore entirely (seller opted out of this leg)
UNKNOWN = "unknown"                 # unrecognized -> provisional + confirmation

_DEFAULTS = [
    (r"^amazon\.in$", AMAZON_DIRECT, "Amazon.in (direct)"),
    (r"stores\.amazon\.in$", OFF_AMAZON_MCF, "Off-Amazon site via FBA (MCF)"),
    (r"^amazon\.(com|co\.uk|de|fr|it|es|ae|sa|sg|com\.au|com\.br|ca|com\.mx|co\.jp|nl|se|pl|com\.tr|eg)$",
     AMAZON_DIRECT, "Amazon (direct)"),
    (r"non-amazon|external|shopify", OFF_AMAZON_MCF, "Off-Amazon channel via FBA (MCF)"),
]


def default_treatment(marketplace):
    """(treatment, human_label) from the registry. Blank/missing/NaN -> amazon_direct (reports
    without a marketplace column are single-channel Amazon exports)."""
    try:
        m = str(marketplace).strip().lower()
    except Exception:
        m = ""
    if not m or m == "nan" or m == "none":
        return AMAZON_DIRECT, "Amazon (direct)"
    for pat, t, label in _DEFAULTS:
        if re.search(pat, m):
            return t, label
    return UNKNOWN, "Unrecognized marketplace"
