# Extending Realify — Contributor Guide

**Status:** Draft / target structure. The *principles and rules* below are binding from day one; the *concrete interface signatures* are filled in as #005 Phase 1 builds each interface. If a signature here says `TBD (Phase 1)`, the interface isn't frozen yet — check the code or ask the platform owner.

This guide is for engineers (including other teams) adding a **component** to Realify — a marketplace connector, an auth provider, a billing provider, or a detector — **without editing core**.

---

## The one rule that matters most

> You build **against an interface**, register your component, and run its **contract test**. You never edit core, never touch the database directly, and never choose the tenant — the platform injects an already-tenant-scoped context. If you find yourself editing a file in `domain/`, `repositories/`, or `db/` to add your component, stop: you're doing it wrong, or the interface is missing something — raise it.

---

## Architecture in one picture

```
api/          thin HTTP routers — no business logic, no SQL
  ↓ calls
services/     use-case orchestration
  ↓ calls
domain/       pure logic: detectors, rules, math   (NO I/O, NO SQL, NO HTTP)
  ↓ via
repositories/ the ONLY place that talks to the DB  (sets tenant context, enforces RLS)
  ↓
db/ + models/ engine, migrations (Alembic), table defs

connectors/   ChannelConnector plugins      ← you may add here
auth/         AuthProvider plugins          ← you may add here
billing/      BillingProvider plugins       ← you may add here
domain/detectors/ Detector plugins          ← you may add here
tasks/        TaskRunner (background/Temporal) — components SUBMIT work here
config/       typed settings (pydantic) — all config + secret access
```

**Dependency direction:** your component depends on core's interfaces; core never depends on your component. You build *outward*.

---

## The golden rules (non-negotiable)

1. **Never edit core to add a component.** Implement an interface + register. If you can't, the interface is incomplete — raise it, don't work around it.
2. **Never touch the DB directly.** Go through a repository, or return domain objects and let a service persist them. Direct SQL bypasses Row-Level Security and risks a **cross-tenant data leak**.
3. **Never choose the tenant.** You receive a tenant-scoped context/session. Don't read `tenant_id` from user input and query by it yourself.
4. **No hardcoded values.** Endpoints, limits, rate limits, feature flags → typed config. Secrets → the secrets interface. **Never log tokens, keys, or PII.**
5. **Translate to the canonical model at your boundary.** Your vendor's shape stays inside your component; what crosses into core is canonical domain types (the `internal_sku` spine and friends).
6. **Ship passing contract tests.** A component without its contract test green does not merge.
7. **One job per file; respect the file-length cap** (enforced in CI lint). Module docstring stating purpose.

---

## Extension points

| Interface | Add one when you want to… | Reference impl to copy |
|---|---|---|
| `ChannelConnector` | integrate a marketplace/data source (Amazon SP-API, Shopify, Walmart, ad platforms) | report-ingestion (the first connector) |
| `AuthProvider` | add a sign-in method (Google OAuth, SSO, …) | `LocalPassword` |
| `BillingProvider` | add a payments/subscription backend (Stripe, Razorpay, …) | TBD (Phase 1 / #006) |
| `Detector` | add a new insight/signal (e.g. CMAA) | existing margin/inventory detectors |
| `TaskRunner` | (platform-level) change how background work runs (background → Temporal) | background impl |

---

## Recipe: add a `ChannelConnector`

> Interface signature: `TBD (Phase 1)` — `authenticate()`, `fetch_reports(kind, window)`, `normalize() -> canonical`, `write_back(action)`.

1. Create `connectors/<name>/` with your implementation of `ChannelConnector`.
2. Declare your config schema (pydantic) in the component; read secrets via the secrets interface. Nothing hardcoded.
3. Map vendor → canonical in `normalize()`. Use the shared **ASIN↔SKU identity service** — don't reinvent identity resolution.
4. Register the connector (registry/entry-point — mechanism `TBD (Phase 1)`).
5. Long/slow/rate-limited work (auth refresh, paginated pulls) → submit via `TaskRunner` (durable + retryable), don't block a request.
6. Run the connector **contract test kit** (`TBD (Phase 1)`): asserts `normalize()` output validates against the canonical schema and that you never call the DB directly.
7. Add a row to the connector docs + an ADR if you made a notable design choice.

## Recipe: add an `AuthProvider`

> Identity model: a `user_identities` row (user_id, provider, provider_subject, email_verified) separates *identity* from *user*. Sign-in routes through the existing create-org-vs-join-via-invite gate.

1. Implement `AuthProvider` in `auth/<provider>/`.
2. Implement the OAuth callback with **state + PKCE**. Account-linking: link to an existing user **only on a verified matching email** (else account-takeover risk).
3. Secrets (client id/secret) via the secrets interface. Never in `.env`-in-repo, never logged.
4. Register the provider. Run the auth contract test (`TBD (Phase 1)`).
5. Coordinate with the platform owner on session issuance — that's core, not your component.

## Recipe: add a `BillingProvider`

> Entitlements (what a tenant may see) live in `domain/` and are separate from billing (who paid). Your provider updates entitlement state **via webhooks**, the source of truth.

1. Implement `BillingProvider` in `billing/<provider>/` (checkout/session, customer portal, webhook handler).
2. **Webhooks are truth**, not the post-checkout redirect. Verify signatures. Make every handler **idempotent** (dedupe on the provider's event id via `billing_events`).
3. Billing attaches to the **tenant/org**, not the user.
4. Secrets (API keys, webhook secret) via the secrets interface.
5. Run the billing contract test (`TBD (Phase 1)`).

## Recipe: add a `Detector`

> Detectors are **pure** (`domain/detectors/`): inputs in, findings out. No I/O, no SQL, no HTTP. NULL-safe — missing inputs produce no finding (graceful degradation via `_cmp`).

1. Implement the `Detector` interface; keep thresholds as **rules-as-data / config**, not literals.
2. Declare required inputs (which reports/fields). The completeness panel reads this to tell users what unlocks your detector.
3. Separate **certain vs. estimated** outputs (never let them be summed).
4. Register the detector. Add unit tests (pure logic = easy to test) + the detector contract test.

---

## Tenant isolation (read this twice)

Isolation is a **database guarantee** (Postgres RLS), not your responsibility to remember — *as long as you obey rule #2 and #3*. The repository layer sets `app.tenant_id` per transaction and resets it on connection return. If you bypass the repository (raw SQL, your own connection), you defeat RLS. **Don't.** Any code path touching tenant data gets a security review before real customer data.

## Config & secrets

- Config: add typed fields to the config module; read them; never hardcode. Document any new env var.
- Secrets: request via the secrets interface (backed by AWS Secrets Manager / SSM in prod). Never commit, never log.

## Interface versioning

- Interfaces are **versioned**; breaking changes are announced via the interface CHANGELOG and an ADR.
- If you need a change to a core interface, open an ADR proposal — don't fork the interface.

## PR checklist for a new component

- [ ] Implements the interface; **core unchanged**
- [ ] Registered via the registry (no central switch edited)
- [ ] No direct DB access; tenant context not hand-chosen
- [ ] No hardcoded config/secrets; nothing sensitive logged
- [ ] Translates to/from canonical types at the boundary
- [ ] Contract test kit green; unit tests added
- [ ] File-length cap respected; module docstring present
- [ ] Docs row + ADR (if a notable decision) added

---

*This guide and the interfaces it documents are owned by the platform team. When in doubt, ask before working around a constraint — the constraints are mostly there to prevent cross-tenant data leaks and un-maintainable forks.*
