# Onboarding — Building on Realify

For a new engineer who has clone access to the repo. By the end you'll have the app running locally, the tests passing, and a clear map of where things live and how to ship a change. Budget about 20 minutes.

This guide is **getting started**. For *adding a component* (a marketplace connector, auth provider, billing provider, or detector) without editing core, read `docs/EXTENDING.md` next — it's the contract you build against.

---

## What Realify is, in one breath

An AI merchandising and operations intelligence platform for Amazon and marketplace sellers. It turns market and seller data into ranked, explained **insight cards** (pricing, inventory, advertising). One architectural rule governs everything and you should internalize it before writing code:

> **L1 decides, the model informs, L2 phrases.** Deterministic L1 detectors compute every number and every decision. The model layer only *informs* (confidence-gated, never overrides). The L2 LLM layer only *phrases* the card text — it never chooses or changes a number. If you ever find a number originating from the model or the LLM, that's a bug.

A second rule that is absolute: **Realify never scrapes Amazon.** Competitive and historical data comes only from Keepa's official API and other official sources.

Two account modes shape how data arrives, and you'll meet both in the code: a **tester** account (`tenants.data_mode = synthetic`) runs on a synthesized demo catalog so every feature is explorable, while a **customer** account (`data_mode = uploaded`) has *no synthesis* — it is built entirely from the seller's own uploaded Amazon reports (Monthly Unified Transaction, COGS, fee-preview, Sponsored Products, Business Report) through the **report-aware ingestion engine** (`realify/ingest/report_ingest.py` → `report_writer.py`). Destructive/reseed operations are server-disabled for customers so real data is never overwritten.

---

## Prerequisites

- **Python 3.12** (the build and production target). 3.13+ works for local dev; if you use a system Python that blocks `pip`, either use a virtualenv (recommended) or add `--break-system-packages`.
- **git**, with access to the repo.
- **Docker** — optional for local dev, but needed for the pre-deploy Postgres smoke (below) and to mirror production. You do **not** need it for everyday work.
- No external API keys are required to run locally — the app defaults to **fixture mode** (seeded data, no live calls).

---

## 1. Get the code and a clean environment

```bash
git clone <your-repo-url> realify-mc
cd realify-mc
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest        # test runner (dev-only, not in requirements.txt)
```

## 2. Configure

For local development you need **almost nothing** — the defaults are built for a zero-config start. Create a `.env` in the repo root only if you want to override something:

```bash
# .env — all optional for local dev
MODE=fixture                 # default; seeded data, no live API calls
# REALIFY_DB=./realify_mc.db  # local SQLite file (default is fine)
# DATABASE_URL=...            # LEAVE UNSET locally → you get SQLite automatically
# REALIFY_ADMIN_KEY=...       # only needed to open the /ops console
# SESSION_SECRET=...          # defaults to a dev value locally; MUST be set in prod
```

The knobs you'll actually touch:

| Variable | Default | What it does |
|---|---|---|
| `MODE` | `fixture` | `fixture` = seeded data, no network. `live` enables real collectors (needs keys). Per-source overrides exist: `MODE_KEEPA`, `MODE_NEWS`, etc. |
| `DATABASE_URL` | *(unset)* | **Unset → SQLite** (local/test). A `postgresql+psycopg://…` URL → Postgres (production). This single variable is the only difference between local and prod. |
| `REALIFY_DB` | `./realify_mc.db` | Path to the local SQLite file (used only when `DATABASE_URL` is unset). |
| `REALIFY_ADMIN_KEY` | *(unset → admin locked)* | The key for the `/ops` operator console. Unset or a weak value = admin endpoints are denied (fail closed). |
| `SESSION_SECRET` | dev placeholder | Signs the session cookie. Fine to leave default locally; **must** be a real secret in production. |
| `KEEPA_KEY`, `ANTHROPIC_API_KEY` | empty | Only needed in `live` mode. Leave empty for fixture work. |

> The golden local rule: **do not put a production `DATABASE_URL` in your local `.env`.** That would point your machine's tests at the live database. Local stays on SQLite simply by leaving it unset.

## 3. First run

```bash
python run.py init     # create schema + seed the rules catalog (runs Alembic migrations)
python run.py demo     # OPTIONAL: also creates a demo org so the app isn't empty
python run.py serve    # start the dev server; prints the local URL
```

`run.py demo` seeds a login you can use immediately:

```
email:    demo@realify.ai
password: demo123
```

Open the URL `serve` printed, log in with the demo account, and click through a few insight cards to see the system end-to-end. (`serve` is the dev server — auth-gated, no background pulls or scheduler. `start` is the production path that also runs the scheduler.)

Before you ever trust an environment, run the preflight:

```bash
python run.py doctor
# dialect: sqlite | DATABASE_URL shape: OK | DB connection: OK | admin key: ... | ALL CHECKS PASSED
```

`doctor` is your safety check on both sides — locally it should say `dialect: sqlite`; in production (via `docker exec`) it must say `dialect: postgresql`.

## 4. Run the tests

```bash
python -m pytest tests/ -q
```

The suite runs on SQLite — fast, hermetic, no network. It's also the deploy gate: a change isn't ready until the suite is green. A few tests are **contract tests** that exist to stop regressions you should know about: the card-JSON shape (the frozen partner contract at `/api/v1`), the upsert-key guard (every Postgres `ON CONFLICT` table must be mapped), and a 400-line-per-file cap (keeps modules from drifting back toward a monolith).

---

## Project layout

```
run.py                  entrypoint + CLI (init / demo / serve / start / doctor / migrate-pg)
realify/
  config.py             typed, immutable Settings read from the environment
  dbengine.py           THE database seam — SQLite vs Postgres, URL validation, dialect
  db.py                 schema, connect(), init_db() (runs Alembic)
  routers/              thin FastAPI routers — NO SQL, NO business logic
    deps.py             the identity seam: current() / require_tenant() / require_admin()
  api.py                service layer the routers call
  repositories/         the ONLY place that touches the DB (all tenant-scoped)
  domain/               L1 detectors + deterministic math: economics.py, cmaa.py (Profit & Ads),
                        and the SIMULATE engine (sim_common + simulate + sim_intel + sim_{inventory,
                        flow,market}) — scenario projections dispatched by detector
  rules.py, models.py   rule catalog + the model-readiness boundary (L1 decides, model informs)
  ingest/               report-aware ingestion — recognizer (header-fingerprint classifier),
                        report_ingest/report_writer (Amazon), extractors_shopify + shopify_commit
                        (Shopify → seller_skus), crosswalk + normalize_finance (SKU unify, MCF pool,
                        booked/settled), rawpath (raw-path detection + reconcile)
  topology.py, nodegraph.py, topology_model.py   cross-channel onboarding as DATA: source-aware
                        manifest, wizard node graph + emit map, Resolved<T> / flags / TenantTopology
  pipeline/             checklist / reconcile / completeness derivation (+ card materialize)
  collectors/           data source connectors (Keepa, recalls, news, trends)
  scheduler.py          background pulls
  runner.py             TaskRunner seam (background work)
migrations/             Alembic migrations
tests/                  pytest suite (runs on SQLite)
docs/                   this guide, EXTENDING, the architecture doc, integration guide, logbook
```

The dependency direction is strict and one-way: **routers → services → domain → repositories → db**. SQL lives *only* in `repositories/`. Tenant identity is resolved server-side in `deps.current()` and is **never** taken from a client-supplied value.

## The data engine: SQLite locally, Postgres in production

This is the one thing that surprises people. The same code and the same container image run on **both** engines — the choice is made entirely by whether `DATABASE_URL` names a Postgres database. SQLite is kept deliberately as the **local and test engine** (fast, no setup); Postgres on RDS is production. The repositories write plain SQL once; a thin connection wrapper makes a Postgres connection behave like the SQLite API the repos expect, so neither engine needs engine-specific query code.

**The catch:** SQLite and Postgres aren't byte-identical (upserts, sequences, a few type quirks). For everyday work, the SQLite test run is enough. **When you change anything database-shaped** (a repository, a migration, `dbengine`), run the full suite against a real Postgres first — one command does the whole dance (spin up a throwaway Postgres in Docker, run the suite against it, tear it down):

Write **portable SQL** in repositories: no SQLite-only constructs. The ones that have bitten us are `SUM(bool_expr)` (Postgres needs `SUM(CASE WHEN … THEN 1 ELSE 0 END)`), `date('now', ?)` (compute the date in Python and pass an ISO string), and selecting a non-aggregated column that isn't in `GROUP BY` (SQLite tolerates it, Postgres rejects it). These pass the SQLite suite and only fail on Postgres — which is exactly why the PG smoke below is the gate for DB-shaped changes.

```bash
make smoke-pg            # equivalently: python run.py doctor --postgres  (requires Docker)
```

If you'd rather drive it by hand (e.g. to keep the database up and poke at it):

```bash
docker run -d --name pg-local -e POSTGRES_PASSWORD=local -e POSTGRES_DB=realify -p 5432:5432 postgres:18
DATABASE_URL="postgresql+psycopg://postgres:local@localhost:5432/realify" python run.py doctor
DATABASE_URL="postgresql+psycopg://postgres:local@localhost:5432/realify" python -m pytest tests/ -q
docker rm -f pg-local      # tear down when done
```

## Scenario projections (SIMULATE) — the three-plane rule, made literal

The clearest example of "L1 decides, L2 phrases, the client renders" in the codebase is **SIMULATE** (`domain/sim_*`, `POST /cmaa/simulate`). A "Simulate" button on any Profit & Ads row or Intelligence card projects that recommendation forward — a 30/60/90-day scenario, what could go wrong, and a monitoring plan — as a **deterministic projection, never a prediction**. The one rule to keep: **every projected number = a current L1 value × a stated, editable assumption**, emitted as an `explain.part` (formula + inputs + result) that the client renders *verbatim* — the client never re-computes a formatted value. Targets default to the tenant's own detector threshold ("your margin floor / cover line / TACoS ceiling"); a missing input degrades to an honest "can't simulate" rather than a fabricated number; a weak base is flagged `sim_quality:"degraded"`. One endpoint serves both surfaces (`{sku}` or `{card_id}`), rebuilding the row server-side. To add a model, write one function returning the shared Simulation shape and register it by detector id in `sim_intel.py` — mirror an existing model (`sim_flow.returns_reduction` is a compact template) and keep each group file under the 400-line cap. The `range`/`explain` band is the model-readiness seam: a model's confidence interval will later populate it with no client change.

## Shipping a change — the deploy flow

The repo follows a fixed three-step deploy discipline; mirror it:

1. **Local + test** — make the change, run `python -m pytest tests/ -q` (green), eyeball with `run.py serve`. For DB changes, also run the local-Postgres smoke above.
2. **Commit** — push to the repo.
3. **Deploy** — on the server: pull, rebuild, restart, then **`docker exec realify python run.py doctor`** must show `dialect: postgresql` and all green before you trust it.

Standing rules to internalize:

- **No SQL outside `repositories/`.** If you're writing SQL in a router or service, stop.
- **Never choose the tenant.** The platform injects an already-tenant-scoped context via `deps`.
- **L1 decides numbers; the model informs; L2 only phrases.**
- **Never scrape Amazon** — official APIs (Keepa) only.
- **400-line file cap** is test-enforced; if you're growing a file past it, extract.
- **`run.py doctor` is the gate** — before and after every deploy.

## Cross-channel onboarding (Shopify) — two paths, one pipeline

A seller connects Shopify alongside Amazon, unified at the **SKU level**, through two entry paths that converge on one pipeline (spec-locked). The **raw path** (default) is the existing drag-drop uploader — a header-fingerprint **recognizer** (`ingest/recognizer.py`) classifies each file, and Shopify types are just new rows in the **source-aware manifest** (`topology.py`). The **guided wizard** (optional) runs a thin interview (`nodegraph.py`) that resolves to a `TenantTopology` + a personalized checklist + a per-goal completeness preview (`/api/wizard/resolve`), then hands back to the same uploader pre-armed.

The invariants to internalize: **rules-as-data** (adding a channel/partner = new manifest + node-graph rows, no branch); **detection wins the number** — `Resolved<T>` (`topology_model.py`) resolves stated-vs-detected, and a reconcile prompt only flips provenance on user confirm; **dedup is record-level** (upsert on `natural_keys`, so re-exports never double-count); and the two trust-critical financial rules (`normalize_finance.py`) — **MCF inventory is one shared FBA pool** (never summed with Shopify stock; margin stays partial until the Amazon-side MCF fee arrives) and **booked (`SHOP_ORDERS`) vs settled (`SHOP_PAYOUTS`) coexist**. To add a channel: add manifest rows (+ Shopify-style fingerprints), map node-graph emits, and — if it commits data — an extractor + a `shopify_commit`-style writer. All modules stay ≤400 lines; the Amazon flow is behavior-preserving. The cross-channel *number merge* per canonical SKU (combining Amazon+Shopify revenue) is deliberately deferred to `channel_economics`; today a mapped SKU is linked in the crosswalk without touching Amazon economics.

## The agency console (Realify for Agencies)

A second product lives in the same app under `realify/agency/` (domain), `realify/routers/agency_*.py` (routes), `realify/pdp/` (policy), and `realify/agency_jobs.py` (jobs): an **agency operates N brand-accounts under a revocable envelope**; effective capability = `intersection(envelope, grant)` via the single pure PDP `realify.pdp.decide()`. It is **Postgres-only** and gated behind the `AGENCY_CONSOLE` env flag (`off` ⇒ agency routes 404). It is live in production; the seller product is untouched for direct customers.

**Running it locally.** The console needs Postgres + RLS, so there's a Docker-free brew harness:

```bash
export AGENCY_CONSOLE=on
make test-agency          # spins ephemeral PG16 + PgBouncer (tools/agency_harness.sh), runs tests/agency/
```

Things to internalize before you touch it:

- **RLS is FORCED and no runtime role bypasses it.** 14 brand-scoped tables enforce `tenant_id = ANY(current_brand_ids())`, read from the transaction-local GUC `app.brand_ids` (set per request via `set_config(..., true)` — PgBouncer transaction-safe). Prod runs as `realify_app` (NOSUPERUSER/NOBYPASSRLS). **The test harness owner (`realify_owner`) IS a superuser and bypasses RLS — so a route that forgets `tenancy.set_brand_scope(...)` passes in tests but 500s in prod.** Exercise RLS-sensitive paths through the pooler (`realify_app`) or verify live. A user reads their own grants/approvals via narrow GUC-keyed self-read policies (migrations 0027/0029), never a bypass.
- **The action loop.** Work-queue item → `approvals.propose` → maker-checker (below threshold self-approves; at/above needs a distinct checker) or brand co-sign (derived from the engagement; emails a signed deep link; silence never executes) → on *approved*, `execution.execute_approval` writes to the **in-process mock marketplace** (`realify/agency/mock_marketplace.py` — there is no real marketplace client) with TOCTOU re-check, idempotency, token buckets, canary/rollback, and per-item Undo. Everything is ledgered (per-brand hash chain, AES-GCM payloads, crypto-shred).
- **Deploy caveat (critical).** Migrations must be applied as **`realify_admin`** in a one-shot BEFORE recreating the container — the runtime `realify_app` can't run DDL. And any one-shot that touches the ledger must pass `--env-file .env` so `MASTER_KEK` matches, or brand keys wrap under the dev KEK.
- **Money is honest.** Execution is mock-only, ROI is *projected* (not measured), Stripe is test-mode, and the report **factuality gate** blocks any number the engine didn't emit. See `docs/WIRING_CENSUS.md` for what's wired vs declared.

The full design is in the architecture doc's **Addendum 2** (`/ops/architecture`).

## Where to go next

- **`docs/EXTENDING.md`** — how to add a connector / auth / billing / detector against the interfaces, without editing core. This is your main reference once you start building.
- **Architecture doc** (`/ops/architecture`, or `docs/Realify-Architecture.html`) — the three-plane design, data flow, schema, tenancy, the data-engine seam, and the full libraries table.
- **Integration guide** (`/ops/integration`) — the per-team seams, contracts, and invariants (conversational, competitive-data, front-end, ML, identity, real-time, advertising, payments, agents).
- **Engineering logbook** (`/ops/logbook`) — numbered build history and the reasoning behind decisions.
- **Formulas reference** (`/ops/formulas`) — every deterministic L1 calculation and the policy for changing one.

Welcome aboard.
