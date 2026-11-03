#!/usr/bin/env python3
"""Tests for saved lineup persistence."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import lineups  # noqa: E402


class LineupStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = Path(self._tmpdir.name) / "saved_lineups.json"
        self._original = lineups.LINEUPS_PATH
        lineups.LINEUPS_PATH = self._path

    def tearDown(self):
        lineups.LINEUPS_PATH = self._original
        self._tmpdir.cleanup()

    def test_save_list_load_delete_individual(self):
        payload = {
            "course": "Average / Neutral",
            "athletes": [
                {"gender": "m", "team": "Wartburg", "athlete": "Test Runner"}
            ],
        }
        lineups.save_lineup("individual", " Dual Preview ", payload)
        self.assertEqual(lineups.list_lineups("individual"), ["Dual Preview"])
        loaded = lineups.get_lineup("individual", "Dual Preview")
        self.assertEqual(loaded["athletes"][0]["team"], "Wartburg")
        lineups.delete_lineup("individual", "Dual Preview")
        self.assertEqual(lineups.list_lineups("individual"), [])

    def test_team_lineups_are_separate(self):
        lineups.save_lineup(
            "team",
            "ARC",
            {"course": "Average / Neutral", "teams": [{"gender": "m", "team": "Wartburg"}]},
        )
        self.assertEqual(lineups.list_lineups("team"), ["ARC"])
        self.assertEqual(lineups.list_lineups("individual"), [])


if __name__ == "__main__":
    unittest.main()
