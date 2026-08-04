# Realify — Integration Guide for Partner Teams

**Audience:** the nine teams building alongside the core platform —
(1) the **Conversational Interface** team, (2) the **Competitive Data** ingestion team,
(3) the **Front-end / Design** team, (4) the **ML / Model** team building and deploying
predictive models, (5) the **Identity / OAuth** team building sign-in on Ory Kratos +
Google OIDC, (6) the **Real-time / Events** team streaming data in over WebSockets and
pushing live updates to the UI, (7) the **Advertising** team building ad-efficiency signals
(the #004 ad spec), (8) the **Payments &amp; Entitlements** team building plans, billing, and
rate limiting, and (9) the **Agent Platform** team making Realify consumable by autonomous
agents (and building agents on top of it).

**Purpose:** describe the stable seams you build against, the contracts at each seam, the
invariants you must not break, and what is still moving underneath you (and when it settles).
The short version: *the platform owns decisions and the numbers behind them; you plug into a
boundary — you do not reach across it.*

> This document reflects the codebase as of the #005 Phase-1 refactor and the July-2026 builds that
> followed it: the router split (`realify/routers/`, `/api/v1`, the `deps.py` identity seam), the
> completed repository layer, **PostgreSQL live in production on RDS** (SQLite remains the local/test
> engine), the **report-aware ingestion engine** (seller reports → own-data), and the **CMAA
> "Profit & Ads" surface with deterministic, explainable recommended actions**. Where a contract is
> not yet frozen, it says so and points to the workstream that freezes it. If something here
> disagrees with the code, the code wins — tell us and we will fix the doc.

---

## 1. The system in sixty seconds

Realify turns a seller's own data plus market data into a ranked feed of **decision cards**.
Three planes, in strict order, and the order is the whole product:

1. **Decision plane (L1).** Deterministic detectors decide *whether there is an issue and how
   big it is*. Detectors are **rules-as-data** (rows in the `rules` table), not code. The number
   on a card — the exposure, the gap, the recoverable rupees — comes from here and only here.
2. **Model plane.** Optional models *inform* a decision (e.g. a forecast, a confidence). They are
   **confidence-gated and never override L1.** A low-confidence model output changes nothing.
3. **Phrasing plane (L2).** An LLM *phrases* a decision into readable language. It never invents
   a figure, never changes a verdict. It is a writer, not a judge.

Data flows one direction:

```
 sources ──▶ repositories ──▶ detectors (L1, rules-as-data) ──▶ model (gated) ──▶ phrasing (L2)
 (Keepa,        (the only           │                                                   │
  reports,       DB boundary)       └────────────── cards ──────────────────────────────┘
  competitive)                                        │
                                                  api / service layer ──▶ UI
```

Two facts that shape every integration:

- **Tenant isolation is universal.** Every domain row carries `tenant_id`; every repository
  method is tenant-scoped; one person = one org (`users.email` is globally unique). Nothing you
  build may read or write across tenants. (Postgres row-level security will *enforce* this in
  workstream 1d; until then it is a discipline, so honour it now.)
- **Graceful degradation is a feature.** A detector comparison against a missing value returns
  *false*, which produces **no card** — never a wrong one. If your data isn't there yet, the
  honest outcome is silence, not a guess. Preserve that.

**Compliance, non-negotiable:** we never scrape Amazon. Data comes from Keepa and official APIs
only. Any new source inherits this rule (see §4, Team 2).

---

## 2. The seams at a glance

| Team | Seam you integrate at | Contract | Stability today |
|---|---|---|---|
| Conversational interface | The **read API / service layer** + the **card schema** | HTTP JSON (`/api/*`) and/or in-process `api.py` functions; `research.ask_card` for Q&A | API surface being formalized + versioned in **1a/1f**; card schema stable, soon frozen by contract test |
| Competitive data | The **DataSource (Collector) contract** + a **repository** + **rules-as-data** | Subclass `Collector`, persist via a repo, register in `scheduler.collectors()`, add rule rows | Collector contract stable today; hardened + typed in **1e** |
| Front-end / design | The **card schema** + **presentation hints** + the **action sub-API** | Card JSON with `surface` / `group` / `severity` / `action_kind`; `POST /api/card/{id}/{action}` | JSON stable; presentation is yours end to end |
| ML / model | The **model (prediction) contract** — the Model plane | Implement `predict(con, tenant_id, asin, detector=None)`, declare `covers`, register in `models.REGISTRY`; output is confidence-gated and informs only | Interface stable today; serving/versioning/offline-mode formalized in **1e** |
| Identity / OAuth | The **authentication seam** — Kratos + Google OIDC in front of `deps.py` | Kratos owns authN (login, OIDC, sessions); the app maps a *verified* Kratos identity → Realify user → tenant inside one dependency; tenant_id never from a client claim | Hand-rolled today; the pluggable identity seam is built in **1a/1f**, the Kratos cutover is its own auth workstream |
| Real-time / events | Inbound: a **streaming source** that persists via a repo. Outbound: a **tenant-scoped event channel** the UI subscribes to | Inbound data still lands through a repository → detectors → cards (push instead of poll); outbound publishes card/metric deltas on a WS/SSE channel, authenticated per tenant | New surface — none today (HTTP + 4h batch). Needs a pub/sub backplane + event-driven pipeline; its own workstream after the Phase-1 core |
| Advertising (#004) | The **rules-as-data + detector** seam + an **ad-report source** | New ad detectors (TACoS/ACoS/wasted-spend) as rule rows in the existing "Ads" group; ad data lands via a collector/report like any other source | Skeleton exists today (the `tacos` detector + `ad_cost_unit`); the #004 spec extends it — no new architecture |
| Payments &amp; entitlements | A **plan catalog** (rules-as-data) + an **entitlements/quota dependency** in `deps.py` + a **billing webhook** | Plans/limits are data rows; `require_quota()` enforces at the seam; Stripe is mirrored via signed webhook into local entitlements | New tables + a `billing` router; all additive on the 1a/1f seams |
| Agent platform | The **`/api/v1` contract** + an **API-key/M2M auth path** in `deps.py` + the **quota** seam | Agents read cards and take actions over `/api/v1` with a scoped token; identity resolves through the same `current()`; quotas apply | `/api/v1` + frozen card shape done in 1a/1f; token auth additive; agent-*triggered* analysis needs `TaskRunner` (1e) |

The unifying rule across all nine: **the boundary is JSON and tenant-scoped function calls,
never shared business logic.** If you find yourself re-deciding a number, re-ranking the feed in
the UI, computing economics in a chat answer, letting a model *originate* a figure a card presents
as fact, trusting a tenant identity that came from the client, letting a real-time event carry a
decision the platform didn't make, hard-coding a price tier or limit instead of reading it as data,
or letting an agent receive a number the platform never decided, stop — that logic lives in the
platform and you are about to drift from it. Transport (HTTP, WebSocket, agent token) changes how
data moves; the plan a tenant is on changes what they may do; neither changes who decides.

---

## 3. Stable contracts

### 3A. The read API / service layer

There are two ways to consume decisions; pick by deployment, not preference.

**Over HTTP** (separate service — the default for the conversational UI and the front end). The
relevant read routes today:

| Route | Returns |
|---|---|
| `GET /api/feed` | the ranked card feed (optionally `?category=&family=&surface=`) |
| `GET /api/summary` | briefing counts (total / new / action) |
| `GET /api/categories` | categories present in the feed |
| `GET /api/kpis` | revenue / margin / cash / inventory KPIs for a window (carries `basis` = `reports` for a customer built from uploaded reports, `orders` for the synthetic path) |
| `GET /api/status` | per-source health (fresh / stale / dark) |
| `GET /api/data/completeness` | which detector groups are active vs. dark, and why |
| `GET /api/card/{id}/explain` | full provenance + inputs + L2 trace for one card |
| `GET /api/card/{id}/research` | the research payload (segment comps, sourcing) |
| `GET /api/card/{id}/why` | the cached "why this, why now" explanation |
| `GET /api/products` | the reconciled cross-channel product view |
| `GET /api/skus` | the SKU data-foundation cockpit — every SKU with values, per-field provenance basis, actual-vs-estimated fee pairs, completeness (report-aware ingestion, §3L) |
| `GET /api/cmaa` | the Profit & Ads (CMAA) rows — per-SKU margin, break-even/actual ACoS, ₹ above break-even, quadrant, and a deterministic `recommendation` object on problem rows (§3M) |
| `GET /api/interpretation` | channel registry: confirmed/default marketplace treatments + pending confirmations |
| `GET /api/log`, `/api/watchlist`, `/api/sourcing` | task-output lists |

The **report-aware write side** (seller-owned, all tenant-scoped via session):

| Route | Effect |
|---|---|
| `POST /api/skus/upload` | add/replace channel reports → the report-aware engine (§3L) |
| `POST /api/skus/edit` | edit a seller-owned field (`cogs` / `margin_floor` / `lifecycle_flag` / `title_override`) — sticky against re-upload; economics recompute immediately |
| `POST /api/interpretation/confirm`, `/dismiss` | confirm/override a channel treatment, or dismiss a confirmation |

The **card action sub-API** (write/clickout side, all tenant-scoped via session):

| Route | Effect |
|---|---|
| `POST /api/card/{id}/ask` | free-text Q&A about a card → `research.ask_card` |
| `POST /api/card/{id}/action` | execute the card's concrete action (draft + deep-link) |
| `POST /api/card/{id}/sourcing` | add to sourcing list |
| `POST /api/card/{id}/save_brief` | save a brief |
| `POST /api/card/{id}/watch` | add to watchlist |
| `POST /api/card/{id}/dismiss` | dismiss the card |

**In-process** (if you embed rather than call over the wire) the service layer in `realify/api.py`
is the same surface, pre-decoration:

```
get_feed(tenant_id, category=None, family=None, new_only=False, surface=None) -> list[card]
get_categories(tenant_id)            briefing_summary(tenant_id)
kpis(tenant_id, window=30)           source_health(tenant_id)
explain_card(tenant_id, card_id)     load_status(tenant_id)
data_completeness(tenant_id)
```

and the Q&A seam in `realify/pipeline/research.py`:

```
research_card(tenant_id, card_id, force=False)   # builds/returns the research payload
ask_card(tenant_id, card_id, question)           # grounded free-text answer about a card
```

`tenant_id` is the first argument of every service function on purpose: it is the isolation
boundary. Resolve it from the authenticated session (HTTP) — never accept it as caller input from
an untrusted layer.

### 3B. The card schema

A card is the platform's atomic unit of decision. Persisted columns (`cards` table):

| Field | Meaning |
|---|---|
| `id`, `tenant_id`, `dedup_key`, `run_id` | identity / dedup / which pipeline run produced it |
| `card_type`, `family`, `type_name` | the rule that fired and its family |
| `asin`, `category` | what it's about |
| `finding`, `why` | the L2-phrased headline and explanation (text only — no authority) |
| `severity`, `sev_label` | priority |
| `confidence`, `conf_label` | model-plane confidence (informational) |
| `exposure_label`, `exposure_pct`, `exposure_val` | **the L1 number** and its label |
| `action` | the concrete or awareness action |
| `sources`, `minis`, `provenance` | JSON: which inputs, mini-metrics, full provenance trail |
| `status`, `is_new`, `created_at`, `updated_at` | lifecycle |

At read time `get_feed` decorates each card with **presentation hints** (these are the front
end's primary inputs):

- `surface` — `intelligence` or `research` (which surface the card belongs on)
- `group` — the demand/operational grouping
- `action_kind` — `execute` (a concrete handler exists) or an awareness verb (`investigate`,
  `monitor`, …)

and returns the feed **already sorted** by `(rank_score, severity, exposure_pct, is_new)`. The
ordering is a platform decision; consume it, don't recompute it.

`sources` / `minis` / `provenance` arrive as JSON strings over HTTP (parsed for you by the
in-process `get_feed`). Treat unknown fields as forward-compatible: render what you know, ignore
the rest, never hard-fail on a new key.

### 3C. The DataSource (Collector) contract

Every source — Keepa, recalls, news, trends, and your competitive feed next — is a subclass of
`realify.collectors.base.Collector`. You implement four things; the base class runs the lifecycle:

```python
class Collector:
    source = "base"                      # unique source key; also the MODE_<SOURCE> key

    def scopes(self, con):  ...          # what to pull for this tenant (e.g. list of ASINs)
    def fetch_live(self, con, scope, window_from, window_to):   ...   # real API call
    def fetch_fixture(self, con, scope, window_from, window_to): ...   # deterministic offline data
    def persist(self, con, scope, records) -> int:  ...               # write via a REPOSITORY
```

What the base `run(force=False)` gives you for free, per tenant, per scope:

- **Watermarked windows** — `window()` reads the last successful watermark from `pull_log`; first
  pull backfills `config.FIRST_PULL_BACKFILL_DAYS`. You get an incremental `(from, to)`.
- **Due-checks** — skips scopes pulled within `interval_hours` unless `force=True`.
- **Live circuit breaker + timeouts** — after `config.LIVE_FAIL_CIRCUIT` consecutive failures it
  stops hammering a flaky source; live calls honour `config.SOURCE_TIMEOUT`.
- **`pull_log` recording** — every run records `ok` / `failed` / `skipped` with counts and the
  window, which feeds `GET /api/status` and the freshness UI automatically.

Mode is resolved from config: `self.mode = config.MODE.get(self.source, "fixture")`, overridable
per source via `MODE_<SOURCE>` env. **Ship `fetch_fixture` first** — it is what makes the whole
system testable offline and is required for our hermetic tests.

Registration is one line in `realify/scheduler.py`:

```python
def collectors(tenant_id):
    return [KeepaCollector(tenant_id), RecallsCollector(tenant_id),
            NewsCollector(tenant_id), TrendsCollector(tenant_id),
            CompetitiveCollector(tenant_id)]      # <- you add this
```

**Persist through a repository, never raw SQL.** This is the rule that kept the Postgres
migration (1c, now live on RDS) a single change-point and keeps RLS (1d) enforceable. Use the existing
`MarketRepository` if your data is snapshots/offers/signals shaped, or we add a small repository
for a new shape — talk to us before introducing a table. (As of 1b, *every* tenant table is behind
a repository; do not be the regression.) Repositories run on **both engines** (SQLite locally/tests,
Postgres in production), so the SQL you write must be dialect-portable — see invariant 4.

### 3D. Rules-as-data — how a new signal becomes a card

Persisting rows is only half the job; a row becomes an *insight* when a **rule** references it. A
rule is a row in the `rules` table — data, shippable without a deploy:

| Field | Role |
|---|---|
| `rule_id`, `name`, `description` | identity |
| `family`, `card_type`, `tier` | grouping and which surface it lands on |
| `primitive` | the deterministic operator (e.g. a threshold) that **decides the number** |
| `inputs` | which persisted fields the primitive reads |
| `params_default`, `editable_params` | thresholds (and which a tenant may tune) |
| `exposure_formula` | how the headline number is computed |
| `action_handler` | the concrete handler, or empty for an awareness card |
| `severity_default`, `enabled_by_default` | defaults |

Per-tenant overrides live in `tenant_rule_settings` (enable/disable, params, severity). So the
competitive team's path to "our signal shows up as a card" is: **(1)** persist normalized rows via
a repo, **(2)** add a rule (or extend an existing rule's `inputs`) that reads them, **(3)** the
existing pipeline detects, gates, phrases, and ranks it for free. No detector code, no UI code.

### 3E. The repository layer (the data boundary)

All persistence goes through `realify/repositories/`. The public surface is the `UnitOfWork`
context manager, which opens one connection, exposes every repository as an attribute, and owns
the transaction:

```python
from realify.repositories import UnitOfWork
with UnitOfWork() as uow:
    skus = uow.sellers.all(tenant_id)
    uow.market.insert_snapshot(tenant_id, asin, ...)
    # commit on clean exit, rollback on exception, always closes
```

Repositories own the SQL; most write methods do **not** commit (the caller/UnitOfWork owns the
transaction boundary) so a multi-step write stays atomic. Don't open `db.connect()` and write SQL
yourself — that is the exact pattern 1b removed.

### 3F. The model (prediction) contract

This is the ML team's seam, and it is the **Model plane** from §1 — the layer that *informs* a
decision but never makes one. The contract lives in `realify/models.py` and is small on purpose.

A model is a class with `id`, `label`, `unit`, and a `covers` set (the detector ids it applies to),
implementing one method:

```python
class StockoutForecaster:
    id = "stockout-forecaster"
    label = "Stockout forecast"
    unit = "days"
    covers = {"days-of-cover", "seasonal-cover", "stock-level"}

    def predict(self, con, tenant_id, asin, detector=None) -> dict:
        # read history (features), project, return:
        return {
            "value": 12.4,                 # the projection, or None if it can't be made
            "confidence": "high",          # 'low' | 'medium' | 'high'
            "kind": self.id, "label": self.label, "unit": self.unit,
            "top_features": [["recent velocity/day", 8.2], ["fit R²", 0.61]],
        }
```

You register it in `models.REGISTRY`. `models.predict_for(con, tenant_id, asin, detector_id)`
selects every model whose `covers` includes the firing detector, runs each, and returns the list.
Per-tenant enable/disable is already handled (`models_disabled` setting); `registry_view()`
exposes the catalogue to the UI.

How a prediction is consumed (`pipeline/materialize.py`) — read this carefully, it defines what a
model can and cannot do:

- **The confidence gate.** A prediction attaches to a card **only if `value is not None` and
  `confidence != "low"`.** A low-confidence or value-less prediction contributes *nothing* — the
  deterministic detector stays authoritative and the card is unchanged. This is the safety valve:
  when your model isn't sure, it is silent, never wrong.
- **What it attaches to.** A gated prediction (a) adds a clearly-labelled **forecast mini**
  (`Forecast · {label}  ~{value} {unit} ({confidence})`) — visually distinct from the locked L1
  numbers — and (b) may contribute an **urgency term to the rank score** (today the stockout
  forecaster lifts cards with <21 days to stockout). It does **not** touch `finding`, `severity`,
  `exposure_pct`, or `exposure_val`. Those are L1's, always.
- **Failure is already safe.** `predict_for` wraps each model in a try/except and degrades a
  raised exception to a low-confidence result — so a model that crashes (or, once you deploy
  remotely, times out) is gated out exactly like a low-confidence one. The pipeline never breaks
  because a model misbehaved. Preserve that contract in whatever you deploy.

**The current implementation is a prototype assumption you will relax — deliberately.** Today the
two in-tree models are pure-Python, read features from `metric_history` via `db.metric_series`,
and do **no network call and no training job at inference** (interpretable linear fits). Your
mandate — *build and deploy* models — breaks those assumptions, and that's expected. The
`predict()` interface is the stable seam; the constraints around it are what we formalize together
in **1e** (see the Team 4 playbook for the four things that change). The interface itself —
inputs, the gated `{value, confidence, ...}` output, `covers`, the registry — does not change.

### 3G. The identity / authentication contract (Kratos + Google OIDC)

This is the Identity team's seam. The decision is made: **Ory Kratos handles authentication, with
Google OIDC brokered through it.** The contract is a clean split of two concerns that today live
together in `auth.py`:

- **Kratos owns authentication (who is this person):** registration, login, credential storage,
  the Google OIDC social-login flow, session issuance, email verification, account recovery, and
  MFA if added. After cutover, the app no longer hashes passwords or runs the login flow itself —
  `auth.py`'s pbkdf2 path is replaced by trusting a Kratos session.
- **Realify owns authorization + tenancy (what may they do):** the user↔tenant mapping, roles
  (`owner` / `member`), invites, provisioning, and every business row. The `users` table stays the
  system of record for *which org, what role*; it gains a `kratos_identity_id` (nullable, unique)
  linking a Realify user to its Kratos identity. `email` stays globally unique — one person = one
  org — and that rule is enforced here, not in Kratos.

**The seam — and it is exactly the `deps.py` from 1a/1f.** A request carries a Kratos session
(cookie or token). The app validates it server-to-server (Kratos `whoami`), reads the *verified*
identity (Kratos id + verified email), maps it to the Realify user, resolves the tenant, and that
is what `current()` / `require_tenant()` return. Resolving identity is the *only* thing that
changes; the 81 handlers that call `require_tenant` are untouched. That is why 1a/1f builds
`current()` / `require_tenant()` as a single pluggable identity resolver — so the source can swap
from "app session cookie" to "validated Kratos session" in one module.

Three rules that are non-negotiable at this seam:

- **tenant_id is resolved server-side from the verified identity — never from a client-supplied
  token claim.** A JWT/identity payload the client can influence is not a tenant assertion. The app
  looks up the tenant from the Kratos identity it just verified, exactly as it does from the session
  today. This is the single most important security property of the whole platform; OIDC must not
  weaken it.
- **Verified email only.** Access is granted on a Kratos-*verified* email (Google OIDC emails are
  pre-verified; password registrations pass Kratos verification first). An unverified email claim
  grants nothing.
- **Fail closed.** Authentication now sits on a network call to Kratos. If `whoami` times out or
  Kratos is unreachable, the request is **denied (401)** — never allowed through. (Note the
  contrast: the model and collector seams fail *open* to "no signal"; auth fails *closed*. Getting
  this backwards is a breach, not a degraded experience.)

**First-login provisioning.** A new verified email with no matching Realify user (e.g. someone's
first Google sign-in) routes into the *existing* provisioning/invite logic — create a user + tenant
for a genuinely new org, or accept a pending invite to join an existing one. Kratos does not invent
tenants; it hands the app a verified identity and the app applies its own one-person-one-org rule.

**Two OAuth surfaces — do not conflate them.** (a) *Sign-in OAuth* — Kratos brokering Google OIDC —
is this contract: authentication. (b) *Integration OAuth* — connecting an external data source
(e.g. a marketplace account) on a tenant's behalf and storing per-tenant tokens for pulls — is the
**connector** concern (Team 2 / the `ChannelConnector` seam in 1e), a different flow with different
storage and scopes. They share the word "OAuth" and nothing else.

### 3H. The real-time / event contract (WebSockets)

This is the newest surface, and the most honest thing to say up front is that **none of it exists
yet** — today the platform is stateless HTTP request/response with a batch pipeline (`run_pipeline`
on a ~4h scheduler) and a UI that fetches on load and refresh. Real-time has two halves, and like
the OAuth contract they share a word and little else; keep them separate:

**Inbound — a streaming source.** A team pushes data in over a WebSocket instead of the
poll/watermark model the collectors use. The transport is different; the contract is not. Inbound
real-time data still **lands through a repository, tenant-scoped, and becomes an insight only via a
detector / rules-as-data** (§3C, §3D). It does not get to write a card directly or carry a verdict.
The one genuinely new thing it forces: to become a card *promptly* rather than at the next 4h tick,
an inbound event must be able to trigger an **incremental pipeline run** for that tenant/ASIN —
which is the `TaskRunner` seam (1e). Until that seam exists, "real-time in" still means "visible at
the next batch."

**Outbound — a tenant-scoped event channel.** The UI subscribes to a WS/SSE endpoint and receives
**card and metric deltas** as they're produced, instead of re-fetching. What it receives is the
same card JSON (§3B); the socket is just a faster delivery truck for platform-decided cards. The
natural publication point is the card-write in `pipeline/materialize.py` (where cards are upserted)
— that's where a future "publish delta" hook lives.

What this changes in the architecture — and it's the load-bearing flag for the whole guide:

- **WebSockets are stateful; the platform is deliberately stateless.** The #005 Phase-1 plan targets
  a stateless API behind a load balancer precisely so scaling is config, not a rewrite. A WS
  connection pins a client to one process. The moment there's more than one API instance, an event
  produced on instance A will not reach a UI connected to instance B **without a pub/sub backplane**
  (Redis pub/sub, Postgres `LISTEN/NOTIFY`, or a broker). So real-time fan-out forces a backplane
  decision; sticky sessions are at best a single-box stopgap. This is the architectural cost, and
  it's why real-time is its own workstream, not a bolt-on.
- **Batch → event-driven.** Cards are produced on a 4h loop today. Real-time requires the pipeline
  to run incrementally on an event and publish the delta — the `TaskRunner` seam (1e) is the
  prerequisite.
- **The channel is authenticated and tenant-scoped at handshake.** A subscription resolves identity
  through the *same* `deps.py` resolver as HTTP (it must be transport-agnostic), and a client
  receives **only its own tenant's events** — never a cross-tenant broadcast. Same isolation
  boundary, new transport.
- **Resource limits.** Long-lived connections consume memory and file descriptors; given the
  prototype's OOM history on a small box, connection caps, heartbeats, and reconnect/backoff are
  part of the contract, not an afterthought.

Delivery semantics: treat events as **at-least-once and idempotent** — the UI dedupes/updates by the
card's `dedup_key` + `updated_at` (the schema already supports this), so a duplicate or out-of-order
delta is harmless. And real-time is **strictly additive**: if the socket drops, the dashboard must
still work by fetching `/api/feed`. The socket is an enhancement, never a hard dependency.

### 3I. The advertising contract (#004 ad spec)

Advertising is **not new architecture** — it is the rules-as-data + detector pattern (§3C, §3D)
applied to ad signals, and a skeleton already exists: there is a `tacos` detector, an `"Ads"` group
in `GROUP_ORDER`, and an `ad_cost_unit` term in the unit economics. The #004 spec *extends* that, it
does not restructure anything.

Two halves, both on existing seams:

- **Ad data in.** Sponsored-ads metrics (spend, sales, ACoS, TACoS, impressions, clicks per ASIN)
  arrive either as a seller-uploaded ad report (**already a recognized kind** in the report-aware
  ingestion path, §3L — it lands per-SKU per-period in `ad_performance`) or, later,
  through the **Amazon Advertising API as a `Collector`** (official API, never scraped — invariant
  6). It persists through a repository, tenant-scoped, like any other metric series.
- **Ad signals out.** New detectors — wasted spend, ACoS above target, TACoS climbing, dayparting
  gaps, ad-driven-rank-dependence — are **rule rows in the "Ads" group**, not code. Each produces a
  standard card (§3B); the deterministic L1 owns the threshold and the exposure math (e.g. ₹ wasted
  = spend on zero-conversion terms). A model (Team 4) may *inform* — a forecast of ACoS if spend
  holds — under the usual confidence gate, never deciding the finding.

The only genuinely new economics is making ad cost a first-class margin input: today `ad_cost_unit`
is a synthetic term and is NULL for customers until ad reports arrive. Once real ad data lands, net
margin and the margin detectors pick it up automatically through `_cmp` — no detector rewrite, the
field simply stops being NULL. That is the graceful-degradation mechanism (invariant 3) doing its
job. Keep ad logic in rules + detectors; do not let the ad report writer compute a card.

The **realized form of this today** is the CMAA "Profit & Ads" surface (§3M): deterministic
per-SKU break-even ACoS, actual ACoS, ₹-above-break-even, the SCALE/FIX-ADS/FIX-MARGIN/CUT-DIVEST
quadrant, and an explainable recommended action — computed from `ad_performance` + `sku_revenue_period`.
The #004 detectors you add to the ranked feed and the CMAA surface share the same locked identity
(break-even ACoS = GCM %) and the same L1-decides discipline.

### 3J. The payments, plans &amp; rate-limiting contract

This is the entitlements seam. The decision it encodes: **plans and limits are *data*, enforcement
is at the `deps.py` seam, and the payment processor is mirrored — never on the request critical
path.** None of it exists yet (no plan/subscription/quota tables today; `usage_events` and tenant
state do exist and are the spine to build on).

Three distinct enforcement types — and they fail differently, which matters:

- **Plan catalog (rules-as-data).** A `plans` table holds the tiers as rows: e.g. *free* (1 user,
  10 insights/day, 10 SKUs, 30-day trial, no card), *starter* ($50/mo per seat), *growth* ($199/mo,
  3 users, 50 insights/day, 50 SKUs). Changing a price or a limit is a row edit, not a deploy. A
  tenant references a `plan_code`; entitlements resolve from the plan.
- **Hard caps — seats &amp; SKUs.** Data-derived (count rows) and enforced at the *mutating action*:
  seat cap at invite-create/accept (Team 5's surface), SKU cap at ingestion/onboarding. These are
  deterministic, need no external service, and **fail closed** — over the cap is denied, with a
  clear "upgrade" signal.
- **Rate limits — insights/queries per day.** A per-tenant daily counter (`usage_counters`:
  tenant_id, metric, day, count) enforced at the metered endpoints — the research/ask/why calls in
  the cards router are the "queries"; a "feed refresh" or pipeline run may count as an "insight"
  (Team 8 defines exactly what meters). `require_quota(request, "query")` lives beside
  `require_tenant` in `deps.py`; over-limit returns **429**, never a wrong or truncated answer
  (invariant 2 still holds). The counter is local (atomic upsert in Postgres, which is now the
  production engine), so it works
  across stateless instances without new infra at these daily volumes; Redis only becomes necessary
  for sub-second limits — and that is the *same* backplane the real-time team needs (§3H).

**Billing (Stripe or equivalent) is mirrored, not synchronous.** The processor owns the money and
the card data — Realify never touches a card number (PCI scope stays with the processor). Checkout
and the customer portal are processor-hosted; the app creates a session server-side and redirects.
Subscription *state* (plan, status, seats, period end) is mirrored into a local table via a
**signed webhook** (`billing` router, signature-verified, no user session — the same machine-to-
machine, fail-closed inbound pattern as §3H and Kratos). Enforcement reads the *local mirror*, so a
delayed or unreachable processor never locks out a paying customer; the webhook just keeps the
mirror fresh. The 30-day no-card trial is a subscription row with `status=trialing` and a
`trial_end`; expiry is evaluated lazily on request (stateless-friendly), downgrading entitlements
rather than hard-blocking reads.

**Data model (four tenant-scoped tables):** `plans` (tiers + limits as rows — `price_cents_per_seat`, `max_users`, `max_skus`, `queries_per_day`, `insights_per_day`, `trial_days`), `subscriptions` (the local mirror — `plan_code`, `status`, `seats`, `trial_end`, `current_period_end`, `stripe_customer_id`, `stripe_subscription_id`), `usage_counters` (`tenant_id`, `metric`, `day`, `count` — the daily rate-limit grain), and `billing_events` (`event_id` unique → webhook idempotency). Seat cap = user count vs `plans.max_users`; SKU cap = catalog count vs `plans.max_skus`.

### 3K. The agent contract (Realify for autonomous agents)

Two questions, both yes — with one honest boundary.

**Can agents consume Realify?** Yes, and the 1a/1f work is exactly the foundation. An agent needs a
*stable, versioned, machine-readable* surface and a *non-cookie* credential. `/api/v1` plus the
frozen card schema (§3B) is the surface; FastAPI emits its OpenAPI automatically, which is also what
lets an MCP server wrap `/api/v1` so any MCP-capable agent (including Claude) can call Realify as a
set of tools. The credential is an **API key / M2M token**: a new `api_keys` table (tenant-scoped,
hashed, *scoped* — read-only vs. action) and a token-resolution path added to `current()` in
`deps.py`. That is the *same* seam Kratos and the WebSocket handshake extend — `current()` becomes a
multi-scheme resolver (session → Kratos → API key), and `tenant_id` is still resolved server-side
from the verified credential, never from a token claim the agent supplies (invariant 8).

**Why Realify is unusually safe for agents.** Because L1 owns the numbers deterministically and
every card carries `finding` / `severity` / `exposure` / `provenance`, an agent built on Realify
gets *grounded, auditable* decisions — not model guesses. The provenance trail is the agent's
citation. An agent literally cannot be handed a fabricated figure, because the platform decides
numbers and the LLM only phrases them (invariant 2). Quotas (§3J) apply to agent tokens too — an
agent that loops cannot exhaust the platform; it gets 429s.

**The honest boundary.** Today the read API is synchronous and the pipeline is batch (4h). So an
agent can *read current cards* and *take the existing advisory actions* (watch / dismiss / save /
clickout) right now over `/api/v1`. What it cannot yet do synchronously is *trigger a fresh
analysis and await the result* — that needs the `TaskRunner` seam (1e) plus a job-status pattern
(agent enqueues, polls/streams completion). And *agent write-back to Amazon* (changing a price, an
ad budget) is a separate, higher-stakes capability that rides the integration/connector OAuth
(Team 2 / `ChannelConnector`) with its own dry-run, confirmation, and audit guardrails — not part
of the read+action surface. Build agents on the read+action surface now; the trigger-and-await and
write-back capabilities arrive with 1e and the connector work.

### 3L. The report-ingestion contract (seller reports → own-data)

Alongside the poll-based collectors (§3C), Realify has a second ingestion path built for **customer
onboarding**: a seller uploads their own Amazon exports and the platform turns them into own-data.
This is how a *customer* account (as opposed to a synthetic *tester*) is populated — there is **no
synthesis**; every number traces to an uploaded report or a seller edit.

The engine is `realify/ingest/report_ingest.py` → `report_writer.py`. It recognizes report kinds
(Monthly Unified Transaction, COGS template, fee-preview, Sponsored Products advertised-product,
Business Report, returns/storage), reconciles them (paid-only ASP, actual fees), and writes:

- **`seller_skus`** — the central per-SKU own-data table (price, COGS, fees, per-unit economics,
  velocity, buy-box, returns, and the seller-owned fields below).
- **`ad_performance`** — per-SKU per-period ad spend & attributed sales (the ACoS numerator/denominator).
- **`sku_revenue_period`** — per-SKU per-period settled revenue (the TACoS denominator).
- **`sku_field_provenance`** — per-field basis/source (`actual` / `reported` / `estimated` / `seller`)
  so every value carries where it came from, and an estimated alternate can sit beside an actual.

Two rules make this path safe, and you build against them:

- **Provenance and graceful degradation.** A field absent from the reports stays NULL — never
  fabricated. Detectors and the CMAA math (§3M) return "undecidable" rather than guess, exactly as
  invariant 3 requires.
- **Seller-owned fields are sticky.** `cogs`, `margin_floor`, `lifecycle_flag`, and `title_override`
  are seller-editable via `POST /api/skus/edit`; a seller edit is **not** overwritten by a later
  report re-upload (the report value is recorded as a provenance alternate for review, but the
  seller value stays the value-of-record). `title_override` lets a seller supply/correct a title
  when the report's is missing or poor; display resolves `title_override or title`.

**Channel interpretation.** Uploaded transactions can span marketplaces. `report_ingest` classifies
each channel; known marketplaces get a default treatment (Amazon-direct vs off-Amazon MCF vs
exclude), unknown ones are filed as **pending confirmations** (`pending_confirmations`) and their
units are held *provisional* — kept out of the judged numbers until the seller confirms
(`account_interpretation` records the confirmed rule). This is why a SKU can be listed but
"held for confirmation" rather than silently mis-counted.

Do not compute a card or a verdict in the report writer — it persists reconciled values and
provenance; detectors, CMAA, and rules decide. Same boundary as every other source.

### 3M. The CMAA / recommended-action contract (Profit & Ads)

CMAA — **Contribution Margin After Ads** — is the realized ad-efficiency engine (`realify/domain/cmaa.py`,
served at `GET /api/cmaa`). It is pure deterministic L1: the same `economics.per_unit()` the SKU tab
uses, plus one locked identity — **break-even ACoS = gross contribution margin %** (#004). Per
advertised SKU it computes margin, break-even ACoS, actual ACoS (spend ÷ attributed sales), **₹ above
break-even** (the *certain* waste), and a **quadrant** — `SCALE` / `FIX ADS` / `FIX MARGIN` /
`CUT/DIVEST`. Unknown inputs → the row is listed but *not judged* (never guessed). Provisional-channel
SKUs are held out of the judged totals.

On the three **problem** quadrants (`FIX ADS`, `FIX MARGIN`, `CUT/DIVEST`) each row carries a
**`recommendation`** object built by `cmaa.recommend()` — a deterministic, explainable recommended
action, **no LLM in the loop**:

```
recommendation = {
  "headline":   str,           # the one-line action
  "steps":      [str, ...],    # ordered, concrete levers
  "evidence":   [str, ...],    # the number→threshold chain; every line traces to a computed figure
  "recoverable": float | None, # ₹ recoverable if acted (= ₹ above break-even for FIX ADS)
  "guarded":    bool,          # true when a lifecycle flag leads (see below)
}
```

Rules you build against:

- **It is L1, not L2.** The recommendation is derived from the row's own figures (margin, ACoS,
  break-even, wasted spend, price/COGS/fees, floor), not phrased by a model. Team 1 must *read* it,
  not recompute it; Team 3 *renders* it, not re-derives it. If a model (Team 4) ever informs it
  (e.g. an elasticity estimate behind a price suggestion), it does so confidence-gated and never
  changes the number — invariant 7.
- **The lifecycle guard leads and never recommends cutting.** If a SKU is flagged `launch` /
  `clearance` / `seasonal` / `discontinued`, `recommendation.guarded` is true, the headline leads
  with the flag, and no "cut / stop ads" step is emitted — stated seller intent is respected, not
  overridden.
- **Every evidence line is auditable.** e.g. *"Actual ACoS = ad spend ₹1,00,519 ÷ ad sales ₹3,21,266
  = 31.3%"* and *"Spend above break-even = spend − (ad sales × margin %) = ₹80,212"*. This is the
  same grounded-decision property that makes the platform safe for agents (§3K).

The `/api/cmaa` row also exposes `referral_fee`, `fba_fee`, and `margin_floor` so a renderer can show
the price-to-floor lever without recomputing economics. Ad detectors that belong in the ranked card
feed remain rules-as-data in the "Ads" group (§3I); CMAA is the dedicated per-SKU surface.

---

## 4. Team playbooks

### Team 1 — Conversational interface

You are a **consumer of decisions**, and you sit closest to the L2 line, so the prime directive
applies hardest to you: **never state a number the platform didn't decide.** When a user asks
"how much am I losing to short-paid settlements?", you do not compute it — you read the relevant
card's `exposure_val` / `provenance`, or call `research.ask_card`, and phrase the platform's
answer. If there is no card, the honest answer is "no issue detected," not an estimate.

Recommended shape:

- **Grounding:** for card-specific questions, route through `ask_card(tenant_id, card_id, q)` —
  it is already grounded in that card's provenance. For "what should I look at?", read
  `get_feed` + `briefing_summary` and summarize; the feed is already ranked, so respect its order.
  For profit/ads questions ("what's my ad waste?", "which SKUs should I fix?"), read `/api/cmaa` —
  the per-SKU numbers and the `recommendation` object (§3M) are already decided and explained; quote
  the `headline` / `steps` / `evidence`, never re-derive them.
- **Capabilities, not free-text actions:** to *do* something, call the action sub-API
  (`/api/card/{id}/action|watch|sourcing|...`). Don't synthesize side effects yourself.
- **Auth + tenancy:** you must run inside an authenticated session and pass the session's
  `tenant_id`. Treat it as a trust boundary, not a parameter the user can set.
- **Cost / latency:** the phrasing and `ask_card` paths call the LLM. Budget for it, cache where
  the card hasn't changed (`updated_at` / `dedup_key` are your cache keys), and degrade to the
  card's existing `finding`/`why` text when you don't need a fresh generation.
- **What we'll give you (1a/1f):** a versioned, typed read surface (`/api/v1`, response models,
  an OpenAPI schema) so your client builds against a frozen contract. Until then, build against
  the routes in §3A and expect the *path prefix* to gain `/v1`.

### Team 2 — Competitive data gathering

You are a **producer of a new source**. Your integration is §3C + §3D, and it is mostly already
built for you. The path:

1. Subclass `Collector`, set a unique `source` key, implement `scopes` / `fetch_live` /
   `fetch_fixture` / `persist`. Ship the fixture path first.
2. Persist via a repository — `MarketRepository` if your data is snapshot/offer/signal shaped, or
   coordinate with us on a new repository + table if not. **No raw SQL.**
3. Register in `scheduler.collectors()` and add a `MODE_<SOURCE>` so you can run live or fixture.
4. Make your signal *mean something* by adding a rule (or extending an existing rule's `inputs`)
   per §3D. That is what turns "we have competitor prices" into "you're being undercut on ASIN X
   by ₹Y, exposure Z%."
5. Honour the invariants: **tenant-scoped** (your rows carry `tenant_id`, your scopes are per
   tenant), **watermarked** (let the base class manage windows; don't re-pull history every run),
   **compliant** (official/licensed sources only — never Amazon scraping, regardless of how
   tempting the data is), and **graceful** (missing data → no signal → no card, not a fabricated
   one).

The reward for staying inside the contract: your source automatically gets freshness tracking,
the circuit breaker, fixture-based tests, multi-tenant fan-out, and a place in `GET /api/status`
and the completeness UI — none of which you have to build.

### Team 3 — Front-end / design

You own **rendering, end to end**. The platform owns *what* to show and *in what order*; you own
*how it looks*. The redesign is therefore a pure presentation change and should not touch a single
decision.

- **Consume the card JSON** (§3B). Drive layout from `surface` (which surface), `group` (section),
  `severity` (priority styling), and `action_kind` (`execute` → a button wired to the action
  sub-API; an awareness verb → an investigate/monitor affordance). Render `finding` / `why` as the
  copy; render the `exposure_*` fields as the headline number — **do not reformat or recompute the
  number**, only style it.
- **Respect the order.** `get_feed` returns the feed pre-ranked. Group and theme it; don't re-sort
  by your own heuristic, or you'll diverge from what the conversational UI and the briefing say.
- **No business logic in the client.** No economics, no thresholds, no "if margin < X color it
  red" — severity is already decided. If you want a new visual state, ask for a field; don't
  derive it.
- **Forward compatibility.** New `card_type`s, `group`s, and JSON keys will appear over time.
  Render what you recognize, ignore what you don't, and never hard-fail on an unknown enum — that
  is how a redesign survives the competitive-data team shipping new card types next quarter.
- **Theming surface:** today the served pages are `frontend.html` / `login.html` / `admin.html` /
  `analytics.html` plus `/assets/logo.png`. If the redesign is a separate SPA, you consume the
  `/api/*` JSON and we keep the HTML shells only as a fallback — let's confirm which.
- **The report-aware surfaces are yours to render too.** The SKU cockpit (`/api/skus`) and Profit &
  Ads (`/api/cmaa`) are presentation over decided data: render the CMAA `recommendation`
  (`headline` / `steps` / `evidence` / `recoverable`) as-is — do not recompute or re-order it — and
  respect `recommendation.guarded` (a lifecycle-flagged row leads with the guard, never a "cut"
  action). Seller-owned fields (`cogs`, `margin_floor`, `lifecycle_flag`, `title_override`) are
  edited via `POST /api/skus/edit`; the picker for `lifecycle_flag` is constrained to the valid
  values client-side, and `title_override` is free text — but the field whitelist and stickiness
  are enforced server-side (§3L), so the client only presents them.

### Team 4 — ML / model deployment

You build and deploy the **Model plane** (§3F). You are an *informant*, not a decider — which makes
your invariant the sharpest of all four: **your projection is never the number a card states as
fact.** The locked `exposure` figure is L1's; your output appears as a clearly-labelled *forecast*
beside it, gated by confidence. If a user ever can't tell your projection from the deterministic
number, that's a platform bug and we treat it as one.

To ship a model:

1. **Implement `predict(con, tenant_id, asin, detector=None)`** per §3F, declare `covers`, register
   in `models.REGISTRY`. Return `confidence: "low"` (or `value: None`) whenever history is thin or
   the fit is poor — that is not a failure, it's the contract; the detector stays authoritative and
   nothing misleading reaches the card.
2. **Read features through the data boundary.** Inference reads history via `db.metric_series` /
   the repositories — tenant-scoped, read-only, no raw SQL. Training happens on your infra,
   offline; the platform's job is to serve features and consume predictions, not to run your
   training loop.
3. **Surface interpretability.** `top_features` is part of the contract for a reason — cards carry
   a `provenance` trail and the explain view shows *why*. A black-box number with no features
   erodes the trust the whole product is built on. Populate it.

The four things your "build and deploy" mandate changes — and which we formalize **with you in
1e**, not unilaterally:

- **Serving boundary.** In-tree models run in-process. If you deploy models as a service, your
  `predict()` becomes a network call — so it inherits the discipline the collectors already have:
  a **timeout** and a **circuit breaker**, with failure degrading to `confidence: "low"` (i.e. the
  card stands without your forecast). The failure *semantics* are already correct (`predict_for`
  gates exceptions out); we're adding the timeout/breaker so a slow model never stalls the pipeline.
  Tell us your inference latency budget and we'll set the timeout above it.
- **Versioning.** Add a model `version` to the prediction and we'll thread it into the card's
  `provenance`, so any card can say *which* model version informed it. Non-negotiable once models
  retrain on a cadence — otherwise we can't audit or reproduce a past card.
- **Offline mode.** Mirror the collectors' fixture path: a deterministic offline inference path so
  your model runs in our hermetic test suite without your serving infra. If our tests can't run
  your model offline, the integration isn't healthy.
- **Rank influence is explicit, not automatic.** Today only the stockout forecaster feeds the
  ranker, via an explicit rule in `materialize.py`. If your model should influence card ordering,
  that gets wired deliberately (and we intend to move that contribution into rules-as-data so it's
  tunable, not hardcoded per model `kind`) — it won't happen just by registering.

The reward for staying inside the contract is the same as for the data team: confidence-gating,
crash isolation, per-tenant enable/disable, the registry view, and the forecast-mini rendering all
come for free. You write `predict`; the platform does the rest safely.

### Team 5 — Identity / OAuth (Kratos + Google OIDC)

You own **authentication** (§3G). You do *not* own tenancy or authorization — that line is the
whole contract. The platform's deepest security invariant is *tenant_id is resolved server-side
and never trusted from the client*; your job is to preserve it through the identity layer, not
around it.

What changes in our architecture when you land — so there are no surprises:

1. **`auth.py` shrinks.** The pbkdf2 password hashing and the `login` / `signup` credential flows
   are replaced by trusting a Kratos session. `accept_invite` and the user/tenant/role logic stay —
   they're authorization, not authentication.
2. **The login/signup routes change shape.** Today they verify a password and set
   `request.session["uid"/"tid"]`. After cutover they validate the Kratos session, map identity →
   user → tenant, and establish the app context. The *handlers downstream don't change* because
   they only ever read `require_tenant`.
3. **`deps.py` is the one place you plug in.** `current()` / `require_tenant()` gain a Kratos-backed
   resolver (validate `whoami` → map `kratos_identity_id` → tenant). Build against that seam; do not
   scatter Kratos calls across handlers.
4. **Schema:** `users.kratos_identity_id TEXT UNIQUE` (nullable, additive) is the link column.
   `email` stays globally unique. No other table changes.
5. **Infra:** Kratos is a service with **its own datastore (Postgres), kept separate from app
   data**. Self-hosted (container + DB) or Ory Network — your call, but the app reaches it over the
   network, so every `whoami` carries a **timeout and fails closed**.

To ship it:

- Stand up Kratos with the password + Google OIDC methods and email verification enabled.
- Implement the resolver in `deps.py`: validate the Kratos session, map the verified identity to a
  Realify user via `kratos_identity_id` (or by verified email on first login), resolve the tenant.
- Route first-login of a new verified email into the existing provisioning/invite logic — never
  mint a tenant inside the identity layer.
- Keep sign-in OAuth strictly separate from integration/connector OAuth (§3G).

This is the workstream that resolves the long-standing "hand-roll vs. managed identity provider"
open question in the logbook (#005 auth seam) — decided: **Kratos + Google OIDC**. The pluggable
resolver lands with **1a/1f**; the Kratos cutover and the `kratos_identity_id` migration are their
own focused auth workstream so they don't ride on top of the router split.

### Team 6 — Real-time / events (WebSockets)

You build the live layer (§3H): data streaming *in* over WebSockets and updates pushing *out* to
the UI. Your discipline is the same as everyone else's, stated as transport: **the socket moves
data faster; it never changes who decides.** An inbound event is a source, not a verdict; an
outbound event is a delivery of a platform-decided card, not a new computation in the client.

The two halves, concretely:

1. **Inbound stream → repository → detector.** Persist incoming data through a repository,
   tenant-scoped, exactly like a collector (§3C) — you're just push instead of poll. Do not write
   cards, do not embed thresholds. To make it show up promptly, an event enqueues an incremental
   pipeline run for that tenant/ASIN via the `TaskRunner` seam (1e); without that seam it surfaces
   at the next batch tick, which is correct-but-slow, not wrong.
2. **Outbound channel → UI.** Publish card/metric deltas (the §3B card JSON) on a tenant-scoped
   WS/SSE channel. The front-end team (Team 3) consumes these the same way it consumes `/api/feed`
   — render the delta, dedupe by `dedup_key`, never recompute. Coordinate the event shape with them.

Non-negotiables for your layer:

- **Authenticate at handshake through `deps.py`** — the same resolver as HTTP, so a socket is bound
  to a verified identity and one tenant. Deliver only that tenant's events; a cross-tenant broadcast
  is a breach, not a bug.
- **Additive, never required.** The dashboard must work without you — if the socket drops, the UI
  falls back to fetching. Don't make live updates a hard dependency.
- **Idempotent + bounded.** At-least-once delivery, deduped by `dedup_key` + `updated_at`; connection
  caps, heartbeats, and reconnect/backoff from day one (the box is small).

What we owe you before this is buildable — and why it's **its own workstream after the Phase-1
core, not part of 1a/1f**:

- A **pub/sub backplane** (Redis pub/sub / Postgres `LISTEN/NOTIFY` / broker) so events survive the
  jump from one API instance to several. This is the real architectural commitment real-time forces;
  we won't fake it with sticky sessions beyond a single box.
- The **`TaskRunner` seam (1e)** so an inbound event can drive an incremental pipeline run.
- A **publish-on-card-write hook** at `materialize.py` — noted now, built then.

1a/1f sets you up for this without building it: `deps.py` is designed transport-agnostic (so your
handshake auth reuses it), and the router layout leaves room for a `realify/realtime/` module. The
backplane + event-driven pipeline land after the stateless-API + Postgres foundation is in, because
they depend on it.

### Team 7 — Advertising (#004 ad spec)

You extend an existing family, you don't add a layer (§3I). The skeleton is already there: a `tacos`
detector, the `"Ads"` group, and `ad_cost_unit` in the economics — and the **CMAA "Profit & Ads"
surface (§3M) is already live**, computing break-even/actual ACoS, ₹-above-break-even, the quadrant,
and an explainable recommended action from real ad data.

1. **Land ad data through a source.** The Sponsored Products advertised-product report is **already a
   recognized report kind** (§3L) — it lands per-SKU per-period in `ad_performance`; the Amazon
   Advertising API as a `Collector` comes later (official API only — never scrape).
2. **Express feed signals as rule rows in the "Ads" group**, not code — wasted spend, ACoS over target,
   TACoS climbing, rank-dependence-on-ads. L1 owns the threshold and the ₹ exposure; a Team-4 model
   may inform a forecast under the confidence gate. Reuse the CMAA identity (break-even ACoS = GCM %)
   rather than re-deriving it.
3. **Let margin pick up ad cost for free.** Once real `ad_cost_unit` is non-NULL, the margin
   detectors fold it in via `_cmp` automatically — don't special-case it, and don't compute a card
   in the report writer.

### Team 8 — Payments &amp; entitlements

You own plans, billing, and rate limiting (§3J). Your discipline: **limits are data, enforcement is
at the seam, the processor is mirrored.**

1. **Model the tiers as rows** in a `plans` table (price, seats, insights/day, SKUs, trial days).
   The free/$50/$199 tiers are three rows; new tiers are new rows.
2. **Enforce in the right place for each limit.** Seats at invite (fail closed), SKUs at ingest
   (fail closed), daily insights/queries via `require_quota()` in `deps.py` at the metered endpoints
   (→ 429, never a degraded answer). Read counters locally; no live processor call on the request
   path.
3. **Mirror Stripe via a signed webhook** into a local entitlements table (`billing` router,
   signature-verified, no session). Enforce on the local mirror so a webhook delay never blocks a
   paying customer. Checkout/portal are processor-hosted — Realify never sees a card number.
4. **Trial = a `trialing` subscription row** with `trial_end`; expire lazily on request, downgrade
   rather than hard-block. No credit card required to start.

Convergence to know: your sub-second rate-limiting (if it ever comes to that) wants the same Redis
backplane the real-time team needs — coordinate so the platform stands up one, not two.

### Team 9 — Agent platform

You make Realify a tool surface for agents, and a base to build agents on (§3K). The 1a/1f work
already gave you the surface (`/api/v1` + frozen card shape + auto OpenAPI).

1. **Add scoped API-key / M2M auth** — an `api_keys` table (hashed, tenant-scoped, read-only vs.
   action scope) and a token path in `current()`. Same seam as Kratos; tenant resolved server-side
   from the key, never a client claim.
2. **Wrap `/api/v1` as MCP tools** (optional but high-leverage) so any MCP agent, Claude included,
   can read cards and take actions. The card's `provenance` is the agent's citation — lean on it.
3. **Respect quotas (Team 8) on agent tokens** — an agent that loops gets 429s, not unbounded cost.
4. **Stay inside read + action for now.** Trigger-and-await fresh analysis needs the `TaskRunner`
   seam (1e) + a job-status pattern; write-back to Amazon is a separate guardrailed capability on
   the connector OAuth. Don't let an agent originate a number — it consumes platform decisions, it
   doesn't make them.

---

## 5. Invariants (the non-negotiables)

These hold for every team, every release. Breaking one is a platform bug regardless of which team
introduced it.

1. **Tenant isolation.** Every read/write is scoped to one `tenant_id`. No cross-tenant access,
   ever. (Enforced by RLS in 1d; honour it before then.)
2. **L1 owns the numbers.** Detectors decide; models inform under a confidence gate; the LLM only
   phrases. No layer above L1 — including a chat answer or a UI badge — originates or alters a
   figure.
3. **Graceful degradation.** Missing input → no card, not a wrong card. Silence is correct.
4. **Persist through repositories, in portable SQL.** No raw SQL outside `realify/repositories/`.
   This is what kept the Postgres swap a single change-point and keeps RLS enforceable. Repositories
   run on **both** SQLite (local/tests) and Postgres (production), so the SQL must be dialect-portable
   — no SQLite-only constructs (`SUM(bool)`, `date('now', ?)`, selecting non-grouped columns). These
   pass the SQLite suite and only fail on Postgres, so DB-shaped changes are gated by a real-Postgres
   smoke before deploy.
5. **One transaction, one owner.** Write methods don't self-commit; the caller / `UnitOfWork`
   owns the boundary so multi-step writes stay atomic.
6. **Compliance + provenance.** Licensed/official sources only; every card keeps a `provenance`
   trail. If you can't say where a number came from, it doesn't ship.
7. **Models inform, never decide.** A prediction is confidence-gated (`!= low` to attach), appears
   only as a labelled forecast beside the locked numbers, and never originates or alters
   `finding` / `severity` / `exposure`. When a model is unsure or unavailable, it is silent and the
   deterministic decision stands.
8. **Identity is verified server-side; auth fails closed.** `tenant_id` is resolved from a
   server-verified identity (session today, validated Kratos session after cutover), never from a
   client-supplied claim. Only verified emails grant access, and if the identity provider can't be
   reached, the request is denied — not allowed through.
9. **Transport never changes who decides.** Real-time is additive: events are tenant-scoped
   (authenticated at handshake, never broadcast across tenants), idempotent (deduped by
   `dedup_key`), and the UI must still work by fetching if the socket drops. An inbound stream is a
   source that lands through a repository and a detector like any other — it never carries a card or
   a verdict of its own.
10. **Limits are data, enforced at the seam; over-limit is 429, never a wrong answer.** Plans and
    quotas live in data rows and are enforced server-side at the `deps.py` seam and at mutating
    actions (seats, SKUs). A metered call past its quota is refused cleanly — the platform never
    fabricates, truncates, or degrades a *number* to fit a limit. Billing state is mirrored locally;
    a payment processor being slow or unreachable never blocks a paying tenant. This holds for human
    sessions and agent tokens alike.

---

## 6. Stable vs. in-flux (build against the right thing)

| Surface | State | Settled by |
|---|---|---|
| Repository layer / `UnitOfWork` | **Stable** (hardened in 1b — all tenant tables behind repos) | done |
| Report-aware ingestion (seller reports → own-data) | **Stable & live** — `report_ingest`/`report_writer`, provenance, channel interpretation, seller-owned sticky fields (§3L) | done |
| CMAA / Profit & Ads + recommended action | **Stable & live** — deterministic break-even/ACoS/quadrant + explainable `recommendation` (§3M) | done |
| Card JSON schema | **Stable**, soon frozen by a contract test | next |
| DataSource (Collector) contract | **Stable**; gains typed config + a formal `TaskRunner`/`ChannelConnector` seam | **1e** |
| Model (prediction) contract | **Stable** interface; gains a serving boundary (timeout/breaker), versioning, offline mode | **1e** |
| HTTP read/action API | `/api/v1` prefix + dual-mount **done in 1a/1f**; response models / OpenAPI hardening ongoing | **1a/1f** |
| Storage engine | **PostgreSQL live in production on RDS**; SQLite remains the local/test engine, selected by `DATABASE_URL`. Migrations at head `0007` (Alembic, dialect-agnostic) | **1c — done** |
| Tenant isolation | discipline today → **enforced by Postgres RLS** (now unlocked by being on Postgres) | **1d** |
| Authentication / identity | hand-rolled sessions today → **Kratos + Google OIDC**; the pluggable resolver seam landed in **1a/1f**, the cutover is its own auth workstream | **1a/1f + auth** |
| Real-time / events | **None today** (HTTP + 4h batch). Needs a pub/sub backplane + event-driven pipeline (`TaskRunner`); seams (transport-agnostic `deps.py`, publish-on-write) set in 1a/1f + 1e | own workstream, post-core |
| Advertising (#004) | **Realized** as the CMAA surface (§3M) on live ad data; extended further via rule rows in the "Ads" group + the Advertising-API collector | rides existing seams |
| Payments / entitlements | **None today.** New `plans` / `usage_counters` / subscription tables + a `billing` router + `require_quota()` in `deps.py`; all additive | own workstream |
| Agent API | `/api/v1` + frozen card shape **done in 1a/1f**; API-key auth + MCP wrapper additive; trigger-and-await needs `TaskRunner` (1e) | 1a/1f + 1e |

What this means in practice: the repository layer, the card schema, the report-aware ingestion
path, and the CMAA surface are safe to build on now. The `/api/v1` prefix is mounted alongside
`/api` (build partner clients against `/api/v1`). The Postgres migration (1c) is **done** — it did
not change any contract in this document; RLS (1d) likewise changes only how isolation is enforced,
below your seam.

---

## 7. Versioning & change management

- **API versioning:** introduced with the 1a/1f router split. Breaking changes bump the version;
  the prior version is supported through a deprecation window. Build clients to send/accept a
  version.
- **Card schema:** additive by default (new fields, new `card_type`s). Removals or semantic
  changes are versioned. A contract test (added next) fails the build if the card shape changes
  without a version note — so your renderer won't silently break.
- **Source contract:** changes to the `Collector` base are announced; your `fetch_fixture` is the
  canary — if our test harness can run your collector offline, your integration is healthy.

---

## 8. What we need from each team

- **Conversational:** your expected call volume and latency budget for the LLM paths, and whether
  you embed in-process or call over HTTP — it changes whether we prioritize the typed HTTP surface
  or a stable in-process facade first.
- **Competitive data:** the shape of your records (snapshot / offer / signal / something new) so
  we agree on `MarketRepository` vs. a new repository before you write code, and the source's
  licensing/compliance basis so we can sign off provenance.
- **Front-end:** SPA-consuming-JSON or server-rendered shells, and the list of any new visual
  states you want — we'd rather add a card field than have you derive one.
- **ML / model:** whether you serve in-process or as a remote endpoint (sets the
  timeout/circuit-breaker design), your inference latency budget, your retrain cadence (drives
  versioning), and which detectors each model `covers` — so we know where its forecast surfaces.
- **Identity / OAuth:** self-hosted Kratos vs. Ory Network, and whether the app trusts the Kratos
  session cookie directly (validate per request) or exchanges it for a short app session — both set
  the `deps.py` resolver design and the `whoami` caching/timeout policy; plus your stance on
  existing password users at cutover (migrate vs. force re-registration).
- **Real-time / events:** the inbound protocol and peak event volume, your backplane preference
  (Redis pub/sub vs. Postgres `LISTEN/NOTIFY` vs. a broker), whether the UI needs card deltas only
  or also metric/KPI streams, and your tolerance for the single-box sticky-session stopgap before
  the backplane lands — these decide when this becomes its own workstream and how big it is.
- **Advertising:** whether ad data arrives first as a seller upload or via the Advertising API, and
  the exact list of ad detectors you want (so we agree the rule rows and the ₹-exposure formula per
  signal) before you write them.
- **Payments &amp; entitlements:** the precise definition of a metered "insight" vs. "query" (what
  increments the daily counter), the processor (Stripe assumed), and whether seats are hard-capped
  or soft (overage-billed) — these set the `usage_counters` grain and the `require_quota` placement.
- **Agent platform:** read-only vs. action scopes you need on API keys, whether you want a hosted
  MCP wrapper around `/api/v1` or will call it directly, and whether you need trigger-and-await
  (which pulls `TaskRunner`/1e forward) or only read+action (available now).

Open a thread per team; we'll turn the answers into the frozen `/api/v1` contract and a short
per-team appendix to this guide.

---

## 9. The agency console (Realify for Agencies) — seams &amp; invariants

A second product ships in the same app under `realify/agency/*`, `realify/routers/agency_*.py`, `realify/pdp/*`, and `realify/agency_jobs.py`. It is **Postgres-only**, feature-flagged behind the `AGENCY_CONSOLE` env flag (`off` ⇒ every agency route 404s), and **live in production**. Build against these seams and invariants.

### 9.1 Seams
- **Policy (PDP):** one pure function `realify.pdp.decide(envelope, grant, action)` — never write per-route policy. Capability = `intersection(envelope, grant)` on the `read < propose < execute` ladder + per-lens autonomy ceilings. Envelope templates and role templates are **data** in `realify/pdp/templates.py`.
- **Identity/scope:** `realify/agency/actor.py::resolve_actor(uid)` → the actor's allowed brand set + agency ids (from grants through active engagements). That set feeds `tenancy.set_brand_scope(cur, ids)` on **every** agency DB touch. This is the agency extension of the same `deps.current()` identity seam used by the seller product.
- **Ledger + crypto:** `realify/agency/ledger.py` (append/verify_chain/read_payload), `keyring.py` (per-brand DEK, `crypto_shred`, KEK-fingerprint guard), `crypto.py` (AES-256-GCM, `kek_fingerprint`). Every state change is ledgered per brand.
- **Execution:** `realify/agency/execution.py` (`execute_approval` single-item, `execute_bulk` canary/rollback, `undo_execution`) writes to the **in-process mock marketplace** `mock_marketplace.py`. There is **no real marketplace client** — that is the seam a future connector implements, behind the same guardrails.
- **Jobs:** `realify/agency_jobs.py` — `run_feeders_once` (decisions + rollups + daily FX per active brand), `run_agency_jobs_once` (health / pilot-lapse / co-sign + gate expiry), `run_billing_once` (monthly invoice build). All no-op without Postgres; all invoked from `scheduler._loop`.
- **Routes:** funnel (`agency.py`), consent+connections+ingest (`agency_consent.py`), console+queue (`agency_console.py`), execution controls (`agency_execution.py`), approvals/cockpit/mobile (`agency_approvals.py`), reporting+billing+SES webhook (`agency_billing.py`), internal admin+quality+superlogin (`agency_admin.py`), brand surfaces (`agency_brand.py`), sandbox hub (`agency_sandbox.py`).

### 9.2 Invariants (non-negotiable)
- **RLS is FORCED; no runtime role bypasses it.** 14 brand-scoped tables enforce `tenant_id = ANY(current_brand_ids())`; `realify_app` (and even the owner `realify_admin`) are NOBYPASSRLS. **Set the brand scope before any brand-table query** — tests use the bypass-capable harness owner, so a missing scope passes in tests and fails in prod. Self-reads of a user's own grants/approvals go through the GUC-keyed policies (0027/0029), never a bypass.
- **Authz for brand invites is grant-based** (`agency_admin` / `account_manager` grant on the target agency), with the Realify staff key as an additional path.
- **Co-sign is derived, never hardcoded** (pricing lens or amount ≥ the engagement's `brand_cosign_threshold`); **silence never executes** (5-day expiry cancels, never runs).
- **Execution is guardrailed:** TOCTOU re-check against the current envelope at execute time, durable idempotency key, per-account token buckets, canary rollout with halt+rollback, per-item Undo — all ledgered.
- **Reports pass a factuality gate:** any numeric claim not emitted by the engine BLOCKS delivery (the report is never sent).
- **Money is honest:** execution is mock-only, ROI is **projected** (sum of executed decisions' projected impact — never a measured counterfactual), Stripe is **test-mode**.
- **Tenant taxonomy:** `tenants.tenant_kind ∈ {seller, agency_workspace, internal, sandbox}` drives aggregates + the drift check; keep new tenants classified.

### 9.3 What's stable vs in-flux
- **Stable to build on:** the PDP contract, the RLS scope model, the ledger/crypto primitives, the maker-checker/co-sign state machine, the execution guardrail set, the migration chain (0015–0030 additive).
- **In-flux / declared-not-triggered** (see `docs/WIRING_CENSUS.md`): the real marketplace connector (mock today), realized-ROI reconciliation (projected today), `ledger.read_payload` and `ops.break_glass` (no route yet), Stripe live mode. Don't design as if these are frozen.

### 9.4 What we need from an agency-console integrator
The real marketplace write connector (Amazon SP-API / Ads API) is the biggest open seam: agree the per-account action scopes, the idempotency-key contract, and the token-bucket limits, and implement behind `execution.execute_*` so the mock swaps out without touching the approval/ledger path. Second: the FX feed (daily rate lock currently uses a manual fallback). Third: realized-impact reconciliation to turn projected ROI into measured ROI.

---

## 10. V4 experience — conversational, agents & the model seam (2026-07-23)

The app now ships a parallel **V4 UI** (`frontend_v4.html`) behind the **Feature/Version Registry**
(`realify/flags.py`, `FEATURE-REGISTRY.md`) — served only when `app_ui` resolves to `v4`. Legacy
(`frontend.html`) is untouched. Everything below is additive; the `/api/v1` contract is unchanged.

### 10.1 Rollout / rollback (Ops-driven, no redeploy)
- Ops: `/ops` → **Rollout** card (`GET/POST /api/admin/rollout`, admin-key gated). Version features
  (build + scope off|internal|on) and gate features (on/off). Read per request → instant.
- URL affixes: **`?skin=v4`** forces V4 for your session; **`?skin=legacy`** forces legacy. Great for
  dogfooding while global scope is still `off`.
- Forward features (`ask`, `agents`) `require: app_ui=v4`; `feature_enabled = gate AND dependency` so
  they are inert (and greyed in Ops) under a legacy build — never an undefined state.

### 10.2 Ask — the conversational seam (`realify/ask/`)
Agent-shaped, not a chatbot echo. One turn: resolve model → context pack → **tool-router** over the
tenant's real data (the same domain code the cards use) → **narrator** composes structured parts →
persist → stream as SSE. **The single swap point is `narrator.py`**: today `StubNarrator` (data-grounded,
no LLM); a self-hosted model implements the same `compose(question, facts, context, history) →
{content, parts}` and is selected by the model's `provider`. Endpoints: `POST /api/ask` (SSE),
`/ask/categories|models|usage|conversations[/{id}]|feedback|followup|followups`. Tables: `ask_*` (mig
0039). Usage capped at 100/mo/tenant. **Integrator task:** host the model behind the narrator protocol
(and/or the RIA `invoke` contract §RIA doc) — nothing else changes.

### 10.3 Agents — the workforce (`realify/agents/`)
Framework (specialist catalog, autonomy ladder Observe→Suggest→Assist→Act, server-side guardrails, the
hash-chained **Autonomy Ledger**, pricing scope hierarchy) is app-owned and built as structure. The
flagship **Pricing** agent consumes the RIA models (see `docs/RIA-MODEL-INTEGRATION.md` §10: `optimize` +
`refit` capabilities, calibrated confidence, live-vs-batch cadence). Behavior is gated: `feature_enabled
('agents')` (default off), agents start in Observe, and **Act stays held until the RIA models + real
Amazon write-back are live**. Tester/sandbox accounts get seeded sample decisions so the surface demos
real; real customers stay honest-empty. Tables: `agent`, `agent_task`, `agent_decision` (Ledger),
`pricing_category_plane`/`pricing_subcat_cps`/`pricing_item_state` (mig 0041).

### 10.4 What we need from integrators (V4-era)
1. **The RIA model service** — implement the `invoke(request) → envelope` contract for the 11 domains
   (`docs/RIA-MODEL-INTEGRATION.md`), incl. the Pricing `optimize`/`refit` seam. Held domains (#4 Demand,
   #10 Ads) flip to live when their data feeds land — cards AND agents light up at once.
2. **The Ask model** — a hosted model behind `narrator.py` (or reuse the RIA `invoke` seam).
3. **Real Amazon write-back** — still the biggest open seam (mock today); agents' Act path unlocks on it.
