"""seller-set title override: seller_skus.title_override

Lets a seller supply/correct a SKU title when the reports don't carry one (or carry a poor one).
Sticky against re-upload (seller-owned); display resolves `title_override or title`. The report's
own `title` still flows into the `title` column underneath, so clearing the override restores it.

Additive and idempotent (inspector-guarded), safe on fresh and existing DBs.

Revision ID: 0007_title_override
Revises: 0006_revenue_period
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_title_override"
down_revision = "0006_revenue_period"
branch_labels = None
depends_on = None


def _missing(insp, table, col):
    return col not in [c["name"] for c in insp.get_columns(table)]


def upgrade():
    insp = sa.inspect(op.get_bind())
    if _missing(insp, "seller_skus", "title_override"):
        op.add_column("seller_skus", sa.Column("title_override", sa.TEXT()))


def downgrade():
    pass
