"""Membership-based engagements selfread: let an agency team MEMBER read their agency's engagements
under the runtime role even with NO per-brand grant. The grant-based selfread (0027) keyed engagement
visibility to a grant (id IN grants WHERE user_id=actor), so a fresh agency admin — membership only, no
grant — read their OWN book back EMPTY under realify_app: empty fleet + /agency/data-sources 403 the
moment they onboarded a brand. This permissive SELECT policy ORs in, keyed to the SAME app.actor_user_id
GUC that resolve_actor sets (fail-closed when the GUC is unset). agency_members carries no tenant_id, so
it is not brand-RLS-scoped and is readable inside the policy subquery.

Postgres-only (agency tables), idempotent. Does NOT change the FORCE-RLS table count.

Revision ID: 0037_engagements_member_selfread
Revises: 0036_deletion_lifecycle
"""
from alembic import op

revision = "0037_engagements_member_selfread"
down_revision = "0036_deletion_lifecycle"
branch_labels = None
depends_on = None

_ACTOR = "NULLIF(current_setting('app.actor_user_id', true),'')::bigint"


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP POLICY IF EXISTS engagements_member_selfread ON engagements")
    op.execute("CREATE POLICY engagements_member_selfread ON engagements FOR SELECT "
               f"USING (agency_id IN (SELECT agency_id FROM agency_members WHERE user_id = {_ACTOR}))")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS engagements_member_selfread ON engagements")
