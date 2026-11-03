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
        return RaceDB.duration_to_timestr(seconds)

    @staticmethod
    def duration_to_timestr(seconds: Optional[float]) -> str:
        """Format a non-negative duration (including zero), e.g. pack spreads."""
        if seconds is None or not math.isfinite(seconds) or seconds < 0:
            return "—"
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
    # Collegiate XC distances only — short "mini meets" (~2k) and ultra-long
    # oddities skew raw-pace comparisons against 5k/6k/8k baselines.
    COURSE_RATING_MIN_METERS = 4000.0
    COURSE_RATING_MAX_METERS = 10000.0
    COURSE_RATING_REF_METERS = 8000.0
    # Per-observation winsorization before the meet median.
    COURSE_FACTOR_OBS_MIN = 0.88
    COURSE_FACTOR_OBS_MAX = 1.15
    # Final meet ratings stay in a band that matches real XC variance
    # (~±5–8% ≈ about 1–2 minutes on a collegiate 8k).
    COURSE_FACTOR_CLIP_MIN = 0.95
    COURSE_FACTOR_CLIP_MAX = 1.08
    # Early-season races are ~2.5% slower than late-season peak fitness.
    SEASON_START_DOY = 235  # ~Aug 23
    SEASON_END_DOY = 325  # ~Nov 21
    MAX_EARLY_SEASON_SLOWDOWN = 0.025
    # Softer than the old 0.35 cap so one blow-up PR cannot dominate.
    FORM_BOOST_CAP = 0.18
    RECENCY_HALF_LIFE_DAYS = 45.0

    @staticmethod
    def normalize_meet_key(meet_name: Optional[str]) -> str:
        """
        Collapse year-prefixed duplicates onto one course key.

        True venue IDs are not in the TFRRS scrape; stripping years is the
        practical stand-in so '2024 Foo Invite' and '2025 Foo Invite' share a
        rating.
        """
        if not meet_name:
            return ""
        name = meet_name.strip()
        name = re.sub(r"^\d{4}\s+", "", name)
        name = re.sub(r"\s+\d{4}(?=\s|$)", "", name)
        return re.sub(r"\s+", " ", name).strip()

    @classmethod
    def meet_importance_weight(cls, meet_name: Optional[str]) -> float:
        """
        Extra trust for races where athletes usually compete all-out.

        Boost NCAA regionals/nationals and pre-nationals. Leave conference
        championships unboosted — depth of conference varies and some teams
        race tactically there.
        """
        if not meet_name:
            return 1.0
        text = meet_name.lower()
        if "ncaa" in text and (
            "region" in text or "national" in text or "championship" in text
        ):
            return 1.45
        if (
            "pre-national" in text
            or "prenational" in text
            or "pre nationals" in text
            or "national preview" in text
        ):
            return 1.25
        return 1.0

    @classmethod
    def season_fitness(cls, when: Optional[datetime]) -> float:
        """
        1.0 near championships; ~0.975 early in the XC season.

        Used to keep September races from looking like permanently harder
        courses / slower athletes when comparing across the country.
        """
        if when is None:
            return 1.0
        doy = when.timetuple().tm_yday
        span = cls.SEASON_END_DOY - cls.SEASON_START_DOY
        progress = (doy - cls.SEASON_START_DOY) / span
        progress = min(1.0, max(0.0, progress))
        return 1.0 - cls.MAX_EARLY_SEASON_SLOWDOWN * (1.0 - progress)

    @classmethod
    def peak_adjusted_time(
        cls, equiv_seconds: float, when: Optional[datetime]
    ) -> float:
        """Estimate peak-fitness equivalent time from a dated performance."""
        return equiv_seconds * cls.season_fitness(when)

    def get_course_ratings(self, min_samples: int = 20) -> dict[str, float]:
        """
        Normalized meet key -> difficulty factor (1.0 = average, higher = harder).

        For each valid collegiate-distance race, convert to an 8k-equivalent
        time (Riegel), season-adjust toward peak fitness, compare that to the
        athlete's median, and take the meet's median ratio. Year variants of
        the same meet name share one key.
        """
        if self._course_cache is not None:
            return self._course_cache

        with self.connection() as conn:
            rows = conn.execute(
                """SELECT athlete_id, distance, race_time, meet_name, meet_date
                   FROM Races"""
            ).fetchall()

        athlete_equivs: dict[int, list[float]] = defaultdict(list)
        parsed: list[tuple[int, float, str]] = []
        for athlete_id, distance, race_time, meet_name, meet_date in rows:
            meters = self.parse_distance_meters(distance)
            secs = self.parse_race_seconds(race_time)
            if (
                meters is None
                or secs is None
                or meters < self.COURSE_RATING_MIN_METERS
                or meters > self.COURSE_RATING_MAX_METERS
            ):
                continue
            equiv = self.riegel_equivalent(
                secs, meters, self.COURSE_RATING_REF_METERS
            )
            if equiv is None:
                continue
            pace = equiv / (self.COURSE_RATING_REF_METERS / 1000.0)
            if pace < 140 or pace > 550:
                continue
            when = self._parse_meet_date(meet_date)
            peak_equiv = self.peak_adjusted_time(equiv, when)
            meet_key = self.normalize_meet_key(meet_name)
            if not meet_key:
                continue
            athlete_equivs[athlete_id].append(peak_equiv)
            parsed.append((athlete_id, peak_equiv, meet_key))

        baselines = {
            athlete_id: median(equivs)
            for athlete_id, equivs in athlete_equivs.items()
            if len(equivs) >= 3
        }

        meet_factors: dict[str, list[float]] = defaultdict(list)
        for athlete_id, equiv, meet_key in parsed:
            baseline = baselines.get(athlete_id)
            if not baseline:
                continue
            factor = equiv / baseline
            factor = min(
                self.COURSE_FACTOR_OBS_MAX,
                max(self.COURSE_FACTOR_OBS_MIN, factor),
            )
            meet_factors[meet_key].append(factor)

        self._course_cache = {}
        for meet, factors in meet_factors.items():
            if len(factors) < min_samples:
                continue
            rating = median(factors)
            self._course_cache[meet] = min(
                self.COURSE_FACTOR_CLIP_MAX,
                max(self.COURSE_FACTOR_CLIP_MIN, rating),
            )
        return self._course_cache

    def get_course_rating(self, meet_name: Optional[str]) -> float:
        if not meet_name or meet_name == "Average / Neutral":
            return 1.0
        ratings = self.get_course_ratings()
        key = self.normalize_meet_key(meet_name)
        return ratings.get(key, ratings.get(meet_name, 1.0))

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

    def course_effect_seconds(
        self, flat_seconds: float, meet_name: Optional[str]
    ) -> float:
        """Seconds added/removed vs neutral for a flat predicted time."""
        return flat_seconds * (self.get_course_rating(meet_name) - 1.0)

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

        Converts history with Riegel scaling, season-adjusts toward peak
        fitness, strips source-course difficulty, weights by recency /
        mild form / NCAA importance, then applies the simulated course
        factor.
        """
        target = self.TARGET_DISTANCE[gender]
        observations: list[tuple[float, datetime, str]] = []

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

            when = self._parse_meet_date(meet_date) or datetime(2020, 1, 1)
            peak_equiv = self.peak_adjusted_time(equiv, when)
            flat_equiv = peak_equiv / self.get_course_rating(meet_name)
            observations.append((flat_equiv, when, meet_name or ""))

        if not observations:
            return None

        newest = max(when for _, when, _ in observations)
        values = [value for value, _, _ in observations]
        best = min(values)
        mean_value = float(np.mean(values))

        weighted_sum = 0.0
        weight_total = 0.0
        for value, when, meet_name in observations:
            days_ago = max(0, (newest - when).days)
            recency = 0.5 ** (days_ago / self.RECENCY_HALF_LIFE_DAYS)
            form_boost = 1.0 + min(
                self.FORM_BOOST_CAP,
                max(0.0, (mean_value - value) / best),
            )
            importance = self.meet_importance_weight(meet_name)
            weight = recency * form_boost * importance
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

    def list_gender_athletes(
        self, gender: str
    ) -> list[tuple[str, str, int, str]]:
        """All rostered athletes for a gender as predict_many tuples."""
        athletes: list[tuple[str, str, int, str]] = []
        for team_name, team_id in self.get_teams(gender):
            for ath_name, ath_id in self.get_roster(team_id):
                athletes.append((gender, team_name, ath_id, ath_name))
        return athletes

    def simulate_gender_field(
        self, gender: str, course_meet: Optional[str] = None
    ) -> list[list]:
        """Predict and sort every athlete for one gender on a course."""
        return self.sort_by_time(
            self.predict_many(self.list_gender_athletes(gender), course_meet)
        )

    def top_athletes_field(
        self,
        gender: str,
        course_meet: Optional[str] = None,
        limit: int = 100,
    ) -> list[list]:
        """Fastest N predicted athletes for a gender/course."""
        field = self.simulate_gender_field(gender, course_meet)
        valid = [row for row in field if self.parse_race_seconds(row[3]) is not None]
        return valid[:limit]

    def top_teams_race(
        self,
        gender: str,
        course_meet: Optional[str] = None,
        n_teams: int = 30,
        per_team: int = 7,
    ) -> dict:
        """
        Rank every team (top `per_team` athletes each), then re-simulate a
        race containing only the top `n_teams` scoring teams.
        """
        field = self.simulate_gender_field(gender, course_meet)
        national_rows = self.limit_athletes_per_team(field, per_team)
        national = self.analyze_team_meet(national_rows)
        top_team_names = [team["team"] for team in national["teams"][:n_teams]]
        top_set = set(top_team_names)
        race_rows = [
            row
            for row in national_rows
            if row[1] in top_set and self.parse_race_seconds(row[3]) is not None
        ]
        race = self.analyze_team_meet(self.sort_by_time(race_rows))
        national_rank = {
            team["team"]: team["place"] for team in national["teams"]
        }
        for team in race["teams"]:
            team["national_rank"] = national_rank.get(team["team"])
        return {
            "national_teams": national["teams"],
            "teams_scored_nationally": len(national["teams"]),
            "race_athletes": len(race_rows),
            "per_team": per_team,
            "n_teams": len(top_team_names),
            **race,
        }

    # ------------------------------------------------------------------
    # Sorting / NCAA team scoring
    # ------------------------------------------------------------------
    def sort_by_time(self, rows: list) -> list:
        """Sort result rows by predicted time at index 3."""

        def sort_key(row):
            secs = self.parse_race_seconds(row[3]) if len(row) > 3 else None
            return (1, math.inf) if secs is None else (0, secs)

        return sorted(rows, key=sort_key)

    def limit_athletes_per_team(
        self, rows: list, max_per_team: Optional[int]
    ) -> list:
        """
        Keep the fastest N valid predictions per team.

        rows: [gender, team, athlete, time_str] already preferred sorted by time.
        Athletes with insufficient data never consume a roster slot.
        """
        if max_per_team is None:
            return list(rows)

        ordered = self.sort_by_time(rows)
        kept: list = []
        counts: dict[str, int] = defaultdict(int)
        leftovers: list = []
        for row in ordered:
            secs = self.parse_race_seconds(row[3]) if len(row) > 3 else None
            if secs is None:
                leftovers.append(row)
                continue
            team = row[1]
            if counts[team] < max_per_team:
                kept.append(row)
                counts[team] += 1
        return kept + leftovers

    def score_teams(self, finishing_teams: list[str]) -> list[list]:
        """
        Apply NCAA rules: only top 7 per team displace; top 5 score.
        Returns [[team_name, score], ...] sorted by score.
        """
        return [
            [team["team"], team["score"]]
            for team in self.analyze_team_meet_from_places(finishing_teams)["teams"]
        ]

    def analyze_team_meet_from_places(self, finishing_teams: list[str]) -> dict:
        """NCAA score breakdown from an ordered list of team names."""
        race_places: dict[str, list[int]] = defaultdict(list)
        for place, team_name in enumerate(finishing_teams, start=1):
            race_places[team_name].append(place)

        displacing: list[tuple[str, int]] = []
        for team_name, places in race_places.items():
            for place in places[:7]:
                displacing.append((team_name, place))
        displacing.sort(key=lambda item: item[1])

        scoring_place_by_race: dict[tuple[str, int], int] = {}
        team_scoring_places: dict[str, list[int]] = defaultdict(list)
        team_displacing_places: dict[str, list[int]] = defaultdict(list)
        for scoring_place, (team_name, race_place) in enumerate(displacing, start=1):
            scoring_place_by_race[(team_name, race_place)] = scoring_place
            team_displacing_places[team_name].append(scoring_place)
            if len(team_scoring_places[team_name]) < 5:
                team_scoring_places[team_name].append(scoring_place)

        teams = []
        for team_name, places in team_scoring_places.items():
            if len(places) < 5:
                continue
            teams.append(
                {
                    "team": team_name,
                    "score": sum(places),
                    "scoring_places": places,
                    "displacing_places": team_displacing_places[team_name],
                }
            )
        teams.sort(key=lambda row: (row["score"], row["scoring_places"][-1]))
        for idx, team in enumerate(teams, start=1):
            team["place"] = idx
            nxt = teams[idx] if idx < len(teams) else None
            team["gap_to_next"] = (
                None if nxt is None else nxt["score"] - team["score"]
            )

        return {
            "teams": teams,
            "scoring_place_by_race": scoring_place_by_race,
            "race_places": dict(race_places),
        }

    def analyze_team_meet(self, rows: list) -> dict:
        """
        Full team-meet breakdown from predicted finish rows.

        rows: sorted [gender, team, athlete, time_str] with valid times.
        """
        scored_rows = [
            row for row in rows if self.parse_race_seconds(row[3]) is not None
        ]
        place_analysis = self.analyze_team_meet_from_places(
            [row[1] for row in scored_rows]
        )
        scoring_place_by_race = place_analysis["scoring_place_by_race"]
        team_meta = {team["team"]: team for team in place_analysis["teams"]}

        team_runners: dict[str, list[dict]] = defaultdict(list)
        board: list[dict] = []
        team_counts: dict[str, int] = defaultdict(int)

        for race_place, row in enumerate(scored_rows, start=1):
            gender, team_name, athlete_name, time_str = row[:4]
            team_counts[team_name] += 1
            team_order = team_counts[team_name]
            if team_order <= 5:
                role = "Scorer"
            elif team_order <= 7:
                role = "Displacer"
            else:
                role = "Non-scorer"

            scoring_place = scoring_place_by_race.get((team_name, race_place))
            seconds = self.parse_race_seconds(time_str)
            entry = {
                "race_place": race_place,
                "gender": gender,
                "team": team_name,
                "athlete": athlete_name,
                "time": time_str,
                "seconds": seconds,
                "team_order": team_order,
                "role": role,
                "scoring_place": scoring_place,
            }
            board.append(entry)
            team_runners[team_name].append(entry)

        teams_out: list[dict] = []
        for team in place_analysis["teams"]:
            runners = team_runners.get(team["team"], [])
            first = runners[0] if runners else None
            fifth = runners[4] if len(runners) >= 5 else None
            seventh = runners[6] if len(runners) >= 7 else None
            spread_1_5 = (
                None
                if not first or not fifth or first["seconds"] is None or fifth["seconds"] is None
                else fifth["seconds"] - first["seconds"]
            )
            spread_1_7 = (
                None
                if not first or not seventh or first["seconds"] is None or seventh["seconds"] is None
                else seventh["seconds"] - first["seconds"]
            )
            teams_out.append(
                {
                    **team,
                    "runners": runners,
                    "first_time": first["time"] if first else None,
                    "fifth_time": fifth["time"] if fifth else None,
                    "seventh_time": seventh["time"] if seventh else None,
                    "spread_1_5": spread_1_5,
                    "spread_1_7": spread_1_7,
                    "spread_1_5_str": self.duration_to_timestr(spread_1_5),
                    "spread_1_7_str": self.duration_to_timestr(spread_1_7),
                    "scorer_names": [r["athlete"] for r in runners if r["role"] == "Scorer"],
                    "displacer_names": [
                        r["athlete"] for r in runners if r["role"] == "Displacer"
                    ],
                }
            )

        # Incomplete teams (fewer than 5 scorers) still get pack stats.
        incomplete = []
        for team_name, runners in team_runners.items():
            if team_name in team_meta:
                continue
            first = runners[0]
            fifth = runners[4] if len(runners) >= 5 else None
            seventh = runners[6] if len(runners) >= 7 else None
            incomplete.append(
                {
                    "team": team_name,
                    "place": None,
                    "score": None,
                    "scoring_places": [],
                    "displacing_places": [],
                    "gap_to_next": None,
                    "runners": runners,
                    "first_time": first["time"],
                    "fifth_time": fifth["time"] if fifth else None,
                    "seventh_time": seventh["time"] if seventh else None,
                    "spread_1_5": None
                    if not fifth or first["seconds"] is None or fifth["seconds"] is None
                    else fifth["seconds"] - first["seconds"],
                    "spread_1_7": None
                    if not seventh or first["seconds"] is None or seventh["seconds"] is None
                    else seventh["seconds"] - first["seconds"],
                    "spread_1_5_str": self.duration_to_timestr(
                        None
                        if not fifth
                        or first["seconds"] is None
                        or fifth["seconds"] is None
                        else fifth["seconds"] - first["seconds"]
                    ),
                    "spread_1_7_str": self.duration_to_timestr(
                        None
                        if not seventh
                        or first["seconds"] is None
                        or seventh["seconds"] is None
                        else seventh["seconds"] - first["seconds"]
                    ),
                    "scorer_names": [r["athlete"] for r in runners if r["role"] == "Scorer"],
                    "displacer_names": [
                        r["athlete"] for r in runners if r["role"] == "Displacer"
                    ],
                }
            )

        insights = self._team_meet_insights(teams_out, board)
        return {
            "teams": teams_out,
            "incomplete_teams": incomplete,
            "board": board,
            "insights": insights,
        }

    def _team_meet_insights(self, teams: list[dict], board: list[dict]) -> list[str]:
        """Short coaching notes from the scored field."""
        notes: list[str] = []
        if not teams:
            return ["Need at least one team with five scoring runners for a team score."]

        winner = teams[0]
        notes.append(
            f"{winner['team']} leads with {winner['score']} "
            f"({', '.join(str(p) for p in winner['scoring_places'])}); "
            f"1–5 spread {winner['spread_1_5_str']}."
        )
        if winner["spread_1_7_str"] != "—":
            notes.append(
                f"{winner['team']} 1–7 pack covers {winner['spread_1_7_str']}."
            )

        if len(teams) >= 2:
            second = teams[1]
            gap = second["score"] - winner["score"]
            notes.append(
                f"{second['team']} is {gap} point(s) back "
                f"({second['score']}; 1–5 spread {second['spread_1_5_str']})."
            )

        tightest = min(
            (t for t in teams if t["spread_1_5"] is not None),
            key=lambda t: t["spread_1_5"],
            default=None,
        )
        if tightest and tightest["team"] != winner["team"]:
            notes.append(
                f"Tightest scoring five: {tightest['team']} "
                f"({tightest['spread_1_5_str']} 1–5)."
            )

        if board:
            leader = board[0]
            notes.append(
                f"Individual leader: {leader['athlete']} ({leader['team']}) "
                f"in {leader['time']}."
            )

        # Flag a decisive 5th-man battle vs the next team when close.
        if len(teams) >= 2 and winner.get("gap_to_next") is not None and winner["gap_to_next"] <= 15:
            w5 = winner["runners"][4] if len(winner["runners"]) >= 5 else None
            s5 = teams[1]["runners"][4] if len(teams[1]["runners"]) >= 5 else None
            if w5 and s5 and w5["seconds"] is not None and s5["seconds"] is not None:
                delta = abs(w5["seconds"] - s5["seconds"])
                ahead = w5["athlete"] if w5["seconds"] <= s5["seconds"] else s5["athlete"]
                notes.append(
                    f"Fifth-man gap is {self.duration_to_timestr(delta)} "
                    f"({ahead} currently ahead)."
                )

        return notes


# Backward-compatible alias used by older imports/tests during migration.
DB = RaceDB


if __name__ == "__main__":
    db = RaceDB()
    ratings = db.get_course_ratings()
    print(f"Rated {len(ratings)} courses")
    print("Hardest:", sorted(ratings.items(), key=lambda kv: -kv[1])[:5])
