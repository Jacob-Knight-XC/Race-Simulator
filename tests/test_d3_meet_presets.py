#!/usr/bin/env python3
"""Tests for NCAA DIII conference / regional meet presets."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import d3_meet_presets  # noqa: E402


class D3MeetPresetTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = Path(self._tmpdir.name) / "d3_meet_presets.json"
        self._original = d3_meet_presets.PRESETS_PATH
        d3_meet_presets.PRESETS_PATH = self._path
        d3_meet_presets.clear_preset_cache()
        payload = {
            "division": "d3",
            "season": "2025-26",
            "regions": {
                "Region I (East)": {
                    "m": ["Tufts", "MIT"],
                    "f": ["Tufts", "Wellesley"],
                    "source": "test",
                },
                "Region X (West)": {
                    "m": ["Pomona-Pitzer"],
                    "f": ["Pomona-Pitzer"],
                    "source": "test",
                },
            },
            "conferences": {
                "NESCAC": {
                    "m": ["Tufts", "Amherst"],
                    "f": ["Tufts", "Williams"],
                    "source_meet": "NESCAC Championships",
                },
                "WIAC": {
                    "m": ["Wis.-La Crosse"],
                    "f": ["Wis.-La Crosse"],
                    "source_meet": "WIAC Championships",
                },
            },
        }
        self._path.write_text(json.dumps(payload), encoding="utf-8")

    def tearDown(self):
        d3_meet_presets.PRESETS_PATH = self._original
        d3_meet_presets.clear_preset_cache()
        self._tmpdir.cleanup()

    def test_lists_and_season(self):
        self.assertTrue(d3_meet_presets.presets_available())
        self.assertEqual(d3_meet_presets.preset_season(), "2025-26")
        self.assertEqual(
            d3_meet_presets.list_conferences(), ["NESCAC", "WIAC"]
        )
        self.assertEqual(
            d3_meet_presets.list_regions(),
            ["Region I (East)", "Region X (West)"],
        )

    def test_parse_and_payload(self):
        options = d3_meet_presets.list_preset_options()
        self.assertIn("Conference · NESCAC", options)
        self.assertIn("Regional · Region I (East)", options)
        self.assertEqual(
            d3_meet_presets.parse_preset_option("Conference · NESCAC"),
            ("conference", "NESCAC"),
        )
        self.assertEqual(
            d3_meet_presets.parse_preset_option("Regional · Region I (East)"),
            ("region", "Region I (East)"),
        )
        self.assertIsNone(d3_meet_presets.parse_preset_option("bogus"))

        teams = d3_meet_presets.teams_for("conference", "NESCAC", "m")
        self.assertEqual(teams, ["Tufts", "Amherst"])
        payload = d3_meet_presets.lineup_payload("region", "Region I (East)", "f")
        self.assertEqual(
            payload["teams"],
            [
                {"gender": "f", "team": "Tufts"},
                {"gender": "f", "team": "Wellesley"},
            ],
        )

    def test_missing_file(self):
        d3_meet_presets.PRESETS_PATH = Path(self._tmpdir.name) / "missing.json"
        d3_meet_presets.clear_preset_cache()
        self.assertFalse(d3_meet_presets.presets_available())
        self.assertEqual(d3_meet_presets.list_conferences(), [])
        self.assertEqual(d3_meet_presets.teams_for("conference", "NESCAC", "m"), [])


class ShippedD3PresetSmokeTests(unittest.TestCase):
    def setUp(self):
        self._original = d3_meet_presets.PRESETS_PATH
        d3_meet_presets.PRESETS_PATH = Path(ROOT) / "data" / "d3_meet_presets.json"
        d3_meet_presets.clear_preset_cache()

    def tearDown(self):
        d3_meet_presets.PRESETS_PATH = self._original
        d3_meet_presets.clear_preset_cache()

    def test_shipped_json_has_regions_and_key_conferences(self):
        if not d3_meet_presets.PRESETS_PATH.is_file():
            self.skipTest("shipped presets not present")
        self.assertTrue(d3_meet_presets.presets_available())
        conferences = set(d3_meet_presets.list_conferences())
        for name in ("NESCAC", "WIAC", "Little East", "NJAC", "United East"):
            self.assertIn(name, conferences)
        regions = d3_meet_presets.list_regions()
        self.assertEqual(len(regions), 10)
        self.assertTrue(regions[0].startswith("Region I"))
        men = d3_meet_presets.teams_for("conference", "NESCAC", "m")
        self.assertGreaterEqual(len(men), 8)


if __name__ == "__main__":
    unittest.main()
