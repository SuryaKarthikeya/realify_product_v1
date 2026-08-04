# Realify — Engineering Logbook

A running log of deferred tasks, decisions, and design notes for the `realify_mc` build.

**Convention**
- Each entry gets a zero-padded number (`#001`, `#002`, …), assigned in order and never reused.
- Status is one of: `Backlog` · `Next up` · `In progress` · `Done` · `Dropped`.
- New entries are appended at the bottom; the index below stays in sync.

**Index**

| # | Title | Status | Logged |
|---|-------|--------|--------|
| [001](#001--model-layer-pluggable-paidoss-models--bd-lifecycle) | Model layer: pluggable paid/OSS models + B→D lifecycle | Backlog | 2026-06-26 |
| [002](#002--source-control--path-a-aws-hosting-shipped--open-items) | Source control + Path A AWS hosting (shipped) + open items | In progress | 2026-06-26 |
| [003](#003--accounts-organizations-admin-console-faq--ops-hardening) | Accounts (tester/customer), customer onboarding, orgs/invites, deletion, admin console, login FAQ + ops hardening | Done | 2026-06-27 |
| [004](#004--ad-spec-margin--ads-fusion-cmaa) | Ad spec — Margin × Ads fusion (CMAA): the profit-after-ads detector | Backlog | 2026-06-28 |
| [005](#005--production-scale-architecture-phase-01--rds-postgres--refactor) | Production-scale architecture: Phase 0 (safety) + Phase 1 (RDS Postgres + refactor); Temporal/integration/elasticity seams | In progress | 2026-06-28 |
| [006](#006--monetization-tiered-paywall--stripe-billing) | Monetization — tiered insight paywall (free/mid/unlimited) + Stripe billing; entitlement seam in Phase 1 | Backlog | 2026-06-29 |
| [007](#007--your-category-analyst-research-tab-rename--synthesis-screen-scaffold) | Your Category Analyst (Research tab rename) — synthesis-led screen + typed card-kind contracts + fixture-backed synthesis seam | In progress | 2026-07-03 |

---

## #001 — Model layer: pluggable paid/OSS models + B→D lifecycle

- **Status:** Backlog
- **Logged:** 2026-06-26
- **Priority:** Medium (moat-relevant; not urgent — sits behind live data accruing)
- **Area:** `realify/models.py`, `realify/history.py`, `realify/db.py`, `scheduler`, pipeline `materialize`

### Context — why this is here
The model layer is **contract-first**, so the *model logic* is already pluggable: anything implementing
`predict(con, tenant_id, asin, detector) → {value, confidence, top_features, label, unit}` plus
`.id/.label/.unit/.covers` drops into `REGISTRY` and works — linear fit, StatsForecast, GBM, or an HTTP call
to a hosted API. The **confidence gate** + the `try/except` in `predict_for` make a new model safe to add
(misbehaves or low confidence ⇒ contributes nothing, deterministic detector stays authoritative), and
**per-tenant enable/disable** already exists for dark-launching.

What is **not** built yet (the real gaps, mostly for *remote/paid* models):
- `predict()` is **synchronous, called inline per card** in `materialize` → a network model = latency × thousands of SKUs × every run. Needs batching, async, timeout + circuit breaker (reuse the `collectors` pattern), and a **predictions cache** so forecasting runs on a schedule, not in the request path.
- **No artifact storage / versioning** — fit-at-inference today; a trained model needs stored weights + a `model_version` stamped on predictions for audit.
- `REGISTRY` is a **hardcoded list, not a table** — adding a model is a redeploy; no per-tenant model *selection*.
- `top_features` assumes an **interpretable** model — a black box breaks the Model layer of the explainability trace unless SHAP is added (this trace is a product differentiator, so it matters more for us).
- **Confidence is categorical** — a model returning prediction intervals needs a mapping into the gate.
- A remote model **sends tenant data to a third party** — in tension with the tenant-isolation / proprietary-data moat.

### The model lifecycle (A → D)
Each phase plugs in behind the same `predict()` contract + confidence gate, so serving, explainability, and
ranking don't change as the model matures. Value (and governance burden) compounds in order; B is prerequisite
for C, C for D. **Today is Phase A.**

- **A — now.** Fit-at-inference, per tenant. Each run reads that tenant's `metric_history`, fits a small linear trend in memory, returns a forecast, discards it. No stored weights, no training job, no cross-tenant learning. History accrues every run via `snapshot_metrics` (this is what makes B–D possible).
- **B — persisted per-tenant models.** Stop fitting per request. Fit on a schedule (nightly/weekly), store fitted state per tenant, serve from cache. Still one seller's data → one seller's model. First step that is "training" in the normal sense; also the operational scaffolding (job runner + model-state storage) everything later needs.
- **C — cohort / pooled models.** Train shared models across *similar* sellers (category × price band × marketplace) so a new seller benefits on day one — the actual network effect ("more sellers → better for every seller"). Hard guardrails live here: strict tenant data isolation in training (a seller's raw data never surfaces in another's output — only learned, aggregated patterns) + consent/governance for pooling.
- **D — continuous retraining.** Scheduled retrain on a rolling window with the production safety rig: drift detection, holdout evaluation, automatic rollback. This is "continuous training," and only makes sense once B and C exist.

### The task (concrete build)
1. **Swap the hand-rolled linear fit for in-process OSS, behind the existing contract.** Recommend **Nixtla StatsForecast** (AutoARIMA / ETS / Theta): pure in-process (no data egress → preserves isolation/compliance), fast across many short series, returns prediction intervals that map cleanly to the confidence gate, stays interpretable so the explainability trace survives. Same operational profile — no new infra. Keep the linear forecaster as the thin-history fallback (already abstains gracefully). Prophet is the alternative only if holiday/seasonality modeling becomes central (heavier, slower at SKU scale).
2. **Build the scaffolding *before* any remote/paid model** (this is also Phase B):
   - `model_predictions` cache table (+ `model_version`).
   - Scheduled fit/forecast job (move forecasting out of the request path).
   - `REGISTRY` loaded from a `models` table (add a model without a redeploy; enable per-tenant selection).
   - Async + batched model calls with a circuit breaker.
   - Shared feature-assembly helper so models stop re-querying `metric_history` individually.
3. **Medium term — the moat:** a tabular GBM (LightGBM/XGBoost) trained across SKUs within a cohort, with lagged + calendar + cross-SKU features (Phase C). SHAP gives defensible `top_features`. Needs the training job + artifact storage + cohort isolation/governance.
4. **Continuous retraining** with drift detection + rollback (Phase D).

### Invariants to preserve (do not cross)
- **Deterministic detectors always decide** the numbers and thresholds. Models inform; they never decide or set a threshold — paid or OSS.
- **Prefer interpretable models** (ARIMA/ETS, GBM+SHAP) over black-box, even at some accuracy cost — the explainability trace is worth more to Realify than a marginal MAPE gain.
- **Keep the LLM out of numeric forecasting.** L2 stays phrasing-only.

### Recommendation summary
Near term: StatsForecast in-process behind the contract (strict upgrade, no new infra). Then the cache +
scheduled-job + registry-table scaffolding (= Phase B). Medium term: cohort GBM for the network effect (Phase C),
then continuous retrain (Phase D). Be skeptical of hosted/paid forecasting for the **core numeric layer**
(latency × volume cost, third-party data egress, loss of control). A foundation time-series model
(TimeGPT, or open-weight Chronos / TimesFM) is worth a **bounded** experiment for **cold-start only**
(brand-new SKUs with no history) — adjunct, not backbone.

### Acceptance criteria
- A new model can be added by inserting a row + class and toggling per tenant — **no redeploy**.
- Forecasts are served from the `model_predictions` cache; `materialize` makes **no synchronous model network calls**.
- Predictions carry `model_version`; explainability trace still shows interpretable `top_features`.
- Confidence gate still abstains on thin data; deterministic feed is byte-identical when all models are disabled.

### Open questions / to verify
- Confirm current status of **Amazon Forecast** (believed wound down / closed to new customers) — wrong default here regardless.
- **Build-vs-buy** for the training stack (own job runner + feature store vs. a managed ML platform) — decide at Phase B/C boundary.
- Cohort definition + **consent/governance** model for pooling (Phase C blocker).

---

## #002 — Source control + Path A AWS hosting (shipped) + open items

- **Status:** In progress (deployment shipped & live; CD + security pass + Path B still open)
- **Logged:** 2026-06-26
- **Priority:** Done-core / Medium for remainder
- **Area:** repo, infra (AWS), deploy/runbook

### What shipped (live as of 2026-06-26)
The prototype is hosted, encrypted, and reachable by invited users at **https://realifyai.app**.
The full chain works: Mac → GitHub → AWS, containerized, persistent data, auto-restart, LLM working in prod.

**Source control**
- Private GitHub repo `realify-mc`. `main` branch.
- `.gitignore` protects `.env`, `*.db*`, `__pycache__`, `outputs/`, venvs.
- `README.md` + `.env.example` committed.
- Auth via GitHub CLI (`gh`) on both Mac and server.

**Hosting — Path A (single instance + SQLite)**
- EC2 `realify-app`: Ubuntu Server 24.04 LTS, **t3.small** (2 GB RAM), 20 GB gp3.
- **Elastic IP** allocated + associated (static; survives stop/start). This is now the SSH + DNS target.
- Security group: SSH 22 from My IP; HTTP 80 + HTTPS 443 from 0.0.0.0/0.
- Docker installed (`get.docker.com`); `ubuntu` in the `docker` group.
- Image `realify-mc` built from a server-side `Dockerfile` (python:3.12-slim, installs requirements, `python3 run.py init && start`, EXPOSE 8001).
- Container run: `--name realify --restart unless-stopped --env-file .env -p 127.0.0.1:8001:8001 -v /data:/data`.
  - App binds `0.0.0.0:8001` inside the container (already correct in `run.py`).
  - **Data persistence:** `REALIFY_DB=/data/realify_mc.db` (env override; `config.py` reads it) + host `/data` (on the EBS volume) mounted in. DB survives container rebuild/redeploy. `/data` owned by `ubuntu`.
  - App republished to **localhost only** (`127.0.0.1:8001`) so Caddy owns the public ports.

**Domain + HTTPS**
- Domain **realifyai.app** registered at **Cloudflare** (Route 53 registration was flaky → used external registrar; DNS + registration are separable).
- Cloudflare DNS: `A` record, name `@` → Elastic IP, **proxy OFF (grey cloud / "DNS only")** — required so Caddy can complete the ACME challenge.
- **Caddy** reverse proxy in front: `/etc/caddy/Caddyfile` = `realifyai.app, www.realifyai.app { reverse_proxy 127.0.0.1:8001 }`. Auto Let's Encrypt TLS. Runs as a systemd service.
- `.app` TLD is HTTPS-only by browser design — reinforces the setup.

**Security**
- Anthropic API key **rotated** after setup (old key revoked) — it had been typed into commands on a now-public box during debugging. New key in server `.env`; env vars only read at `docker run`, so the container was recreated to pick it up.

### Runbook (manual deploy, until CD lands)
```
ssh -i ~/.ssh/ShivasKeyPair.pem ubuntu@<ELASTIC_IP>
cd ~/realify-mc && git pull
docker build -t realify-mc .
docker stop realify && docker rm realify
docker run -d --name realify --restart unless-stopped --env-file .env \
  -p 127.0.0.1:8001:8001 -v /data:/data realify-mc
```
Notes: editing `.env` requires recreating the container. `/data` (DB) is never touched by rebuilds.
Pitfalls hit during setup: heredoc `EOF` must be on its own line (use `printf` for `.env`); `docker build` needs the trailing `.`; stay in `~/realify-mc` (don't spawn a nested `bash` that drops to `$HOME`).

### Open items
1. **Commit the server-side `Dockerfile` back to GitHub** so the box is reproducible (`git add Dockerfile && git commit -m "chore: add Dockerfile" && git push`). ⬜ confirm done.
2. **`www` CNAME** in Cloudflare (`www` → `realifyai.app`, grey) if `www.` should resolve. Optional.
3. **CD — auto-deploy on push to `main`** (GitHub Actions): build, then deploy via SSM run-command (Path A) or `aws ecs update-service` (Path B). Use **GitHub OIDC → IAM role** (no long-lived AWS keys in GitHub). Add a **staging** target + environment protection (manual approve for prod). Also stand up CI first: `ruff` + `pytest` (TestClient suite) as required checks; branch protection on `main`.
4. **Security pass before real customer data** (explicit gate — not met yet): rate limiting, review the `REALIFY_ADMIN_KEY` admin-endpoint path, SSH/server hardening (e.g. fail2ban, key-only auth), automated backups of `/data` + tested restore, billing alarm confirmed (`billing-over-20`). Cleared today only for **owner + invited testers**.

### Sub-task — Path B scale migration (its own future entry when triggered)
Trigger is concurrency/uptime need, not a date. Path A caps at a single instance because **SQLite is single-writer** and the **scheduler runs in-process** (multiple workers/instances ⇒ duplicate jobs + write contention; v1 is single instance, single uvicorn worker).
When triggered:
- **SQLite → RDS Postgres:** port the `db.py` layer; replace `PRAGMA`/`ALTER` migrations with **Alembic**. (Biggest work item; warrants its own logbook number.)
- **Extract the scheduler** out of the web process (separate ECS service or EventBridge-scheduled task) so the web tier can run multiple workers/instances.
- **ECS Fargate behind an ALB**, autoscaling, RDS; add CloudWatch logs/metrics/alarms + structured logging; automated RDS backups + tested restore.
- Containerizing from day one (done) means Path B is largely a config/infra change, not an app rewrite.

---

## #003 — Accounts, organizations, admin console, FAQ + ops hardening

- **Status:** Done (all shipped & deployed to prod)
- **Logged:** 2026-06-27
- **Priority:** Done
- **Area:** product (onboarding, accounts, tenancy), admin, login page, infra/ops

### What shipped (live as of 2026-06-27)

**Account types — tester vs customer**
- `tenants.account_type` ∈ {tester, customer, NULL}, chosen at a post-signup gate ("How will you use Realify?").
- Lock is tied to `tenants.provisioned`, NOT to first-set: freely switchable while exploring, **locked once provisioning succeeds** (a failed customer upload leaves it switchable). Endpoint returns 400 invalid / 409 locked.
- Gate has a "← Log out" link (clears session → /login) and the onboarding panels have "← Choose a different account type" back-links — no dead-ends, no premature lock-in.
- **Tester** = unchanged (demo / ASIN + full synthesis; wipe/resynthesize allowed).
- **Customer** = NO synthesis ever.

**Customer no-synthesis onboarding**
- Graceful-degradation is the enabling mechanism: L1 `_cmp(val,op,thr)` returns False on NULL, so unprovided fields simply produce no card (verified: only real-data signals fire, no false cards on NULL).
- `catalog_only_seed` builds the SKU spine from a real catalog/listings export (real price/title/category; all behavioural metrics NULL; `annual_rev_inr=0` sentinel to avoid None>num crash). Margin is *derived* from price − COGS − referral % (real math, not fabrication).
- `realify/cogs.py`: COGS template (sku,cogs,currency,+title) + validate (rejects blank SKU / non-numeric / ≤0 / duplicate-in-file / SKU-not-in-catalog) + apply (recompute referral/net/margin/floor). Partial provisioning allowed; rejects logged to `pull_log` (surfaced in Log tab). Floor = catalog + ≥1 valid COGS.
- `/api/onboard/customer` (multipart: cogs file + channel reports tagged channel:/report:): wipe → catalog spine → COGS validate/apply → layer other reports by kind → `scheduler.start_provision_customer` (no synth, no synthetic history backfill; **market enrichment stays ON**).
- Server guards (defense-in-depth): customer 403 on synthetic `/api/onboard`, `/api/wipe`, `/api/settings/resynthesize`. Demo never on a customer tenant.
- Account-tab customer surfaces: wipe/resynth hidden; **data-completeness panel** (`/api/data/completeness` → X/N detectors active + which report unlocks each); report re-upload (reuses the channel grid) + COGS re-upload (`/api/cogs/upload`), each processed/persisted as it arrives, pipeline re-runs.

**Organizations + invites**
- A tenant IS the organization. Signup = create-org (first member, role owner).
- `invites` table (tenant_id, email, role, token_hash, status, expires_at, created_by/accepted_by). Tokens stored **SHA-256 hashed**; raw token only in the link. Single-use, 14-day expiry.
- No-email flow: owner generates an invite → server returns a copy-ready email **body + subject + /join?token=… link** (built from request.base_url, so it's correct on localhost and prod). Owner sends it themselves (no SMTP).
- Join flow: `/join?token=` page mode (preview shows org + locked email), `POST /api/join` (accept_invite) attaches the new user to the inviting tenant, inheriting its account type.
- Account-tab "Team & invites": list members, create invite, revoke pending. Same access for all members for now (role recorded for a future read-only tier).
- **Limitation:** `users.email` is globally unique → one person = one org. Inviting an existing email → 409. (Future: membership across orgs; ownership transfer.)

**Self-service account/org deletion**
- `/api/account/delete`: requires re-entered password; resolves from role + member count. Single-member org OR owner of multi-member org → full `delete_tenant` (all tenant-scoped tables + invites + usage_events + users + the tenant row; **frees the email** for re-provisioning). Non-owner of multi-member org → `delete_user` (leave org; org survives). Full deletes require type-to-confirm ("delete").
- Account-tab "Danger zone" adapts label to scenario. Verified: wrong pw 403, missing confirm 400, solo delete → email freed → re-signup works → fresh gate; leave-org preserves the org.

**Admin operator console (`/ops`)**
- Key-only gate (`x-realify-admin` == `REALIFY_ADMIN_KEY`; `require_admin` no longer needs a tenant session). `/robots.txt` disallows /ops + /analytics; `X-Robots-Tag: noindex` on the page. (Obscurity is hygiene; the key is the control.)
- Panels: system health (`/api/admin/system` — counts, DB size, MODE live/fixture, API-key presence, per-source pull status), usage statistics (reuses analytics summary + link to `/analytics`), tenants/orgs table (`/api/admin/tenants`), and key-gated links to the architecture doc (`/ops/architecture?k=`) and logbook (`/ops/logbook?k=`).
- Docs vendored into the repo at `docs/` so they deploy with the app.
- **Caveat:** doc links pass the admin key as `?k=` (lands in history/logs) — acceptable for an internal doc; switch to a short admin-session cookie when auth is hardened.

**Login-screen FAQ**
- 9 Q&As (single-open accordion) below the sign-in card. Title: "FAQs (Frequently Asked Questions)".
- Self-contained animated SVG/CSS visuals (NOT recorded GIFs — GIFs can't be bundled, are heavy, need test data): two-plane flow (Your numbers → Rules + ML decide → AI explains), mini prioritized feed, L1/Model/L2 explainability trace, completeness pills. Animations trigger on scroll-into-view (IntersectionObserver) + replay on open.
- Ambient music: generated Web Audio pad behind a speaker toggle, **default off** (browsers block autoplay-with-sound; generated audio avoids file weight + copyright).
- Layout: hero is a vertical column (card + cue stack), no full-viewport gap before the FAQ.

### Config correction (carried from earlier, locked here)
- `config.py` reads **`KEEPA_KEY`** (NOT `KEEPA_API_KEY` — the old name was silently ignored) and **`NEWS_API_KEY`** (NewsAPI.org — it IS used by the news collector). Keys do nothing unless **`MODE=live`** (or per-source `MODE_KEEPA`/`MODE_NEWS=live`); default is `fixture`. Keepa burns tokens per query; NewsAPI free tier is rate-limited/server-restricted.

### Standing rules added (process)
1. **Every build response ends with three deploy sections:** (1) deploy locally + test, (2) commit to Git, (3) deploy to AWS + test.
2. **Update the architecture HTML on architectural builds** (new tables/endpoints/data flow/tenancy). Done for this entry — addendum appended to `docs/Realify-Architecture.html`.
3. **Safer deploy sequence** (see ops incident below): `docker stop realify` before `docker build` (frees ~370MB RAM), and verify the boot log shows `[init] schema + rules catalog ready at /data/realify_mc.db` (the `/data` path, not bare `realify_mc.db`).

### Ops incident — prod outage 2026-06-27 (resolved)
- **Symptom:** realifyai.app unreachable; EC2 **Instance status check: failed**. Reboot didn't clear it; stop hung ("stopping"); recovered via **force stop ("skip OS shutdown")** → start. On a clean boot, Docker (`--restart unless-stopped`) and Caddy (systemd) self-restored; site came back.
- **Root cause (high confidence, circumstantial):** memory exhaustion. Disk was fine (25% used, 6MB reclaimable Docker cache — ruled out the disk/cruft theory). The box is **t3.small (2 GB RAM) with NO swap**, and we'd run many `docker build`s (compiles wheels via build-essential) → OOM-killer wedged the OS → status-check failure. A clean boot cleared the transient pressure.
- **Fixes applied:**
  - **Added 2 GB swap** (`/swapfile`, persisted in `/etc/fstab`) — removes the actual fragility. Confirmed `Swap: 2.0Gi`.
  - **Stop-container-before-build** added to the deploy ritual.
  - DB integrity after the force-stop: `PRAGMA integrity_check` → `('ok',)` (no corruption; force-stop was low-risk since the site was already down / no live writes).
- **Forensics note:** persistent journald wasn't enabled, so the crash-boot OOM line wasn't captured. Enabled going forward (`/var/log/journal`) so `journalctl -b -1 | grep -i oom` works next time.
- **Heavier future fix (optional):** build the image on Mac/CI and pull on the server (registry) so the t3.small never compiles — eliminates build-time memory risk. Swap + stop-before-build is the proportionate fix for now.

### Deploy lessons (carried)
- `docker exec ... run.py init` does NOT inherit `--env-file`, so it migrates a throwaway `realify_mc.db` instead of `/data/...`. To migrate the live DB by hand: `docker exec -e REALIFY_DB=/data/realify_mc.db realify python3 run.py init`. (Normal boot is fine — the container's `CMD` runs init with the env from `--env-file`, provided the container is genuinely recreated from the rebuilt image — use `docker rm -f`.)
- Hard-refresh (Cmd+Shift+R) after deploying login-page changes — the login HTML/CSS/JS caches aggressively.

### Open items / not yet done
1. **Logbook #002 open items still stand:** commit server Dockerfile to repo (confirm), optional `www` CNAME, **CD auto-deploy** (GitHub OIDC), and the **security pass before real customer data** (rate limiting, admin-key review, SSH hardening, automated `/data` backups + tested restore).
2. **Read-only / scoped member roles** + per-member removal + ownership transfer (role is recorded but unused).
3. **Parser column-mapping fallback** for messy real-world report formats — the biggest ongoing investment.
4. **Admin auth hardening** — replace `?k=` doc-link with an admin session cookie; consider an `admins` table (multi-admin) over the single shared key.
5. **Pricing FAQ (Q10)** — deferred until a pricing model is decided.
6. **Path B** (Postgres/Alembic + extracted scheduler + ECS Fargate) — still triggered by concurrent multi-user load, now more relevant with orgs/invites enabling multiple users per tenant.

---

## #004 — Ad spec: Margin × Ads fusion (CMAA)

- **Status:** Backlog (spec'd, not built)
- **Logged:** 2026-06-28
- **Priority:** High — this is the Adbrew-differentiating wedge and the flagship "profit, not ads" detector
- **Area:** detector logic (L1), model layer (TACoS/what-if), ingestion (ads + fees), product (Profit & Ads view)
- **Source:** `margin-x-ads-build-guide-for-CPO.md` (uploaded), plus the Adbrew gap analysis.

### The one idea
**Break-even ACoS = gross contribution margin %.** If an ad-driven sale's ACoS exceeds the item's margin %, you're buying unprofitable revenue. This turns the existing margin engine into an ads engine for free. The product metric is **CMAA — Contribution Margin After Ads**:
```
CMAA/unit = (price − COGS − all fees − returns) − (ad_spend ÷ units)
          =  gross contribution margin           −  ad cost per unit
```
Maximizing CMAA is the product. (Math verified: marginal ad unit's ad cost = ACoS×ASP; break-even when GCM = ACoS×ASP ⇒ ACoS = GCM/ASP = GCM%.)

### Why it's the wedge
Adbrew (and PPC-only tools) optimize ACoS **in isolation** and are **Amazon-ads-only**. They structurally cannot see that cutting spend is wrong when the real problem is margin or an imminent stockout. CMAA subordinates ads to unit economics, across channels. Don't fight Adbrew on bid-algorithm depth — reframe ads as one input to a profit decision. The cross-channel version (Amazon + Shopify) is something a PPC specialist can't follow.

### The action quadrant (per item, rules-as-data)
- margin_ok = `gcm_pct >= MARGIN_FLOOR` (customer-tunable threshold)
- ads_ok = `acos <= breakeven_acos`
- SCALE (both ok) · FIX ADS (margin ok, ads not) · FIX MARGIN (ads ok, margin not) · CUT/DIVEST (neither)
- Headline number: **"$X of ad spend is above break-even"** = `Σ max(ad_spend − ad_sales×breakeven_acos, 0)` over inefficient items. This is the line that sells.

### THREE CORRECTNESS GUARDS (build from the start — the math being right ≠ the recommendation being safe)
1. **Organic halo / TACoS.** Raw ACoS ignores ad-driven organic lift, so the naive quadrant will tell you to CUT ads that are actually profitable. ACoS-break-even is the *entry heuristic*; **TACoS-over-time is the honest steady-state metric**. Caveat all CUT/FIX-ADS calls until TACoS trend exists. (Rising TACoS + flat total sales = cannibalization: funding sales you'd get free.)
2. **Lifecycle guard.** Launch-phase SKUs intentionally run ACoS above break-even to buy rank/reviews. Suppress CUT/FIX-ADS on new SKUs (low age / low review count / user-flagged "launching"), or the quadrant emits false positives that look naive to a serious seller.
3. **Certain vs estimated, enforced at the schema level.** "Recovered waste" (spend above break-even) is *certain*; "reallocation upside" is *modeled* (cutting spend usually drops ad_sales AND organic). Never sum them. Apply a conservative haircut to estimates, label them ESTIMATE, keep them visually + structurally separate. *Trust beats optimism.*

### Data inputs (Amazon Seller Central, IN — Phase 0/1 is Amazon-only)
The CMAA logic is channel-agnostic; the **data plumbing is not symmetric** (Amazon = one clean ecosystem; Shopify = orders + Meta/Google/TikTok ad spend with messy attribution → later phase).
- **Business report** → exact name **"Detail Page Sales and Traffic By Child Item"** (Reports → Business Reports → By ASIN). units, sales, sessions, conversion. [conf: high]
- **Advertised Product Report** (+ Search Term Report) → **Amazon Ads console**, NOT Seller Central (Sponsored Ads → Measurement & Reporting → report type "Advertised product"/"Search term"). spend, ad_sales, ad_units, ACOS. [name high / menu medium]
- **Settlement/fees** → assemble, not one file. Settlement/transaction flat file (Reports → Payments → Reports Repository) is the cleanest single source for per-unit referral+FBA in IN; storage fees separate (Fulfillment). "settlement_fees.csv" is a *derived* file. [medium — messiest input]
- **Returns** → FBA: "FBA Customer Returns" (Reports → Fulfillment); FBM: Returns Reports. `return_cost` is **computed** (units × econ), not an exported column. [medium]
- **COGS** → NOT from Amazon. The customer's own master sheet (SKU → unit cost + inbound freight) = the COGS template Realify already has. [certain]
- Join is ASIN ↔ SKU. **The persisted SKU↔ASIN map is a first-class reusable asset** and the real ongoing cost — same cross-channel identity-resolution problem flagged as the biggest ongoing investment. Build the loader tolerant to report name/column variants; verify exact IN strings against live Seller Central or current help docs before wiring ingestion (no live account available at spec time).

### Reference implementation
The uploaded guide's pandas script is the reference logic (CSV in, ranked table + headline out). Null/zero guards present; roll up by **summing dollars then recomputing %** (never average %s). Port column names to the ingest layer.

### Phasing
- **Phase 0 — Prove the number (no product integration).** `tools/cmaa_poc.py` in the repo, hardened (consistent attribution window across spend & ad_sales; assembled fees; derived return_cost). CSV in → "$X above break-even" + ranked actions. On synthetic-but-real-shaped CSVs until a real account's 5 exports are available. Highest-leverage, few hours, de-risks the join, produces the sales/fundraising number.
- **Phase 1 — CMAA detector in Realify (L1/Model/L2).** New deterministic detector (CMAA, breakeven_acos, acos, tacos, wasted_spend) + quadrant as tunable rules; NULL-safe via `_cmp` (no ads/fees → no card). Cards ranked by `rank_score` weighted on wasted_spend. New "Advertised Product Report" ingest kind, **period-aware** (ads are period totals — needs a time dimension the snapshot model may not fully have; FLAG). Completeness panel lists CMAA's required reports. **Architectural build → update architecture HTML.**
- **Phase 2 — Trust layer.** TACoS-over-time + cannibalization detection (Model layer, confidence-gated); lifecycle guard; what-if simulator ("cap ACoS at break-even on bottom quartile → +$Y") as a *separate* ESTIMATE-labeled function.
- **Phase 3 — Close the loop (later, gated).** Approve → write-back to Amazon Ads API (bid/budget). Competes on action, not just insight = the real Adbrew endgame. Gated behind production-grade/security (Tier 0) work; stays co-pilot (approve-each-action), never autopilot.

### Open questions (Shiva to answer on return)
1. Phase 0 data: real account's 5 CSVs, or build on synthetic-shaped data first? (Recommend: build synthetic-shaped now, drop real data in when available.)
2. Do current ingest reports capture ad data **over time** (multiple periods) or only a snapshot? Determines whether TACoS/cannibalization is near-term or needs a data-model change first.
3. First design partner Amazon-primary or Shopify-primary? (Recommend Amazon-only for Phase 0/1; Shopify = deliberate later phase, where the work is multi-platform ad-spend ingestion + attribution reconciliation, not the CMAA math.)

### Dependency / sequencing note
Sequence Phase 1 against Tier-0 production-readiness (#003 open items: backups + security pass): CMAA on real customer data raises the stakes on data correctness, and Phase 3 write-back can't precede the security pass.

**Decided 2026-06-28 — build order vs. the #005 refactor (Postgres + layering):**
- **CMAA Phase 0 (the `tools/cmaa_poc.py` PoC) runs BEFORE / in parallel with the refactor.** It's a throwaway standalone script touching no core code, and it's the highest-leverage *sales/fundraising* artifact in the 30–60 day window (produces the "$X above break-even" number). Blocks nothing; on its own track.
- **CMAA Phase 1 (the real detector) is built AFTER #005 Phase 1 (RDS + refactor).** Reason: the detector lives exactly where the refactor is rebuilding the floor — detectors move to `domain/`, data access to `repositories/`, and CMAA needs period-aware ads ingestion + the certain-vs-estimated schema split that land in the refactored structure. Building it first = paying for it twice (the "twice" trap).
- **But the seams are designed INTO #005 Phase 1** so the detector drops onto prepared ground: the period-aware ads time dimension, the Advertised Product connector slot in the `ChannelConnector` interface, and the certain/estimated dollar separation at the schema level. See #005 scope.
- Open question #2 (ads over time vs. snapshot) becomes a **conscious Phase-1 schema decision** during the refactor — another reason the detector waits for it.

---

## #005 — Production-scale architecture: Phase 0/1 (RDS Postgres + refactor)

- **Status:** In progress — Phase 1 workstreams **1b**, **1a/1f**, **1e**, **1c** (SQLAlchemy + Alembic + Postgres), and **1g** (data migration) all COMPLETE; **production cut over to RDS Postgres 2026-06-30**. Remaining: **1d** (Postgres row-level security, now unlocked) and the rest of the **Phase 0** safety gate (tested-restore drill + secrets → Secrets Manager). See *Build log* at the end of this entry.
- **Logged:** 2026-06-28
- **Priority:** High — critical path to paying customers
- **Area:** data layer, app architecture, infra, maintainability
- **Forcing function:** paying customers in **30–60 days**. 200 customers × 10 users ≈ 2,000 users, dozens concurrent at peak.

### Principal-engineer framing (the load-bearing judgment)
At this scale the system runs fine on **Postgres + a stateless API + the existing in-process scheduler** (now that swap + right-sizing prevent OOM). The goal is **build the seams now so scaling later is config, not a rewrite** — and **do NOT put Temporal or autoscaling on the pre-launch critical path** (adding a distributed system while racing to first revenue is the bigger risk). Build boundaries now; defer the expensive machinery (Temporal cluster, autoscaling, read replicas) until load justifies it.

### Decided scope
- **Postgres target:** **RDS** (managed; not a container on EC2) — matches the elastic-on-demand requirement.
- **Refactor is folded INTO Phase 1** (one disruption, not two) — the maintainability ask is far cheaper during the migration than after.
- **Temporal:** **Temporal Cloud** when adopted (post-launch), not self-hosted. (No single AWS AMI exists; self-host = Helm chart on EKS backed by RDS + OpenSearch — a platform-eng commitment to defer. Keep Temporal's datastore separate from app data.)

### Phase 0 — Safety gate (~1 week, blocks Phase 1 going live with real data)
- Automated backups + **tested restore drill** (RDS snapshots/PITR once on Postgres; the drill is the deliverable).
- Security pass: rate limiting (auth + expensive endpoints); admin key off URLs (session cookie for `/ops` doc links); SSH key-only + fail2ban; secrets → **AWS Secrets Manager / SSM** (out of `.env`-on-box); billing alarm confirmed.
- Health checks + auto-recovery: `/healthz`, container `HEALTHCHECK`, CloudWatch status-check alarm.

### Phase 1 — RDS Postgres + maintainability refactor (the 30–60 day core)
End-state package layout (layered; nothing skips a layer; detectors never touch HTTP or SQL):
```
realify/
  api/   auth.py onboarding.py ads.py admin.py integrations.py account.py   # thin routers (break up run.py)
  services/   # use-case orchestration
  domain/     # pure logic: detectors, rules, CMAA math — no I/O
  repositories/   # ONLY place that talks to the DB
  connectors/     # ChannelConnector plugins (integration seam)
  tasks/          # TaskRunner interface + background impl (Temporal seam)
  config/         # pydantic-settings; no magic numbers
  db/             # engine, session, Alembic migrations, RLS policies
  models/         # SQLAlchemy table defs
```
Workstreams:
- **1b Repository layer** — every SQL statement behind `*Repository` classes; build on **current SQLite first** with TestClient green (decouple data access before changing DB). The key de-risking step.
  - *Progress (2026-06-29):* shipped `repositories/` (BaseRepository + UnitOfWork) and migrated contexts — **identity/tenancy** (Tenant/User/Invite), **settings**, **pull-log/watermark**, **metrics/history**, and the **card/feed READ path** (CardRepository, via api.py). db.py keeps thin delegators so legacy callers are unchanged. `auth.py` on UnitOfWork as the reference impl. Tests: tests/ (13 across repo unit + me-regression + read-path integration). Card **write/materialization** path now also migrated (2026-06-29): CardRepository gained upsert/prune_stale/existing_dedup_keys (materialize.py), set_status (tasks dismiss/done), save_research/clear_research + card reads (research.py, scheduler.py), count_all/count_distinct_types (run.py admin, synth_conditions). Card write methods don't commit — caller owns the transaction (preserves single-commit materialization). Tests: tests/test_card_write.py (dedup, prune preserves dismissed/done, status writes, research save/clear). The **cards table is now fully behind CardRepository.** Remaining 1b: seller/catalog and rules contexts.
- **1a/1f Refactor** — split `run.py` (~50 endpoints) into domain routers; layered architecture enforced; **file-length cap (~400 lines) in CI lint**; module docstrings.
- **1c SQLite → RDS Postgres** — **SQLAlchemy Core** (not full ORM) + **Alembic** (replaces hand-rolled PRAGMA/ALTER migrations); **PgBouncer/RDS Proxy** pooling from day one; app runs on SQLite (local) or Postgres (prod) **by config alone** during transition.
- **1d Tenant isolation via Postgres RLS** — per-table policies + per-request `SET app.tenant_id` (applied in the repository layer); isolation becomes a DB guarantee, not query discipline. (Satisfies "clean data separation.")
  - **RLS × pooling correctness (must handle explicitly):** a pooler (PgBouncer/RDS Proxy) hands the same physical connection to different requests, so `app.tenant_id` must be set **per-transaction** in the repository layer and **reset on checkout/return** — a pooled connection must never carry one tenant's context into another tenant's request. (Use `SET LOCAL` within a transaction, or reset on release; avoid session-level state that outlives the request.) This is exactly why pooling + RLS both live in the repository layer (the single connection-checkout point). Flag for the security reviewer before real customer data — a bug here is a cross-tenant leak.
- **1e Config + two future-proofing seams (built now, even if unused):**
  - **Typed config** (pydantic-settings) — every threshold/rate-limit/endpoint/flag from env/secrets; **zero hardcoded constants** (the "no hardcoded stuff" requirement).
  - **Config-driven formula coefficients (added 2026-06-29):** every coefficient in the deterministic-math layer (referral_pct, FBA fee base/per-band, rank weights — severity_weight, the 250000 exposure scale, ×60/×3 factors, 21-day urgency knee, ×8 slope — trend window=14d, per-rule thresholds) becomes typed config / rules-as-data, **zero hardcoded numbers in the economics path**. Formula *structure* (e.g. `net = price − COGS − referral − FBA − ad − returns`) consolidates from its scattered copies (seller.py/seed.py/cogs.py/multichannel.py) into ONE pure function per identity in `domain/economics.py` — so structure changes happen in one tested place. **Deliberately NOT supported: arbitrary formula expressions in config** (injection surface, untestable, breaks auditability). Coefficients = data; structure = reviewed code with one owner. Reference: **docs/FORMULAS.md** (shipped 2026-06-29, served at `/ops/formulas`) is the single source of truth for the L1 math and this policy; keep it in sync when formulas/coefficients change.
  - **`TaskRunner` interface** — provisioning/scheduler/integration pulls call `task_runner.run(...)`; current impl = simple background worker; **Temporal is a later swap of this impl, not a rewrite**. (Also the structural OOM fix: heavy work leaves the web process.)
  - **`ChannelConnector` interface** — `authenticate / fetch_reports / normalize / write_back`; existing report-kind ingestion refactored as the first connector; a new marketplace = implement interface + declarative field-mapping config, touching no core code. Shared **ASIN↔SKU identity-resolution** service (the biggest ongoing investment) used by all connectors.
- **1g Data migration** — one-shot script reads live `/data/realify_mc.db` → RDS **through the new repositories**; dry-run on a copy; reconcile row counts; keep SQLite as rollback; cutover in a maintenance window with a backup taken immediately before. **Riskiest hour — treat with care.**
- **1f Maintainability scaffolding** — CI gates (`ruff` + `pytest`/TestClient + repository tests vs. real Postgres via testcontainers) required on `main` + branch protection; **ADRs** (why RDS, RLS, repository pattern, TaskRunner seam); "how to add a connector / a detector" guides; **structured logging** (tenant_id on every line) + error tracking (Sentry); architecture HTML updated (standing rule).

**Phase 1 sequence (each step shippable; `main` always runnable):** (1) repository layer on SQLite + tests → (2) run.py→routers + config extraction (no behavior change) → (3) SQLAlchemy Core + Alembic, still SQLite → (4) stand up RDS, flip by config, RLS → (5) data-migration dry-run → cutover with rollback → (6) TaskRunner + ChannelConnector seams → (7) CI gates + ADRs + observability.

### Auth & OAuth seam (sign-in + integrations) — added 2026-06-28
Two distinct OAuth needs; the architecture must account for both, and the seams go into the Phase 1 auth refactor (cheap now, painful to retrofit post-launch):
- **Integration OAuth (Amazon SP-API/Ads, Shopify, Walmart…) — already accounted for** by the `ChannelConnector.authenticate()` seam (1e). Make explicit: a **per-tenant encrypted credential store** (access + refresh tokens, scopes, expiry, keyed by tenant + connector); token refresh as a TaskRunner/Temporal activity; a per-connector OAuth redirect/callback endpoint. Tokens are secrets → Secrets Manager / encrypted column, never plaintext, never in logs.
- **Sign-in OAuth ("Sign in with Google" / user creation) — partial today** (auth is password-only: `pw_hash`/`pw_salt`). Introduce an **identity abstraction during the Phase 1 auth refactor**:
  - `user_identities` table (user_id, provider, provider_subject, email_verified) separating *identity* from *user* — a user can have a local password and/or ≥1 OAuth identities.
  - Auth-provider interface (LocalPassword, GoogleOAuth, …): adding a provider = implement interface, not rewrite auth.
  - OAuth callback + **state/PKCE**; **account-linking policy** = link to an existing account only on a *verified* matching email (else account-takeover risk).
  - Still routes through the existing **create-org vs. join-via-invite** gate (#003).
- **Build-vs-buy decision (OPEN, needed before building auth in Phase 1):** hand-roll OAuth vs. managed identity provider (Cognito / Auth0 / Clerk / WorkOS). Given small team + minimal-ops + likely future enterprise SSO, a managed provider for *sign-in* is worth serious consideration (changes where identity/session lives). Integration OAuth is custom regardless.
- **Security:** OAuth is a classic foot-gun (state/PKCE, token storage, linking takeover) → human security reviewer before real customer data.
- **Net:** integration OAuth is covered by the ChannelConnector seam; sign-in OAuth needs the identity abstraction added to Phase 1 — build the seam now even if only local-password + one provider ship initially.

### CMAA (#004) seams to bake into Phase 1
Per the #004 decision (PoC before; detector after the refactor), design these in now so the CMAA detector drops onto prepared ground:
- **Period-aware ads time dimension** in the schema (ads are period totals — resolve open-Q#2 here, consciously).
- **Advertised Product Report connector slot** in the `ChannelConnector` interface.
- **Certain-vs-estimated dollar separation at the schema level** (so recovered-waste and modeled-upside can never be summed by accident).

### Billing/entitlement (#006) seam to bake into Phase 1
The **entitlement layer** (tenant plan + insight-limit enforcement) folds into Phase 1 — it's a tenant attribute + an enforcement check + a card lock/blur hook, on the same tenant/plan model being migrated. Build the seam now even before Stripe is wired:
- `tenants.plan / stripe_customer_id / subscription_status / plan_limit` (limits from config, not hardcoded).
- Stable insight id + per-tenant visible/entitled count (if "view distinct insights" metering — see #006).
- `billing_events` table (Stripe event id unique → idempotency).
- Entitlement check lives in `domain/`, channel-agnostic, **works even if Stripe is unreachable**; Stripe stays an adapter behind an interface (like ChannelConnector/auth provider). Stripe wiring itself = its own phase ~launch (see #006).

### Extensibility contract — the platform handoff (FIRST-CLASS Phase 1 deliverable)
A team picks up OAuth (#005 auth) and Stripe (#006) **right after Phase 1**, so the highest-value Phase 1 output is the **contract that lets another team build a component without touching core or being able to break tenant isolation.** The refactor IS the platform handed to them. Seven required elements:
1. **Stable extension points (ports/interfaces):** `ChannelConnector`, `AuthProvider`, `BillingProvider`, `Detector`, `TaskRunner` — each an abstract interface with a documented contract. New component = implement interface, never edit core (dependency inversion: core depends on the interface; the plugin depends on core's interface; teams build *outward*).
2. **Registry, not a switch:** components self-register (registry / entry-point), so adding one never edits a central `if provider==…`. No cross-team collisions in one file.
3. **Canonical model at the boundary:** a component translates vendor shape ↔ canonical domain types (the `internal_sku` spine) and **never touches the DB directly** — goes through repositories / returns domain objects. Prevents a plugin from corrupting data or bypassing RLS.
4. **Tenant context is injected, not chosen:** the component receives an already-tenant-scoped context/session; it physically cannot reach across tenants. A contributor who forgets isolation still can't leak — platform enforces it, not the plugin. (Ties to RLS + repository-layer `SET app.tenant_id`.)
5. **Config + secrets via the platform:** each component declares a typed (pydantic) config schema and reads secrets through the platform's secrets interface — never hardcodes, never logs tokens. (Extends "no hardcoded stuff" to plugins.)
6. **Contract test kit per interface:** each interface ships a test harness the implementer runs against their component (e.g. connector harness asserts `normalize()` matches canonical schema). Keeps quality **without line-by-line review** — components prove conformance.
7. **Reference implementation per interface:** existing report-ingestion refactored as the canonical first `ChannelConnector`; `LocalPassword` as the first `AuthProvider`. Teams copy a working example — the biggest accelerator.

**Documentation deliverable:** `docs/EXTENDING.md` (contributor guide) — architecture overview, layered rules, a "how to add a {connector / auth provider / billing provider / detector}" recipe each, do's/don'ts, contract-test instructions. Plus **versioned interfaces + an interface CHANGELOG + ADRs** so downstream teams are warned when a contract changes. The architecture HTML gains an **extension-points diagram** when Phase 1 builds the interfaces (standing rule).

**Trade-off (accepted):** this raises the Phase 1 bar — interfaces must be designed as real external contracts, not just internal seams — but it's what lets the team move in parallel afterward, so it's the right call.

### Parallelization (where it pays — Phase 4, post-launch)
Fan out the I/O-bound, per-tenant/per-SKU work: one workflow **per tenant** for the scheduled refresh; **per-connector/per-SKU** report pulls (network-bound). Batch writes. Do NOT parallelize the fast deterministic detector math, and never fan out writes in a way that fights Postgres.

### After launch (deferred until load/integrations justify)
- **Phase 2:** Temporal (Cloud) swapped behind `TaskRunner`; scheduler + provisioning + integrations become durable, retryable workflows; workers autoscale independently of the API. First real marketplace integration is its proving ground.
- **Phase 3:** stateless API on **ECS Fargate** behind an ALB, autoscaled; **S3** for uploaded reports/generated files (removes last local-disk state); worker tier autoscaled on queue depth. "Elastic on demand" becomes real — mostly config because the seams exist.

### Guardrails / honest caveats
- If timeline tightens, cuttable = observability polish, some ADRs. **NOT** cuttable: repository layer, RLS, Alembic (ruinous to retrofit).
- Architecture guidance, **not a security audit** — Phase 0 security pass + RLS policies (tenant isolation especially) should get a human security reviewer before real customer data lands.
- Local-dev parity decision pending: dual SQLite/Postgres during transition (recommended) → Postgres-only once stable.

### Open decisions (to confirm before building)
1. Local dev: dual-backend during transition vs. Postgres-only (lean: dual, then Postgres-only).
2. Start point: begin at **1b (repository layer on SQLite, tests green)** — de-risks everything after, changes no behavior.
3. Auth: **hand-roll OAuth vs. managed identity provider** (Cognito/Auth0/Clerk/WorkOS) for sign-in — decide before building the Phase 1 auth refactor. (Integration OAuth is custom regardless.)

### Build log

**2026-06-29 — Workstream 1b (repository layer) COMPLETE & deployed.** All ~20 tenant-scoped tables now sit behind repositories in `realify/repositories/`; zero inline SQL anywhere outside that package. The only SQL left in `db.py` is its own schema DDL (correct — it is the data layer), and its single tenant write routes through `TenantRepository`. The sweep folded in the channel/order layer (seller_orders, traffic, inventory, settlements, products, channel_listings, returns, storage_fees), market data (keepa_snapshots, competitor_offers, tierc_signals), multichannel (channels, channel_economics), task/research outputs (actions_log, watchlist, sourcing_list, saved_briefs, card_why, runs), usage_events, plus stray sites in pull_log / metric_history / tenants / users that earlier increments had missed. A two-pass audit (table-name grep + strict `con.execute` grep) confirms zero remaining sites. 26 tests green via `pytest tests/`, including a new end-to-end provisioning test that proves every swept table is populated through the real pipeline, and a `conftest.py` that fixes a cross-file DB-isolation bug in the suite. Deployed live on EC2; verified by git-SHA match, presence of the sweep repo files inside the running container, and a clean inline-SQL audit in-container. **No behavior change by construction** (byte-for-byte SQL relocation), no schema change, data intact. Makes the Postgres swap (1c) a single change-point and RLS (1d) enforceable. Deploy-process note: the session also surfaced that the `rsync --delete` step orphaned the server's untracked `Dockerfile` and dropped `REALIFY_ADMIN_KEY` from `.env`; both fixed, and the next build commits the Dockerfile into the repo and tightens the rsync excludes.

**2026-06-29 — Workstream 1a/1f (router split + API versioning) COMPLETE & deployed.** `run.py` went from **1048 lines to 84** — `make_app()` is now thin wiring. All 81 route handlers moved **verbatim** (scripted slice-and-dedent, not retyped) into `realify/routers/`: eight concern-grouped modules (pages, auth, onboarding, insights, cards, settings, admin) plus two shared seams — `deps.py` (`current` / `require_tenant` / `require_admin`: the **single identity-resolution point**, written transport-agnostic and pluggable so the Kratos/OIDC cutover, a future WebSocket handshake, and agent API-key/M2M tokens swap only this one body, never the 81 handlers) and `helpers.py` (`page` / `_track` / `_log_import` / `_is_customer` / `BASE_DIR`). One real wrinkle, caught and fixed: the planned package name `realify/api/` collided with the existing `realify/api.py` service module (shadowed it, broke `api.explain_card` and 4 tests) → renamed the package to `realify/routers/`. The partner-facing read+action surface (insights + cards) is **dual-mounted at both `/api` (existing UI, byte-identical) and `/api/v1` (frozen partner contract)** — this FastAPI version wraps `include_router` in opaque `_IncludedRouter` objects, so parity was proven by a TestClient probe (all 81 original paths + 23 `/api/v1` aliases resolve, no 404, nothing extra) rather than structural route enumeration. Two new guards: `tests/test_card_contract.py` freezes the 27-field public card shape and asserts `/api` ≡ `/api/v1` (fails on a removed field *or* an undocumented leak; internal `tenant_id`/`run_id`/`dedup_key` allowed but not promised), and `tests/test_file_length.py` enforces a 400-line cap (largest file now `db.py` at 375). **29 tests green**; behavior-preserving by construction (verbatim move) and verified by the parity probe + full functional suite. No schema change; `/data` DB untouched. Architecture HTML gained an API-layer addendum. This build also ships the partner **Integration Guide expanded from 4 to 9 teams** across the session — added Identity/OAuth (Kratos + Google OIDC, §3G), Real-time/WebSockets (§3H), Advertising (#004, §3I), Payments & entitlements (§3J), and Agent platform (§3K), each with a contract + playbook + invariant; a re-pass confirmed the last three are architecturally sound on the 1a/1f seams with **no further refactor**. The `deps.py` seam is now the load-bearing convergence point: session today; the plug-in for Kratos sign-in, WebSocket-handshake auth, and agent tokens (a future multi-scheme resolver) tomorrow.

**2026-06-29 — Workstream 1e (typed config + TaskRunner + ChannelConnector + model-serving boundary) COMPLETE & deployed.** Built in order, every piece behaviour-preserving. **Typed config:** `config.py`'s scattered `os.environ` reads are wrapped in a frozen `Settings` dataclass (`config.settings`); all 24 legacy module-level names (`DB_PATH`, `MODE`, ...) are re-exported, so the ~50 call sites and the test suite's `config.DB_PATH` monkeypatch are untouched. **TaskRunner** (`realify/runner.py` — named to avoid the existing `realify/tasks.py`): a small work-execution seam, `submit(kind, fn, tenant_id) → job_id` / `get(job_id)`, backed by a new tenant-scoped `jobs` table + `JobRepository`. `InlineTaskRunner` (synchronous, for tests) and `ThreadTaskRunner` (daemon thread) ship today; `run_pipeline_async()` is the real entry point real-time inbound events (§3H) and agent trigger-and-await (§3K) build on — the heavy implementation (external queue + workers) drops in behind the seam without touching callers. **ChannelConnector** (`collectors/base.py`): the collector contract gains a typed `ConnectorConfig` (mode, timeout, circuit-breaker, interval — the breaker already existed, now formalized) plus a reserved, **unregistered** `AdvertisedProductCollector` slot for the period-aware ads ingestion of #004 (certain-vs-estimated dollars kept separate at persistence); wiring it in is Team 7's job and changes nothing until then. **Model-serving boundary** (`models.py`): every prediction is crash-isolated and stamped with a model `version` that flows into card provenance; a failed model degrades to `low` confidence (silent, never wrong), so the deterministic L1 number always stands. **38 tests green** (29 prior + 9 new: runner, connector, model-serving), verified from the shipped zip; the e2e provisioning test still passes *through* the new model-serving boundary, proving behaviour preservation. New table `jobs(id, tenant_id, kind, state, result, error, created_at, updated_at)` is applied additively by `run.py init` (CREATE TABLE IF NOT EXISTS on the existing `/data` DB; data intact). **Honest caveat:** the model `timeout` is a *no-op guard for the in-process models* — `db.connect()` has default thread affinity and the metric snapshot isn't committed before `predict_for` reads it, so moving `predict()` to a worker thread would either break SQLite's thread rule or read stale data; predictions therefore run in-thread (pure-Python, can't hang), and the timeout/circuit-breaker is the documented contract that activates at the **remote** serving boundary (Team 4's build-and-deploy path). 1e did **not** build the payments tables — that is the payments workstream; 1e only documents the `require_quota` seam location beside `require_tenant` in `deps.py`. This build also shipped the #006 reconciliation to **per-seat pricing** (Free trial → Starter $50/seat → Growth $199/3-seats; daily rate limits + seat/SKU caps; four-table data model `plans`/`subscriptions`/`usage_counters`/`billing_events`), the matching §3J guide data model, and the architecture-HTML 1e addendum.

**2026-06-30 — Workstream 1c (SQLAlchemy + Alembic + Postgres) + 1g (data migration) COMPLETE & deployed; production cut over to RDS Postgres.** The database engine swap, in three shippable slices, each behaviour-preserving with SQLite as the default until the deliberate flip.
- **1c slice 1 — engine seam.** `realify/dbengine.py`: a SQLAlchemy engine keyed off `DATABASE_URL` (defaults to `sqlite:///` derived live from `config.DB_PATH`), dialect detection, and the load-bearing **connection wrapper** that gives a psycopg connection the exact `sqlite3`-style API the repositories use (`?`→`%s`, rows supporting `["col"]`/`[0]`/`dict()`). `db.connect()` branches on dialect — SQLite path byte-identical, Postgres routes through the wrapper. So the ~500 `?` placeholders across 18 repositories are **untouched** — the payoff of the 1b sweep. Alembic scaffolded; `DATABASE_URL` added to typed config; SQLAlchemy/alembic/psycopg added to requirements (imported lazily — a SQLite boot never loads them).
- **1c slice 2 — dialect completion.** The 13 `INSERT OR REPLACE/IGNORE` upserts → `ON CONFLICT` rewritten centrally in the wrapper via a `_CONFLICT_KEYS` map (one entry per table's real unique key; a guard test fails if a new upsert table is unmapped) — repositories still untouched. `schema_to_postgres()` translates the one SQLite-ism (`INTEGER PRIMARY KEY AUTOINCREMENT` → `BIGSERIAL`, ×20). `init`→**Alembic cutover**: `db.init_db()` runs `alembic upgrade head` (idempotent baseline adopts the existing SQLite DB cleanly); the two ad-hoc PRAGMA `ALTER`s moved into a dialect-agnostic `0002` migration (SQLAlchemy inspector). `lastrowid`→`RETURNING` via `db.create_returning_id` (one site).
- **1g — data migration.** `realify/migrate_sqlite_to_pg.py` + `run.py migrate-pg [--dry-run]`: copies all 33 tables by **truncate-then-copy** (idempotent re-runs regardless of constraints — chosen after a bug where `metric_history`, which has no unique key, would have duplicated under the original `ON CONFLICT` approach), resets the 20 serial sequences via the catalog (`information_schema` + `pg_get_serial_sequence` — *not* a hardcoded `id`, which was the first crash), and verifies row counts. Never touches SQLite.
- **The cutover (production).** RDS PostgreSQL 18.3 single instance (`db.t4g.micro`, private, SG allows only the EC2 SG on 5432, 7-day backups, encrypted). Dry-run then real `migrate-pg` copied ~320k rows (`seller_orders` 136,310, `settlements` 124,622, `metric_history` 50,580) — every table `src==dst`. Flipped by adding `DATABASE_URL` to `.env` and restarting; verified live on Postgres.
- **Incident + the fixes it forced (this build).** The cutover hit avoidable sharp edges: a passwordless `DATABASE_URL` (an RDS managed-secret `rotate-secret` left the master credential in an ambiguous state) produced a 200-line psycopg traceback and a crash loop instead of a clear message; recovery was a manual high-wire act. Resolved by self-setting the master password via `modify-db-instance`. Hardening shipped so it can't recur: (1) **`dbengine.validate_url()`** — `init_db()` now fails with one clear line ("DATABASE_URL points at Postgres but has no password …") instead of a traceback; (2) **`run.py doctor`** — a preflight that validates URL shape + tests the connection + reports admin-key status, so a flip is checked *before* the live container restarts; (3) **admin-key hardening** — `deps.effective_admin_key()` treats unset *and* known-weak/exposed values (incl. the leaked prototype `dingbats2027`) as unconfigured → admin endpoints fail closed, with a loud boot warning; the operator must set a fresh strong key.
- **57 tests green** (51 + 6 hardening), verified from the shipped zip. **Honest caveats:** the Postgres path was validated by unit + fake-DBAPI tests in the sandbox (no PG there) — first real contact was the cutover dry-run, which passed. The RDS master password is currently **self-managed** (not Secrets Manager) after the rotation tangle — folding it back into Secrets Manager with boot-time injection remains the open Phase-0 secrets item. Remaining Phase-1 work: **1d** (Postgres row-level security, now unlocked) and the rest of **Phase 0** (tested-restore drill + secrets injection).

---

## #006 — Monetization: tiered paywall + Stripe billing

- **Status:** Backlog (spec'd; entitlement seam folds into #005 Phase 1, Stripe wiring is its own phase ~launch)
- **Logged:** 2026-06-29
- **Priority:** High — required before paying customers (30–60 day window)
- **Area:** entitlements (domain), billing adapter (connectors/billing), API, UI paywall, data model

### The model (per-seat — decided 2026-06-29)
Per-seat pricing with **daily rate limits** and **hard resource caps**; limits are data, never hardcoded:
- **Free trial** — 30 days, no credit card. 1 user, 10 insights/queries per day, 10 SKUs.
- **Starter — $50/mo per seat** (Stripe subscription `quantity` = seats).
- **Growth — $199/mo** — 3 users, 50 insights/queries per day, 50 SKUs.

(Supersedes the earlier org-pool / "view distinct insights" model. Prices + limits live in a `plans` table as rules-as-data.)

### Key design decision — three enforcement types, three failure modes (decided 2026-06-29)
- **Rate limits (insights/queries per day):** a per-tenant daily counter (`usage_counters`) checked at the metered endpoints — the research/ask/why calls in the cards router are the "queries", a feed refresh / pipeline run is an "insight". Over-limit → **429, never a degraded or fabricated answer** (invariant 2 holds). The counter is a local atomic upsert, so it works across stateless instances; Redis only if sub-second limits are ever needed (shared with the real-time backplane).
- **Hard caps (seats & SKUs):** data-derived row counts enforced at the *mutating action* — seat cap at invite-create/accept, SKU cap at ingestion. **Fail closed** (deny over cap, clear upgrade signal).
- **Why per-day, not a generation pool:** metering *cards generated* lets the 4h pipeline / re-uploads burn the quota — unstable, feels broken, the system (not the user) decides the bill. A daily query/insight ceiling is user-driven, resets cleanly, and is honest.

### Architecture — entitlements and billing are SEPARATE concerns
1. **Entitlement layer (yours, `domain/`):** `tenant.plan` (free/mid/unlimited) → limits (`max_insights`); an enforcement check the API/services consult before surfacing/unlocking a card. **Source of truth for "what may this tenant see right now"; must work even if Stripe is unreachable.** Config-driven limits/prices. Channel-agnostic.
2. **Billing layer (Stripe adapter, behind an interface — like ChannelConnector/auth provider):** Stripe **Checkout** (subscription signup) + **customer portal** (plan change/cancel) + **webhooks as the source of truth** for payment state (`subscription.created/updated/deleted`, `invoice.payment_failed`). Webhook updates the tenant entitlement. Never trust the client to report plan state. The rest of the app never imports Stripe.

### Sharp edges (bake in from the start)
- **Webhooks are the truth, not the post-Checkout redirect** (redirect may race the webhook). Provision entitlement on the **webhook**; redirect = "setting up." Verify webhook signatures.
- **Idempotency:** Stripe retries webhooks → dedupe on Stripe event id; every handler idempotent (repository concern).
- **Per-seat billing (decided 2026-06-29):** the subscription attaches to the tenant/org (one `stripe_customer_id`, one subscription) but is **per-seat** — Stripe subscription `quantity` = number of seats at the plan's per-seat price ($50 Starter); Growth ($199) bundles 3 seats. Add/remove a user → update the subscription quantity (Stripe proration). The plan gates daily rate limits + the seat/SKU caps, not a shared insight pool.
- **Grace + downgrade:** payment fail → dunning, not instant cutoff. Downgrade unlimited→50 while 200 visible → define which 50 stay (e.g. top-ranked by materiality; rest lock). Decide now.
- **Secrets:** Stripe keys (test/live) → Secrets Manager, never `.env`-on-box or logs.
- **IN entity / processor flag:** confirm Stripe availability + supported methods for an India-registered business early — may affect Stripe-vs-Razorpay choice for IN. **Verify before committing.** (No live account to check at spec time.)

### Data model (updated 2026-06-29 — per-seat + daily limits + caps)
- **`plans`** (rules-as-data): `plan_code` (free/starter/growth), `display_name`, `price_cents_per_seat`, `included_seats`, `max_users`, `max_skus`, `queries_per_day`, `insights_per_day`, `trial_days`. Three tiers = three rows; price/limit changes are row edits, no deploy.
- **`subscriptions`** (local mirror of Stripe state): `tenant_id`, `plan_code`, `status` (trialing/active/past_due/canceled), `seats`, `trial_end`, `current_period_end`, `stripe_customer_id`, `stripe_subscription_id`. Source of truth for "what may this tenant do right now"; **enforced even if Stripe is unreachable**.
- **`usage_counters`** (daily rate-limit grain): `tenant_id`, `metric` (query|insight), `day`, `count`. Atomic upsert on increment; multi-instance-safe.
- **`billing_events`** (idempotency): Stripe `event_id` (unique), type, payload, processed_at.
- Seat cap = `COUNT(users WHERE tenant_id)` vs `plans.max_users`; SKU cap = catalog count vs `plans.max_skus`. All tenant-scoped → covered by RLS (#005 1d).

### Phasing / timing
- **Entitlement layer + paywall UI hook → #005 Phase 1** (cheap; it's a tenant attribute + enforcement check + a lock/blur on cards; touches the tenant/plan model already being migrated). Build the seam even before Stripe is wired.
- **Stripe integration → own focused phase right after Phase 1 / around launch** (need payments before paying customers, but must not destabilize the Postgres migration). Checkout + portal + webhooks + idempotency + dunning.
- Write-back/Temporal not required; webhook handling can be a simple endpoint initially (move to TaskRunner/Temporal activity only if retry/volume needs it).

### Decisions (resolved 2026-06-29) + remaining opens
- **RESOLVED — model:** per-seat ($50/seat Starter; $199 Growth = 3 seats) with daily query/insight rate limits (free 10/day, growth 50/day) + hard caps (free 1 user/10 SKUs, growth 3 users/50 SKUs). 30-day no-card trial. Supersedes the org-pool / view-distinct-insights model.
- **RESOLVED — enforcement:** rate limits → 429 at metered endpoints; seats/SKUs → fail-closed at the mutating action; billing state mirrored locally and enforced even if Stripe is down.
- OPEN — exact definition of a metered "insight" vs "query" (what increments the counter).
- OPEN — **processor: Stripe vs Razorpay for an IN entity** — verify Stripe India support before committing.
- OPEN — proration/downgrade UX when seats are removed mid-cycle; annual plans.

---

## #007 — Integration guide for partner teams

- **Status:** Written 2026-06-29; folded into the app this build (served HTML + repo source). Updated as partner contracts firm up.
- **Area:** platform handoff, contracts, documentation
- **Forcing function:** four teams now building alongside the core platform and needing stable seams to integrate against.

A single guide (`docs/INTEGRATION-GUIDE.md`, also served at `/ops/integration`) that contracts out every integration seam, grounded in the real code rather than aspiration. Covers four teams:

1. **Conversational interface** — consumes decisions via the read API / service layer (`api.py` + `/api/*`) and `research.ask_card`; the hard rule is *read numbers from L1/cards, never fabricate*.
2. **Competitive data** — a new source: subclass `Collector`, persist via a repository, register in `scheduler.collectors()`, make the signal meaningful via rules-as-data. Compliance: official/licensed sources only, never scrape Amazon.
3. **Front-end / design** — consumes the card JSON + presentation hints (`surface` / `group` / `severity` / `action_kind`) and the action sub-API; no business logic in the client, never re-rank or recompute.
4. **ML / model** — implements the Model-plane contract in `realify/models.py`: `predict(con, tenant_id, asin, detector) -> {value, confidence, top_features, kind, label, unit}`, declares `covers`, registers in `models.REGISTRY`. Confidence-gated (`!= low` to attach), informs only — adds a labelled forecast mini and can nudge rank, but NEVER touches `finding` / `severity` / `exposure`.

**The through-line for all four:** the boundary is JSON and tenant-scoped calls, never shared business logic. The platform owns decisions and the numbers behind them; teams plug into a seam, they do not reach across it.

**Commitments the briefs force (land in 1a/1f):** freeze the card JSON schema (a contract test fails the build if it drifts without a version bump) and introduce an `/api/v1` prefix so the conversational + front-end teams build against a frozen contract.

**Tension surfaced by the ML brief:** today `models.py` is in-process / pure-Python / no-network / no-training (a prototype assumption). "Build and deploy models" relaxes that; the `predict()` interface is the stable seam, but four things get formalized in **1e** — a serving boundary (timeout + circuit-breaker degrading to `low`), a model `version` threaded into card provenance, an offline/fixture inference path for hermetic tests, and explicit (eventually rules-as-data) rank influence rather than per-`kind` hardcoding. So 1e now carries two partner contracts (the Collector seam and the model-serving seam), not one.

**This build also:** reformatted `/ops/formulas` into proper HTML tables (was an escaped-markdown dump), added a dependency-free Markdown→HTML renderer (`realify/opsdoc.py`) shared by both doc pages, linked the integration guide from the admin console, and hardened the deploy process (Dockerfile committed to the repo + shipped in the zip; rsync excludes server-only files; dropped the bogus `/api/health` liveness check).

---

## #007 — Your Category Analyst (Research tab rename) + synthesis-screen scaffold

**Status:** In progress · **Logged:** 2026-07-03

Renamed the **Research** tab → **Your Category Analyst** and inverted it: not a research tab of data widgets, but an analyst that did the work overnight and shows up with a dated memo + a ranked shortlist of moves. Synthesis leads; the data threads (Signal feed, Whitespace, Competitive, Voice of Customer, Market Pulse) are the drill-down; the decision→outcome loop (Moves) and Ask-your-analyst sit underneath. A persistent scope bar (category + price-band + the brand's own share/rank/velocity) keeps it operationally grounded. Deliberately excluded standalone Keywords / Trends / raw Reviews tabs — the inversion *is* the product.

**Built for real:** route + page + tenancy. New router `realify/routers/analyst.py` → `GET /category-analyst`, dual-mounted at `/api` and `/api/v1` (like insights/cards/cmaa). Tenancy resolved server-side via `require_tenant()` — fail closed (401), never trusted from the client. The `#analystView` surface in `frontend.html` (no new front-end stack) renders the payload verbatim and computes nothing.

**Typed contract (the concrete target for the backend):** `realify/domain/analyst.py` defines dataclass contracts for every card kind (ScopeBar/BrandPosition, Brief, SignalItem, WhitespaceItem, CompetitiveItem, VoiceItem, MarketPulseItem, MovesLoop, AskAnalyst → `AnalystBrief`), each number carrying a first-class `Provenance` tier: **`official`** (your own data / official APIs) vs **`scraped`** (competitor/marketplace scrape — directional, rendered visually distinct so it's never forwarded as fact). `to_public()` serializes; `PUBLIC_KEYS` + provenance validity + `/api`==`/api/v1` parity + tenancy-fail-closed are asserted by `tests/test_analyst_contract.py`. L1 owns the numbers — the client renders pre-formatted strings.

**Synthesis SEAM (the one function the future service implements):** `synthesize_category_analyst(tenant_id, category, price_band) -> AnalystBrief` in `realify/domain/analyst.py`. Today it returns a typed fixture (`realify/domain/analyst_fixture.py`). **TODO(analyst-service):** replace the fixture body with real synthesis on top of the **1a/1f** card pipeline + the net-new analyst/synthesis service (materiality ranking, whitespace scoring, VoC comparison, move generation), scoping every read to `tenant_id` via the repository/deps path. The synthesis engine is intentionally NOT built here.

**`/api/v1` note:** the endpoint is already dual-mounted and the client consumes `/api/category-analyst`; what's gated on 1a/1f is the *content* behind the seam, not the mount. Ask-your-analyst is stubbed (acknowledges the seam) — **TODO** route it to the conversational synthesis endpoint. All new `.py` under the 400-line cap; the frozen `/api/feed` card contract is untouched (separate card kinds, separate endpoint).

---

## #008 — Profit & Ads → ad-spend control room

**Status:** Built + deployed · **Logged:** 2026-07-04

Reframed the live Profit & Ads page from an *advertised-SKU ledger* (every SKU in one table, sorted by ₹ above break-even) into an **ad-spend control room** for a Commerce/Merchandising VP. The verdict math is untouched and stays L1-correct (break-even ACoS = margin %, ₹ above break-even = certain waste, the window-consistent CMAA fix from #004/`5835e58`); what changed is the *frame* — STATUS buckets are now the primary filter, and the hero + worklist + action reframe per bucket.

**Frontend-led (`renderCmaa` → a stateful control room in `frontend.html`):**
- **Buckets are the primary filter** — the 4 quadrant cards became a clickable segmented control (default **FIX ADS**, sorted by recoverable desc), each carrying its own per-bucket metric.
- **Per-bucket reframe** (hero + value column + action verb + bulk bar all switch):
  - **FIX ADS** → *recoverable ₹* (₹ above break-even), action "pull ACoS to break-even".
  - **SCALE** → *directional upside* (the new L1 number, badged **directional**), action "raise budget". No recoverable — it's efficient.
  - **CUT/DIVEST** → *ad bleed you'd stop* (= ad spend), action "stop ads". **No** ACoS-to-break-even action — impossible at negative margin.
  - **FIX MARGIN** → **honest empty**: shows the count, states "₹0 is recoverable by cutting ads here — the fix is unit economics". Never a fake ad-recovery number.
- **Margin % column dropped** (it was identical to break-even ACoS); margin still shows in the expand math. Recoverable is promoted to a first-class worklist column.
- **Cohort chips** (below-cost, cannibalization-risk) intersect with the active bucket. **Scope bar** (category / price band + a read-only timeframe caption = the actual ad window) consistent with the Category Analyst page. All filtering/subtotalling is display-only over L1-provided per-row values — the client computes no business metric, and an unfiltered bucket subtotal equals the L1 portfolio roll-up by construction.
- **Elevated action panel** (row expand): keeps the L1 diagnosis + recoverable + "do this" + the transparent number→threshold math **verbatim**, and adds actions.

**Actions v1 — no Amazon Ads write-back (we have no ad-write scope):**
- **Export change set** — a client-side CSV the seller applies in Amazon Ads themselves (per-SKU or bulk "apply to all N in bucket", with the projected total shown before confirm).
- **Record a Move** — `POST /api/cmaa/action` logs to our own `actions_log` (recommended → acted); the tab reads acted SKUs back (`ActionRepository.acted_cmaa_skus`) so the state sticks on reload. **TODO(team-7):** real Amazon Ads bid/budget write-back + persisting a generated rule via `/api/settings/rules` — both gated on ad-write scope.

**L1 (the one genuinely new number + supporting flags):**
- `domain/cmaa.scale_upside(ad_spend, ad_sales, gcm%, actual_acos)` — the **mirror of `wasted_spend`**: headroom below break-even `H = ad_sales×be − ad_spend`, deployed at current efficiency → `U = H×(be/actual_acos − 1)`. **Directional** (assumes marginal efficiency holds as spend scales — real auctions don't guarantee it), so it's badged everywhere and returns `None` when there's no headroom or margin/ACoS are undecidable. Wired into `evaluate()` (SCALE-gated) and into `recommend()` as a directional raise-budget action. Roll-up `summary.total_scale_upside`.
- `summary.total_cut_bleed` (Σ ad spend on CUT/DIVEST — what stopping ads saves) and per-card `cmaa_denom_est` (True when CMAA % rests on the monthly-fallback denominator, so the UI can mark it `~`). Per-card `category`, `scale_upside`, `acted` added.
- `domain/cmaa_sample.py` rewritten to **compute** every derived figure (ACoS, ₹ above break-even, CMAA, upside, quadrant) via the same domain functions the live tab uses — the empty-state preview is now internally consistent (no "ACoS below break-even yet flagged overspending" contradictions) and can't drift from the real math.

**Tests:** `scale_upside` math + SCALE-gating + rollups + `total_cut_bleed` + the record-a-Move loop (`test_cmaa_tab_step3.py`); the `recommend()` contract test updated for the new SCALE action (`test_cmaa_recommend.py`). Full SQLite suite green (the one red — `test_headline` — is a pre-existing env artifact: it asserts *no* ANTHROPIC_API_KEY but one is set locally; fails identically on clean HEAD). All touched `.py` under the 400-line cap. Postgres smoke (`run.py doctor --postgres`) not runnable here (no local Docker) — the one new query is dialect-neutral (same `?`-placeholder pattern as the PG-verified `recent()`), and the live box runs Postgres so the deployed `/api/cmaa` is the real PG check. Render verified with headless Chrome across all 4 bucket states + the expanded action panel.

---

## #009 — Profit & Ads: tie every number into the existing explainability mechanism + bound scale_upside

**Status:** Built + deployed · **Logged:** 2026-07-04

Wired every calculated number on Profit & Ads into the SAME explainability mechanism cards use — no parallel contract — and replaced the unbounded `scale_upside` with a bounded, defensible method.

**Reused the existing mechanism (not a new one):** the account toggle `explain_mode` (`GET/POST /api/settings/app`), the body `explain-on` gate, the `.explain-ic` icon and `.explain-panel`, and the `ep-*` panel styling — all unchanged from the card path. When the toggle is ON, an ⓘ appears on the hero, each right-rail lever, and every per-SKU figure in the row-expand; OFF, they're hidden. Clicking opens the same panel showing formula + plugged inputs + result + timeframe + provenance.

**Shared producer (`realify/domain/explain.py`, new):** `part()` / `aggregate()` / `window_basis()` emit the one canonical shape `{label, formula, inputs:[{label,value,unit}], result, provenance, timeframe_basis}` (aggregates add `n` + `top`). `explain.cmaa_parts(card, sym, ctx)` builds every per-SKU derivation (break-even ACoS, actual ACoS, recoverable, ad-spend/bleed, CMAA ₹, CMAA %, scale upside). BOTH the `/api/cmaa` builder and the empty-state sample call this one producer, so their derivations are identical in shape and computed by the same functions. Summary carries aggregate parts (portfolio recoverable / scale upside / cut bleed / TACoS); filtered hero/bucket subtotals are assembled client-side from the same per-SKU L1 parts (a display subtotal — equals the L1 roll-up when unfiltered).

**Single-sourced (kills the ₹23,293-vs-₹23,871 mismatch by construction):** the row-expand's primary value, the worklist column, and the explain panel's `result` all read the identical L1 field (`k[bk.key]`). The old hand-written "why the numbers" evidence block is GONE — the derivation now lives behind the toggle-gated ⓘ. Golden test asserts `explain.recoverable.result == card.above_breakeven`.

**Bounded `scale_upside` (the fix):** the prior `headroom × (break-even/actual_acos − 1)` was UNBOUNDED — the factor blows up as ACoS → 0, producing ₹50.75L on one SKU and a ₹90.14L portfolio. Replaced with `incremental_ad_sales × (break-even − actual_acos)` where `incremental_ad_sales = ad_sales × (SCALE_MAX_MULTIPLE − 1)` (2× ⇒ "at most double today's ad-driven sales"). Bounded by construction: `upside < incremental_ad_sales` (per-SKU upside ≤ its ad-sales headroom) — asserted by `test_scale_upside_bounded_invariant`. Still directional (badged) — real ACoS rises as you scale. Portfolio upside is now order-of-magnitude of ad spend, not lakhs.

**Framing + worklist (fell out of single-sourcing):** expand headline adopts the bucket frame (FIX ADS "Recoverable now" / SCALE "Upside (dir.)" / CUT "Bleed you stop" / FIX MARGIN honest-empty — never "Recoverable" on a CUT SKU). Right-rail all-bucket total relabeled "**ad spend above break-even, portfolio-wide**" (not "recoverable" — that's the FIX-ADS lever only); three distinct levers kept (recover / upside / stop). CMAA carries one labeled timeframe basis (`window_basis`) surfaced in every CMAA explanation; the open CMAA%-denominator edge is flagged in the part's note (not shown as certain). In a bucket view the worklist drops STATUS (constant once filtered), moves AD SPEND into the expand, leads with the bucket money column, and adds a compact ACoS-vs-break-even micro-bar. Hero adds "start with the top N — they hold X% of the recoverable."

**Tests:** every Ads number emits the explain shape + aggregates carry `top`; golden single-source (`explain result == column value`); upside bounded-invariant; bounded-math + rollups updated. Full SQLite suite green (the one red `test_headline` is the pre-existing env artifact). `node --check` on frontend + login JS; `login.html` untouched (control room is app-only; shared conflict-zip block byte-identical). All touched `.py` under the 400-line cap. Live `/api/cmaa` on the deployed Postgres box is the real PG check (no local Docker).

---

## #010 — Profit & Ads: SCALE profitability gate + CMAA reliability & window fixes

**Status:** Built + deployed · **Logged:** 2026-07-04

Live audit surfaced AFWCLEANER0008: CMAA −₹57,839 (−2276.5%) yet classified **SCALE** ("efficient — room to scale") — advice that loses money, off a CMAA built from ₹1,131 × **1 settled unit** − **₹58,971** ad spend, with the contribution term on a 2-period settled window and the spend cumulative over the 3-period ad window. Three fixes, all L1-owned and explainable via the existing explain mechanism.

**Fix 1 — SCALE profitability gate (`domain/cmaa.scale_gate`):** `quadrant()` still decides ads-efficiency + margin-floor, but a *confident* SCALE now also requires trustworthy CMAA AND CMAA ≥ 0. Applied in the router after CMAA is known:
- efficient + reliable + CMAA ≥ 0 → SCALE (unchanged).
- efficient + reliable + **CMAA < 0 → FIX MARGIN** with a distinct recommendation: "Efficient on ads, but losing money after ads (CMAA < 0) — fix the economics, don't scale" (no upside surfaced; does **not** cite `price_for_floor`, since the margin already clears its floor — the gap is after-ads).
- efficient + **unreliable CMAA → HELD** (stays SCALE-classified but flagged "held — verify units", no upside, no budget-raise advice).

**Fix 3 — CMAA reliability (`domain/cmaa.cmaa_reliable`):** CMAA = contribution/unit × settled units − ad spend, so a tiny settled base under material ad spend is nonsensical. **Default rule (tunable, called out for sign-off):** unreliable when ad spend ≥ **₹1,000** (material) AND (settled units < **2** OR ad-attributed sales > **1.5×** settled window revenue). When unreliable the CMAA **% is HELD** (rendered "unreliable — settled units lag ad spend", never −2276.5%) and the SKU is treated per Fix 1. **CMAA%-denominator decision (default):** kept **net settled revenue** (the P&L basis); alternative (total sales ≥ ad_sales) left as a tunable — flagged for sign-off.

**Fix 2 — CMAA window consistency:** the window-path CMAA now subtracts ad spend over the SAME settled-unit periods as the contribution (internally consistent), instead of full-window cumulative spend against a part-window contribution. When those settled periods are a strict subset of the ad-report window that recoverable/upside use, the row carries `cmaa_window_mismatch` → a △ marker + the CMAA cell tooltip + the derivation state CMAA's actual (shorter) window, so the two aren't read on the same basis.

**Explainability:** new per-SKU flags (`cmaa_reliable`, `cmaa_held`, `cmaa_window_mismatch`, `scale_gate_reason`) flow through `explain.cmaa_parts` — the CMAA part's note explains unreliability/mismatch, and a new **`classification`** part ("Why this isn't a clean SCALE") shows the efficient ACoS AND the negative/untrustworthy CMAA that gated it. Everything single-sourced; the held/flagged state is itself click-to-explain.

**Frontend nits:** (A) dropped the double "L1 · " prefix from the aggregate-lever provenance fallback (the panel already renders an L1 badge). (B) tightened the card-row first column (`minmax(200px,440px)` + `justify-content:start`) so ACoS-vs-break-even / CMAA / money anchor sit closer to the title.

**Tests:** golden AFWCLEANER0008 (efficient + unreliable + CMAA<0 → held, %-held, window-mismatch, explainable); SCALE-gate (efficient + reliable + CMAA<0 → FIX MARGIN); reliability + gate domain unit tests. Full SQLite suite green (pre-existing `test_headline` env failure aside). `node --check` FE; all `.py` < 400 (`cmaa.py` 394). `login.html` untouched.

---

## #011 — Category Analyst Phase 1: real off fixture + per-section data-state contract

**Status:** Built + deployed · **Logged:** 2026-07-05

Reshaped the fixture-backed Analyst surface into real L1 synthesis for the reshape-only sections, and formalized a per-section **data-state contract** so real-vs-synthetic is explicit in the payload AND unmistakable in the UI. No new ingestion, no scraping. Three-plane rule throughout: L1 owns every number/ranking/classification; prose is deterministic-from-L1 (the `_phrase` seam an L2 later replaces, introducing no number); the client renders and never computes.

**Data-state contract (frozen, added to `PUBLIC_KEYS`):** a top-level `states` map, one `SectionState{state, provenance, coming}` per section — `state ∈ live|partial|fixture`. Partial sub-fields carry `Metric.field_state="coming"` (a "—" placeholder, never a fabricated/zero number). `Metric` also gained `explain` (the shared explain-part shape) so every live analyst number plugs into the same `explain_mode` ⓘ as Profit & Ads. Dual-mounted /api + /api/v1.

**Live off real L1 (`realify/domain/analyst_live.py`, new):** Signal Feed, Market Pulse, Competitive Landscape and the Brief are assembled from the tenant's C1–C9 feed cards (materiality = `rank_score`); Competitive moves are L1-classified (price_cut / new_entrant / assortment_shift / ratings_surge) from the detector + finding. Scope (category + point-in-time velocity live; share/rank/price_band/velocity_trend coming) and Moves (recommended/acted counts live; attributed_margin/hit_rate coming) are **partial**. The Brief is assembly-not-a-brain: L1 ranks the top moves by rank_score/exposure, and the memo references only those L1 numbers (test: `brief.moves` impacts must all be values L1 produced).

**Exposure gate (server + client):** Whitespace + Voice of Customer stay **fixture** — synthetic content is emitted ONLY to the fixture tenant (`account_type='tester'` or `data_mode='synthetic'`); a real tenant gets an empty list + coming-state copy, never a fabricated number (test: real tenant ⇒ fixture sections carry no items). Ask is partial (input shell live; conversational answers coming).

**UI border vocabulary (`renderAnalyst`):** the state is carried by the section's outer border, pattern-first so it survives colourblindness/dark backgrounds — **live** = solid hairline (no badge), **fixture** = 1.5px dashed amber + a "COMING" pill + coming-state body, **partial** = left-accent (3px) with per-field `— [coming]` chips. A legend strip (shown to all tenants) teaches the three states. Provenance chips are independent + per-row: official (neutral) / scraped·directional / est.·directional (amber). New tokens `--warn-border/-bg/-text`, `--accent-border` in `:root`. `login.html` untouched (analyst is app-only).

**Tests:** contract (frozen keys incl. `states`, provenance tiers, dual-mount parity), per-section state, exposure gate (real tenant sees no fixture numbers), brief-assembly (no number absent from L1), scope params. Full SQLite suite green (pre-existing `test_headline` env failure aside); `node --check` FE + login; all `.py` < 400 (analyst.py 231, analyst_live.py 240). PG parity via the deployed endpoint (assembly reads only dialect-portable repos, no raw SQL).

---

## #012 — Category Analyst Phase 1: content + rendering fix pass

**Status:** Built + deployed · **Logged:** 2026-07-05

Fixed the P0/P1/P2 bugs from the live audit — all in the two intended layers (L2 assembly `analyst_live.py`, client `renderAnalyst`). The data-state architecture (states map, exposure gate, fixture/partial borders, legend, coming-chips) was verified correct and left untouched.

**P0-1 — raw HTML rendered as literal text.** L1 emits a closed markup set into prose (`<b>…</b>`, `<span class='rupee'>…</span>` — same hooks Profit & Ads uses), but `renderAnalyst` escaped it. Added `_anHtml()` — escapes everything, then whitelist-unescapes exactly those tags (no blanket innerHTML of server strings). Applied to Brief/Signal/Competitive/Market-pulse prose; bold + rupee now style correctly.

**P0-2 — false "under the 30% floor" claim (reported before changing).** Root: `analyst_live` had no floor logic — it relayed the card `finding` verbatim, and the "under the floor" sentence originates in the **shared L1 card pipeline** (`interpret.py`/`generate.py` margin-vs-floor phrasing), not the analyst. Fix (as instructed, in `analyst_live`): the analyst now OWNS the `below_floor` verdict from L1 seller data (`net_margin_pct < margin_floor`), **drops** any floor-breach card the data contradicts, and **re-phrases** genuine breaches from L1 (real margin + real floor value, not a hardcoded 30% or the card's stale number). Flagged the upstream card-pipeline phrasing separately (can still surface on Feed/Profit & Ads).

**P1** — `_cat_phrase()` guards category interpolation ("all categories", never `None`); competitive classification kept as machine `kind` + human `kind_label` (no `[price_cut]` token in prose); business numbers (₹-at-stake, net margin %, Buy Box %) emitted as **structured Metrics with explain parts** and rendered with the same `explain_mode` ⓘ as Profit & Ads — the raw `materiality` sort score is no longer a user-facing metric (feed items now show a discreet `#n` ordinal); duplicated revenue label removed.

**P2** — Signals are one line (what changed · the play · structured metrics), no embedded duplicate move card; each Competitive row carries **per-row provenance** (official vs scraped·directional) and section provenance now names real sources (not the leaked `net_margin_pct` column); Brief memo count == rendered feed count; headlines are title/SKU-led (not raw ASINs) and the Brief dedupes to one move per product (highest exposure).

**Tests:** floor-gate (above-floor SKU never surfaced; genuine breach phrased from L1), category-all phrasing, no enum token / no duplicated label, business-metrics-carry-explain (materiality not a ⓘ metric), per-row competitive provenance, memo-count==feed + brief dedupe. Full suite green (pre-existing `test_headline` env failure aside); `node --check` FE; `.py` < 400 (analyst_live 343). `login.html` untouched; dual-mount parity held.

---

## #013 — Category Analyst: explain-panel render, competitive count, upstream floor phrasing, Signal Feed re-source

**Status:** Built + deployed · **Logged:** 2026-07-05

Four scoped fixes; the verified states map / exposure gate / borders / legend / coming-chips untouched.

**Fix 1 (P0, render) — explain panel corrupted a correct payload.** The analyst opened its ⓘ via `_epPartHtml(part, null)`, so the pre-formatted L1 result string ("₹5.6L") fell through to `_epFmt` → `Number("₹5.6L")` → **₹NaN**. Fixed: pass `part.result` so the panel renders `explain.result` **verbatim** (client renders, never recomputes). The "÷→+" operator report couldn't be reproduced — `_esc` and the whole panel path preserve `÷/×/−/Σ` (proven by a node render test and a real-browser DOM check: the ₹-at-stake panel now shows "annual revenue ÷ 12" and "₹5.6L"). Added a render test asserting an opened panel contains "÷ 12" and the result string with no "NaN".

**Fix 2 — Competitive returned only 1 row.** Not legitimate — a bug: `_is_floor_card` matched the substring `"floor"` in a finding, and C1's wording is *"…undercuts your price above your floor"*, so genuine competitive cards were dropped by the P0-2 floor-gate. Reported pre/post: 3 raw competitive cards → 1 surfaced (pre) → 3 surfaced (post). Fixed by scoping `_is_floor_card` to own-SKU families with a *below/under/beneath*-floor finding, never the external C1–C9 detectors.

**Fix 3 (upstream durable) — margin-vs-floor phrasing at the L1 source.** Root: `net_margin_pct` mapped to the `margin-vs-floor` detector for BOTH `op="lt"` (breach) and `op="gt"` (high-margin OPPORTUNITY), and every pool phrasing hard-codes "under the floor" — so a 48.7% margin on a `gt 30` opportunity rule read "under the 30% floor". Fixed in `interpret.detector_for`: `net_margin_pct` + `op="gt"` routes to a new `margin-headroom` detector (no below-floor pool) → `generate.py` phrases it with the correct relation ("above your … line"). `op="lt"` still uses `margin-vs-floor`. This is the SHARED pipeline (Feed/Profit & Ads/Analyst), so a margin ≥ floor SKU is no longer phrased below-floor on any surface; genuine breaches still fire. The `analyst_live` guard stays as defense-in-depth.

**Fix 4 (Decision A) — Signal Feed re-sourced.** The Signal Feed now carries CATEGORY / COMPETITIVE change only (the C1–C9 detectors: competitor moves, category demand, opportunity/whitespace, recalls/news). Own-SKU P&A/Intelligence findings (margin-below-floor, Buy Box, ad spend — the generic catalog-rule cards) are removed from the feed and instead referenced by the Brief as a context INPUT ("N own-SKU findings on your Profit & Ads worklist — factored in, not repeated here"). No feed item duplicates a P&A/Intelligence card; the feed is intentionally thinner (external signals like VoC/share are Phase 2). Kept intact: one-line signals, title/SKU headlines, #n ordinals, structured money Metrics with ⓘ.

**Tests:** explain-render (÷ survives, result verbatim, no NaN); competitive per-row provenance + count; `interpret.detector_for` gt→margin-headroom / lt→margin-vs-floor + `generate` gt phrased "above" not below-floor (new `test_margin_floor_phrasing.py`); Fix-4 feed excludes own-SKU findings (Brief cites them as inputs). Full suite green (pre-existing `test_headline` env failure aside); `node --check` FE + login; `.py` < 400. `login.html` untouched; dual-mount parity held.

---

## #014 — Profit & Ads: SIMULATE (deterministic scenario projection)

**Status:** Built + deployed · **Logged:** 2026-07-05

A "Simulate" button in each expanded Profit & Ads row opens a modal that projects the row's recommendation — a 30/60/90 forecast of the affected numbers, what could go wrong, and a 7/15/30/60 monitoring plan — every figure traceable to (a current L1 value × a stated, editable assumption), on the existing explain_mode / renderExplain spine. It is a **deterministic scenario projection, never a prediction**, badged `L1 · projection · directional` everywhere.

**Contract (`realify/domain/simulate.py`).** `simulate(row, assumptions)` → five explainable parts: intervention model · 30/60/90 projection (with a DO-NOTHING baseline + ₹ delta) · what-could-go-wrong · the 7/15/30/60 monitoring plan (the trust hero — each checkpoint has an expected value + an explicit tripwire) · editable assumptions (defaults + sources + conservative/expected/optimistic presets). Every projected number is emitted as a `explain.part` (formula + inputs + the assumption used + result); the `result` is a PRE-FORMATTED string the client renders verbatim (never recomputed — the Fix-1 rule). Assumption-driven headlines show a range, not a lone point.

**One intervention model per bucket** (mechanics differ): **FIX ADS** — pull ACoS→break-even; CMAA gain = recoverable − (1−organic_hold) × (recoverable ÷ ACoS) × margin; ≤ the recoverable ceiling. **SCALE** — raise budget with diminishing returns; gain = incremental ad-sales (capped at max_multiple) × (break-even − ACoS) × (1 − acos_drift); ≤ the bounded scale-upside ceiling. **CUT/DIVEST** — bleed stops immediately (= ad spend); organic-retention R governs units at risk. **FIX MARGIN** — price↑ vs demand elasticity e → margin recovery net of units lost. An effect RAMPS in (linear to steady state; default 60 days, editable). A lever missing a required input degrades to an honest "can't simulate — missing X", never a fabricated value.

**Assumptions** (each defaulted + sourced + editable, with presets): organic_hold (0.7), acos_drift (0.5), organic_retention (0.4), price_increase (0.08), elasticity (1.2), max_multiple (2.0), ramp_days. Editing + Re-simulate re-runs `simulate()` server-side and round-trips into the CSV.

**Endpoint** `POST /cmaa/simulate` (dual-mounted /api + /api/v1, tenant-scoped, fail-closed): rebuilds the row **server-side** via the new single-source `build_row_card` (the same builder the /cmaa feed uses — never trusts a client-supplied row), then projects over the posted assumptions.

**UI** (`renderCmaa` / new modal): a "Simulate" button sits LEFT of "Export change set" in the expanded row. The modal shows the 5 parts; every projection/monitoring/headline cell is click-to-explain (opens the same `_epPartHtml` panel with formula + inputs + verbatim result — always, since the sim's purpose is showing math). "Download CSV" exports the current simulation (assumptions used, per-metric projection + formula, risks, monitoring plan, disclaimer). `login.html` untouched; NO Amazon Ads write-back (projection only; actions stay export/record-Move).

**Refactor:** the per-row card build was extracted into `build_row_card` (single source) so the sim projects off the exact figures the worklist shows; the 14 existing CMAA tests stay green.

**Tests (`test_simulate.py`):** every projection cell carries an explain + renders the server result verbatim (no NaN); editing an assumption moves dependent projections; do-nothing baseline present; ranges present where assumption-driven; missing-input → honest-empty; FIX ADS 90-day ≤ recoverable ceiling; SCALE gain ≤ bounded upside ceiling; CSV-needed fields present; endpoint dual-mount + fail-closed. Full suite green (pre-existing test_headline env failure aside); node --check; all `.py` < 400. An adversarial multi-agent audit (15 agents) surfaced + verified 10 real issues — all fixed with regression tests: a SCALE-monitor blocker (displayed value ≠ its explain result), no server-side validation/clamping of edited assumptions (malformed → 500; out-of-range → ceilings blown), SCALE gain exceeding the bounded ceiling, ranges hard-coding preset tuples instead of deriving from the declared presets, and unnamed magic constants in tripwires/risk. Now: assumptions are coerced+clamped to declared [min,max] server-side; max_multiple capped at the L1 ceiling + gain min-capped to it; every monitor cell's explain.result equals its displayed value; every range derives from _presets(); tripwire/risk factors are named module constants surfaced in the tripwire text.

## #015 — Profit & Ads SIMULATE modal: two live-audit patches

**Status:** Built + deployed · **Logged:** 2026-07-05

Two defects from the live audit of #014 (tester tenant, FIX ADS row VKAMCOVER0074). Scoped to these two only — projection math, explain panels, and the assumptions/re-simulate plumbing were verified good and left untouched.

**Bug 1 (P1 — trust): the headline confidence RANGE didn't re-simulate.** The band was computed from the FIXED preset values (organic_hold 0.5/0.7/0.9), so it was invariant to the *edited* assumption: editing organic_hold 0.7→0.4 moved the point (₹75,369→₹70,525) but left the band frozen, so "expected" no longer matched the point and the point fell outside its own band. Since the range IS the honesty mechanism (and the model-readiness seam for a future confidence interval), a band that decouples from the inputs is worse than none. **Fix:** the band is now re-derived AROUND the current point on every simulate — `expected == the headline point` by construction, bracketed by ±a named half-width (`BAND_H`/`BAND_DRIFT`/`BAND_E`, ≈ the declared preset spread) on each lever's key uncertainty assumption. So the whole band moves on Re-simulate, the point always sits within [conservative, optimistic], and L1 still owns the band (client renders verbatim, never recomputes). Applied to FIX ADS (organic_hold), SCALE (acos_drift), FIX MARGIN (elasticity); CUT stays a flat band (bleed is certain).

**Bug 2 (P2 — cosmetic): the modal header rendered "[object Object]".** The Simulation dict had a key collision — `base["headline"]` held the L2 recommendation *string* (for the header subtitle) but the return spread `{**base, "headline": m["headline"]}` clobbered it with the headline-comparison *object*, so the header's `_esc(s.headline)` stringified the object. **Fix:** the recommendation string now lives under its own key `rec_headline`; the header subtitle and CSV read `s.rec_headline`, while the comparison object keeps `headline` (used as `hl`). No more collision.

**Tests:** `test_confidence_band_brackets_point_and_re_derives` — `expected == headline point` on every lever, point within [conservative, optimistic], and editing the key assumption moves the whole band (not just the point) across two levers. `test_header_field_is_recommendation_string_not_object` — `rec_headline` is the recommendation string, `headline` is the comparison object, no stray "[object Object]". Full suite green (pre-existing test_headline env failure aside); node --check FE + login; login.html byte-identical; all `.py` < 400 (simulate.py 399); pure-Python change, no new SQL (dialect-portable).

## #016 — Degraded-simulation disclaimer (Part A) + Simulate in every Intelligence card (Part B)

**Status:** Built + deployed · **Logged:** 2026-07-05

Extends the deterministic SIMULATE spine (#014/#015) from Profit & Ads to the whole Intelligence surface, and adds an honest "may not be useful here" disclaimer for degraded projections. Same contract throughout: every projected number = a current L1 value × a stated, editable assumption, emitted as an `explain.part` and rendered verbatim; `L1 · projection · directional`; the monitoring plan is the hero. No parallel mechanism — one engine, dispatched by card kind.

**Part A — degraded-simulation disclaimer.** The Simulation contract gains `sim_quality` ("useful"|"degraded") + `degraded_reason` (an L1-owned sentence). When degraded, the modal pins a caution banner at the very top (`var(--warn-*)`, not an error style): *"Disclaimer: Simulation may not be useful here because &lt;reason&gt;."* The projection, do-nothing baseline, and editable assumptions still render; a headline built on a null base dims to "—" (`headline.null_base`). P&A degrade triggers (enumerated, non-exhaustive): SCALE on a null CMAA/units base; a volume-dependent lever with no units (projects ₹0); `cmaa_reliable=false`/`cmaa_held`; ad spend below a materiality floor. L1 owns the classification + reason; the client renders it verbatim.

**Part B — Simulate on every Intelligence card.** A "Simulate" button sits left of each card's primary action (suppressed for news/recall/social — a projection there would be fabricated). It opens the SAME modal, dispatched by **canonical detector id** (`interpret.detector_for`) to one own-data intervention model:

| detector | model | lever / key assumption |
|---|---|---|
| margin-vs-floor · margin-headroom | FIX-ECONOMICS | price ↑ (± COGS/returns) vs elasticity |
| returns-rate | RETURNS-REDUCTION | return rate → your ceiling; refund cost recovered |
| revenue-share | CONCENTRATION STRESS-TEST | shock% → portfolio revenue/contribution at risk |
| conversion | CVR-LIFT | CVR → your line; sessions × ΔCVR × unit contribution |
| velocity · rank-movement | DEMAND-CAPTURE | run-rate contribution + stockout exposure |
| days-of-cover · seasonal-cover · stock-level | REORDER (exemplary) | reorder qty → your cover line; contribution protected; overstock guard |
| tacos | TACOS-ARREST | TACoS → your ceiling; spend saved net of held sales |
| buy-box-ownership | BUY-BOX-REGAIN | win-rate → your line; sales follow BB share |
| price-competitiveness (C1) | PRICE-RESPONSE | respond vs hold; heavily ranged, directional |
| competition-density (C2) | *disclaimer-only* | no own-data lever → banner + watch plan, no projection |
| rating · review-count | REVIEW-RECOVERY | gated on conversion data; wide range; else honest-empty |
| opportunity · assortment-breadth (C5/C6) | GAP-CAPTURE | capture% of a stated gap at est. margin; directional |

Every model: expected == the headline point (band re-derived around it); do-nothing baseline; risks; a 7/15/30/60 monitoring plan with tripwires where every cell's ⓘ result equals the displayed value; degrades to honest-empty on a missing required input, never a fabricated number.

**Threshold-sourced defaults.** Wherever a model needs a TARGET it defaults to the tenant's OWN detector threshold from `/api/settings/detectors` (their margin floor, TACoS ceiling, days-of-cover line, CVR line, returns ceiling, Buy Box line), labelled "your floor/ceiling/line" and flagged when customized. Read via `effective_rules(tid)` with a `catalog.CATALOG` fallback (works before the rules table is seeded).

**Endpoint.** `POST /cmaa/simulate` now also accepts `{card_id}` (in addition to `{sku}`): it resolves the card server-side (`CardRepository`), rebuilds the own-product SKU row (`seller_skus` + latest `traffic`), reads the rule's field/op + tenant threshold, and dispatches to `sim_intel.simulate_card`. Dual-mounted `/api` + `/api/v1`, tenant-scoped, fail-closed. Never trusts a client-supplied value.

**Structure (400-line cap; one module per model group):** `sim_common.py` (shared spine — formatting, ramp, explain-cell/row, band, validate/clamp, degrade classification, finalize); `simulate.py` slimmed to the P&A engine; `sim_inventory.py` / `sim_flow.py` / `sim_market.py` (the intelligence models); `sim_intel.py` (dispatch).

**Step-0 findings (reported before building):** the `project()` model-readiness seam and its mock-`predict()` test do not exist as a function — the seam is the `headline.range` band + the `explain.part` derivation (formula OR model-basis string), which is preserved. The MARGIN-11 "undefined minis" is **not reproducible server-side** (minis are built + stringified correctly in `generate.py`/`materialize.py`) — flagged as a likely frontend/data artifact, not fixed here. `INTEL_GROUPS` marks only Margin/Sales/Cash/Inventory/Ads/Pricing&BuyBox as intelligence-surface; per direction, the button ships on **all** enumerated detectors (research-surface Reviews/Opportunity/Share/Competitive included).

**Tests:** `test_sim_intel.py` — detector dispatch; no-button for C7/C8/C9; every model traceable + no NaN/[object Object] + do-nothing baseline + expected==point + point-in-band; monitor ⓘ == displayed (the #014 blocker class) for every model; extreme-row division-safety; per-model sanity (reorder cover math + overstock, concentration shock, gap ≤ gap×capture×margin, tacos ≤ spend saved); degrade/honest-empty paths; disclaimer-only C2; zero-volume degrade; threshold-sourced defaults + customized label; clamp + malformed-safe; endpoint {card_id} dual-mount + fail-closed + 404. `test_simulate.py` — Part A sim_quality classification + null_base. Full suite green (pre-existing `test_headline` env failure aside); node --check; `login.html` byte-identical; all `.py` < 400; dialect-portable (the one new query is standard `?`+LIMIT SQL).

**Adversarial audit (2 reviewers) found + fixed 8 issues before ship:** a BLOCKER — `buybox_regain` multiplied units by `target/current` Buy-Box share, exploding at the low-BB values this card fires on (bounded now: denominator floored + uplift capped at +100%, and degraded when BB is too low to project reliably); a HIGH — the post-price-cut unit contribution was `price×(1−pc)×(gcm−pc)` (double-counting the cut), corrected to `price×(gcm−pc)` in both `buybox_regain` and `price_response` (the latter wrong by default); a MED — `reorder`'s confidence band was degenerate (clamped flat) and its risk text claimed a velocity sensitivity the band denied (band now varies the reorder-qty lever; risk text made consistent); and LOWs — the modal header showed literal `<b>` markup from the card finding (stripped server-side), a `threshold_customized` false-positive + an ignored cover line on the special detectors BB-OWN/C4 (both fixed by sourcing the target default from effective-rules + targeting C4's `days_of_cover_lt`), a velocity monitor mislabeled "units" for a u/day rate, and an imprecise TACoS explain label. All other models + the endpoint's tenant-scoping/fail-closed/validation were verified clean.

## #017 — Cross-channel onboarding: Shopify + guided wizard (parallel raw ingestion)

**Status:** Built + deployed · **Logged:** 2026-07-07

Extends the Amazon CSV onboarding so a seller can also connect **Shopify**, unified at the **SKU level**, via two entry paths that converge on one pipeline (spec design-locked). Built + deployed in nine phases, each tested; the existing Amazon flow is **behavior-preserving** throughout, and `login.html`/`frontend.html` shared `.cflt-*` blocks stay byte-identical.

**Two paths, one pipeline (§3).** The **raw path** (default) is the existing drag-drop controller, extended: a header-fingerprint recognizer classifies each file and Shopify types are just new rows. The **guided wizard** (optional) runs a thin interview, emits a personalized checklist + a persisted topology, then hands back to the same controller pre-armed. Both write the same `TenantTopology` and run the same recognizer.

**Rules-as-DATA spine.** `realify/topology.py` — a **source-aware manifest**: each row is a data need with `csv` + `inline` slots (live) and an `api` slot (declared-dormant for the future connected-source lane, §14), plus shared `natural_keys` so a CSV upload and a later API pull idempotently converge. `realify/nodegraph.py` — the wizard node graph + the answer→emit map (§6 Table 1), with test-enforced graph↔manifest referential integrity. Adding Walmart/TikTok or an ad partner is new rows, not a branch.

**Recognizer (Phase 1).** Extracted to `realify/ingest/recognizer.py` (100%-signature substring match, greedy-best, ANY-OF tokens for e.g. Shopify inventory's "Available" OR "On hand"); Shopify fingerprints are sourced from the manifest so recognizer + checklist stay in lockstep. `report_ingest.py` slimmed 396→339 by re-export (it was one edit from the 400-line cap).

**Data model + persistence (Phase 2).** `realify/topology_model.py` — **`Resolved<T>`** (stated/detected/effective; **detection wins the number immediately** on conflict, provenance flips STATED→RECONCILED only on user confirm; RAW path = DETECTED) + the **reliability-flag lifecycle** (ARMED→SATISFIED→WAIVED) with the blocks/satisfied-by mapping as data + `TenantTopology`/`ChecklistItem`. Migration `0010` (additive, inspector-guarded): `tenant_topology` (resolved topology as a JSON blob) + `sku_crosswalk` ((channel, store_id, external_sku, external_variant_id) → `canonical_sku_id` = `internal_sku`); both registered in `dbengine._CONFLICT_KEYS` + `db.TENANT_DATA_TABLES`. Live on prod Postgres.

**Crosswalk + normalization (Phases 3-4).** `ingest/crosswalk.py` — auto-map (Shopify Variant SKU == Amazon SKU), unmapped bucket (blank/bundle), reconcile-arm on a stated-IDENTICAL mismatch; **record-level dedup** (upsert on `natural_keys`, file-hash advisory). `ingest/normalize_finance.py` — **MCF shared inventory** (an "Amazon Fulfillment" location is the one FBA pool, NOT summed with Shopify stock; margin stays partial until `AMZ_MCF_FEES`) and **booked (`SHOP_ORDERS`) vs settled (`SHOP_PAYOUTS`) coexistence** (unmatched orders = not-yet-paid-out).

**Node graph + resolution + checklist (Phase 5).** `nodegraph.resolve_answers` walks answered nodes → topology + emitted file_row_ids; `pipeline/checklist.py` derives the goal-ordered checklist (dedup across nodes, NO_LONGER_REQUIRED when the last emitter is removed).

**Wizard + raw-path + reconcile + completeness (Phases 6-9).** `routers/wizard.py` (`/api/wizard/graph` + `/api/wizard/resolve`, tenant-scoped, fail-closed); `ingest/rawpath.py` builds the `/api/ingest/identify` response with detection signals + **reconcile prompts** RC-1..RC-8 (`pipeline/reconcile.py`, §8); `pipeline/completeness.py` yields per-goal AVAILABLE/PARTIAL/UNAVAILABLE. `ingest/shopify_commit.py` (wired into `/api/onboard/reports`) writes recognized Shopify reports into `seller_skus` — Shopify-only SKUs become new rows (COGS/price/units/stock + provenance) while a SKU that maps to an existing Amazon SKU is linked in the crosswalk **without overwriting Amazon economics** (the cross-channel number merge belongs in `channel_economics`, deferred). Wizard UI is server-rendered in `login.html`, reusing the existing components + tokens (no client framework).

**Step-0 decisions (adopted):** R4 `canonical_sku_id` = `internal_sku` (avoids touching the `seller_skus` PK); R9 booked/settled coexist as provenance alternates (actual wins); R2 manifest runs parallel-then-converge (Amazon recognition unchanged).

**Tests:** all 10 §12 feature acceptance tests pass — recognizer, manifest-source-aware, topology-resolution, flags-lifecycle, dedup-record-level, shared-inventory-MCF, node-emit-resolution, checklist-derivation, completeness-preview, reconcile-prompts — plus extractors + shopify-commit + file-length, and the behavior-preserving Amazon onboarding suite. Full suite green (pre-existing `test_headline` env failure aside); every `.py` ≤ 400; dialect-portable (verified on real Postgres); migration `0010` applied on prod. Deployed across commits (Phase 1) `23a8048` → (Phase 6 wiring) `9689675`.

**Deferred (design intent, not built):** the cross-channel number merge per canonical SKU; connected-API auto-pull (§14) — the manifest is already source-aware so wiring it later is a Collector job, not a reshape.

## #018 — V4 reskin (parallel skin) + Feature/Version Registry + Ask & Agents

**Status:** Built + deployed (dark, behind a flag) · **Logged:** 2026-07-23

Reskin of the whole app to the **V4 / "Intelligence v2" design language** (cool/light, all-sans, blue accent, flat cards, status pills, metric tiles), shipped as a **parallel skin** with zero risk to the live app, plus two net-new surfaces (Ask, Agents) and the rollout machinery that governs them.

**Zero-risk delivery model.** The V4 seller SPA is a **new file `frontend_v4.html`** — `frontend.html` (legacy) is never edited, so it cannot regress. `pages.home()` serves v4 only when the skin resolves to v4 AND the file exists. All backend is **additive** (new routers/tables/nullable columns); the frozen `/api/v1` contract is untouched. Deploying the whole thing changed nothing a user sees until a flag is flipped.

**Feature/Version Registry (the standing convention — `realify/flags.py`, `FEATURE-REGISTRY.md`).** Every new feature/UI version ships **dark** behind the registry and is turned on / rolled back entirely from the **Ops page** (`/ops` → Rollout; `GET/POST /api/admin/rollout`, admin-key gated). Two flag kinds: **version** features (coexisting builds with a baseline — `app_ui`: legacy(baseline)/v4; pick build + scope off|internal|on; rollback = pick prior build or scope off) and **gate** features (behavior on/off, default off — `ask`, `agents`). DB-backed (system pseudo-tenant 0 + per-tenant in `tenant_settings`, no FK), read per-request → instant flip, no redeploy. `?skin=v4` / `?skin=legacy` query pins let you dogfood without touching global rollout. **Forward-feature dependency model:** ask/agents declare `requires: app_ui=v4`; `feature_enabled = gate AND dependency-satisfied`, so an "on" gate under a legacy build is inert (never an undefined state), and the Ops toggles grey out with a note until v4 is rolled.

**Surfaces built (all behind app_ui=v4).** Shell (rail Ask·Intel·Ads·Agents + Settings·Integrations, header, right pane, ⌘K omnibox); **Ask** (conversational home — SSE streaming, stub narrator behind a swappable seam, category chips, model picker + monthly-usage cap, feedback/follow-ups/history; backend `realify/ask/*` + migration 0039); **Intel** (feed + KPI band + card→modal with numbers/research-L2/explainability/ask, sub-views Intelligence/Analyst/Channels); **Ads** (coverage/quadrants/worklist + full Fix-Ads modal: per-campaign Apply/Preview/Open/Why/Simulate + Apply-all/Export/guardrails + ƒ inline reveal); **Settings** (account/avatar/change-pw/roles/billing/staff-ops-link, Product Catalog + per-SKU drawer, RIA model panel, tester tools, Team & invites, COGS) + **Integrations** (unified `/?add-data=1` uploader); **Agents** (workforce framework + flagship Pricing spec + hash-chained Autonomy Ledger + pricing scope tables + tester-seeded sample decisions; `realify/agents/*` + migration 0041). Migrations added: 0039 (ask), 0040 (users.avatar), 0041 (agents). Head now **0041**.

**Parity-restore pass (R30–R32).** The first surface build shipped DLS *shells* that under-delivered feature depth; restored full legacy parity via the existing endpoints — Intel modal numbers (minis are `[k,v,color]` arrays — the bug) / research / explainability / ask; the complete Fix-Ads modal; the per-SKU catalog drawer; functional Rules pane + Action list. **Lesson recorded:** match legacy feature-for-feature, not just the happy-path shell.

**Marketing reskin (R22).** The static site (`site/tokens.py`/`ui.py` + all `site/ui_*`) reskinned in-place to V4 (light, all-sans, cool) — deployed live (not dark; reversible token swap). Google OAuth brand colors + family tints deliberately preserved.

**Adjacent fixes.** R24 — the pipeline crashed on SKUs with NULL `annual_rev_inr` (`detect.py` divided raw); null-safed. R35 — synth ad campaigns now named after the product title (were raw SKU codes reading as "auto parts"); and the agency fleet "$-at-stake" showed ₹0 for real ₹-native brands because the feeder defaulted currency to USD (no agency CSV rows) and `decisions.generate` crashed on a missing FX rate — both fixed (currency falls back to the brand's marketplace; generate is FX-tolerant). R34 — agency console Log out + team back-to-fleet.

**Rollout instructions live on the Ops page** (see the Rollout card): dogfood via `?skin=v4`; roll out via Ops Rollout (build=v4 + scope on); roll back via scope off or `?skin=legacy`.

**Still held / external:** the RIA models (cofounder — `docs/RIA-MODEL-INTEGRATION.md`), the Ask self-hosted model (narrator seam), the Agents engine math + Arbiter execution + real Amazon write-back.
