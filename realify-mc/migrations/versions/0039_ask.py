"""Ask surface (agent-shaped conversational home) — persistence for conversations, messages, per-message
feedback, marked follow-ups, and the monthly usage counter. Tenant-scoped seller data (isolated by
`WHERE tenant_id=?` like seller_skus/cards/ad_entity_perf), so NO RLS — only realify_app table grants.

Cross-dialect the same way as the baseline: the DDL is written in SQLite and translated to Postgres via
`dbengine.schema_to_postgres`, so a fresh SQLite test DB and an existing prod Postgres both get the tables.

Revision ID: 0039_ask
Revises: 0038_agency_owner
"""
from alembic import op

revision = "0039_ask"
down_revision = "0038_agency_owner"
branch_labels = None
depends_on = None

# SQLite DDL (single source of truth); TEXT uuid PKs (no sequences), TEXT for json/timestamps → valid PG too.
ASK_SCHEMA = """
CREATE TABLE IF NOT EXISTS ask_conversation(
  id TEXT PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  user_id INTEGER,
  title TEXT,
  model_id TEXT,
  created_at TEXT,
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_ask_conv_tenant ON ask_conversation(tenant_id, user_id, updated_at);

CREATE TABLE IF NOT EXISTS ask_message(
  id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  tenant_id INTEGER NOT NULL,
  role TEXT NOT NULL,                -- 'user' | 'assistant'
  content TEXT,                      -- plain-text rendering of the turn
  parts TEXT,                        -- JSON array of structured parts (tiles/actions/followups/citations)
  model_id TEXT,
  category TEXT,                     -- the Ask category chip, when the turn came from one
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_ask_msg_conv ON ask_message(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS ask_message_feedback(
  message_id TEXT PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  rating TEXT NOT NULL,             -- 'good' | 'bad'
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS ask_followup(
  id TEXT PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  user_id INTEGER,
  conversation_id TEXT,
  message_id TEXT,
  snippet TEXT,
  status TEXT DEFAULT 'open',       -- 'open' | 'done'
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_ask_followup_tenant ON ask_followup(tenant_id, status, created_at);

CREATE TABLE IF NOT EXISTS ask_usage(
  tenant_id INTEGER NOT NULL,
  period TEXT NOT NULL,             -- 'YYYY-MM'
  model_id TEXT NOT NULL,
  count INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT,
  PRIMARY KEY (tenant_id, period, model_id)
);
"""

_TABLES = ["ask_conversation", "ask_message", "ask_message_feedback", "ask_followup", "ask_usage"]


def upgrade():
    from realify import dbengine
    is_sqlite = op.get_bind().dialect.name == "sqlite"
    ddl = ASK_SCHEMA if is_sqlite else dbengine.schema_to_postgres(ASK_SCHEMA)
    for stmt in [s for s in ddl.split(";") if s.strip()]:
        op.execute(stmt)
    if not is_sqlite:
        for t in _TABLES:
            op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO realify_app")


def downgrade():
    for t in reversed(_TABLES):
        op.execute(f"DROP TABLE IF EXISTS {t}")
