import sqlite3
import time
from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from .items import AthleteItem, RaceItem, TeamItem


class TfrrsPipeline:
    """Persist scraped TFRRS teams, athletes, and races to SQLite."""

    COMMIT_EVERY = 200

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.curr = None
        self._pending = 0

    @classmethod
    def from_crawler(cls, crawler):
        db_path = crawler.settings.get("RACE_DB_PATH", "racedata.db")
        return cls(db_path=db_path)

    def open_spider(self, spider):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.curr = self.conn.cursor()
        self._create_tables()

    def close_spider(self, spider):
        if self.conn is not None:
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
                CONSTRAINT unq UNIQUE(
                    athlete_id, distance, race_time, meet_name, meet_date
                )
            );
            """
        )
        self.conn.commit()

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
            self.curr.execute(
                "INSERT OR IGNORE INTO Races VALUES (?, ?, ?, ?, ?)",
                (
                    item["athlete_id"],
                    item["distance"],
                    item["race_time"],
                    item["meet_name"],
                    item["meet_date"],
                ),
            )
            self._touch()
        except sqlite3.Error as exc:
            raise DropItem(f"race store failed: {exc}") from exc
