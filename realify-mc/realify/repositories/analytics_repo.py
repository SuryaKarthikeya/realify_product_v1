"""Usage analytics (`usage_events`) + deployment-wide admin counts.
SQL moved verbatim from analytics.py and run.py admin endpoints (1b-2). The analytics
write commits inline (best-effort telemetry, as before); reads don't commit."""
from .base import BaseRepository
import datetime


def _since(days):
    """Cutoff date (ISO 'YYYY-MM-DD') N days before today. Computed in Python and compared as a
    string against the stored ISO `day`, so the SQL is dialect-agnostic — SQLite's date('now',?)
    has no Postgres equivalent, and string comparison of ISO dates is correct on both."""
    return (datetime.date.today() - datetime.timedelta(days=int(days))).isoformat()


def _scope(tenant_id, alias=""):
    """(where_fragment, params). tenant_id=None → whole deployment (operator view)."""
    a = (alias + ".") if alias else ""
    if tenant_id is None:
        return f"{a}day>=?", []
    return f"{a}tenant_id=? AND {a}day>=?", [tenant_id]


class AnalyticsRepository(BaseRepository):
    def record(self, tenant_id, user_id, ts, day, event_type, page, card_id, card_type, meta):
        self.con.execute(
            "INSERT INTO usage_events(tenant_id,user_id,ts,day,event_type,page,card_id,card_type,meta) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (tenant_id, user_id, ts, day, event_type, page, card_id, card_type, meta))

    def daily_summary(self, tenant_id, days):
        where, pre = _scope(tenant_id)
        rows = self.con.execute(
            "SELECT day,"
            " COUNT(DISTINCT user_id) AS active_users,"
            " SUM(CASE WHEN event_type='page_view'      THEN 1 ELSE 0 END) AS page_views,"
            " SUM(CASE WHEN event_type='insight_click'  THEN 1 ELSE 0 END) AS insight_clicks,"
            " SUM(CASE WHEN event_type='research'       THEN 1 ELSE 0 END) AS researched,"
            " SUM(CASE WHEN event_type='action_clickout' THEN 1 ELSE 0 END) AS action_clickouts "
            f"FROM usage_events WHERE {where} "
            "GROUP BY day ORDER BY day",
            (*pre, _since(days))).fetchall()
        return [dict(r) for r in rows]

    def totals(self, tenant_id, days):
        where, pre = _scope(tenant_id)
        return self.con.execute(
            "SELECT COUNT(DISTINCT user_id) AS active_users,"
            " SUM(CASE WHEN event_type='page_view'       THEN 1 ELSE 0 END) AS page_views,"
            " SUM(CASE WHEN event_type='insight_click'   THEN 1 ELSE 0 END) AS insight_clicks,"
            " SUM(CASE WHEN event_type='research'        THEN 1 ELSE 0 END) AS researched,"
            " SUM(CASE WHEN event_type='action_clickout' THEN 1 ELSE 0 END) AS action_clickouts,"
            " COUNT(*) AS events "
            f"FROM usage_events WHERE {where}",
            (*pre, _since(days))).fetchone()

    def top_users(self, tenant_id, days, limit):
        where, pre = _scope(tenant_id, alias="e")
        rows = self.con.execute(
            "SELECT e.user_id AS user_id, COALESCE(u.email,'(unknown)') AS email,"
            " COUNT(*) AS events,"
            " SUM(CASE WHEN e.event_type='page_view'       THEN 1 ELSE 0 END) AS page_views,"
            " SUM(CASE WHEN e.event_type='insight_click'   THEN 1 ELSE 0 END) AS insight_clicks,"
            " SUM(CASE WHEN e.event_type='research'        THEN 1 ELSE 0 END) AS researched,"
            " SUM(CASE WHEN e.event_type='action_clickout' THEN 1 ELSE 0 END) AS action_clickouts,"
            " MAX(e.ts) AS last_seen "
            "FROM usage_events e LEFT JOIN users u ON u.id=e.user_id "
            f"WHERE {where} "
            "GROUP BY e.user_id, u.email ORDER BY events DESC LIMIT ?",
            (*pre, _since(days), int(limit))).fetchall()
        return [dict(r) for r in rows]

    def last_activity(self, tenant_id):
        return self.con.execute(
            "SELECT MAX(day) m FROM usage_events WHERE tenant_id=?", (tenant_id,)).fetchone()["m"]


class SystemRepository(BaseRepository):
    """Deployment-wide diagnostics for the operator console (global, not tenant-scoped)."""
    _COUNTABLE = ("tenants", "users", "cards", "seller_skus", "invites")

    def entity_counts(self):
        return {t: self.con.execute(f"SELECT COUNT(*) c FROM {t}").fetchone()["c"]
                for t in self._COUNTABLE}
