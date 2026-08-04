"""Attributable-ads repositories (Part A): the campaign->SKU entity graph, SP search-term rows, and the
per-tenant ingest coverage summary. Same bounded context (attributable Amazon ad entities), same style as
AdPerformanceRepository — tenant-first methods, INSERT OR REPLACE (dbengine rewrites to Postgres upsert),
SQL lives only here. The future AdsCollector (API) writes the same rows under the same natural keys.
"""
import datetime

from .base import BaseRepository


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class AdEntityPerfRepository(BaseRepository):
    """campaign -> ad group -> advertised SKU/ASIN, with spend/sales/clicks/orders per period."""

    def upsert(self, tenant_id, campaign, ad_group, advertised_asin, advertised_sku, internal_sku,
               period_start, grain, spend, sales, clicks=None, orders=None, source="sp_report_upload"):
        self.con.execute(
            "INSERT OR REPLACE INTO ad_entity_perf"
            "(tenant_id, campaign, ad_group, advertised_asin, advertised_sku, internal_sku,"
            " period_start, grain, spend, sales, clicks, orders, source, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, campaign or "", ad_group or "", advertised_asin or "", advertised_sku,
             internal_sku, period_start, grain, spend, sales, clicks, orders, source, _now()))

    def rows_for_sku(self, tenant_id, internal_sku, grain="month"):
        return [dict(r) for r in self.con.execute(
            "SELECT campaign, ad_group, advertised_asin, period_start, spend, sales, clicks, orders "
            "FROM ad_entity_perf WHERE tenant_id=? AND internal_sku=? AND grain=?",
            (tenant_id, internal_sku, grain)).fetchall()]

    def campaign_slices_for_sku(self, tenant_id, internal_sku, grain="month"):
        """Per-(campaign, ad_group) rollup of THIS SKU's spend/sales — the SKU slice a campaign average
        would hide. Rows carry the campaign's ACOS *for this SKU*, computed by the caller."""
        rows = self.con.execute(
            "SELECT campaign, ad_group, SUM(spend) AS spend, SUM(sales) AS sales, "
            "SUM(clicks) AS clicks, SUM(orders) AS orders FROM ad_entity_perf "
            "WHERE tenant_id=? AND internal_sku=? AND grain=? GROUP BY campaign, ad_group",
            (tenant_id, internal_sku, grain)).fetchall()
        return [dict(r) for r in rows]

    def skus(self, tenant_id, grain="month"):
        """Distinct SKUs that carry attributed ad spend (mapped rows only)."""
        return [r["internal_sku"] for r in self.con.execute(
            "SELECT DISTINCT internal_sku FROM ad_entity_perf "
            "WHERE tenant_id=? AND grain=? AND internal_sku IS NOT NULL AND internal_sku<>''",
            (tenant_id, grain)).fetchall()]

    def tenant_totals(self, tenant_id, grain="month"):
        """spend/clicks/orders totals across all campaigns/periods (Workspace ads substats: CPC,
        CPA, CVR). Click/order-level data isn't universally ingested — callers should treat 0
        rows as unavailable."""
        r = self.con.execute(
            "SELECT COALESCE(SUM(spend),0) spend, COALESCE(SUM(clicks),0) clicks, "
            "COALESCE(SUM(orders),0) orders, COUNT(*) rows "
            "FROM ad_entity_perf WHERE tenant_id=? AND grain=?", (tenant_id, grain)).fetchone()
        return {"spend": r["spend"], "clicks": r["clicks"], "orders": r["orders"], "rows": r["rows"]}

    def coverage(self, tenant_id, grain="month"):
        """{mapped_spend, unmapped_spend, total_spend, coverage_pct} — the attributable claim, auditable.
        Unmapped = spend on an advertised ASIN with no resolved internal_sku (would otherwise be dropped)."""
        rows = self.con.execute(
            "SELECT internal_sku, SUM(spend) AS spend FROM ad_entity_perf "
            "WHERE tenant_id=? AND grain=? GROUP BY internal_sku", (tenant_id, grain)).fetchall()
        mapped = sum((r["spend"] or 0.0) for r in rows if r["internal_sku"])
        unmapped = sum((r["spend"] or 0.0) for r in rows if not r["internal_sku"])
        total = mapped + unmapped
        return {"mapped_spend": mapped, "unmapped_spend": unmapped, "total_spend": total,
                "coverage_pct": (mapped / total * 100.0) if total > 0 else None}

    def counts(self, tenant_id, grain="month"):
        """{entity_rows, mapped_rows} — RAW row counts read straight from the table (the independent
        tiebreaker for the fallback decision: entity_rows>0 with 0 recommendations is never a benign
        fallback). mapped_rows = rows keyed to a catalog SKU."""
        r = self.con.execute(
            "SELECT COUNT(*) AS entity_rows, "
            "SUM(CASE WHEN internal_sku IS NOT NULL AND internal_sku<>'' THEN 1 ELSE 0 END) AS mapped_rows "
            "FROM ad_entity_perf WHERE tenant_id=? AND grain=?", (tenant_id, grain)).fetchone()
        return {"entity_rows": (r["entity_rows"] or 0), "mapped_rows": (r["mapped_rows"] or 0)}

    def clear(self, tenant_id):
        self.con.execute("DELETE FROM ad_entity_perf WHERE tenant_id=?", (tenant_id,))
        self.con.commit()


class AdSearchTermRepository(BaseRepository):
    """SP Search Term rows. Target-grained (campaign/ad group/targeting/customer search term); SKU linkage
    is via AdEntityPerf on (campaign, ad_group)."""

    def upsert(self, tenant_id, campaign, ad_group, targeting, match_type, customer_search_term,
               period_start, grain, spend, sales, clicks=None, orders=None):
        self.con.execute(
            "INSERT OR REPLACE INTO ad_search_term"
            "(tenant_id, campaign, ad_group, targeting, match_type, customer_search_term,"
            " period_start, grain, spend, sales, clicks, orders, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, campaign or "", ad_group or "", targeting, match_type,
             customer_search_term or "", period_start, grain, spend, sales, clicks, orders, _now()))

    def grouped(self, tenant_id, grain="month"):
        """{(campaign, ad_group): [term rows]} — engine-safe (filter in the caller by the SKU's slices)."""
        out = {}
        for r in self.con.execute(
                "SELECT campaign, ad_group, targeting, match_type, customer_search_term, "
                "SUM(spend) AS spend, SUM(sales) AS sales, SUM(clicks) AS clicks, SUM(orders) AS orders "
                "FROM ad_search_term WHERE tenant_id=? AND grain=? "
                "GROUP BY campaign, ad_group, targeting, match_type, customer_search_term",
                (tenant_id, grain)).fetchall():
            out.setdefault((r["campaign"], r["ad_group"]), []).append(dict(r))
        return out

    def count(self, tenant_id):
        r = self.con.execute("SELECT COUNT(*) AS n FROM ad_search_term WHERE tenant_id=?",
                             (tenant_id,)).fetchone()
        return r["n"] if r else 0

    def clear(self, tenant_id):
        self.con.execute("DELETE FROM ad_search_term WHERE tenant_id=?", (tenant_id,))
        self.con.commit()


class AdIngestSummaryRepository(BaseRepository):
    """One row per tenant: the coverage + fidelity + granularity verdict, surfaced honestly in the UI."""

    def upsert(self, tenant_id, coverage_pct, mapped_spend, unmapped_spend, fidelity,
               granularity_flag=None, has_advertised_product=0, has_search_term=0, has_campaign_only=0):
        self.con.execute(
            "INSERT OR REPLACE INTO ad_ingest_summary"
            "(tenant_id, coverage_pct, mapped_spend, unmapped_spend, fidelity, granularity_flag,"
            " has_advertised_product, has_search_term, has_campaign_only, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, coverage_pct, mapped_spend, unmapped_spend, fidelity, granularity_flag,
             int(has_advertised_product), int(has_search_term), int(has_campaign_only), _now()))

    def get(self, tenant_id):
        r = self.con.execute("SELECT * FROM ad_ingest_summary WHERE tenant_id=?",
                             (tenant_id,)).fetchone()
        return dict(r) if r else None

    def clear(self, tenant_id):
        self.con.execute("DELETE FROM ad_ingest_summary WHERE tenant_id=?", (tenant_id,))
        self.con.commit()
