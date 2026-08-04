"""Actor-bootstrap RLS: let a user read THEIR OWN grants (and the engagements those grants reference)
without bypassing RLS — needed because no runtime role has BYPASSRLS (realify_app AND realify_admin are
both NOSUPERUSER/NOBYPASSRLS). resolve_actor set a transaction-local GUC app.actor_user_id; these
permissive SELECT policies OR with the existing brand-isolation policy, so nothing brand-scoped is
widened (the self-read is keyed to the actor's own user_id, fail-closed when the GUC is unset).

Postgres-only (agency tables), idempotent. Does not change the FORCE-RLS table count.

Revision ID: 0027_actor_selfread_rls
Revises: 0026_brand_cosign_threshold
"""
from alembic import op

revision = "0027_actor_selfread_rls"
down_revision = "0026_brand_cosign_threshold"
branch_labels = None
depends_on = None

_ACTOR = "NULLIF(current_setting('app.actor_user_id', true),'')::bigint"


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP POLICY IF EXISTS grants_actor_selfread ON grants")
    op.execute(f"CREATE POLICY grants_actor_selfread ON grants FOR SELECT USING (user_id = {_ACTOR})")
    op.execute("DROP POLICY IF EXISTS engagements_actor_selfread ON engagements")
    op.execute("CREATE POLICY engagements_actor_selfread ON engagements FOR SELECT "
               f"USING (id IN (SELECT engagement_id FROM grants WHERE user_id = {_ACTOR}))")


def downgrade():
    pass
