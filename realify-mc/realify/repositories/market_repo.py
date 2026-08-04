"""Market data: keepa_snapshots / competitor_offers / tierc_signals.
SQL moved verbatim from pipeline/detect.py, pipeline/research.py,
collectors/keepa_collector.py, collectors/tierc_collector.py (1b-2). Writes don't commit."""
from .base import BaseRepository


class MarketRepository(BaseRepository):
    # ---- keepa_snapshots ----
    def recent_snapshots(self, tenant_id, asin, limit=2):
        return self.con.execute(
            "SELECT * FROM keepa_snapshots WHERE tenant_id=? AND asin=? ORDER BY captured_at DESC LIMIT ?",
            (tenant_id, asin, limit)).fetchall()

    def latest_bsr(self, tenant_id, asin):
        return self.con.execute(
            "SELECT bsr FROM keepa_snapshots WHERE tenant_id=? AND asin=? AND bsr IS NOT NULL "
            "ORDER BY captured_at DESC LIMIT 1", (tenant_id, asin)).fetchone()

    def insert_snapshot(self, tenant_id, asin, captured_at, price, bsr, bsr_avg30, rating,
                        review_count, offer_count, buybox_price, buybox_seller, raw):
        self.con.execute(
            "INSERT OR IGNORE INTO keepa_snapshots("
            "tenant_id,asin,captured_at,price,bsr,bsr_avg30,rating,review_count,offer_count,"
            "buybox_price,buybox_seller,raw) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, asin, captured_at, price, bsr, bsr_avg30, rating, review_count,
             offer_count, buybox_price, buybox_seller, raw))

    # ---- competitor_offers ----
    def latest_offers(self, tenant_id, asin):
        return self.con.execute(
            "SELECT seller,price FROM competitor_offers "
            "WHERE tenant_id=? AND asin=? AND captured_at=("
            "SELECT MAX(captured_at) FROM competitor_offers WHERE tenant_id=? AND asin=?) "
            "ORDER BY price ASC",
            (tenant_id, asin, tenant_id, asin)).fetchall()

    def insert_offer(self, tenant_id, asin, captured_at, seller, price, is_buybox, is_fba, in_stock, condition):
        self.con.execute(
            "INSERT INTO competitor_offers("
            "tenant_id,asin,captured_at,seller,price,is_buybox,is_fba,in_stock,condition) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (tenant_id, asin, captured_at, seller, price, is_buybox, is_fba, in_stock, condition))

    # ---- tierc_signals ----
    def latest_trend(self, tenant_id):
        return self.con.execute(
            "SELECT title,summary,raw FROM tierc_signals WHERE tenant_id=? AND signal_type='trend' "
            "ORDER BY published_at DESC LIMIT 1", (tenant_id,)).fetchone()

    def trends(self, tenant_id, limit=3):
        return self.con.execute(
            "SELECT * FROM tierc_signals WHERE tenant_id=? AND signal_type='trend' "
            "ORDER BY published_at DESC LIMIT ?", (tenant_id, limit)).fetchall()

    def latest_signal(self, tenant_id, signal_type):
        """Returns a list of 0 or 1 rows (LIMIT 1) — the call site iterates the result."""
        return self.con.execute(
            "SELECT * FROM tierc_signals WHERE tenant_id=? AND signal_type=? "
            "ORDER BY published_at DESC LIMIT 1", (tenant_id, signal_type)).fetchall()

    def insert_signal(self, tenant_id, source, signal_type, captured_at, published_at, category,
                      title, url, summary, confidence, raw, dedup_key):
        self.con.execute(
            "INSERT OR IGNORE INTO tierc_signals("
            "tenant_id,source,signal_type,captured_at,published_at,category,title,url,summary,confidence,raw,dedup_key) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, source, signal_type, captured_at, published_at, category, title, url,
             summary, confidence, raw, dedup_key))
