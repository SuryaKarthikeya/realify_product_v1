"""Own-data metric history (snapshots over time). SQL moved verbatim from db.py (workstream 1b).

The list of tracked metrics lives in db.HISTORY_METRICS (kept there as it's referenced by the
schema/seed too)."""
from .. import db
from .base import BaseRepository


class MetricsRepository(BaseRepository):
    def snapshot(self, tenant_id, captured_at=None):
        """Write one history row per (asin, tracked metric) from current seller_skus."""
        captured_at = captured_at or db.now_iso()
        cols = ",".join(db.HISTORY_METRICS)
        rows = self.con.execute(
            f"SELECT asin,{cols} FROM seller_skus WHERE tenant_id=?", (tenant_id,)
        ).fetchall()
        payload = []
        for r in rows:
            for m in db.HISTORY_METRICS:
                v = r[m]
                if v is not None:
                    payload.append((tenant_id, r["asin"], m, float(v), captured_at))
        self.con.executemany(
            "INSERT INTO metric_history(tenant_id,asin,metric,value,captured_at) VALUES(?,?,?,?,?)",
            payload,
        )
        self.con.commit()
        return len(payload)

    def series(self, tenant_id, asin, metric, limit=400):
        """Ascending (captured_at, value) series for one SKU+metric."""
        rows = self.con.execute(
            """SELECT value, captured_at FROM metric_history
               WHERE tenant_id=? AND asin=? AND metric=? ORDER BY captured_at ASC LIMIT ?""",
            (tenant_id, asin, metric, limit),
        ).fetchall()
        return [(r["captured_at"], r["value"]) for r in rows]

    # ---- added in 1b-2: metric_history sites previously inline in history.py / run.py ----
    def history_exists(self, tenant_id):
        return self.con.execute(
            "SELECT 1 FROM metric_history WHERE tenant_id=? LIMIT 1", (tenant_id,)).fetchone() is not None

    def insert_history_many(self, payload):
        """executemany of (tenant_id,asin,metric,value,captured_at) tuples. Caller commits."""
        self.con.executemany(
            "INSERT INTO metric_history(tenant_id,asin,metric,value,captured_at) VALUES(?,?,?,?,?)",
            payload)

    def delete_history(self, tenant_id):
        self.con.execute("DELETE FROM metric_history WHERE tenant_id=?", (tenant_id,))
