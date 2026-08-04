# Deploy runbook — realify-mc (production EC2)

Production: **https://realifyai.app** · box `ubuntu@54.167.138.13` (key `~/.ssh/ShivasKeyPair.pem`) ·
app at `/home/ubuntu/realify-mc` (a git checkout of `origin/main`) · DB = **Postgres RDS** · runtime
role = **`realify_app`** (NOSUPERUSER, NOBYPASSRLS — so RLS FORCE binds).

## Golden rules

1. **NEVER `git reset --hard` on the box.** `.env` is now UNTRACKED (R10.1), but treat the box's
   working tree as sacred regardless. A hard reset (or `git clean -fdx`) can wipe the local `.env`
   that holds the prod secrets (`DATABASE_URL=realify_app…`, `MASTER_KEK`, `STRIPE_*`, admin keys). If
   `.env` is lost the app FAILS CLOSED (see below) rather than silently serving off empty SQLite — but
   you still have an outage. Use `git pull --ff-only` (or `git fetch` + `git checkout <paths>` for
   code-only updates).
2. **The prod `.env` lives ONLY on the box** (untracked / secrets manager). It is never committed, so
   `git pull` can never touch it. Keep a timestamped backup: `cp .env .env.bak-$(date +%Y%m%d-%H%M)`.
3. **Never run `pytest` on the box** — conftest recreates the schema per test and would wipe prod RDS.
4. **Commits must not stage `.env`/`*.db`** (both are gitignored as of R10.1; `.env.example` is the
   one tracked template).

## Fail-closed DB guard (R10.1)

In prod/agency mode (`AGENCY_CONSOLE=on`, or `REQUIRE_POSTGRES=1`) the app REFUSES to start unless
`DATABASE_URL` is a **reachable Postgres** — no silent SQLite fallback. If boot aborts with
`FATAL: prod/agency mode requires …Postgres…`, the `.env` is missing/blank or RDS is unreachable —
restore `.env` and retry; do NOT unset `AGENCY_CONSOLE` to "fix" it in prod.

## Safe redeploy sequence

```bash
# 0. locally: tests green, commit, tag, push
python3 -m pytest tests/ -q --ignore=tests/agency        # SQLite suite
AGENCY_DATABASE_URL=… AGENCY_POOLER_URL=… python3 -m pytest tests/agency -q
git push origin main && git push origin <tag>

# 1. on the box: fast-forward ONLY (never reset --hard)
ssh -i ~/.ssh/ShivasKeyPair.pem ubuntu@54.167.138.13
cd ~/realify-mc
cp .env .env.bak-$(date +%Y%m%d-%H%M)                    # snapshot secrets first
git pull --ff-only origin main

# 2. stage rollback + rebuild image (COPY . . bakes code in — restart alone reuses the old image)
sudo docker tag realify-mc:latest realify-mc:rollback
sudo docker build -t realify-mc:latest .

# 3. NEW migration? apply as realify_admin FIRST (realify_app is non-owner, cannot DDL)
#    admin creds live in .env.bak-rolesplit
sudo docker run --rm --env-file .env.bak-rolesplit realify-mc:latest alembic upgrade head
sudo docker run --rm --env-file .env.bak-rolesplit realify-mc:latest alembic current   # confirm head

# 4. recreate the container (serves as realify_app via .env)
sudo docker stop realify && sudo docker rm realify
sudo docker run -d --name realify --restart unless-stopped \
  --env-file .env -v /data:/data -p 127.0.0.1:8001:8001 \
  realify-mc:latest sh -c "python3 run.py init && python3 run.py start"

# 5. verify — Postgres (NOT sqlite), health, superlogin renders without a URL key
sudo docker exec realify printenv DATABASE_URL | sed -E 's#://([^:]+):.*@#://\1:***@#'  # realify_app@RDS
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8001/                          # 200
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8001/superlogin                # 200, form (no ?key=)
```

Rollback: `sudo docker stop realify && sudo docker rm realify` then re-run step 4 with
`realify-mc:rollback`.

## Incident log

- **2026-07-15 (R9.1 deploy):** `git reset --hard origin/main` on the box reverted the tracked-but-
  locally-modified `.env` to the sanitized committed version → lost `DATABASE_URL`/secrets → app fell
  back to SQLite (agency routes 503/404). Recovered by restoring `.env` from `.env.bak-prelaunch-agency`
  and recreating. Fixed for good in R10.1: `.env` untracked + fail-closed DB guard + this runbook.
