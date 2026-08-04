"""R17: the unified account-deletion lifecycle. Two additive tables on BOTH engines (self-serve delete
runs on the seller SQLite path; the ops close-out queue runs on the agency Postgres path; in prod they
share one RDS). Polymorphic + FK-free BY DESIGN — a deletion_request/captured_seed must OUTLIVE the rows
it describes (like deletion_ledger). No FK ⇒ safe on both engines.

Revision ID: 0036_deletion_lifecycle
Revises: 0035_users_name
"""
from alembic import op
import sqlalchemy as sa

revision = "0036_deletion_lifecycle"
down_revision = "0035_users_name"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if "deletion_requests" not in tables:
        op.create_table(
            "deletion_requests",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("entity_type", sa.String(), nullable=False),   # brand | user | agency
            sa.Column("entity_ref", sa.String(), nullable=False),    # tenant_id | user_id | agency_id (text; polymorphic, FK-free)
            sa.Column("label", sa.String()),                         # human display (brand/agency name) captured at request time
            sa.Column("requested_by", sa.String()),
            sa.Column("requested_at", sa.String()),                  # isoformat, app-set (portable across engines)
            sa.Column("status", sa.String(), nullable=False),        # requested | hold | ready | wiped | canceled
            sa.Column("account_type", sa.String()),                  # customer | tester | managed_brand | agency (routing hint)
            sa.Column("billing_settled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("override_reason", sa.String()),
            sa.Column("capture_seed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("reason", sa.String()),
            sa.Column("notes", sa.String()),
            sa.Column("executed_at", sa.String()),
        )
        op.create_index("ix_deletion_requests_status", "deletion_requests", ["status"])

    if "captured_seeds" not in tables:
        op.create_table(
            "captured_seeds",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("country", sa.String()),
            sa.Column("brand_name", sa.String()),                    # R17 decision 2 — the REAL name is kept
            sa.Column("sku_count", sa.Integer()),
            sa.Column("catalog", sa.JSON()),                         # minimal seed [{asin,title,category,cogs,price}]
            sa.Column("source_ref", sa.String()),                    # the tenant_id it was rescued from
            sa.Column("created_at", sa.String()),
        )

    # Postgres: the runtime role (realify_app, NOBYPASSRLS) needs DML + the PK sequences.
    if bind.dialect.name == "postgresql":
        for t in ("deletion_requests", "captured_seeds"):
            op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO realify_app")
            op.execute(f"GRANT USAGE, SELECT ON SEQUENCE {t}_id_seq TO realify_app")
        # R17 agency composite delete runs as realify_app in prod (the harness owner bypasses grants, so
        # missing grants would be a false-green that only surfaces live — R2/R11 lesson). Grant DELETE on
        # the agency row + its cascade children so `DELETE FROM agencies` (and FK-cascade) succeed live.
        for t in ("agencies", "agency_members", "engagements", "envelopes", "grants"):
            op.execute(f"GRANT DELETE ON {t} TO realify_app")


def downgrade():
    pass
