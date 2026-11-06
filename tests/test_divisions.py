#!/usr/bin/env python3
"""Division registry and NAIA meet-importance smoke tests."""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

from divisions import (  # noqa: E402
    DEFAULT_DIVISION,
    DIVISION_ORDER,
    db_path_for,
    get_division,
    league_id_for,
    normalize_division_key,
)
from race_db import RaceDB  # noqa: E402


class DivisionRegistryTests(unittest.TestCase):
    def test_default_is_d3(self):
        self.assertEqual(DEFAULT_DIVISION, "d3")
        self.assertEqual(normalize_division_key(None), "d3")
        self.assertEqual(normalize_division_key("DIII"), "d3")

    def test_naia_maps_to_separate_db_and_league(self):
        self.assertEqual(normalize_division_key("NAIA"), "naia")
        naia = get_division("naia")
        self.assertEqual(naia.tfrrs_league_id, 53)
        self.assertEqual(naia.db_filename, "racedata-naia.db")
        self.assertEqual(naia.national_teams_mode, "ustfccca")
        self.assertEqual(naia.poll_snapshot, "ustfccca_naia_national_poll.json")
        self.assertTrue(str(db_path_for("naia")).endswith("racedata-naia.db"))
        self.assertEqual(league_id_for("naia"), 53)
        self.assertNotEqual(db_path_for("d3"), db_path_for("naia"))

    def test_d3_keeps_legacy_db_name(self):
        d3 = get_division("d3")
        self.assertEqual(d3.tfrrs_league_id, 51)
        self.assertEqual(d3.db_filename, "racedata.db")
        self.assertEqual(d3.national_teams_mode, "ustfccca")

    def test_unknown_division_raises(self):
        with self.assertRaises(ValueError):
            normalize_division_key("njcaa")

    def test_division_order(self):
        self.assertEqual(DIVISION_ORDER, ("d3", "naia"))


class NaiaMeetImportanceTests(unittest.TestCase):
    def test_naia_nationals_boosted(self):
        self.assertEqual(
            RaceDB.meet_importance_weight("NAIA Cross Country National Championships"),
            1.45,
        )
        self.assertEqual(
            RaceDB.meet_importance_weight("NAIA Great Lakes Challenge / Regionals"),
            1.45,
        )
        self.assertEqual(RaceDB.meet_importance_weight("Regular Season Invite"), 1.0)


if __name__ == "__main__":
    unittest.main()
