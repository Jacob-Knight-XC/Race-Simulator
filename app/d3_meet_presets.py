"""NCAA Division III conference & regional meet presets for Team Race quick-load."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRESETS_PATH = DATA_DIR / "d3_meet_presets.json"

PresetKind = Literal["conference", "region"]


@lru_cache(maxsize=1)
def _raw_presets() -> dict[str, Any]:
    if not PRESETS_PATH.is_file():
        return {"division": "d3", "season": "", "regions": {}, "conferences": {}}
    with PRESETS_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        return {"division": "d3", "season": "", "regions": {}, "conferences": {}}
    data.setdefault("regions", {})
    data.setdefault("conferences", {})
    return data


def clear_preset_cache() -> None:
    """Test helper: drop the cached JSON payload."""
    _raw_presets.cache_clear()


def presets_available() -> bool:
    data = _raw_presets()
    return bool(data.get("regions") or data.get("conferences"))


def preset_season() -> str:
    return str(_raw_presets().get("season") or "")


def list_conferences() -> list[str]:
    return sorted(_raw_presets().get("conferences", {}).keys())


def list_regions() -> list[str]:
    """Keep NCAA Roman-numeral region order when present."""
    regions = _raw_presets().get("regions", {})
    return list(regions.keys())


def list_preset_options() -> list[str]:
    """Searchable labels: 'Conference · NESCAC', 'Regional · Region I (East)'."""
    out = [f"Conference · {name}" for name in list_conferences()]
    out.extend(f"Regional · {name}" for name in list_regions())
    return out


def parse_preset_option(label: str) -> tuple[PresetKind, str] | None:
    if not label or " · " not in label:
        return None
    prefix, name = label.split(" · ", 1)
    name = name.strip()
    if not name:
        return None
    if prefix == "Conference":
        return ("conference", name)
    if prefix == "Regional":
        return ("region", name)
    return None


def teams_for(kind: PresetKind, name: str, gender: str) -> list[str]:
    """Return TFRRS team names for a conference/region + gender (`m`/`f`)."""
    g = "m" if gender == "m" else "f"
    bucket = "conferences" if kind == "conference" else "regions"
    entry = _raw_presets().get(bucket, {}).get(name)
    if not isinstance(entry, dict):
        return []
    teams = entry.get(g) or []
    return [str(t) for t in teams if t]


def lineup_payload(
    kind: PresetKind,
    name: str,
    gender: str,
    course: str | None = None,
) -> dict[str, Any]:
    """Build a pending_team_load payload for Team Race."""
    teams = [
        {"gender": gender, "team": team}
        for team in teams_for(kind, name, gender)
    ]
    payload: dict[str, Any] = {"teams": teams}
    if course:
        payload["course"] = course
    return payload
