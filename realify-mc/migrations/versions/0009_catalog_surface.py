"""catalog surface: seller_skus.optimize_for + cogs_suggestions (model output)

Two additive changes for the Product Catalog surface:
  * seller_skus.optimize_for — the seller's per-SKU strategy choice (Cash Flow / Margin / Growth).
    Stored intent only; it does not (yet) change engine behavior.
  * cogs_suggestions — model-estimated COGS per SKU with an explanation. This is MODEL OUTPUT and
    lives in its own table, never inside seller_skus, so the deterministic facts L1 detectors read
    stay untouched (see realify/models.py principles). Recomputed whenever reports are ingested or a
    SKU's cost inputs change.

Additive, inspector-guarded, safe on fresh and existing DBs.

Revision ID: 0009_catalog_surface
Revises: 0008_ingested_reports
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_catalog_surface"
down_revision = "0008_ingested_reports"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("seller_skus")] if "seller_skus" in insp.get_table_names() else []
    if "seller_skus" in insp.get_table_names() and "optimize_for" not in cols:
        op.add_column("seller_skus", sa.Column("optimize_for", sa.TEXT()))
    if "cogs_suggestions" not in insp.get_table_names():
        op.create_table(
            "cogs_suggestions",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("internal_sku", sa.TEXT(), nullable=False),
            sa.Column("value", sa.REAL()),
            sa.Column("confidence", sa.TEXT()),
            sa.Column("basis", sa.TEXT()),
            sa.Column("computed_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "internal_sku"),
        )


def downgrade():
    pass
