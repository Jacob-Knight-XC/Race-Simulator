#!/usr/bin/env python3
"""
Repair Meets geocodes / weather and backfill Races.meet_id.

- Clears overseas geocode misses (e.g. 38.67,29.41 Turkey)
- Re-enriches city/state/lat/lon/elevation/weather
- Links Races rows to Meets by normalized name + date when meet_id is missing
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scraper"))

from race_db import RaceDB  # noqa: E402
from tfrrs.enrichment import (  # noqa: E402
    coords_plausible_us,
    enrich_meet_rows,
)


def clear_bad_coords(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT meet_id, lat, lon FROM Meets WHERE lat IS NOT NULL"
    ).fetchall()
    cleared = 0
    for meet_id, lat, lon in rows:
        if coords_plausible_us(lat, lon):
            continue
        conn.execute(
            """
            UPDATE Meets
            SET lat=NULL, lon=NULL, elevation_m=NULL,
                temp_c=NULL, precip_mm=NULL, weather_source=NULL
            WHERE meet_id=?
            """,
            (meet_id,),
        )
        cleared += 1
    conn.commit()
    return cleared


def backfill_race_meet_ids(conn: sqlite3.Connection, db: RaceDB) -> int:
    lookup = db._meet_id_lookup()
    rows = conn.execute(
        """
        SELECT rowid, meet_name, meet_date, meet_id
        FROM Races
        WHERE meet_id IS NULL OR meet_id = ''
        """
    ).fetchall()
    updated = 0
    for rowid, meet_name, meet_date, _meet_id in rows:
        date_key = db._date_key(meet_date)
        if not meet_name or not date_key:
            continue
        resolved = lookup.get((db.normalize_meet_key(meet_name), date_key)) or lookup.get(
            (meet_name.strip(), date_key)
        )
        if not resolved:
            continue
        conn.execute("UPDATE Races SET meet_id=? WHERE rowid=?", (resolved, rowid))
        updated += 1
    conn.commit()
    return updated


def reenrich_meets(conn: sqlite3.Connection, workers: int = 6, limit: int = 0) -> int:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT meet_id, meet_name, meet_date, location_text, venue_name,
               city, state, lat, lon, elevation_m, temp_c, precip_mm,
               weather_source
        FROM Meets
        WHERE lat IS NULL OR lon IS NULL OR temp_c IS NULL OR precip_mm IS NULL
        ORDER BY meet_date DESC
        """
    ).fetchall()
    pending = [dict(row) for row in rows]
    if limit:
        pending = pending[:limit]
    if not pending:
        return 0

    def _progress(done: int, total: int) -> None:
        print(f"  enrich {done}/{total}", flush=True)

    enriched = enrich_meet_rows(pending, workers=workers, on_progress=_progress)
    for row in enriched:
        conn.execute(
            """
            UPDATE Meets SET
                venue_name=?, city=?, state=?, lat=?, lon=?,
                elevation_m=?, temp_c=?, precip_mm=?, weather_source=?
            WHERE meet_id=?
            """,
            (
                row.get("venue_name"),
                row.get("city"),
                row.get("state"),
                row.get("lat"),
                row.get("lon"),
                row.get("elevation_m"),
                row.get("temp_c"),
                row.get("precip_mm"),
                row.get("weather_source"),
                row.get("meet_id"),
            ),
        )
    conn.commit()
    return len(enriched)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(ROOT / "app" / "racedata.db"))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0, help="Max meets to re-enrich")
    parser.add_argument(
        "--skip-enrich",
        action="store_true",
        help="Only clear bad coords + backfill meet_ids",
    )
    args = parser.parse_args()

    db = RaceDB(args.db)
    conn = sqlite3.connect(args.db)
    cleared = clear_bad_coords(conn)
    print(f"Cleared overseas/bogus coordinates on {cleared} meet(s)")
    # Rebuild lookup after any meet edits.
    db._meet_id_by_name_date = None
    db._meet_meta_cache = None
    updated = backfill_race_meet_ids(conn, db)
    print(f"Backfilled meet_id on {updated} race row(s)")
    if not args.skip_enrich:
        print("Re-enriching meets needing geo/weather…")
        n = reenrich_meets(conn, workers=args.workers, limit=args.limit)
        print(f"Updated {n} meet row(s)")
    # Summary
    print(
        "meets with lat",
        conn.execute("SELECT COUNT(*) FROM Meets WHERE lat IS NOT NULL").fetchone()[0],
    )
    print(
        "meets with temp",
        conn.execute("SELECT COUNT(*) FROM Meets WHERE temp_c IS NOT NULL").fetchone()[0],
    )
    print(
        "races with meet_id",
        conn.execute(
            "SELECT COUNT(*) FROM Races WHERE meet_id IS NOT NULL AND meet_id != ''"
        ).fetchone()[0],
    )
    overseas = conn.execute(
        """
        SELECT COUNT(*) FROM Meets
        WHERE lat IS NOT NULL AND NOT (lat BETWEEN 18 AND 72 AND lon BETWEEN -170 AND -65)
        """
    ).fetchone()[0]
    print("meets still outside US box", overseas)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
