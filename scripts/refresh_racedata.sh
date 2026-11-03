#!/usr/bin/env bash
# Full TFRRS refresh into app/racedata.db (used by weekly automation).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/scraper"

echo "Scraping TFRRS DIII into app/racedata.db…"
scrapy crawl xc -s ENRICH_MEETS=True

echo "Done. DB: $ROOT/app/racedata.db"
