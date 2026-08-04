"""Structured upload conflicts + resolver (Phase 1).

Turns overlap/duplicate DETECTION into structured conflict OBJECTS the upload UIs can resolve inline,
and applies the user's choice back onto the ad-report ingest. Phase 1 covers the two cases where the
old advisory copy was misleading or unactionable:
  * period_overlap — two AD reports cover the same month (default is take-latest, NOT "add them up")
  * duplicate_file — a re-uploaded file is byte-identical to one already ingested (skipped)

Everything is computed ON DEMAND from the in-memory frames — no new table. The DEFAULT resolution
(keep_latest) reproduces today's dedupe_ad_periods EXACTLY, so skipping resolution changes nothing;
resolving is pure upside. Conflict ids are deterministic (hash of type+period+sorted filenames) so a
choice made at the preview step matches the same conflict at commit. The schema (type/options/
confidence/impact) is intentionally roomy for Phase 2 (partial-overlap skip_period per month,
cross-report metric disagreement).
"""
import hashlib
import json

from .periods import _ad_periods, _file_periods

KEEP_LATEST, KEEP_FILE, SUM, SKIP_PERIOD = "keep_latest", "keep_file", "sum", "skip_period"


def _cid(prefix, *parts):
    raw = "|".join(str(p) for p in parts)
    return prefix + "_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def period_conflict_id(period, filenames):
    """Deterministic id for an ad-report period overlap — stable across preview and commit (same
    files) so a resolution chosen at preview resolves the same conflict at commit."""
    return _cid("cf", "period_overlap", "ad_report", period, *sorted(filenames))


def parse_resolutions(raw):
    """Parse the optional `resolutions` form field — a JSON object {conflict_id: choice} — into a
    dict. Tolerant: missing/malformed input yields {} (i.e. today's default behavior, no block)."""
    if not raw:
        return {}
    try:
        d = json.loads(raw) if isinstance(raw, str) else raw
        return {str(k): str(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except Exception:
        return {}


# ---- ad-frame combination (the resolver applied at ingest) -----------------
def _grouped(df):
    """{period_start: {asin: ad_period_rec}} for one AD frame (per-asin-per-month spend/sales)."""
    g = {}
    for r in _ad_periods(df):
        g.setdefault(r["period_start"], {})[r["asin"]] = r
    return g


def _combine_period(covering, choice):
    """Combine one month across the files covering it (in upload order; last = most recent).
    covering: list of (filename, {asin: rec}). choice: keep_latest | sum | keep_file:<name> |
    skip_period:<name>. Returns a list of combined recs for the period."""
    kind, _, arg = choice.partition(":")
    if kind == KEEP_FILE and arg:
        covering = [(n, g) for n, g in covering if n == arg] or covering
        kind = KEEP_LATEST
    elif kind == SKIP_PERIOD and arg:
        covering = [(n, g) for n, g in covering if n != arg] or covering
        kind = KEEP_LATEST
    merged = {}
    for _n, g in covering:                       # upload order; later files overwrite (take-latest)
        for asin, rec in g.items():
            if kind == SUM and asin in merged:
                merged[asin] = {**rec,
                                "spend": round(merged[asin]["spend"] + rec["spend"], 2),
                                "sales": round(merged[asin]["sales"] + rec["sales"], 2)}
            else:
                merged[asin] = dict(rec)
    return list(merged.values())


def resolve_ad_frames(named_frames, resolutions=None):
    """Combine AD frames into ad_period records honoring {conflict_id: choice}. With no (or unknown)
    choice per month the default is keep_latest, which equals dedupe_ad_periods — so an empty map
    reproduces today's numbers exactly. `named_frames`: list of (filename, DataFrame), upload order."""
    resolutions = resolutions or {}
    per_file = [(name, _grouped(df)) for name, df in named_frames]
    periods = sorted({p for _n, g in per_file for p in g})
    out = []
    for pstart in periods:
        covering = [(name, g[pstart]) for name, g in per_file if pstart in g]   # upload order
        choice = KEEP_LATEST
        if len(covering) > 1:
            cid = period_conflict_id(pstart[:7], [n for n, _ in covering])
            choice = resolutions.get(cid, KEEP_LATEST)
        out.extend(_combine_period(covering, choice))
    return out


# ---- detection: structured conflict objects for the UI ---------------------
def _sum_metrics(recs):
    return {"ad_spend": round(sum(r["spend"] for r in recs), 2),
            "ad_sales": round(sum(r["sales"] for r in recs), 2)}


def _month_metrics(df):
    """{'YYYY-MM': {'ad_spend','ad_sales'}} for one AD frame (summed across asins)."""
    out = {}
    for r in _ad_periods(df):
        m = out.setdefault(r["period_start"][:7], {"ad_spend": 0.0, "ad_sales": 0.0})
        m["ad_spend"] += r["spend"]; m["ad_sales"] += r["sales"]
    return {p: {k: round(v, 2) for k, v in m.items()} for p, m in out.items()}


def _rng(months):
    ms = sorted(months)
    return ms[0] if len(ms) <= 1 else f"{ms[0]}..{ms[-1]}"


def _period_overlap(month, files, named, metrics, total_spend):
    pstart = month + "-01"
    sides = [{"file": n, "uploaded_at": None, "period_covered": _rng(_file_periods(named[n])),
              "metrics": metrics[n].get(month, {"ad_spend": 0.0, "ad_sales": 0.0})} for n in files]
    covering = [(n, _grouped(named[n]).get(pstart, {})) for n in files]         # upload order
    keep = _sum_metrics(_combine_period(covering, KEEP_LATEST))
    summ = _sum_metrics(_combine_period(covering, SUM))
    spends = [s["metrics"].get("ad_spend", 0.0) for s in sides]
    sales = [s["metrics"].get("ad_sales", 0.0) for s in sides]
    identical = (max(spends) - min(spends) < 0.01) and (max(sales) - min(sales) < 0.01)
    delta = round(summ["ad_spend"] - keep["ad_spend"], 2)
    return {
        "id": period_conflict_id(month, files),
        "type": "period_overlap", "report_type": "ad_report", "period": month,
        "sides": sides,
        "options": [KEEP_LATEST, KEEP_FILE, SUM, SKIP_PERIOD],
        "recommended": KEEP_LATEST,
        "impact": {"keep_latest": keep, "sum": summ,
                   "delta_vs_recommended": {
                       "ad_spend": delta,
                       "pct_of_total": (round(100 * delta / total_spend, 1) if total_spend else None)}},
        "confidence": "high" if identical else "medium",
        "auto_reason": ("Both files report the same ad spend for this month — keep either."
                        if identical else
                        "The files report different ad spend for this month — the most recent is kept."),
    }


def _duplicate(name, prior, when):
    reason = ("This file is identical to one you uploaded on " + when[:10] + " — it was skipped."
              if when else "This file is identical to another file in this upload — it was skipped.")
    return {
        "id": _cid("cfdup", name, prior or "", when or ""),
        "type": "duplicate_file", "report_type": None, "period": None,
        "sides": [{"file": name, "uploaded_at": None, "period_covered": None, "metrics": {}},
                  {"file": prior or name, "uploaded_at": when, "period_covered": None, "metrics": {}}],
        "options": [KEEP_LATEST], "recommended": KEEP_LATEST, "impact": {},
        "confidence": "high", "auto_reason": reason,
    }


def detect_conflicts(tables, duplicates=None):
    """Structured conflicts for the upload UI: ad-report period overlaps (rich ₹ impact) + duplicate
    files. `tables`: list of (filename, DataFrame) (the fresh, non-duplicate frames). `duplicates`:
    the partition() duplicates list [(name, prior_filename, prior_ingested_at)], or None."""
    from .report_ingest import detect_report_type, AD_REPORT
    ad = [(n, df) for n, df in tables if df is not None and detect_report_type(df.columns) == AD_REPORT]
    named = {n: df for n, df in ad}
    metrics = {n: _month_metrics(df) for n, df in ad}
    # by_month uses the AD-ROW months (the same covering set resolve_ad_frames keys the conflict id on,
    # so a chosen resolution always matches at ingest). `subst` counts files that SUBSTANTIALLY cover a
    # month (>=10% share, same primitive as detect_overlaps) — we only raise a conflict when >=2 do, so
    # boundary-row spillover isn't flagged.
    by_month, subst = {}, {}
    for n, df in ad:
        for m in metrics[n]:
            by_month.setdefault(m, []).append(n)
        for m in _file_periods(df):
            subst[m] = subst.get(m, 0) + 1
    total_spend = round(sum(r["spend"] for r in resolve_ad_frames(ad)), 2) if ad else 0.0
    out = [_period_overlap(m, by_month[m], named, metrics, total_spend)
           for m in sorted(by_month) if len(by_month[m]) > 1 and subst.get(m, 0) > 1]
    out += [_duplicate(name, prior, when) for name, prior, when in (duplicates or [])]
    return out


def record_overlap_confirmations(conf, tenant_id, tables):
    """Persist the 'resolve later on Channels' record for each same-type additive overlap. Keeps the
    unchanged kind='report_overlap' + ckey format the Channels tab / tests rely on, but with ACCURATE
    copy: ad reports are take-latest (most recent kept), not summed. Shared by both commit endpoints."""
    from .report_ingest import detect_overlaps, AD_REPORT
    for ov in detect_overlaps(tables):
        rt, periods = ov["report_type"], ", ".join(ov["shared_periods"])
        ckey = "overlap:" + rt + ":" + ",".join(ov["shared_periods"])
        if rt == AD_REPORT:
            detail = (f"{' and '.join(ov['files'])} both cover {periods}. We kept the most recent "
                      f"file for the overlapping month(s); nothing is double-counted. Change on Channels.")
        else:
            detail = (f"{' and '.join(ov['files'])} both cover {periods} — we combined them, which "
                      f"double-counts if it's the same data. Re-upload just one to replace.")
        conf.upsert(tenant_id, ckey, "report_overlap",
                    f"Two {rt.replace('_', ' ')} reports overlap", detail, suggested=None)
