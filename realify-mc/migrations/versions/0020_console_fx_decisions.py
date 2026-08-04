"""portfolio console: fx_rates, decisions, rollup_cache (Postgres-only) — agency-plan P4

No-op on SQLite. Money paths are integer minor units; fx_rates stores the locked rate as rate_ppm
(quote-per-USD × 1e6, an integer) and every cross-currency figure references an fx_rates row by id.

  fx_rates      — daily locked rates; global (no RLS)
  decisions     — rule-generated queue items; BRAND-SCOPED -> RLS
  rollup_cache  — materialized per-brand GMV/margin/TACoS (selling + USD); BRAND-SCOPED -> RLS

Revision ID: 0020_console_fx_decisions
Revises: 0019_brand_consent_connections
"""
from alembic import op

revision = "0020_console_fx_decisions"
down_revision = "0019_brand_consent_connections"
branch_labels = None
depends_on = None

APP_ROLE = "realify_app"
NEW_BRAND_SCOPED = ["decisions", "rollup_cache"]

_DDL = r"""
CREATE TABLE IF NOT EXISTS fx_rates (
  id bigserial PRIMARY KEY,
  as_of date NOT NULL,
  base text NOT NULL,                               -- 'USD'
  quote text NOT NULL,                              -- 'USD' | 'INR' | ...
  rate_ppm bigint NOT NULL,                         -- quote per 1 base, × 1_000_000 (integer)
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (as_of, base, quote)
);
CREATE TABLE IF NOT EXISTS decisions (
  id bigserial PRIMARY KEY,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  lens text NOT NULL,
  kind text NOT NULL,
  impact_minor bigint NOT NULL,                     -- selling-currency minor units
  impact_currency text NOT NULL,
  fx_rate_id bigint REFERENCES fx_rates(id),
  impact_usd_minor bigint NOT NULL,                 -- USD minor units (via the locked fx row)
  confidence integer NOT NULL DEFAULT 50,
  signal text,
  status text NOT NULL DEFAULT 'open',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_decisions_rank ON decisions(tenant_id, impact_usd_minor DESC);
CREATE TABLE IF NOT EXISTS rollup_cache (
  tenant_id bigint PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  currency text NOT NULL,
  fx_rate_id bigint REFERENCES fx_rates(id),
  gmv_minor bigint NOT NULL DEFAULT 0,
  gmv_usd_minor bigint NOT NULL DEFAULT 0,
  margin_minor bigint NOT NULL DEFAULT 0,
  margin_usd_minor bigint NOT NULL DEFAULT 0,
  tacos_bps integer NOT NULL DEFAULT 0,
  refreshed_at timestamptz NOT NULL DEFAULT now()
);
"""


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(_DDL)
    for t in NEW_BRAND_SCOPED:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS {t}_brand_isolation ON {t}")
        op.execute(f"CREATE POLICY {t}_brand_isolation ON {t} "
                   f"USING (tenant_id = ANY(current_brand_ids())) "
                   f"WITH CHECK (tenant_id = ANY(current_brand_ids()))")
    op.execute(
        f"DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='{APP_ROLE}') THEN "
        f"  GRANT SELECT, INSERT, UPDATE, DELETE ON fx_rates, decisions, rollup_cache TO {APP_ROLE}; "
        f"  GRANT USAGE, SELECT ON SEQUENCE fx_rates_id_seq, decisions_id_seq TO {APP_ROLE}; "
        f"END IF; END $$;")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for t in ["decisions", "rollup_cache", "fx_rates"]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
