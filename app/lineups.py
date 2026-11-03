"""Persist saved individual and team race lineups to disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LINEUPS_PATH = Path(__file__).resolve().parent / "saved_lineups.json"

EMPTY: dict[str, dict[str, Any]] = {"individual": {}, "team": {}}


def _read() -> dict[str, dict[str, Any]]:
    if not LINEUPS_PATH.exists():
        return {"individual": {}, "team": {}}
    try:
        data = json.loads(LINEUPS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"individual": {}, "team": {}}
    return {
        "individual": dict(data.get("individual") or {}),
        "team": dict(data.get("team") or {}),
    }


def _write(data: dict[str, dict[str, Any]]) -> None:
    LINEUPS_PATH.write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def list_lineups(kind: str) -> list[str]:
    return sorted(_read().get(kind, {}).keys(), key=str.lower)


def get_lineup(kind: str, name: str) -> dict[str, Any] | None:
    return _read().get(kind, {}).get(name)


def save_lineup(kind: str, name: str, payload: dict[str, Any]) -> None:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Lineup name is required")
    data = _read()
    bucket = data.setdefault(kind, {})
    bucket[cleaned] = payload
    _write(data)


def delete_lineup(kind: str, name: str) -> None:
    data = _read()
    bucket = data.get(kind, {})
    if name in bucket:
        del bucket[name]
        _write(data)
