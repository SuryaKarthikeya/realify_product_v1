"""Usage analytics — funnel events + daily aggregates. Internal/admin only.

Events are attributed server-side from the session (tenant_id, user_id); the client
never supplies identity. Recording is best-effort and must never break the request
path, so every write is wrapped and failures are swallowed.

Funnel: login (active user) -> page_view -> insight_click -> research -> action_clickout

SQL lives in AnalyticsRepository (workstream 1b-2); this module owns connection
lifecycle + the best-effort contract only.
"""
from . import db
from .repositories.analytics_repo import AnalyticsRepository

EVENTS = ("login", "page_view", "insight_click", "research", "action_clickout")


def record(tenant_id, user_id, event_type, page=None, card_id=None, card_type=None, meta=None):
    if event_type not in EVENTS or not tenant_id:
        return
    import json as _json
    con = db.connect()
    try:
        now = db.now_iso()
        AnalyticsRepository(con).record(
            tenant_id, user_id, now, now[:10], event_type, page,
            card_id if isinstance(card_id, int) else None, card_type,
            _json.dumps(meta) if meta else None)
        con.commit()
    except Exception:
        pass  # analytics must never break the request path
    finally:
        con.close()


def daily_summary(tenant_id=None, days=14):
    """One row per day in range, with the funnel counts and distinct active users.
    tenant_id=None aggregates across the whole deployment (all tenants)."""
    con = db.connect()
    try:
        return AnalyticsRepository(con).daily_summary(tenant_id, days)
    finally:
        con.close()


def totals(tenant_id=None, days=14):
    """Range totals for the KPI cards. active_users = distinct users over the whole range."""
    con = db.connect()
    try:
        r = AnalyticsRepository(con).totals(tenant_id, days)
        d = dict(r) if r else {}
        for k in ("active_users", "page_views", "insight_clicks", "researched", "action_clickouts", "events"):
            d[k] = d.get(k) or 0
        return d
    finally:
        con.close()


def top_users(tenant_id=None, days=14, limit=10):
    """Top users by total events in range, with their funnel breakdown."""
    con = db.connect()
    try:
        return AnalyticsRepository(con).top_users(tenant_id, days, limit)
    finally:
        con.close()
