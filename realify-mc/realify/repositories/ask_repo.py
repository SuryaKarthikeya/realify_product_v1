"""Ask-surface persistence (one bounded context: the conversational home).

Tenant-scoped like the other seller-data repositories — every method takes `tenant_id` explicitly and
every statement filters on it (no RLS on these tables; isolation is application-level, same as
seller_skus/cards). SQL lives only here. Upserts use explicit `ON CONFLICT` (portable across SQLite and
Postgres, and — unlike `INSERT OR REPLACE` — needs no entry in the dbengine rewrite registry).
"""
import datetime
import json
import uuid

from .base import BaseRepository


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _uid():
    return uuid.uuid4().hex


class AskRepository(BaseRepository):
    """Conversations + messages + feedback + follow-ups + monthly usage for the Ask surface."""

    # ---- conversations ----
    def create_conversation(self, tenant_id, user_id, model_id, title=None):
        cid = _uid()
        now = _now()
        self.con.execute(
            "INSERT INTO ask_conversation(id, tenant_id, user_id, title, model_id, created_at, updated_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (cid, tenant_id, user_id, title, model_id, now, now))
        return cid

    def touch_conversation(self, tenant_id, conversation_id, title=None):
        if title is not None:
            self.con.execute(
                "UPDATE ask_conversation SET updated_at=?, title=COALESCE(title, ?) "
                "WHERE id=? AND tenant_id=?", (_now(), title, conversation_id, tenant_id))
        else:
            self.con.execute("UPDATE ask_conversation SET updated_at=? WHERE id=? AND tenant_id=?",
                             (_now(), conversation_id, tenant_id))

    def conversation(self, tenant_id, conversation_id):
        r = self.con.execute(
            "SELECT id, tenant_id, user_id, title, model_id, created_at, updated_at "
            "FROM ask_conversation WHERE id=? AND tenant_id=?", (conversation_id, tenant_id)).fetchone()
        return dict(r) if r else None

    def conversations(self, tenant_id, user_id, limit=50):
        """Most-recent-first list for the History tab. Scoped to the asking user within the tenant."""
        rows = self.con.execute(
            "SELECT id, title, model_id, created_at, updated_at FROM ask_conversation "
            "WHERE tenant_id=? AND (user_id=? OR ? IS NULL) ORDER BY updated_at DESC LIMIT ?",
            (tenant_id, user_id, user_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def delete_conversation(self, tenant_id, conversation_id):
        """Hard-delete a conversation and its turns (tenant-scoped). Messages go first — `ask_message`
        has no FK cascade, so orphan rows would otherwise linger."""
        self.con.execute("DELETE FROM ask_message WHERE conversation_id=? AND tenant_id=?",
                         (conversation_id, tenant_id))
        self.con.execute("DELETE FROM ask_followup WHERE conversation_id=? AND tenant_id=?",
                         (conversation_id, tenant_id))
        self.con.execute("DELETE FROM ask_conversation WHERE id=? AND tenant_id=?",
                         (conversation_id, tenant_id))

    def rename_conversation(self, tenant_id, conversation_id, title):
        self.con.execute("UPDATE ask_conversation SET title=?, updated_at=? WHERE id=? AND tenant_id=?",
                         (title, _now(), conversation_id, tenant_id))

    # ---- messages ----
    def add_message(self, tenant_id, conversation_id, role, content, parts=None, model_id=None,
                    category=None, message_id=None):
        """`message_id` lets a caller pre-allocate the id — the streaming path announces it in its
        first SSE frame (so feedback/follow-up work immediately) and persists under it later."""
        mid = message_id or _uid()
        self.con.execute(
            "INSERT INTO ask_message(id, conversation_id, tenant_id, role, content, parts, model_id, "
            "category, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (mid, conversation_id, tenant_id, role, content,
             json.dumps(parts or []), model_id, category, _now()))
        return mid

    def messages(self, tenant_id, conversation_id):
        rows = self.con.execute(
            "SELECT id, role, content, parts, model_id, category, created_at FROM ask_message "
            "WHERE conversation_id=? AND tenant_id=? ORDER BY created_at ASC",
            (conversation_id, tenant_id)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["parts"] = json.loads(d.get("parts") or "[]")
            except Exception:
                d["parts"] = []
            out.append(d)
        return out

    def history_for_model(self, tenant_id, conversation_id):
        """Role/content pairs (oldest first) — the transcript a real model receives as prior context."""
        return [{"role": m["role"], "content": m["content"] or ""}
                for m in self.messages(tenant_id, conversation_id)]

    # ---- feedback ----
    def set_feedback(self, tenant_id, message_id, rating):
        self.con.execute(
            "INSERT INTO ask_message_feedback(message_id, tenant_id, rating, created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(message_id) DO UPDATE SET rating=excluded.rating, created_at=excluded.created_at",
            (message_id, tenant_id, rating, _now()))

    def feedback(self, tenant_id, message_id):
        r = self.con.execute("SELECT rating FROM ask_message_feedback WHERE message_id=? AND tenant_id=?",
                             (message_id, tenant_id)).fetchone()
        return r["rating"] if r else None

    # ---- follow-ups ----
    def add_followup(self, tenant_id, user_id, conversation_id, message_id, snippet):
        fid = _uid()
        self.con.execute(
            "INSERT INTO ask_followup(id, tenant_id, user_id, conversation_id, message_id, snippet, "
            "status, created_at) VALUES(?,?,?,?,?,?,'open',?)",
            (fid, tenant_id, user_id, conversation_id, message_id, snippet, _now()))
        return fid

    def followups(self, tenant_id, status="open", limit=100):
        rows = self.con.execute(
            "SELECT id, conversation_id, message_id, snippet, status, created_at FROM ask_followup "
            "WHERE tenant_id=? AND (status=? OR ? IS NULL) ORDER BY created_at DESC LIMIT ?",
            (tenant_id, status, status, limit)).fetchall()
        return [dict(r) for r in rows]

    def set_followup_status(self, tenant_id, followup_id, status):
        self.con.execute("UPDATE ask_followup SET status=? WHERE id=? AND tenant_id=?",
                         (status, followup_id, tenant_id))

    # ---- usage (per tenant, per month, per model) ----
    def bump_usage(self, tenant_id, model_id, period=None):
        period = period or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")
        self.con.execute(
            "INSERT INTO ask_usage(tenant_id, period, model_id, count, updated_at) VALUES(?,?,?,1,?) "
            "ON CONFLICT(tenant_id, period, model_id) DO UPDATE SET count=ask_usage.count+1, "
            "updated_at=excluded.updated_at",
            (tenant_id, period, model_id, _now()))

    def usage(self, tenant_id, period=None):
        """{'total': int, 'by_model': {model_id: count}} for the given (default current) month."""
        period = period or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")
        rows = self.con.execute(
            "SELECT model_id, count FROM ask_usage WHERE tenant_id=? AND period=?",
            (tenant_id, period)).fetchall()
        by_model = {r["model_id"]: r["count"] for r in rows}
        return {"period": period, "total": sum(by_model.values()), "by_model": by_model}
