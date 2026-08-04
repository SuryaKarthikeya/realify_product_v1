"""brand_keys.kek_fingerprint — a non-secret id of the KEK a brand DEK was wrapped under, so a key
wrapped by the WRONG KEK is caught with a clear error instead of a cryptic AEAD failure (the R2 live
incident: a one-shot without MASTER_KEK wrapped a key under the dev KEK). Lazy-backfilled on the next
successful unwrap. Postgres-only (brand_keys is an agency table), additive.

Revision ID: 0028_brand_key_kek_fingerprint
Revises: 0027_actor_selfread_rls
"""
from alembic import op

revision = "0028_brand_key_kek_fingerprint"
down_revision = "0027_actor_selfread_rls"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE brand_keys ADD COLUMN IF NOT EXISTS kek_fingerprint text")


def downgrade():
    pass
