"""agency console core: tenancy, IAM, ledger (Postgres-only) — agency-plan P1

POSTGRES-ONLY (§1c-2): the whole migration is a NO-OP on SQLite, so the existing SQLite suite is
untouched. On Postgres it adds the additive agency tables (referencing the existing users/tenants)
and turns on row-level security.

Tables (additive):
  agencies, agency_members            — the agency org + its staff (agency-scoped, not brand-scoped)
  engagements(agency_id, tenant_id)   — an agency operating one brand(=tenant); brand-scoped
  envelopes                           — versioned capability grant to an engagement (never updated in
                                        place — new version row each change); brand-scoped
  grants                              — a user's capability within an engagement; brand-scoped
  brand_keys(tenant_id, wrapped_dek)  — per-brand wrapped DEK for envelope encryption; brand-scoped
  ledger                              — append-only, per-brand hash chain; brand-scoped

RLS: every brand-scoped table (carries tenant_id) gets ENABLE + FORCE ROW LEVEL SECURITY with policy
`tenant_id = ANY(current_brand_ids())`. current_brand_ids() reads the transaction-local GUC
app.brand_ids (set per request via set_config(..., /*local*/ true) — pgbouncer-transaction-safe).
The app role is NOSUPERUSER + NOBYPASSRLS so the policy binds; FORCE makes it bind for the owner too.
Fail-closed: unset GUC -> empty array -> zero rows. Legacy tables keep app-layer tenant filtering
(RLS retrofit is backlog AGY-RLS-RETROFIT, §1c-3).

Revision ID: 0015_agency_core
Revises: 0014_sandbox_flag
"""
from alembic import op

revision = "0015_agency_core"
down_revision = "0014_sandbox_flag"
branch_labels = None
depends_on = None

APP_ROLE = "realify_app"
BRAND_SCOPED = ["engagements", "envelopes", "grants", "brand_keys", "ledger"]

_FUNC = r"""
CREATE OR REPLACE FUNCTION current_brand_ids() RETURNS bigint[]
LANGUAGE sql STABLE AS $$
  SELECT COALESCE(NULLIF(current_setting('app.brand_ids', true), ''), '{}')::bigint[]
$$;
"""

_TABLES = r"""
CREATE TABLE IF NOT EXISTS agencies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  hq_country text NOT NULL DEFAULT 'US',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS agency_members (
  agency_id uuid NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (agency_id, user_id)
);
CREATE TABLE IF NOT EXISTS engagements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id uuid NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'invited',          -- invited|active|paused|terminated
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (agency_id, tenant_id)
);
CREATE TABLE IF NOT EXISTS envelopes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  engagement_id uuid NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  version integer NOT NULL,
  caps jsonb NOT NULL DEFAULT '{}'::jsonb,
  ceilings jsonb NOT NULL DEFAULT '{}'::jsonb,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (engagement_id, version)
);
CREATE TABLE IF NOT EXISTS grants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  engagement_id uuid NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  role text NOT NULL,
  caps jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, engagement_id)
);
CREATE TABLE IF NOT EXISTS brand_keys (
  tenant_id bigint PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  wrapped_dek bytea,                                -- NULL after crypto-shred
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ledger (
  seq bigserial PRIMARY KEY,
  ts timestamptz NOT NULL DEFAULT now(),
  actor_user bigint REFERENCES users(id),
  tenant_id bigint NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  grant_id uuid,
  engagement_id uuid,
  envelope_version integer,
  action text NOT NULL,
  payload_enc bytea,
  prev_hash text,
  hash text NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ledger_brand_seq ON ledger(tenant_id, seq);
"""


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return                                       # agency tables are Postgres-only (§1c-2)
    op.execute(_FUNC)
    op.execute(_TABLES)
    for t in BRAND_SCOPED:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS {t}_brand_isolation ON {t}")
        op.execute(
            f"CREATE POLICY {t}_brand_isolation ON {t} "
            f"USING (tenant_id = ANY(current_brand_ids())) "
            f"WITH CHECK (tenant_id = ANY(current_brand_ids()))")
    # Grant the non-owner app role (created by the harness/prod bootstrap) DML on everything, but only
    # if it exists — keeps the migration safe on RDS/CI where the app role may be named differently.
    op.execute(
        f"DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname='{APP_ROLE}') THEN "
        f"  GRANT USAGE ON SCHEMA public TO {APP_ROLE}; "
        f"  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}; "
        f"  GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE}; "
        f"  GRANT EXECUTE ON FUNCTION current_brand_ids() TO {APP_ROLE}; "
        f"END IF; END $$;")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for t in reversed(BRAND_SCOPED):
        op.execute(f"DROP POLICY IF EXISTS {t}_brand_isolation ON {t}")
    for t in ["ledger", "brand_keys", "grants", "envelopes", "engagements", "agency_members", "agencies"]:
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    op.execute("DROP FUNCTION IF EXISTS current_brand_ids()")
