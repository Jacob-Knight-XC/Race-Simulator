#!/usr/bin/env python3
"""Smoke tests for course difficulty and race prediction."""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

from race_db import RaceDB  # noqa: E402

DB_PATH = os.path.join(APP, "racedata.db")


class RaceAlgorithmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = RaceDB(DB_PATH)

    def test_parse_time_and_distance(self):
        self.assertAlmostEqual(
            self.db.parse_race_seconds("25:42.8"), 25 * 60 + 42.8
        )
        self.assertAlmostEqual(self.db.parse_race_seconds("01:06:48.6"), 4008.6)
        self.assertIsNone(self.db.parse_race_seconds("DNF"))
        self.assertAlmostEqual(self.db.parse_distance_meters("8k"), 8000.0)
        self.assertAlmostEqual(
            self.db.parse_distance_meters("3.1M"), 3.1 * 1609.344, places=3
        )

    def test_course_ratings_exist(self):
        ratings = self.db.get_course_ratings()
        self.assertGreater(len(ratings), 100)
        values = list(ratings.values())
        self.assertLess(min(values), 1.0)
        self.assertGreater(max(values), 1.0)
        self.assertEqual(self.db.get_course_rating("Average / Neutral"), 1.0)

    def test_riegel_scales_with_distance(self):
        eight = self.db.riegel_equivalent(26 * 60, 8000, 8000)
        six = self.db.riegel_equivalent(26 * 60, 8000, 6000)
        self.assertAlmostEqual(eight, 26 * 60)
        self.assertLess(six, eight)

    def test_predict_known_athlete(self):
        with self.db.connection() as conn:
            athlete_id = conn.execute(
                """SELECT athlete_id FROM Races
                   GROUP BY athlete_id HAVING COUNT(*) >= 8
                   ORDER BY COUNT(*) DESC LIMIT 1"""
            ).fetchone()[0]
            gender = conn.execute(
                """SELECT gender FROM Athletes a
                   JOIN Teams t ON a.team_id = t.team_id
                   WHERE a.athlete_id = ?""",
                (athlete_id,),
            ).fetchone()[0]

        races = self.db.get_athlete_races(athlete_id)
        seconds = self.db.predict_race_seconds(races, gender)
        self.assertIsNotNone(seconds)
        self.assertGreater(seconds, 14 * 60)
        self.assertLess(seconds, 45 * 60)

        hard_meet = max(self.db.get_course_ratings().items(), key=lambda kv: kv[1])[0]
        hard_seconds = self.db.predict_race_seconds(races, gender, hard_meet)
        self.assertGreater(hard_seconds, seconds)

    def test_batch_predict_and_team_scoring(self):
        gender = "m"
        teams = self.db.get_teams(gender)[:3]
        athletes = []
        for team_name, team_id in teams:
            for ath_name, ath_id in self.db.get_roster(team_id)[:5]:
                athletes.append((gender, team_name, ath_id, ath_name))

        rows = self.db.sort_by_time(self.db.predict_many(athletes))
        self.assertEqual(len(rows), len(athletes))
        self.assertTrue(any(self.db.parse_race_seconds(r[3]) for r in rows))

        places = ["A", "B", "A", "B", "A", "B", "A", "A", "B", "A"]
        scored = {name: score for name, score in self.db.score_teams(places)}
        self.assertIn("A", scored)
        self.assertNotIn("B", scored)

    def test_scraper_package_imports(self):
        scraper_root = os.path.join(ROOT, "scraper")
        sys.path.insert(0, scraper_root)
        from tfrrs.items import AthleteItem, RaceItem, TeamItem  # noqa: WPS433
        from tfrrs.spiders.xc import XcSpider  # noqa: WPS433

        self.assertEqual(XcSpider.name, "xc")
        self.assertTrue(issubclass(TeamItem, object))
        self.assertTrue(AthleteItem and RaceItem)


if __name__ == "__main__":
    unittest.main()
