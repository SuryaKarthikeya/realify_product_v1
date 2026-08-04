"""Agents (the workforce) — additive, tenant-scoped seller data (isolated by WHERE tenant_id=?, no RLS,
same pattern as ask_* / seller_skus). Structure for: agents (specialists), their tasks, the hash-chained
Autonomy Ledger (decisions), and the pricing scope hierarchy (Category plane / Subcategory CPS / Item
state). The elasticity/pricing MATH is held for the RIA models — these tables hold the structure the
agent framework + Arbiter operate over. Cross-dialect via schema_to_postgres.

Revision ID: 0041_agents
Revises: 0040_user_avatar
"""
from alembic import op

revision = "0041_agents"
down_revision = "0040_user_avatar"
branch_labels = None
depends_on = None

AGENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent(
  id TEXT PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  specialist TEXT NOT NULL,            -- 'pricing' | 'discovery' | 'campaign' | 'fulfillment' | 'channel'
  name TEXT,
  status TEXT DEFAULT 'active',        -- 'active' | 'paused'
  autonomy TEXT DEFAULT 'observe',     -- observe | suggest | assist | act (per-agent default)
  autonomy_by_lens TEXT,               -- JSON {lens: level}
  guardrails TEXT,                     -- JSON list of {kind, params}
  scope TEXT,                          -- JSON {marketplaces, catalog:'all'|'category'|'selected', skus}
  created_at TEXT,
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_agent_tenant ON agent(tenant_id, status);

CREATE TABLE IF NOT EXISTS agent_task(
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  tenant_id INTEGER NOT NULL,
  name TEXT,
  clock TEXT,                          -- day | season | month | year (pricing) or ''
  cadence TEXT,                        -- realtime | hourly | daily | weekly | on_trigger
  autonomy TEXT DEFAULT 'observe',
  scope TEXT,
  next_run TEXT,
  status TEXT DEFAULT 'active',
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_agent_task ON agent_task(agent_id, status);

CREATE TABLE IF NOT EXISTS agent_decision(
  id TEXT PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  agent_id TEXT,
  task_id TEXT,
  seq INTEGER,                         -- per-tenant monotonically increasing (hash-chain order)
  signal TEXT,                         -- e.g. 'S1 competitor' | 'S5 in-stock'
  lens TEXT,                           -- Margin | Sales | Inventory | Ads
  target_sku TEXT,
  action TEXT,                         -- human line: "Held Dutch Oven at $79.99"
  detail TEXT,                         -- JSON: rationale, arbiter notes, projected value
  value_text TEXT,                     -- "+$312 / mo"
  confidence REAL,
  state TEXT,                          -- applied | awaiting | handoff | held
  reversible INTEGER DEFAULT 1,
  prev_hash TEXT,
  hash TEXT,
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_agent_decision ON agent_decision(tenant_id, seq);

-- pricing scope hierarchy (structure) policy inherits down, outcomes aggregate up
CREATE TABLE IF NOT EXISTS pricing_category_plane(
  tenant_id INTEGER NOT NULL, category TEXT NOT NULL,
  role TEXT, cm3_target REAL, markdown_budget REAL, markdown_used REAL DEFAULT 0,
  architecture TEXT, calendar TEXT, updated_at TEXT,
  PRIMARY KEY (tenant_id, category)
);
CREATE TABLE IF NOT EXISTS pricing_subcat_cps(
  tenant_id INTEGER NOT NULL, subcat TEXT NOT NULL,
  archetype TEXT, thresholds TEXT, str_curve TEXT, ladder_depths TEXT,
  cover_block_woc REAL, elasticity_class TEXT, parity_rule TEXT, floor_pct REAL, updated_at TEXT,
  PRIMARY KEY (tenant_id, subcat)
);
CREATE TABLE IF NOT EXISTS pricing_item_state(
  tenant_id INTEGER NOT NULL, sku TEXT NOT NULL, channel TEXT DEFAULT 'AMAZON',
  category TEXT, subcat TEXT, price REAL, lifecycle TEXT, woc REAL, str REAL,
  clock_context TEXT, budget_share REAL, override_json TEXT, updated_at TEXT,
  PRIMARY KEY (tenant_id, sku, channel)
);
"""

_TABLES = ["agent", "agent_task", "agent_decision",
           "pricing_category_plane", "pricing_subcat_cps", "pricing_item_state"]


def upgrade():
    from realify import dbengine
    is_sqlite = op.get_bind().dialect.name == "sqlite"
    ddl = AGENTS_SCHEMA if is_sqlite else dbengine.schema_to_postgres(AGENTS_SCHEMA)
    for stmt in [s for s in ddl.split(";") if s.strip()]:
        op.execute(stmt)
    if not is_sqlite:
        for t in _TABLES:
            op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO realify_app")


def downgrade():
    for t in reversed(_TABLES):
        op.execute(f"DROP TABLE IF EXISTS {t}")
