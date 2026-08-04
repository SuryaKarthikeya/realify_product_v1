"""Deep-link self-read on approvals: a co-signer who opened the emailed deep link can read THAT
approval (keyed by deeplink_user_id = the actor GUC), so the mobile co-sign works under RLS even though
the brand co-signer holds no agency grant (no role can bypass RLS in prod). Permissive SELECT policy,
OR'd with brand-isolation; fail-closed when the GUC is unset. Postgres-only, additive.

Revision ID: 0029_approval_deeplink_selfread
Revises: 0028_brand_key_kek_fingerprint
"""
from alembic import op

revision = "0029_approval_deeplink_selfread"
down_revision = "0028_brand_key_kek_fingerprint"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP POLICY IF EXISTS approvals_deeplink_selfread ON approvals")
    op.execute("CREATE POLICY approvals_deeplink_selfread ON approvals FOR SELECT "
               "USING (deeplink_user_id = NULLIF(current_setting('app.actor_user_id', true),'')::bigint)")


def downgrade():
    pass
