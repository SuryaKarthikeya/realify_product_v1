"""R9: tester-saved worlds (name + seed + params, owned by the tester) and a sandbox settings KV (the
email short-circuit toggle lives here). Additive, Postgres-only (sandbox lives on Postgres).

Revision ID: 0034_saved_worlds
Revises: 0033_agency_internal_flag
"""
from alembic import op
import sqlalchemy as sa

revision = "0034_saved_worlds"
down_revision = "0033_agency_internal_flag"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("""
        CREATE TABLE IF NOT EXISTS saved_worlds (
            id bigserial PRIMARY KEY,
            owner_email text NOT NULL,
            name text NOT NULL,
            seed text NOT NULL,
            country text NOT NULL,
            params jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (owner_email, name)
        )""")
    op.execute("""
        CREATE TABLE IF NOT EXISTS sandbox_settings (
            key text PRIMARY KEY,
            value text NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT now()
        )""")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON saved_worlds TO realify_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE saved_worlds_id_seq TO realify_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON sandbox_settings TO realify_app")


def downgrade():
    pass
