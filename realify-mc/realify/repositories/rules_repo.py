"""Rules-as-data — the `rules` catalog (global) + `tenant_rule_settings` (per-tenant overrides).
SQL moved verbatim from rules.py / api.py / synth_conditions.py (workstream 1b).

Write methods do NOT commit — the caller owns the transaction (rules.py keeps its own commits)."""
from .. import db
from .base import BaseRepository


class RulesRepository(BaseRepository):
    # ---------- rules catalog ----------
    def upsert_rule(self, rule_id, name, description, family, card_type, tier, primitive,
                    inputs, params_default, editable_params, exposure_formula,
                    action_handler, severity_default, enabled_by_default):
        self.con.execute(
            """INSERT OR REPLACE INTO rules(rule_id,name,description,family,card_type,tier,primitive,
               inputs,params_default,editable_params,exposure_formula,action_handler,severity_default,enabled_by_default)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rule_id, name, description, family, card_type, tier, primitive, inputs,
             params_default, editable_params, exposure_formula, action_handler,
             severity_default, enabled_by_default))

    def all_rules(self):
        """{rule_id: row dict} for the whole catalog."""
        return {r["rule_id"]: dict(r) for r in self.con.execute("SELECT * FROM rules").fetchall()}

    def get_rule(self, rule_id):
        r = self.con.execute("SELECT * FROM rules WHERE rule_id=?", (rule_id,)).fetchone()
        return dict(r) if r else None

    def count_rules(self):
        return self.con.execute("SELECT COUNT(*) c FROM rules").fetchone()["c"]

    def surface_map_rows(self):
        """(rule_id, inputs, action_handler) for the read layer's surface map (api._surface_map)."""
        return [dict(r) for r in self.con.execute(
            "SELECT rule_id, inputs, action_handler FROM rules").fetchall()]

    # ---------- per-tenant overrides ----------
    def tenant_overrides(self, tenant_id):
        """{rule_id: override row dict} for a tenant."""
        return {r["rule_id"]: dict(r) for r in self.con.execute(
            "SELECT * FROM tenant_rule_settings WHERE tenant_id=?", (tenant_id,)).fetchall()}

    def upsert_override(self, tenant_id, rule_id, enabled, params, severity, updated_by="seller"):
        self.con.execute(
            """INSERT INTO tenant_rule_settings(tenant_id,rule_id,enabled,params,severity,updated_at,updated_by)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(tenant_id,rule_id) DO UPDATE SET enabled=excluded.enabled, params=excluded.params,
               severity=excluded.severity, updated_at=excluded.updated_at, updated_by=excluded.updated_by""",
            (tenant_id, rule_id, enabled, params, severity, db.now_iso(), updated_by))

    def delete_override(self, tenant_id, rule_id=None):
        if rule_id:
            self.con.execute(
                "DELETE FROM tenant_rule_settings WHERE tenant_id=? AND rule_id=?", (tenant_id, rule_id))
        else:
            self.con.execute(
                "DELETE FROM tenant_rule_settings WHERE tenant_id=?", (tenant_id,))
