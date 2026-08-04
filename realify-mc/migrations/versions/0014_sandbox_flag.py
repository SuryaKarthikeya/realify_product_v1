"""sandbox flag on tenants — marks seeded sandbox brand-tenants (P0.5)

Additive, inspector-guarded, safe on fresh and existing DBs (SQLite + Postgres). Sandbox tenants are
excluded from aggregates/billing/metrics in P7; for now the column just lets the canary seed tag its
36 brands and lets tests scope to them. Legacy `tenants` keeps app-layer tenant filtering (agency-plan
§1c: RLS retrofit on legacy tables is backlog AGY-RLS-RETROFIT, out of scope for P1-P7).

Revision ID: 0014_sandbox_flag
Revises: 0013_deleted_account_audit
"""
from alembic import op
import sqlalchemy as sa

revision = "0014_sandbox_flag"
down_revision = "0013_deleted_account_audit"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "tenants" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("tenants")}
    if "sandbox" not in cols:
        op.add_column("tenants", sa.Column("sandbox", sa.Integer(), server_default="0"))


def downgrade():
    pass
