"""Step 2: period-aware advertising dimension.

ad_performance — advertising spend & attributed sales per SKU per period (month grain from the SP
Advertised-Product report today; the AdvertisedProductCollector will write the same shape from the
Amazon Ads API later). Separate from the seller_skus aggregate (ad_spend/ad_sales/tacos) which the
current cards still read; this table is what the CMAA tab and TACoS-over-time consume.

Additive and idempotent.

Revision ID: 0005_ad_performance
Revises: 0004_channel_interpretation
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_ad_performance"
down_revision = "0004_channel_interpretation"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "ad_performance" not in insp.get_table_names():
        op.create_table(
            "ad_performance",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("internal_sku", sa.TEXT(), nullable=False),
            sa.Column("period_start", sa.TEXT(), nullable=False),   # ISO date, first of month for month grain
            sa.Column("grain", sa.TEXT(), nullable=False),          # month | day
            sa.Column("spend", sa.REAL()),                          # reported (certain)
            sa.Column("sales", sa.REAL()),                          # attributed (estimated)
            sa.Column("source", sa.TEXT()),                         # sp_report_upload | ads_api
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "internal_sku", "period_start", "grain"),
        )


def downgrade():
    pass
