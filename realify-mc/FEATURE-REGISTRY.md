# Feature / Version Registry — standard convention

**Every new feature or UI version ships DARK behind the registry and is turned on / rolled back from the
Ops page (`/ops` → "Rollout"). No redeploy to flip; nothing a user sees changes until Ops turns it on.**

This is the standing convention for all new development. It exists so we can (a) keep a catalog of what
we've shipped, (b) choose which version runs, and (c) roll back instantly — all Ops-driven, and
backward-compatible by design.

## The two flag kinds (`realify/flags.py`)
- **Version feature** — coexisting versions of a surface (e.g. `app_ui`: `legacy` (baseline) vs `v4`).
  One version is the **baseline** (always safe). Ops picks the **selected** build + a **scope**.
- **Gate feature** — a capability that may *act* (e.g. `ask`, `agents`). `on`/`off`, default **off**.
  Independent of version: hiding a surface never runs it; showing one never forces it to act.

## Resolution (read per request → instant flip)
`active_version(key, request, tenant_id)` = **query pin** (`?<key>=<ver>`, `?skin=` alias for `app_ui`)
→ **tenant pin** → **(scope `on` ? selected : baseline)**. Default baseline.
`feature_enabled(key, tenant_id)` = per-tenant gate → global gate. Default off.
State lives in `tenant_settings` (system pseudo-tenant `0` for globals — the table has no FK, so id 0 is
safe on SQLite and Postgres) + per-tenant rows.

## Ops controls (`/ops` → Rollout card)
- **Build** buttons — pick the selected version. **Rollback** = pick a previous version.
- **Scope** — `off` (baseline for all) · `internal` (baseline default, opt-in via `?skin=`/per-tenant) ·
  `on` (selected for all). Rollback = scope `off`.
- **Gate** — enable/disable a capability.
Backed by `GET/POST /api/admin/rollout` (admin-key gated).

## Adding a feature (the recipe)
1. Add an entry to `FEATURES` in `flags.py` (version list, or `kind:"gate"`).
2. Build the new code behind the resolver: `if flags.active_version("X", request, tid) == "v2": …`
   (UI) or `if flags.feature_enabled("X", tid): …` (behavior). Keep the baseline path untouched.
3. Ship it **additive** (see rules). It's dark by default → deploy is a no-op.
4. Turn it on from Ops: dogfood (`?X=v2`) → scope `internal` → scope `on`. Roll back anytime from Ops.
5. When the old version's usage is zero, **sunset** it (remove the old code + version entry).

## Backward-compatibility rules (enforced)
- **Additive-only** to existing contracts: new endpoints, new tables, new **nullable** columns. Never
  rename / remove / repurpose an existing route, column, or response field in place.
- **Expand → contract** for behavior changes: add the new path alongside the old, dual-run behind the
  flag, migrate, then retire the old once usage is zero.
- **Versioned contracts**: keep frozen paths frozen (e.g. `/api/v1`). New shape = new version.
- **Parallel UI**: a new UI version is a new file/template served behind the version flag; the old file
  is not edited.
- **Ship dark**: default baseline/off; releasing ≠ deploying.

## Not free (the honest caveat)
Backward-compatibility-by-design is a discipline, not automatic: you carry coexisting versions until you
sunset the old one, and truly breaking changes still need an expand→contract migration (the pattern makes
them compatible *during* the transition, with instant rollback). Behavior (agents acting) is gated
separately from UI version, and a tenant on the baseline UI has its net-new agent execution paused.
