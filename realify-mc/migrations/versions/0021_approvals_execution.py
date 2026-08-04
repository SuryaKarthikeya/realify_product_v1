"""approvals & execution write path (Postgres-only) — agency-plan P5

No-op on SQLite. Adds approvals, executions (idempotency_key UNIQUE + pre_state for rollback),
brand_pause (pause-all flag) — all BRAND-SCOPED -> RLS ENABLE+FORCE. Adds the per-engagement
maker-checker threshold. Executions are against an IN-PROCESS mock marketplace only (no real API).

Revision ID: 0021_approvals_execution
Revises: 0020_console_fx_decisions
"""
from alembic import op

revision = "0021_approvals_execution"
down_revision = "0020_console_fx_decisions"
branch_labels = None
depends_on = None

APP_ROLE = "realify_app"
NEW_BRAND_SCOPED = ["approvals", "executions", "brand_pause"]

_DDL = r"""
ALTER TABLE engagements ADD COLUMN IF NOT EXISTS maker_checker_threshold_usd_minor bigint NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS approvals (
  id bigserial PRIMARY KEY,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  engagement_id uuid REFERENCES engagements(id) ON DELETE CASCADE,
  lens text NOT NULL,
  kind text NOT NULL,
  signal text,
  impact_usd_minor bigint NOT NULL DEFAULT 0,
  maker_user bigint,
  checker_user bigint,
  requires_cosign boolean NOT NULL DEFAULT false,
  status text NOT NULL DEFAULT 'proposed',          -- proposed|approved|cosign_pending|expired|rejected|executed|canceled
  cosign_expires_at timestamptz,
  nudge_count integer NOT NULL DEFAULT 0,
  escalated boolean NOT NULL DEFAULT false,
  envelope_version integer,
  context jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_approvals_status ON approvals(tenant_id, status);
CREATE TABLE IF NOT EXISTS executions (
  id bigserial PRIMARY KEY,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  approval_id bigint REFERENCES approvals(id) ON DELETE CASCADE,
  account text NOT NULL,
  idempotency_key text NOT NULL UNIQUE,             -- durable idempotency across crash/restart
  status text NOT NULL DEFAULT 'pending',           -- done|excluded|rolledback|halted
  excluded_reason text,
  pre_state jsonb,                                   -- snapshot for rollback
  result jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS brand_pause (
  tenant_id bigint PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  paused boolean NOT NULL DEFAULT false,
  reason text,
  updated_at timestamptz NOT NULL DEFAULT now()
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
        f"  GRANT SELECT, INSERT, UPDATE, DELETE ON approvals, executions, brand_pause TO {APP_ROLE}; "
        f"  GRANT USAGE, SELECT ON SEQUENCE approvals_id_seq, executions_id_seq TO {APP_ROLE}; "
        f"END IF; END $$;")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for t in ["executions", "approvals", "brand_pause"]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    op.execute("ALTER TABLE engagements DROP COLUMN IF EXISTS maker_checker_threshold_usd_minor")
