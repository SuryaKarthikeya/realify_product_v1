"""agencies.owner_user_id — the founding admin who OWNS the agency and may manage its team (invite +
remove teammates). Everyone else is a plain agency_admin who sees + operates all brands but cannot manage
the roster. Backfilled to the earliest agency_members row per agency (the founder). PG-only, additive —
no change to the FORCE-RLS table count (agencies is not brand-scoped).

Revision ID: 0038_agency_owner
Revises: 0037_engagements_member_selfread
"""
from alembic import op

revision = "0038_agency_owner"
down_revision = "0037_engagements_member_selfread"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TABLE agencies ADD COLUMN IF NOT EXISTS owner_user_id bigint "
               "REFERENCES users(id) ON DELETE SET NULL")
    # backfill: the founding owner is the earliest member of each agency
    op.execute("""
        UPDATE agencies a SET owner_user_id = m.user_id
        FROM (SELECT DISTINCT ON (agency_id) agency_id, user_id
              FROM agency_members ORDER BY agency_id, created_at, user_id) m
        WHERE m.agency_id = a.id AND a.owner_user_id IS NULL
    """)


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE agencies DROP COLUMN IF EXISTS owner_user_id")
