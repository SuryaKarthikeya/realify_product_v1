# Verification-tenant convention (R7 Part 0b)

Phases kept polluting the fleet (`/ops/agency/admin`) with verification artifacts — "Live Verify",
"R3 Feeder Verify", per-click "Sandbox Agency" singletons. To stop the accumulation:

## Rule

Every verification tenant/agency created from R7 onward **must**:

1. Be **named `VERIFY-*`** (e.g. `VERIFY-r7-queue`), and
2. Have its brand tenants set **`tenant_kind='internal'`**.

Internal/sandbox agencies are excluded from the default fleet view and from the billable/revenue
counters (both are query-time, retroactive). `agencies.internal` (migration 0033) is the reversible
retirement flag — set it, don't hard-delete.

## Retire existing cruft (Part 0a — reversible)

```
make sweep-verify      # flags Live/Feeder/VERIFY-*/legacy Sandbox agencies internal=true; prints counts
```
Backed by `realify.agency.sweep.sweep(cur)`. Reverse a single agency with `sweep.unretire(cur, id)`.

## Reaper (retire stale VERIFY-* automatically)

```
make reap-verify       # retires VERIFY-* agencies whose rows are older than 7 days (default)
```
Backed by `realify.agency.sweep.reap_verify(cur, older_than_days=7)`. Run it from cron / a scheduled
job, or by hand after a phase. It only ever sets the reversible `internal` flag.

Both targets act on `DATABASE_URL` (prod = the RDS `realify_app` role; the flag update needs only DML,
which `realify_app` has). Neither deletes anything.
