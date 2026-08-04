"""Channel layer: products / channel_listings / returns / storage_fees / channels /
channel_economics. SQL moved verbatim from channels.py and multichannel.py (1b-2).
Writes don't commit (the build routines own the transaction)."""
from .base import BaseRepository


class ProductRepository(BaseRepository):
    def upsert(self, tenant_id, internal_sku, title, category, brand, cogs, created_at):
        self.con.execute(
            "INSERT OR REPLACE INTO products(tenant_id,internal_sku,title,category,brand,cogs,created_at) "
            "VALUES(?,?,?,?,?,?,?)", (tenant_id, internal_sku, title, category, brand, cogs, created_at))

    def all(self, tenant_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM products WHERE tenant_id=?", (tenant_id,)).fetchall()]

    def count(self, tenant_id):
        return self.con.execute("SELECT COUNT(*) c FROM products WHERE tenant_id=?",
                                (tenant_id,)).fetchone()["c"]

    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM products WHERE tenant_id=?", (tenant_id,))


class ChannelListingRepository(BaseRepository):
    def upsert(self, tenant_id, internal_sku, channel, channel_id, channel_sku,
               listing_status, link_status, price, url):
        self.con.execute(
            "INSERT OR REPLACE INTO channel_listings(tenant_id,internal_sku,channel,channel_id,"
            "channel_sku,listing_status,link_status,price,url) VALUES(?,?,?,?,?,?,?,?,?)",
            (tenant_id, internal_sku, channel, channel_id, channel_sku, listing_status,
             link_status, price, url))

    def by_sku(self, tenant_id, internal_sku):
        return [dict(r) for r in self.con.execute(
            "SELECT channel,channel_id,price,link_status FROM channel_listings "
            "WHERE tenant_id=? AND internal_sku=?", (tenant_id, internal_sku)).fetchall()]

    def count(self, tenant_id):
        return self.con.execute("SELECT COUNT(*) c FROM channel_listings WHERE tenant_id=?",
                                (tenant_id,)).fetchone()["c"]

    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM channel_listings WHERE tenant_id=?", (tenant_id,))


class ReturnsRepository(BaseRepository):
    def insert(self, tenant_id, channel, internal_sku, return_date, order_id, units, reason, refund_amount):
        self.con.execute(
            "INSERT INTO returns(tenant_id,channel,internal_sku,return_date,order_id,units,reason,refund_amount) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (tenant_id, channel, internal_sku, return_date, order_id, units, reason, refund_amount))

    def insert_many(self, batch):
        """Bulk insert (report-aware ingest: tenant_id, channel, internal_sku, return_date,
        order_id, units, reason, refund_amount tuples)."""
        self.con.executemany(
            "INSERT INTO returns(tenant_id,channel,internal_sku,return_date,order_id,units,reason,refund_amount) "
            "VALUES(?,?,?,?,?,?,?,?)", batch)

    def delete_by_channel(self, tenant_id, channel):
        self.con.execute("DELETE FROM returns WHERE tenant_id=? AND channel=?", (tenant_id, channel))

    def count(self, tenant_id):
        return self.con.execute("SELECT COUNT(*) c FROM returns WHERE tenant_id=?",
                                (tenant_id,)).fetchone()["c"]

    def window_summary(self, tenant_id, since):
        """refund_amount/units totals since a date (Workspace revenue substats: Net Revenue)."""
        return dict(self.con.execute(
            "SELECT COALESCE(SUM(refund_amount),0) refund_amount, COALESCE(SUM(units),0) units "
            "FROM returns WHERE tenant_id=? AND return_date>=?", (tenant_id, since)).fetchone())

    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM returns WHERE tenant_id=?", (tenant_id,))


class StorageFeeRepository(BaseRepository):
    def insert(self, tenant_id, channel, internal_sku, period, monthly_storage_fee,
               aged_surcharge, volume_cuft, age_days):
        self.con.execute(
            "INSERT INTO storage_fees(tenant_id,channel,internal_sku,period,monthly_storage_fee,aged_surcharge,volume_cuft,age_days) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (tenant_id, channel, internal_sku, period, monthly_storage_fee, aged_surcharge,
             volume_cuft, age_days))

    def insert_many(self, batch):
        """Bulk insert (report-aware ingest: tenant_id, channel, internal_sku, period,
        monthly_storage_fee, aged_surcharge, volume_cuft, age_days tuples)."""
        self.con.executemany(
            "INSERT INTO storage_fees(tenant_id,channel,internal_sku,period,monthly_storage_fee,aged_surcharge,volume_cuft,age_days) "
            "VALUES(?,?,?,?,?,?,?,?)", batch)

    def delete_by_channel(self, tenant_id, channel):
        self.con.execute("DELETE FROM storage_fees WHERE tenant_id=? AND channel=?", (tenant_id, channel))

    def count(self, tenant_id):
        return self.con.execute("SELECT COUNT(*) c FROM storage_fees WHERE tenant_id=?",
                                (tenant_id,)).fetchone()["c"]

    def window_summary(self, tenant_id, since_month):
        """monthly_storage_fee+aged_surcharge total since a 'YYYY-MM' period (Workspace margin/cash substats).
        `period` is stored month-granular, so filtering is by month prefix, not exact date."""
        return self.con.execute(
            "SELECT COALESCE(SUM(monthly_storage_fee),0)+COALESCE(SUM(aged_surcharge),0) v "
            "FROM storage_fees WHERE tenant_id=? AND period>=?", (tenant_id, since_month)).fetchone()["v"]

    def all_time_summary(self, tenant_id):
        """monthly_storage_fee+aged_surcharge total, all periods (Workspace cash substats: Cash Balance)."""
        return self.con.execute(
            "SELECT COALESCE(SUM(monthly_storage_fee),0)+COALESCE(SUM(aged_surcharge),0) v "
            "FROM storage_fees WHERE tenant_id=?", (tenant_id,)).fetchone()["v"]

    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM storage_fees WHERE tenant_id=?", (tenant_id,))


class ChannelRepository(BaseRepository):
    """The `channels` registry (which marketplaces are active for a tenant)."""
    def upsert(self, tenant_id, channel, label, active, fee_pct, fulfillment, currency):
        self.con.execute(
            "INSERT OR REPLACE INTO channels(tenant_id,channel,label,active,fee_pct,fulfillment,currency) "
            "VALUES(?,?,?,?,?,?,?)", (tenant_id, channel, label, active, fee_pct, fulfillment, currency))

    def active(self, tenant_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM channels WHERE tenant_id=? AND active=1", (tenant_id,)).fetchall()]


class ChannelEconomicsRepository(BaseRepository):
    """`channel_economics` — the per-(sku,channel) fanned-out economics rows."""
    def all(self, tenant_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM channel_economics WHERE tenant_id=?", (tenant_id,)).fetchall()]

    def count_present(self, tenant_id, channel):
        return self.con.execute(
            "SELECT COUNT(*) n FROM channel_economics WHERE tenant_id=? AND channel=? AND present=1",
            (tenant_id, channel)).fetchone()["n"]

    def delete_all(self, tenant_id):
        self.con.execute("DELETE FROM channel_economics WHERE tenant_id=?", (tenant_id,))

    def insert_absent(self, tenant_id, internal_sku, asin, title, category, channel, fee_pct, cogs, fulfillment):
        """A channel where the SKU is NOT present (recorded so the gap shows in the view)."""
        self.con.execute(
            "INSERT OR REPLACE INTO channel_economics(tenant_id,internal_sku,asin,title,category,"
            "channel,present,price,units_month,referral_pct,fee_unit,ad_unit,cogs,net_unit,margin_pct,"
            "revenue_month,on_hand,days_cover,fulfillment,source) "
            "VALUES(?,?,?,?,?,?,0,NULL,0,?,0,0,?,0,0,0,0,0,?, 'synthetic')",
            (tenant_id, internal_sku, asin, title, category, channel, fee_pct, cogs, fulfillment))

    def insert_present(self, tenant_id, internal_sku, asin, title, category, channel, price,
                        units_month, referral_pct, fee_unit, ad_unit, cogs, net_unit, margin_pct,
                        revenue_month, on_hand, days_cover, fulfillment):
        self.con.execute(
            "INSERT OR REPLACE INTO channel_economics(tenant_id,internal_sku,asin,title,category,"
            "channel,present,price,units_month,referral_pct,fee_unit,ad_unit,cogs,net_unit,margin_pct,"
            "revenue_month,on_hand,days_cover,fulfillment,source) "
            "VALUES(?,?,?,?,?,?,1,?,?,?,?,?,?,?,?,?,?,?,?, 'synthetic')",
            (tenant_id, internal_sku, asin, title, category, channel, price, units_month, referral_pct,
             fee_unit, ad_unit, cogs, net_unit, margin_pct, revenue_month, on_hand, days_cover, fulfillment))
