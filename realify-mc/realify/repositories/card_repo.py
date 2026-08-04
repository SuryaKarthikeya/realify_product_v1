"""Card / feed READ path — tenant-scoped reads of materialized cards + cached research.
SQL moved verbatim from realify/api.py (workstream 1b).

Scope note: this is the READ path only. Card *materialization* (the dynamic INSERT/dedup
logic in pipeline/materialize.py) and card *actions* (status writes in tasks.py) are a
separate context, migrated in a later 1b increment.
"""
from .. import db
from .base import BaseRepository


class CardRepository(BaseRepository):
    # ---- feed ----
    def feed(self, tenant_id, category=None, family=None, new_only=False):
        """Non-dismissed cards for a tenant, with optional category/family/new filters.
        Returns raw row dicts; presentation (surface mapping, sort) stays in the read layer."""
        q = "SELECT * FROM cards WHERE tenant_id=? AND status!='dismissed'"
        args = [tenant_id]
        if category and category != "all":
            q += " AND category=?"; args.append(category)
        if family and family != "all":
            q += " AND family=?"; args.append(family)
        if new_only:
            q += " AND is_new=1"
        return [dict(r) for r in self.con.execute(q, args).fetchall()]

    def get(self, tenant_id, card_id):
        r = self.con.execute(
            "SELECT * FROM cards WHERE id=? AND tenant_id=?", (card_id, tenant_id)
        ).fetchone()
        return dict(r) if r else None

    # ---- briefing counts ----
    def _count(self, where, params):
        return self.con.execute(
            f"SELECT COUNT(*) n FROM cards WHERE {where}", params
        ).fetchone()["n"]

    def count_open(self, tenant_id):
        return self._count("tenant_id=? AND status!='dismissed'", (tenant_id,))

    def count_new(self, tenant_id):
        return self._count("tenant_id=? AND is_new=1", (tenant_id,))

    def count_action(self, tenant_id):
        return self._count("tenant_id=? AND severity IN('act','crit')", (tenant_id,))

    def count_opportunity(self, tenant_id):
        return self._count("tenant_id=? AND severity='opp'", (tenant_id,))

    def count_new_in_category(self, tenant_id, category):
        return self._count("tenant_id=? AND category=? AND is_new=1", (tenant_id, category))

    def count_alerts_in_category(self, tenant_id, category):
        return self._count("tenant_id=? AND category=? AND severity IN('act','crit')", (tenant_id, category))

    # ---- cached research payload (L2 trace) ----
    def research_payload(self, tenant_id, dedup_key):
        r = self.con.execute(
            "SELECT payload FROM card_research WHERE tenant_id=? AND dedup_key=?",
            (tenant_id, dedup_key),
        ).fetchone()
        return r["payload"] if r else None

    # ---- counts used outside the feed/briefing ----
    def count_all(self, tenant_id):
        return self._count("tenant_id=?", (tenant_id,))

    def count_distinct_types(self, tenant_id):
        """Distinct non-dismissed card_type count (rule-coverage measure)."""
        return self.con.execute(
            "SELECT COUNT(DISTINCT card_type) c FROM cards WHERE tenant_id=? AND status!='dismissed'",
            (tenant_id,),
        ).fetchone()["c"]

    def sum_exposure_inr(self, tenant_id, severities, exclude_card_types=()):
        """Real Sum(exposure_inr) over open (non-dismissed/done) cards matching `severities`,
        excluding fabricated-exposure card types (caller passes api.FABRICATED_EXPOSURE) — never
        sum a hard-coded constant as if it were a computed figure. NULL exposure_inr (cards
        materialized before the column existed, not yet re-run) is excluded by SUM itself."""
        if not severities:
            return 0.0
        sev_qs = ",".join("?" * len(severities))
        q = (f"SELECT COALESCE(SUM(exposure_inr),0) v FROM cards "
             f"WHERE tenant_id=? AND status NOT IN('dismissed','done') AND severity IN({sev_qs})")
        args = [tenant_id, *severities]
        if exclude_card_types:
            q += f" AND card_type NOT IN({','.join('?' * len(exclude_card_types))})"
            args += list(exclude_card_types)
        return self.con.execute(q, args).fetchone()["v"]

    def count_distinct_skus(self, tenant_id):
        """Distinct ASIN count over open (non-dismissed/done) cards — the "# SKUs" Brief tile."""
        return self.con.execute(
            "SELECT COUNT(DISTINCT asin) c FROM cards "
            "WHERE tenant_id=? AND status NOT IN('dismissed','done') AND asin IS NOT NULL",
            (tenant_id,),
        ).fetchone()["c"]

    # ---- WRITE / materialization path ----
    # These methods do NOT commit: the caller (the pipeline run, an action handler) owns the
    # transaction, preserving the single-commit materialization behavior. (Contrast with the
    # settings/pull repos, whose methods commit per call to match their original db.py semantics.)
    def existing_dedup_keys(self, tenant_id):
        return {r["dedup_key"] for r in self.con.execute(
            "SELECT dedup_key FROM cards WHERE tenant_id=?", (tenant_id,)).fetchall()}

    def upsert(self, payload):
        """Insert-or-update one card by (tenant_id, dedup_key). `payload` is a column->value
        dict; dedup_key/tenant_id/created_at are preserved on update. No commit."""
        cols = ",".join(payload.keys())
        qs = ",".join("?" * len(payload))
        updates = ",".join(f"{k}=excluded.{k}" for k in payload if k not in ("dedup_key", "tenant_id", "created_at"))
        self.con.execute(
            f"INSERT INTO cards({cols}) VALUES({qs}) "
            f"ON CONFLICT(tenant_id,dedup_key) DO UPDATE SET {updates}",
            list(payload.values()),
        )

    def prune_stale(self, tenant_id, existing, produced):
        """Delete ACTIVE cards present before the run but not produced this run; preserve cards
        the seller dismissed/marked done so they don't resurrect. Returns count pruned. No commit."""
        pruned = 0
        for dk in existing:
            if dk in produced:
                continue
            cur = self.con.execute(
                "DELETE FROM cards WHERE tenant_id=? AND dedup_key=? AND status NOT IN('dismissed','done')",
                (tenant_id, dk),
            )
            pruned += cur.rowcount
        return pruned

    def set_status(self, tenant_id, card_id, status):
        """Set a card's status (e.g. 'dismissed' / 'done'). No commit — caller commits."""
        self.con.execute(
            "UPDATE cards SET status=? WHERE id=? AND tenant_id=?", (status, card_id, tenant_id))

    # ---- card_research (cached L2 / brief) ----
    def save_research(self, tenant_id, dedup_key, payload_json):
        """Cache the research payload for a card (insert-or-replace). No commit — caller commits."""
        self.con.execute(
            "INSERT OR REPLACE INTO card_research(tenant_id,dedup_key,payload,created_at) VALUES(?,?,?,?)",
            (tenant_id, dedup_key, payload_json, db.now_iso()))

    def clear_research(self, tenant_id):
        """Drop all cached research for a tenant (e.g. after catalog regen). No commit."""
        self.con.execute("DELETE FROM card_research WHERE tenant_id=?", (tenant_id,))

    # ---- added in 1b-2: card_why cache, previously inline in pipeline/research.py ----
    def why_cached(self, tenant_id, dedup_key):
        return self.con.execute(
            "SELECT why FROM card_why WHERE tenant_id=? AND dedup_key=?", (tenant_id, dedup_key)).fetchone()

    def save_why(self, tenant_id, dedup_key, why, created_at):
        self.con.execute(
            "INSERT OR REPLACE INTO card_why(tenant_id,dedup_key,why,created_at) VALUES(?,?,?,?)",
            (tenant_id, dedup_key, why, created_at))
