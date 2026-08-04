# Agents (the Realify workforce) — architecture

**Audience:** the app team. The internal design for the Agents surface — an AI *workforce* of specialists
that reason over the RIA domains and act, under autonomy + guardrails, with a tamper-evident ledger.
Source of truth for scope decisions is `V4-RESKIN-SPEC.md` (PAGE 7). Model-side contract is
`RIA-MODEL-INTEGRATION.md` (esp. §10). This doc is the *how we build it*.

**One line:** hire a specialist → configure it → assign tasks on cadences → it decides within
server-side guardrails at its autonomy level → every decision is logged, reversible, and (when they
conflict) arbitrated.

---

## 1. Model — an AI workforce, not scripts

**Lifecycle (per specialist):** Onboard (5-step hire: role → scope/access → autonomy → tasks/cadence →
review) → Configure (Overview · Instructions · Guardrails · Tasks · Performance · Activity) → Assign
(tasks, each with its own cadence + autonomy) → Monitor (performance trends + the Autonomy Ledger).

**Autonomy ladder** — set per **agent**, per **task**, and per **lens**; new hires start in **Observe**:
- **Observe** — sees + logs, acts on nothing.
- **Suggest** — recommends; human approves each.
- **Assist** — handles routine, escalates the big calls.
- **Act** — executes within guardrails.

**Guardrails — enforced server-side (control plane).** The agent *literally cannot act outside them* at
any autonomy level: contribution floor per SKU, max change % per move, inventory-first gate (pause raises
when cover < N days), Buy-Box-never-below-floor, change-frequency cap, blast-radius per batch, escalate
to human (confidence < 0.6 or impact > $X).

**The Arbiter** — resolves cross-agent conflicts (Pricing vs Ads vs Inventory) by portfolio priority, so
"Ads wants to spend, Pricing wants to cut, but cover is 6 days → pacing wins" is a single coherent call.

**Autonomy Ledger** — hash-chained, tamper-evident, signal-tagged, **every action reversible**; the audit
spine for Applied / Awaiting / Handoff decisions.

**Specialists (roster):** **Pricing & Margin** (flagship, fully specced) · Discovery / Category Analyst ·
Campaign Manager · Fulfillment Analyst · Channel Strategist (the latter four = onboarding-catalog shells
for now).

**Rail:** our agreed rail is kept; **Agents expands to nested sub-items** = the specialists **+ Tasks &
Schedule + Autonomy Ledger + Shadow Mode**.

---

## 2. The Pricing agent — "runs like a GMM" (flagship)

**Four clocks** (slower clocks set the plane; the daily clock executes within it; outcomes feed back up):
- **Annual** — sets the control plane: category roles, portfolio CM3 targets, markdown budgets, MAP &
  floors, event calendar, competitive posture.
- **Seasonal** — per-archetype curves: build→manage→exit, ladder depths, event depth ceilings.
- **Monthly** — paces & recalibrates: margin close, markdown-budget burn, **elasticity refit**, CPS
  re-baseline.
- **Daily** — runs the SOP + five-signal engine within the plane above.

**Five signals** → source → trigger → role-steered response → auto/HITL line:
1. **Competitor price** (Keepa) — rival moves a comparison KVI → role-steered (Traffic: follow sharp /
   Margin: hold & harvest); auto in-band, HITL below floor/MAP.
2. **Margin compression** (CM3 & TACoS) — drifts to floor / TACoS over target → raise into headroom, cut
   ad reliance; HITL for structural (bundle/delist/renegotiate).
3. **Sell-through** (STR vs plan curve) — off curve → slow: markdown step vs budget / hot: raise gated by
   cover; HITL step-2+/clearance.
4. **Promo events** (calendar/deal asks) — window opens / rival promos KVI → event price within depth
   ceiling; HITL doorbuster/below-floor.
5. **In-stock** (WOC/OOS/Buy-Box) — **HARD cover-block gate**: block demand cuts + ration via price when
   WOC < cover-block; HITL KVI-OOS/overstock clearance.

**ITL-ARB-01 priority ladder** (top rung wins): (1) **hard gates** (cover-block, CM3 floor, MAP) → (2)
**category role** (sets objective: image vs margin vs sell-through) → (3) **portfolio margin cap** → (4)
**markdown budget** → (5) **price-image band**.

**Daily loop SOP (per item):** read canonical state → classify (lifecycle × season × role) → role-steered
signal response → arbitrate (ITL-ARB-01) → decide (auto in-band / HITL if invariant-crossing) → write to
Ledger. *Same competitor −6% ⇒ different call per item* (Dutch Oven Margin/Destination → hold; Fry Pan
Traffic/KVI at 6-day cover → cover-block fires → restock, don't discount).

---

## 3. The scope hierarchy (foundational data model)

Three scoped levels; **policy inherits DOWN, outcomes + budget-burn aggregate UP.**

- **Category** — written by the **annual** job (GMM-approved): role · portfolio margin target · category
  markdown budget · price architecture · event calendar · competitive posture.
- **Subcategory = the CPS row** — written by the **seasonal + monthly** jobs: archetype · signal
  thresholds · planned STR curve · ladder depths · cover-block WOC · **elasticity class** · parity rule ·
  price-endings · min/max · freshness · review cadence.
- **Item = SKU × channel** — runtime state (Observe/Analyze): current price · lifecycle stage · live
  signals + confidence · WOC/STR · clock-context (season phase, days-to-deadline) · budget-remaining
  share.

**Downward — effective policy:** `effective_policy(item) = category_control_plane[category_id]
⊕ subcat_CPS[subcat_id] ⊕ item_overrides[id]` (rare hero-SKU hand-set floor wins). Built by walking the
tree.

**Upward — roll-up:** an item markdown draws down its subcat's slice of the category budget → can be
**blocked** if the subcat (or category) budget is exhausted *even when the other isn't* → **HITL** for the
GMM to reallocate. Item CM3 (units-weighted) → subcat realized margin → checked vs portfolio target. Item
STR-vs-curve → subcat pace → season plan & next buy.

**Data objects:** `CanonicalState` · `TriggerEvent` · `DecisionObject` · `effective_policy` ·
`ClockContext`.

---

## 4. Reuse map (build on existing, don't reinvent)

| Need | Reuse |
|---|---|
| Domain intelligence (price, elasticity, demand, inventory, competitive…) | **RIA registry** (11 domains) via the `invoke` seam + §10 `optimize`/`refit` |
| Tamper-evident decision log | **Existing hash-chained ledger** (agency ledger) → the Autonomy Ledger |
| Autonomy caps + propose-vs-execute | **Agency PDP / envelope machinery** (`agency/execution.py`, PDP `ROLES`, caps) |
| Decisions / approvals / handoffs surface | **Action list + Follow-ups + Notifications** (right-side pane) |
| Scheduling / cadence | **Scheduler** (periodic run seam) |
| Natural-language "analyze / simulate / act" entry | **Chrome ⌘K omnibox** (Ask) |
| Triggers on thresholds | **Detectors / rules** (`/api/settings/detectors`) |

**New to build:** the specialist/onboarding model; autonomy-per-task/lens; Tasks & Schedule; the Arbiter;
Shadow Mode; the pricing scope tables (Category/Subcategory-CPS/Item) + effective-policy resolution +
roll-up; the four-clocks/five-signals daily-loop engine (math **held** for RIA models); the tester seed.

---

## 5. Data model sketch (tenant-scoped, seller-data pattern; no RLS)

- `agent` — id, tenant_id, specialist_type, name, status (active/paused), autonomy (per-lens), created_at.
- `agent_task` — id, agent_id, tenant_id, name, scope (all/category/selected SKUs), cadence
  (realtime/hourly/daily/weekly/on-trigger + clock), autonomy, next_run, status.
- `agent_guardrail` — agent_id/task_id, kind (floor/max-change/cover-gate/buybox/freq/blast/escalate),
  params. **Checked server-side before any Act.**
- `agent_decision` — the Autonomy Ledger row: agent_id, task_id, signal, target (sku), action, projected
  value, confidence, state (applied/awaiting/handoff), reversible-token, **hash-chain link**, ts.
- Pricing scope: `pricing_category_plane` (role/targets/budget/architecture/calendar), `pricing_subcat_cps`
  (the CPS fields incl. elasticity_class), `pricing_item_state` (runtime) + `pricing_item_override`.
- Reuse `ask_*`/action/ledger where they already fit.

---

## 6. Honesty & gating (same discipline as Ask + RIA)

- **Act is gated** until the RIA models + real Amazon write-back are live; agents start **Observe/Suggest**
  and *propose* into the Action list.
- **Held domains → held agents** (Ad Optimizer, reprice→demand) — honest "needs {data}", never fabricated.
- **Testers/sandbox get SEEDED sample decisions** (populated Autonomy Ledger + activity + performance) so
  the surface demos real — same synthetic path as the rest of the app. Real customers stay honest-empty
  until agents actually run.
- Guardrails are a hard server-side boundary — enforced regardless of autonomy or model output.

---

## 7. Build phases (Agents is a subsystem, not a page)

1. **Framework** — specialist/onboarding model, autonomy ladder, guardrail engine (server-side), Tasks &
   Schedule, the Ledger (on the existing hash-chain), the Agents rail nest.
2. **Pricing flagship** — the four-clocks/five-signals daily loop SOP + the configure/monitor tabs, wired
   to the RIA `optimize`/`what_if` seam (held → Observe).
3. **Scope hierarchy + engine** — Category/Subcategory-CPS/Item tables, effective-policy resolution,
   upward roll-up/budget draw-down, ITL-ARB-01 arbitration.
4. **Arbiter + Ledger polish** — cross-agent conflict resolution; reversible actions; handoffs.
5. **Tester seed** — synthetic decisions/ledger/activity for sandbox accounts.
