#!/usr/bin/env python3
"""Smoke tests for course difficulty and race prediction."""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UI = os.path.join(ROOT, "Source-Code", "User-Interface")
sys.path.insert(0, UI)

from data_pull import DB  # noqa: E402


DB_PATH = os.path.join(UI, "racedata.db")


class RaceAlgorithmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DB(DB_PATH)

    def test_parse_time_and_distance(self):
        self.assertAlmostEqual(self.db.parse_race_seconds("25:42.8"), 25 * 60 + 42.8)
        self.assertAlmostEqual(self.db.parse_race_seconds("01:06:48.6"), 4008.6)
        self.assertIsNone(self.db.parse_race_seconds("DNF"))
        self.assertAlmostEqual(self.db.parse_distance_meters("8k"), 8000.0)
        self.assertAlmostEqual(self.db.parse_distance_meters("3.1M"), 3.1 * 1609.344, places=3)

    def test_course_ratings_exist(self):
        ratings = self.db.get_course_ratings()
        self.assertGreater(len(ratings), 100)
        # Twilight 5ks should trend fast (< 1.0)
        twilight = [v for k, v in ratings.items() if "Twilight" in k]
        self.assertTrue(twilight)
        self.assertLess(sum(twilight) / len(twilight), 1.0)
        self.assertEqual(self.db.get_course_rating("Average / Neutral"), 1.0)

    def test_riegel_scales_with_distance(self):
        eight = self.db.riegel_equivalent(26 * 60, 8000, 8000)
        six = self.db.riegel_equivalent(26 * 60, 8000, 6000)
        self.assertAlmostEqual(eight, 26 * 60)
        self.assertLess(six, eight)

    def test_predict_known_athlete(self):
        # Grab a busy athlete from the DB
        self.db._start_connection()
        athlete_id = self.db.curr.execute(
            """SELECT athlete_id FROM Races
               GROUP BY athlete_id HAVING COUNT(*) >= 8
               ORDER BY COUNT(*) DESC LIMIT 1"""
        ).fetchone()[0]
        team_row = self.db.curr.execute(
            """SELECT gender FROM Athletes a
               JOIN Teams t ON a.team_id = t.team_id
               WHERE a.athlete_id = ?""",
            (athlete_id,),
        ).fetchone()
        self.db._close_connection()
        gender = team_row[0]
        races = self.db.get_athlete_races(athlete_id)
        seconds = self.db.predict_race_seconds(races, gender)
        self.assertIsNotNone(seconds)
        # Collegiate XC ballpark
        self.assertGreater(seconds, 14 * 60)
        self.assertLess(seconds, 45 * 60)

        hard_meet = max(self.db.get_course_ratings().items(), key=lambda kv: kv[1])[0]
        hard_seconds = self.db.predict_race_seconds(races, gender, hard_meet)
        self.assertGreater(hard_seconds, seconds)

    def test_team_scoring_requires_five(self):
        places = ["A", "B", "A", "B", "A", "B", "A", "A", "B"]
        limited = self.db.actual_score(places)
        scored = self.db.team_score_test(limited)
        # Both have 4+ in limited top7; A has 5 scorers, B has 4
        teams = {name: score for name, score in scored}
        self.assertIn("A", teams)
        self.assertNotIn("B", teams)


if __name__ == "__main__":
    unittest.main()
