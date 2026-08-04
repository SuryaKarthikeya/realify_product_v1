"""Period-aware advertising repository (Step 2). The CMAA tab and TACoS-over-time read spend/sales
by period from here; the SP-report ingest and the future AdvertisedProductCollector both write here.
"""
import datetime

from .base import BaseRepository


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class AdPerformanceRepository(BaseRepository):
    def upsert(self, tenant_id, internal_sku, period_start, grain, spend, sales, source="sp_report_upload"):
        if not internal_sku:
            return
        self.con.execute(
            "INSERT OR REPLACE INTO ad_performance"
            "(tenant_id, internal_sku, period_start, grain, spend, sales, source, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (tenant_id, internal_sku, period_start, grain, spend, sales, source, _now()))

    def for_sku(self, tenant_id, internal_sku, grain="month"):
        return [dict(r) for r in self.con.execute(
            "SELECT period_start, spend, sales FROM ad_performance "
            "WHERE tenant_id=? AND internal_sku=? AND grain=? ORDER BY period_start",
            (tenant_id, internal_sku, grain)).fetchall()]

    def totals(self, tenant_id, grain="month"):
        """Per-SKU rolled-up spend/sales across all periods — the aggregate the CMAA tab starts from."""
        rows = self.con.execute(
            "SELECT internal_sku, SUM(spend) AS spend, SUM(sales) AS sales "
            "FROM ad_performance WHERE tenant_id=? AND grain=? GROUP BY internal_sku",
            (tenant_id, grain)).fetchall()
        return {r["internal_sku"]: {"spend": r["spend"], "sales": r["sales"]} for r in rows}

    def periods(self, tenant_id, grain="month"):
        return [r["period_start"] for r in self.con.execute(
            "SELECT DISTINCT period_start FROM ad_performance WHERE tenant_id=? AND grain=? "
            "ORDER BY period_start", (tenant_id, grain)).fetchall()]

    def all_by_sku(self, tenant_id, grain="month"):
        """{internal_sku: {period_start: spend}} — spend series per SKU, for TACoS-over-time."""
        out = {}
        for r in self.con.execute(
                "SELECT internal_sku, period_start, spend FROM ad_performance "
                "WHERE tenant_id=? AND grain=?", (tenant_id, grain)).fetchall():
            out.setdefault(r["internal_sku"], {})[r["period_start"]] = r["spend"]
        return out
