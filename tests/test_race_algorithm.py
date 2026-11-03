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
        self.assertGreaterEqual(min(values), self.db.COURSE_FACTOR_CLIP_MIN)
        self.assertLessEqual(max(values), self.db.COURSE_FACTOR_CLIP_MAX)
        self.assertLess(min(values), 1.0)
        self.assertGreater(max(values), 1.0)
        self.assertEqual(self.db.get_course_rating("Average / Neutral"), 1.0)
        # Short-distance "Little 3 Cross Country Meet" used to rate ~1.57
        # from raw 1.24M paces; it must stay inside the realistic band.
        little3 = ratings.get("Little 3 Cross Country Meet")
        if little3 is not None:
            self.assertLessEqual(little3, self.db.COURSE_FACTOR_CLIP_MAX)
        human = self.db.get_meet_names()
        self.assertTrue(human)
        self.assertFalse(any(name.startswith(("geo:", "city:")) for name in human))

    def test_environmental_and_venue_helpers(self):
        self.assertGreater(
            self.db.environmental_factor(elevation_m=1500, precip_mm=20, temp_c=28),
            1.0,
        )
        self.assertEqual(
            self.db.venue_key(41.04, -73.71, "Purchase", "NY", "Foo"),
            "geo:41.04,-73.71",
        )
        self.assertEqual(
            self.db.venue_key(None, None, "Purchase", "NY", "Foo Invite"),
            "city:purchase,ny",
        )

    def test_meet_normalization_season_and_importance(self):
        self.assertEqual(
            self.db.normalize_meet_key("2025 Purple Valley XC Invite"),
            "Purple Valley XC Invite",
        )
        self.assertEqual(
            self.db.normalize_meet_key("Purple Valley XC Invite"),
            "Purple Valley XC Invite",
        )
        early = self.db.season_fitness(self.db._parse_meet_date("09/01/2025"))
        late = self.db.season_fitness(self.db._parse_meet_date("11/15/2025"))
        self.assertLess(early, late)
        self.assertAlmostEqual(late, 1.0, places=2)
        self.assertGreater(
            self.db.meet_importance_weight(
                "NCAA Division III Midwest Region Cross Country Championships"
            ),
            1.0,
        )
        self.assertEqual(
            self.db.meet_importance_weight(
                "American Rivers Conference Championships"
            ),
            1.0,
        )
        self.assertEqual(self.db.FORM_BOOST_CAP, 0.18)

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

    def test_limit_athletes_per_team(self):
        rows = [
            ["m", "Alpha", "A1", "25:00.0"],
            ["m", "Alpha", "A2", "25:10.0"],
            ["m", "Alpha", "A3", "25:20.0"],
            ["m", "Beta", "B1", "25:05.0"],
            ["m", "Alpha", "A4", "Insufficient Data"],
        ]
        limited = self.db.limit_athletes_per_team(rows, 2)
        names = [row[2] for row in limited if self.db.parse_race_seconds(row[3])]
        self.assertEqual(names, ["A1", "B1", "A2"])
        self.assertTrue(any(row[2] == "A4" for row in limited))

    def test_team_meet_breakdown_spreads_and_roles(self):
        rows = [
            ["m", "Alpha", "A1", "25:00.0"],
            ["m", "Beta", "B1", "25:05.0"],
            ["m", "Alpha", "A2", "25:10.0"],
            ["m", "Beta", "B2", "25:15.0"],
            ["m", "Alpha", "A3", "25:20.0"],
            ["m", "Beta", "B3", "25:25.0"],
            ["m", "Alpha", "A4", "25:30.0"],
            ["m", "Beta", "B4", "25:35.0"],
            ["m", "Alpha", "A5", "25:40.0"],
            ["m", "Beta", "B5", "25:45.0"],
            ["m", "Alpha", "A6", "25:50.0"],
            ["m", "Alpha", "A7", "26:00.0"],
            ["m", "Alpha", "A8", "26:10.0"],
        ]
        analysis = self.db.analyze_team_meet(rows)
        teams = {t["team"]: t for t in analysis["teams"]}
        self.assertIn("Alpha", teams)
        self.assertIn("Beta", teams)
        self.assertEqual(teams["Alpha"]["place"], 1)
        self.assertEqual(teams["Alpha"]["scoring_places"], [1, 3, 5, 7, 9])
        self.assertEqual(teams["Alpha"]["spread_1_5_str"], "00:40.0")
        self.assertEqual(teams["Alpha"]["spread_1_7_str"], "01:00.0")
        roles = {
            row["athlete"]: row["role"]
            for row in analysis["board"]
            if row["team"] == "Alpha"
        }
        self.assertEqual(roles["A5"], "Scorer")
        self.assertEqual(roles["A6"], "Displacer")
        self.assertEqual(roles["A7"], "Displacer")
        self.assertEqual(roles["A8"], "Non-scorer")
        self.assertTrue(analysis["insights"])

    def test_top_teams_and_athletes_national(self):
        gender = "m"
        top_athletes = self.db.top_athletes_field(gender, None, limit=100)
        self.assertLessEqual(len(top_athletes), 100)
        self.assertTrue(top_athletes)
        times = [self.db.parse_race_seconds(row[3]) for row in top_athletes]
        self.assertTrue(all(t is not None for t in times))
        self.assertEqual(times, sorted(times))

        race = self.db.top_teams_race(gender, None, n_teams=30, per_team=7)
        self.assertLessEqual(race["n_teams"], 30)
        self.assertTrue(race["teams"])
        self.assertLessEqual(len(race["teams"]), 30)
        for team in race["teams"]:
            self.assertLessEqual(len(team["runners"]), 7)
            self.assertIsNotNone(team.get("national_rank"))
            self.assertGreaterEqual(team["national_rank"], 1)
            self.assertLessEqual(team["national_rank"], race["teams_scored_nationally"])
        team_names = {t["team"] for t in race["teams"]}
        self.assertEqual(len(team_names), race["n_teams"])
        counts = {}
        for row in race["board"]:
            self.assertIn(row["team"], team_names)
            counts[row["team"]] = counts.get(row["team"], 0) + 1
        self.assertTrue(all(count <= 7 for count in counts.values()))

    def test_ustfccca_poll_snapshot_and_ranked_race(self):
        from ustfccca_poll import (  # noqa: WPS433
            load_snapshot_poll,
            map_ustfccca_team_name,
        )

        self.assertEqual(map_ustfccca_team_name("UW-La Crosse"), "Wis.-La Crosse")
        self.assertEqual(map_ustfccca_team_name("Chicago"), "U. of Chicago")
        poll = load_snapshot_poll("m")
        self.assertGreaterEqual(len(poll["teams"]), 25)
        ranked = []
        for entry in poll["teams"]:
            mapped = map_ustfccca_team_name(entry["name"])
            if self.db.get_team_id(mapped, "m"):
                ranked.append({"rank": entry["rank"], "name": mapped})
        self.assertGreaterEqual(len(ranked), 20)
        race = self.db.race_ranked_teams("m", ranked[:10], None, per_team=7)
        self.assertTrue(race["teams"])
        for team in race["teams"]:
            self.assertIsNotNone(team.get("national_rank"))
            self.assertLessEqual(team["national_rank"], 10)

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
