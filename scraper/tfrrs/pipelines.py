import sqlite3
import time
from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from .enrichment import enrich_meet_row
from .items import AthleteItem, MeetItem, RaceItem, TeamItem


class TfrrsPipeline:
    """Persist scraped TFRRS teams, athletes, races, and meets to SQLite."""

    COMMIT_EVERY = 200

    def __init__(self, db_path: str, enrich_meets: bool = True):
        self.db_path = db_path
        self.enrich_meets = enrich_meets
        self.conn = None
        self.curr = None
        self._pending = 0

    @classmethod
    def from_crawler(cls, crawler):
        db_path = crawler.settings.get("RACE_DB_PATH", "racedata.db")
        enrich = crawler.settings.getbool("ENRICH_MEETS", True)
        return cls(db_path=db_path, enrich_meets=enrich)

    def open_spider(self, spider):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.curr = self.conn.cursor()
        self._create_tables()

    def close_spider(self, spider):
        if self.conn is None:
            return
        if self.enrich_meets:
            spider.logger.info("Enriching meets with geocode / weather…")
            self._enrich_pending_meets(spider)
        self.conn.commit()
        self.conn.close()

    def _create_tables(self):
        self.curr.executescript(
            """
            CREATE TABLE IF NOT EXISTS Teams(
                team_id TEXT PRIMARY KEY,
                team_name TEXT,
                gender TEXT
            );
            CREATE TABLE IF NOT EXISTS Athletes(
                athlete_id INTEGER PRIMARY KEY,
                ath_first TEXT,
                ath_last TEXT,
                team_id TEXT,
                FOREIGN KEY (team_id) REFERENCES Teams (team_id)
            );
            CREATE TABLE IF NOT EXISTS Races(
                athlete_id INTEGER,
                distance TEXT,
                race_time TEXT,
                meet_name TEXT,
                meet_date DATE,
                meet_id TEXT,
                CONSTRAINT unq UNIQUE(
                    athlete_id, distance, race_time, meet_name, meet_date
                )
            );
            CREATE TABLE IF NOT EXISTS Meets(
                meet_id TEXT PRIMARY KEY,
                meet_name TEXT,
                meet_date DATE,
                location_text TEXT,
                venue_name TEXT,
                city TEXT,
                state TEXT,
                lat REAL,
                lon REAL,
                elevation_m REAL,
                temp_c REAL,
                precip_mm REAL,
                weather_source TEXT
            );
            """
        )
        self._ensure_column("Races", "meet_id", "TEXT")
        for col, decl in [
            ("location_text", "TEXT"),
            ("venue_name", "TEXT"),
            ("city", "TEXT"),
            ("state", "TEXT"),
            ("lat", "REAL"),
            ("lon", "REAL"),
            ("elevation_m", "REAL"),
            ("temp_c", "REAL"),
            ("precip_mm", "REAL"),
            ("weather_source", "TEXT"),
        ]:
            self._ensure_column("Meets", col, decl)
        self.conn.commit()

    def _ensure_column(self, table: str, column: str, decl: str):
        existing = {
            row[1] for row in self.curr.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing:
            self.curr.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")

    def process_item(self, item, spider):
        if isinstance(item, TeamItem):
            self._store_team(item)
        elif isinstance(item, AthleteItem):
            self._store_athlete(item)
        elif isinstance(item, RaceItem):
            adapter = ItemAdapter(item)
            raw_date = adapter.get("meet_date")
            if raw_date:
                try:
                    cleaned = raw_date.strip().strip("()")
                    parsed = time.strptime(cleaned, "%b %d, %Y")
                    adapter["meet_date"] = time.strftime("%m/%d/%Y", parsed)
                except ValueError:
                    pass
            self._store_race(item)
        elif isinstance(item, MeetItem):
            adapter = ItemAdapter(item)
            raw_date = adapter.get("meet_date")
            if raw_date:
                try:
                    cleaned = " ".join(str(raw_date).split())
                    parsed = time.strptime(cleaned, "%b %d, %Y")
                    adapter["meet_date"] = time.strftime("%m/%d/%Y", parsed)
                except ValueError:
                    pass
            self._store_meet(item)
        return item

    def _touch(self):
        self._pending += 1
        if self._pending >= self.COMMIT_EVERY:
            self.conn.commit()
            self._pending = 0

    def _store_team(self, item):
        try:
            self.curr.execute(
                "INSERT OR IGNORE INTO Teams VALUES (?, ?, ?)",
                (item["team_id"], item["team_name"], item["gender"]),
            )
            self._touch()
        except sqlite3.Error as exc:
            raise DropItem(f"team store failed: {exc}") from exc

    def _store_athlete(self, item):
        try:
            self.curr.execute(
                "INSERT OR IGNORE INTO Athletes VALUES (?, ?, ?, ?)",
                (
                    item["athlete_id"],
                    item["ath_first"],
                    item["ath_last"],
                    item["team_id"],
                ),
            )
            self._touch()
        except sqlite3.Error as exc:
            raise DropItem(f"athlete store failed: {exc}") from exc

    def _store_race(self, item):
        try:
            adapter = ItemAdapter(item)
            self.curr.execute(
                """
                INSERT OR IGNORE INTO Races
                (athlete_id, distance, race_time, meet_name, meet_date, meet_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    adapter.get("athlete_id"),
                    adapter.get("distance"),
                    adapter.get("race_time"),
                    adapter.get("meet_name"),
                    adapter.get("meet_date"),
                    adapter.get("meet_id"),
                ),
            )
            if adapter.get("meet_id"):
                self.curr.execute(
                    """
                    UPDATE Races
                    SET meet_id = COALESCE(meet_id, ?)
                    WHERE athlete_id = ?
                      AND distance = ?
                      AND race_time = ?
                      AND meet_name = ?
                      AND (
                        meet_date = ?
                        OR (meet_date IS NULL AND ? IS NULL)
                      )
                    """,
                    (
                        adapter.get("meet_id"),
                        adapter.get("athlete_id"),
                        adapter.get("distance"),
                        adapter.get("race_time"),
                        adapter.get("meet_name"),
                        adapter.get("meet_date"),
                        adapter.get("meet_date"),
                    ),
                )
            self._touch()
        except sqlite3.Error as exc:
            raise DropItem(f"race store failed: {exc}") from exc

    def _store_meet(self, item):
        try:
            adapter = ItemAdapter(item)
            self.curr.execute(
                """
                INSERT INTO Meets (
                    meet_id, meet_name, meet_date, location_text,
                    venue_name, city, state
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(meet_id) DO UPDATE SET
                    meet_name=excluded.meet_name,
                    meet_date=COALESCE(excluded.meet_date, Meets.meet_date),
                    location_text=COALESCE(excluded.location_text, Meets.location_text),
                    venue_name=COALESCE(excluded.venue_name, Meets.venue_name),
                    city=COALESCE(excluded.city, Meets.city),
                    state=COALESCE(excluded.state, Meets.state)
                """,
                (
                    adapter.get("meet_id"),
                    adapter.get("meet_name"),
                    adapter.get("meet_date"),
                    adapter.get("location_text"),
                    adapter.get("venue_name"),
                    adapter.get("city"),
                    adapter.get("state"),
                ),
            )
            self._touch()
        except sqlite3.Error as exc:
            raise DropItem(f"meet store failed: {exc}") from exc

    def _enrich_pending_meets(self, spider):
        rows = self.curr.execute(
            """
            SELECT meet_id, meet_name, meet_date, location_text, venue_name,
                   city, state, lat, lon, elevation_m, temp_c, precip_mm,
                   weather_source
            FROM Meets
            WHERE lat IS NULL OR lon IS NULL OR temp_c IS NULL OR precip_mm IS NULL
            """
        ).fetchall()
        cols = [
            "meet_id",
            "meet_name",
            "meet_date",
            "location_text",
            "venue_name",
            "city",
            "state",
            "lat",
            "lon",
            "elevation_m",
            "temp_c",
            "precip_mm",
            "weather_source",
        ]
        for values in rows:
            row = dict(zip(cols, values))
            try:
                enrich_meet_row(row)
            except Exception as exc:  # noqa: BLE001 - keep scrape alive
                spider.logger.warning("Meet enrich failed for %s: %s", row.get("meet_id"), exc)
                continue
            self.curr.execute(
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
            self._touch()
        self.conn.commit()
