"""R5: restore the full intake field set on agency_requests (website, book_size, marketplaces,
ad_platforms, current_tool, target_start) — additive, PG-only (agency_requests is Postgres). Plus a
both-engines password_resets table for the seller sign-in reset flow (single-use, TTL, ledgered).

Revision ID: 0031_intake_fields_and_resets
Revises: 0030_decisions_pool
"""
from alembic import op
import sqlalchemy as sa

revision = "0031_intake_fields_and_resets"
down_revision = "0030_decisions_pool"
branch_labels = None
depends_on = None

_COLS = ["website", "book_size", "marketplaces", "ad_platforms", "current_tool", "target_start"]


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if bind.dialect.name == "postgresql" and "agency_requests" in insp.get_table_names():
        for c in _COLS:
            op.execute(f"ALTER TABLE agency_requests ADD COLUMN IF NOT EXISTS {c} text")
    # password_resets — both engines (users exist on both)
    if "password_resets" not in insp.get_table_names():
        op.create_table(
            "password_resets",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String, nullable=False),
            sa.Column("token_hash", sa.String, nullable=False),
            sa.Column("expires_at", sa.String, nullable=False),
            sa.Column("used", sa.Integer, nullable=False, server_default="0"),
            sa.Column("created_at", sa.String, server_default=""))
    if bind.dialect.name == "postgresql":
        op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON password_resets TO realify_app")
        op.execute("GRANT USAGE, SELECT ON SEQUENCE password_resets_id_seq TO realify_app")


def downgrade():
    pass
