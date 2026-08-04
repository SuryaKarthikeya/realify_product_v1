"""Per-period settled revenue repository (Step 4). The TACoS denominator: the CMAA trust layer reads
revenue-by-period from here and divides ad_performance spend by it to get TACoS over time.
"""
import datetime

from .base import BaseRepository


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class RevenuePeriodRepository(BaseRepository):
    def upsert(self, tenant_id, internal_sku, period_start, grain, revenue, units):
        if not internal_sku:
            return
        self.con.execute(
            "INSERT OR REPLACE INTO sku_revenue_period"
            "(tenant_id, internal_sku, period_start, grain, revenue, units, updated_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (tenant_id, internal_sku, period_start, grain, revenue, units, _now()))

    def for_sku(self, tenant_id, internal_sku, grain="month"):
        return {r["period_start"]: r["revenue"] for r in self.con.execute(
            "SELECT period_start, revenue FROM sku_revenue_period "
            "WHERE tenant_id=? AND internal_sku=? AND grain=? ORDER BY period_start",
            (tenant_id, internal_sku, grain)).fetchall()}

    def all_by_sku(self, tenant_id, grain="month"):
        """{internal_sku: {period_start: revenue}} — revenue series per SKU."""
        out = {}
        for r in self.con.execute(
                "SELECT internal_sku, period_start, revenue FROM sku_revenue_period "
                "WHERE tenant_id=? AND grain=?", (tenant_id, grain)).fetchall():
            out.setdefault(r["internal_sku"], {})[r["period_start"]] = r["revenue"]
        return out

    def units_by_sku(self, tenant_id, grain="month"):
        """{internal_sku: {period_start: units}} — units series per SKU. Pairs with all_by_sku so the
        CMAA tab can sum units AND revenue over the SAME periods the ad totals cover (window-consistent
        contribution vs cumulative ad spend)."""
        out = {}
        for r in self.con.execute(
                "SELECT internal_sku, period_start, units FROM sku_revenue_period "
                "WHERE tenant_id=? AND grain=?", (tenant_id, grain)).fetchall():
            out.setdefault(r["internal_sku"], {})[r["period_start"]] = r["units"]
        return out
