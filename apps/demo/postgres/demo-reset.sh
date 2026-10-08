#!/usr/bin/env bash
# Keep the hosted demo's organization linked to Clerk, and restore its original data.
#
# Usage:
#   demo-reset link       # point the demo organization at DEMO_CLERK_ORG_ID
#   demo-reset reset-now  # restore the original data once
#   demo-reset schedule   # restore it every day at DEMO_RESET_AT (default 03:00, in TZ)
#
# Connects with the standard PGHOST, PGUSER and PGPASSWORD variables.
set -euo pipefail

LIVE=heftra
NEXT=heftra_next
PREVIOUS=heftra_previous
DUMP=/docker-entrypoint-initdb.d/10-demo.sql.gz
DEMO_ORG_ID=35156cc7-fb21-4b93-9b06-9fb0356e8457
RESET_AT="${DEMO_RESET_AT:-03:00}"

log() {
  echo "[demo-reset] $(date '+%Y-%m-%d %H:%M:%S %Z') $*"
}

run_sql() {
  local database="$1"
  shift
  psql -X -q -v ON_ERROR_STOP=1 -d "$database" "$@"
}

link_org() {
  local database="$1"
  run_sql "$database" -v clerk_org="${DEMO_CLERK_ORG_ID:?set DEMO_CLERK_ORG_ID}" \
    -v org="$DEMO_ORG_ID" <<'SQL'
update organizations set clerk_org_id = :'clerk_org' where id = :'org';
SQL
}

schema_version() {
  run_sql "$1" -tAc "select version_num from alembic_version"
}

load_next() {
  log "loading the original data into $NEXT"
  run_sql postgres -c "drop database if exists $NEXT with (force)"
  run_sql postgres -c "drop database if exists $PREVIOUS with (force)"
  run_sql postgres -c "create database $NEXT"
  gunzip -c "$DUMP" | run_sql "$NEXT" >/dev/null
  link_org "$NEXT"
  pg_dump --data-only --table=public.erp_credentials "$LIVE" | run_sql "$NEXT" >/dev/null
}

same_schema() {
  local live next
  live="$(schema_version "$LIVE")"
  next="$(schema_version "$NEXT")"
  if [[ "$live" == "$next" ]]; then
    return 0
  fi
  log "not resetting: the dump is at schema $next but the live database is at $live; rebuild the dump"
  return 1
}

swap_in_next() {
  log "swapping $NEXT in for $LIVE"
  run_sql postgres <<SQL
alter database $LIVE with allow_connections false;
select pg_terminate_backend(pid) from pg_stat_activity
  where datname = '$LIVE' and pid <> pg_backend_pid();
alter database $LIVE rename to $PREVIOUS;
alter database $NEXT rename to $LIVE;
SQL
  run_sql postgres -c "drop database $PREVIOUS with (force)"
}

reset_now() {
  load_next
  if ! same_schema; then
    run_sql postgres -c "drop database $NEXT with (force)"
    exit 1
  fi
  swap_in_next
  log "the demo has its original data again"
}

seconds_until_next_reset() {
  local now next
  now="$(date +%s)"
  next="$(date -d "today $RESET_AT" +%s)"
  if (( next <= now )); then
    next="$(date -d "tomorrow $RESET_AT" +%s)"
  fi
  echo $(( next - now ))
}

schedule() {
  log "resetting every day at $RESET_AT"
  while true; do
    sleep "$(seconds_until_next_reset)"
    if ! "$0" reset-now; then
      log "the reset did not complete; see the messages above"
    fi
  done
}

case "${1:-}" in
  link)
    link_org "$LIVE"
    log "the demo organization is linked to $DEMO_CLERK_ORG_ID"
    ;;
  reset-now)
    reset_now
    ;;
  schedule)
    schedule
    ;;
  *)
    sed -n '4,7p' "$0" >&2
    exit 2
    ;;
esac
