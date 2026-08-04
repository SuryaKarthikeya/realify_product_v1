"""Orders — the `seller_orders` table. SQL moved verbatim from seller.py / api.py /
ingest/report_parse.py / channels.py / tasks.py (workstream 1b-2). Writes don't commit."""
from .base import BaseRepository

_INSERT_SYNTH_COLS = ("tenant_id,order_id,asin,order_date,units,gross,referral_fee,fba_fee,"
                      "expected_deposit,actual_deposit,settlement_date,delivered_date,"
                      "has_review,review_eligible,status")


class OrderRepository(BaseRepository):
    # ---- reads ----
    def count(self, tenant_id):
        return self.con.execute("SELECT COUNT(*) c FROM seller_orders WHERE tenant_id=?",
                                (tenant_id,)).fetchone()["c"]

    def count_short_paid(self, tenant_id):
        return self.con.execute(
            "SELECT COUNT(*) c FROM seller_orders WHERE tenant_id=? AND actual_deposit>0 "
            "AND actual_deposit < expected_deposit*0.99", (tenant_id,)).fetchone()["c"]

    def count_review_eligible(self, tenant_id):
        return self.con.execute(
            "SELECT COUNT(*) c FROM seller_orders WHERE tenant_id=? AND review_eligible=1",
            (tenant_id,)).fetchone()["c"]

    def window_rows(self, tenant_id, since):
        """asin/units/gross/referral_fee/fba_fee for orders since a date (KPI rollup)."""
        return self.con.execute(
            "SELECT asin,units,gross,referral_fee,fba_fee FROM seller_orders "
            "WHERE tenant_id=? AND order_date>=?", (tenant_id, since)).fetchall()

    def range_rows(self, tenant_id, since, until=None):
        """Bounded-range sibling of window_rows (which is open-ended: since -> today). Pass
        `until` to get a closed-start/open-end [since, until) slice — the prior-period comparison
        window for MoM (Workspace Brief). `until=None` behaves exactly like window_rows."""
        if until is None:
            return self.window_rows(tenant_id, since)
        return self.con.execute(
            "SELECT asin,units,gross,referral_fee,fba_fee FROM seller_orders "
            "WHERE tenant_id=? AND order_date>=? AND order_date<?",
            (tenant_id, since, until)).fetchall()

    def window_aggregate(self, tenant_id, since):
        """orders/units/gross/referral_fee/fba_fee totals since a date (Workspace revenue substats)."""
        return dict(self.con.execute(
            "SELECT COUNT(DISTINCT order_id) orders, COALESCE(SUM(units),0) units, "
            "COALESCE(SUM(gross),0) gross, COALESCE(SUM(referral_fee),0) referral_fee, "
            "COALESCE(SUM(fba_fee),0) fba_fee FROM seller_orders "
            "WHERE tenant_id=? AND order_date>=?", (tenant_id, since)).fetchone())

    def pending_deposit_sum(self, tenant_id):
        """expected_deposit for orders not yet settled (Workspace cash substats: Payouts Pending)."""
        return self.con.execute(
            "SELECT COALESCE(SUM(expected_deposit),0) v FROM seller_orders "
            "WHERE tenant_id=? AND settlement_date IS NULL", (tenant_id,)).fetchone()["v"]

    def all_time_units_by_asin(self, tenant_id):
        """asin -> total units ever sold (Workspace cash substats: all-time COGS-on-sold-units)."""
        return {r["asin"]: r["units"] for r in self.con.execute(
            "SELECT asin, COALESCE(SUM(units),0) units FROM seller_orders "
            "WHERE tenant_id=? GROUP BY asin", (tenant_id,)).fetchall()}

    def settled(self, tenant_id):
        return self.con.execute(
            "SELECT order_id,internal_sku,gross,referral_fee,fba_fee,actual_deposit,settlement_date "
            "FROM seller_orders WHERE tenant_id=? AND status='settled'", (tenant_id,)).fetchall()

    def channel_rollup(self, tenant_id, internal_sku):
        return self.con.execute(
            "SELECT channel, COUNT(*) orders, SUM(units) units, SUM(gross) revenue "
            "FROM seller_orders WHERE tenant_id=? AND internal_sku=? GROUP BY channel",
            (tenant_id, internal_sku)).fetchall()

    def short_paid_detail(self, tenant_id, asin=None, limit=12):
        """Settled orders whose deposit fell short, worst-gap first (case builder)."""
        q = ("SELECT order_id,order_date,expected_deposit,actual_deposit "
             "FROM seller_orders WHERE tenant_id=? AND actual_deposit>0 "
             "AND actual_deposit < expected_deposit*0.99 " +
             ("AND asin=? " if asin else "") +
             "ORDER BY (expected_deposit-actual_deposit) DESC LIMIT ?")
        params = (tenant_id, asin, limit) if asin else (tenant_id, limit)
        return self.con.execute(q, params).fetchall()

    def review_eligible_detail(self, tenant_id, asin=None, limit=25):
        q = ("SELECT order_id,delivered_date FROM seller_orders "
             "WHERE tenant_id=? AND review_eligible=1 " +
             ("AND asin=? " if asin else "") +
             "ORDER BY delivered_date DESC LIMIT ?")
        params = (tenant_id, asin, limit) if asin else (tenant_id, limit)
        return self.con.execute(q, params).fetchall()

    # ---- writes (no commit) ----
    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM seller_orders WHERE tenant_id=?", (tenant_id,))

    def delete_by_channel(self, tenant_id, channel):
        self.con.execute("DELETE FROM seller_orders WHERE tenant_id=? AND channel=?", (tenant_id, channel))

    def insert_many_synthetic(self, batch):
        """executemany of fully-formed synthetic order tuples (seller.generate_orders)."""
        qs = ",".join("?" * 15)
        self.con.executemany(
            f"INSERT OR IGNORE INTO seller_orders({_INSERT_SYNTH_COLS}) VALUES({qs})", batch)

    def insert_imported(self, tenant_id, order_id, asin, order_date, units, gross, channel, internal_sku):
        """Customer-uploaded order row (report_parse 'orders'); status defaults to 'settled'."""
        self.con.execute(
            "INSERT INTO seller_orders(tenant_id,order_id,asin,order_date,units,gross,channel,internal_sku,status) "
            "VALUES(?,?,?,?,?,?,?,?, 'settled')",
            (tenant_id, order_id, asin, order_date, units, gross, channel, internal_sku))

    def insert_many_imported(self, batch):
        """Bulk insert_imported (report-aware ingest, e.g. Unified Transaction rows: tenant_id,
        order_id, asin, order_date, units, gross, referral_fee, fba_fee, channel, internal_sku
        tuples). OR REPLACE on the (tenant_id, order_id) primary key so re-uploading the same
        order is idempotent, not a crash."""
        self.con.executemany(
            "INSERT OR REPLACE INTO seller_orders(tenant_id,order_id,asin,order_date,units,gross,"
            "referral_fee,fba_fee,channel,internal_sku,status) "
            "VALUES(?,?,?,?,?,?,?,?,?,?, 'settled')", batch)

    def link_channel(self, tenant_id, asin, internal_sku, channel):
        self.con.execute(
            "UPDATE seller_orders SET internal_sku=?, channel=? WHERE tenant_id=? AND asin=?",
            (internal_sku, channel, tenant_id, asin))
