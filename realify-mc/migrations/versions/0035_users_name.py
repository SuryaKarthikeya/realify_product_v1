"""R9.1: a display name on users so agency members / brand owners render as real people ("Sarah
Mitchell") instead of raw seed emails. Additive, BOTH engines (users exists on both).

Revision ID: 0035_users_name
Revises: 0034_saved_worlds
"""
from alembic import op
import sqlalchemy as sa

revision = "0035_users_name"
down_revision = "0034_saved_worlds"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("users")] if "users" in insp.get_table_names() else []
    if "users" in insp.get_table_names() and "name" not in cols:
        op.add_column("users", sa.Column("name", sa.String(), nullable=True))


def downgrade():
    pass
