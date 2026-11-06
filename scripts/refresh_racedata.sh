#!/usr/bin/env bash
# Full TFRRS refresh for one college division into its dedicated SQLite DB.
# Usage:
#   ./scripts/refresh_racedata.sh            # NCAA DIII → app/racedata.db
#   ./scripts/refresh_racedata.sh naia       # NAIA → app/racedata-naia.db
#   DIVISION=naia ./scripts/refresh_racedata.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIVISION="${1:-${DIVISION:-d3}}"

eval "$(
  python3 - <<PY
import sys
sys.path.insert(0, "$ROOT/app")
from divisions import get_division, normalize_division_key
key = normalize_division_key("$DIVISION")
div = get_division(key)
print(f"DIV_KEY={key!r}")
print(f"DB_FILE={str(div.db_path)!r}")
print(f"DIV_LABEL={div.label!r}")
print(f"LEAGUE_ID={div.tfrrs_league_id}")
PY
)"

cd "$ROOT/scraper"

echo "Scraping TFRRS $DIV_LABEL (league $LEAGUE_ID) into $DB_FILE…"
scrapy crawl xc \
  -a "division=$DIV_KEY" \
  -s "RACE_DB_PATH=$DB_FILE" \
  -s ENRICH_MEETS=True \
  -s ENRICH_WORKERS="${ENRICH_WORKERS:-6}" \
  -s AUTOTHROTTLE_TARGET_CONCURRENCY="${AUTOTHROTTLE_TARGET_CONCURRENCY:-4}" \
  -s CONCURRENT_REQUESTS="${CONCURRENT_REQUESTS:-16}" \
  -s DOWNLOAD_DELAY="${DOWNLOAD_DELAY:-0}" \
  -s AUTOTHROTTLE_START_DELAY="${AUTOTHROTTLE_START_DELAY:-0.5}"

echo "Repairing meet geo/weather + race meet_ids…"
python3 "$ROOT/scripts/repair_meet_geo_weather.py" --db "$DB_FILE" --workers "${ENRICH_WORKERS:-6}"

echo "Done. DB: $DB_FILE"
