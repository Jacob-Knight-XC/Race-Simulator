#!/usr/bin/env python3
"""Backfill geocode / elevation / weather for Meets rows."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scraper"))

from tfrrs.enrichment import enrich_meet_row  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        default=str(ROOT / "app" / "racedata.db"),
        help="Path to racedata.db",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional max meets to enrich (0 = all needing data)",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
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
    if args.limit:
        rows = rows[: args.limit]

    print(f"Enriching {len(rows)} meet(s)…")
    for row in rows:
        data = dict(row)
        enrich_meet_row(data)
        conn.execute(
            """
            UPDATE Meets SET
                venue_name=?, city=?, state=?, lat=?, lon=?,
                elevation_m=?, temp_c=?, precip_mm=?, weather_source=?
            WHERE meet_id=?
            """,
            (
                data.get("venue_name"),
                data.get("city"),
                data.get("state"),
                data.get("lat"),
                data.get("lon"),
                data.get("elevation_m"),
                data.get("temp_c"),
                data.get("precip_mm"),
                data.get("weather_source"),
                data.get("meet_id"),
            ),
        )
        conn.commit()
        loc = ", ".join(
            p for p in (data.get("city"), data.get("state")) if p
        ) or "unknown"
        print(
            f"  {data.get('meet_id')} {data.get('meet_name')} @ {loc} "
            f"elev={data.get('elevation_m')} precip={data.get('precip_mm')}"
        )
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
