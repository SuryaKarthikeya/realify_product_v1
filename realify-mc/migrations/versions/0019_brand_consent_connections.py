"""brand consent, connections, CSV ingest, deletion ledger (Postgres-only) — agency-plan P3

No-op on SQLite. Adds:
  brand_consents        — brand-consent flow (token+OTP accessed pre-engagement); agency-level, no RLS
  connections           — a brand's provider connections; BRAND-SCOPED -> RLS ENABLE+FORCE
  agency_ingest_rows    — CSV-ingested rows tagged source_class+currency; BRAND-SCOPED -> RLS
  report_column_mappings— remembered per-report-type column mapping (global config); no RLS
  deletion_ledger       — hash-chained tenant-deletion audit; NO tenant FK so it SURVIVES deletion

Revision ID: 0019_brand_consent_connections
Revises: 0018_agency_funnel
"""
from alembic import op

revision = "0019_brand_consent_connections"
down_revision = "0018_agency_funnel"
branch_labels = None
depends_on = None

APP_ROLE = "realify_app"
NEW_BRAND_SCOPED = ["connections", "agency_ingest_rows"]

_DDL = r"""
CREATE TABLE IF NOT EXISTS brand_consents (
  id bigserial PRIMARY KEY,
  agency_id uuid REFERENCES agencies(id) ON DELETE CASCADE,
  tenant_id bigint REFERENCES tenants(id) ON DELETE CASCADE,
  engagement_id uuid REFERENCES engagements(id) ON DELETE SET NULL,
  agency_name text,
  email text NOT NULL,
  token_hash text NOT NULL,
  status text NOT NULL DEFAULT 'invited',          -- invited|viewed|granted|countered|declined|expired
  envelope_template text,
  ceilings jsonb,
  counter jsonb,
  expires_at timestamptz NOT NULL,
  viewed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS connections (
  id bigserial PRIMARY KEY,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  provider text NOT NULL,                           -- amazon|shopify|amazon_ads|google_ads|meta_ads
  status text NOT NULL DEFAULT 'pending',           -- connected|pending|expired
  expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, provider)
);
CREATE TABLE IF NOT EXISTS agency_ingest_rows (
  id bigserial PRIMARY KEY,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  report_type text NOT NULL,
  source_class text NOT NULL,                        -- csv | api
  currency text,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS report_column_mappings (
  report_type text PRIMARY KEY,
  mapping jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS deletion_ledger (
  seq bigserial PRIMARY KEY,
  ts timestamptz NOT NULL DEFAULT now(),
  actor text,
  tenant_id bigint,                                  -- NO FK: must survive the tenant's deletion
  prev_hash text,
  hash text NOT NULL
);
"""


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(_DDL)
    for t in NEW_BRAND_SCOPED:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS {t}_brand_isolation ON {t}")
        op.execute(f"CREATE POLICY {t}_brand_isolation ON {t} "
                   f"USING (tenant_id = ANY(current_brand_ids())) "
                   f"WITH CHECK (tenant_id = ANY(current_brand_ids()))")
    op.execute(
        f"DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='{APP_ROLE}') THEN "
        f"  GRANT SELECT, INSERT, UPDATE, DELETE ON brand_consents, connections, agency_ingest_rows, "
        f"    report_column_mappings, deletion_ledger TO {APP_ROLE}; "
        f"  GRANT USAGE, SELECT ON SEQUENCE brand_consents_id_seq, connections_id_seq, "
        f"    agency_ingest_rows_id_seq, deletion_ledger_seq_seq TO {APP_ROLE}; "
        f"END IF; END $$;")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for t in ["brand_consents", "connections", "agency_ingest_rows", "report_column_mappings",
              "deletion_ledger"]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
