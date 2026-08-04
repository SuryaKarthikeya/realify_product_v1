"""Tenancy: organizations, provisioning state, account type, full-org deletion.

A tenant IS an organization (see #003). SQL moved verbatim from db.py (1b) — behavior is
unchanged; db.py now delegates here so existing callers are unaffected.
"""
from .. import db
from .base import BaseRepository


class TenantRepository(BaseRepository):
    def create(self, name):
        new_id = db.create_returning_id(
            self.con,
            "INSERT INTO tenants(name,created_at,provisioned) VALUES(?,?,0)",
            (name, db.now_iso()))
        self.con.commit()
        return new_id

    def get(self, tenant_id):
        r = self.con.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,)).fetchone()
        return dict(r) if r else None

    def set_provisioned(self, tenant_id, mode):
        self.con.execute(
            "UPDATE tenants SET provisioned=1, data_mode=? WHERE id=?", (mode, tenant_id)
        )
        self.con.commit()

    def get_account_type(self, tenant_id):
        """'tester' | 'customer' | None (not yet chosen)."""
        r = self.con.execute(
            "SELECT account_type FROM tenants WHERE id=?", (tenant_id,)
        ).fetchone()
        return (dict(r).get("account_type") if r else None) or None

    def set_account_type(self, tenant_id, account_type):
        """Settable freely until provisioned; LOCKED once provisioned. Returns False if the
        type is invalid, or if the tenant is provisioned and the requested type differs."""
        if account_type not in ("tester", "customer"):
            return False
        t = self.get(tenant_id)
        provisioned = bool(t and t["provisioned"])
        cur = self.get_account_type(tenant_id)
        if provisioned and cur and cur != account_type:
            return False
        self.con.execute(
            "UPDATE tenants SET account_type=? WHERE id=?", (account_type, tenant_id)
        )
        self.con.commit()
        return True

    # ---- Stripe subscription (0011) — the tenant is the billing entity ----
    _SUB_COLS = ("stripe_customer_id", "stripe_subscription_id", "subscription_status",
                 "trial_ends_at", "current_period_end")

    def set_stripe_customer(self, tenant_id, customer_id):
        self.con.execute("UPDATE tenants SET stripe_customer_id=? WHERE id=?", (customer_id, tenant_id))
        self.con.commit()

    def set_subscription(self, tenant_id, **fields):
        """Update only the subscription columns passed as keyword args (None values are written too,
        so a handler can explicitly clear a field). Unknown keys are ignored."""
        cols = [(k, v) for k, v in fields.items() if k in self._SUB_COLS]
        if not cols:
            return
        setclause = ", ".join(f"{k}=?" for k, _ in cols)
        self.con.execute(f"UPDATE tenants SET {setclause} WHERE id=?",
                         tuple(v for _, v in cols) + (tenant_id,))
        self.con.commit()

    def get_by_stripe_customer(self, customer_id):
        if not customer_id:
            return None
        r = self.con.execute("SELECT * FROM tenants WHERE stripe_customer_id=?", (customer_id,)).fetchone()
        return dict(r) if r else None

    def get_by_stripe_subscription(self, subscription_id):
        if not subscription_id:
            return None
        r = self.con.execute("SELECT * FROM tenants WHERE stripe_subscription_id=?", (subscription_id,)).fetchone()
        return dict(r) if r else None

    def delete(self, tenant_id):
        """Full organization delete: every tenant-scoped row across all tables, plus invites,
        usage_events, member users, and the tenant row — one transaction. Frees the email(s)."""
        for t in db.TENANT_DATA_TABLES:
            self.con.execute(f"DELETE FROM {t} WHERE tenant_id=?", (tenant_id,))
        # config / transient / confirmed-decision tables: preserved on a data reload, but a full
        # account delete must remove them too (nothing tenant-scoped may survive).
        for t in ("account_interpretation", "tenant_settings", "channels", "channel_economics",
                  "jobs", "usage_events", "invites", "users"):
            self.con.execute(f"DELETE FROM {t} WHERE tenant_id=?", (tenant_id,))
        self.con.execute("DELETE FROM tenants WHERE id=?", (tenant_id,))
        self.con.commit()
        # P3 rider: additive hash-chained deletion ledger (any delete path). PG-only, best-effort —
        # never alters delete semantics; no-op on SQLite so the existing flow/tests are unchanged.
        from ..agency import deletion
        deletion.on_tenant_deleted(tenant_id)

    # ---- added in 1b-2: tenants reads previously inline in scheduler.py / run.py ----
    def list_provisioned_ids(self):
        return [r["id"] for r in self.con.execute(
            "SELECT id FROM tenants WHERE provisioned=1").fetchall()]

    def list_all(self):
        return [dict(r) for r in self.con.execute(
            "SELECT id,name,account_type,provisioned,data_mode,created_at FROM tenants ORDER BY id").fetchall()]

    def reset_provisioning(self, tenant_id):
        self.con.execute(
            "UPDATE tenants SET provisioned=0, data_mode=NULL WHERE id=?", (tenant_id,))
