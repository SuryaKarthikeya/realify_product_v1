"""ensure post-baseline columns: cards.rank_score, tenants.account_type

Ported from init_db's old PRAGMA-guarded ALTERs, made dialect-agnostic via the SQLAlchemy
inspector so it is safe on a fresh DB and on a legacy DB that already has the columns.

Revision ID: 0002_ensure_columns
Revises: 0001_baseline
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_ensure_columns"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def _missing(insp, table, col):
    return col not in [c["name"] for c in insp.get_columns(table)]


def upgrade():
    insp = sa.inspect(op.get_bind())
    if _missing(insp, "cards", "rank_score"):
        op.add_column("cards", sa.Column("rank_score", sa.REAL(), server_default="0"))
    if _missing(insp, "tenants", "account_type"):
        op.add_column("tenants", sa.Column("account_type", sa.TEXT()))


def downgrade():
    pass
