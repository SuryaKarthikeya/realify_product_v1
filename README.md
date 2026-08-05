# Realify

Realify is a multi-tenant Amazon seller-analytics product. Sellers sign up, onboard by either
**synthesizing** sample data or **uploading their own Seller Central / Ads reports**, and get a
workspace of KPI cards (Revenue, Margin, Cash, Inventory, Ads) plus an insight feed — all scoped
to their own isolated data (`tenant_id` is resolved from the session, never trusted from the client).

The repository holds two applications:

| Folder | What it is | Stack |
|---|---|---|
| [`realify-mc/`](realify-mc) | Backend API + data pipeline | Python, FastAPI, SQLite (Postgres-ready) |
| [`realifyAi/`](realifyAi) | Frontend single-page app | React + Vite + Tailwind |

The frontend talks to the backend over `/api/*`; in local dev Vite proxies those calls to the
backend so the browser sees one origin (no CORS setup needed locally).

---

## Prerequisites

- **Python 3.11+** (backend)
- **Node.js 18+** and **npm** (frontend)
- No database server needed for local dev — the backend defaults to a bundled SQLite file
  (`realify-mc/realify_mc.db`). PostgreSQL is only needed for production (see below).

---

## Quick start (local dev)

Run the backend and frontend in **two separate terminals**.

### 1. Backend — `realify-mc/`

```bash
cd realify-mc
python -m venv .venv && source .venv/bin/activate      # optional but recommended
pip install -r requirements.txt

python run.py init        # create the schema + rules catalog (run once)
python run.py demo        # create a demo account: demo@realify.ai / demo123
python run.py serve       # start the API at http://localhost:8001
```

The backend now serves on **http://localhost:8001** (configurable via `REALIFY_PORT`).

### 2. Frontend — `realifyAi/`

```bash
cd realifyAi
npm install
npm run dev               # opens http://localhost:5173
```

Vite runs on **http://localhost:5173** and proxies every `/api/*` request to the backend on
`:8001`. Open the browser tab it launches and log in with **demo@realify.ai / demo123**, or sign up.

---

## Onboarding & data

After logging in, each account picks how to populate its workspace:

- **Synthesize** — start from bundled sample ASINs, or upload a simple `asin, cogs, category` list
  and Realify synthesizes full economics/velocity/inventory from it.
- **Upload reports** — upload real Amazon reports. The pipeline auto-detects each report type by
  its column headers and parses it into the fact tables the KPIs read from. Supported reports include:
  - **Unified/Custom Transaction** → orders, settlements, refunds (Revenue, Margin, Cash)
  - **COGS** (`SKU, Unit Price`) → per-SKU cost (Margin, Inventory value)
  - **Sponsored Products / Ads** → ad spend & performance (Ad spend, ROAS, CPC, CPA, CVR)
  - **Storage Fee** → on-hand inventory & storage fees (Inventory, Days of Cover)
  - **Business Report** → Buy Box %, conversion
  - **Fee Preview** → estimated referral/FBA fees

Every account is fully isolated. The top-right account menu (⚙) has **reset** (wipe your data and
return to onboarding) and **logout** — so one account can act as a real customer *or* a tester.

> Note: uploaded report values are computed at **ingest time**. If you change ingest logic, existing
> accounts must **re-upload** the affected report for the new values to take effect.

---

## Backend commands (`python run.py <cmd>`)

| Command | What it does |
|---|---|
| `init` | Create the DB schema + seed the rules catalog (run once per fresh DB) |
| `demo` | Create/reset `demo@realify.ai / demo123` |
| `serve` | Serve the UI + API from the existing DB (auth-gated, no background pulls) |
| `start` | `serve` **plus** the background 4-hour scheduler across tenants |
| `status` | Print the data-source config panel |
| `doctor` | Preflight check (DB config, connection, admin key) without starting the app |
| `migrate-pg` | Copy data from SQLite → Postgres (`--dry-run` to preview) |

---

## Frontend commands (`npm run <cmd>`)

| Command | What it does |
|---|---|
| `dev` | Start the Vite dev server (with API proxy) and open the browser |
| `build` | Production build to `dist/` |
| `preview` | Serve the production build locally |
| `lint` | Run ESLint |

---

## Tests (backend)

```bash
cd realify-mc
python -m pytest tests/ -q                 # full suite (SQLite)
python run.py doctor --postgres            # run the suite against a throwaway Postgres (needs Docker)
```

---

## Configuration (backend env vars)

Set these in the backend environment (e.g. a `.env` loaded by your shell) as needed:

| Variable | Default | Purpose |
|---|---|---|
| `REALIFY_PORT` | `8001` | API server port |
| `DATABASE_URL` | `sqlite:///…/realify_mc.db` | DB connection; set a `postgresql+psycopg://…` URL for Postgres |
| `APP_URL` | – | Public frontend origin (CORS + Stripe redirects) in deployed environments |
| `REALIFY_ADMIN_KEY` | – | Strong key that unlocks the admin/operator endpoints (fail-closed if unset) |

For production, point `DATABASE_URL` at Postgres, run `python run.py doctor` to validate, then
`python run.py init` and `python run.py migrate-pg` to move data over.

---

## Project structure

```
.
├── realify-mc/            # Backend
│   ├── run.py             # entrypoint (init / demo / serve / start / doctor / migrate-pg)
│   ├── realify/
│   │   ├── api.py         # KPI computation (Workspace cards + per-domain substats)
│   │   ├── ingest/        # report detection + parsing → fact tables
│   │   ├── repositories/  # DB access layer
│   │   └── routers/       # FastAPI routes
│   ├── migrations/        # Alembic migrations
│   ├── tests/
│   └── requirements.txt
└── realifyAi/             # Frontend
    ├── src/
    │   └── features/workspace/pages/WorkspacePage.jsx   # KPI card rendering
    ├── vite.config.js     # dev server + /api proxy → :8001
    └── package.json
```
