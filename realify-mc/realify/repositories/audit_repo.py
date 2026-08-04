"""Admin audit — a persistent, append-only record of fully-deleted accounts. NOT tenant-scoped (it must
outlive the tenant it describes; key column is `deleted_tenant_id`, never `tenant_id`). Plain INSERT
(append-only), so no ON CONFLICT key is registered."""
import datetime

from .base import BaseRepository


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


class DeletedAccountAuditRepository(BaseRepository):
    def record(self, deleted_tenant_id, tenant_name, account_type, emails,
               member_count, sku_count, card_count, deleted_by):
        self.con.execute(
            "INSERT INTO deleted_account_audit"
            "(deleted_tenant_id, tenant_name, account_type, emails, member_count, sku_count,"
            " card_count, deleted_by, deleted_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (deleted_tenant_id, tenant_name, account_type, emails, member_count, sku_count,
             card_count, deleted_by, _now()))
        self.con.commit()

    def list_all(self, limit=200):
        return [dict(r) for r in self.con.execute(
            "SELECT * FROM deleted_account_audit ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()]
