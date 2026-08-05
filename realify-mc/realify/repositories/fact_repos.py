"""Per-channel fact tables: traffic / inventory / settlements.
SQL moved verbatim from channels.py / ingest/report_parse.py / api.py / synth_conditions.py /
pipeline/detect.py (workstream 1b-2). Writes don't commit."""
from .base import BaseRepository


class TrafficRepository(BaseRepository):
    def internal_skus_ordered(self, tenant_id):
        return [r["internal_sku"] for r in self.con.execute(
            "SELECT internal_sku FROM traffic WHERE tenant_id=? ORDER BY internal_sku",
            (tenant_id,)).fetchall()]

    def count_with_conversion(self, tenant_id):
        return self.con.execute(
            "SELECT COUNT(*) c FROM traffic WHERE tenant_id=? AND conversion_pct IS NOT NULL",
            (tenant_id,)).fetchone()["c"]

    def conversion_values(self, tenant_id):
        """Non-null conversion_pct values as reported by the seller (Sales & Traffic upload) —
        never computed from clicks/orders."""
        return [r["conversion_pct"] for r in self.con.execute(
            "SELECT conversion_pct FROM traffic WHERE tenant_id=? AND conversion_pct IS NOT NULL",
            (tenant_id,)).fetchall()]

    def conversion_by_asin(self, tenant_id):
        """asin -> conversion_pct, joining traffic to channel_listings on internal_sku."""
        return self.con.execute(
            "SELECT cl.channel_id asin, t.conversion_pct conv "
            "FROM traffic t JOIN channel_listings cl ON cl.tenant_id=t.tenant_id AND cl.internal_sku=t.internal_sku "
            "WHERE t.tenant_id=?", (tenant_id,)).fetchall()

    def count(self, tenant_id):
        return self.con.execute("SELECT COUNT(*) c FROM traffic WHERE tenant_id=?",
                                (tenant_id,)).fetchone()["c"]

    def set_conversion(self, tenant_id, internal_sku, conversion_pct):
        self.con.execute(
            "UPDATE traffic SET conversion_pct=? WHERE tenant_id=? AND internal_sku=?",
            (conversion_pct, tenant_id, internal_sku))

    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM traffic WHERE tenant_id=?", (tenant_id,))

    def delete_by_channel_date(self, tenant_id, channel, date):
        self.con.execute("DELETE FROM traffic WHERE tenant_id=? AND channel=? AND date=?",
                         (tenant_id, channel, date))

    def insert(self, tenant_id, channel, internal_sku, date, sessions, page_views,
               conversion_pct, buybox_pct):
        self.con.execute(
            "INSERT INTO traffic(tenant_id,channel,internal_sku,date,sessions,page_views,conversion_pct,buybox_pct) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (tenant_id, channel, internal_sku, date, sessions, page_views, conversion_pct, buybox_pct))


class InventoryRepository(BaseRepository):
    def list_on_hand(self, tenant_id):
        return self.con.execute(
            "SELECT on_hand, internal_sku sku FROM inventory WHERE tenant_id=?", (tenant_id,)).fetchall()

    def count_low_cover(self, tenant_id):
        return self.con.execute(
            "SELECT COUNT(*) c FROM inventory WHERE tenant_id=? AND days_of_cover<14",
            (tenant_id,)).fetchone()["c"]

    def sum_by_sku(self, tenant_id, internal_sku):
        return self.con.execute(
            "SELECT COALESCE(SUM(on_hand),0) oh, COALESCE(SUM(inbound),0) ib "
            "FROM inventory WHERE tenant_id=? AND internal_sku=?", (tenant_id, internal_sku)).fetchone()

    def count(self, tenant_id):
        return self.con.execute("SELECT COUNT(*) c FROM inventory WHERE tenant_id=?",
                                (tenant_id,)).fetchone()["c"]

    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM inventory WHERE tenant_id=?", (tenant_id,))

    def insert(self, tenant_id, channel, internal_sku, captured_at, on_hand, inbound,
               reserved, unfulfillable, days_of_cover):
        self.con.execute(
            "INSERT INTO inventory(tenant_id,channel,internal_sku,captured_at,on_hand,inbound,reserved,unfulfillable,days_of_cover) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (tenant_id, channel, internal_sku, captured_at, on_hand, inbound, reserved,
             unfulfillable, days_of_cover))


class SettlementRepository(BaseRepository):
    def window_summary(self, tenant_id, since):
        return self.con.execute(
            "SELECT COALESCE(SUM(payout),0) payout, COALESCE(SUM(gross-fees-payout),0) short, "
            "COALESCE(SUM(fees),0) fees "
            "FROM settlements WHERE tenant_id=? AND settlement_date>=?", (tenant_id, since)).fetchone()

    def all_time_summary(self, tenant_id):
        """payout/fees totals, all periods (Workspace cash substats: Cash Balance)."""
        return self.con.execute(
            "SELECT COALESCE(SUM(payout),0) payout, COALESCE(SUM(fees),0) fees "
            "FROM settlements WHERE tenant_id=?", (tenant_id,)).fetchone()

    def window_gross_by_channel(self, tenant_id, since):
        """gross totals per channel since a date (Workspace margin substats: payment-processing proxy)."""
        return {r["channel"]: r["gross"] for r in self.con.execute(
            "SELECT channel, COALESCE(SUM(gross),0) gross FROM settlements "
            "WHERE tenant_id=? AND settlement_date>=? GROUP BY channel", (tenant_id, since)).fetchall()}

    def sum_fees_by_sku(self, tenant_id, internal_sku):
        return self.con.execute(
            "SELECT COALESCE(SUM(fees),0) f FROM settlements WHERE tenant_id=? AND internal_sku=?",
            (tenant_id, internal_sku)).fetchone()["f"]

    def count(self, tenant_id):
        return self.con.execute("SELECT COUNT(*) c FROM settlements WHERE tenant_id=?",
                                (tenant_id,)).fetchone()["c"]

    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM settlements WHERE tenant_id=?", (tenant_id,))

    def delete_by_channel(self, tenant_id, channel):
        self.con.execute("DELETE FROM settlements WHERE tenant_id=? AND channel=?", (tenant_id, channel))

    def insert(self, tenant_id, channel, internal_sku, order_id, settlement_date, gross, fees, payout, reserve):
        self.con.execute(
            "INSERT INTO settlements(tenant_id,channel,internal_sku,order_id,settlement_date,gross,fees,payout,reserve) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (tenant_id, channel, internal_sku, order_id, settlement_date, gross, fees, payout, reserve))

    def insert_many(self, batch):
        self.con.executemany(
            "INSERT INTO settlements(tenant_id,channel,internal_sku,order_id,settlement_date,gross,fees,payout,reserve) "
            "VALUES(?,?,?,?,?,?,?,?,?)", batch)
