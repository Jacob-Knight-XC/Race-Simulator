"""SQLite access, course difficulty, and race-time prediction."""

from __future__ import annotations

import math
import re
import sqlite3
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Iterable, Iterator, Optional

import numpy as np

INVALID_RESULTS = frozenset({"DNF", "DNS", "DQ", "SCR", "X"})
DEFAULT_DB = Path(__file__).resolve().parent / "racedata.db"


class RaceDB:
    """Read race history and produce difficulty-aware predictions."""

    TARGET_DISTANCE = {"m": 8000.0, "f": 6000.0}
    TARGET_LABEL = {"m": "8k", "f": "6k"}

    def __init__(self, name: str | Path | None = None):
        self.path = str(name or DEFAULT_DB)
        self._course_cache: Optional[dict[str, float]] = None
        self._teams_cache: dict[str, list[tuple[str, str]]] = {}

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def get_teams(self, gender: str) -> list[tuple[str, str]]:
        """Return [(team_name, team_id), ...] for gender 'm' or 'f'."""
        if gender in self._teams_cache:
            return self._teams_cache[gender]
        with self.connection() as conn:
            rows = conn.execute(
                """SELECT team_name, team_id
                   FROM Teams
                   WHERE gender = ?
                   ORDER BY team_name""",
                (gender,),
            ).fetchall()
        self._teams_cache[gender] = rows
        return rows

    def get_team_id(self, name: str, gender: str) -> Optional[str]:
        for team_name, team_id in self.get_teams(gender):
            if team_name == name:
                return team_id
        return None

    def get_roster(self, team_id: str) -> list[tuple[str, int]]:
        with self.connection() as conn:
            return conn.execute(
                """SELECT (ath_first || ' ' || ath_last) AS name, athlete_id
                   FROM Athletes
                   WHERE team_id = ?
                   ORDER BY name""",
                (team_id,),
            ).fetchall()

    def get_athlete_id(self, name: str, team_id: str) -> Optional[int]:
        for ath_name, ath_id in self.get_roster(team_id):
            if ath_name == name:
                return ath_id
        return None

    def get_athlete_races(self, athlete_id: Optional[int]) -> list[tuple]:
        if athlete_id is None:
            return []
        with self.connection() as conn:
            return conn.execute(
                """SELECT distance, race_time, meet_name, meet_date
                   FROM Races
                   WHERE athlete_id = ?
                   ORDER BY meet_date DESC""",
                (athlete_id,),
            ).fetchall()

    def get_races_for_athletes(
        self, athlete_ids: Iterable[int]
    ) -> dict[int, list[tuple]]:
        """Batch-load race rows for many athletes in one query."""
        ids = [int(a) for a in athlete_ids]
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as conn:
            rows = conn.execute(
                f"""SELECT athlete_id, distance, race_time, meet_name, meet_date
                    FROM Races
                    WHERE athlete_id IN ({placeholders})
                    ORDER BY athlete_id, meet_date DESC""",
                ids,
            ).fetchall()
        by_athlete: dict[int, list[tuple]] = defaultdict(list)
        for athlete_id, distance, race_time, meet_name, meet_date in rows:
            by_athlete[athlete_id].append(
                (distance, race_time, meet_name, meet_date)
            )
        return by_athlete

    def get_meet_names(self) -> list[str]:
        ratings = self.get_course_ratings()
        return [name for name, _ in sorted(ratings.items(), key=lambda kv: -kv[1])]

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def parse_distance_meters(distance: Optional[str]) -> Optional[float]:
        if not distance:
            return None
        match = re.match(r"^(\d+(?:\.\d+)?)\s*([kKmM])$", distance.strip())
        if not match:
            return None
        value = float(match.group(1))
        return value * 1000.0 if match.group(2).lower() == "k" else value * 1609.344

    @staticmethod
    def parse_race_seconds(race_time: Optional[str]) -> Optional[float]:
        if not race_time or race_time in INVALID_RESULTS:
            return None
        parts = race_time.strip().split(":")
        try:
            if len(parts) == 2:
                return float(parts[0]) * 60.0 + float(parts[1])
            if len(parts) == 3:
                return (
                    float(parts[0]) * 3600.0
                    + float(parts[1]) * 60.0
                    + float(parts[2])
                )
        except ValueError:
            return None
        return None

    @staticmethod
    def seconds_to_timestr(seconds: Optional[float]) -> str:
        if seconds is None or not math.isfinite(seconds) or seconds <= 0:
            return "N/A"
        total_tenths = int(round(seconds * 10))
        mins, tenths = divmod(total_tenths, 600)
        secs, tenth = divmod(tenths, 10)
        return f"{mins:02d}:{secs:02d}.{tenth}"

    def _times_near_distance(
        self, race_rows, target_meters: float, tolerance: float = 0.02
    ) -> list[str]:
        times = []
        for row in race_rows:
            meters = self.parse_distance_meters(row[0])
            secs = self.parse_race_seconds(row[1])
            if meters is None or secs is None:
                continue
            if abs(meters - target_meters) / target_meters <= tolerance:
                times.append(self.seconds_to_timestr(secs))
        times.sort(key=lambda t: self.parse_race_seconds(t) or math.inf)
        return times

    def get_8k_times(self, race_rows) -> list[str]:
        return self._times_near_distance(race_rows, 8000.0)

    def get_6k_times(self, race_rows) -> list[str]:
        return self._times_near_distance(race_rows, 6000.0)

    def get_5k_times(self, race_rows) -> list[str]:
        return self._times_near_distance(race_rows, 5000.0)

    def average_time(self, time_lst: list[str]) -> str:
        seconds = [s for t in time_lst if (s := self.parse_race_seconds(t)) is not None]
        if not seconds:
            return "Less than One Race"
        return self.seconds_to_timestr(float(np.mean(seconds)))

    def get_avg_8k(self, race_rows) -> str:
        return self.average_time(self.get_8k_times(race_rows))

    def get_avg_6k(self, race_rows) -> str:
        return self.average_time(self.get_6k_times(race_rows))

    def get_avg_5k(self, race_rows) -> str:
        return self.average_time(self.get_5k_times(race_rows))

    def fastest_average(self, time_lst: list[str], n: int = 4) -> str:
        seconds = sorted(
            s for t in time_lst if (s := self.parse_race_seconds(t)) is not None
        )
        if not seconds:
            return "Less than One Race"
        return self.seconds_to_timestr(float(np.mean(seconds[:n])))

    def athlete_pr(self, time_lst: list[str]) -> str:
        seconds = [
            s for t in time_lst if (s := self.parse_race_seconds(t)) is not None
        ]
        return self.seconds_to_timestr(min(seconds)) if seconds else "N/A"

    # ------------------------------------------------------------------
    # Course difficulty
    # ------------------------------------------------------------------
    def get_course_ratings(self, min_samples: int = 20) -> dict[str, float]:
        """meet_name -> difficulty factor (1.0 = average, higher = harder)."""
        if self._course_cache is not None:
            return self._course_cache

        with self.connection() as conn:
            rows = conn.execute(
                "SELECT athlete_id, distance, race_time, meet_name FROM Races"
            ).fetchall()

        athlete_paces: dict[int, list[float]] = defaultdict(list)
        parsed: list[tuple[int, float, str]] = []
        for athlete_id, distance, race_time, meet_name in rows:
            meters = self.parse_distance_meters(distance)
            secs = self.parse_race_seconds(race_time)
            if meters is None or secs is None or meters < 1500:
                continue
            pace = secs / (meters / 1000.0)
            if pace < 120 or pace > 600:
                continue
            athlete_paces[athlete_id].append(pace)
            parsed.append((athlete_id, pace, meet_name))

        baselines = {
            athlete_id: median(paces)
            for athlete_id, paces in athlete_paces.items()
            if len(paces) >= 3
        }

        meet_factors: dict[str, list[float]] = defaultdict(list)
        for athlete_id, pace, meet_name in parsed:
            baseline = baselines.get(athlete_id)
            if baseline:
                meet_factors[meet_name].append(pace / baseline)

        self._course_cache = {
            meet: median(factors)
            for meet, factors in meet_factors.items()
            if len(factors) >= min_samples
        }
        return self._course_cache

    def get_course_rating(self, meet_name: Optional[str]) -> float:
        if not meet_name or meet_name == "Average / Neutral":
            return 1.0
        return self.get_course_ratings().get(meet_name, 1.0)

    @staticmethod
    def describe_course_rating(factor: float) -> str:
        if factor >= 1.04:
            label = "Hard"
        elif factor >= 1.015:
            label = "Above Average"
        elif factor <= 0.96:
            label = "Fast"
        elif factor <= 0.985:
            label = "Below Average"
        else:
            label = "Average"
        return f"{factor:.3f} ({label})"

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    @staticmethod
    def riegel_equivalent(
        time_seconds: float,
        from_meters: float,
        to_meters: float,
        exponent: float = 1.06,
    ) -> Optional[float]:
        if from_meters <= 0 or to_meters <= 0 or time_seconds <= 0:
            return None
        return time_seconds * ((to_meters / from_meters) ** exponent)

    @staticmethod
    def _parse_meet_date(meet_date: Optional[str]) -> Optional[datetime]:
        if not meet_date:
            return None
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y"):
            try:
                return datetime.strptime(meet_date.strip(), fmt)
            except ValueError:
                continue
        return None

    def predict_race_seconds(
        self,
        race_rows,
        gender: str,
        course_meet: Optional[str] = None,
    ) -> Optional[float]:
        """
        Predict finish seconds at the standard collegiate distance.

        Converts history with Riegel scaling, strips source-course
        difficulty, weights recent/strong races, then applies the
        simulated course factor.
        """
        target = self.TARGET_DISTANCE[gender]
        ratings = self.get_course_ratings()
        observations: list[tuple[float, datetime]] = []

        for distance, race_time, meet_name, meet_date in race_rows:
            meters = self.parse_distance_meters(distance)
            secs = self.parse_race_seconds(race_time)
            if meters is None or secs is None or meters < 2000 or meters > 12000:
                continue

            equiv = self.riegel_equivalent(secs, meters, target)
            if equiv is None:
                continue
            pace = equiv / (target / 1000.0)
            if pace < 140 or pace > 550:
                continue

            flat_equiv = equiv / ratings.get(meet_name, 1.0)
            when = self._parse_meet_date(meet_date) or datetime(2020, 1, 1)
            observations.append((flat_equiv, when))

        if not observations:
            return None

        newest = max(when for _, when in observations)
        values = [value for value, _ in observations]
        best = min(values)
        mean_value = float(np.mean(values))

        weighted_sum = 0.0
        weight_total = 0.0
        for value, when in observations:
            days_ago = max(0, (newest - when).days)
            recency = 0.5 ** (days_ago / 45.0)
            form_boost = 1.0 + min(0.35, max(0.0, (mean_value - value) / best))
            weight = recency * form_boost
            weighted_sum += value * weight
            weight_total += weight

        return (weighted_sum / weight_total) * self.get_course_rating(course_meet)

    def predict_race_time(
        self,
        race_rows,
        gender: str,
        course_meet: Optional[str] = None,
    ) -> str:
        seconds = self.predict_race_seconds(race_rows, gender, course_meet)
        return (
            "Insufficient Data"
            if seconds is None
            else self.seconds_to_timestr(seconds)
        )

    def predict_many(
        self,
        athletes: list[tuple[str, str, int, str]],
        course_meet: Optional[str] = None,
    ) -> list[list]:
        """
        Predict for many athletes with one batched race-history query.

        athletes: [(gender, team_name, athlete_id, athlete_name), ...]
        returns rows [gender, team, athlete_name, predicted_time]
        """
        races_by_id = self.get_races_for_athletes(athlete_id for _, _, athlete_id, _ in athletes)
        results = []
        for gender, team_name, athlete_id, athlete_name in athletes:
            predicted = self.predict_race_time(
                races_by_id.get(athlete_id, []), gender, course_meet
            )
            results.append([gender, team_name, athlete_name, predicted])
        return results

    # ------------------------------------------------------------------
    # Sorting / NCAA team scoring
    # ------------------------------------------------------------------
    def sort_by_time(self, rows: list) -> list:
        """Sort result rows by predicted time at index 3."""

        def sort_key(row):
            secs = self.parse_race_seconds(row[3]) if len(row) > 3 else None
            return (1, math.inf) if secs is None else (0, secs)

        return sorted(rows, key=sort_key)

    def score_teams(self, finishing_teams: list[str]) -> list[list]:
        """
        Apply NCAA rules: only top 7 per team displace; top 5 score.
        Returns [[team_name, score], ...] sorted by score.
        """
        by_team: dict[str, list[int]] = defaultdict(list)
        for place, team_name in enumerate(finishing_teams, start=1):
            if len(by_team[team_name]) < 7:
                by_team[team_name].append(place)

        limited = sorted(
            ([team, place] for team, places in by_team.items() for place in places),
            key=lambda row: row[1],
        )
        order = [team for team, _ in limited]

        scorers: dict[str, list[int]] = defaultdict(list)
        for place, team_name in enumerate(order, start=1):
            if len(scorers[team_name]) < 5:
                scorers[team_name].append(place)

        scored = [
            [team, sum(places)]
            for team, places in scorers.items()
            if len(places) >= 5
        ]
        return sorted(scored, key=lambda row: row[1])


# Backward-compatible alias used by older imports/tests during migration.
DB = RaceDB


if __name__ == "__main__":
    db = RaceDB()
    ratings = db.get_course_ratings()
    print(f"Rated {len(ratings)} courses")
    print("Hardest:", sorted(ratings.items(), key=lambda kv: -kv[1])[:5])
