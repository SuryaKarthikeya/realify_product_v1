# Realify — Deterministic Math Reference

The single source of truth for the deterministic (L1) calculations. Every number Realify
shows a seller is computed here, in code — the language layer (L2) only phrases these, it
never computes. This doc is generated from the actual source; keep it in sync when formulas
or their coefficients change.

**Status note (2026-07-07):** the base economics still live across several modules (seller.py,
seed.py, cogs.py, country.py, multichannel.py, pipeline/detect.py, pipeline/materialize.py) pending
the #005 Phase-1 consolidation into a single pure `domain/` layer with all coefficients in typed
config — see *How to change a formula* at the end. The **ads + projection** math below is already
consolidated in `domain/` (`economics.py`, `cmaa.py`, `sim_common.py` + `simulate.py`/`sim_intel.py`/
`sim_inventory.py`/`sim_flow.py`/`sim_market.py`) — one pure, tested definition of each identity.

---

## Unit economics & margin
| Name | Formula |
|---|---|
| Referral fee | `price × referral_pct` (IN 0.155, US 0.15) |
| Net profit / unit (full) | `price − COGS − referral − FBA_fee − ad_cost_unit − return_cost_unit` |
| Net profit / unit (customer, COGS-only) | `price − COGS − referral` (before FBA/ads/returns arrive) |
| Net margin % | `net_profit_unit / price × 100` |
| Break-even floor (full) | `(COGS + FBA + ad + returns) / (1 − referral_pct)` |
| Break-even floor (COGS-only) | `COGS / (1 − referral_pct)` |

## Sales & velocity
| Name | Formula |
|---|---|
| Velocity / day | `units_month / 30` |
| Units / year | `units_month × 12` |
| Annual revenue | `price × units_year` |
| Monthly revenue | `annual_rev / 12` |
| Implied sessions | `units_month / (conversion_pct / 100)` |

## Inventory
| Name | Formula |
|---|---|
| Days of cover | `stock_on_hand / velocity_day` |
| Channel days of cover | `on_hand / (units_month / 30)` |

## Multi-channel
| Name | Formula |
|---|---|
| Channel fee / unit | `price × (referral_pct + fulfilment_fee_pct + creator_pct)` |
| Channel net / unit | `price − COGS − fee_unit − ad_unit` |
| Channel margin % | `net_unit / price × 100` |
| Channel revenue | `price × units` |
| Cross-channel price spread % | `(max_price − min_price) / min_price × 100` |

## Detection primitives (pure functions; detectors compose these)
| Name | Formula |
|---|---|
| Threshold | `value < limit` (below) / `value > limit` (above) |
| Ratio vs baseline | `value / baseline ≥ ratio` (or `≤`) |
| Period-over-period % | `(current − prior) / prior × 100` |
| Z-score | `(value − mean) / std` |
| Slope (least-squares) | `Σ(x−x̄)(y−ȳ) / Σ(x−x̄)²` |
| Level crossing | direction of `prev → curr` across `level` |

## Exposure & ranking
| Name | Formula |
|---|---|
| Exposure — revenue at stake | `annual_rev / 12` |
| Exposure — stockout risk | `velocity_day × 30 × price` |
| Exposure — contested revenue | `annual_rev / 12 × 0.3` |
| Exposure % (card bar) | `min(95, max(20, exposure_inr / 250000 × 60))` |
| **Rank score** | `severity_weight × 1000 + exposure_comp × 3 + urgency` |
| ↳ severity_weight | crit 4, act 3, opp 2, watch 1 |
| ↳ exposure_comp | `min(100, max(0, exposure_inr / 250000 × 60))` |
| ↳ urgency | `min(200, max(0, (21 − days_to_stockout) × 8))` |
| 14-day trend % | `(latest − baseline) / baseline × 100`, baseline ≈ value 14d prior |

## Reported, not computed
`conversion_pct`, `buybox_pct`, `tacos`, `returns_rate`, `rating`, `review_count` are *ingested*
from reports (or synthesized for demo) — inputs, not formulas. Margin, floor, velocity, cover,
revenue, exposure, and rank are what we genuinely compute.

## Synthetic-generation heuristics — ⚠️ NOT business definitions
These fabricate demo data (random, seeded by ASIN hash); listed so they're not mistaken for
metric definitions: demo price `COGS × U(2.0,3.4)`; demo FBA `base + per_band × U(0,2)`; demo
ad/unit `price × U(0.02,0.06)`; demo return/unit `price × U(0.01,0.04)`; buybox/returns/tacos/
rating drawn from distributions.

## CMAA — Contribution Margin After Ads (built · `domain/cmaa.py`, `GET /api/cmaa`)
| Name | Formula |
|---|---|
| Break-even ACoS | `= gross contribution margin %` (the locked identity, #004) |
| Actual ACoS | `ad_spend / ad_sales` |
| ₹ above break-even (certain waste) | `max(ad_spend − ad_sales × breakeven_acos, 0)` |
| CMAA (contribution after ads) | `gross_contribution_unit × units_in_window − ad_spend` |
| CMAA % | `cmaa / net_revenue_in_window` |
| Scale upside (directional, bounded) | `incremental_ad_sales × (breakeven_acos − actual_acos)`, with `incremental_ad_sales ≤ (SCALE_MAX_MULTIPLE − 1) × ad_sales`, `SCALE_MAX_MULTIPLE = 2.0` |
| Quadrant | SCALE / FIX ADS / FIX MARGIN / CUT·DIVEST — from (above/below break-even) × (CMAA sign) |

`cmaa_reliable` withholds confident numbers off a thin/uneven ad window; a lifecycle-flagged SKU is guarded and never told to cut. Every recommendation-evidence line traces to one figure above (no LLM in the loop).

### Fix-Ads modal — `formula_id` registry (single source · `domain/formula_registry.py`)
Every number the Fix-Ads modal renders carries a `formula_id` resolved against this registry — the ƒ reveal (explainability on) prints the expression with the SKU's own inputs substituted, sourced `· admin registry`. `test_every_number_has_registered_formula` fails the build if any rendered `formula_id` is unregistered. Registry ids map to the rows above:

| `formula_id` | Row |
|---|---|
| `break_even_acos` | Break-even ACoS |
| `acos` | Actual ACoS |
| `cmaa` | CMAA (contribution after ads) |
| `recoverable` | ₹ above break-even (certain waste) |
| `cmaa_projection` | FIX ADS headline (30/60/90 projection behind `project()`) |
| `ad_coverage` | `coverage = mapped_ad_spend ÷ total_ad_spend` — the % of ad spend mapped to SKUs (confidence pill) |
| `tripwire_units` | `tripwire = units_wk < baseline_units_wk × (1 − 0.15)` — auto-revert guard on a bid cut |
| `combined_projection` | `combined = Σ proj_gain(recommendation_i)` — footer "Projected if all applied" |

## SIMULATE — deterministic scenario projection (built · `domain/sim_*`, `POST /cmaa/simulate`)
Scenario, not forecast. **Every projected figure = a current L1 value × a stated assumption, ramped to steady state**, emitted as an explain part and rendered verbatim. Targets default to the tenant's own detector threshold (`/api/settings/detectors`). `unit_contribution = price × net_margin% / 100`.

| Name | Formula |
|---|---|
| Ramp (linear) | `reached(day) = min(day / ramp_days, 1.0)`; horizon value `= base + steady_delta × reached(day)` |
| Confidence band | `expected = f(current_assumption)` (exactly the point); `conservative` / `optimistic` `= f(key_assumption ∓ half_width)` — so the point always lies within the band and the whole band moves on re-simulate |
| Degrade | required input missing → honest-empty (no projection); weak/undefined base → `sim_quality = "degraded"` + L1 reason (projection still shown; a null-base headline dims to "—") |

Per-model headline (₹/mo unless noted):

| Model (detector) | Headline formula |
|---|---|
| FIX ADS (P&A) | `recoverable − (1 − organic_hold) × (recoverable ÷ ACoS) × margin`; ≤ recoverable ceiling |
| SCALE (P&A) | `incremental_ad_sales × (breakeven − ACoS) × (1 − acos_drift)`; ≤ bounded scale-upside |
| CUT·DIVEST (P&A) | ad bleed stopped `= ad_spend` (immediate); organic_retention governs units at risk |
| FIX MARGIN / FIX-ECONOMICS | `price × new_margin × units_after − baseline`; `units_after = units × (1 − min(price_change × elasticity, 1))`; `new_margin = margin + price_change + cogs_cut + returns_cut` |
| REORDER (days-of-cover / stock-level) | protected `= min(units_lost, reorder_qty) × unit_contribution`; `units_lost = velocity × max(0, 90 − stock/velocity)`; overstock warns if post-reorder cover > 150d |
| DEMAND-CAPTURE (velocity / rank) | run-rate `= velocity × 30 × unit_contribution`; at-risk `= velocity × unit_contribution × days_out_of_stock` |
| TACOS-ARREST (tacos) | `spend_saved − (1 − organic_hold) × attributable_sales × margin`; `spend_saved = (tacos − target)/100 × sales`; `attributable_sales = spend_saved ÷ (tacos/100)`; ≤ spend_saved |
| RETURNS-REDUCTION (returns-rate) | `(return_rate − target)/100 × units × (unit_contribution + return_cost_unit)` |
| CVR-LIFT (conversion) | `(sessions × sessions_held × target_cvr/100 − current_units) × unit_contribution` |
| CONCENTRATION (revenue-share) | contribution at risk `= sku_monthly_revenue × shock% × margin` (a risk stress-test — the action is "diversify", which has no direct lever) |
| BUY-BOX-REGAIN (buy-box) | `units × (1 + recovery) × (price × (margin − price_cut)) − baseline`; `recovery = min(max(0, target − bb)/max(bb, 20) × sales_factor, 1.0)` (bounded) |
| PRICE-RESPONSE (C1) | respond − do-nothing; per-unit contribution after a cut `= price × (margin − price_cut)`; heavily ranged, directional (competitor reaction is not own data) |
| REVIEW-RECOVERY (rating) | `sessions × rating_lift × cvr_sensitivity × unit_contribution` — GATED on conversion data; wide range (the rating→sales link is the softest assumption) |
| GAP-CAPTURE (opportunity / assortment) | `gap_value × capture% × est_margin`, ramped over a 90-day launch; estimate · directional (gap + entry costs are estimates) |

## Cross-channel onboarding — Shopify unification (built · `realify/ingest/{crosswalk,normalize_finance}.py`)
Not economics coefficients — the deterministic RULES that keep cross-channel numbers correct. Rules-as-data (the manifest `natural_keys`, node-graph emit map) live in `realify/topology.py` + `realify/nodegraph.py`.

| Name | Rule |
|---|---|
| Record-level dedup | upsert on a manifest row's `natural_keys` (LAST wins), NOT a sum — an overlapping/wider Shopify re-export never double-counts (`SHOP_ORDERS` keys = order_name + lineitem_id) |
| SKU crosswalk (canonical) | `(channel, store_id, external_sku, external_variant_id) → canonical_sku_id`; `canonical = internal_sku`. Auto-map when Shopify Variant SKU == an Amazon SKU; blank/bundle SKU → parked; stated-IDENTICAL mismatch → parked + arm reconcile |
| MCF shared inventory | units at the Shopify "Amazon Fulfillment" location are the one FBA pool: `combined_on_hand(sku) = amazon_fba` for an MCF SKU (**not** `amazon_fba + shopify_own`); a self/3PL SKU adds the separate pools |
| MCF margin state | `partial` for an MCF SKU until `AMZ_MCF_FEES` lands (fulfilment cost is Amazon-side, absent from every Shopify file), else `complete` |
| Booked vs settled | `SHOP_ORDERS` = booked (reported); `SHOP_PAYOUTS` = settled net-of-fee (actual), joined on order id; unmatched order → `NOT_YET_PAID_OUT`. Both coexist; actual wins (existing `_BASIS_RANK`) |
| Exposure bar → gap ₹ (inverse) | `gap ≈ exposure_pct / 60 × 250000` (reconstructs a directional gap from the stored bar; clamped, so flagged as an estimate) |
| Goal completeness | per goal: `UNAVAILABLE` if a HARD input is absent (COGS→profit, ad-spend→ad-efficiency); `PARTIAL` if a soft flag blocks it or an essential file is pending; else `AVAILABLE` |

---

## How to change a formula (the config-driven policy)

Two kinds of "change", handled deliberately differently:

**1. Change a coefficient / threshold / weight → typed config, no code edit.**
All tunable numbers are config, not literals: `referral_pct`, `fba_fee_base` / `fba_fee_per_band`
(per-country profile), the rank weights (`severity_weight`, the `250000` exposure scale, the `×60`
/ `×3` factors, the `21`-day urgency knee and `×8` slope), the trend window (`14` days), and
per-rule thresholds (already rules-as-data in the `rules` table, e.g. margin floor, buy-box %,
days-of-cover). Changing any of these is a config/data change — no redeploy of logic, fully
testable, and per-tenant where it makes sense (e.g. a tenant's margin floor).

**2. Change a formula's structure → one pure function in `domain/`, one tested place.**
The *shape* of an identity (e.g. `net = price − COGS − referral − FBA − ad − returns`) lives as a
single pure function in the `domain/` layer (post-#005-refactor: `domain/economics.py`), which reads
its coefficients from config. To change the structure you edit that one function — not config, and
not five scattered copies.

**What we deliberately do NOT do: arbitrary formula expressions in config.** Letting formulas be
free-text expressions evaluated at runtime is an anti-pattern here — it's an injection surface, it
can't be unit-tested or type-checked, and it makes the deterministic layer impossible to reason
about or audit (auditability is a core product promise). Coefficients are data; structure is
reviewed, tested code with one owner.

**Refactor guarantee (#005, workstream 1e):** the typed-config layer must expose every coefficient
above with zero hardcoded constants remaining in the economics path, and the scattered formula
copies (seller.py / seed.py / cogs.py / multichannel.py) collapse into the single `domain/`
source so there is exactly one definition of each identity. Until that lands, this doc lists where
each formula currently lives.
