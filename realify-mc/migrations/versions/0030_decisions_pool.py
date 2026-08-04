"""agency_subscriptions.decisions_pool — the pooled-Decisions allowance the billing page meters against
(burn projection + 85% warn). Postgres-only (agency table), additive.

Revision ID: 0030_decisions_pool
Revises: 0029_approval_deeplink_selfread
"""
from alembic import op

revision = "0030_decisions_pool"
down_revision = "0029_approval_deeplink_selfread"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE agency_subscriptions ADD COLUMN IF NOT EXISTS "
               "decisions_pool bigint NOT NULL DEFAULT 1000")


def downgrade():
    pass
