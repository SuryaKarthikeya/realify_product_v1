"""Add users.avatar (additive, nullable) — a small data-URL avatar set from Settings. Backward-compatible:
existing code never reads it, so this changes nothing until the V4 Settings surface uses it.

Revision ID: 0040_user_avatar
Revises: 0039_ask
"""
from alembic import op

revision = "0040_user_avatar"
down_revision = "0039_ask"
branch_labels = None
depends_on = None


def upgrade():
    # additive nullable column. Postgres supports IF NOT EXISTS (idempotent, transaction-safe);
    # SQLite doesn't, but this is a fresh migration so the column won't pre-exist there.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar TEXT")
    else:
        op.execute("ALTER TABLE users ADD COLUMN avatar TEXT")


def downgrade():
    pass
