# Agency wiring census

Every agency domain capability, and whether a route/job/CLI (outside `tests/`) reaches it.
Status: **WIRED** · **ENGINE-ONLY-DECLARED** (a real capability kept intentionally un-triggered, with
rationale) · **ORPHANED** (reachable only from tests — a gap) · **ABSENT** (not built).

Updated: R3.

## Wired this release (R2/R3)
| capability | reachable-via |
|---|---|
| `execution.execute_bulk` / `execute_approval` / `undo_execution` | queue propose/bulk + `/api/agency/executions/{id}/undo` |
| `metering.record` · `toctou.check_at_execute` | via `execute_bulk` |
| `decisions.generate` · `rollups.compute` · `fx.lock_rate` | **`scheduler.run_feeders_once`** (R3) |
| `pilots.lapse_job` · `connections.health_run` · `approvals.expire_cosigns` · `gates.expire_gates` | `scheduler.run_agency_jobs_once` (gates wired R3) |
| `ingest.ingest_csv` / `detect_report_type` / `get_mapping` | `/api/agency/data-sources/{id}/ingest` (R3) |
| `approvals.create_deeplink` (issuance) · `resolve_deeplink` · `cosign` · `verify_otp_skip_token` | cosign email + mobile `decide` (R3) |
| `ops.revoke_engagement` · `ops.publish_envelope` (narrow) | brand portal revoke/narrow (R3) |
| `keyring.crypto_shred` · `ledger.verify_chain` | offboarding delete-certificate (R3) |
| `ledger` read (transparency) · consent flow · `queue.build` | brand portal / consent routes / console |

## Declare-or-wire decisions (R3 audit items)
| capability | status | rationale |
|---|---|---|
| `gates.expire_gates` | **WIRED** (R3) | Natural periodic job — added to `run_agency_jobs_once`. |
| `gates.set_auto` | **ENGINE-ONLY-DECLARED** | Ops primitive to (re)assert an auto gate; the admin gate UI (attest/fleet) is R4. No unsafe default — wire when the admin console gains a set-auto control. |
| `queue.fair_select` | **ENGINE-ONLY-DECLARED** | Least-recently-shown fairness weighting for books larger than top-K. The live queue uses deterministic $-rank; `fair_select` activates only once a book exceeds the top-K window (not yet true for pilot books). Kept tested so it's ready. |
| `connections.guard_decisions` | **ENGINE-ONLY-DECLARED** | The raise-on-paused variant. The feeder + queue use the non-raising `decisions_paused`/`compute_decisions_guarded` pattern (pause-not-guess) instead; `guard_decisions` is the exception-style alternative for callers that prefer it. |
| `internal.count_billable_tenants` / `count_revenue_accounts` | **ENGINE-ONLY-DECLARED** | Fleet/revenue counters for the internal admin overview (screens 25–26), whose rich UI is R4. Correct + tested; surfaced then. |

## Still ORPHANED — R4 scope (unchanged, left as-is per plan)
- `reports.generate` + factuality gate — no route generates reports yet.
- `billing_agency.build_invoice` / `allocate` / `reconciliation_delta` / `sync_customer` — no invoice trigger.
- `quality.mitigation` (ledgered gate-raise) — no route.
- ROI counterfactual (vs do-nothing) — **ABSENT** (not built).

## Notes
- `sandbox.*` engine is now no longer the ONLY feeder: real brands flow through `run_feeders_once`. The
  tester-hub controls remain inert (R1 note) — a separate follow-up.
- `ops.grant_role` / `create_engagement` are reached transitively via consent grant + provision; the
  standalone grant/break-glass/revoke admin surfaces beyond the brand portal remain R4/ops-tooling.

## R4 update
Newly WIRED: `reports.generate` + factuality gate (report route); `billing_agency.build_invoice`/
`allocate`/`reconciliation_delta` (billing page + `agency_jobs.run_billing_once`); `quality.mitigation`
(Review/Apply); `sandbox.*` engine (agency_sandbox routes + hub buttons); `gates.set_auto` (admin
control); `internal.fleet_rows`/`count_billable_tenants`/`count_revenue_accounts` (fleet page);
`rollups.roi_projected` (ROI v1, labeled projected).
ENGINE-ONLY-DECLARED: `billing_agency.sync_customer` (Stripe TEST-mode; not called by the DB-only
invoice job by design); `queue.fair_select`; `connections.guard_decisions`.
**Still ORPHANED after R4 — 2:** `ledger.read_payload` (no route decrypts brand payloads; crypto-shred
+ verify_chain are wired) · `ops.break_glass` (time-boxed elevation has no route; revoke is wired).
ABSENT: ROI *realized* reconciliation (v1 projected shipped; measured-vs-do-nothing is future work).
