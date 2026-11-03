"""USTFCCCA NCAA DIII National Coaches Poll helpers."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# USTFCCCA Polls & Rankings API (web4)
API_LATEST = (
    "https://web4.ustfccca.org/iz/polls-rankings/api/v1/rankings/latest"
    "?sport={sport}&division={division}&type={type_id}"
)
SPORT_MEN = 8
SPORT_WOMEN = 9
DIVISION_DIII = 2032
TYPE_NATIONAL_COACHES_POLL = 6

PAGE_MEN = "https://web4.ustfccca.org/iz/polls-rankings/collection/17801"
PAGE_WOMEN = "https://web4.ustfccca.org/iz/polls-rankings/collection/17893"

# USTFCCCA display names → TFRRS / local DB team_name values
TEAM_ALIASES = {
    "UW-La Crosse": "Wis.-La Crosse",
    "UW-Stevens Point": "Wis.-Stevens Point",
    "UW-Eau Claire": "Wis.-Eau Claire",
    "UW-Oshkosh": "Wis.-Oshkosh",
    "UW-Whitewater": "Wis.-Whitewater",
    "UW-Platteville": "Wis.-Platteville",
    "UW-River Falls": "Wis.-River Falls",
    "UW-Stout": "Wis.-Stout",
    "Washington (Mo.)": "Washington U.",
    "Wesleyan (Conn.)": "Wesleyan",
    "Central (Iowa)": "Central College",
    "Chicago": "U. of Chicago",
    "Trinity (Texas)": "Trinity (Tex.)",
    "Case Western Reserve": "Case Western",
}

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "ustfccca_national_poll.json"


def _http_get_json(url: str, timeout: float = 20.0) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "XC-Race-Simulator/1.0 (+https://github.com/Jacob-Knight-XC/Race-Simulator)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def map_ustfccca_team_name(name: str) -> str:
    """Map a USTFCCCA team label onto the local TFRRS team_name when known."""
    if name in TEAM_ALIASES:
        return TEAM_ALIASES[name]
    return name


def _rows_from_api_payload(payload: Any) -> list[dict]:
    rows = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    ranked: list[dict] = []
    for row in rows:
        rank = row.get("rank")
        name = row.get("team_name") or row.get("name")
        if rank is None or not name:
            continue
        ranked.append(
            {
                "rank": int(rank),
                "name": str(name),
                "points": row.get("score"),
                "conference": row.get("conference"),
                "region": row.get("region"),
            }
        )
    ranked.sort(key=lambda item: (item["rank"], item["name"]))
    return ranked


def fetch_latest_poll(gender: str) -> dict:
    """
    Live-fetch the latest NCAA DIII National Coaches Poll for gender 'm' or 'f'.

    Returns {"teams": [...], "source": "live", "released": None, "page": url}.
    """
    sport = SPORT_MEN if gender == "m" else SPORT_WOMEN
    url = API_LATEST.format(
        sport=sport, division=DIVISION_DIII, type_id=TYPE_NATIONAL_COACHES_POLL
    )
    payload = _http_get_json(url)
    teams = _rows_from_api_payload(payload)
    if not teams:
        raise RuntimeError("USTFCCCA poll response had no ranked teams")
    return {
        "gender": gender,
        "teams": teams,
        "source": "live",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "page": PAGE_MEN if gender == "m" else PAGE_WOMEN,
        "released": None,
    }


def load_snapshot_poll(gender: str, path: Optional[Path] = None) -> dict:
    """Load a checked-in poll snapshot (offline / API failure fallback)."""
    snap_path = path or SNAPSHOT_PATH
    raw = json.loads(snap_path.read_text(encoding="utf-8"))
    block = (raw.get("genders") or {}).get(gender) or {}
    teams = block.get("teams") or []
    if not teams:
        raise RuntimeError(f"No snapshot poll teams for gender={gender}")
    return {
        "gender": gender,
        "teams": teams,
        "source": "snapshot",
        "fetched_at": raw.get("fetched_at"),
        "released": block.get("released"),
        "page": block.get("page") or (PAGE_MEN if gender == "m" else PAGE_WOMEN),
        "week": block.get("week"),
    }


def get_national_poll(gender: str) -> dict:
    """Prefer live USTFCCCA poll; fall back to the repo snapshot."""
    try:
        return fetch_latest_poll(gender)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, ValueError):
        return load_snapshot_poll(gender)


def write_snapshot(path: Optional[Path] = None) -> Path:
    """Refresh the checked-in snapshot from the live API (men + women)."""
    snap_path = path or SNAPSHOT_PATH
    men = fetch_latest_poll("m")
    women = fetch_latest_poll("f")
    payload = {
        "source": "USTFCCCA NCAA DIII National Coaches Poll",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "genders": {
            "m": {
                "released": men.get("released"),
                "page": men.get("page"),
                "teams": men["teams"],
            },
            "f": {
                "released": women.get("released"),
                "page": women.get("page"),
                "teams": women["teams"],
            },
        },
    }
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return snap_path
