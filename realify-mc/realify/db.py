"""SQLite layer: schema (multi-tenant), connection, append-only snapshots, the
incremental 'pull_log' watermark machinery, and user/tenant identity.

MULTI-TENANCY: every data row carries tenant_id, and tenant_id ALWAYS comes from
the authenticated session — never from the client. Primary/unique keys that used
to be global (asin, dedup_key, order_id) now include tenant_id so two tenants can
hold the same ASIN without collision."""
import os, sqlite3, json, datetime as dt
from . import config

def now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

def connect():
    # Engine seam (#005 1c): Postgres goes through the dbengine wrapper; SQLite is unchanged.
    from . import dbengine
    if dbengine.dialect() == "postgresql":
        return dbengine.pg_connect()
    con = sqlite3.connect(config.DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)  # timeout=10: wait out the concurrent background-enrich writer instead of "database is locked"
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def create_returning_id(con, sql, params, pk="id"):
    """INSERT that returns the new row's auto-PK across dialects: SQLite uses cursor.lastrowid;
    Postgres appends `RETURNING <pk>` (lastrowid is unsupported there). The single place the app
    needs an inserted id (JobRepository.create) routes through here."""
    from . import dbengine
    if dbengine.dialect() == "postgresql":
        row = con.execute(sql.rstrip().rstrip(";") + f" RETURNING {pk}", params).fetchone()
        return row[pk] if row else None
    return con.execute(sql, params).lastrowid

SCHEMA = """
-- ===== identity / tenancy =====
CREATE TABLE IF NOT EXISTS tenants(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created_at TEXT,
  data_mode TEXT,            -- 'synthetic' | 'uploaded' | NULL (not yet provisioned)
  provisioned INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, email TEXT UNIQUE,
  pw_hash TEXT, pw_salt TEXT, created_at TEXT, role TEXT DEFAULT 'owner'
);

-- ===== own-seller data (synthetic now; report-ingested later) =====
CREATE TABLE IF NOT EXISTS seller_skus(
  tenant_id INTEGER, asin TEXT, title TEXT, category TEXT, ptype TEXT, amazon_cat TEXT,
  price REAL, cogs REAL, referral_fee REAL, fba_fee REAL, ad_cost_unit REAL,
  return_cost_unit REAL, net_profit_unit REAL, net_margin_pct REAL, breakeven_floor REAL,
  units_month INTEGER, units_year INTEGER, velocity_day REAL, annual_rev_inr REAL,
  rev_share_pct REAL, stock_on_hand INTEGER, days_of_cover REAL, buybox_pct INTEGER,
  tacos REAL, returns_rate REAL, rating REAL, review_count INTEGER,
  internal_sku TEXT, channel TEXT DEFAULT 'amazon',
  PRIMARY KEY(tenant_id, asin)
);

CREATE TABLE IF NOT EXISTS seller_orders(
  tenant_id INTEGER, order_id TEXT, asin TEXT, order_date TEXT, units INTEGER,
  gross REAL, referral_fee REAL, fba_fee REAL, expected_deposit REAL, actual_deposit REAL,
  settlement_date TEXT, delivered_date TEXT, has_review INTEGER, review_eligible INTEGER,
  status TEXT, channel TEXT DEFAULT 'amazon', internal_sku TEXT,
  PRIMARY KEY(tenant_id, order_id)
);
CREATE INDEX IF NOT EXISTS ix_orders_asin ON seller_orders(tenant_id, asin, order_date);

-- ===== incremental backbone (per tenant) =====
CREATE TABLE IF NOT EXISTS pull_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER,
  source TEXT NOT NULL, scope TEXT NOT NULL,
  started_at TEXT, finished_at TEXT, status TEXT, records INTEGER DEFAULT 0,
  window_from TEXT, window_to TEXT, note TEXT
);
CREATE INDEX IF NOT EXISTS ix_pull ON pull_log(tenant_id, source, scope, status, finished_at);

CREATE TABLE IF NOT EXISTS keepa_snapshots(
  tenant_id INTEGER, asin TEXT, captured_at TEXT, price REAL, bsr INTEGER, bsr_avg30 INTEGER,
  rating REAL, review_count INTEGER, offer_count INTEGER,
  buybox_price REAL, buybox_seller TEXT, raw TEXT,
  PRIMARY KEY(tenant_id, asin, captured_at)
);

CREATE TABLE IF NOT EXISTS competitor_offers(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER,
  asin TEXT, captured_at TEXT, seller TEXT, price REAL,
  is_buybox INTEGER, is_fba INTEGER, in_stock INTEGER, condition TEXT
);
CREATE INDEX IF NOT EXISTS ix_offer ON competitor_offers(tenant_id, asin, captured_at);

CREATE TABLE IF NOT EXISTS tierc_signals(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER,
  source TEXT, signal_type TEXT, captured_at TEXT, published_at TEXT,
  category TEXT, title TEXT, url TEXT, summary TEXT, confidence INTEGER, raw TEXT,
  dedup_key TEXT, UNIQUE(tenant_id, dedup_key)
);
CREATE INDEX IF NOT EXISTS ix_tierc ON tierc_signals(tenant_id, signal_type, category, published_at);

-- ===== materialized cards =====
CREATE TABLE IF NOT EXISTS cards(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER,
  dedup_key TEXT, run_id INTEGER, card_type TEXT, family TEXT, type_name TEXT,
  asin TEXT, category TEXT, finding TEXT, why TEXT, severity TEXT, sev_label TEXT,
  confidence INTEGER, conf_label TEXT, exposure_label TEXT, exposure_pct INTEGER,
  exposure_val TEXT, action TEXT, sources TEXT, minis TEXT, provenance TEXT,
  status TEXT DEFAULT 'new', is_new INTEGER DEFAULT 1,
  created_at TEXT, updated_at TEXT, UNIQUE(tenant_id, dedup_key)
);
CREATE INDEX IF NOT EXISTS ix_card ON cards(tenant_id, family, category, status, is_new);

CREATE TABLE IF NOT EXISTS category_products(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER,
  category TEXT, segment TEXT, asin TEXT, title TEXT, brand TEXT,
  price REAL, bsr INTEGER, reviews INTEGER, rating REAL, captured_at TEXT,
  UNIQUE(tenant_id, segment, asin)
);

CREATE TABLE IF NOT EXISTS card_research(
  tenant_id INTEGER, dedup_key TEXT, payload TEXT, created_at TEXT,
  PRIMARY KEY(tenant_id, dedup_key)
);

-- ===== explainability + research-native artifacts =====
CREATE TABLE IF NOT EXISTS actions_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, ts TEXT, card_id INTEGER, card_type TEXT,
  task_type TEXT, title TEXT, summary TEXT, explanation TEXT,
  mechanism TEXT, destination_url TEXT, payload TEXT
);
CREATE TABLE IF NOT EXISTS sourcing_list(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, ts TEXT, source_card_id INTEGER, segment TEXT,
  asin TEXT, title TEXT, brand TEXT, price REAL, bsr INTEGER, reviews INTEGER,
  rating REAL, opp_score REAL, note TEXT, UNIQUE(tenant_id, asin, segment)
);
CREATE TABLE IF NOT EXISTS watchlist(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, ts TEXT, card_id INTEGER, kind TEXT,
  label TEXT, category TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS saved_briefs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, ts TEXT, card_id INTEGER, card_type TEXT,
  category TEXT, brief TEXT
);

CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, started_at TEXT, finished_at TEXT,
  cards_new INTEGER, cards_updated INTEGER, status TEXT
);

-- ===== Step 3: channel-aware identity layer =====
CREATE TABLE IF NOT EXISTS products(
  tenant_id INTEGER, internal_sku TEXT, title TEXT, category TEXT, brand TEXT,
  cogs REAL, created_at TEXT, PRIMARY KEY(tenant_id, internal_sku)
);
CREATE TABLE IF NOT EXISTS channel_listings(
  tenant_id INTEGER, internal_sku TEXT, channel TEXT, channel_id TEXT, channel_sku TEXT,
  listing_status TEXT, link_status TEXT, price REAL, url TEXT,
  PRIMARY KEY(tenant_id, channel, channel_id)
);
CREATE INDEX IF NOT EXISTS ix_listing_prod ON channel_listings(tenant_id, internal_sku);

-- ===== Step 3: normalized per-channel fact tables (the 7 Amazon reports + Shopify later) =====
CREATE TABLE IF NOT EXISTS traffic(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  date TEXT, sessions INTEGER, page_views INTEGER, conversion_pct REAL, buybox_pct INTEGER
);
CREATE INDEX IF NOT EXISTS ix_traffic ON traffic(tenant_id, channel, internal_sku, date);
CREATE TABLE IF NOT EXISTS settlements(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  order_id TEXT, settlement_date TEXT, gross REAL, fees REAL, payout REAL, reserve REAL
);
CREATE INDEX IF NOT EXISTS ix_settle ON settlements(tenant_id, channel, internal_sku);
CREATE TABLE IF NOT EXISTS inventory(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  captured_at TEXT, on_hand INTEGER, inbound INTEGER, reserved INTEGER, unfulfillable INTEGER,
  days_of_cover REAL
);
CREATE INDEX IF NOT EXISTS ix_inv ON inventory(tenant_id, channel, internal_sku);
CREATE TABLE IF NOT EXISTS returns(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  return_date TEXT, order_id TEXT, units INTEGER, reason TEXT, refund_amount REAL
);
CREATE INDEX IF NOT EXISTS ix_ret ON returns(tenant_id, channel, internal_sku);
CREATE TABLE IF NOT EXISTS storage_fees(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  period TEXT, monthly_storage_fee REAL, aged_surcharge REAL, volume_cuft REAL, age_days INTEGER
);
CREATE INDEX IF NOT EXISTS ix_storage ON storage_fees(tenant_id, channel, internal_sku);

-- ===== Step 3: rules as data (default catalog + per-tenant overrides) =====
CREATE TABLE IF NOT EXISTS rules(
  rule_id TEXT PRIMARY KEY, name TEXT, description TEXT, family TEXT, card_type TEXT,
  tier INTEGER DEFAULT 1, primitive TEXT, inputs TEXT,
  params_default TEXT, editable_params TEXT, exposure_formula TEXT, action_handler TEXT,
  severity_default TEXT, enabled_by_default INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS tenant_rule_settings(
  tenant_id INTEGER, rule_id TEXT, enabled INTEGER, params TEXT, severity TEXT,
  updated_at TEXT, updated_by TEXT, PRIMARY KEY(tenant_id, rule_id)
);
CREATE TABLE IF NOT EXISTS tenant_settings(
  tenant_id INTEGER, key TEXT, value TEXT, PRIMARY KEY(tenant_id, key)
);
-- ===== Multi-channel: registry + canonical per-channel economics =====
-- channels: which marketplaces this tenant sells on, + the (approximate) fee model.
CREATE TABLE IF NOT EXISTS channels(
  tenant_id INTEGER, channel TEXT, label TEXT, active INTEGER DEFAULT 1,
  fee_pct REAL, fulfillment TEXT, currency TEXT,
  PRIMARY KEY(tenant_id, channel)
);
-- channel_economics: the canonical per-SKU-per-channel truth. BOTH the synthesizer and
-- (later) the CSV report parsers write here, so the cross-channel view is source-agnostic.
CREATE TABLE IF NOT EXISTS channel_economics(
  tenant_id INTEGER, internal_sku TEXT, asin TEXT, title TEXT, category TEXT,
  channel TEXT, present INTEGER DEFAULT 1, price REAL, units_month INTEGER,
  referral_pct REAL, fee_unit REAL, ad_unit REAL, cogs REAL, net_unit REAL,
  margin_pct REAL, revenue_month REAL, on_hand INTEGER, days_cover REAL,
  fulfillment TEXT, source TEXT DEFAULT 'synthetic',
  PRIMARY KEY(tenant_id, internal_sku, channel)
);
CREATE INDEX IF NOT EXISTS ix_chec ON channel_economics(tenant_id, channel);
CREATE INDEX IF NOT EXISTS ix_chec_sku ON channel_economics(tenant_id, internal_sku);
-- L2-tailored "why this matters" text, generated lazily on drill-down and cached per card.
CREATE TABLE IF NOT EXISTS card_why(
  tenant_id INTEGER, dedup_key TEXT, why TEXT, created_at TEXT,
  PRIMARY KEY(tenant_id, dedup_key)
);
-- Stage 2 Phase 0: per-run history of own-data metrics. The substrate for trends
-- (deterministic) and the model layer (forecasts). One row per (asin, metric, time).
CREATE TABLE IF NOT EXISTS metric_history(
  tenant_id INTEGER, asin TEXT, metric TEXT, value REAL, captured_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_mh ON metric_history(tenant_id, asin, metric, captured_at);
-- Usage analytics: funnel events, attributed server-side from the session.
-- Internal/admin only. `day` is denormalized (YYYY-MM-DD) for fast daily rollups.
CREATE TABLE IF NOT EXISTS usage_events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, user_id INTEGER,
  ts TEXT, day TEXT, event_type TEXT, page TEXT, card_id INTEGER, card_type TEXT, meta TEXT
);
CREATE INDEX IF NOT EXISTS ix_usage ON usage_events(tenant_id, day, event_type);
CREATE INDEX IF NOT EXISTS ix_usage_user ON usage_events(tenant_id, day, user_id);
-- Async job ledger (TaskRunner seam, #005 1e). Generic work-execution status so a triggered
-- pipeline run / future agent + real-time work can be enqueued and polled. Tenant-scoped.
CREATE TABLE IF NOT EXISTS jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, kind TEXT,
  state TEXT DEFAULT 'queued', result TEXT, error TEXT, created_at TEXT, updated_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_jobs ON jobs(tenant_id, kind, state);
-- Organization invites. tenant_id IS the organization. Tokens are stored hashed; the raw
-- token lives only in the invite link the owner sends. One user belongs to one org (users.email
-- is globally unique). Role is recorded but access is identical for all members for now.
CREATE TABLE IF NOT EXISTS invites(
  id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, email TEXT, role TEXT DEFAULT 'member',
  token_hash TEXT, status TEXT DEFAULT 'pending', created_at TEXT, expires_at TEXT,
  created_by INTEGER, accepted_by INTEGER, accepted_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_invite ON invites(tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_invite_tok ON invites(token_hash);
"""

def get_setting(con, tenant_id, key, default=None):
    from .repositories.settings_repo import SettingsRepository
    return SettingsRepository(con).get(tenant_id, key, default)

def set_setting(con, tenant_id, key, value):
    from .repositories.settings_repo import SettingsRepository
    return SettingsRepository(con).set(tenant_id, key, value)

def init_db():
    """Build/upgrade the schema via Alembic (`alembic upgrade head`) — one mechanism for both SQLite
    and Postgres. The baseline is idempotent (CREATE TABLE IF NOT EXISTS), so this safely ADOPTS an
    existing pre-Alembic SQLite DB (baseline is a no-op on existing tables, then later migrations
    apply). Targets whatever dbengine.url() resolves to (live config.DB_PATH / DATABASE_URL)."""
    from alembic.config import Config
    from alembic import command
    from . import dbengine
    dbengine.validate_url()                      # one clear line on a bad URL, not a deep traceback
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = Config(os.path.join(root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(root, "migrations"))
    command.upgrade(cfg, "head")

# ---------------- incremental watermark API (tenant-scoped) ----------------
def last_watermark(con, tenant_id, source, scope):
    from .repositories.pull_repo import PullLogRepository
    return PullLogRepository(con).last_watermark(tenant_id, source, scope)

def last_successful_pull_time(con, tenant_id, source, scope):
    from .repositories.pull_repo import PullLogRepository
    return PullLogRepository(con).last_successful_pull_time(tenant_id, source, scope)

def record_pull(con, tenant_id, source, scope, started_at, status, records, window_from, window_to, note=""):
    from .repositories.pull_repo import PullLogRepository
    return PullLogRepository(con).record(tenant_id, source, scope, started_at, status, records, window_from, window_to, note)

def due_for_pull(con, tenant_id, source, scope, interval_hours):
    from .repositories.pull_repo import PullLogRepository
    return PullLogRepository(con).due(tenant_id, source, scope, interval_hours)

# ---------------- tenant / user / invite helpers ----------------
# SQL for these bounded contexts now lives in realify/repositories/ (workstream 1b of #005).
# These remain as thin delegators so existing callers (run.py, api.py, scheduler.py) that pass
# their own `con` keep working unchanged. New code should prefer the repositories / UnitOfWork
# directly (see realify/repositories/__init__.py). Imports are local to avoid a circular import.
def create_tenant(con, name):
    from .repositories.tenant_repo import TenantRepository
    return TenantRepository(con).create(name)

def get_tenant(con, tenant_id):
    from .repositories.tenant_repo import TenantRepository
    return TenantRepository(con).get(tenant_id)

def set_tenant_provisioned(con, tenant_id, mode):
    from .repositories.tenant_repo import TenantRepository
    return TenantRepository(con).set_provisioned(tenant_id, mode)

def get_account_type(con, tenant_id):
    from .repositories.tenant_repo import TenantRepository
    return TenantRepository(con).get_account_type(tenant_id)

def set_account_type(con, tenant_id, account_type):
    from .repositories.tenant_repo import TenantRepository
    return TenantRepository(con).set_account_type(tenant_id, account_type)

def get_user_by_email(con, email):
    from .repositories.user_repo import UserRepository
    return UserRepository(con).get_by_email(email)

def get_user_by_id(con, user_id):
    from .repositories.user_repo import UserRepository
    return UserRepository(con).get_by_id(user_id)

def count_members(con, tenant_id):
    from .repositories.user_repo import UserRepository
    return UserRepository(con).count_members(tenant_id)

def delete_user(con, user_id):
    from .repositories.user_repo import UserRepository
    return UserRepository(con).delete(user_id)

def delete_tenant(con, tenant_id):
    from .repositories.tenant_repo import TenantRepository
    return TenantRepository(con).delete(tenant_id)

def create_user(con, email, pw_hash, pw_salt, tenant_id):
    from .repositories.user_repo import UserRepository
    return UserRepository(con).create(email, pw_hash, pw_salt, tenant_id)

def list_members(con, tenant_id):
    from .repositories.user_repo import UserRepository
    return UserRepository(con).list_members(tenant_id)

def create_invite(con, tenant_id, email, role, token_hash, expires_at, created_by):
    from .repositories.invite_repo import InviteRepository
    return InviteRepository(con).create(tenant_id, email, role, token_hash, expires_at, created_by)

def get_invite_by_token_hash(con, token_hash):
    from .repositories.invite_repo import InviteRepository
    return InviteRepository(con).get_by_token_hash(token_hash)

def list_invites(con, tenant_id):
    from .repositories.invite_repo import InviteRepository
    return InviteRepository(con).list(tenant_id)

def revoke_invite(con, tenant_id, invite_id):
    from .repositories.invite_repo import InviteRepository
    return InviteRepository(con).revoke(tenant_id, invite_id)

def mark_invite_accepted(con, invite_id, user_id):
    from .repositories.invite_repo import InviteRepository
    return InviteRepository(con).mark_accepted(invite_id, user_id)

# wipe ALL data rows for a tenant (keeps the tenant + user; returns them to onboarding)
TENANT_DATA_TABLES = ["seller_skus","seller_orders","pull_log","keepa_snapshots","competitor_offers",
    "tierc_signals","cards","card_why","category_products","card_research","actions_log","sourcing_list",
    "watchlist","saved_briefs","runs","products","channel_listings","traffic","settlements",
    "inventory","returns","storage_fees","tenant_rule_settings","metric_history","ad_performance",
    "sku_revenue_period","sku_field_provenance","pending_confirmations","ingested_reports","cogs_suggestions","tenant_topology","sku_crosswalk","ad_entity_perf","ad_search_term","ad_ingest_summary","channels","channel_economics"]  # +1b/CMAA +0008/0009/0010 +0012; channels/economics carry per-SKU DATA (audit QW-3) so wipe clears them

# Own-data metrics tracked over time (conversion lives in traffic, not seller_skus, so excluded)
HISTORY_METRICS = ["net_margin_pct","velocity_day","days_of_cover","stock_on_hand",
                   "rev_share_pct","tacos","returns_rate","rating","review_count","buybox_pct"]

def snapshot_metrics(con, tenant_id, captured_at=None):
    from .repositories.metrics_repo import MetricsRepository
    return MetricsRepository(con).snapshot(tenant_id, captured_at)

def metric_series(con, tenant_id, asin, metric, limit=400):
    from .repositories.metrics_repo import MetricsRepository
    return MetricsRepository(con).series(tenant_id, asin, metric, limit)

def wipe_tenant_data(con, tenant_id):
    # Data-layer-internal bulk wipe: a generic DELETE across every tenant-scoped table.
    # This is db.py's own schema-wide operation (not app logic bypassing a repo); the
    # per-table list lives here next to the schema. The tenant status reset goes through
    # the repository like everything else (lazy import to avoid the repos->db cycle).
    from .repositories.tenant_repo import TenantRepository
    for t in TENANT_DATA_TABLES:
        con.execute(f"DELETE FROM {t} WHERE tenant_id=?", (tenant_id,))
    TenantRepository(con).reset_provisioning(tenant_id)
    con.commit()
