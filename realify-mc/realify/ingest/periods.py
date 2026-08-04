"""Period-aware + channel-detection extractors, split out of report_ingest.py to keep both files
under the line cap. Behaviour is unchanged; report_ingest re-exports these names so existing callers
(report_ingest.detect_channels, ._ad_periods, ._revenue_periods) keep working.

Low-level helpers (_norm, _num, report-type constants) are imported lazily from report_ingest to
avoid an import cycle.
"""
import pandas as pd


def _ad_periods(df, grain="month"):
    """Period-aware ad dimension (Step 2 seam for the CMAA tab / TACoS-over-time).
    Collapse the daily SP Advertised-Product report to (asin, period_start, grain, spend, sales).
    Spend (reported/certain) and sales (attributed/estimated) are kept as separate columns and never
    blended, so downstream detectors keep the certain-vs-estimated distinction."""
    from .report_ingest import _norm, _num, _ad_sales_col
    d = df.rename(columns={c: _norm(c) for c in df.columns})
    sales_c = _ad_sales_col(d.columns)
    if "advertised asin" not in d.columns or sales_c is None:
        return []
    d["spend"] = _num(d["spend"]) if "spend" in d.columns else 0.0
    d[sales_c] = _num(d[sales_c])
    if "date" in d.columns:
        dt_ = pd.to_datetime(d["date"], errors="coerce")
        d["_period"] = dt_.dt.strftime("%Y-%m-01") if grain == "month" else dt_.dt.strftime("%Y-%m-%d")
    else:
        d["_period"] = "unknown"
    g = d.groupby(["advertised asin", "_period"], as_index=False).agg(
        spend=("spend", "sum"), sales=(sales_c, "sum"))
    return [{"asin": str(r["advertised asin"]).strip(), "period_start": r["_period"], "grain": grain,
             "spend": round(float(r["spend"]), 2), "sales": round(float(r["sales"]), 2)}
            for _, r in g.iterrows() if str(r["advertised asin"]).strip().lower() not in ("nan", "")]


def dedupe_ad_periods(frames, grain="month"):
    """Combine several SP Advertised-Product report files into one (asin, period_start) series WITHOUT
    double-counting a period that two files both cover. Each file is collapsed to the period grain on
    its own (so multiple campaign/day rows *within* a file still sum correctly); across files, a period
    present in more than one file is TAKEN FROM THE LAST file in upload order rather than summed — the
    'take latest' rule. This is what stops two overlapping 2026-06 reports from doubling June spend.
    (Two files that split one month into non-overlapping halves are the rare case the rule trades away;
    detect_overlaps still surfaces the overlap to the seller.)"""
    merged = {}
    for df in frames:
        for rec in _ad_periods(df, grain=grain):
            merged[(rec["asin"], rec["period_start"])] = rec   # last file wins for a shared period
    return list(merged.values())


def _revenue_periods(df, resolver=None, grain="month"):
    """Per-SKU per-period Amazon-direct settled revenue & units (Step 4, TACoS denominator).
    Channel-scoped via the resolver so it matches every other metric. Derives the period from the
    transaction date; rows with an unparseable date are dropped, never bucketed to a guess."""
    from .report_ingest import _norm, _num
    from .marketplace_registry import AMAZON_DIRECT, default_treatment
    resolve = resolver or (lambda mp: default_treatment(mp)[0])
    d = df.rename(columns={c: _norm(c) for c in df.columns})
    if "product sales" not in d.columns or "sku" not in d.columns:
        return []
    date_c = next((c for c in d.columns if c in ("date/time", "date", "posted-date")), None)
    if not date_c:
        return []
    d["product sales"] = _num(d["product sales"])
    d["quantity"] = _num(d["quantity"]) if "quantity" in d.columns else 1
    mp = d["marketplace"] if "marketplace" in d.columns else pd.Series("", index=d.index)
    d["_t"] = mp.map(resolve)
    d["_dt"] = pd.to_datetime(d[date_c], errors="coerce", utc=True)
    d["_period"] = d["_dt"].dt.strftime("%Y-%m-01")
    o = d[(d.get("type") == "Order") & (d["_t"] == AMAZON_DIRECT) & (d["product sales"] > 0)]
    o = o[o["_period"].notna()]
    g = o.groupby(["sku", "_period"], as_index=False).agg(
        revenue=("product sales", "sum"), units=("quantity", "sum"))
    return [{"internal_sku": str(r["sku"]).strip(), "period_start": r["_period"], "grain": grain,
             "revenue": round(float(r["revenue"]), 2), "units": int(r["units"])}
            for _, r in g.iterrows() if str(r["sku"]).strip().lower() not in ("nan", "")]


def _settlement_rows(df, resolver=None):
    """Per-order settlement rows (Amazon-direct, paid orders only) for seller_orders/settlements —
    the row-level detail _revenue_periods() collapses away into monthly sums. Channel-scoped via the
    resolver so it matches every other UNIFIED_TRANSACTION metric. Rows with no order id/sku or an
    unparseable date are dropped, never guessed."""
    from .report_ingest import _norm, _num
    from .marketplace_registry import AMAZON_DIRECT, default_treatment
    resolve = resolver or (lambda mp: default_treatment(mp)[0])
    d = df.rename(columns={c: _norm(c) for c in df.columns})
    required = ("product sales", "sku", "order id")
    if any(c not in d.columns for c in required):
        return []
    date_c = next((c for c in d.columns if c in ("date/time", "date", "posted-date")), None)
    if not date_c:
        return []
    money = ["product sales", "selling fees", "fba fees", "other transaction fees", "total"]
    for c in money:
        if c in d.columns:
            d[c] = _num(d[c])
    d["quantity"] = _num(d["quantity"]) if "quantity" in d.columns else 1
    mp = d["marketplace"] if "marketplace" in d.columns else pd.Series("", index=d.index)
    d["_t"] = mp.map(resolve)
    d["_dt"] = pd.to_datetime(d[date_c], errors="coerce", utc=True)
    rel_c = next((c for c in d.columns if c == "transaction release date"), None)
    d["_rel"] = pd.to_datetime(d[rel_c], errors="coerce", utc=True) if rel_c else pd.NaT
    o = d[(d.get("type") == "Order") & (d["_t"] == AMAZON_DIRECT) & (d["product sales"] > 0)]
    o = o[o["_dt"].notna()]
    rows = []
    for _, r in o.iterrows():
        order_id = str(r.get("order id") or "").strip()
        sku = str(r.get("sku") or "").strip()
        if not order_id or not sku or sku.lower() == "nan":
            continue
        # selling fees / fba fees arrive as negative deductions in the source; store as positive
        # magnitudes to match seller_orders.referral_fee/fba_fee's existing sign convention
        # (subtracted in api.kpis()'s margin calc: margin = rev - referral - fba - cogs - ads).
        referral_fee = round(-float(r.get("selling fees") or 0), 2)
        fba_fee = round(-float(r.get("fba fees") or 0), 2)
        fees = referral_fee + fba_fee - float(r.get("other transaction fees") or 0)
        settle = r["_rel"] if pd.notna(r["_rel"]) else r["_dt"]
        rows.append({
            "order_id": order_id, "sku": sku,
            "order_date": r["_dt"].strftime("%Y-%m-%d"),
            "settlement_date": settle.strftime("%Y-%m-%d"),
            "units": int(r["quantity"]) if pd.notna(r["quantity"]) and r["quantity"] > 0 else 1,
            "gross": round(float(r["product sales"]), 2),
            "referral_fee": referral_fee, "fba_fee": fba_fee,
            "fees": round(fees, 2),
            "payout": round(float(r.get("total") or 0), 2),
        })
    return rows


def _return_rows(df, resolver=None):
    """Per-refund rows (Amazon-direct only) for the returns table — Unified Transaction 'Refund'
    type rows, the real dollar-refund data _settlement_rows() deliberately excludes (it keeps only
    'Order' rows). The FBA Customer Returns report has no dollar refund_amount column at all (only
    a unit count), so this is the only real source for it. `reason` isn't in this report either —
    stays None, never guessed."""
    from .report_ingest import _norm, _num
    from .marketplace_registry import AMAZON_DIRECT, default_treatment
    resolve = resolver or (lambda mp: default_treatment(mp)[0])
    d = df.rename(columns={c: _norm(c) for c in df.columns})
    required = ("product sales", "sku", "order id")
    if any(c not in d.columns for c in required):
        return []
    date_c = next((c for c in d.columns if c in ("date/time", "date", "posted-date")), None)
    if not date_c:
        return []
    d["product sales"] = _num(d["product sales"])
    d["quantity"] = _num(d["quantity"]) if "quantity" in d.columns else 1
    mp = d["marketplace"] if "marketplace" in d.columns else pd.Series("", index=d.index)
    d["_t"] = mp.map(resolve)
    d["_dt"] = pd.to_datetime(d[date_c], errors="coerce", utc=True)
    rf = d[(d.get("type") == "Refund") & (d["_t"] == AMAZON_DIRECT) & (d["product sales"] < 0)]
    rf = rf[rf["_dt"].notna()]
    rows = []
    for _, r in rf.iterrows():
        order_id = str(r.get("order id") or "").strip()
        sku = str(r.get("sku") or "").strip()
        if not order_id or not sku or sku.lower() == "nan":
            continue
        rows.append({
            "order_id": order_id, "sku": sku,
            "return_date": r["_dt"].strftime("%Y-%m-%d"),
            "units": int(r["quantity"]) if pd.notna(r["quantity"]) and r["quantity"] > 0 else 1,
            "refund_amount": round(-float(r["product sales"]), 2),
        })
    return rows


def _storage_fee_rows(df):
    """Per-(asin, period) storage-fee rows for the storage_fees table — the row-level detail the
    scalar storage_fee_month field (in report_ingest._extract, latest-month-only for the seller_skus
    aggregate) collapses away. Only monthly_storage_fee + period are populated: the report's
    item-volume column is present in mixed units (cubic feet on some files, cubic meter on others,
    per its own volume-units column) with nothing downstream reading it, so rather than guess a
    conversion it's left out entirely — aged_surcharge/age_days aren't in this report type at all
    and stay None too, never fabricated."""
    from .report_ingest import _norm, _num
    d = df.rename(columns={c: _norm(c) for c in df.columns})
    if "asin" not in d.columns or "estimated-monthly-storage-fee" not in d.columns:
        return []
    d["estimated-monthly-storage-fee"] = _num(d["estimated-monthly-storage-fee"])
    period_c = "month-of-charge" if "month-of-charge" in d.columns else None
    rows = []
    for _, r in d.iterrows():
        asin = str(r.get("asin") or "").strip()
        fee = r.get("estimated-monthly-storage-fee")
        if not asin or asin.lower() == "nan" or pd.isna(fee):
            continue
        period = str(r.get(period_c) or "").strip() if period_c else ""
        rows.append({"asin": asin, "period": period or None, "monthly_storage_fee": round(float(fee), 2)})
    return rows


def detect_channels(tables, resolver=None):
    """Scan transaction marketplaces and classify each via the resolver. Returns a list of
    {marketplace, treatment, label, units} — the raw material for pending confirmations.
    An UNKNOWN treatment is what the registry UI raises for the seller to confirm."""
    from .report_ingest import _norm, _num, detect_report_type, UNIFIED_TRANSACTION
    from .marketplace_registry import default_treatment
    resolve = resolver or (lambda mp: default_treatment(mp)[0])
    seen = {}
    for _name, df in tables:
        if detect_report_type(df.columns) != UNIFIED_TRANSACTION:
            continue
        d = df.rename(columns={c: _norm(c) for c in df.columns})
        if "marketplace" not in d.columns:
            continue
        d["quantity"] = _num(d["quantity"]) if "quantity" in d.columns else 1
        for mp, g in d.groupby(d["marketplace"].astype(str)):
            t = resolve(mp)
            _, label = default_treatment(mp)
            acc = seen.setdefault(mp, {"marketplace": mp, "treatment": t, "label": label, "units": 0.0})
            acc["units"] += float(g["quantity"].sum())
    return list(seen.values())


def _file_periods(df, min_share=0.10):
    """Set of 'YYYY-MM' months a report file *substantially* covers (>= min_share of its dated rows).
    The share floor ignores settlement boundary spillover — a monthly report legitimately carries a
    few rows dated in the adjacent month, and that must not read as an overlap with the neighbour."""
    from .report_ingest import _norm
    d = df.rename(columns={c: _norm(c) for c in df.columns})
    date_c = next((c for c in d.columns if c in ("date/time", "date", "return-date", "posted-date")), None)
    if not date_c:
        return set()
    months = pd.to_datetime(d[date_c], errors="coerce", utc=True).dt.strftime("%Y-%m").dropna()
    if len(months) == 0:
        return set()
    share = months.value_counts(normalize=True)
    return set(share[share >= min_share].index)


def detect_overlaps(tables):
    """Find same-type report files that cover overlapping months. Only for ADDITIVE report types
    (transactions, ad reports, returns) — the ones the engine sums, where an overlap double-counts.
    Storage fees are last-wins (not summed) and identity reports are dedup-safe, so they're skipped.
    Returns findings the upload path raises as confirmations instead of silently summing."""
    from collections import defaultdict
    from .report_ingest import detect_report_type, UNIFIED_TRANSACTION, AD_REPORT, FBA_RETURNS
    additive = {UNIFIED_TRANSACTION, AD_REPORT, FBA_RETURNS}
    by_type = defaultdict(list)
    for name, df in tables:
        rt = detect_report_type(df.columns)
        if rt in additive:
            by_type[rt].append((name, _file_periods(df)))
    findings = []
    for rt, files in by_type.items():
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                shared = files[i][1] & files[j][1]
                if shared:
                    findings.append({"kind": "report_overlap", "report_type": rt,
                                     "files": [files[i][0], files[j][0]],
                                     "shared_periods": sorted(shared)})
    return findings
