"""internal admin, quality console, superlogin hardening (agency-plan P7 — FINAL)

superlogin_* tables are created on BOTH engines (superlogin is on the main app, SQLite + Postgres);
none are brand-scoped, so no RLS and the brand-scoped RLS count stays 14. `gates` (attestation engine)
is Postgres-only (agency admin console).

Revision ID: 0023_admin_superlogin_gates
Revises: 0022_reporting_billing
"""
from alembic import op
import sqlalchemy as sa

revision = "0023_admin_superlogin_gates"
down_revision = "0022_reporting_billing"
branch_labels = None
depends_on = None

APP_ROLE = "realify_app"


def _has(insp, name):
    return name in insp.get_table_names()


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    # ---- superlogin hardening (both engines) ----
    if not _has(insp, "superlogin_sessions"):
        op.create_table(
            "superlogin_sessions",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.Text, nullable=False),
            sa.Column("ip", sa.Text),
            sa.Column("created_at", sa.Text),
            sa.Column("expires_at", sa.Text))
    if not _has(insp, "superlogin_lockout"):
        op.create_table(
            "superlogin_lockout",
            sa.Column("email", sa.Text, primary_key=True),
            sa.Column("fails", sa.Integer, nullable=False, server_default="0"),
            sa.Column("locked_until", sa.Text))
    if not _has(insp, "superlogin_otp"):
        op.create_table(
            "superlogin_otp",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.Text, nullable=False),
            sa.Column("code_hash", sa.Text, nullable=False),
            sa.Column("expires_at", sa.Text, nullable=False),
            sa.Column("used", sa.Integer, nullable=False, server_default="0"))

    if bind.dialect.name != "postgresql":
        return
    # ---- gates / attestation engine (Postgres-only) ----
    op.execute(r"""
    CREATE TABLE IF NOT EXISTS gates (
      id bigserial PRIMARY KEY,
      gate_key text NOT NULL,
      scope text NOT NULL DEFAULT 'platform',          -- platform | agency
      provenance text NOT NULL,                         -- auto | attested
      status text NOT NULL DEFAULT 'active',            -- active | EXPIRED
      evidence_link text,
      valid_from timestamptz NOT NULL DEFAULT now(),
      valid_until timestamptz,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_gates_key ON gates(gate_key, created_at);
    """)
    op.execute(
        f"DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='{APP_ROLE}') THEN "
        f"  GRANT SELECT, INSERT, UPDATE, DELETE ON gates, superlogin_sessions, superlogin_lockout, "
        f"    superlogin_otp TO {APP_ROLE}; "
        f"  GRANT USAGE, SELECT ON SEQUENCE gates_id_seq, superlogin_sessions_id_seq, "
        f"    superlogin_otp_id_seq TO {APP_ROLE}; "
        f"END IF; END $$;")


def downgrade():
    for t in ["gates", "superlogin_otp", "superlogin_lockout", "superlogin_sessions"]:
        op.execute(f"DROP TABLE IF EXISTS {t}")
