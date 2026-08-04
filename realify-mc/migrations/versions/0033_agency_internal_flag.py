"""R7: reversible 'internal' flag on agencies so verification/sandbox agencies can be retired from the
fleet view without a hard delete (Part 0a) and excluded from /ops/agency/admin by default (Part 3a).
Additive, Postgres-only (agencies live on Postgres).

Revision ID: 0033_agency_internal_flag
Revises: 0032_sandbox_scenario_state
"""
from alembic import op
import sqlalchemy as sa

revision = "0033_agency_internal_flag"
down_revision = "0032_sandbox_scenario_state"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    if "agencies" in sa.inspect(bind).get_table_names():
        op.execute("ALTER TABLE agencies ADD COLUMN IF NOT EXISTS internal boolean NOT NULL DEFAULT false")


def downgrade():
    pass
