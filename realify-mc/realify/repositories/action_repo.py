"""Task & pipeline outputs: actions_log / watchlist / sourcing_list / saved_briefs / runs.
SQL moved verbatim from tasks.py and pipeline/materialize.py (1b-2). Writes don't commit
EXCEPT where the original committed inline (noted per method) — preserved to keep behaviour
identical until the Postgres cutover centralizes transactions."""
from .base import BaseRepository
from .. import db


class ActionRepository(BaseRepository):
    # ---- actions_log ----
    def log_action(self, tenant_id, ts, card_id, card_type, task_type, title, summary,
                   explanation, mechanism, destination_url, payload):
        """Insert an explainability log row; returns its new id. (Caller commits.)"""
        return db.create_returning_id(
            self.con,
            "INSERT INTO actions_log(tenant_id,ts,card_id,card_type,task_type,title,summary,explanation,"
            "mechanism,destination_url,payload) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, ts, card_id, card_type, task_type, title, summary, explanation,
             mechanism, destination_url, payload))

    def recent(self, tenant_id, limit):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM actions_log WHERE tenant_id=? ORDER BY id DESC LIMIT ?",
            (tenant_id, limit)).fetchall()]

    def acted_cmaa_skus(self, tenant_id):
        """SKUs the seller has recorded a Profit & Ads Move on (card_id holds the SKU for these rows).
        Powers the decision→outcome loop: the CMAA tab badges these 'acted' so the state sticks."""
        return {r["card_id"] for r in self.con.execute(
            "SELECT DISTINCT card_id FROM actions_log WHERE tenant_id=? AND card_type=?",
            (tenant_id, "cmaa_sku")).fetchall() if r["card_id"] is not None}

    # ---- watchlist ----
    def add_watchlist(self, tenant_id, ts, card_id, kind, label, category, note):
        self.con.execute(
            "INSERT INTO watchlist(tenant_id,ts,card_id,kind,label,category,note) VALUES(?,?,?,?,?,?,?)",
            (tenant_id, ts, card_id, kind, label, category, note))

    def list_watchlist(self, tenant_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM watchlist WHERE tenant_id=? ORDER BY id DESC", (tenant_id,)).fetchall()]

    # ---- sourcing_list ----
    def add_sourcing(self, tenant_id, ts, source_card_id, segment, asin, title, brand,
                     price, bsr, reviews, rating, opp_score, note):
        self.con.execute(
            "INSERT OR IGNORE INTO sourcing_list(tenant_id,ts,source_card_id,segment,asin,title,brand,"
            "price,bsr,reviews,rating,opp_score,note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, ts, source_card_id, segment, asin, title, brand, price, bsr, reviews,
             rating, opp_score, note))

    def list_sourcing(self, tenant_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM sourcing_list WHERE tenant_id=? ORDER BY opp_score DESC",
            (tenant_id,)).fetchall()]

    # ---- saved_briefs ----
    def add_brief(self, tenant_id, ts, card_id, card_type, category, brief):
        self.con.execute(
            "INSERT INTO saved_briefs(tenant_id,ts,card_id,card_type,category,brief) VALUES(?,?,?,?,?,?)",
            (tenant_id, ts, card_id, card_type, category, brief))

    # ---- runs (pipeline run ledger) ----
    def start_run(self, tenant_id, started, status="running"):
        return db.create_returning_id(
            self.con, "INSERT INTO runs(tenant_id,started_at,status) VALUES(?,?,?)",
            (tenant_id, started, status))

    def finish_run(self, run_id, finished_at, cards_new, cards_updated, status="ok"):
        self.con.execute(
            "UPDATE runs SET finished_at=?,cards_new=?,cards_updated=?,status=? WHERE id=?",
            (finished_at, cards_new, cards_updated, status, run_id))
