"""1b: sku_field_provenance table + seller_skus columns (replacement_units, lifecycle_flag, margin_floor)

Additive and idempotent (inspector-guarded), safe on fresh and existing DBs. `seller_skus` stays the
value-of-record; provenance records where each field came from (basis/source) and the estimate
alternate, so the SKU tab can show actual-vs-estimated and honor sticky seller edits.

Revision ID: 0003_sku_provenance
Revises: 0002_ensure_columns
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_sku_provenance"
down_revision = "0002_ensure_columns"
branch_labels = None
depends_on = None


def _missing(insp, table, col):
    return col not in [c["name"] for c in insp.get_columns(table)]


def upgrade():
    insp = sa.inspect(op.get_bind())
    if _missing(insp, "seller_skus", "replacement_units"):
        op.add_column("seller_skus", sa.Column("replacement_units", sa.INTEGER()))
    if _missing(insp, "seller_skus", "lifecycle_flag"):
        op.add_column("seller_skus", sa.Column("lifecycle_flag", sa.TEXT()))
    if _missing(insp, "seller_skus", "margin_floor"):
        op.add_column("seller_skus", sa.Column("margin_floor", sa.REAL()))
    if _missing(insp, "seller_skus", "mcf_units"):
        op.add_column("seller_skus", sa.Column("mcf_units", sa.INTEGER()))
    if "sku_field_provenance" not in insp.get_table_names():
        op.create_table(
            "sku_field_provenance",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("internal_sku", sa.TEXT(), nullable=False),
            sa.Column("field", sa.TEXT(), nullable=False),
            sa.Column("basis", sa.TEXT(), nullable=False),   # seller | actual | reported | estimated
            sa.Column("source", sa.TEXT()),                  # originating report type
            sa.Column("value", sa.TEXT()),                   # value for THIS basis (esp. the estimate alternate)
            sa.Column("edited", sa.INTEGER(), server_default="0"),
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "internal_sku", "field", "basis"),
        )


def downgrade():
    pass
