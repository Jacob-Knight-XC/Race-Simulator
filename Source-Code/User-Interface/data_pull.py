import math
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median

import numpy as np


INVALID_RESULTS = {"DNF", "DNS", "DQ", "SCR", "X"}


class DB:
    """SQLite access plus race prediction and course-difficulty helpers."""

    TARGET_DISTANCE = {"m": 8000.0, "f": 6000.0}
    TARGET_LABEL = {"m": "8k", "f": "6k"}

    def __init__(self, name="racedata.db"):
        self.name = name
        self._course_cache = None

    def _start_connection(self):
        try:
            self.conn = sqlite3.connect(self.name)
            self.curr = self.conn.cursor()
        except sqlite3.Error:
            print("did not connect")

    def _close_connection(self):
        if getattr(self, "conn", None) is not None:
            self.conn.close()
            self.conn = None
            self.curr = None

    # ------------------------------------------------------------------
    # Team / athlete lookups
    # ------------------------------------------------------------------
    def get_div_teams(self, gender):
        """Return [(team_name, team_id), ...] for a gender ('m' or 'f')."""
        self._start_connection()
        teams = self.curr.execute(
            """SELECT team_name, team_id
               FROM Teams
               WHERE gender = ?
               ORDER BY team_name""",
            (gender,),
        ).fetchall()
        self._close_connection()
        return teams

    def get_team_id(self, name, gender):
        for team_name, team_id in self.get_div_teams(gender):
            if team_name == name:
                return team_id
        return None

    def get_init_team_roster(self, team_id):
        self._start_connection()
        roster = self.curr.execute(
            """SELECT (ath_first || ' ' || ath_last) AS name, athlete_id
               FROM Athletes
               WHERE team_id = ?
               ORDER BY name""",
            (team_id,),
        ).fetchall()
        self._close_connection()
        return roster

    def get_athlete_id(self, name, team_id):
        for ath_name, ath_id in self.get_init_team_roster(team_id):
            if ath_name == name:
                return ath_id
        return None

    def get_athlete_races(self, athlete_id):
        if athlete_id is None:
            return []
        self._start_connection()
        races = self.curr.execute(
            """SELECT distance, race_time, meet_name, meet_date
               FROM Races
               WHERE athlete_id = ?
               ORDER BY meet_date DESC""",
            (athlete_id,),
        ).fetchall()
        self._close_connection()
        return races

    def get_a_race(self, meet_name):
        self._start_connection()
        races = self.curr.execute(
            """SELECT distance, race_time, meet_name, meet_date, athlete_id
               FROM Races
               WHERE meet_name = ?
               ORDER BY race_time""",
            (meet_name,),
        ).fetchall()
        self._close_connection()
        return races

    def get_meet_names(self):
        """Return meet names that have a computed course rating, hardest first."""
        ratings = self.get_course_ratings()
        return [name for name, _ in sorted(ratings.items(), key=lambda kv: -kv[1])]

    # ------------------------------------------------------------------
    # Distance / time parsing
    # ------------------------------------------------------------------
    @staticmethod
    def parse_distance_meters(distance):
        if not distance:
            return None
        match = re.match(r"^(\d+(?:\.\d+)?)\s*([kKmM])$", distance.strip())
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2).lower()
        if unit == "k":
            return value * 1000.0
        return value * 1609.344

    @staticmethod
    def parse_race_seconds(race_time):
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
    def seconds_to_timestr(seconds):
        if seconds is None or not math.isfinite(seconds) or seconds <= 0:
            return "N/A"
        total_ms = int(round(seconds * 10))
        mins, tenths = divmod(total_ms, 600)
        secs, tenth = divmod(tenths, 10)
        return f"{mins:02d}:{secs:02d}.{tenth}"

    @staticmethod
    def _str_to_seconds(times):
        """Convert MM:SS.f / HH:MM:SS.f strings to seconds."""
        converted = []
        for t in times:
            secs = DB.parse_race_seconds(t)
            if secs is not None:
                converted.append(secs)
        return converted

    def _is_target_distance(self, distance, gender):
        meters = self.parse_distance_meters(distance)
        if meters is None:
            return False
        target = self.TARGET_DISTANCE[gender]
        return abs(meters - target) / target <= 0.02

    def get_8k_times(self, race_time):
        return self._times_near_distance(race_time, 8000.0)

    def get_6k_times(self, race_time):
        return self._times_near_distance(race_time, 6000.0)

    def get_5k_times(self, race_time):
        return self._times_near_distance(race_time, 5000.0)

    def _times_near_distance(self, race_rows, target_meters, tolerance=0.02):
        times = []
        for row in race_rows:
            meters = self.parse_distance_meters(row[0])
            secs = self.parse_race_seconds(row[1])
            if meters is None or secs is None:
                continue
            if abs(meters - target_meters) / target_meters <= tolerance:
                times.append(self.seconds_to_timestr(secs))
        # fastest first
        times.sort(key=lambda t: self.parse_race_seconds(t))
        return times

    def get_avg_time(self, time_lst):
        seconds = self._str_to_seconds(time_lst)
        if len(seconds) < 1:
            return "Less than One Race"
        return self.seconds_to_timestr(float(np.mean(seconds)))

    def get_avg_8k(self, race_rows):
        return self.get_avg_time(self.get_8k_times(race_rows))

    def get_avg_6k(self, race_rows):
        return self.get_avg_time(self.get_6k_times(race_rows))

    def get_avg_5k(self, race_rows):
        return self.get_avg_time(self.get_5k_times(race_rows))

    def fastest_times(self, time_lst):
        """Average of an athlete's fastest performances (up to 4)."""
        seconds = self._str_to_seconds(time_lst)
        if not seconds:
            return "Less than One Race"
        best = sorted(seconds)[:4]
        return self.seconds_to_timestr(float(np.mean(best)))

    def get_athlete_pr(self, time_lst):
        seconds = self._str_to_seconds(time_lst)
        if not seconds:
            return "N/A"
        return self.seconds_to_timestr(min(seconds))

    # ------------------------------------------------------------------
    # Course difficulty
    # ------------------------------------------------------------------
    def get_course_ratings(self, min_samples=20):
        """
        Map meet_name -> difficulty factor.

        1.00 is average. Higher means a slower/harder course relative to
        each athlete's own typical pace; lower means a faster course.
        """
        if self._course_cache is not None:
            return self._course_cache

        self._start_connection()
        rows = self.curr.execute(
            "SELECT athlete_id, distance, race_time, meet_name FROM Races"
        ).fetchall()
        self._close_connection()

        athlete_paces = defaultdict(list)
        parsed = []
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

        meet_factors = defaultdict(list)
        for athlete_id, pace, meet_name in parsed:
            baseline = baselines.get(athlete_id)
            if baseline:
                meet_factors[meet_name].append(pace / baseline)

        ratings = {
            meet: median(factors)
            for meet, factors in meet_factors.items()
            if len(factors) >= min_samples
        }
        self._course_cache = ratings
        return ratings

    def get_course_rating(self, meet_name):
        if not meet_name or meet_name == "Average / Neutral":
            return 1.0
        return self.get_course_ratings().get(meet_name, 1.0)

    def describe_course_rating(self, factor):
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
    # Race prediction algorithm
    # ------------------------------------------------------------------
    @staticmethod
    def riegel_equivalent(time_seconds, from_meters, to_meters, exponent=1.06):
        """Distance-equivalent time using Riegel's endurance formula."""
        if from_meters <= 0 or to_meters <= 0 or time_seconds <= 0:
            return None
        return time_seconds * ((to_meters / from_meters) ** exponent)

    def _parse_meet_date(self, meet_date):
        if not meet_date:
            return None
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y"):
            try:
                return datetime.strptime(meet_date.strip(), fmt)
            except ValueError:
                continue
        return None

    def predict_race_seconds(self, race_rows, gender, course_meet=None):
        """
        Predict a finishing time (seconds) at the standard collegiate
        distance for `gender`, optionally adjusted for `course_meet`.

        Method:
        1. Convert every valid race to an equivalent flat time at the
           target distance (Riegel), removing the source meet's course
           difficulty.
        2. Weight recent races more heavily and give a slight boost to
           stronger performances (athletes race closer to ability on
           good days).
        3. Take the weighted mean, then re-apply the selected course
           difficulty for the simulated race.
        """
        target = self.TARGET_DISTANCE[gender]
        ratings = self.get_course_ratings()
        observations = []

        for distance, race_time, meet_name, meet_date in race_rows:
            meters = self.parse_distance_meters(distance)
            secs = self.parse_race_seconds(race_time)
            if meters is None or secs is None or meters < 2000 or meters > 12000:
                continue

            # Discard absurd paces after conversion
            equiv = self.riegel_equivalent(secs, meters, target)
            if equiv is None:
                continue
            pace = equiv / (target / 1000.0)
            if pace < 140 or pace > 550:
                continue

            source_factor = ratings.get(meet_name, 1.0)
            flat_equiv = equiv / source_factor

            when = self._parse_meet_date(meet_date) or datetime(2020, 1, 1)
            observations.append((flat_equiv, when))

        if not observations:
            return None

        newest = max(when for _, when in observations)
        values = [value for value, _ in observations]
        best = min(values)

        weighted_sum = 0.0
        weight_total = 0.0
        for value, when in observations:
            days_ago = max(0, (newest - when).days)
            recency = 0.5 ** (days_ago / 45.0)
            # Faster performances get more trust (cap the boost).
            form_boost = 1.0 + min(0.35, max(0.0, (np.mean(values) - value) / best))
            weight = recency * form_boost
            weighted_sum += value * weight
            weight_total += weight

        flat_prediction = weighted_sum / weight_total
        course_factor = self.get_course_rating(course_meet)
        return flat_prediction * course_factor

    def predict_race_time(self, race_rows, gender, course_meet=None):
        seconds = self.predict_race_seconds(race_rows, gender, course_meet)
        if seconds is None:
            return "Insufficient Data"
        return self.seconds_to_timestr(seconds)

    def new_predict(self, time_lst):
        """
        Backward-compatible helper used by older pages.

        `time_lst` is expected to be same-distance time strings already
        filtered to 8k/6k. Prefer predict_race_time() for new code.
        """
        if len(time_lst) < 1:
            return "Less Than Two Races"
        # Build synthetic race rows so the new algorithm can run.
        synthetic = [
            ("8k", t, "Average / Neutral", "01/01/2023") for t in time_lst
        ]
        # Gender inferred as male target; callers should migrate.
        prediction = self.predict_race_time(synthetic, "m")
        if prediction == "Insufficient Data":
            return "Less Than Two Races"
        return prediction

    # ------------------------------------------------------------------
    # Sorting / team scoring
    # ------------------------------------------------------------------
    def Sort(self, sub_li):
        """Sort rows by predicted time at index 3; invalid times sink."""

        def sort_key(row):
            secs = self.parse_race_seconds(row[3]) if len(row) > 3 else None
            if secs is None:
                return (1, float("inf"))
            return (0, secs)

        return sorted(sub_li, key=sort_key)

    def Sorttwo(self, sub_li):
        """Sort [team, score] rows by score ascending."""
        return sorted(sub_li, key=lambda row: row[1])

    def actual_score(self, team_places):
        """
        Keep only each team's top 7 finishers (NCAA displacement rule),
        then return team names in finishing order for scoring.
        """
        by_team = defaultdict(list)
        for place, team_name in enumerate(team_places, start=1):
            by_team[team_name].append(place)

        limited = []
        for team_name, places in by_team.items():
            for place in places[:7]:
                limited.append([team_name, place])

        limited.sort(key=lambda row: row[1])
        return [team_name for team_name, _ in limited]

    def team_score_test(self, team_places):
        """
        Score teams by summing the places of their first five finishers.
        Teams with fewer than five scoring runners are omitted.
        """
        by_team = defaultdict(list)
        for place, team_name in enumerate(team_places, start=1):
            by_team[team_name].append(place)

        scored = []
        for team_name, places in by_team.items():
            if len(places) >= 5:
                scored.append([team_name, sum(places[:5])])
        return self.Sorttwo(scored)


if __name__ == "__main__":
    db = DB()
    ratings = db.get_course_ratings()
    print(f"Rated {len(ratings)} courses")
    sample = sorted(ratings.items(), key=lambda kv: -kv[1])[:5]
    print("Hardest:", sample)
