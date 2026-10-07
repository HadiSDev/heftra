#!/usr/bin/env bash
# Build the hosted demo's database dump: only the fictional Nordlys Byg A/S, never dev data.
#
# Usage:
#   scripts/build-demo-db.sh                      # writes deploy/demo/postgres/demo.sql.gz
#   scripts/build-demo-db.sh --factors-from NAME  # container holding an imported emission factor set
#
# It starts a throwaway PostgreSQL, applies the migrations, copies the emission factor sets and
# price indices (public reference data) from the dev database, creates the demo organization and a
# placeholder user, runs the demo-company seed against it, and dumps the result.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/deploy/demo/postgres/demo.sql.gz"
FACTORS_FROM="heftra-postgres-1"
FACTORS_DB="heftra"
SCRATCH="heftra-demo-build"
PORT=55432
ORG_ID="35156cc7-fb21-4b93-9b06-9fb0356e8457"

usage() {
  sed -n '2,10p' "$0"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --factors-from)
      FACTORS_FROM="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

cleanup() {
  docker rm -f "$SCRATCH" >/dev/null 2>&1 || true
}
trap cleanup EXIT

scratch_psql() {
  docker exec -i "$SCRATCH" psql -X -q -v ON_ERROR_STOP=1 -U demo -d demo "$@"
}

echo "Starting a throwaway PostgreSQL on port $PORT…"
cleanup
docker run -d --name "$SCRATCH" -p "127.0.0.1:$PORT:5432" \
  -e POSTGRES_DB=demo -e POSTGRES_USER=demo -e POSTGRES_PASSWORD=demo postgres:16 >/dev/null
until docker exec "$SCRATCH" pg_isready -U demo -d demo >/dev/null 2>&1; do
  sleep 1
done
sleep 2

export DATABASE_URL="postgresql://demo:demo@127.0.0.1:$PORT/demo"
export S3_ENDPOINT_URL=""
export S3_ACCESS_KEY=""
export S3_SECRET_KEY=""

echo "Applying migrations…"
(cd "$ROOT/apps/web-api" && uv run alembic upgrade head)

echo "Copying the emission factor set from $FACTORS_FROM…"
docker exec "$FACTORS_FROM" pg_dump -U "$FACTORS_DB" -d "$FACTORS_DB" --data-only --no-owner \
  -t emission_factor_sets -t emission_sectors -t emission_factors -t emission_country_regions \
  -t price_index_values \
  | scratch_psql

echo "Creating the demo organization…"
scratch_psql <<SQL
insert into organizations (id, name, slug, status)
values ('$ORG_ID', 'Nordlys Byg', 'nordlys-byg', 'active');
insert into users (id, organization_id, email, name, role, is_system_admin)
values ('demo-seed-user', '$ORG_ID', 'seed@heftra.invalid', 'Demo seed', 'admin', false);
SQL

echo "Seeding Nordlys Byg A/S…"
(cd "$ROOT" && uv run python apps/ai-api/scripts/demo_company)

echo "Writing $OUT…"
mkdir -p "$(dirname "$OUT")"
docker exec "$SCRATCH" pg_dump -U demo -d demo --no-owner --no-privileges | gzip -9 > "$OUT"
ls -lh "$OUT"
