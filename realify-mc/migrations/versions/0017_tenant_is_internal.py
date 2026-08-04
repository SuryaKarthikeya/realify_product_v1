"""is_internal flag on tenants — internal testers/Realify users: full access, never billed, excluded
from aggregates/metrics (updated agency plan).

Additive, inspector-guarded, safe on SQLite + Postgres. Distinct from `data_mode` (data source:
synthetic|uploaded) and from `sandbox` (0014, seeded canary brands). Column only here; the initial
prod backfill (tag existing non-Stripe tenants internal) is done as an explicit one-time data op, not
baked into the migration, so it never mislabels tenants on other databases.

Revision ID: 0017_tenant_is_internal
Revises: 0016_agency_otp_breakglass
"""
from alembic import op
import sqlalchemy as sa

revision = "0017_tenant_is_internal"
down_revision = "0016_agency_otp_breakglass"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "tenants" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("tenants")}
    if "is_internal" not in cols:
        op.add_column("tenants", sa.Column("is_internal", sa.Boolean(),
                                           server_default=sa.false(), nullable=False))


def downgrade():
    pass
