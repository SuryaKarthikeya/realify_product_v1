"""Category/competitor product cache — the `category_products` table.
SQL moved verbatim from collectors/keepa_collector.py (workstream 1b). No commit; caller owns it."""
from .. import db
from .base import BaseRepository


class CatalogRepository(BaseRepository):
    def cached_segment(self, tenant_id, segment):
        """Cached competitor SKUs for a segment, best-rank first. [] if none cached."""
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM category_products WHERE tenant_id=? AND segment=? ORDER BY bsr ASC",
            (tenant_id, segment)).fetchall()]

    def insert_product(self, tenant_id, category, segment, asin, title, brand, price, bsr, reviews, rating):
        self.con.execute(
            """INSERT OR IGNORE INTO category_products(tenant_id,category,segment,asin,title,brand,price,bsr,reviews,rating,captured_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (tenant_id, category, segment, asin, title, brand, price, bsr, reviews, rating, db.now_iso()))
