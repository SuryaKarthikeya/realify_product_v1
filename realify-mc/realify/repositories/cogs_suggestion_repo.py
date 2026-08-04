"""COGS suggestion store (0009): model-estimated COGS per SKU + explanation.

This is model OUTPUT, kept separate from seller_skus so the deterministic cost facts stay
authoritative. `all()` feeds the Product Catalog drawer; `replace_all()` is called by the
estimator after ingest / cost changes.
"""
import datetime

from .base import BaseRepository


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class CogsSuggestionRepository(BaseRepository):
    def all(self, tenant_id):
        """{internal_sku: {value, confidence, basis}} for the tenant."""
        rows = self.con.execute(
            "SELECT internal_sku, value, confidence, basis FROM cogs_suggestions WHERE tenant_id=?",
            (tenant_id,)).fetchall()
        return {r["internal_sku"]: {"value": r["value"], "confidence": r["confidence"],
                                    "basis": r["basis"]} for r in rows}

    def upsert(self, tenant_id, internal_sku, value, confidence, basis):
        self.con.execute(
            "INSERT OR REPLACE INTO cogs_suggestions"
            "(tenant_id, internal_sku, value, confidence, basis, computed_at) VALUES(?,?,?,?,?,?)",
            (tenant_id, internal_sku, value, confidence, basis, _now()))

    def replace_all(self, tenant_id, suggestions):
        """suggestions: iterable of (internal_sku, value, confidence, basis)."""
        self.con.execute("DELETE FROM cogs_suggestions WHERE tenant_id=?", (tenant_id,))
        for sku, value, confidence, basis in suggestions:
            self.upsert(tenant_id, sku, value, confidence, basis)
