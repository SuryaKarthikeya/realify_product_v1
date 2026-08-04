"""Account-interpretation + pending-confirmation repositories (1b.5).

The channel resolver is the load-bearing piece: given a marketplace string it returns the treatment
to apply, checking seller confirmations first, then the registry defaults. Ingestion uses one
resolver for orders AND refunds AND returns, so a channel is never counted on one side of a ratio
but not the other.
"""
import datetime

from .base import BaseRepository
from realify.ingest import marketplace_registry as reg


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class InterpretationRepository(BaseRepository):
    def set_rule(self, tenant_id, category, key, value, confidence="seller"):
        self.con.execute(
            "INSERT OR REPLACE INTO account_interpretation"
            "(tenant_id, category, key, value, confidence, updated_at) VALUES(?,?,?,?,?,?)",
            (tenant_id, category, key, value, confidence, _now()))

    def channel_map(self, tenant_id):
        """{marketplace: treatment} of seller-confirmed channel rules."""
        rows = self.con.execute(
            "SELECT key, value FROM account_interpretation WHERE tenant_id=? AND category='channel_map'",
            (tenant_id,)).fetchall()
        return {r["key"]: r["value"] for r in rows}

    def resolver(self, tenant_id):
        """Return a callable marketplace -> treatment: seller confirmation wins, else registry
        default (blank/missing marketplace -> amazon_direct)."""
        confirmed = self.channel_map(tenant_id)

        def resolve(marketplace):
            try:
                m = str(marketplace).strip().lower()
            except Exception:
                m = ""
            if m in confirmed:
                return confirmed[m]
            return reg.default_treatment(m)[0]
        return resolve

    def mappings_view(self, tenant_id):
        """For the registry UI: every marketplace rule with its source (seller-confirmed vs default)."""
        confirmed = self.channel_map(tenant_id)
        return confirmed


class ConfirmationRepository(BaseRepository):
    def upsert(self, tenant_id, ckey, kind, title, detail, suggested, impact_units=None, impact_amount=None):
        # don't clobber a resolved confirmation back to pending
        cur = self.con.execute(
            "SELECT status FROM pending_confirmations WHERE tenant_id=? AND ckey=?",
            (tenant_id, ckey)).fetchone()
        if cur and cur["status"] != "pending":
            return
        self.con.execute(
            "INSERT OR REPLACE INTO pending_confirmations"
            "(tenant_id, ckey, kind, title, detail, suggested, impact_units, impact_amount, status, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, ckey, kind, title, detail, suggested, impact_units, impact_amount, "pending", _now()))

    def pending(self, tenant_id):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM pending_confirmations WHERE tenant_id=? AND status='pending' "
            "ORDER BY impact_units DESC", (tenant_id,)).fetchall()]

    def resolve(self, tenant_id, ckey, status="confirmed"):
        self.con.execute(
            "UPDATE pending_confirmations SET status=?, updated_at=? WHERE tenant_id=? AND ckey=?",
            (status, _now(), tenant_id, ckey))
