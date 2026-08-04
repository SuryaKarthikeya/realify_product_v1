"""sku_field_provenance — where each SKU field came from and the estimate alternate.

`seller_skus` holds the value-of-record; this table records, per (sku, field), one row per basis
(seller / actual / reported / estimated) with that basis's value, so the SKU tab can render the
actual-vs-estimated pair and honor sticky seller edits (a seller-edited field is not overwritten by
a re-uploaded report; the report's differing value is recorded, not silently applied).
"""
import datetime

from .base import BaseRepository


class ProvenanceRepository(BaseRepository):
    def set(self, tenant_id, sku, field, basis, source=None, value=None, edited=0):
        self.con.execute(
            "INSERT OR REPLACE INTO sku_field_provenance"
            "(tenant_id, internal_sku, field, basis, source, value, edited, updated_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (tenant_id, sku, field, basis, source,
             None if value is None else str(value), int(edited),
             datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")))

    def for_sku(self, tenant_id, sku):
        """-> {field: {basis: {source, value, edited}}}"""
        rows = self.con.execute(
            "SELECT field, basis, source, value, edited FROM sku_field_provenance "
            "WHERE tenant_id=? AND internal_sku=?", (tenant_id, sku)).fetchall()
        out = {}
        for r in rows:
            out.setdefault(r["field"], {})[r["basis"]] = {
                "source": r["source"], "value": r["value"], "edited": bool(r["edited"])}
        return out

    def all_for_tenant(self, tenant_id):
        rows = self.con.execute(
            "SELECT internal_sku, field, basis, source, value, edited FROM sku_field_provenance "
            "WHERE tenant_id=?", (tenant_id,)).fetchall()
        out = {}
        for r in rows:
            out.setdefault(r["internal_sku"], {}).setdefault(r["field"], {})[r["basis"]] = {
                "source": r["source"], "value": r["value"], "edited": bool(r["edited"])}
        return out

    def is_seller_edited(self, tenant_id, sku, field):
        r = self.con.execute(
            "SELECT edited FROM sku_field_provenance WHERE tenant_id=? AND internal_sku=? "
            "AND field=? AND basis='seller'", (tenant_id, sku, field)).fetchone()
        return bool(r and r["edited"])
