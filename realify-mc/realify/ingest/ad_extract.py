"""Attributable-ads extraction (spec A1/A3) — reads the campaign columns the aggregate ad path discards.

Runs as an ADDITIVE second pass after the existing report ingest (so seller_skus / the ASIN->SKU identity
already exist): re-reads the recognized ad files via the rules-as-data header-alias map, builds the
campaign -> ad group -> advertised SKU/ASIN graph + SP search-term rows, resolves ASIN->canonical SKU,
and records the coverage summary (coverage_pct, unmapped_spend, fidelity, granularity flag). It never
fabricates attribution: an advertised ASIN with no resolved SKU is kept as UNMAPPED spend, not invented.

Idempotent: within a file, rows collapse to the period grain; across files a shared (entity, period) is
'take latest' (same rule as dedupe_ad_periods), so overlapping re-exports converge instead of doubling.
"""
import logging

import pandas as pd

from realify.ingest import ad_headers as H
from realify.ingest.recognizer import detect_report_type, AD_REPORT, SEARCH_TERM, AD_CAMPAIGN
from realify.ingest.report_ingest import _num

_log = logging.getLogger("realify.ads.ingest")
from realify.domain import ad_fidelity
from realify.repositories.seller_repo import SellerRepository
from realify.repositories.ad_entity_repo import (
    AdEntityPerfRepository, AdSearchTermRepository, AdIngestSummaryRepository)


def _period(series, grain="month"):
    dt = pd.to_datetime(series, errors="coerce")
    fmt = "%Y-%m-01" if grain == "month" else "%Y-%m-%d"
    return dt.dt.strftime(fmt)


def _col(df, cols, field):
    c = cols.get(field)
    return df[c] if c is not None else None


def _asin_to_sku(con, tenant_id):
    """ASIN -> canonical internal_sku, from the seller_skus populated by the main ingest. Also lets an
    'Advertised SKU' that IS a known internal_sku resolve directly."""
    rows = SellerRepository(con).all(tenant_id)
    by_asin, skus = {}, set()
    for r in rows:
        sku = r.get("internal_sku")
        if sku:
            skus.add(str(sku))
        if r.get("asin") and sku:
            by_asin[str(r["asin"]).strip()] = str(sku)
    return by_asin, skus


def _resolve_sku(asin, adv_sku, by_asin, known_skus):
    a = str(asin or "").strip()
    if a and a in by_asin:
        return by_asin[a]
    s = str(adv_sku or "").strip()
    if s and s in known_skus:          # an advertised SKU that is already a canonical SKU
        return s
    return None


def _graph_rows(df, by_asin, known_skus, grain):
    """Collapse an Advertised Product frame to (campaign, ad_group, advertised_asin, period) rows."""
    cols = H.resolve_all(df.columns, "ad_report")
    if "advertised_asin" not in cols and "advertised_sku" not in cols:
        return {}
    d = pd.DataFrame(index=df.index)
    d["campaign"] = _col(df, cols, "campaign") if "campaign" in cols else ""
    d["ad_group"] = _col(df, cols, "ad_group") if "ad_group" in cols else ""
    d["asin"] = _col(df, cols, "advertised_asin") if "advertised_asin" in cols else ""
    d["adv_sku"] = _col(df, cols, "advertised_sku") if "advertised_sku" in cols else None
    d["spend"] = _num(_col(df, cols, "spend")) if "spend" in cols else 0.0
    d["sales"] = _num(_col(df, cols, "sales")) if "sales" in cols else 0.0
    d["clicks"] = _num(_col(df, cols, "clicks")) if "clicks" in cols else 0.0
    d["orders"] = _num(_col(df, cols, "orders")) if "orders" in cols else 0.0
    d["_p"] = _period(_col(df, cols, "date"), grain) if "date" in cols else "unknown"
    for k in ("campaign", "ad_group", "asin"):
        d[k] = d[k].astype(str).fillna("").str.strip()
    g = d.groupby(["campaign", "ad_group", "asin", "_p"], as_index=False).agg(
        spend=("spend", "sum"), sales=("sales", "sum"), clicks=("clicks", "sum"),
        orders=("orders", "sum"), adv_sku=("adv_sku", "first"))
    out = {}
    for _, r in g.iterrows():
        key = (r["campaign"], r["ad_group"], r["asin"], r["_p"])
        out[key] = {"campaign": r["campaign"], "ad_group": r["ad_group"], "advertised_asin": r["asin"],
                    "advertised_sku": (str(r["adv_sku"]).strip() if r["adv_sku"] is not None else None),
                    "internal_sku": _resolve_sku(r["asin"], r["adv_sku"], by_asin, known_skus),
                    "period_start": r["_p"], "spend": round(float(r["spend"]), 2),
                    "sales": round(float(r["sales"]), 2), "clicks": float(r["clicks"]),
                    "orders": float(r["orders"])}
    return out


def _term_rows(df, grain):
    cols = H.resolve_all(df.columns, "search_term")
    if "customer_search_term" not in cols:
        return {}
    d = pd.DataFrame(index=df.index)
    d["campaign"] = _col(df, cols, "campaign") if "campaign" in cols else ""
    d["ad_group"] = _col(df, cols, "ad_group") if "ad_group" in cols else ""
    d["targeting"] = _col(df, cols, "targeting") if "targeting" in cols else None
    d["match_type"] = _col(df, cols, "match_type") if "match_type" in cols else None
    d["term"] = _col(df, cols, "customer_search_term")
    d["spend"] = _num(_col(df, cols, "spend")) if "spend" in cols else 0.0
    d["sales"] = _num(_col(df, cols, "sales")) if "sales" in cols else 0.0
    d["clicks"] = _num(_col(df, cols, "clicks")) if "clicks" in cols else 0.0
    d["orders"] = _num(_col(df, cols, "orders")) if "orders" in cols else 0.0
    d["_p"] = _period(_col(df, cols, "date"), grain) if "date" in cols else "unknown"
    for k in ("campaign", "ad_group", "term"):
        d[k] = d[k].astype(str).fillna("").str.strip()
    g = d.groupby(["campaign", "ad_group", "term", "_p"], as_index=False).agg(
        spend=("spend", "sum"), sales=("sales", "sum"), clicks=("clicks", "sum"),
        orders=("orders", "sum"), targeting=("targeting", "first"), match_type=("match_type", "first"))
    out = {}
    for _, r in g.iterrows():
        out[(r["campaign"], r["ad_group"], r["term"], r["_p"])] = {
            "campaign": r["campaign"], "ad_group": r["ad_group"],
            "targeting": (str(r["targeting"]).strip() if r["targeting"] is not None else None),
            "match_type": (str(r["match_type"]).strip() if r["match_type"] is not None else None),
            "customer_search_term": r["term"], "period_start": r["_p"],
            "spend": round(float(r["spend"]), 2), "sales": round(float(r["sales"]), 2),
            "clicks": float(r["clicks"]), "orders": float(r["orders"])}
    return out


def safe_ingest_ad_graph(con, tenant_id, tables):
    """Wrapper that never lets the additive ad-graph pass block the core ingest (returns None on error)."""
    try:
        return ingest_ad_graph(con, tenant_id, tables)
    except Exception:
        # never block the core ingest — but no longer swallow SILENTLY: log the full traceback so a
        # failed/partial ad-graph extraction is diagnosable (this hid gogodolls' zero-row outcome).
        _log.exception("ad-graph ingest failed tid=%s (ad recs will be SKU-level only)", tenant_id)
        return None


def ingest_ad_graph(con, tenant_id, tables, grain="month"):
    """Extract + persist the attributable ad graph, search terms, and coverage summary. Additive and
    behavior-preserving; returns a small summary dict. `tables` = [(filename, DataFrame)]."""
    by_asin, known_skus = _asin_to_sku(con, tenant_id)
    graph, terms = {}, {}
    has_ap = has_st = has_campaign_only = False
    for _name, df in tables:
        rt = detect_report_type(df.columns)
        if rt == AD_REPORT:
            has_ap = True
            g = _graph_rows(df, by_asin, known_skus, grain)             # take-latest per (entity, period)
            graph.update(g)
            _log.info("ad-graph file '%s' -> AD_REPORT: %s input rows, %s graph rows (%s distinct advertised ASINs)",
                      _name, len(df), len(g), len({r["advertised_asin"] for r in g.values()}))
        elif rt == SEARCH_TERM:
            has_st = True
            terms.update(_term_rows(df, grain))
        elif rt == AD_CAMPAIGN:
            has_campaign_only = True
            _log.info("ad-graph file '%s' -> AD_CAMPAIGN (campaign-summary only, no per-SKU breakdown)", _name)

    ep, st, su = (AdEntityPerfRepository(con), AdSearchTermRepository(con), AdIngestSummaryRepository(con))
    mapped = unmapped = 0.0
    for rec in graph.values():
        ep.upsert(tenant_id, rec["campaign"], rec["ad_group"], rec["advertised_asin"],
                  rec["advertised_sku"], rec["internal_sku"], rec["period_start"], grain,
                  rec["spend"], rec["sales"], rec["clicks"], rec["orders"])
        if rec["internal_sku"]:
            mapped += rec["spend"] or 0.0
        else:
            unmapped += rec["spend"] or 0.0
    for rec in terms.values():
        st.upsert(tenant_id, rec["campaign"], rec["ad_group"], rec["targeting"], rec["match_type"],
                  rec["customer_search_term"], rec["period_start"], grain,
                  rec["spend"], rec["sales"], rec["clicks"], rec["orders"])

    total = mapped + unmapped
    coverage_pct = (mapped / total * 100.0) if total > 0 else None
    fidelity = ad_fidelity.fidelity(has_ap, has_st, has_campaign_only)
    flag = ad_fidelity.granularity_flag(has_ap, has_campaign_only)
    su.upsert(tenant_id, coverage_pct, mapped, unmapped, fidelity, flag,
              has_advertised_product=has_ap, has_search_term=has_st, has_campaign_only=has_campaign_only)
    _log.info("ad-graph tid=%s DONE: entity_rows=%s mapped_rows=%s distinct_asins=%s distinct_campaigns=%s "
              "coverage=%s%% mapped_spend=%s unmapped_spend=%s fidelity=%s",
              tenant_id, len(graph), sum(1 for r in graph.values() if r["internal_sku"]),
              len({r["advertised_asin"] for r in graph.values()}),
              len({r["campaign"] for r in graph.values()}),
              (round(coverage_pct, 1) if coverage_pct is not None else None),
              round(mapped, 2), round(unmapped, 2), fidelity)
    return {"graph_rows": len(graph), "search_terms": len(terms), "coverage_pct": coverage_pct,
            "mapped_spend": round(mapped, 2), "unmapped_spend": round(unmapped, 2),
            "fidelity": fidelity, "granularity_flag": flag}
