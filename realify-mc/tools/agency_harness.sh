#!/usr/bin/env bash
# Docker-free stand-in for the docker-compose postgres:16 + pgbouncer harness (agency-plan §1c-2).
# Spins up an EPHEMERAL PostgreSQL 16 cluster (its own data dir + port, so it never touches the
# developer's default cluster) behind PgBouncer in TRANSACTION pooling mode — the mode P1's RLS design
# needs (transaction-local `SET LOCAL app.brand_ids`, pooler-safe). CI still uses docker-compose (see
# docker-compose.agency.yml); this is the local equivalent when Docker is unavailable.
#
# Usage: tools/agency_harness.sh {up|down|status|psql}
# Roles: realify_owner (owns tables, runs migrations) and realify_app (NOSUPERUSER, NOBYPASSRLS —
#        RLS FORCE applies to it). Both use password 'realify' (local only).
set -euo pipefail

PGBIN="${PGBIN:-/opt/homebrew/opt/postgresql@16/bin}"
PGBOUNCER="${PGBOUNCER:-$(command -v pgbouncer)}"
STATE="${AGENCY_HARNESS_DIR:-$HOME/.realify-agency-harness}"
PGDATA="$STATE/pgdata"
PGPORT="${AGENCY_PGPORT:-5433}"
PGBPORT="${AGENCY_PGBPORT:-6432}"
DBNAME="realify_agency"
LOGDIR="$STATE/log"
export LC_ALL=C   # homebrew PG refuses to start "multithreaded during startup" without a fixed locale

mkdir -p "$STATE" "$LOGDIR"

up() {
  if [ ! -f "$PGDATA/PG_VERSION" ]; then
    # UTF8 (like docker postgres:16 / RDS) with C locale (avoids homebrew's multithreaded-startup bug).
    # Without --encoding=UTF8 a C-locale initdb yields SQL_ASCII, and psycopg returns bytes for text.
    "$PGBIN/initdb" -D "$PGDATA" -U realify_owner --auth=trust --encoding=UTF8 --locale=C >/dev/null
    echo "unix_socket_directories = '$STATE'" >> "$PGDATA/postgresql.conf"
    echo "port = $PGPORT" >> "$PGDATA/postgresql.conf"
  fi
  if ! "$PGBIN/pg_ctl" -D "$PGDATA" status >/dev/null 2>&1; then
    "$PGBIN/pg_ctl" -D "$PGDATA" -l "$LOGDIR/pg.log" -o "-p $PGPORT" -w start >/dev/null
  fi
  # roles + db (idempotent)
  "$PGBIN/psql" -h "$STATE" -p "$PGPORT" -U realify_owner -d postgres -v ON_ERROR_STOP=1 -q <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='realify_app') THEN
    CREATE ROLE realify_app LOGIN PASSWORD 'realify' NOSUPERUSER NOCREATEDB NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='realify_owner' AND rolcanlogin) THEN
    ALTER ROLE realify_owner LOGIN PASSWORD 'realify';
  END IF;
END \$\$;
SQL
  "$PGBIN/psql" -h "$STATE" -p "$PGPORT" -U realify_owner -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='$DBNAME'" | grep -q 1 \
    || "$PGBIN/createdb" -h "$STATE" -p "$PGPORT" -U realify_owner "$DBNAME"

  # pgbouncer: transaction pooling, trust (client password ignored; PG hba is trust)
  cat > "$STATE/pgbouncer.ini" <<INI
[databases]
$DBNAME = host=$STATE port=$PGPORT dbname=$DBNAME
[pgbouncer]
listen_addr = 127.0.0.1
listen_port = $PGBPORT
unix_socket_dir = $STATE
auth_type = trust
auth_file = $STATE/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 20
logfile = $LOGDIR/pgbouncer.log
pidfile = $STATE/pgbouncer.pid
INI
  printf '"realify_app" "realify"\n"realify_owner" "realify"\n' > "$STATE/userlist.txt"
  if [ ! -f "$STATE/pgbouncer.pid" ] || ! kill -0 "$(cat "$STATE/pgbouncer.pid")" 2>/dev/null; then
    "$PGBOUNCER" -d "$STATE/pgbouncer.ini" >/dev/null 2>&1
    sleep 1
  fi
  echo "harness up:"
  echo "  direct (owner):  postgresql+psycopg://realify_owner:realify@127.0.0.1:$PGPORT/$DBNAME"
  echo "  pooler (app):    postgresql+psycopg://realify_app:realify@127.0.0.1:$PGBPORT/$DBNAME"
}

down() {
  [ -f "$STATE/pgbouncer.pid" ] && kill "$(cat "$STATE/pgbouncer.pid")" 2>/dev/null || true
  rm -f "$STATE/pgbouncer.pid"
  "$PGBIN/pg_ctl" -D "$PGDATA" -w stop >/dev/null 2>&1 || true
  echo "harness down"
}

status() {
  "$PGBIN/pg_ctl" -D "$PGDATA" status 2>&1 | head -1 || true
  if [ -f "$STATE/pgbouncer.pid" ] && kill -0 "$(cat "$STATE/pgbouncer.pid")" 2>/dev/null; then
    echo "pgbouncer: running (pid $(cat "$STATE/pgbouncer.pid"), port $PGBPORT, transaction mode)"
  else
    echo "pgbouncer: stopped"
  fi
}

case "${1:-up}" in
  up) up ;;
  down) down ;;
  status) status ;;
  psql) shift; "$PGBIN/psql" -h 127.0.0.1 -p "$PGBPORT" -U realify_app -d "$DBNAME" "$@" ;;
  *) echo "usage: $0 {up|down|status|psql}" >&2; exit 2 ;;
esac
