# RIA model integration — design doc

**Audience:** the model author (cofounder) wiring the RIA models into the realify_mc app.
**Goal:** one stable contract + registry so all 11 feed domains plug in once and light up **every**
surface — cards, the Ask conversational interface, Agents, Simulate, and the Settings model panel —
without per-surface glue. The app owns the *registry + seam + consumption*; you own the *models behind
the contract*.

**TL;DR of the contract:** implement each domain as a capability that answers a uniform `invoke(request)
→ envelope`. Stamp `version`, declare `status` (`live | rule | held`) and `data_needs`, and **never
override the app's locked L1 numbers** — models *inform* (forecast / what-if / RCA / content), they don't
replace facts. A slow/broken model degrades to low-confidence-silent, never wrong.

---

## 1. What exists today (build against this, don't replace it)

`realify/models.py` is the live model-serving seam:

- **Model object protocol** — each model has `id`, `version`, `label`, `unit`, `covers` (the detector
  ids it serves), and `predict(con, tenant_id, asin, detector=None) → prediction`.
- **Prediction shape** — `{kind, label, unit, value, confidence: "low|medium|high", top_features:
  [[name, val], …], note?, model_id, version}`. `confidence` maps to the card's 1–4 scale via `CONF_NUM`.
- **`_serve()`** — the serving boundary: crash-isolated (any exception → `_degraded`, contributes
  nothing), **version-stamped**, and honoring a `timeout` that is *"the contract for an out-of-process /
  remote model… exceeding `timeout` degrades to 'low' exactly like a crash, so a slow model is silent,
  never wrong."* (`config.MODEL_TIMEOUT`.)
- **`predict_for(con, tenant_id, asin, detector_id, timeout)`** — the pipeline entry point.
  `realify/pipeline/materialize.py` calls it to attach a forecast + confidence to each own-data signal:
  *"Models inform only — they never change the locked numbers."*
- **`registry_view(con, tenant_id)`** and **`disabled_ids()`** (per-tenant `models_disabled` setting) —
  already power a per-tenant model on/off UI (today's account-drawer "Forecast models" box).

**Two hard invariants that carry over unchanged:**
1. **Inform-only.** The deterministic L1 number (margin, spend, units) is computed by the app and is
   final. A model's output is a forecast / what-if / diagnosis layered *on top* and recorded in the
   card's provenance + explainability (`ƒ`). It must never mutate an L1 fact.
2. **Fail-silent, never-wrong.** Timeout, crash, or low data → degrade to `low` confidence and drop out
   of the surface. Wrong-but-confident is the one unacceptable outcome.

---

## 2. The Domain Capability Registry (the backbone)

The app formalizes the 11 domains into ONE registry (extending `models.py`). Every surface reads from it;
you implement the models behind it. Registry entry schema:

```
{
  id:            "inventory",                 # stable domain id
  label:         "Inventory",
  produces:      "restock / stockout forecast + graph cold-start",
  capability:    "forecast",                  # forecast | what_if | rca | content_intel | extraction | rule
  model:         "chronos-2",                 # your model/tech (informational + telemetry)
  status:        "live",                      # live | rule | held
  version:       "1.0.0",                     # you stamp; flows to provenance
  data_needs:    null,                        # non-null string when status=held (what's missing)
  maps_to: { family: "risk", kpi: "Inventory", ask_category: "cash", detectors: ["days-of-cover", …] }
}
```

`status` is a **first-class, surfaced fact** (see §8). `maps_to` is how one registry reconciles the
app's several taxonomies (card families, KPI band, the 5 Ask categories) — set once, here.

---

## 3. The invocation contract (what each model implements)

Today's `predict(asin, detector) → value` is the **forecast** capability. RIA needs four more capability
shapes. All share ONE envelope so app-side handling is identical:

### Request
```
{
  domain:      "ads",
  capability:  "what_if",
  tenant_id:   231,
  entities:    ["B0ABC…"],          # ASIN/SKU list, or [] for portfolio-scope
  params:      { bid_change_pct: -0.10, horizon_days: 90 },   # capability-specific
  context:     { country: "IN", currency: "INR" }             # light framing (never trust for scope)
}
```
`tenant_id` is resolved server-side by the app and passed in; **never** trust a client value.

### Response envelope (uniform)
```
{
  status:      "ok" | "held" | "rule" | "degraded",
  result:      { … capability-specific, see below … },
  confidence:  "low" | "medium" | "high",
  evidence:    [ { factor, value|weight, source } ],   # feeds the ƒ / ⓘ explainability panels
  model_id:    "econml-uplift",
  version:     "0.3.1",
  data_needs:  "real daily ad spend + bid log",         # present iff status="held"
  note:        "…"                                       # optional human line
}
```

### Capability-specific `result`
- **forecast** — `{ metric, unit, horizon_days, value, series?: [[t, v]…] }` (domains 1, 3, 11).
- **what_if** — `{ intervention, projected: { metric, delta, horizon_days }, curve?: [[x, y]…],
  tripwire?: {…} }` (domains 4 Demand, 10 Ads). *This is the seam behind Simulate — see §5.*
- **rca** — `{ target, causes: [ { factor, contribution, evidence } ] }` (domain 6 Competitive:
  "why is X at risk").
- **content_intel** — `{ attributes: […], keyword_gaps: […], seo_recommendations: […] }` (domain 5,
  Qwen2.5-VL, from product photos + listing).
- **extraction** — `{ signals: [ { type, entity, severity, source, ts } ] }` (domain 7 News, Gemma —
  writes structured signals into the graph).
- **rule** — computed by the **app**, not you (domains 8 Margin, 9 Cash). The registry marks them
  `status: "rule"` so callers label them "a fact, not a forecast." No model call.

### Honesty semantics (enforced app-side, but you signal them)
- `status:"held"` → the model returns **no fabricated numbers**; app renders "not yet — needs
  {data_needs}." (This is exactly today's `ad_resolution` state machine for the held Ads domain —
  `realify/domain/ad_resolution.py`.)
- `status:"degraded"` (or timeout/crash) → dropped silently, L1 stands.
- `confidence` gates prominence; `evidence` populates the `ƒ`/`ⓘ` explainability tags (kept on every
  surface).

---

## 4. Serving & data access (deployment choices for you)

Two integration modes; the app-side registry entry adapts either into the Model protocol, so the app
contract is identical regardless:

- **In-process** — a Python class in `models.REGISTRY` implementing `invoke(request)`. Fine for light
  models; shares the app's DB connection; bounded by `MODEL_TIMEOUT`.
- **Remote service (expected for chronos-2 / Moirai / EconML / Qwen / Gemma)** — an HTTP/gRPC inference
  service; the app wraps it in a thin client that satisfies the same protocol. `_serve()` already treats
  a remote call's timeout as degrade-to-low. Suggested endpoint: `POST /infer` taking the §3 request,
  returning the §3 envelope; service-token auth; **stateless + idempotent**.

**Feature/data access — one decision to make:** the held domains need history (per-SKU price, daily ad
spend/bid log). Either (a) the model service reads the **shared Postgres** (RDS) directly for features
[recommended for volume], or (b) the app passes a feature payload in `context`. Pick per domain; the
contract supports both. If (a), you'll get a read-only role + the relevant table list from the app team.

**Versioning:** bump `version` on every model change; it's stamped into each prediction and into card
provenance, so a regression is traceable to a model version.

---

## 5. Where each domain surfaces (consumption points — so you see the blast radius)

1. **Cards / pipeline** — `predict_for` attaches `forecast`-capability output to own-data cards
   (inform-only). Live today for the forecast domains.
2. **Ask (conversational)** — the Ask tool-router (`realify/ask/tools.py`, scaffolded) will be
   **re-anchored on the registry**: each domain = a tool; the narrator renders `result` + `evidence`
   honestly (held → honest-empty, rule → fact). One question → one or more domain `invoke`s.
3. **Agents** (surface not yet designed) — agents orchestrate several domains per goal (e.g.
   Margin·rule → Pricing·LightGBM → Competitive·rca → Demand·what_if). Same registry, same contract.
4. **Simulate** — the `what_if` capability backs the Fix-Ads / Demand what-ifs. Today's deterministic
   `realify/domain/ad_simulate.py:project()` is the placeholder; the EconML/Moirai `what_if` replaces it
   behind the same call site (Simulate UI unchanged).
5. **Settings → Intelligence models panel** — `registry_view` lists all 11 with Live/Rule/Held badges +
   per-tenant enable (`disabled_ids`). Inline held-badges appear wherever a held domain can't answer.

---

## 6. Per-domain spec (all 11)

| # | Domain | Capability | Model | Status | Inputs → Output | Surfaces |
|---|---|---|---|---|---|---|
| 1 | Inventory | forecast | chronos-2 | live | velocity+stock series → days-of-cover / stockout date | cards, Ask(Cash/Forecasts), Simulate |
| 2 | Pricing & Buy Box | forecast/what_if | LightGBM | live | price/elasticity features → price rec | cards, Ask(Competition/Performance) |
| 3 | Sales | forecast | chronos-derived | live | sales series → velocity + revenue momentum | cards, KPI(Revenue), Ask(Performance/Forecasts) |
| 5 | Opportunity/Content | content_intel | Qwen2.5-VL | live¹ | product photos + listing → attributes + keyword-gap SEO | cards(opportunity), Ask, Catalog |
| 6 | Competitive | rca | signal graph | live | competitor/BuyBox events → "why is X at risk" causes | cards(competitive), Ask(Competition) |
| 7 | News/External | extraction | Gemma | live | news/recall/trend text → structured signals into graph | cards(news), feed |
| 11 | Risk–Rating | forecast | drift forecast | live² | rating series → rating-drop early warning | cards(risk), Ask |
| 8 | Margin | rule | — (app) | rule | margin-vs-floor **fact** | cards, KPI(Margin), Ask(Performance) |
| 9 | Cash | rule | — (app) | rule | trapped-capital **fact** | cards, KPI(Cash), Ask(Cash) |
| 4 | Demand–covariates | what_if | Moirai | held | needs **per-SKU price history** → "reprice → demand" | Simulate, Ask(Forecasts) |
| 10 | Ads | what_if | EconML uplift | held | needs **real daily ad spend + bid log** → "cut bid 10% → lose X sales" | Ads/Fix-Ads Simulate, Ask(Ads) |

¹ #5: listing intelligence (image attributes + keyword gaps) is live; the deeper **conversion-prediction**
model is validated-but-held (needs a daily conversion feed).
² #11: the rating-drop forecast is live; the **"why" (aspect sentiment)** needs review text (Keepa
doesn't provide it) — a separate data ask.

---

## 7. Remaining data feeds (the whole backlog)

1. **Per-SKU price history** → unblocks #4 Demand (Moirai).
2. **Real daily ad spend + bid log** → unblocks #10 Ads (EconML uplift).
(Plus the two footnotes: daily conversion feed for #5's deep model; review text for #11's aspect
sentiment.) Everything else is live or a rule-by-design.

---

## 8. Division of labor

- **App team (this repo):** the Domain Registry, the `invoke` seam + remote client, crash/timeout/version
  handling, status propagation + honest-empty rendering, and all consumption (cards, Ask, Agents,
  Simulate, Settings panel).
- **You (models):** implement each domain's `invoke(request) → envelope`, stamp `version`, declare
  `status`/`data_needs`, and (per §4) decide feature access. When a held domain's data feed lands, flip
  its `status` to `live` — no app change needed; it lights up everywhere at once.

## 9. Open decisions for you
1. **Serving mode per domain** — in-process vs remote HTTP (expected: remote for the heavy models).
2. **Feature access** — model service reads shared RDS (read-only role) vs app passes feature payloads.
3. **Capability confirmations** — is Pricing (#2) forecast-only or also `what_if` (price → BuyBox/units)?
4. **Auth + SLA** — service token + a target p95 latency so we can set `MODEL_TIMEOUT` sensibly.
5. **Pricing `optimize`/`refit` split (see §10)** — confirm the live-vs-batch boundary + the CPS
   elasticity-class output shape.

---

## 10. Agents consumption — what the workforce layer needs from your models

The app is building an AI **workforce** (agents/specialists) *on top of* these domains. The agent
framework — autonomy ladder (Observe→Suggest→Assist→Act), server-side guardrails, the Arbiter,
the hash-chained Autonomy Ledger, the task scheduler, and the pricing scope-hierarchy — is
**app-team-owned; you don't build it.** But the flagship **Pricing & Margin** agent adds a few
requirements to *your* model contract:

1. **New capability `optimize` (margin-optimal price).** The Pricing daily loop's "compute optimal
   price" step needs, per item: given the resolved `effective_policy` (category **role**, subcat
   **floor%**, **price-image band**, **cover/WOC**), return
   `{ price, elasticity, expected_cm3_delta, confidence, evidence }`. Add this for domain #2 (Pricing &
   Buy Box, LightGBM) alongside `forecast`/`what_if`; the policy constraints arrive in `params`, you
   return the *constrained* optimum + why.
2. **Confidence is contract-critical — calibrate it.** The autonomy ladder gates on `confidence`:
   `≥ threshold → auto (in-band)`, else `→ HITL`. The decks run `0.89 → auto`, `0.83 → HITL`, escalate
   `< 0.6`. A mis-calibrated score wrongly auto-applies or needlessly escalates — return a **calibrated
   [0,1]** confidence on every reply.
3. **Clock cadence — per-decision vs batch.** Two call patterns:
   - **Live (low-latency):** the daily loop calls `optimize`/`what_if` per item, per run (p95 target, §9).
   - **Batch (`refit`, monthly):** re-estimate elasticity + re-baseline the subcategory CPS.
   Annual sizing consumes app-side outcome roll-ups — no model call.
4. **You feed the scope hierarchy, not just cards.** The **Subcategory CPS** row's **elasticity class**
   (+ monthly refit params) is written from your `refit` output. So the model feeds the
   Category→Subcategory→Item hierarchy (policy inherits down, outcomes aggregate up), not only the feed.
5. **Held domains gate the held agents.** #10 Ads (EconML) and #4 Demand (Moirai) being `held` is exactly
   why the **Ad Optimizer** agent and the **"reprice → demand"** what-if stay Observe-only. Ship the two
   feeds (per-SKU price history; real ad spend/bid log), flip `status: "live"`, and **both the cards and
   the agents light up** — no app change.

**Net for you:** add `optimize` + `refit` for Pricing, keep `confidence` calibrated, and flag which
capabilities are live vs batch. Everything above the model line (agent autonomy, guardrails, ledger,
arbiter) is ours.

---

## 11. App-side status (2026-07-23) — the seam is now built and waiting on you

Everything above the model line is now **built and deployed (dark, behind a flag)** — so the moment your
models answer the `invoke` contract, they light up with no further app work:

- **The registry + seam.** `realify/models.py` remains the serving boundary (crash-isolated,
  version-stamped, timeout→degrade). The 11-domain registry is the source of truth every surface reads.
- **Ask** is live behind a swappable narrator (`realify/ask/narrator.py`) — a data-grounded stub today;
  drop your model in as a provider and it serves the conversational home immediately.
- **Agents** is built as structure: the specialist framework, autonomy ladder, server-side guardrails,
  the hash-chained Autonomy Ledger, and the **pricing scope-hierarchy tables**
  (`pricing_category_plane` / `pricing_subcat_cps` / `pricing_item_state`) exist. The flagship Pricing
  agent's daily loop is scaffolded and calls the `optimize`/`what_if` seam — held on your models. Its
  `refit` (monthly) is where you write the subcategory **CPS elasticity class**.
- **Honesty is enforced.** `held` domains (#4 Demand, #10 Ads) render honest-empty and their agents stay
  in Observe; flip a domain to `live` when its feed lands and both cards AND agents activate at once.

**Your critical path is unchanged:** (1) the `invoke(request)→envelope` contract for the 11 domains,
(2) Pricing `optimize` + `refit`, (3) calibrated `confidence`, (4) the two held data feeds (per-SKU price
history → #4; real daily ad spend + bid log → #10). Nothing on the app side blocks you.
