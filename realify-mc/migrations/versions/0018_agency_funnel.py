"""agency funnel: intake -> review -> provision (Postgres-only) — agency-plan P2

No-op on SQLite. Adds the funnel tables + an agency-level append-only ops audit, and plan/billing
columns on agencies. None are brand-scoped (they are agency/ops-level, not per-brand), so no RLS —
brand-scoped mutations keep the P1 hash-chained brand ledger; agency/ops events use agency_audit.

Revision ID: 0018_agency_funnel
Revises: 0017_tenant_is_internal
"""
from alembic import op

revision = "0018_agency_funnel"
down_revision = "0017_tenant_is_internal"
branch_labels = None
depends_on = None

APP_ROLE = "realify_app"

_DDL = r"""
CREATE TABLE IF NOT EXISTS agency_requests (
  id bigserial PRIMARY KEY,
  ref text UNIQUE NOT NULL,
  agency_name text NOT NULL,
  contact_name text,
  contact_email text NOT NULL,
  hq_country text NOT NULL,                       -- US | IN
  am_headcount integer,
  reporting_hours text,
  status text NOT NULL DEFAULT 'received',        -- received|in_review|approved|declined|provisioning|live
  agency_id uuid REFERENCES agencies(id),
  decline_reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS agency_invites (
  id bigserial PRIMARY KEY,
  agency_id uuid NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  email text NOT NULL,
  role text NOT NULL DEFAULT 'agency_admin',
  token_hash text NOT NULL,
  expires_at timestamptz NOT NULL,
  used boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS agency_provision_steps (
  request_id bigint NOT NULL REFERENCES agency_requests(id) ON DELETE CASCADE,
  step text NOT NULL,
  status text NOT NULL DEFAULT 'pending',         -- pending|done|failed
  error text,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (request_id, step)
);
CREATE TABLE IF NOT EXISTS agency_audit (
  id bigserial PRIMARY KEY,
  ts timestamptz NOT NULL DEFAULT now(),
  actor text,
  action text NOT NULL,
  agency_id uuid,
  tenant_id bigint,
  detail jsonb,
  reason text
);
CREATE INDEX IF NOT EXISTS ix_agency_audit_tenant ON agency_audit(tenant_id);
ALTER TABLE agencies ADD COLUMN IF NOT EXISTS plan_params jsonb;
ALTER TABLE agencies ADD COLUMN IF NOT EXISTS billing_status text;
"""


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(_DDL)
    op.execute(
        f"DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='{APP_ROLE}') THEN "
        f"  GRANT SELECT, INSERT, UPDATE, DELETE ON agency_requests, agency_invites, "
        f"    agency_provision_steps, agency_audit TO {APP_ROLE}; "
        f"  GRANT USAGE, SELECT ON SEQUENCE agency_requests_id_seq, agency_invites_id_seq, "
        f"    agency_audit_id_seq TO {APP_ROLE}; "
        f"END IF; END $$;")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for t in ["agency_provision_steps", "agency_invites", "agency_audit", "agency_requests"]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    op.execute("ALTER TABLE agencies DROP COLUMN IF EXISTS plan_params")
    op.execute("ALTER TABLE agencies DROP COLUMN IF EXISTS billing_status")
