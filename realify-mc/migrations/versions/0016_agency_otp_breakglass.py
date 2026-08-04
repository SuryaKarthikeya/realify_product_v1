"""agency OTP table + break-glass fields on grants (Postgres-only) — agency-plan P1

No-op on SQLite. Adds:
  * agency_otp — email-OTP codes (6-digit, 10-min TTL, single-use); not brand-scoped, no RLS.
  * grants.expires_at — NULL = permanent; set for time-boxed break-glass grants.
  * grants.break_glass — flags a temporary elevation grant.

Also re-grants DML on the NEW table to the app role (0015's blanket grant predated it).

Revision ID: 0016_agency_otp_breakglass
Revises: 0015_agency_core
"""
from alembic import op

revision = "0016_agency_otp_breakglass"
down_revision = "0015_agency_core"
branch_labels = None
depends_on = None

APP_ROLE = "realify_app"

_DDL = r"""
CREATE TABLE IF NOT EXISTS agency_otp (
  id bigserial PRIMARY KEY,
  email text NOT NULL,
  code_hash text NOT NULL,
  expires_at timestamptz NOT NULL,
  used boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_agency_otp_email ON agency_otp(email);
ALTER TABLE grants ADD COLUMN IF NOT EXISTS expires_at timestamptz;
ALTER TABLE grants ADD COLUMN IF NOT EXISTS break_glass boolean NOT NULL DEFAULT false;
"""


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(_DDL)
    op.execute(
        f"DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='{APP_ROLE}') THEN "
        f"  GRANT SELECT, INSERT, UPDATE, DELETE ON agency_otp TO {APP_ROLE}; "
        f"  GRANT USAGE, SELECT ON SEQUENCE agency_otp_id_seq TO {APP_ROLE}; "
        f"END IF; END $$;")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE grants DROP COLUMN IF EXISTS break_glass")
    op.execute("ALTER TABLE grants DROP COLUMN IF EXISTS expires_at")
    op.execute("DROP TABLE IF EXISTS agency_otp")
