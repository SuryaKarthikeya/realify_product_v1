"""Workspace Brief: persist the real ₹ exposure figure on cards, not just the lossy
exposure_pct (20-95 index) and the pre-formatted exposure_val string ("₹18.8L"). materialize.py
already computes sig["exposure_inr"] for ranking (Phase 2 action-ranker) and discards it before
the card is written — this column lets the Brief sum real Opportunity $/At Risk $ instead of
re-parsing a formatted string. Additive, both engines.

Revision ID: 0042_card_exposure_inr
Revises: 0041_agents
"""
from alembic import op
import sqlalchemy as sa

revision = "0042_card_exposure_inr"
down_revision = "0041_agents"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "cards" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("cards")]
        if "exposure_inr" not in cols:
            op.add_column("cards", sa.Column("exposure_inr", sa.Float(), nullable=True))


def downgrade():
    pass
