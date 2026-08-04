# Data & Seeding — Where the SQL lives and how to seed a database

A companion to `ONBOARDING.md`. That doc gets you cloned, configured, and running;
this one answers two specific questions:

1. **Where is all the SQL in this app?**
2. **How do I seed a database so I have data to work with?**

Read `ONBOARDING.md` first if you haven't — it covers prerequisites, the `.env`, the
SQLite-local / Postgres-prod split, and the deploy flow.

---

## 1. Where the SQL lives

The app keeps SQL in **one** layer on purpose. If you're looking for a query, changing
one, or adding a table, you only ever need these locations:

| Location | What's there |
|---|---|
| **`realify/repositories/`** | **All data SQL.** Every `SELECT` / `INSERT` / `UPDATE` / `DELETE` for tenant data. 18 repository modules. This is the only place business queries live. |
| **`realify/db.py`** | **The schema.** All 34 `CREATE TABLE` statements, plus `connect()` and small helpers. The DDL home. |
| **`realify/dbengine.py`** | **The SQLite ↔ Postgres dialect seam.** Not business queries — placeholder rewriting (`?` → `%s`), `INSERT OR REPLACE/IGNORE` → `ON CONFLICT`, and `schema_to_postgres()` which translates the `db.py` DDL for Postgres. (It also contains a `CREATE TABLE` reference — that's the translator, not a second schema.) |
| **`migrations/versions/`** | **Alembic baseline migration** — the versioned schema used on Postgres (`alembic upgrade head`). |
| **`tests/`** | SQL only in fixtures/test setup. |
| **`run.py` (one line)** | A single `SELECT 1` — the `doctor` health-check ping. Not a data query. |

**The invariant:** there is **no inline data SQL anywhere outside `repositories/`.** Modules
like `seller.py`, `channels.py`, `pipeline/`, and `ingest/` do business logic and call into
repositories — they never write SQL directly. If you find raw SQL outside `repositories/`
(other than the schema in `db.py` and the dialect translator in `dbengine.py`), that's a bug
against this rule.

### The repository modules

All under `realify/repositories/`. `base.py` is the shared base class; the rest are grouped
by domain:

| Module | Domain |
|---|---|
| `tenant_repo.py` | Tenants (orgs) |
| `user_repo.py` | Users / auth records |
| `invite_repo.py` | Team / collaborator invites |
| `seller_repo.py` | Seller SKUs, ASINs, economics |
| `catalog_repo.py` | Product / rule catalog |
| `order_repo.py` | Orders |
| `metrics_repo.py` | Metrics, velocity |
| `fact_repos.py` | Fact tables (batch inserts) |
| `market_repo.py` | Market snapshots & offers (Keepa) |
| `channel_repo.py` | Multichannel data |
| `card_repo.py` | Insight cards |
| `rules_repo.py` | Rule definitions / state |
| `analytics_repo.py` | Analytics / aggregate reads |
| `settings_repo.py` | Per-tenant settings |
| `action_repo.py` | Action log, pipeline run tracking |
| `pull_repo.py` | Collector pull log (source health) |
| `job_repo.py` | Background-job records (TaskRunner) |

### How a query reaches the database

```
route / business module  →  Repository method (the SQL)  →  db.connect()
                                                              │
                                          dbengine.py decides dialect:
                                          SQLite (local)  or  Postgres (prod)
```

Every query is tenant-scoped through `deps.require_tenant()` / `current()` — `tenant_id` is
resolved server-side, never taken from the client. So when you write a new repository method,
it should take `tenant_id` and filter on it like the others.

---

## 2. How to seed a database

### The important thing first

**There is no "run a SQL seed file" step. Seeding goes through the synth pipeline, not raw SQL.**

`python3 run.py demo` deliberately seeds **no data** — it only creates the schema, the rules
catalog, and the demo account. It prints *"No data provisioned yet — by design."* Data only
lands when **synthetic provisioning** runs, scoped to a tenant, and that's triggered by a
choice in the app (so no Keepa / market pulls fire until a human opts in).

The path under the hood:

```
SyntheticSource (realify/ingest/synthetic.py)
   → load_seller_data() + generate_orders()  (realify/seller.py)
      → repositories write the rows
```

- Bundled seed catalog: `realify/seller_data.json` and `realify/catalog94.json` (~50 ASINs,
  the "Autofy" demo set). Used when `SyntheticSource(seed_skus=None)`.
- Uploaded ASIN list: parsed by `realify/ingest/seed.py` (`parse_seed_csv` →
  `expand_minimal_seed`), passed as `SyntheticSource(seed_skus=[...])`.

### Seed a local dev database (the normal path)

Local development uses **SQLite** — zero config. **Do not set `DATABASE_URL` locally**
(that's prod Postgres only). From your clone:

```bash
cd realify-mc
python3 run.py demo     # init schema + rules catalog, create demo@realify.ai / demo123
python3 run.py serve    # start the app (auth-gated, no background pulls)
```

Then in the browser:

1. Log in as **`demo@realify.ai`** / **`demo123`**
2. On the onboarding screen, choose **"Use demo ASINs"**

That click is what triggers `SyntheticSource(seed_skus=None)` to provision the bundled
catalog plus synthetic orders and rule-tripping conditions. After it finishes, the feed,
KPIs, and cards are populated.

### Seed with your own ASIN list instead

Same flow, but pick **"Upload my ASINs"** and supply a CSV. Columns (case-insensitive,
any order):

| Column | Required? | Notes |
|---|---|---|
| `asin` | yes | the ASIN |
| `cogs` | yes | cost of goods (used to synthesize economics; rows with cogs ≤ 0 are skipped) |
| `category` | yes | defaults to "Other Accessories" if blank |
| `price` | no | optional |
| `title` | no | optional |

`parse_seed_csv` is defensive — it skips blank/malformed rows rather than failing.

### Things to know

- **Use `run.py demo`, not `run.py start`.** `start` launches the background scheduler and
  does live pulls; `demo` + `serve` keeps it auth-gated with no pulls — correct for local dev.
- **Re-running `run.py demo` resets the demo tenant** (`wipe_tenant_data`) instead of
  duplicating — safe to run repeatedly.
- **Local stays on SQLite.** `init` creates the schema at `config.DB_PATH` (a local file).
  Leaving `DATABASE_URL` unset is what selects SQLite — see `ONBOARDING.md` § "The data
  engine" and the `dbengine.py` seam.
- **Tester vs customer accounts:** the demo account is a *tester* — collectors run in
  **fixture** (synthetic) mode for testers regardless of the global mode, so you get a full
  set of synthetic market signals without any live API. Customer accounts pull live.
- **Verifying it worked:** `python3 run.py doctor` confirms the dialect and DB connection;
  the app's feed shows cards once provisioning completes.

### Optional: a headless one-shot seed

The flow above needs a click in the onboarding screen (by design). If you want a *no-UI*
seed — e.g. for CI or a scripted reset — ask the maintainer to add a small
`run.py seed-demo` command that calls `SyntheticSource(None).provision(tid)` directly. It
doesn't exist yet; it's a few lines if it's useful to you.

---

## Quick reference

```
Find a query        →  realify/repositories/<domain>_repo.py
Change the schema   →  realify/db.py  (CREATE TABLE)  +  a new Alembic migration
Dialect issues      →  realify/dbengine.py
Seed a dev DB       →  python3 run.py demo  →  serve  →  log in demo@realify.ai/demo123  →  "Use demo ASINs"
Seed your own ASINs →  same, choose "Upload my ASINs", CSV: asin,cogs,category[,price,title]
Health check        →  python3 run.py doctor
```
