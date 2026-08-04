"""Step 4: per-period settled revenue (for TACoS-over-time in the trust layer).

sku_revenue_period — Amazon-direct settled revenue & units per SKU per period (month grain), the
denominator TACoS needs (spend / total revenue) alongside ad_performance (spend / ad sales = ACoS).
Channel-scoped at ingest (Amazon-direct paid only), so it stays consistent with every other metric.

Additive and idempotent.

Revision ID: 0006_revenue_period
Revises: 0005_ad_performance
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_revenue_period"
down_revision = "0005_ad_performance"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "sku_revenue_period" not in insp.get_table_names():
        op.create_table(
            "sku_revenue_period",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("internal_sku", sa.TEXT(), nullable=False),
            sa.Column("period_start", sa.TEXT(), nullable=False),
            sa.Column("grain", sa.TEXT(), nullable=False),
            sa.Column("revenue", sa.REAL()),
            sa.Column("units", sa.INTEGER()),
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "internal_sku", "period_start", "grain"),
        )


def downgrade():
    pass
