"""cross-channel onboarding: tenant_topology + sku_crosswalk

Two additive, tenant-scoped tables for the Shopify cross-channel onboarding (spec §5):
  * tenant_topology — the resolved TenantTopology (channels, fulfilment, Resolved<T> fields, reliability
    flags, completeness) persisted as a JSON blob (volatile/nested, like cards.provenance). One row per
    tenant; both the wizard and raw paths write it.
  * sku_crosswalk — (channel, store_id, external_sku, external_variant_id) -> canonical_sku_id
    (= internal_sku), so Amazon + Shopify unify at the SKU level. store_id/external_variant_id default
    to '' (not NULL) so the composite PK is well-defined on both engines.

Additive, inspector-guarded, safe on fresh and existing DBs.

Revision ID: 0010_topology
Revises: 0009_catalog_surface
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_topology"
down_revision = "0009_catalog_surface"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    tables = insp.get_table_names()
    if "tenant_topology" not in tables:
        op.create_table(
            "tenant_topology",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("schema_version", sa.INTEGER()),
            sa.Column("entry_path", sa.TEXT()),          # WIZARD | RAW
            sa.Column("topology", sa.TEXT()),            # JSON blob (see topology_model.TenantTopology)
            sa.Column("created_at", sa.TEXT()),
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id"),
        )
    if "sku_crosswalk" not in tables:
        op.create_table(
            "sku_crosswalk",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("channel", sa.TEXT(), nullable=False),
            sa.Column("store_id", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("external_sku", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("external_variant_id", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("canonical_sku_id", sa.TEXT()),    # = internal_sku (R4)
            sa.Column("status", sa.TEXT()),              # MAPPED | UNMAPPED | PARKED
            sa.Column("created_at", sa.TEXT()),
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "channel", "store_id", "external_sku", "external_variant_id"),
        )


def downgrade():
    pass
