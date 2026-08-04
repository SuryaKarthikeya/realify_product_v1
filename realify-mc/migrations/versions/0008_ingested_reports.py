"""ingested report fingerprints: ingested_reports

Records a SHA-256 fingerprint of each *ingested* report table (parsed + normalized: sorted
columns, sorted rows, stringified cells) per tenant, so a byte-identical re-upload — even
re-exported with a different row/column order — is detected as a 100% duplicate and skipped
instead of re-ingested. Fingerprint identity only ever matches genuinely identical data (a
false positive would require a SHA-256 collision), so it never drops a distinct report.
Semantic overlap (same period, different numbers) is deliberately NOT handled here — that
stays with the existing report_overlap confirmation flow, which can't be judged fool-proof.

Additive and idempotent (inspector-guarded), safe on fresh and existing DBs.

Revision ID: 0008_ingested_reports
Revises: 0007_title_override
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_ingested_reports"
down_revision = "0007_title_override"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    if "ingested_reports" not in insp.get_table_names():
        op.create_table(
            "ingested_reports",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("content_hash", sa.TEXT(), nullable=False),
            sa.Column("report_type", sa.TEXT()),
            sa.Column("filename", sa.TEXT()),
            sa.Column("ingested_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "content_hash"),
        )


def downgrade():
    pass
