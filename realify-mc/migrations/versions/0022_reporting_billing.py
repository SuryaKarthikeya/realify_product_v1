"""reporting, billing (Stripe test mode), pilot conversion (Postgres-only) — agency-plan P6

No-op on SQLite. Brand-scoped (RLS): metering_events, invoice_lines. Agency/global (no RLS):
invoices, agency_subscriptions, suppression_list (email), agency_pilots. Adds hardened approval
deep-link columns. Billing math is integer minor units; Stripe is TEST MODE only + mockable.

Revision ID: 0022_reporting_billing
Revises: 0021_approvals_execution
"""
from alembic import op

revision = "0022_reporting_billing"
down_revision = "0021_approvals_execution"
branch_labels = None
depends_on = None

APP_ROLE = "realify_app"
NEW_BRAND_SCOPED = ["metering_events", "invoice_lines"]

_DDL = r"""
CREATE TABLE IF NOT EXISTS metering_events (
  id bigserial PRIMARY KEY,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  approval_id bigint,
  execution_id bigint,
  event_type text NOT NULL DEFAULT 'decision.executed',
  qty integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_metering_tenant ON metering_events(tenant_id, created_at);
CREATE TABLE IF NOT EXISTS invoices (
  id bigserial PRIMARY KEY,
  agency_id uuid REFERENCES agencies(id) ON DELETE CASCADE,
  period_start date, period_end date,
  currency text NOT NULL DEFAULT 'USD',
  usage_usd_minor bigint NOT NULL DEFAULT 0,
  base_usd_minor bigint NOT NULL DEFAULT 0,
  total_usd_minor bigint NOT NULL DEFAULT 0,
  inr_reference_minor bigint,
  fx_rate_id bigint REFERENCES fx_rates(id),
  net_terms_days integer NOT NULL DEFAULT 30,
  status text NOT NULL DEFAULT 'open',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS invoice_lines (
  id bigserial PRIMARY KEY,
  invoice_id bigint NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  qty integer NOT NULL DEFAULT 0,
  usage_usd_minor bigint NOT NULL DEFAULT 0,
  base_usd_minor bigint NOT NULL DEFAULT 0,
  total_usd_minor bigint NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS agency_subscriptions (
  agency_id uuid PRIMARY KEY REFERENCES agencies(id) ON DELETE CASCADE,
  stripe_customer_id text, stripe_subscription_id text,
  per_account_price_minor bigint NOT NULL DEFAULT 0,
  platform_fee_minor bigint NOT NULL DEFAULT 0,
  usage_unit_price_minor bigint NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'trialing',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS suppression_list (
  email text PRIMARY KEY,
  reason text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS agency_pilots (
  agency_id uuid PRIMARY KEY REFERENCES agencies(id) ON DELETE CASCADE,
  started_at timestamptz NOT NULL DEFAULT now(),
  signed_at timestamptz,
  terms_version text,
  read_only boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS deeplink_token_hash text;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS deeplink_user_id bigint;
ALTER TABLE approvals ADD COLUMN IF NOT EXISTS deeplink_expires_at timestamptz;
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
        f"  GRANT SELECT, INSERT, UPDATE, DELETE ON metering_events, invoices, invoice_lines, "
        f"    agency_subscriptions, suppression_list, agency_pilots TO {APP_ROLE}; "
        f"  GRANT USAGE, SELECT ON SEQUENCE metering_events_id_seq, invoices_id_seq, invoice_lines_id_seq "
        f"    TO {APP_ROLE}; "
        f"END IF; END $$;")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for t in ["metering_events", "invoice_lines", "invoices", "agency_subscriptions",
              "suppression_list", "agency_pilots"]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    for col in ["deeplink_token_hash", "deeplink_user_id", "deeplink_expires_at"]:
        op.execute(f"ALTER TABLE approvals DROP COLUMN IF EXISTS {col}")
