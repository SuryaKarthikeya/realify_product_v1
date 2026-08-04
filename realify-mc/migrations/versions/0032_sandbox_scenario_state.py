"""R6: sandbox scenario state — tag the sandbox agency + its tenants with the scenario key so a preset
reload is IDEMPOTENT (reuse the same tenant set, reset it to seed, never mint extras) and stray
singletons from the old per-click loader can be identified and cleaned. Additive, Postgres-only
(agencies/sandbox live on Postgres). tenant_kind already exists (0024) on both engines.

Revision ID: 0032_sandbox_scenario_state
Revises: 0031_intake_fields_and_resets
"""
from alembic import op
import sqlalchemy as sa

revision = "0032_sandbox_scenario_state"
down_revision = "0031_intake_fields_and_resets"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    insp = sa.inspect(bind)
    tables = insp.get_table_names()
    if "agencies" in tables:
        op.execute("ALTER TABLE agencies ADD COLUMN IF NOT EXISTS sandbox_scenario text")
        op.execute("ALTER TABLE agencies ADD COLUMN IF NOT EXISTS sandbox_loaded_at text")
    if "tenants" in tables:
        op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS sandbox_scenario text")


def downgrade():
    pass
