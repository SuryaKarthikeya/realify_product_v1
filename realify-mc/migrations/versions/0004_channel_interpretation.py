"""1b.5: account-level interpretation rules + pending confirmations + provisional_units.

account_interpretation  — per-account confirmed rules (channel/marketplace treatment, COGS basis,
                          attribution window) that override registry defaults.
pending_confirmations   — ambiguities detected on ingest, filed with a best-guess default and the
                          impact at stake, for the seller to confirm/correct once.
seller_skus.provisional_units — units on an unresolved (unknown) marketplace, held out of Amazon
                          metrics and surfaced as 'provisional' until the channel is confirmed.

Additive and idempotent (inspector-guarded).

Revision ID: 0004_channel_interpretation
Revises: 0003_sku_provenance
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_channel_interpretation"
down_revision = "0003_sku_provenance"
branch_labels = None
depends_on = None


def _missing(insp, table, col):
    return col not in [c["name"] for c in insp.get_columns(table)]


def upgrade():
    insp = sa.inspect(op.get_bind())
    if _missing(insp, "seller_skus", "provisional_units"):
        op.add_column("seller_skus", sa.Column("provisional_units", sa.INTEGER()))
    if "account_interpretation" not in insp.get_table_names():
        op.create_table(
            "account_interpretation",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("category", sa.TEXT(), nullable=False),   # channel_map | cogs_basis | attribution_window
            sa.Column("key", sa.TEXT(), nullable=False),        # e.g. the marketplace string
            sa.Column("value", sa.TEXT()),                      # e.g. off_amazon_mcf
            sa.Column("confidence", sa.TEXT()),                 # seller | default
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "category", "key"),
        )
    if "pending_confirmations" not in insp.get_table_names():
        op.create_table(
            "pending_confirmations",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("ckey", sa.TEXT(), nullable=False),       # stable dedup key, e.g. channel_map:<mp>
            sa.Column("kind", sa.TEXT()),                       # channel_map | cogs_gt_price | ...
            sa.Column("title", sa.TEXT()),
            sa.Column("detail", sa.TEXT()),
            sa.Column("suggested", sa.TEXT()),                  # best-guess default treatment/value
            sa.Column("impact_units", sa.REAL()),
            sa.Column("impact_amount", sa.REAL()),
            sa.Column("status", sa.TEXT(), server_default="pending"),   # pending | confirmed | dismissed
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "ckey"),
        )


def downgrade():
    pass
