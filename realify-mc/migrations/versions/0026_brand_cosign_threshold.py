"""engagements.brand_cosign_threshold_usd_minor — the brand-cosign rule input (R2). Co-sign is required
when a change is high-stakes: a pricing-lens change, or an amount >= this threshold. 0 disables the
amount rule (pricing still always co-signs). Postgres-only (engagements is an agency table), additive.

Revision ID: 0026_brand_cosign_threshold
Revises: 0025_approval_viewed
"""
from alembic import op

revision = "0026_brand_cosign_threshold"
down_revision = "0025_approval_viewed"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE engagements ADD COLUMN IF NOT EXISTS "
               "brand_cosign_threshold_usd_minor bigint NOT NULL DEFAULT 0")


def downgrade():
    pass
