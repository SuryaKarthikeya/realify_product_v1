PY ?= python3

.PHONY: test doctor smoke-pg serve init harness-up harness-down test-agency verify-p1 verify-p2 verify-p3 verify-p4 verify-p5 verify-p6 verify-p7

# Fast hermetic unit suite on SQLite.
test:
	$(PY) -m pytest tests/ -q

# Preflight: validate DB config + connection + admin key for the CURRENT environment.
doctor:
	$(PY) run.py doctor

# One-command Postgres smoke: spin up a throwaway Postgres in Docker, run the full
# suite against it, tear it down. Requires Docker. Run this before deploying any DB change.
smoke-pg:
	$(PY) run.py doctor --postgres

# Local dev server (SQLite). Run `make init` first if you have no database yet.
serve:
	$(PY) run.py serve

init:
	$(PY) run.py init

# ---- agency console (Postgres-only) test harness — agency-plan §1c-2 ----
# Local Docker-free Postgres 16 + PgBouncer (transaction pooling). CI uses docker-compose.agency.yml.
harness-up:
	./tools/agency_harness.sh up

harness-down:
	./tools/agency_harness.sh down

# R7 Part 0: retire verification/test agencies from the fleet (reversible). Acts on DATABASE_URL (PG).
sweep-verify:
	$(PY) -c "from realify.agency import db as adb, sweep; c=adb.agency_connect(); cur=c.cursor(); print(sweep.sweep(cur)); c.commit()"

# R7 Part 0b: reap VERIFY-* agencies older than 7 days (run from cron or by hand). Reversible flag only.
reap-verify:
	$(PY) -c "from realify.agency import db as adb, sweep; c=adb.agency_connect(); cur=c.cursor(); print('reaped', sweep.reap_verify(cur)); c.commit()"

# Agency suite through the pooler. REQUIRED gate in every verify-pN (alongside `test`).
test-agency: harness-up
	AGENCY_DATABASE_URL="postgresql+psycopg://realify_owner:realify@127.0.0.1:5433/realify_agency" \
	AGENCY_POOLER_URL="postgresql+psycopg://realify_app:realify@127.0.0.1:6432/realify_agency" \
	$(PY) -m pytest tests/agency -q

# Phase-1 verifier: runs the existing SQLite suite + the agency suite and prints the AUDIT_BLOCK.
verify-p1: harness-up
	$(PY) -m tools.verify p1

# Phase-2 verifier (agency funnel). Set P2_INTERNAL_TOTAL / P2_REVENUE_ACCOUNTS from prod for the
# full block.
verify-p2: harness-up
	$(PY) -m tools.verify p2

# Phase-3 verifier (brand consent, connections, CSV ingest).
verify-p3: harness-up
	$(PY) -m tools.verify p3

# Phase-4 verifier (portfolio console & work queue).
verify-p4: harness-up
	$(PY) -m tools.verify p4

# Phase-5 verifier (approvals & execution write path).
verify-p5: harness-up
	$(PY) -m tools.verify p5

# Phase-6 verifier (reporting, billing, pilot conversion).
verify-p6: harness-up
	$(PY) -m tools.verify p6

# Phase-7 verifier (internal admin, quality, sandbox, superlogin — FINAL).
verify-p7: harness-up
	$(PY) -m tools.verify p7
