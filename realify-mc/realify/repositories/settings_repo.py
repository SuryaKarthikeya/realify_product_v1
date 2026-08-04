"""Per-tenant key/value settings. SQL moved verbatim from db.py (workstream 1b)."""
from .base import BaseRepository


class SettingsRepository(BaseRepository):
    def get(self, tenant_id, key, default=None):
        r = self.con.execute(
            "SELECT value FROM tenant_settings WHERE tenant_id=? AND key=?", (tenant_id, key)
        ).fetchone()
        return r["value"] if r else default

    def set(self, tenant_id, key, value):
        self.con.execute(
            """INSERT INTO tenant_settings(tenant_id,key,value) VALUES(?,?,?)
               ON CONFLICT(tenant_id,key) DO UPDATE SET value=excluded.value""",
            (tenant_id, key, str(value)),
        )
        self.con.commit()
