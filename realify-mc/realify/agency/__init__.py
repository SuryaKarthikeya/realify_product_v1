"""Agency console (the multi-tenant overlay — agency-plan Phase 1+).

New concepts (agencies, engagements, envelopes, grants, ledger, PDP) live here as ADDITIVE modules
that reference the existing `users`/`tenants` tables; nothing here renames or repurposes existing
schema. Agency data tables are Postgres-only (§1c two-track DB policy); this package's P0.5 pieces
(the sandbox canary seed) run on the existing tenants model and therefore work on SQLite too.
"""
