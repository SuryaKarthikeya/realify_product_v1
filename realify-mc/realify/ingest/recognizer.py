"""Report recognizer — the header-fingerprint classifier + content hash, extracted from report_ingest
so new source types (Shopify, and later Walmart/TikTok) are added as DATA rows, not by editing a full
module. Detection is a 100%-signature substring match, greedy-best-wins; a signature token may be a
tuple meaning ANY-OF (e.g. Shopify inventory's "Available" OR "On hand").

Amazon signatures stay inline here (behavior-preserving). Shopify signatures are sourced from the
source-aware manifest (realify.topology) so "add a channel = add a manifest row" holds — the recognizer
and the checklist read the same rows rather than a third parallel list.
"""
import hashlib

import pandas as pd

# ---- Amazon report types + column signatures (unchanged; substring match on normalised headers) ----
BUSINESS_REPORT = "business_report"
UNIFIED_TRANSACTION = "unified_transaction"
FEE_PREVIEW = "fee_preview"
STORAGE_FEE = "storage_fee"
FBA_RETURNS = "fba_returns"
COGS = "cogs"
AD_REPORT = "ad_report"              # SP Advertised Product (the attributable, per-SKU ad file)
SEARCH_TERM = "search_term"          # SP Search Term (unlocks keyword-level: negatives + target bids)
AD_CAMPAIGN = "ad_campaign"          # SP campaign-summary (fallback only — NO per-SKU breakdown)
ALL_LISTINGS = "all_listings"
UNKNOWN = "unknown"

# Order matters: AD_REPORT and SEARCH_TERM precede AD_CAMPAIGN so a granular file (which also carries
# 'campaign name') wins the equal-token tie over the campaign-summary fallback (detect keeps the FIRST
# type to reach a full match). A campaign-summary file — no 'advertised asin', no 'customer search term'
# — matches only AD_CAMPAIGN, which the fidelity ladder reads as CHANNEL_ONLY / AD_GRANULARITY_INSUFFICIENT.
_AMAZON_SIGNATURES = {
    UNIFIED_TRANSACTION: ["settlement id", "product sales", "selling fees", "fba fees"],
    BUSINESS_REPORT:     ["(child) asin", "sessions - total", "units ordered"],
    FEE_PREVIEW:         ["estimated-referral-fee-per-unit", "estimated-fee-total"],
    STORAGE_FEE:         ["estimated-monthly-storage-fee", "average-quantity-on-hand"],
    FBA_RETURNS:         ["detailed-disposition", "return-date", "reason"],
    AD_REPORT:           ["advertised asin", "spend", "total advertising cost of sales"],
    SEARCH_TERM:         ["customer search term", "spend",
                          ("7 day total sales", "14 day total sales", "total sales")],
    AD_CAMPAIGN:         ["campaign name", "spend", "total advertising cost of sales"],
    ALL_LISTINGS:        ["seller-sku", "asin1"],
    COGS:                ["sku", "unit price"],
}

_SIG_CACHE = None


def _norm(h):
    return " ".join(str(h).strip().lower().split())


def _signatures():
    """Amazon (inline) + Shopify (from the source-aware manifest). Built once and cached; the manifest
    import is lazy so topology can stay free of any ingest import (no cycle)."""
    global _SIG_CACHE
    if _SIG_CACHE is None:
        from realify.topology import csv_fingerprints
        sigs = {k: list(v) for k, v in _AMAZON_SIGNATURES.items()}
        for rtype, tokens in csv_fingerprints().items():
            sigs[rtype] = [tuple(_norm(x) for x in tok) if isinstance(tok, (list, tuple)) else _norm(tok)
                           for tok in tokens]
        _SIG_CACHE = sigs
    return _SIG_CACHE


def _hit(tok, cols):
    """A signature token matches when its substring is in ANY column; a tuple token is ANY-OF."""
    if isinstance(tok, tuple):
        return any(any(alt in c for c in cols) for alt in tok)
    return any(tok in c for c in cols)


def detect_report_type(headers):
    """Classify by how many of a type's signature tokens appear; require the FULL signature,
    greedy-best-wins. COGS is intentionally last-resort (its 'sku'/'unit price' are generic) so a
    richer type always wins on more matched tokens."""
    cols = {_norm(h) for h in headers}
    best, best_score = UNKNOWN, 0
    for rtype, sig in _signatures().items():
        hits = sum(_hit(tok, cols) for tok in sig)
        if hits == len(sig) and hits > best_score:
            best, best_score = rtype, hits
    return best


def content_hash(df):
    """SHA-256 over the parsed + normalized table: columns sorted by name, rows sorted, cells
    stringified (NaN/None -> ""). Works positionally over df.values so duplicate column labels and
    mixed dtypes are handled. Identical data hashes identically regardless of column/row order or
    file container; any difference yields a different hash (a false 'duplicate' would require a
    SHA-256 collision). Safe direction: never matches two genuinely different reports."""
    if df is None:
        return hashlib.sha256(b"").hexdigest()
    cols = [str(c) for c in df.columns]
    order = sorted(range(len(cols)), key=lambda i: (cols[i], i))  # by name; stable on duplicates
    sorted_cols = [cols[i] for i in order]
    if len(df) == 0:
        return hashlib.sha256(("\x1e".join(sorted_cols)).encode("utf-8")).hexdigest()
    vals = df.values
    rows = []
    for r in vals:
        cells = ["" if (x is None or (isinstance(x, float) and pd.isna(x))) else str(x)
                 for x in (r[i] for i in order)]
        rows.append("\x1f".join(cells))
    rows.sort()
    payload = "\x1e".join(sorted_cols) + "\n" + "\n".join(rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
