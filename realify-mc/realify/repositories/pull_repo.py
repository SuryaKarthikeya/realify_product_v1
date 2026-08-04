"""Incremental pull bookkeeping (watermarks + pull_log), tenant-scoped.
SQL moved verbatim from db.py (workstream 1b)."""
import datetime as dt
from .. import db
from .base import BaseRepository


class PullLogRepository(BaseRepository):
    def last_watermark(self, tenant_id, source, scope):
        row = self.con.execute(
            "SELECT MAX(window_to) AS wm FROM pull_log WHERE tenant_id=? AND source=? AND scope=? AND status='ok'",
            (tenant_id, source, scope),
        ).fetchone()
        return row["wm"] if row and row["wm"] else None

    def last_successful_pull_time(self, tenant_id, source, scope):
        row = self.con.execute(
            "SELECT MAX(finished_at) AS t FROM pull_log WHERE tenant_id=? AND source=? AND scope=? AND status='ok'",
            (tenant_id, source, scope),
        ).fetchone()
        return row["t"] if row and row["t"] else None

    def record(self, tenant_id, source, scope, started_at, status, records, window_from, window_to, note=""):
        self.con.execute(
            "INSERT INTO pull_log(tenant_id,source,scope,started_at,finished_at,status,records,window_from,window_to,note)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, source, scope, started_at, db.now_iso(), status, records, window_from, window_to, note),
        )
        self.con.commit()

    def due(self, tenant_id, source, scope, interval_hours):
        last = self.last_successful_pull_time(tenant_id, source, scope)
        if not last:
            return True
        last_dt = dt.datetime.fromisoformat(last)
        return (dt.datetime.now(dt.timezone.utc) - last_dt) >= dt.timedelta(hours=interval_hours)

    # ---- added in 1b-2: sites previously inline in api.py / scheduler.py / run.py ----
    def max_ok_by_source(self, tenant_id, source):
        """(MAX finished_at, MAX records) for a tenant+source where status='ok'."""
        return self.con.execute(
            "SELECT MAX(finished_at) t, MAX(records) r FROM pull_log "
            "WHERE tenant_id=? AND source=? AND status='ok'", (tenant_id, source)).fetchone()

    def max_ok(self, tenant_id):
        return self.con.execute(
            "SELECT MAX(finished_at) t FROM pull_log WHERE tenant_id=? AND status='ok'",
            (tenant_id,)).fetchone()["t"]

    def last_by_source(self, tenant_id, source):
        return self.con.execute(
            "SELECT status, note, records FROM pull_log WHERE tenant_id=? AND source=? "
            "ORDER BY id DESC LIMIT 1", (tenant_id, source)).fetchone()

    def log_import(self, tenant_id, source, scope, started_at, finished_at, status, records, note):
        """The import-path pull_log row (no window columns). Caller commits."""
        self.con.execute(
            "INSERT INTO pull_log(tenant_id,source,scope,started_at,finished_at,status,records,note) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (tenant_id, source, scope, started_at, finished_at, status, records, note))

    def sources_last_global(self):
        return self.con.execute(
            "SELECT source, MAX(finished_at) last_at FROM pull_log GROUP BY source").fetchall()

    def last_global_by_source(self, source):
        return self.con.execute(
            "SELECT status, finished_at, note FROM pull_log WHERE source=? "
            "ORDER BY finished_at DESC LIMIT 1", (source,)).fetchone()
