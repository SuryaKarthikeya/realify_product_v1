"""Report-aware ingestion (Step 1a) — the backbone that replaces the catalog-only `parse_many`.

Given a bag of uploaded Amazon reports (any mix, any order), this:
  1. detects each file's *type* by its column signature (not filename),
  2. extracts that report's real fields, keyed to SKU or ASIN, each value carrying provenance
     (which report it came from + whether it's an ACTUAL, ESTIMATED, REPORTED, or SELLER value),
  3. resolves ASIN-keyed rows to SKU via a built identity map,
  4. merges into one per-SKU record, applying precedence (actual beats estimated), and
  5. never fabricates: a field we don't have stays absent and is reported as a gap.

Pandas is used here (ingest layer); the pure decision logic stays in `realify/domain/`.
"""
from dataclasses import dataclass, field as _dc_field
from typing import Optional

import pandas as pd

# The header-fingerprint recognizer + content hash now live in realify.ingest.recognizer (extracted so
# new source types are added as DATA rows there without editing this near-full module). Re-exported here
# so existing callers keep importing them from report_ingest unchanged.
from realify.ingest.recognizer import (  # noqa: F401  (re-export for back-compat)
    content_hash, detect_report_type, _norm,
    BUSINESS_REPORT, UNIFIED_TRANSACTION, FEE_PREVIEW, STORAGE_FEE,
    FBA_RETURNS, COGS, AD_REPORT, SEARCH_TERM, AD_CAMPAIGN, ALL_LISTINGS, UNKNOWN)

# precedence for the same field arriving from multiple reports
_BASIS_RANK = {"seller": 4, "actual": 3, "reported": 2, "estimated": 1}


# ---- a merged field carries its value + where it came from ----
@dataclass
class Field:
    value: object
    basis: str          # seller | actual | reported | estimated
    source: str         # report type it came from
    alternates: list = _dc_field(default_factory=list)   # (value, basis, source) that lost precedence


@dataclass
class IngestResult:
    skus: dict                      # sku -> {field_name: Field}
    identity_map: dict              # asin -> sku
    unmapped_asins: dict            # asin -> {field_name: Field}  (advertised/reported, no SKU)
    report_types: dict              # filename -> detected type
    ad_periods: list = None         # [{internal_sku|asin, period_start, grain, spend, sales}] (Step 2)
    revenue_periods: list = None    # [{internal_sku, period_start, grain, revenue, units}] (Step 4)
    settlement_rows: list = None    # [{order_id, sku, order_date, settlement_date, units, gross, fees, payout}]
    storage_fee_rows: list = None   # [{asin, internal_sku, period, monthly_storage_fee}]
    return_rows: list = None        # [{order_id, sku, return_date, units, refund_amount}]
    def field_coverage(self):
        cov = {}
        for rec in self.skus.values():
            for k in rec:
                cov[k] = cov.get(k, 0) + 1
        return cov


def _num(series):
    """Coerce a money/number column to float. Real marketplace exports (esp. Amazon India, ₹) render
    money as '₹1,234.50' / 'Rs. 1,234' / '1 234,50' with a currency symbol, thousands separators, and
    non-breaking spaces. The old comma-only strip left the ₹ in place, so `to_numeric` returned NaN and
    a summed column (ad spend / attributed sales) silently collapsed to 0 — the ACoS-undefined bug.
    We strip currency symbols/words, grouping separators and whitespace, and normalise
    parenthesised negatives, before coercing."""
    s = (series.astype(str)
         .str.replace(r"^\s*\((.*?)\)\s*$", r"-\1", regex=True)  # (123) -> -123 (accounting negatives)
         .str.replace(r"[₹$£€¥]", "", regex=True)                # currency symbols incl. ₹
         .str.replace(r"(?i)(rs\.?|inr|usd)", "", regex=True)   # currency words (+ trailing dot)
         .str.replace(r"[\s,]", "", regex=True))            # whitespace (incl. nbsp) + grouping commas
    return pd.to_numeric(s, errors="coerce")


def _ad_sales_col(cols):
    """The attributed-sales column of an SP Advertised-Product report, from already-normalised
    headers. Tolerates the reporting-window prefix ('7 Day' / '14 Day') and a trailing currency tag,
    and never mistakes the ACoS column ('total advertising cost of sales') for attributed sales."""
    return next((c for c in cols if "total sales" in c and "cost of sales" not in c), None)


def _read_headered(name, raw_or_df):
    """Return a DataFrame. Handles the Unified Transaction preamble (real header after N lines)."""
    if isinstance(raw_or_df, pd.DataFrame):
        return raw_or_df
    return raw_or_df  # caller passes DataFrames; loader below handles files


from realify.ingest.periods import (_ad_periods, dedupe_ad_periods, _revenue_periods,  # noqa: E402
                                     _settlement_rows, _storage_fee_rows, _return_rows,
                                     detect_channels, detect_overlaps)  # (split for line cap)


def load_table(filename, data):
    """Bytes from an uploaded file -> DataFrame. Handles csv/tsv/xlsx and the Unified Transaction
    preamble (the real header sits several lines down)."""
    import io
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(data))
    sep = "\t" if name.endswith(".tsv") else ","
    text = data.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()[:25]
    skip = next((i for i, l in enumerate(lines) if "settlement id" in l.lower()), 0)
    return pd.read_csv(io.StringIO(text), sep=sep, skiprows=skip)


# ---- per-type extractors: each yields (kind, key, field_name, value, basis) ----
def _extract(rtype, df, n_months=1, resolver=None):
    df = df.rename(columns={c: _norm(c) for c in df.columns})
    out = []
    from realify.ingest.marketplace_registry import (
        AMAZON_DIRECT, OFF_AMAZON_MCF, EXCLUDE, UNKNOWN, default_treatment)
    resolve = resolver or (lambda mp: default_treatment(mp)[0])

    def add(kind, key, fname, val, basis):
        if key and str(key).lower() not in ("nan", "") and val is not None and not (isinstance(val, float) and pd.isna(val)):
            out.append((kind, str(key).strip(), fname, val, basis))

    if rtype == COGS:
        skucol = next(c for c in df.columns if "sku" in c)
        costcol = next(c for c in df.columns if "price" in c or "cost" in c)
        cost = _num(df[costcol])
        for s, v in zip(df[skucol], cost):
            add("sku", s, "cogs", None if pd.isna(v) else round(float(v), 2), "seller")

    elif rtype == FEE_PREVIEW:
        for _, r in df.iterrows():
            sku = r.get("sku")
            add("sku", sku, "asin", r.get("asin"), "reported")
            add("sku", sku, "title", str(r.get("product-name") or "")[:120], "reported")
            add("sku", sku, "category", r.get("product-group"), "reported")
            add("sku", sku, "price", _num(pd.Series([r.get("your-price")]))[0], "reported")
            add("sku", sku, "referral_fee", _num(pd.Series([r.get("estimated-referral-fee-per-unit")]))[0], "estimated")
            # estimated FBA-side per-unit = total estimated fee minus referral
            tot = _num(pd.Series([r.get("estimated-fee-total")]))[0]
            ref = _num(pd.Series([r.get("estimated-referral-fee-per-unit")]))[0]
            if pd.notna(tot):
                add("sku", sku, "fba_fee", round(float(tot) - (0 if pd.isna(ref) else float(ref)), 2), "estimated")

    elif rtype == UNIFIED_TRANSACTION:
        money = ["selling fees", "fba fees", "other transaction fees"]
        for c in ["product sales", "quantity"] + money:
            if c in df.columns:
                df[c] = _num(df[c])
        # Resolve each row's marketplace to a treatment, then scope EVERY metric (orders, refunds,
        # returns, fees) to that treatment — the "both sides of every ratio" rule. UNKNOWN legs are
        # held provisional, never silently counted as Amazon.
        mp = df["marketplace"] if "marketplace" in df.columns else pd.Series("", index=df.index)
        df["_t"] = mp.map(resolve)
        o = df[df.get("type") == "Order"]
        rf = df[df.get("type") == "Refund"]
        amz_paid = o[(o["_t"] == AMAZON_DIRECT) & (o["product sales"] > 0)]
        amz_free = o[(o["_t"] == AMAZON_DIRECT) & (o["product sales"] == 0)]
        mcf = o[o["_t"] == OFF_AMAZON_MCF]
        prov = o[o["_t"] == UNKNOWN]
        amz_refunds = rf[rf["_t"] == AMAZON_DIRECT]        # only Amazon refunds hit Amazon returns
        for sku, g in amz_paid.groupby("sku"):
            units = g["quantity"].sum()
            if units <= 0:
                continue
            refunded = amz_refunds.loc[amz_refunds["sku"] == sku, "quantity"].sum() if len(amz_refunds) else 0
            asp = g["product sales"].sum() / units
            ref_pu = -(g["selling fees"].sum() + g.get("other transaction fees", pd.Series(0)).sum()) / units
            fba_pu = -g["fba fees"].sum() / units
            add("sku", sku, "price", round(float(asp), 2), "actual")
            add("sku", sku, "referral_fee", round(float(ref_pu), 2), "actual")
            add("sku", sku, "fba_fee", round(float(fba_pu), 2), "actual")
            add("sku", sku, "units_month", int(round(units / max(1, n_months))), "actual")
            if units:
                add("sku", sku, "returns_rate", round(float(refunded) / float(units), 4), "actual")
        for sku, g in mcf.groupby("sku"):
            add("sku", sku, "mcf_units", float(g["quantity"].sum()), "actual")       # Shopify/MCF
        for sku, g in amz_free.groupby("sku"):
            add("sku", sku, "replacement_units", float(g["quantity"].sum()), "actual")  # true free/promo
        for sku, g in prov.groupby("sku"):
            add("sku", sku, "provisional_units", float(g["quantity"].sum()), "actual")   # unresolved leg

    elif rtype == BUSINESS_REPORT:
        asin_c = next((c for c in df.columns if "(child) asin" in c), None)
        for _, r in df.iterrows():
            asin = r.get(asin_c)
            fo = str(r.get("featured offer percentage") or "").replace("%", "").strip()
            if fo:
                try:
                    add("asin", asin, "buybox_pct", int(round(float(fo))), "reported")
                except ValueError:
                    pass
            add("asin", asin, "title", str(r.get("title") or "")[:120], "reported")

    elif rtype == STORAGE_FEE:
        # a report may carry several monthly rows per ASIN; keep the latest month, then the merge
        # sums across the ASINs that share a SKU (total current monthly storage / on-hand snapshot).
        if "month-of-charge" in df.columns:
            df = df.sort_values("month-of-charge").groupby("asin", as_index=False).last()
        for _, r in df.iterrows():
            add("asin", r.get("asin"), "storage_fee_month",
                _num(pd.Series([r.get("estimated-monthly-storage-fee")]))[0], "reported")
            add("asin", r.get("asin"), "stock_on_hand",
                _num(pd.Series([r.get("average-quantity-on-hand")]))[0], "reported")

    elif rtype == FBA_RETURNS:
        cnt = {}
        for _, r in df.iterrows():
            s = str(r.get("sku") or "").strip()
            if s:
                cnt[s] = cnt.get(s, 0) + (float(_num(pd.Series([r.get("quantity")]))[0] or 1))
        for s, n in cnt.items():
            add("sku", s, "returned_units", n, "actual")

    elif rtype == AD_REPORT:
        # coerce money cols through _num FIRST (real reports render ₹/comma strings; summing those raw
        # would concatenate/NaN) — same fix as the period path. Sales column is variant-tolerant.
        sales_c = _ad_sales_col(df.columns)
        df = df.assign(_spend=_num(df["spend"]) if "spend" in df.columns else 0.0,
                       _sales=_num(df[sales_c]) if sales_c else 0.0)
        g = df.groupby("advertised asin").agg(spend=("_spend", "sum"), sales=("_sales", "sum"))
        for asin, r in g.iterrows():
            add("asin", asin, "ad_spend", round(float(r["spend"]), 2), "actual")
            add("asin", asin, "ad_sales", round(float(r["sales"]), 2), "actual")

    elif rtype == ALL_LISTINGS:
        for _, r in df.iterrows():
            add("sku", r.get("seller-sku"), "asin", r.get("asin1"), "reported")

    return out


def _build_identity(all_records):
    """asin <-> sku from any record that carries both a sku key and an 'asin' field, or an
    all-listings/fee-preview mapping."""
    a2s = {}
    for kind, key, fname, val, basis in all_records:
        if kind == "sku" and fname == "asin" and val:
            a2s.setdefault(str(val).strip(), key)
    return a2s


# field aggregation policy when combining same-basis values (e.g. many ASINs -> one SKU)
_AGG = {"ad_spend": "sum", "ad_sales": "sum", "storage_fee_month": "sum", "stock_on_hand": "sum",
        "returned_units": "sum", "units_month": "sum", "replacement_units": "sum", "mcf_units": "sum", "provisional_units": "sum", "buybox_pct": "mean"}
_IDENTITY = {"asin", "title", "category"}


def _reduce(fname, vals):
    """vals: list of (value, basis). Winning basis is chosen by rank (actual>reported>estimated);
    within the winning basis, values combine by policy (sum for additive, mean for rates, else
    first). Losing-basis values are kept as alternates for provenance."""
    from collections import defaultdict
    by_basis = defaultdict(list)
    for v, b in vals:
        if v is not None and not (isinstance(v, float) and pd.isna(v)):
            by_basis[b].append(v)
    if not by_basis:
        return Field(None, "none", "none")
    win = max(by_basis, key=lambda b: _BASIS_RANK.get(b, 0))
    wv = by_basis[win]
    policy = _AGG.get(fname, "first")
    if fname in _IDENTITY or policy == "first":
        value = wv[0]
    elif policy == "sum":
        value = round(sum(float(x) for x in wv), 4)
    elif policy == "mean":
        value = round(sum(float(x) for x in wv) / len(wv), 4)
    else:
        value = wv[0]
    alts = [(v, b) for b in by_basis for v in by_basis[b] if b != win][:5]
    return Field(value, win, win, alternates=alts)


def ingest_tables(tables, resolver=None, resolutions=None):
    """tables: list of (filename, DataFrame). Groups same-type files, extracts once per type
    (so multi-month reports aggregate instead of colliding), resolves ASIN->SKU, reduces.
    `resolver` maps a marketplace string -> channel treatment (defaults to the registry).
    `resolutions` is an optional {conflict_id: choice} map from inline conflict resolution; when
    given, ad-report periods are combined per the user's choice, else take-latest (today's default)."""
    from collections import defaultdict
    report_types, by_type, ad_named = {}, defaultdict(list), []
    for name, df in tables:
        rt = detect_report_type(df.columns)
        report_types[name] = rt
        if rt != UNKNOWN:
            by_type[rt].append(df)
            if rt == AD_REPORT:
                ad_named.append((name, df))

    all_records = []
    for rt, frames in by_type.items():
        big = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
        if rt == UNIFIED_TRANSACTION:
            all_records.extend(_extract(rt, big, n_months=len(frames), resolver=resolver))
        else:
            all_records.extend(_extract(rt, big))

    a2s = _build_identity(all_records)

    raw_sku, raw_unmapped = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    for kind, key, fname, val, basis in all_records:
        if kind == "sku":
            raw_sku[key][fname].append((val, basis))
        else:
            sku = a2s.get(key)
            (raw_sku[sku] if sku else raw_unmapped[key])[fname].append((val, basis))

    skus = {k: {f: _reduce(f, vals) for f, vals in fields.items()} for k, fields in raw_sku.items()}
    unmapped = {k: {f: _reduce(f, vals) for f, vals in fields.items()} for k, fields in raw_unmapped.items()}

    # period-aware ad dimension (Step 2): resolve advertised ASIN -> SKU where known. Files are
    # deduped per (asin, period_start) — NOT concat-then-summed — so two overlapping monthly ad
    # reports don't double-count that month's spend/sales (June-overlap fix).
    ad_periods = []
    if AD_REPORT in by_type:
        from realify.ingest import conflicts
        recs = (conflicts.resolve_ad_frames(ad_named, resolutions) if resolutions
                else dedupe_ad_periods(by_type[AD_REPORT]))
        for rec in recs:
            rec["internal_sku"] = a2s.get(rec["asin"])
            ad_periods.append(rec)

    # per-period settled revenue (Step 4): TACoS denominator, channel-scoped
    revenue_periods, settlement_rows, return_rows = [], [], []
    if UNIFIED_TRANSACTION in by_type:
        big_tx = pd.concat(by_type[UNIFIED_TRANSACTION], ignore_index=True) if len(by_type[UNIFIED_TRANSACTION]) > 1 else by_type[UNIFIED_TRANSACTION][0]
        revenue_periods = _revenue_periods(big_tx, resolver=resolver)
        settlement_rows = _settlement_rows(big_tx, resolver=resolver)
        return_rows = _return_rows(big_tx, resolver=resolver)

    # per-period storage fee rows — the row-level detail the scalar storage_fee_month field
    # (latest-month-only, above) collapses away; feeds the real storage_fees table.
    storage_fee_rows = []
    if STORAGE_FEE in by_type:
        big_sf = pd.concat(by_type[STORAGE_FEE], ignore_index=True) if len(by_type[STORAGE_FEE]) > 1 else by_type[STORAGE_FEE][0]
        for rec in _storage_fee_rows(big_sf):
            rec["internal_sku"] = a2s.get(rec["asin"]) or rec["asin"]
            storage_fee_rows.append(rec)

    return IngestResult(skus=skus, identity_map=a2s, unmapped_asins=unmapped,
                        storage_fee_rows=storage_fee_rows, return_rows=return_rows,
                        report_types=report_types, ad_periods=ad_periods,
                        revenue_periods=revenue_periods, settlement_rows=settlement_rows)


# ---- bridge to provisioning: per-SKU dicts for seller_skus (values only, None where absent) ----
_SELLER_SKU_FIELDS = ["asin", "title", "category", "price", "cogs", "referral_fee", "fba_fee",
                      "units_month", "returns_rate", "buybox_pct"]


def to_seller_sku_rows(result: IngestResult):
    rows = []
    for sku, rec in result.skus.items():
        row = {"internal_sku": sku, "channel": "amazon"}
        for f in _SELLER_SKU_FIELDS:
            row[f] = rec[f].value if f in rec else None      # absent stays None — never fabricated
        # tacos = spend/attributed-sales is a clean ratio (window-agnostic). ad_cost_unit needs an
        # aligned ad/units window, so it's left to the detector (Step 3) rather than guessed here.
        if "ad_spend" in rec and "ad_sales" in rec and rec["ad_sales"].value:
            row["tacos"] = round(rec["ad_spend"].value / rec["ad_sales"].value, 4)
        rows.append(row)
    return rows
