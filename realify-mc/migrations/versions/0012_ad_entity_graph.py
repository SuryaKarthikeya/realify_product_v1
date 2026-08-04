"""attributable ads: campaign->SKU entity graph, search-term rows, ingest coverage summary

Part A of "Attributable CMAA + Prescriptive Fix-Ads". The existing ad_performance table (0005) aggregates
spend/sales to (SKU, period) and DISCARDS the campaign/ad-group columns — so there is no way to say "which
campaign is bleeding on this SKU". These three additive tables carry the missing grain:

  * ad_entity_perf — the campaign -> ad group -> advertised SKU/ASIN graph with spend/sales/clicks/orders
    per period. Keyed on Amazon entity names (CSV carries names, not IDs; Part B/API adds IDs under the
    same natural key). This is the raw material for per-SKU-per-campaign diagnosis.
  * ad_search_term — SP Search Term rows (campaign/ad group/targeting/customer search term + metrics).
    SKU linkage is via ad_entity_perf on (campaign, ad_group); the report itself is target-grained.
  * ad_ingest_summary — one row per tenant: coverage_pct + mapped/unmapped spend + fidelity + the
    AD_GRANULARITY_INSUFFICIENT flag, so the "attributable" claim is auditable and shown honestly in UI.

Additive, inspector-guarded, safe on fresh + existing DBs (SQLite + Postgres). Text key columns default
to '' so composite PKs are well-defined on both engines (same pattern as sku_crosswalk in 0010).

Revision ID: 0012_ad_entity_graph
Revises: 0011_subscriptions
"""
from alembic import op
import sqlalchemy as sa

revision = "0012_ad_entity_graph"
down_revision = "0011_subscriptions"
branch_labels = None
depends_on = None


def upgrade():
    insp = sa.inspect(op.get_bind())
    tables = insp.get_table_names()

    if "ad_entity_perf" not in tables:
        op.create_table(
            "ad_entity_perf",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("campaign", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("ad_group", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("advertised_asin", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("advertised_sku", sa.TEXT()),
            sa.Column("internal_sku", sa.TEXT()),         # resolved via ASIN->SKU; NULL = unmapped spend
            sa.Column("period_start", sa.TEXT(), nullable=False),   # ISO, first-of-month for month grain
            sa.Column("grain", sa.TEXT(), nullable=False, server_default="month"),
            sa.Column("spend", sa.REAL()),
            sa.Column("sales", sa.REAL()),
            sa.Column("clicks", sa.REAL()),
            sa.Column("orders", sa.REAL()),
            sa.Column("source", sa.TEXT()),               # sp_report_upload | ads_api
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "campaign", "ad_group", "advertised_asin",
                                    "period_start", "grain"),
        )
        op.create_index("idx_ad_entity_sku", "ad_entity_perf", ["tenant_id", "internal_sku"])

    if "ad_search_term" not in tables:
        op.create_table(
            "ad_search_term",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("campaign", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("ad_group", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("targeting", sa.TEXT()),
            sa.Column("match_type", sa.TEXT()),
            sa.Column("customer_search_term", sa.TEXT(), nullable=False, server_default=""),
            sa.Column("period_start", sa.TEXT(), nullable=False),
            sa.Column("grain", sa.TEXT(), nullable=False, server_default="month"),
            sa.Column("spend", sa.REAL()),
            sa.Column("sales", sa.REAL()),
            sa.Column("clicks", sa.REAL()),
            sa.Column("orders", sa.REAL()),
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id", "campaign", "ad_group", "customer_search_term",
                                    "period_start", "grain"),
        )
        op.create_index("idx_ad_st_campaign", "ad_search_term", ["tenant_id", "campaign", "ad_group"])

    if "ad_ingest_summary" not in tables:
        op.create_table(
            "ad_ingest_summary",
            sa.Column("tenant_id", sa.INTEGER(), nullable=False),
            sa.Column("coverage_pct", sa.REAL()),         # % of ad spend mapped to a known SKU
            sa.Column("mapped_spend", sa.REAL()),
            sa.Column("unmapped_spend", sa.REAL()),
            sa.Column("fidelity", sa.TEXT()),             # KEYWORD | CAMPAIGN_SKU | CHANNEL_ONLY
            sa.Column("granularity_flag", sa.TEXT()),     # e.g. AD_GRANULARITY_INSUFFICIENT | NULL
            sa.Column("has_advertised_product", sa.INTEGER()),
            sa.Column("has_search_term", sa.INTEGER()),
            sa.Column("has_campaign_only", sa.INTEGER()),
            sa.Column("updated_at", sa.TEXT()),
            sa.PrimaryKeyConstraint("tenant_id"),
        )


def downgrade():
    pass
