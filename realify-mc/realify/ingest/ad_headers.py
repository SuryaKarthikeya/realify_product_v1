"""Rules-as-data header-alias map for Amazon Ads CSV exports — the SINGLE place real column names are
locked (spec "Verify-before-build #1"). Everything downstream reads columns through `resolve()`, never
by hardcoding a header string, so correcting for a real export = editing the alias lists here only.

>>> VERIFY-BEFORE-LOCK <<<
The alias lists below are seeded from Amazon's current US-console export columns (and the header strings
already present in this repo's tests). Amazon varies these by locale/console version. Confirm them against
one real customer export of each report and adjust the alias lists — no other file should need changing.

Matching: a field resolves to the first report column whose normalized header CONTAINS one of the field's
aliases, aliases tried most-specific-first (so 'total sales' wins before a bare 'sales', and the ACOS
column is never mistaken for attributed sales — its header is 'total advertising cost of sales', which
does not contain the contiguous substring 'total sales').
"""

# canonical field -> ordered aliases (most specific first), matched as normalized substrings
_ALIASES = {
    "date":                 ["date"],
    "campaign":             ["campaign name", "campaign"],
    "ad_group":             ["ad group name", "ad group", "adgroup"],
    "advertised_sku":       ["advertised sku"],
    "advertised_asin":      ["advertised asin"],
    "targeting":            ["targeting", "keyword text", "keyword"],
    "match_type":           ["match type"],
    "customer_search_term": ["customer search term", "search term"],
    "spend":                ["spend"],
    # attributed sales: 'total sales' matches '7/14 Day Total Sales' but NOT 'Total Advertising Cost of
    # Sales' (no contiguous 'total sales') nor 'Advertised SKU Sales'.
    "sales":                ["7 day total sales", "14 day total sales", "total sales"],
    "acos":                 ["total advertising cost of sales", "acos"],
    "clicks":               ["clicks"],
    "impressions":          ["impressions"],
    "orders":               ["7 day total orders", "total orders"],
    "units":                ["7 day total units", "total units"],
}

# which canonical fields each report type is expected to carry (drives extraction + fidelity)
FIELDS_BY_REPORT = {
    "ad_report":   ["date", "campaign", "ad_group", "advertised_sku", "advertised_asin",
                    "spend", "sales", "acos", "clicks", "orders", "units"],
    "search_term": ["date", "campaign", "ad_group", "targeting", "match_type", "customer_search_term",
                    "advertised_asin", "spend", "sales", "acos", "clicks", "orders"],
    "ad_campaign": ["date", "campaign", "spend", "sales", "acos", "clicks", "orders"],
}


def _norm(h):
    return " ".join(str(h).strip().lower().split())


def resolve(columns, field):
    """Return the actual column label in `columns` for a canonical `field`, or None if absent.
    Aliases are tried in order (most specific first); the first column containing an alias wins."""
    norm = {c: _norm(c) for c in columns}
    for alias in _ALIASES.get(field, []):
        for col, n in norm.items():
            if alias in n:
                return col
    return None


def resolve_all(columns, report_type):
    """{canonical_field: actual_column} for every expected field of a report type that is present."""
    out = {}
    for field in FIELDS_BY_REPORT.get(report_type, []):
        col = resolve(columns, field)
        if col is not None:
            out[field] = col
    return out


def has_sku_granularity(columns):
    """True when a file exposes per-advertised-product granularity (SKU or ASIN) — the make-or-break
    signal that separates an Advertised Product file from a campaign-summary file."""
    return resolve(columns, "advertised_asin") is not None or resolve(columns, "advertised_sku") is not None
