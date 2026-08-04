# Realify Research — Working Prototype (multi-tenant)

A multi-tenant app: users sign up, choose **synthesize** or **upload reports** (upload is the
fast-follow), and see the full insight feed on **their own isolated data**. Every data row is
scoped by `tenant_id`, resolved from the authenticated session — never from the client.

## Quick start

```bash
pip install fastapi uvicorn itsdangerous       # server + sessions
python run.py init                             # create the multi-tenant schema (run once)
python run.py demo                             # create demo@realify.ai / demo123 + synthetic data
python run.py serve                            # http://localhost:8000  (auth-gated, no pulls)
```

Open http://localhost:8000 → log in with **demo@realify.ai / demo123**, or sign up a new
account. In onboarding under **Synthesize**, choose either:
- **Use sample ASINs** — the bundled 44 Autofy ASINs (prototype-2 data), instant start.
- **Upload my ASIN list** — a CSV with `asin, cogs, category` (price optional); Realify
  synthesizes full economics/velocity/inventory from it. A template is downloadable in the UI.

Each account is fully isolated. (Real Seller Central / Shopify report upload is the fast-follow.)

**Account menu (top-right ⚙):** `reset` wipes all your data and returns you to onboarding;
`logout` signs out. This is what lets one account act as a real customer *or* a tester.

## Multi-tenancy & auth (Step 1)

- `users` + `tenants` tables; passwords hashed with PBKDF2 (stdlib, no native deps).
- Session cookie (Starlette `SessionMiddleware`); `tenant_id` comes only from the session.
- Every table carries `tenant_id`; every query is scoped; cross-tenant card IDs return
  "card not found". Verified with a two-user isolation test.
- **Ingestion seam** (`realify/ingest/`): `DataSource.provision(tenant_id)` — `SyntheticSource`
  now; report-file parsers drop in as new adapters later **without** schema/pipeline changes.

## Channel-aware foundation (Step 3)

- **Identity layer:** `products` (canonical, channel-agnostic SKU; COGS lives here) +
  `channel_listings` (one product → its ASIN / Shopify variant / etc., with `link_status`).
- **Channel dimension** + normalized fact tables for the 7 Amazon reports: `traffic`,
  `settlements`, `inventory`, `returns`, `storage_fees` (plus `orders`), each tagged `channel`.
  Synthetic Amazon data flows through all of them; Shopify/TikTok/eBay/Walmart adapters add
  rows the same way later — no schema change.
- **Reconciled row:** `GET /api/products` returns one row per product across channels
  (total units/revenue, blended margin, total inventory) — the cross-channel promise, computed.
- **Rules as data:** a default `rules` catalog + per-tenant `tenant_rule_settings` overrides.
  The **⚙ Rules** button (top-right) opens a settings drawer where a seller enables/disables
  rules and edits thresholds *for their account only*; Apply rebuilds their feed. Sellers tune
  thresholds, not logic; the server validates edits against each rule's declared bounds.

## Full rule catalog + coverage (Steps 5 & 4)

- **Rules as data (Step 5):** the consolidated 94-rule catalog is ported into the `rules`
  registry. 9 are the prototype's market/tier-C detectors (rich cards); the rest are
  **data-driven threshold rules** — each carries a condition (field, operator, tunable
  threshold) evaluated by one generic engine. All are listed and tunable in ⚙ Rules.
- **Synthetic coverage + shuffle (Step 4):** provisioning injects a spread of conditions
  so the catalog fires (coverage measured explicitly — see ⚙ Account → Test data, which
  shows "N/Total rules firing"). A **Resynthesize** control re-rolls which conditions apply:
  *reroll* (keep ASINs/orders), *full* (regenerate orders), *coverage* (one SKU per band to
  maximize rules per pass). Coverage logic runs on **synthetic data only** — real uploaded
  CSVs are never altered to hit a target.

## Fast onboarding (non-blocking)

Onboarding no longer blocks on slow work. `POST /api/onboard` kicks off a **background
job** and returns immediately; the browser polls `/api/onboard/status` for real staged
progress (loading catalog → channel layer → detecting insights → ready) behind a progress
bar + a rotating dad-jokes panel. The app **opens on the seller's own-data insights** as
soon as they're ready (seconds), then **live market data (Keepa/news/trends) backfills in
the background** with fail-fast per-source timeouts (`SOURCE_TIMEOUT`, default 8s) and a
consecutive-failure circuit breaker (`LIVE_FAIL_CIRCUIT`, default 3) so a stalling or
zero-returning live source can never hang onboarding. Card narratives are deterministic at
provision time (no per-card LLM calls); the richer LLM brief renders lazily on drill-down.
Order/settlement inserts are batched (`executemany`).

## Commands

| Command | What it does |
|---|---|
| `python run.py init` | Create the SQLite schema |
| `python run.py seed` | Load the synthetic seller data (`realify/seller_data.json`) |
| `python run.py pull` | Run all collectors once — **incremental**: skips any source pulled within the interval |
| `python run.py pull --force` | Force a pull (fetches the time-difference since the last watermark) |
| `python run.py pipeline` | Detect → generate → materialize cards |
| `python run.py feed` | Print the current feed (JSON) |
| `python run.py bootstrap` | One-shot: init + seed + pull + pipeline |
| `python run.py start` | Bootstrap, then **background scheduler every 4h** + FastAPI server on :8000 |

## How the scheduling & incremental logic works (the core of the design)

- **`pull_log`** records every collector run with the time window it covered.
- Before a pull, the collector reads its **last watermark** (`MAX(window_to)` of successful
  pulls for that source+scope) and fetches only data newer than it — *the difference in time*.
- A pull within `PULL_INTERVAL_HOURS` (default 4) is **skipped** unless `--force`.
- `start` runs everything once on boot, then re-pulls every 4h; each cycle is incremental,
  so unchanged sources do no work.
- Snapshots are **append-only** (`keepa_snapshots`, `competitor_offers`, `tierc_signals`),
  keyed so re-fetched overlapping history doesn't duplicate.

Proof (fixture): the first keepa pull covers a 30-day backfill window; a second pull
seconds later is `skipped`; a forced pull covers only `last_watermark → now`.

## Going live (substitute real sources)

Copy the env template, fill in your keys, and run the same commands — no shell exports needed:

```bash
cp .env.example .env
# edit .env:  MODE_KEEPA=live, KEEPA_KEY=..., ANTHROPIC_API_KEY=..., KEEPA_DOMAIN=IN
pip install keepa anthropic        # (add fastapi uvicorn for the server)
python run.py start
```

`config.py` loads `.env` automatically on import. Shell exports still override `.env`
if you want to change one value for a single run (e.g. `MODE_KEEPA=fixture python run.py pull`).

- Keepa + Anthropic only: set `MODE_KEEPA=live` and both keys; leave `MODE` unset so
  recalls/news/trends stay in fixture mode. `KEEPA_DOMAIN=IN` is required for amazon.in ASINs.
- L2 narratives (Claude) turn on whenever `ANTHROPIC_API_KEY` is present — independent of Keepa.
- To turn everything live at once, set `MODE=live` and provide the Tier-C keys/installs too.

- **Keepa** (`collectors/keepa_collector.py` → `fetch_live`): uses the `keepa` package,
  domain IN. `pip install keepa`.
- **Recalls** (`fetch_live`): CPSC REST (free); add BIS/openFDA/NHTSA endpoints alongside.
- **News** (`fetch_live`): NewsAPI `everything` endpoint (free dev tier).
- **Trends** (`fetch_live`): `pytrends` best-effort. `pip install pytrends`.
- **L2** (`pipeline/generate.py`): calls Claude when a key is set; otherwise the
  deterministic fallback writes the card. Numbers always come from the signal.

Each live path is isolated — switch one source to live and leave the rest fixture.

## Layout

```
run.py                      entrypoint / CLI
realify/
  config.py                 env-driven settings
  db.py                     schema + incremental watermark API
  seller.py                 synthetic-seller loader (CSV-ingestion target)
  seller_data.json          Step-1 synthetic data (44 real ASINs)
  collectors/
    base.py                 incremental + due-check + pull_log bookkeeping
    keepa_collector.py      market data (live keepa / fixture)
    tierc_collector.py      recalls / news / trends / social (live / fixture)
  pipeline/
    primitives.py           the 6 detection primitives
    detect.py               the 9 card-type detectors
    generate.py             L2 narrative (Claude / fallback)
    materialize.py          dedup + write cards + is_new
  scheduler.py              run-once / background 4h scheduler
  api.py                    feed / categories / summary / source-health reads
```

## Synthetic data (Step 1)

Only the seller's **own** data is synthetic. Two layers, both derived consistently:
- **SKU aggregates** (`seller_skus`) — 44 real Autofy ASINs with generated price/margin/
  inventory/velocity. Replaced in production by Seller Central CSV ingestion.
- **Order-level rows** (`seller_orders`) — generated *from* the SKU aggregates so they roll
  back up (units ≈ velocity). Includes a fee breakdown + settlement deposit per order, with
  two injected signals: ~6% short-paid orders (so settlement-reconciliation cases find real
  shortfalls) and recently-delivered orders without a review (so review-request finds real
  eligible IDs). Replaced in production by the 'All Orders' + 'Settlement' report ingestion.

Because of this layer, the **case/report** and **review_request** handlers run real queries
(real order IDs, computed shortfall amounts), not templated text — same fidelity as reprice.

## Seeing the UI

You only need to pull data when you want it refreshed. To just **look at the data you
already have** (no pulls, no Keepa tokens):

```bash
pip install fastapi uvicorn         # one-time, for the server
python run.py serve                 # serves existing realify.db on :8000 — NO pulls
```
Open **http://localhost:8000**.

Use `start` instead only when you want it to refresh: it pulls once on launch and then
every 4 hours, and serves the UI. `serve` is the everyday command; `start` is for a live,
self-refreshing instance.

- `python run.py serve` — UI + API from existing DB, no pulls (cheap, instant)
- `python run.py start` — pull now + every 4h + serve (spends Keepa tokens each cycle)
- `python run.py pull --force` then `serve` — refresh once, then just view

The page loads the live feed from the API (`/api/feed`, `/api/categories`). Opened directly
as a file (no server), it falls back to its built-in seeded data so it still renders.

## API (when running `start` or `serve`)

- `GET /api/feed?category=&family=&new_only=` → ranked cards
- `GET /api/categories` → category pulse rollup
- `GET /api/summary` → briefing counts + source health
- `GET /api/card/{id}/research` → level-2 drill-down (price/BSR chart, ranked real
  competitor SKUs via Keepa product-finder, search-trend depth, review themes, and an
  LLM decision brief). Lazy + cached per card, so it pulls deep data only on click.
- `POST /api/card/{id}/ask` `{ "question": "..." }` → grounded LLM follow-up.
- `POST /api/card/{id}/action` `{ "action": "reprice|ad_action|restock_task|listing_update|case_report|monitoring_ticket|review_request" }`
  → performs the no-SP-API task: returns a deep-link + pre-filled value/draft + a written
  explanation, and logs it. Omit "action" to use the card's primary handler.
- `POST /api/card/{id}/sourcing` `{ "picks": [...] }` → add competitor SKUs to the sourcing list.
- `POST /api/card/{id}/save_brief`, `/watch`, `/dismiss?done=` → research-native artifacts.
- `GET /api/card/{id}/clickout?kind=amazon|source|research` → returns a click-out URL (logged).
- `GET /api/log` → the explainability log (every task + its reasoning).
- `GET /api/sourcing`, `/api/sourcing/export` (CSV), `/api/watchlist` → saved artifacts.

**Explainability:** every action pops a modal explaining what it does, why, what it does NOT do
(it never writes to Amazon), the data used, and the deep-link to complete it in Seller Central.
Everything is recorded in the **Activity** panel (top-right) — Log / Sourcing / Watchlist tabs.

Point the HTML prototype at these endpoints (it currently ships with seeded data;
swap its `D`/`CATS` arrays for `fetch('/api/feed')` / `fetch('/api/categories')`).

## Notes & caveats

- Fixture data is for development; **fee schedules and any margin numbers are approximate**
  — confirm current amazon.in rates before relying on them.
- `start` serves on `0.0.0.0:8000`; run it on your machine where Keepa/Anthropic are reachable.
- Two bootstrap pull cycles run 1.1s apart so delta-based cards have snapshot history;
  in production the 4h cadence provides this naturally.
