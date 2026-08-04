# V4 Reskin — living spec (planning only, NO build yet)

Reskin realifyai.app to the **V4 / "Intelligence v2"** design language (flat white surfaces,
all-sans type, colored status pills, metric tiles, tinted section boxes, near-black primary CTA).
Reference mockup: https://claude.ai/code/artifact/bf6f26ab-af85-4648-b2ac-315a943e1f48

## Locked global decisions
1. **Parallel skin, fully A/B-able.** Both the current skin and V4 ship; a flag switches between them
   (destructive-free, instant rollback). Mechanism TBD in build (likely `data-skin` on root + a session/env flag).
2. **Whole-app sweep.** One unified V4 token set across every surface — no half-warm/half-cool state.
3. **Hard rule (carried from the plan): freeze the DOM contract.** IDs / `data-*` / class names that
   JS or tests depend on do NOT get renamed. Only how things are painted changes. Where a V4 detail
   needs new markup, it's a one-component change with its tests updated in the same commit.

## Working method
User gives instructions for one page/surface at a time → I note them below (verbatim intent) →
I ground against the current code → reflect back. No code until the whole spec is agreed.

## Process (agreed)
1. **Design/scope every screen** page-by-page (in progress). Backend scaffolding may be built as we go
   when a screen needs net-new wiring (e.g. Ask was built early).
2. **Bidirectional COVERAGE AUDIT** once all screens are scoped, before front-end build:
   - **Forward:** every NEW piece of functionality defined in this spec → maps to an EXISTING wire
     (endpoint/repo/domain fn) OR gets NEW scaffolding created. No feature left without a wire.
   - **Backward:** every EXISTING wire/feature in the app → has a UI in the new design and is NOT
     orphaned/ignored. No capability silently dropped in the reskin.
3. **Then build** the front-end (parallel V4 skin, A/B-able) surface-by-surface.

### PAGE 2 — Shared chrome (left rail + header + right-side pane)
Status: SCOPING COMPLETE (pending user nod on the unified omnibox).

**Left rail:**
- Logo top-left, correctly sized.
- Top nav: Ask · Intel · Ads · Agents (active-state highlight). [Research removed as a rail surface.]
- Bottom: Settings · Integrations, plus **theme toggle** (light default, dark available) and **rail
  collapse/expand** (collapses to icons).

**Header:**
- **Surface name** (current screen).
- Top-right cluster: **profile menu** + **Refresh data** + **right-pane button**.
  - Profile menu folds in today's **⚙ Account**, the who's-signed-in **identity** (brand · agency),
    and the **Explainability (ƒ) toggle** (`explain_mode`, `/api/settings/app`).
  - Refresh data shows a **freshness indicator** ("updated 2h ago ⟳") — this is also where today's
    **Pulse** source-freshness surfaces (Pulse as a separate pane is retired).
- **Agency back-to-fleet bar** shown in chrome when an operator is drilled into a brand (existing backbar).

**Right slide-in pane (from the header pane button) — tabs:**
- **Rules** = existing detectors/thresholds (`#rulesBtn`/`#rulesDrawer`, `/api/settings/detectors`).
- **Follow-ups** = new (built).
- **Action list** = `ActionRepository` (recommended/executed actions).
- **History** = persisted Ask conversations (built).
- **Notifications** = folds today's **Activity** feed (`#actBtn` + unread count).

**Omnibox (UNIFIES global search + Ask entry — resolves "why 2?"):** ONE input, two paths —
- **Lookup path:** deterministic entity search (SKU / product / customer / surface → jump). No model,
  no usage. **NEW lightweight search wire needed (scaffold).**
- **Ask path:** natural-language question → starts an Ask conversation (existing `/api/ask`).
- Presentation: full-size **hero box on the Ask landing**; compact **header field** on other surfaces;
  **⌘K** summons it anywhere.

**Coverage notes (chrome):** existing→UI homes — Account→profile, Rules→pane, Activity→Notifications tab,
Pulse→Refresh freshness, explainability ƒ→profile, agency backbar→chrome, greet/ident/stamp→profile.
New wires to scaffold — entity-search endpoint (omnibox lookup). Ask/usage/pane-data already built.

### PAGE 3 — Intel (today's Intelligence, reskinned to the DLS; Research folded in)
Status: SCOPING COMPLETE. Pure reskin + one interaction change — NO new wires.

- **Sub-nav under Intel = 3 views** (NOT V4's Overall/Channel/Category/Item tabs — user rejected those):
  **Intelligence** (default, the merged insight feed) · **Category Analyst** · **Channels**. Analyst +
  Channels are the "2 sub-nav items parked under Intel."
- **Card → MODAL** (replaces today's inline dropdown expand): clicking a card opens the reskinned
  EXPANDED card as a modal — ANALYSIS INSIGHTS · KEY METRICS tiles · RECOMMENDED PLAY · GUARDRAILS —
  holding Why + the numbers + **Research further (L2)** + **Simulate** + all actions (View on Amazon ·
  Dismiss · Simulate · primary CTA). One modal = the single detail+action surface. Reuses the mockup's
  expanded-card design.
- **KPI band:** KEEP the existing **5** (Revenue / Margin / Cash / Inventory / Ads) + the 7/30/60-day
  window + **tap-a-metric-to-filter**. Restyled to the DLS (KPI cards get V4 sparklines). NOT adopting
  the AI/Dashboard toggle or Customize-KPIs.
- **Feed filtering:** KEEP family pills (Competitive/Demand/Opportunity/News&Risk) + category-pulse strip
  + "New since yesterday" toggle — restyled to the DLS.
- **The Realify Brief:** keep a **compact** brief line at the top of Intel (Ask owns the full hero).
- **Research folded in:** market/research stays MIXED into the Intelligence feed (News&Risk / research
  lens); "Research further" L2 deep-dive lives inside the card modal.
- Keep: crosslinks, empty state, ƒ explainability (toggle now lives in the profile menu per chrome).
- **Coverage:** all existing Intel features retain a UI; no capability dropped. **No new backend wires**
  (existing feed/cards/simulate/research/settings endpoints). Card→modal is a front-end change only.

### PAGE 4 — Ads (today's Profit & Ads / CMAA, reskinned)
Status: SCOPING COMPLETE. Pure reskin — every feature kept, NO new wires.

Keep ALL of today's `#cmaaView`: coverage banner + 4 honest resolution states
(NO_ENTITY_DATA/UNMAPPED/QUERY_ERROR/RENDERED_OK) · headline + aggregate band · 4 cohort quadrants
(keyboard/aria, tap-to-filter) · inline campaign detail (`#cmaaRecs`, R20) · cohort chips
(below_cost/cannibalization) · the worklist (SKU/title · ACoS-vs-break-even micro-bar · CMAA · bucket
money anchor · trend) · row→modal (`_famOpenSku` / `_cmBasicModal`) · Fix-Ads modal (actionable +
advisory cards, Apply/Preview/Open-in-Amazon/Why/Simulate, footer projected-if-all + Export + Apply-all
+ guardrails) · interactive Simulate (30/60/90 + probability, `/api/ads/simulate`) · bulk bar · CSV
export · sample/demo banners · scope bar.

Reskin decisions:
- Serif→sans; quadrants/rows/banners/chips/buttons → DLS (tiles, pills, near-black primary CTA, tinted
  boxes).
- **Fix-Ads modal → reskinned to MATCH the Intel card-modal language** (tiles / tinted PLAN+GUARDRAILS
  boxes) while **keeping ALL its functionality** (the richer multi-card structure, Apply-all, Export,
  guardrails). [User confirmed.]
- **Keep BOTH explainability affordances: the `ƒ` formula tags AND the `ⓘ` info/explain tags.** [User.]
- Row→modal already the current behavior — consistent with the Intel decision.
- **Coverage:** no capability dropped; **no new backend wires** (`/api/cmaa*`, `/api/ads/*`,
  `/api/cmaa/action` unchanged). Front-end reskin only.

### CROSS-CUTTING — RIA model backbone (the 11 feed domains)
Status: design doc written for the cofononder → `RIA-MODEL-INTEGRATION.md`. Decisions:
- **(1) Models are being written by the cofononder (external), not live yet** → the app builds a
  **Domain Registry + `invoke` seam + status-aware stub** (same pattern as the Ask narrator seam); live
  models drop in behind the contract. The doc is the interface he implements against.
- **(2) YES — formalize ONE canonical Domain Capability Registry** (extends `realify/models.py`
  REGISTRY/predict_for/registry_view/disabled_ids). Single source of truth read by every surface.
- **(3) YES — re-anchor the Ask tool-router (and, when designed, Agents) on the 11 domains** with
  propagated status honesty (live/rule/held). NOTE: `realify/ask/tools.py` currently routes by card-group
  → to be re-anchored on the registry during build.
- **(4) YES — surface status in Settings** ("Intelligence models" panel via `registry_view` + per-tenant
  toggles) **+ inline held-badges** where a domain can't answer yet.
- 11 domains: 7 live-AI (Inventory·chronos-2, Pricing·LightGBM, Sales·chronos, Opportunity/Content·Qwen,
  Competitive·signal-graph, News·Gemma, Risk-Rating·drift), 2 rules-by-design (Margin, Cash),
  2 held-on-data (Demand·Moirai needs per-SKU price history; Ads·EconML needs real ad spend/bid log).
- Invariants carried over: **inform-only** (never overrides locked L1 numbers) + **fail-silent**
  (timeout/crash → degrade to low, never wrong). `held` never fabricates (= today's ad_resolution).

### PAGE 5 — Settings (bottom rail)
Status: SCOPING COMPLETE.

- **Account:** name + email (name editable, `users.name`); **role badges** (informational) — Agency
  admin/member (`agency_members` + `agencies.owner_user_id` + `grants.role`), Brand owner/member
  (`users.role`), Realify admin (`is_staff_email`), Realify tester (`account_type='tester'`/sandbox);
  **change password** (NEW authed endpoint — today only email-reset exists); **delete account** (exists);
  **log out** (exists); **upload DP/avatar** (NEW — `users.avatar` col + upload path); **Plan & billing**
  (brands → Stripe portal link); **Staff → operator tools** (Realify admin gets a link to the superlogin
  hub / admin.html).
- **Product Catalog:** the full SKU cockpit re-homed as a Settings sub-page (table + edit COGS +
  completeness + add/replace files — existing catalog upload flow).
- **Intelligence models (RIA panel):** all 11 domains with Live/Rule/Held badges. Brands see it
  **read-only (status)**; **on/off toggling is tester/admin-only** (`models_disabled`, default on).
- **Tester / sandbox section (tester + Realify-admin only):** ALL existing synthetic ops kept together —
  **Resynthesize** (`/api/settings/resynthesize`), **models on/off**, **Wipe & re-onboard**, **Refresh
  market data**, **Inject scenarios** (sandbox), **Reseed forecast history**.
- **Agency users:** Settings **links out to the existing `/agency/console`** (fleet/team/billing/
  engagements) — NOT embedded (it's a large RLS-scoped surface of its own). [reco accepted]
- **Brand users:** invite others (existing `membersBox` + invites/roles).
- **Superlogin (Q7):** stays its OWN standalone, separately-gated operator surface OUTSIDE the app
  (separate `superlogin_session` auth, out of the SPA). Settings only links staff to it. V4 reskin of it
  is optional/low-priority.
- **New wires to scaffold:** authenticated change-password endpoint; avatar column + upload. Everything
  else maps to existing (catalog, resynth, detectors/models, invites, billing portal, lifecycle-delete).

### PAGE 6 — Integrations (bottom rail)
Status: SCOPING COMPLETE.
- Connected data sources (Amazon/Shopify/TikTok…) with status + freshness.
- **Connect / upload (CSV):** reuse the SAME unified upload module as the Product Catalog page — the R21
  onboarding drag-drop **recognizer → `/api/onboard/reports`** (full pipeline: recognition + write_ingest
  + safe_ingest_ad_graph + run_pipeline). ONE module across the app; the auto-recognizer classifies any
  dropped CSV. [User directive: "use the correct upload module — the same one used in the product page."]
- **RETIRED: the separate per-channel `/api/ingest/upload` grid** — superseded by the recognizer. No
  second/divergent upload path (that divergence was the R21 bug: in-app uploads that skipped the
  ad-graph). Guard: every CSV entry point app-wide routes through `/api/onboard/reports`.
- OAuth connectors shown as "coming soon" tiles (CSV is the live path).
- Channel interpretation confirmations (`confRegistry`).
- COGS upload/template. Data completeness (`completenessBox`).
- (Cross-channel ANALYSIS stays under Intel › Channels.)
- **Coverage:** no new wires — reuses `/api/onboard/reports`; consolidates upload paths (removes the
  lesser `/api/ingest/upload` and `/api/skus/upload` divergences from the UI).

### PAGE 7 — Agents (WORKFORCE) — SOURCE DOCS DIGESTED; scoping in progress
Inputs: `Realify_Agents_EndToEnd.pptx` (15sl), `Realify_Pricing_Execution-1.pptx` (10sl),
`Pricing-Agent-Scope-Hierarchy (1).pdf`. Nested sub-agents listed under Agents in the left rail.

**Workforce model (End-to-End):** lifecycle Onboard(5-step: role→scope→autonomy→tasks→review) →
Configure(Overview·Instructions·Guardrails·Tasks·Performance·Activity) → Assign(tasks × cadence ×
autonomy) → Monitor(perf + Ledger). **Autonomy ladder Observe→Suggest→Assist→Act** (per agent/task/lens;
start in Observe). **Guardrails enforced server-side** (floor, max-change%, inventory-first gate, BuyBox
floor, freq cap, blast radius, escalate conf<0.6 / >$500). **Arbiter** resolves cross-agent conflicts by
portfolio priority. **Autonomy Ledger** = hash-chained, tamper-evident, reversible. Specialists: Pricing &
Margin · Discovery/Category Analyst · Campaign Manager · Fulfillment Analyst · Channel Strategist.
Extra surfaces in deck: Tasks & Schedule, Shadow Mode, Autonomy Ledger.

**Pricing agent "runs like a GMM" (Pricing Execution):** Four Clocks (Annual sets plane / Seasonal
curves / Monthly refit / Daily loop) · Five Signals (competitor, margin CM3/TACoS, sell-through STR-vs-
curve, promo/events, in-stock HARD cover-block gate) · **ITL-ARB-01 ladder** (hard gates → category role
→ portfolio margin cap → markdown budget → price-image band) · daily loop SOP (read→classify→respond→
arbitrate→decide; auto in-band / HITL if invariant-crossing).

**Scope Hierarchy (PDF) — foundational data model:** Category (annual job: role, margin target, markdown
budget, architecture, calendar) → Subcategory = CPS row (seasonal/monthly: archetype, thresholds, STR
curve, ladder depths, cover-block WOC, elasticity class, floor%) → Item = SKU×channel (runtime state).
**Policy inherits DOWN** (effective_policy = category ⊕ subcat CPS ⊕ item override); **outcomes/budget
aggregate UP** (item markdown draws subcat's slice of category budget; blocked if subcat budget exhausted
→ HITL reallocation). Data objects: CanonicalState · TriggerEvent · DecisionObject · effective_policy ·
ClockContext.

**Reuse (not net-new):** agents consume the RIA registry (11 domains); Autonomy Ledger extends the
existing hash-chained agency ledger; guardrails/autonomy extend the agency PDP/envelope + propose-vs-
execute (`agency/execution.py`, PDP caps); decisions/handoffs → Action list + Follow-ups + Notifications;
⌘K "Ask…act" = the chrome omnibox. NEW: specialist/onboarding model, autonomy-per-task/lens, tasks &
schedule, Arbiter, Shadow Mode, the pricing scope-hierarchy + four-clocks/five-signals engine.

**CONFIRMED DECISIONS (all yes):**
1. **Nav:** keep our rail; **Agents expands to nested sub-items** = the specialists **+ Tasks & Schedule
   + Autonomy Ledger + Shadow Mode**.
2. **Roster/depth:** build the full **Agents framework** (onboard→configure→assign→monitor + autonomy +
   guardrails + ledger) **+ Pricing & Margin as the flagship** (four-clocks / five-signals /
   scope-hierarchy); other four specialists (Discovery/Category Analyst, Campaign, Fulfillment, Channel
   Strategist) = **onboarding-catalog shells** for now.
3. **Scaffold-vs-real:** scaffold honestly (like Ask) — framework + Pricing loop run against stub/held
   models; **Act gated** until models + Amazon write are live; agents start Observe/Suggest.
   **+ For tester/sandbox accounts, SEED sample agent decisions** (populated Autonomy Ledger + activity +
   performance) so it demos real — same synthetic path as the rest of the app; real customers stay
   honest-empty until agents run.
4. **Reuse:** Autonomy Ledger extends the existing hash-chained ledger; guardrails/autonomy + propose-vs-
   execute extend the agency PDP/envelope machinery.
5. **Pricing scope-hierarchy:** scaffold the Category/Subcategory/Item scope tables + downward
   effective-policy resolution + upward budget/outcome roll-up + the ITL-ARB-01 ladder as STRUCTURE;
   elasticity/pricing math HELD for the cofononder's model.
6. **Arbiter:** scaffold now as the decision-arbitration seam (even if only Pricing feeds it initially).

**BUILD NOTE:** Agents is the largest surface — a subsystem, not a page. Treat as its own multi-phase
workstream at build time (framework → Pricing flagship → scope-hierarchy/engine → Arbiter/Ledger →
tester seed). Scoping COMPLETE.

### PAGE 8 — Onboarding / auth (`login.html`) — RESKIN
Keep all flows; apply DLS (login.html is already sans → low lift). No new wires.
- **Sign-in / sign-up** (`#auth`, `#acctWrap`), **password reset** (`auth.request_reset` — email token).
- **Account-type gate** (`#gate`: choose customer vs tester).
- **Customer "Connect your data"** (`#obCustomer`, `custProvision`, `wizardStart`/`obWizard`) — this is
  the **unified upload module** (R21) reused by add-data + Integrations. Keep.
- **Tester onboarding** (`#ob`, country/`provision`). **Join / invite-accept** (`initJoin`).
- Handlers kept: `showOnboarding/showGate/showCustomerOnboarding/routeAfterAuth/initJoin`.
- Coverage: no capability dropped; no new wires.

### PAGE 9 — Marketing site (`site/ui_platform`, `ui_pricing`, `ui_agencies`, `ui_about`, `ui_faq`) — RESKIN
Highest-leverage token swap: all built on **`site/tokens.py`** (shared) → flipping those token *values*
to V4 reskins every marketing + agency-site surface at once.
- Front door (`ui_platform`: hero/features/pricing teaser/plans), **Pricing** (tiers/plans/features),
  **Realify-for-Agencies** landing, **About**, **FAQ** — all kept, DLS-restyled.
- Fix the misnamed `--blue` (currently terracotta) during the swap.
- Coverage: content/sections unchanged; no new wires.
- **STATUS: DEPLOYED (R22, commit c767f3d).** Swapped `tokens.TOKENS` → V4 cool/all-sans (light default,
  single theme); fixed misnamed `--blue`; surgical warm→cool sweep of `ui.py` neutrals/accent; LEFT Google
  OAuth colors + family tints untouched; `test_r10_tokens.py` updated in lockstep. Heading face = all-sans
  (flip `--serif` value for a display serif). Verified: all 5 pages render clean; 555 tests pass; live
  front door serves `--bg:#F4F6F9`/`--blue:#2E68E6`. Agency hub (hubkit) + frontend.html SPA still warm —
  those reskin at PAGE 10 / the SPA build (parallel flag).

### PAGE 10 — Agency console (`agency_console`, `agency_team`, `site/fleet`, `brandscope`, consent) — RESKIN
Built on hubkit/tokens → token swap reskins it. Keep all features.
- **`/agency/console`** — fleet grid ($-at-stake cards) + Add-a-client panel + queue endpoints.
- **`/agency/team`** — invite / reassign / view-as / assign / remove.
- **Consent flow** (`agency_consent`), **back-to-fleet bar** (`backbar`, shown in chrome when acting).
- Brand **drill-in** already routes into the reskinned five-lens app (R15 unified) — `brandscope`
  scope-switcher largely superseded; keep only what drill-in still uses.
- Settings links agency users here (decided PAGE 5). Coverage: no capability dropped; no new wires.

### PAGE 11 — Ops (`admin.html`, `analytics.html`) + superlogin — RESKIN (low-priority, internal)
Staff-only internal surfaces; functional DLS pass, not pixel-perfect.
- **Operator Console** (`admin.html`): key gate · system health · sources · documentation links · usage
  statistics · organizations/tenants (delete/manage). **Analytics** (`analytics.html`): usage funnels +
  charts + KPIs. Give charts the DLS treatment (area fill, faint grid, emphasized endpoint).
- **Superlogin hub** (`site/hub.py`) stays OUTSIDE (Q7); optional DLS pass later. Settings staff→ops link
  points here. Coverage: no capability dropped; no new wires.

## ZERO-RISK DEPLOY STRATEGY (parallel skin, A/B, instant rollback)

Principle: the new UI ships **additive + dormant + flag-gated**, so a deploy changes NOTHING a user sees
until the flag is flipped — and the flip is per-request (no redeploy to enable or roll back).

1. **Freeze the existing UI — parallel files, not edits.** The V4 SPA is authored as NEW files
   (`frontend_v4.html` + new CSS/components), leaving `frontend.html` / `login.html` / their JS / their
   tests **untouched**. Legacy literally cannot regress because its files don't change. (Marketing R22
   was an exception — a reversible in-place token swap, already shipped.)
2. **Additive backend only.** New routers (Ask, omnibox-search, RIA, Agents) never modify existing
   routes. New tables are **CREATE-only** migrations; the only existing-table change allowed is an
   **additive nullable column** (e.g. `users.avatar`). Existing endpoints/`/api/v1` contract unchanged →
   legacy keeps working byte-identical. Preserve the `/api/v1` dual-mount.
3. **The skin switch — a per-request resolver** `resolve_skin(request, tenant)`, precedence:
   `?skin=v4|legacy` query (testers/you) > per-tenant setting > **global DB rollout flag**
   (`skin_v4_rollout` in sandbox_settings: `off | internal | <pct> | on`). **Default = legacy (off).**
   Page routes (`home()`, etc.) pick the template off this — one branch.
4. **Instant kill switch.** The global rollout flag is read from the DB **per request**, so flipping it
   (off) reverts everyone on the next request — **no redeploy**. Docker rollback image is the deploy-level
   backstop.
5. **Rollout stages:** (a) deploy v4 code with flag OFF — a no-op release that de-risks the deploy itself;
   (b) dogfood via `?skin=v4` / your tenant; (c) enable for testers, then a % cohort; (d) monitor
   (errors, Ledger, Ask usage); (e) flip default → v4 when confident; (f) later retire legacy files.
6. **Gates before each deploy:** full non-agency suite green + agency suite on the PG harness; **Postgres
   smoke (`run.py doctor --postgres`) for every new migration**; new-UI tests added; the realify_admin
   one-shot before recreate when a migration is present.

**SKIN vs BEHAVIOR (net-new functionality like Agents):**
- **Skin flag = presentation only.** Flip to legacy → new surfaces' UI hides; their data (ask_*, agent_*,
  Ledger, follow-ups) is ADDITIVE + persisted → invisible but intact, fully restored on flip-back. No
  destructive revert.
- **Behavior = separate feature gates**, NOT the skin. `feature_enabled('agents', tid)` default OFF +
  autonomy ladder (start Observe) + Act-gated-until-models-live + server-side guardrails. Flipping a
  tenant to legacy PAUSES agent execution (scheduler skips agent tasks) → never unmonitored autonomy.

**BUILT + CODIFIED — the Feature/Version Registry (`realify/flags.py`) — the STANDARD CONVENTION.**
See `FEATURE-REGISTRY.md`. Every new feature/version ships dark behind it; turned on / rolled back
entirely from **Ops** (`/ops` → Rollout). Two kinds: VERSION features (pick the build + scope; rollback =
pick prior version / scope off — e.g. `app_ui`: legacy(baseline)/v4) and GATE features (behavior on/off,
default off, independent of version — e.g. `ask`, `agents`). DB-backed (system tid 0 + per-tenant, no FK)
→ read per request → instant, no redeploy. Ops catalog UI + `GET/POST /api/admin/rollout` (admin-gated).
`home()` guarded branch serves `frontend_v4.html` only when app_ui resolves v4 AND the file exists → pure
no-op today. `tests/test_flags.py` (8). **DEPLOYED (switch only; Ask backend NOT included).**

## COVERAGE AUDIT (bidirectional) — run against the full route/feature inventory

### Backward (every existing wire/feature → a home in the new design)
Clean mappings (no gap): insights feed/kpis/headline/summary/categories → **Intel**; channels/cross,
channels/list → **Intel › Channels**; analyst → **Intel › Category Analyst**; cmaa + ads/* → **Ads**;
card explain/why/research/ask/action/dismiss/clickout → **Intel card modal**; skus/edit/export/upload →
**Settings › Product Catalog**; interpretation + cogs + ingest/onboard/reports + completeness →
**Integrations**; detectors/rules → **Rules pane tab**; models/settings.models/metrics.history →
**Settings › Intelligence models**; settings.app → **profile menu**; resynth/wipe/refresh_market/rebuild →
**Settings › Tester**; auth/login/join/reset → **Onboarding**; delete/logout/me/members/invites +
billing.portal/subscription → **Settings › Account**; log/status → **chrome Refresh + Notifications
(Activity) pane tab**; admin/* + ops/* → **Ops (PAGE 11)**; all agency_* → **Agency console (PAGE 10)** +
Settings link-out; superlogin → **outside (Q7)**.

**GAPS — existing features with NO explicit home (need a decision):**
- **G1 · Watchlist** (`/api/watchlist`, card `watch` action) — no home in the new IA.
- **G2 · Sourcing pipeline** (`/api/sourcing`, `/sourcing/export`, card `sourcing`) — the expansion/
  opportunity list; no explicit home.
- **G3 · Save brief** (`/api/card/{id}/save_brief`) — saved briefs; no home.
- **G4 (minor) · Pulse drawer** — "surface directory" (→ nav/omnibox) + "confidence scale" explainer +
  "sources & freshness" (→ chrome Refresh). Mostly absorbed; confirm the confidence-scale explainer isn't lost.
- **Note** — `insights/cards/cmaa/analyst` are dual-mounted at `/api/v1` (frozen partner contract). Not a
  UI; keep the dual-mount intact through the reskin (don't break the v1 paths).

### Forward (every new feature → an existing wire or new scaffold)
Built: Ask (`/api/ask*`). Maps to existing: Notifications tab → `/api/log`; Settings model panel →
`/api/models`/`registry_view`; profile ƒ toggle → `/api/settings/app`; Autonomy Ledger → hash-chained
ledger; agent guardrails → PDP/`agency/execution.py`. **New scaffold flagged:** omnibox entity-search
endpoint; avatar upload + authed change-password; RIA domain registry + `invoke` seam (+ cofononder
models); Agents subsystem (framework, tasks&schedule, Arbiter, scope-hierarchy tables, tester seed);
Follow-ups store must accept non-Ask sources if G1/G3 fold into it.

### Gap resolutions — CONFIRMED (user approved)
- **G1 Watchlist + G3 Save-brief → fold into the Follow-ups pane** (extend the followup store to accept
  `watch` / `brief` sources; pane already exists). Follow-ups store gains a `source` field.
- **G2 Sourcing → the Discovery / Category-Analyst AGENT** (its ranked expansion pipeline) + surfaced in
  **Intel**. The `/api/sourcing*` wires feed that agent's view.
- **G4 → confidence-scale explainer rehomes to profile/help; standalone Pulse drawer retired**, nothing dropped.
**→ Spec is coverage-complete: every wire has a UI, every new feature has a wire.**

## Surface checklist (walk in any order)
Seller app — `frontend.html`
- [ ] Top nav / header (logo, search, KPI window/filter chips, account button)
- [ ] Intelligence feed + card  ← already mocked (the pilot)
- [ ] Intelligence KPI band (Revenue / Margin / Cash / Inventory / Ads)
- [ ] Product Catalog (SKU table + completeness)
- [ ] Profit & Ads (CMAA worklist + cohort tabs)
- [ ] Fix-Ads modal (campaign detail, Simulate, ƒ explainability)
- [ ] Category Analyst (overnight memo)
- [ ] Channels (cross-channel view + upload)
- [ ] Account drawer (reports/COGS, tester controls, danger zone)
- [ ] SKU drawer / Pulse drawer / explainability modal

Onboarding / auth — `login.html`
- [ ] Sign-in + account-type gate
- [ ] Customer "Connect your data" uploader (+ add-data mode)
- [ ] Tester onboarding · Join (invite)

Marketing & agency — `site/*`
- [ ] Marketing front door (ui_platform)
- [ ] Pricing (ui_pricing) · About · FAQ
- [ ] Agency console / hub / fleet
- [ ] Brand drill-in (brandscope) + back-bar
- [ ] Consent pages · state pages

Ops / internal
- [ ] Superlogin hub
- [ ] admin.html · analytics.html

## Per-page notes

### PAGE 1 — "Ask" (net-new default home) + left-nav restructure
Status: SCOPING (user asked to stop & clarify before noting/building). Q1 answered; Q2–9 open.

**Nav / IA (Q1 — answered):**
- **Ask = default landing** (replaces today's default, which is Product Catalog).
- **Intel** = today's Intelligence surface, with Research (market signals) folded in — same as current app.
  - **Category Analyst** and **Channels** move UNDER Intel as **sub-nav**.
- **Ads** = today's Profit & Ads (CMAA).
- **Agents** = NEW surface (the only net-new rail surface).
- **Research** = **REMOVED as a rail surface** (user, later decision). Market-signals research stays
  folded into Intel, unchanged. No standalone Research surface.
- Bottom rail: **Settings**, **Integrations** (two buttons).
- **Product Catalog** (today's landing) → moves INTO the **Settings** page.

**Rail order (top):** Ask · Intel · Ads · Agents   **(bottom):** Settings · Integrations
One new surface: Agents.

**Ask page — described intent (not yet confirmed, see Q2–9):**
- Animated Realify logo; centered text box; generated headline-with-highlights above (reuse Intel/Ads thesis).
- Below box: category chips {Performance, Cash, Ads, Forecasts, Competition} → pick one → 5 questions drop down.
- Click a question → submits like a typed prompt → starts conversation (Claude-style: input drops to bottom,
  transcript above). Categories collapse into an expandable corner control on the input.
- Model picker (multi-model). Usage = text-box outline rendered in a different color + small %, 100 queries/mo = full.
- Per-response actions: Copy · Speak · Good · Bad · mark-as-follow-up.
- Backend: real `/api/ask` endpoint with a swappable STUB model.

**Ask page — confirmed decisions:**
- **Q2 (headline):** REUSE the live generated thesis (personalized, data-driven, with highlighted spans) —
  same mechanism as the Intel/Ads thesis. Not a static welcome. [Default accepted.]
- **Q3 (categories):** 5 categories, in this order → **Performance · Cash · Ads · Forecasts · Competition**.
  (Margin → renamed to Performance.)
- **Q4 (category questions):** STATIC/curated for now; `/api/ask` shaped so they can become data-generated
  later. v1 seed set below (editable):
  - **Performance:** (1) Which SKUs are quietly losing money after fees and ads? (2) What's driving my
    margin change versus last month? (3) Which products grew fastest this week — and why? (4) Where am I
    leaving profit on the table right now? (5) Is my overall profitability trending up or down?
  - **Cash:** (1) Which SKUs are about to stock out? (2) Where is my cash tied up in slow-moving inventory?
    (3) What should I reorder this week, and how much? (4) Which products are overstocked and bleeding
    storage fees? (5) How many days of cover do I have across the catalog?
  - **Ads:** (1) Where am I wasting ad spend right now? (2) Which campaigns are below break-even ACoS?
    (3) Which SKUs have room to scale spend profitably? (4) What keywords drain budget without converting?
    (5) How is my ROAS trending, and what's moving it?
  - **Forecasts:** (1) What will sales look like over the next 30 days? (2) Which products are trending up
    in demand? (3) Am I stocked for the demand I'm forecasting? (4) What's my projected revenue this month
    at current pace? (5) Which SKUs face a seasonal drop soon?
  - **Competition:** (1) Who's undercutting me on price right now? (2) Where am I losing the Buy Box — and
    why? (3) How does my pricing compare to the market? (4) Which competitors are gaining share in my
    categories? (5) What should I reprice to win back sales?
- **Q5 (usage):** REAL server-side counter, per tenant, **resets monthly**; 100 queries/mo = full.
  The text-box **outline** renders overall monthly usage in a different color + a small % readout.
  **Per-model** usage breakdown shown inside the model-picker dropdown. [Default accepted.]
- **Q6 (mark as follow-up):** "Mark as follow-up" adds the response to a **right-side PANE**.
  - Pane is opened by a **button in the top-right of the header** (mirrors V4's Notifications pane pattern).
  - Pane has **4 tabs: Rules · Follow-ups · Action list · History**.
  - Follow-ups tab receives the marked responses.
  - **All 4 tabs are REAL/functional** (not placeholders).
  - The **conversation/dialog itself is net-new → scaffolded** with the stub model. But: response text is
    stubbed while **storage + UI + usage counting are real**, so `History` shows genuine past chats.
  - **Q8 persistence RESOLVED → YES, persist conversations** (History depends on it). Model stays stubbed.
  - Data sources:
    - **Rules** = the EXISTING "Detectors & thresholds" feature (today's header `#rulesBtn` → `#rulesDrawer`,
      backed by `/api/settings/detectors`) — thresholds/on-off/severity per detector. Reused, moved into
      this pane as the Rules tab. [Confirmed by user: "Rules are thresholds… already in the app."]
    - **Follow-ups** = user-marked responses (new store, we build it).
    - **History** = persisted Ask conversations.
    - **Action list** = the existing recommended/executed actions (`ActionRepository`: CMAA/Ads
      recommendations you Apply + what you've executed), as a running list. [Confirmed by user.]
- **Q7 (backend) — "as rich as possible", agent skeleton (user: "yes. build the scaffolding… we'll put
  in a model later. We will probably host our own model"):** SSE streaming · stateful (full history) ·
  tenant-scoped + context pack · tool-router over the SAME domain code the cards use · data-grounded
  STUB narrator · structured response parts (text + tiles + citations + actions + follow-ups) ·
  provider-agnostic narrator seam (future = SELF-HOSTED model, not Anthropic).
- **Q8 (models + persistence):** picker = **Realify Pro** (default) + **Realify Fast** (both provider
  "stub" today); **conversations ARE persisted** (History tab is real). Model list is data-driven.
- **Q9 (confirms) — CLOSED:** Speak = browser TTS ✓ · Good/Bad = thumbs stored server-side ✓ (backend
  built) · **logo = DRAW-ON ASSEMBLY animation** (the mark assembles/draws itself in). All other
  Ask-page visual micro-decisions = default from the V4 DLS/mockup (empty→chat transition, category
  chips collapsing into the input's corner control, model-picker placement, usage-outline color,
  per-message action-row styling).

**PAGE 1 (Ask) — SCOPING COMPLETE.** Backend scaffolding built + tested. Front-end build PENDING
(deferred until all screens are scoped, per the process below).

**BUILT — backend scaffolding (local + tested, NOT deployed, no UI yet):**
- `migrations/versions/0039_ask.py` — ask_conversation / ask_message / ask_message_feedback /
  ask_followup / ask_usage. Cross-dialect (SQLite + PG via schema_to_postgres), PG grants, NO RLS
  (seller-data pattern). Head now 0039.
- `realify/repositories/ask_repo.py`; `realify/ask/{models,context,tools,narrator,service}.py`;
  `realify/routers/ask.py`; registered in run.py make_app under `/api`.
- Endpoints: `POST /api/ask` (SSE), `/ask/categories`, `/ask/models`, `/ask/usage`,
  `/ask/conversations[/{id}]`, `/ask/feedback`, `/ask/followup`, `/ask/followups`.
- Usage: per-tenant monthly counter, cap 100 (`ask.models.MONTHLY_QUERY_CAP`).
- Tests: `tests/test_ask.py` (9). Full non-agency suite green (555 pass / 1 skip).
- **NOT done:** frontend Ask page / nav rail / right-side pane (reskin UI, still scoping);
  Postgres smoke (`run.py doctor --postgres`) pending; deploy pending; real model (self-hosted) pending.
- **Model swap point:** `realify/ask/narrator.py` — implement `SelfHostedNarrator.compose` (POST to the
  inference endpoint, map reply → {content, parts}); add a MODELS entry with provider "self_hosted".
  - Header consolidation: the new top-right pane button subsumes today's separate ⚙ Rules button.
