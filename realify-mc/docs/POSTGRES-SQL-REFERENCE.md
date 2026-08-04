# Realify — Postgres SQL reference

*Generated 2026-06-30 from the source of truth: `realify/db.py` (schema), `realify/repositories/` (queries), translated to Postgres form by `realify/dbengine.py`.*

**33 tables, 19 indexes, 184 query statements.**

---

## How to read this

The app's SQL is **written** in SQLite dialect and **translated to Postgres at runtime** by `dbengine.py`. Every statement below is shown in its **Postgres form** — what actually executes against RDS:

- **Placeholders:** `?` becomes `%s` (psycopg *pyformat*). Parameters are bound positionally, in the order they appear — `%s` is not a string-format, it's the bind marker.

- **Upserts:** `INSERT OR REPLACE/IGNORE INTO t(...)` becomes `INSERT INTO t(...) ON CONFLICT (<key>) DO UPDATE SET … / DO NOTHING`, keyed by each table's real unique key (see appendix).

- **Auto-increment ids:** `INTEGER PRIMARY KEY AUTOINCREMENT` becomes `BIGSERIAL PRIMARY KEY`. Insert-and-return-id uses `db.create_returning_id()`, which appends `RETURNING id` on Postgres.

- **Dynamic SQL:** a few statements are assembled at runtime (dynamic column lists, `IN (...)` expansions). These are shown as templates with `{…}` marking the interpolated part and are flagged _dynamic_.

- Every query is tenant-scoped (`WHERE tenant_id=%s`); `tenant_id` is resolved server-side, never from the client.

---

## Part 1 — Schema (Postgres DDL)

The complete `CREATE TABLE` / `CREATE INDEX` set as it exists on Postgres (via `dbengine.schema_to_postgres`). This is also what Alembic's baseline migration creates.

```sql
-- ===== identity / tenancy =====
CREATE TABLE IF NOT EXISTS tenants(
  id BIGSERIAL PRIMARY KEY, name TEXT, created_at TEXT,
  data_mode TEXT,            -- 'synthetic' | 'uploaded' | NULL (not yet provisioned)
  provisioned INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS users(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, email TEXT UNIQUE,
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
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER,
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
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER,
  asin TEXT, captured_at TEXT, seller TEXT, price REAL,
  is_buybox INTEGER, is_fba INTEGER, in_stock INTEGER, condition TEXT
);
CREATE INDEX IF NOT EXISTS ix_offer ON competitor_offers(tenant_id, asin, captured_at);

CREATE TABLE IF NOT EXISTS tierc_signals(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER,
  source TEXT, signal_type TEXT, captured_at TEXT, published_at TEXT,
  category TEXT, title TEXT, url TEXT, summary TEXT, confidence INTEGER, raw TEXT,
  dedup_key TEXT, UNIQUE(tenant_id, dedup_key)
);
CREATE INDEX IF NOT EXISTS ix_tierc ON tierc_signals(tenant_id, signal_type, category, published_at);

-- ===== materialized cards =====
CREATE TABLE IF NOT EXISTS cards(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER,
  dedup_key TEXT, run_id INTEGER, card_type TEXT, family TEXT, type_name TEXT,
  asin TEXT, category TEXT, finding TEXT, why TEXT, severity TEXT, sev_label TEXT,
  confidence INTEGER, conf_label TEXT, exposure_label TEXT, exposure_pct INTEGER,
  exposure_val TEXT, action TEXT, sources TEXT, minis TEXT, provenance TEXT,
  status TEXT DEFAULT 'new', is_new INTEGER DEFAULT 1,
  created_at TEXT, updated_at TEXT, UNIQUE(tenant_id, dedup_key)
);
CREATE INDEX IF NOT EXISTS ix_card ON cards(tenant_id, family, category, status, is_new);

CREATE TABLE IF NOT EXISTS category_products(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER,
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
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, ts TEXT, card_id INTEGER, card_type TEXT,
  task_type TEXT, title TEXT, summary TEXT, explanation TEXT,
  mechanism TEXT, destination_url TEXT, payload TEXT
);
CREATE TABLE IF NOT EXISTS sourcing_list(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, ts TEXT, source_card_id INTEGER, segment TEXT,
  asin TEXT, title TEXT, brand TEXT, price REAL, bsr INTEGER, reviews INTEGER,
  rating REAL, opp_score REAL, note TEXT, UNIQUE(tenant_id, asin, segment)
);
CREATE TABLE IF NOT EXISTS watchlist(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, ts TEXT, card_id INTEGER, kind TEXT,
  label TEXT, category TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS saved_briefs(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, ts TEXT, card_id INTEGER, card_type TEXT,
  category TEXT, brief TEXT
);

CREATE TABLE IF NOT EXISTS runs(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, started_at TEXT, finished_at TEXT,
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
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  date TEXT, sessions INTEGER, page_views INTEGER, conversion_pct REAL, buybox_pct INTEGER
);
CREATE INDEX IF NOT EXISTS ix_traffic ON traffic(tenant_id, channel, internal_sku, date);
CREATE TABLE IF NOT EXISTS settlements(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  order_id TEXT, settlement_date TEXT, gross REAL, fees REAL, payout REAL, reserve REAL
);
CREATE INDEX IF NOT EXISTS ix_settle ON settlements(tenant_id, channel, internal_sku);
CREATE TABLE IF NOT EXISTS inventory(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  captured_at TEXT, on_hand INTEGER, inbound INTEGER, reserved INTEGER, unfulfillable INTEGER,
  days_of_cover REAL
);
CREATE INDEX IF NOT EXISTS ix_inv ON inventory(tenant_id, channel, internal_sku);
CREATE TABLE IF NOT EXISTS returns(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
  return_date TEXT, order_id TEXT, units INTEGER, reason TEXT, refund_amount REAL
);
CREATE INDEX IF NOT EXISTS ix_ret ON returns(tenant_id, channel, internal_sku);
CREATE TABLE IF NOT EXISTS storage_fees(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, channel TEXT, internal_sku TEXT,
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
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, user_id INTEGER,
  ts TEXT, day TEXT, event_type TEXT, page TEXT, card_id INTEGER, card_type TEXT, meta TEXT
);
CREATE INDEX IF NOT EXISTS ix_usage ON usage_events(tenant_id, day, event_type);
CREATE INDEX IF NOT EXISTS ix_usage_user ON usage_events(tenant_id, day, user_id);
-- Async job ledger (TaskRunner seam, #005 1e). Generic work-execution status so a triggered
-- pipeline run / future agent + real-time work can be enqueued and polled. Tenant-scoped.
CREATE TABLE IF NOT EXISTS jobs(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, kind TEXT,
  state TEXT DEFAULT 'queued', result TEXT, error TEXT, created_at TEXT, updated_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_jobs ON jobs(tenant_id, kind, state);
-- Organization invites. tenant_id IS the organization. Tokens are stored hashed; the raw
-- token lives only in the invite link the owner sends. One user belongs to one org (users.email
-- is globally unique). Role is recorded but access is identical for all members for now.
CREATE TABLE IF NOT EXISTS invites(
  id BIGSERIAL PRIMARY KEY, tenant_id INTEGER, email TEXT, role TEXT DEFAULT 'member',
  token_hash TEXT, status TEXT DEFAULT 'pending', created_at TEXT, expires_at TEXT,
  created_by INTEGER, accepted_by INTEGER, accepted_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_invite ON invites(tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_invite_tok ON invites(token_hash);
```

---

## Part 2 — Queries by repository

All data SQL lives in `realify/repositories/`. Grouped by file, then by the method that issues the query, in source order.

### `action_repo.py` — 9 statement(s)

**`ActionRepository.log_action()`**
```sql
INSERT INTO actions_log(tenant_id,ts,card_id,card_type,task_type,title,summary,explanation,mechanism,destination_url,payload) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
```
**`ActionRepository.recent()`**
```sql
SELECT * FROM actions_log WHERE tenant_id=%s ORDER BY id DESC LIMIT %s
```
**`ActionRepository.add_watchlist()`**
```sql
INSERT INTO watchlist(tenant_id,ts,card_id,kind,label,category,note) VALUES(%s,%s,%s,%s,%s,%s,%s)
```
**`ActionRepository.list_watchlist()`**
```sql
SELECT * FROM watchlist WHERE tenant_id=%s ORDER BY id DESC
```
**`ActionRepository.add_sourcing()`**
```sql
INSERT INTO sourcing_list(tenant_id,ts,source_card_id,segment,asin,title,brand,price,bsr,reviews,rating,opp_score,note) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id, asin, segment) DO NOTHING
```
**`ActionRepository.list_sourcing()`**
```sql
SELECT * FROM sourcing_list WHERE tenant_id=%s ORDER BY opp_score DESC
```
**`ActionRepository.add_brief()`**
```sql
INSERT INTO saved_briefs(tenant_id,ts,card_id,card_type,category,brief) VALUES(%s,%s,%s,%s,%s,%s)
```
**`ActionRepository.start_run()`**
```sql
INSERT INTO runs(tenant_id,started_at,status) VALUES(%s,%s,%s)
```
**`ActionRepository.finish_run()`**
```sql
UPDATE runs SET finished_at=%s,cards_new=%s,cards_updated=%s,status=%s WHERE id=%s
```

### `analytics_repo.py` — 10 statement(s)

**`AnalyticsRepository.record()`**
```sql
INSERT INTO usage_events(tenant_id,user_id,ts,day,event_type,page,card_id,card_type,meta) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
```
**`AnalyticsRepository.daily_summary()`**  *(dynamic)*
```sql
SELECT day, COUNT(DISTINCT user_id) AS active_users, SUM(event_type='page_view')      AS page_views, SUM(event_type='insight_click')  AS insight_clicks, SUM(event_type='research')       AS researched, SUM(event_type='action_clickout') AS action_clickouts FROM usage_events WHERE {where} GROUP BY day ORDER BY day
```
**`AnalyticsRepository.daily_summary()`**
```sql
SELECT day, COUNT(DISTINCT user_id) AS active_users, SUM(event_type='page_view')      AS page_views, SUM(event_type='insight_click')  AS insight_clicks, SUM(event_type='research')       AS researched, SUM(event_type='action_clickout') AS action_clickouts FROM usage_events WHERE
```
**`AnalyticsRepository.totals()`**  *(dynamic)*
```sql
SELECT COUNT(DISTINCT user_id) AS active_users, SUM(event_type='page_view')       AS page_views, SUM(event_type='insight_click')   AS insight_clicks, SUM(event_type='research')        AS researched, SUM(event_type='action_clickout') AS action_clickouts, COUNT(*) AS events FROM usage_events WHERE {where}
```
**`AnalyticsRepository.totals()`**
```sql
SELECT COUNT(DISTINCT user_id) AS active_users, SUM(event_type='page_view')       AS page_views, SUM(event_type='insight_click')   AS insight_clicks, SUM(event_type='research')        AS researched, SUM(event_type='action_clickout') AS action_clickouts, COUNT(*) AS events FROM usage_events WHERE
```
**`AnalyticsRepository.top_users()`**  *(dynamic)*
```sql
SELECT e.user_id AS user_id, COALESCE(u.email,'(unknown)') AS email, COUNT(*) AS events, SUM(e.event_type='page_view')       AS page_views, SUM(e.event_type='insight_click')   AS insight_clicks, SUM(e.event_type='research')        AS researched, SUM(e.event_type='action_clickout') AS action_clickouts, MAX(e.ts) AS last_seen FROM usage_events e LEFT JOIN users u ON u.id=e.user_id WHERE {where} GROUP BY e.user_id ORDER BY events DESC LIMIT %s
```
**`AnalyticsRepository.top_users()`**
```sql
SELECT e.user_id AS user_id, COALESCE(u.email,'(unknown)') AS email, COUNT(*) AS events, SUM(e.event_type='page_view')       AS page_views, SUM(e.event_type='insight_click')   AS insight_clicks, SUM(e.event_type='research')        AS researched, SUM(e.event_type='action_clickout') AS action_clickouts, MAX(e.ts) AS last_seen FROM usage_events e LEFT JOIN users u ON u.id=e.user_id WHERE
```
**`AnalyticsRepository.last_activity()`**
```sql
SELECT MAX(day) m FROM usage_events WHERE tenant_id=%s
```
**`SystemRepository.entity_counts()`**  *(dynamic)*
```sql
SELECT COUNT(*) c FROM {t}
```
**`SystemRepository.entity_counts()`**
```sql
SELECT COUNT(*) c FROM
```

### `card_repo.py` — 16 statement(s)

**`CardRepository.feed()`**
```sql
SELECT * FROM cards WHERE tenant_id=%s AND status!='dismissed'
```
**`CardRepository.get()`**
```sql
SELECT * FROM cards WHERE id=%s AND tenant_id=%s
```
**`CardRepository._count()`**  *(dynamic)*
```sql
SELECT COUNT(*) n FROM cards WHERE {where}
```
**`CardRepository._count()`**
```sql
SELECT COUNT(*) n FROM cards WHERE
```
**`CardRepository.research_payload()`**
```sql
SELECT payload FROM card_research WHERE tenant_id=%s AND dedup_key=%s
```
**`CardRepository.count_distinct_types()`**
```sql
SELECT COUNT(DISTINCT card_type) c FROM cards WHERE tenant_id=%s AND status!='dismissed'
```
**`CardRepository.existing_dedup_keys()`**
```sql
SELECT dedup_key FROM cards WHERE tenant_id=%s
```
**`CardRepository.upsert()`**  *(dynamic)*
```sql
INSERT INTO cards({cols}) VALUES({qs}) ON CONFLICT(tenant_id,dedup_key) DO UPDATE SET {updates}
```
**`CardRepository.upsert()`**
```sql
INSERT INTO cards(
```
**`CardRepository.upsert()`**
```sql
) ON CONFLICT(tenant_id,dedup_key) DO UPDATE SET
```
**`CardRepository.prune_stale()`**
```sql
DELETE FROM cards WHERE tenant_id=%s AND dedup_key=%s AND status NOT IN('dismissed','done')
```
**`CardRepository.set_status()`**
```sql
UPDATE cards SET status=%s WHERE id=%s AND tenant_id=%s
```
**`CardRepository.save_research()`**
```sql
INSERT INTO card_research(tenant_id,dedup_key,payload,created_at) VALUES(%s,%s,%s,%s) ON CONFLICT (tenant_id, dedup_key) DO UPDATE SET payload=EXCLUDED.payload, created_at=EXCLUDED.created_at
```
**`CardRepository.clear_research()`**
```sql
DELETE FROM card_research WHERE tenant_id=%s
```
**`CardRepository.why_cached()`**
```sql
SELECT why FROM card_why WHERE tenant_id=%s AND dedup_key=%s
```
**`CardRepository.save_why()`**
```sql
INSERT INTO card_why(tenant_id,dedup_key,why,created_at) VALUES(%s,%s,%s,%s) ON CONFLICT (tenant_id, dedup_key) DO UPDATE SET why=EXCLUDED.why, created_at=EXCLUDED.created_at
```

### `catalog_repo.py` — 2 statement(s)

**`CatalogRepository.cached_segment()`**
```sql
SELECT * FROM category_products WHERE tenant_id=%s AND segment=%s ORDER BY bsr ASC
```
**`CatalogRepository.insert_product()`**
```sql
INSERT INTO category_products(tenant_id,category,segment,asin,title,brand,price,bsr,reviews,rating,captured_at)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id, segment, asin) DO NOTHING
```

### `channel_repo.py` — 21 statement(s)

**`ProductRepository.upsert()`**
```sql
INSERT INTO products(tenant_id,internal_sku,title,category,brand,cogs,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id, internal_sku) DO UPDATE SET title=EXCLUDED.title, category=EXCLUDED.category, brand=EXCLUDED.brand, cogs=EXCLUDED.cogs, created_at=EXCLUDED.created_at
```
**`ProductRepository.all()`**
```sql
SELECT * FROM products WHERE tenant_id=%s
```
**`ProductRepository.count()`**
```sql
SELECT COUNT(*) c FROM products WHERE tenant_id=%s
```
**`ProductRepository.delete_all()`**
```sql
DELETE FROM products WHERE tenant_id=%s
```
**`ChannelListingRepository.upsert()`**
```sql
INSERT INTO channel_listings(tenant_id,internal_sku,channel,channel_id,channel_sku,listing_status,link_status,price,url) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id, channel, channel_id) DO UPDATE SET internal_sku=EXCLUDED.internal_sku, channel_sku=EXCLUDED.channel_sku, listing_status=EXCLUDED.listing_status, link_status=EXCLUDED.link_status, price=EXCLUDED.price, url=EXCLUDED.url
```
**`ChannelListingRepository.by_sku()`**
```sql
SELECT channel,channel_id,price,link_status FROM channel_listings WHERE tenant_id=%s AND internal_sku=%s
```
**`ChannelListingRepository.count()`**
```sql
SELECT COUNT(*) c FROM channel_listings WHERE tenant_id=%s
```
**`ChannelListingRepository.delete_all()`**
```sql
DELETE FROM channel_listings WHERE tenant_id=%s
```
**`ReturnsRepository.insert()`**
```sql
INSERT INTO returns(tenant_id,channel,internal_sku,return_date,order_id,units,reason,refund_amount) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
```
**`ReturnsRepository.count()`**
```sql
SELECT COUNT(*) c FROM returns WHERE tenant_id=%s
```
**`ReturnsRepository.delete_all()`**
```sql
DELETE FROM returns WHERE tenant_id=%s
```
**`StorageFeeRepository.insert()`**
```sql
INSERT INTO storage_fees(tenant_id,channel,internal_sku,period,monthly_storage_fee,aged_surcharge,volume_cuft,age_days) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
```
**`StorageFeeRepository.count()`**
```sql
SELECT COUNT(*) c FROM storage_fees WHERE tenant_id=%s
```
**`StorageFeeRepository.delete_all()`**
```sql
DELETE FROM storage_fees WHERE tenant_id=%s
```
**`ChannelRepository.upsert()`**
```sql
INSERT INTO channels(tenant_id,channel,label,active,fee_pct,fulfillment,currency) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id, channel) DO UPDATE SET label=EXCLUDED.label, active=EXCLUDED.active, fee_pct=EXCLUDED.fee_pct, fulfillment=EXCLUDED.fulfillment, currency=EXCLUDED.currency
```
**`ChannelRepository.active()`**
```sql
SELECT * FROM channels WHERE tenant_id=%s AND active=1
```
**`ChannelEconomicsRepository.all()`**
```sql
SELECT * FROM channel_economics WHERE tenant_id=%s
```
**`ChannelEconomicsRepository.count_present()`**
```sql
SELECT COUNT(*) n FROM channel_economics WHERE tenant_id=%s AND channel=%s AND present=1
```
**`ChannelEconomicsRepository.delete_all()`**
```sql
DELETE FROM channel_economics WHERE tenant_id=%s
```
**`ChannelEconomicsRepository.insert_absent()`**
```sql
INSERT INTO channel_economics(tenant_id,internal_sku,asin,title,category,channel,present,price,units_month,referral_pct,fee_unit,ad_unit,cogs,net_unit,margin_pct,revenue_month,on_hand,days_cover,fulfillment,source) VALUES(%s,%s,%s,%s,%s,%s,0,NULL,0,%s,0,0,%s,0,0,0,0,0,%s, 'synthetic') ON CONFLICT (tenant_id, internal_sku, channel) DO UPDATE SET asin=EXCLUDED.asin, title=EXCLUDED.title, category=EXCLUDED.category, present=EXCLUDED.present, price=EXCLUDED.price, units_month=EXCLUDED.units_month, referral_pct=EXCLUDED.referral_pct, fee_unit=EXCLUDED.fee_unit, ad_unit=EXCLUDED.ad_unit, cogs=EXCLUDED.cogs, net_unit=EXCLUDED.net_unit, margin_pct=EXCLUDED.margin_pct, revenue_month=EXCLUDED.revenue_month, on_hand=EXCLUDED.on_hand, days_cover=EXCLUDED.days_cover, fulfillment=EXCLUDED.fulfillment, source=EXCLUDED.source
```
**`ChannelEconomicsRepository.insert_present()`**
```sql
INSERT INTO channel_economics(tenant_id,internal_sku,asin,title,category,channel,present,price,units_month,referral_pct,fee_unit,ad_unit,cogs,net_unit,margin_pct,revenue_month,on_hand,days_cover,fulfillment,source) VALUES(%s,%s,%s,%s,%s,%s,1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, 'synthetic') ON CONFLICT (tenant_id, internal_sku, channel) DO UPDATE SET asin=EXCLUDED.asin, title=EXCLUDED.title, category=EXCLUDED.category, present=EXCLUDED.present, price=EXCLUDED.price, units_month=EXCLUDED.units_month, referral_pct=EXCLUDED.referral_pct, fee_unit=EXCLUDED.fee_unit, ad_unit=EXCLUDED.ad_unit, cogs=EXCLUDED.cogs, net_unit=EXCLUDED.net_unit, margin_pct=EXCLUDED.margin_pct, revenue_month=EXCLUDED.revenue_month, on_hand=EXCLUDED.on_hand, days_cover=EXCLUDED.days_cover, fulfillment=EXCLUDED.fulfillment, source=EXCLUDED.source
```

### `fact_repos.py` — 21 statement(s)

**`TrafficRepository.internal_skus_ordered()`**
```sql
SELECT internal_sku FROM traffic WHERE tenant_id=%s ORDER BY internal_sku
```
**`TrafficRepository.count_with_conversion()`**
```sql
SELECT COUNT(*) c FROM traffic WHERE tenant_id=%s AND conversion_pct IS NOT NULL
```
**`TrafficRepository.conversion_by_asin()`**
```sql
SELECT cl.channel_id asin, t.conversion_pct conv FROM traffic t JOIN channel_listings cl ON cl.tenant_id=t.tenant_id AND cl.internal_sku=t.internal_sku WHERE t.tenant_id=%s
```
**`TrafficRepository.count()`**
```sql
SELECT COUNT(*) c FROM traffic WHERE tenant_id=%s
```
**`TrafficRepository.set_conversion()`**
```sql
UPDATE traffic SET conversion_pct=%s WHERE tenant_id=%s AND internal_sku=%s
```
**`TrafficRepository.delete_all()`**
```sql
DELETE FROM traffic WHERE tenant_id=%s
```
**`TrafficRepository.delete_by_channel_date()`**
```sql
DELETE FROM traffic WHERE tenant_id=%s AND channel=%s AND date=%s
```
**`TrafficRepository.insert()`**
```sql
INSERT INTO traffic(tenant_id,channel,internal_sku,date,sessions,page_views,conversion_pct,buybox_pct) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
```
**`InventoryRepository.list_on_hand()`**
```sql
SELECT on_hand, internal_sku sku FROM inventory WHERE tenant_id=%s
```
**`InventoryRepository.count_low_cover()`**
```sql
SELECT COUNT(*) c FROM inventory WHERE tenant_id=%s AND days_of_cover<14
```
**`InventoryRepository.sum_by_sku()`**
```sql
SELECT COALESCE(SUM(on_hand),0) oh, COALESCE(SUM(inbound),0) ib FROM inventory WHERE tenant_id=%s AND internal_sku=%s
```
**`InventoryRepository.count()`**
```sql
SELECT COUNT(*) c FROM inventory WHERE tenant_id=%s
```
**`InventoryRepository.delete_all()`**
```sql
DELETE FROM inventory WHERE tenant_id=%s
```
**`InventoryRepository.insert()`**
```sql
INSERT INTO inventory(tenant_id,channel,internal_sku,captured_at,on_hand,inbound,reserved,unfulfillable,days_of_cover) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
```
**`SettlementRepository.window_summary()`**
```sql
SELECT COALESCE(SUM(payout),0) payout, COALESCE(SUM(gross-fees-payout),0) short FROM settlements WHERE tenant_id=%s AND settlement_date>=%s
```
**`SettlementRepository.sum_fees_by_sku()`**
```sql
SELECT COALESCE(SUM(fees),0) f FROM settlements WHERE tenant_id=%s AND internal_sku=%s
```
**`SettlementRepository.count()`**
```sql
SELECT COUNT(*) c FROM settlements WHERE tenant_id=%s
```
**`SettlementRepository.delete_all()`**
```sql
DELETE FROM settlements WHERE tenant_id=%s
```
**`SettlementRepository.delete_by_channel()`**
```sql
DELETE FROM settlements WHERE tenant_id=%s AND channel=%s
```
**`SettlementRepository.insert()`**
```sql
INSERT INTO settlements(tenant_id,channel,internal_sku,order_id,settlement_date,gross,fees,payout,reserve) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
```
**`SettlementRepository.insert_many()`**
```sql
INSERT INTO settlements(tenant_id,channel,internal_sku,order_id,settlement_date,gross,fees,payout,reserve) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
```

### `invite_repo.py` — 5 statement(s)

**`InviteRepository.create()`**
```sql
INSERT INTO invites(tenant_id,email,role,token_hash,status,created_at,expires_at,created_by)
               VALUES(%s,%s,%s,%s,'pending',%s,%s,%s)
```
**`InviteRepository.get_by_token_hash()`**
```sql
SELECT * FROM invites WHERE token_hash=%s
```
**`InviteRepository.list()`**
```sql
SELECT id,email,role,status,created_at,expires_at FROM invites WHERE tenant_id=%s ORDER BY created_at DESC
```
**`InviteRepository.revoke()`**
```sql
UPDATE invites SET status='revoked' WHERE id=%s AND tenant_id=%s AND status='pending'
```
**`InviteRepository.mark_accepted()`**
```sql
UPDATE invites SET status='accepted', accepted_by=%s, accepted_at=%s WHERE id=%s
```

### `job_repo.py` — 3 statement(s)

**`JobRepository.create()`**
```sql
INSERT INTO jobs(tenant_id, kind, state, created_at, updated_at) VALUES(%s,%s,%s,%s,%s)
```
**`JobRepository.set_state()`**
```sql
UPDATE jobs SET state=%s, result=%s, error=%s, updated_at=%s WHERE id=%s
```
**`JobRepository.get()`**
```sql
SELECT * FROM jobs WHERE id=%s
```

### `market_repo.py` — 9 statement(s)

**`MarketRepository.recent_snapshots()`**
```sql
SELECT * FROM keepa_snapshots WHERE tenant_id=%s AND asin=%s ORDER BY captured_at DESC LIMIT %s
```
**`MarketRepository.latest_bsr()`**
```sql
SELECT bsr FROM keepa_snapshots WHERE tenant_id=%s AND asin=%s AND bsr IS NOT NULL ORDER BY captured_at DESC LIMIT 1
```
**`MarketRepository.insert_snapshot()`**
```sql
INSERT INTO keepa_snapshots(tenant_id,asin,captured_at,price,bsr,bsr_avg30,rating,review_count,offer_count,buybox_price,buybox_seller,raw) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id, asin, captured_at) DO NOTHING
```
**`MarketRepository.latest_offers()`**
```sql
SELECT seller,price FROM competitor_offers WHERE tenant_id=%s AND asin=%s AND captured_at=(SELECT MAX(captured_at) FROM competitor_offers WHERE tenant_id=%s AND asin=%s) ORDER BY price ASC
```
**`MarketRepository.insert_offer()`**
```sql
INSERT INTO competitor_offers(tenant_id,asin,captured_at,seller,price,is_buybox,is_fba,in_stock,condition) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
```
**`MarketRepository.latest_trend()`**
```sql
SELECT title,summary,raw FROM tierc_signals WHERE tenant_id=%s AND signal_type='trend' ORDER BY published_at DESC LIMIT 1
```
**`MarketRepository.trends()`**
```sql
SELECT * FROM tierc_signals WHERE tenant_id=%s AND signal_type='trend' ORDER BY published_at DESC LIMIT %s
```
**`MarketRepository.latest_signal()`**
```sql
SELECT * FROM tierc_signals WHERE tenant_id=%s AND signal_type=%s ORDER BY published_at DESC LIMIT 1
```
**`MarketRepository.insert_signal()`**
```sql
INSERT INTO tierc_signals(tenant_id,source,signal_type,captured_at,published_at,category,title,url,summary,confidence,raw,dedup_key) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tenant_id, dedup_key) DO NOTHING
```

### `metrics_repo.py` — 6 statement(s)

**`MetricsRepository.snapshot()`**  *(dynamic)*
```sql
SELECT asin,{cols} FROM seller_skus WHERE tenant_id=%s
```
**`MetricsRepository.snapshot()`**
```sql
INSERT INTO metric_history(tenant_id,asin,metric,value,captured_at) VALUES(%s,%s,%s,%s,%s)
```
**`MetricsRepository.series()`**
```sql
SELECT value, captured_at FROM metric_history
               WHERE tenant_id=%s AND asin=%s AND metric=%s ORDER BY captured_at ASC LIMIT %s
```
**`MetricsRepository.history_exists()`**
```sql
SELECT 1 FROM metric_history WHERE tenant_id=%s LIMIT 1
```
**`MetricsRepository.insert_history_many()`**
```sql
INSERT INTO metric_history(tenant_id,asin,metric,value,captured_at) VALUES(%s,%s,%s,%s,%s)
```
**`MetricsRepository.delete_history()`**
```sql
DELETE FROM metric_history WHERE tenant_id=%s
```

### `order_repo.py` — 18 statement(s)

**`OrderRepository.count()`**
```sql
SELECT COUNT(*) c FROM seller_orders WHERE tenant_id=%s
```
**`OrderRepository.count_short_paid()`**
```sql
SELECT COUNT(*) c FROM seller_orders WHERE tenant_id=%s AND actual_deposit>0 AND actual_deposit < expected_deposit*0.99
```
**`OrderRepository.count_review_eligible()`**
```sql
SELECT COUNT(*) c FROM seller_orders WHERE tenant_id=%s AND review_eligible=1
```
**`OrderRepository.window_rows()`**
```sql
SELECT asin,units,gross,referral_fee,fba_fee FROM seller_orders WHERE tenant_id=%s AND order_date>=%s
```
**`OrderRepository.settled()`**
```sql
SELECT order_id,internal_sku,gross,referral_fee,fba_fee,actual_deposit,settlement_date FROM seller_orders WHERE tenant_id=%s AND status='settled'
```
**`OrderRepository.channel_rollup()`**
```sql
SELECT channel, COUNT(*) orders, SUM(units) units, SUM(gross) revenue FROM seller_orders WHERE tenant_id=%s AND internal_sku=%s GROUP BY channel
```
**`OrderRepository.short_paid_detail()`**  *(dynamic)*
```sql
SELECT order_id,order_date,expected_deposit,actual_deposit FROM seller_orders WHERE tenant_id=%s AND actual_deposit>0 AND actual_deposit < expected_deposit*0.99 {…}ORDER BY (expected_deposit-actual_deposit) DESC LIMIT %s
```
**`OrderRepository.short_paid_detail()`**  *(dynamic)*
```sql
SELECT order_id,order_date,expected_deposit,actual_deposit FROM seller_orders WHERE tenant_id=%s AND actual_deposit>0 AND actual_deposit < expected_deposit*0.99 {…}
```
**`OrderRepository.short_paid_detail()`**
```sql
SELECT order_id,order_date,expected_deposit,actual_deposit FROM seller_orders WHERE tenant_id=%s AND actual_deposit>0 AND actual_deposit < expected_deposit*0.99
```
**`OrderRepository.review_eligible_detail()`**  *(dynamic)*
```sql
SELECT order_id,delivered_date FROM seller_orders WHERE tenant_id=%s AND review_eligible=1 {…}ORDER BY delivered_date DESC LIMIT %s
```
**`OrderRepository.review_eligible_detail()`**  *(dynamic)*
```sql
SELECT order_id,delivered_date FROM seller_orders WHERE tenant_id=%s AND review_eligible=1 {…}
```
**`OrderRepository.review_eligible_detail()`**
```sql
SELECT order_id,delivered_date FROM seller_orders WHERE tenant_id=%s AND review_eligible=1
```
**`OrderRepository.delete_all()`**
```sql
DELETE FROM seller_orders WHERE tenant_id=%s
```
**`OrderRepository.delete_by_channel()`**
```sql
DELETE FROM seller_orders WHERE tenant_id=%s AND channel=%s
```
**`OrderRepository.insert_many_synthetic()`**  *(dynamic)*
```sql
INSERT OR IGNORE INTO seller_orders({_INSERT_SYNTH_COLS}) VALUES({qs})
```
**`OrderRepository.insert_many_synthetic()`**
```sql
INSERT OR IGNORE INTO seller_orders(
```
**`OrderRepository.insert_imported()`**
```sql
INSERT INTO seller_orders(tenant_id,order_id,asin,order_date,units,gross,channel,internal_sku,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s, 'settled')
```
**`OrderRepository.link_channel()`**
```sql
UPDATE seller_orders SET internal_sku=%s, channel=%s WHERE tenant_id=%s AND asin=%s
```

### `pull_repo.py` — 9 statement(s)

**`PullLogRepository.last_watermark()`**
```sql
SELECT MAX(window_to) AS wm FROM pull_log WHERE tenant_id=%s AND source=%s AND scope=%s AND status='ok'
```
**`PullLogRepository.last_successful_pull_time()`**
```sql
SELECT MAX(finished_at) AS t FROM pull_log WHERE tenant_id=%s AND source=%s AND scope=%s AND status='ok'
```
**`PullLogRepository.record()`**
```sql
INSERT INTO pull_log(tenant_id,source,scope,started_at,finished_at,status,records,window_from,window_to,note) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
```
**`PullLogRepository.max_ok_by_source()`**
```sql
SELECT MAX(finished_at) t, MAX(records) r FROM pull_log WHERE tenant_id=%s AND source=%s AND status='ok'
```
**`PullLogRepository.max_ok()`**
```sql
SELECT MAX(finished_at) t FROM pull_log WHERE tenant_id=%s AND status='ok'
```
**`PullLogRepository.last_by_source()`**
```sql
SELECT status, note, records FROM pull_log WHERE tenant_id=%s AND source=%s ORDER BY id DESC LIMIT 1
```
**`PullLogRepository.log_import()`**
```sql
INSERT INTO pull_log(tenant_id,source,scope,started_at,finished_at,status,records,note) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
```
**`PullLogRepository.sources_last_global()`**
```sql
SELECT source, MAX(finished_at) last_at FROM pull_log GROUP BY source
```
**`PullLogRepository.last_global_by_source()`**
```sql
SELECT status, finished_at, note FROM pull_log WHERE source=%s ORDER BY finished_at DESC LIMIT 1
```

### `rules_repo.py` — 9 statement(s)

**`RulesRepository.upsert_rule()`**
```sql
INSERT INTO rules(rule_id,name,description,family,card_type,tier,primitive,
               inputs,params_default,editable_params,exposure_formula,action_handler,severity_default,enabled_by_default)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (rule_id) DO UPDATE SET name=EXCLUDED.name, description=EXCLUDED.description, family=EXCLUDED.family, card_type=EXCLUDED.card_type, tier=EXCLUDED.tier, primitive=EXCLUDED.primitive, inputs=EXCLUDED.inputs, params_default=EXCLUDED.params_default, editable_params=EXCLUDED.editable_params, exposure_formula=EXCLUDED.exposure_formula, action_handler=EXCLUDED.action_handler, severity_default=EXCLUDED.severity_default, enabled_by_default=EXCLUDED.enabled_by_default
```
**`RulesRepository.all_rules()`**
```sql
SELECT * FROM rules
```
**`RulesRepository.get_rule()`**
```sql
SELECT * FROM rules WHERE rule_id=%s
```
**`RulesRepository.count_rules()`**
```sql
SELECT COUNT(*) c FROM rules
```
**`RulesRepository.surface_map_rows()`**
```sql
SELECT rule_id, inputs, action_handler FROM rules
```
**`RulesRepository.tenant_overrides()`**
```sql
SELECT * FROM tenant_rule_settings WHERE tenant_id=%s
```
**`RulesRepository.upsert_override()`**
```sql
INSERT INTO tenant_rule_settings(tenant_id,rule_id,enabled,params,severity,updated_at,updated_by)
               VALUES(%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT(tenant_id,rule_id) DO UPDATE SET enabled=excluded.enabled, params=excluded.params,
               severity=excluded.severity, updated_at=excluded.updated_at, updated_by=excluded.updated_by
```
**`RulesRepository.delete_override()`**
```sql
DELETE FROM tenant_rule_settings WHERE tenant_id=%s AND rule_id=%s
```
**`RulesRepository.delete_override()`**
```sql
DELETE FROM tenant_rule_settings WHERE tenant_id=%s
```

### `seller_repo.py` — 25 statement(s)

**`SellerRepository.all()`**
```sql
SELECT * FROM seller_skus WHERE tenant_id=%s
```
**`SellerRepository.by_asin()`**
```sql
SELECT * FROM seller_skus WHERE tenant_id=%s AND asin=%s
```
**`SellerRepository.count()`**
```sql
SELECT COUNT(*) c FROM seller_skus WHERE tenant_id=%s
```
**`SellerRepository.count_non_null()`**  *(dynamic)*
```sql
SELECT COUNT(*) c FROM seller_skus WHERE tenant_id=%s AND {col} IS NOT NULL
```
**`SellerRepository.count_non_null()`**
```sql
SELECT COUNT(*) c FROM seller_skus WHERE tenant_id=%s AND
```
**`SellerRepository.distinct_categories()`**
```sql
SELECT DISTINCT category FROM seller_skus WHERE tenant_id=%s
```
**`SellerRepository.category_aggregate()`**
```sql
SELECT COUNT(*) n, COALESCE(SUM(annual_rev_inr),0) gmv, AVG(buybox_pct) bb
               FROM seller_skus WHERE tenant_id=%s AND category=%s
```
**`SellerRepository.distinct_values()`**  *(dynamic)*
```sql
SELECT DISTINCT {col} AS v FROM seller_skus WHERE tenant_id=%s AND {col} IS NOT NULL AND {col}<>''
```
**`SellerRepository.asins()`**  *(dynamic)*
```sql
SELECT asin FROM seller_skus WHERE tenant_id=%s{…}
```
**`SellerRepository.asins()`**
```sql
SELECT asin FROM seller_skus WHERE tenant_id=%s
```
**`SellerRepository.select_columns()`**  *(dynamic)*
```sql
SELECT {cols} FROM seller_skus WHERE tenant_id=%s
```
**`SellerRepository.price_row_by_sku_or_asin()`**
```sql
SELECT price FROM seller_skus WHERE tenant_id=%s AND (asin=%s OR internal_sku=%s)
```
**`SellerRepository.columns_by_asin()`**  *(dynamic)*
```sql
SELECT {cols} FROM seller_skus WHERE tenant_id=%s AND asin=%s
```
**`SellerRepository.delete_all()`**
```sql
DELETE FROM seller_skus WHERE tenant_id=%s
```
**`SellerRepository.insert()`**  *(dynamic)*
```sql
INSERT OR REPLACE INTO seller_skus({cols}) VALUES({qs})
```
**`SellerRepository.insert()`**
```sql
INSERT OR REPLACE INTO seller_skus(
```
**`SellerRepository.update_economics()`**
```sql
UPDATE seller_skus SET cogs=%s, referral_fee=%s, net_profit_unit=%s, net_margin_pct=%s, breakeven_floor=%s WHERE tenant_id=%s AND (asin=%s OR internal_sku=%s)
```
**`SellerRepository.update_cogs()`**
```sql
UPDATE seller_skus SET cogs=%s WHERE tenant_id=%s AND (asin=%s OR internal_sku=%s)
```
**`SellerRepository.update_fields_by_asin()`**  *(dynamic)*
```sql
UPDATE seller_skus SET {sets} WHERE tenant_id=%s AND asin=%s
```
**`SellerRepository.update_fields_by_asin()`**
```sql
UPDATE seller_skus SET
```
**`SellerRepository.update_fields_by_sku_or_asin()`**  *(dynamic)*
```sql
UPDATE seller_skus SET {sets} WHERE tenant_id=%s AND (asin=%s OR internal_sku=%s)
```
**`SellerRepository.update_fields_by_sku_or_asin()`**
```sql
UPDATE seller_skus SET
```
**`SellerRepository.normalize_tacos_random()`**  *(dynamic)*
```sql
UPDATE seller_skus SET tacos={expr} WHERE tenant_id=%s
```
**`SellerRepository.normalize_tacos_random()`**
```sql
UPDATE seller_skus SET tacos=
```
**`SellerRepository.link_channel()`**
```sql
UPDATE seller_skus SET internal_sku=%s, channel=%s WHERE tenant_id=%s AND asin=%s
```

### `settings_repo.py` — 2 statement(s)

**`SettingsRepository.get()`**
```sql
SELECT value FROM tenant_settings WHERE tenant_id=%s AND key=%s
```
**`SettingsRepository.set()`**
```sql
INSERT INTO tenant_settings(tenant_id,key,value) VALUES(%s,%s,%s)
               ON CONFLICT(tenant_id,key) DO UPDATE SET value=excluded.value
```

### `tenant_repo.py` — 10 statement(s)

**`TenantRepository.create()`**
```sql
INSERT INTO tenants(name,created_at,provisioned) VALUES(%s,%s,0)
```
**`TenantRepository.get()`**
```sql
SELECT * FROM tenants WHERE id=%s
```
**`TenantRepository.set_provisioned()`**
```sql
UPDATE tenants SET provisioned=1, data_mode=%s WHERE id=%s
```
**`TenantRepository.get_account_type()`**
```sql
SELECT account_type FROM tenants WHERE id=%s
```
**`TenantRepository.set_account_type()`**
```sql
UPDATE tenants SET account_type=%s WHERE id=%s
```
**`TenantRepository.delete()`**  *(dynamic)*
```sql
DELETE FROM {t} WHERE tenant_id=%s
```
**`TenantRepository.delete()`**
```sql
DELETE FROM tenants WHERE id=%s
```
**`TenantRepository.list_provisioned_ids()`**
```sql
SELECT id FROM tenants WHERE provisioned=1
```
**`TenantRepository.list_all()`**
```sql
SELECT id,name,account_type,provisioned,data_mode,created_at FROM tenants ORDER BY id
```
**`TenantRepository.reset_provisioning()`**
```sql
UPDATE tenants SET provisioned=0, data_mode=NULL WHERE id=%s
```

### `user_repo.py` — 7 statement(s)

**`UserRepository.get_by_email()`**
```sql
SELECT * FROM users WHERE email=%s
```
**`UserRepository.get_by_id()`**
```sql
SELECT * FROM users WHERE id=%s
```
**`UserRepository.count_members()`**
```sql
SELECT COUNT(*) c FROM users WHERE tenant_id=%s
```
**`UserRepository.create()`**
```sql
INSERT INTO users(tenant_id,email,pw_hash,pw_salt,created_at) VALUES(%s,%s,%s,%s,%s)
```
**`UserRepository.set_role()`**
```sql
UPDATE users SET role=%s WHERE id=%s
```
**`UserRepository.delete()`**
```sql
DELETE FROM users WHERE id=%s
```
**`UserRepository.list_members()`**
```sql
SELECT id,email,role,created_at FROM users WHERE tenant_id=%s ORDER BY created_at
```

---

## Part 3 — Helper queries in `db.py`

`db.py` owns the schema and connection; it also has a few small helper queries (auth lookups, account type, tenant data wipe).

**`init_db()`**
```sql
Build/upgrade the schema via Alembic (`alembic upgrade head`) — one mechanism for both SQLite
    and Postgres. The baseline is idempotent (CREATE TABLE IF NOT EXISTS), so this safely ADOPTS an
    existing pre-Alembic SQLite DB (baseline is a no-op on existing tables, then later migrations
    apply). Targets whatever dbengine.url() resolves to (live config.DB_PATH / DATABASE_URL).
```
**`wipe_tenant_data()`**  *(dynamic)*
```sql
DELETE FROM {t} WHERE tenant_id=%s
```

---

## Appendix

### Upsert conflict keys

`INSERT OR REPLACE/IGNORE` rewrites to `ON CONFLICT` on these keys (from `dbengine._CONFLICT_KEYS`):

| Table | Conflict key |
|---|---|
| `category_products` | `(tenant_id, segment, asin)` |
| `sourcing_list` | `(tenant_id, asin, segment)` |
| `seller_skus` | `(tenant_id, asin)` |
| `rules` | `(rule_id)` |
| `products` | `(tenant_id, internal_sku)` |
| `channel_listings` | `(tenant_id, channel, channel_id)` |
| `channels` | `(tenant_id, channel)` |
| `channel_economics` | `(tenant_id, internal_sku, channel)` |
| `keepa_snapshots` | `(tenant_id, asin, captured_at)` |
| `tierc_signals` | `(tenant_id, dedup_key)` |
| `seller_orders` | `(tenant_id, order_id)` |
| `card_research` | `(tenant_id, dedup_key)` |
| `card_why` | `(tenant_id, dedup_key)` |

### Other SQL-bearing files (not app queries)

- `realify/dbengine.py` — the dialect translator itself (placeholder/upsert/schema rewriting); no business queries.

- `realify/migrate_sqlite_to_pg.py` — the one-time SQLite→Postgres data copy: per-table `INSERT ... ON CONFLICT DO NOTHING`, sequence resets via `pg_get_serial_sequence` and `information_schema`, and row-count verification.

- `migrations/versions/` — Alembic baseline migration (creates the Part 1 schema on Postgres).

- `run.py` — a single `SELECT 1` used by `run.py doctor` as a connection health check.
