"""tenant_kind on tenants — a single, legible classifier replacing the overloaded is_internal flag.

tenant_kind ∈ {seller, agency_workspace, internal, sandbox}, default 'seller'. Aggregates / ops
counters / drift now read tenant_kind (exclude kind <> 'seller' wherever they excluded is_internal).
is_internal is KEPT and written in sync (deprecated, not dropped) for backward-compat.

Backfill (order matters — sandbox before internal): sandbox orgs -> 'sandbox'; remaining is_internal
testers -> 'internal'; agency-admin login tenants are written 'agency_workspace' going forward (none are
historically distinguishable from 'internal', so they backfill as 'internal' — acceptable, prod had
none at R1). Additive, inspector-guarded, safe on SQLite + Postgres.

Revision ID: 0024_tenant_kind
Revises: 0023_admin_superlogin_gates
"""
from alembic import op
import sqlalchemy as sa

revision = "0024_tenant_kind"
down_revision = "0023_admin_superlogin_gates"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "tenants" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("tenants")}
    if "tenant_kind" not in cols:
        op.add_column("tenants", sa.Column("tenant_kind", sa.String(),
                                           server_default="seller", nullable=False))
    # Backfill from the legacy flags (sandbox first so an is_internal+sandbox row lands as 'sandbox').
    op.execute("UPDATE tenants SET tenant_kind='sandbox' WHERE COALESCE(sandbox,0)=1")
    op.execute("UPDATE tenants SET tenant_kind='internal' WHERE is_internal AND tenant_kind='seller'")


def downgrade():
    pass
