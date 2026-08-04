"""admin: persistent audit of fully-deleted accounts

When an operator deletes an account from the console, TenantRepository.delete wipes every tenant-scoped
row + the users + the tenant itself (freeing the email for a clean re-signup). This table is the ONE
record that must SURVIVE that wipe, so the operator can see what was deleted.

Deliberately NOT tenant-scoped: the key column is `deleted_tenant_id` (NOT `tenant_id`) so (a) the
wipe/delete teardown never touches it and (b) the dynamic orphan-guard in test_wipe_delete_coverage —
which keys off a literal `tenant_id` column — does not try to clear it. Append-only (plain INSERT).

Additive, inspector-guarded, safe on fresh + existing DBs (SQLite + Postgres).

Revision ID: 0013_deleted_account_audit
Revises: 0012_ad_entity_graph
"""
from alembic import op
import sqlalchemy as sa

revision = "0013_deleted_account_audit"
down_revision = "0012_ad_entity_graph"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "deleted_account_audit" in insp.get_table_names():
        return
    op.create_table(
        "deleted_account_audit",
        sa.Column("id", sa.INTEGER(), primary_key=True, autoincrement=True),
        sa.Column("deleted_tenant_id", sa.INTEGER()),   # historical reference to the removed tenant
        sa.Column("tenant_name", sa.TEXT()),
        sa.Column("account_type", sa.TEXT()),
        sa.Column("emails", sa.TEXT()),                 # comma-joined member emails, now freed for reuse
        sa.Column("member_count", sa.INTEGER()),
        sa.Column("sku_count", sa.INTEGER()),
        sa.Column("card_count", sa.INTEGER()),
        sa.Column("deleted_by", sa.TEXT()),
        sa.Column("deleted_at", sa.TEXT()),
    )


def downgrade():
    pass
