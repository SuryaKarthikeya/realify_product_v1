"""approvals.viewed_at — records when the approver first opened the approval (mobile deep link / cockpit
row), so the cockpit can show a viewed/not-viewed signal (mockup screen 22). Postgres-only (approvals
is an agency table), additive, idempotent.

Revision ID: 0025_approval_viewed
Revises: 0024_tenant_kind
"""
from alembic import op

revision = "0025_approval_viewed"
down_revision = "0024_tenant_kind"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return                                   # approvals table exists only on Postgres
    op.execute("ALTER TABLE approvals ADD COLUMN IF NOT EXISTS viewed_at timestamptz")


def downgrade():
    pass
