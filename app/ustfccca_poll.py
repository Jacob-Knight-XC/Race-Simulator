"""USTFCCCA National Coaches Poll helpers (NCAA DIII + NAIA)."""

from __future__ import annotations

import json
import re
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
TYPE_NATIONAL_COACHES_POLL = 6

DIVISION_DIII = 2032
DIVISION_NAIA = 2028

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Per-app-division poll config. Keys match app/divisions.py.
POLL_BY_DIVISION: dict[str, dict[str, Any]] = {
    "d3": {
        "api_division": DIVISION_DIII,
        "source": "USTFCCCA NCAA DIII National Coaches Poll",
        "snapshot": DATA_DIR / "ustfccca_national_poll.json",
        "pages": {
            "m": "https://web4.ustfccca.org/iz/polls-rankings/collection/17801",
            "f": "https://web4.ustfccca.org/iz/polls-rankings/collection/17893",
        },
        # USTFCCCA display names → TFRRS / local DB team_name values
        "aliases": {
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
        },
    },
    "naia": {
        "api_division": DIVISION_NAIA,
        "source": "USTFCCCA NAIA National Coaches Poll",
        "snapshot": DATA_DIR / "ustfccca_naia_national_poll.json",
        "pages": {
            "m": "https://web4.ustfccca.org/iz/polls-rankings/collection/17767",
            "f": "https://web4.ustfccca.org/iz/polls-rankings/collection/17859",
        },
        "aliases": {
            "Embry-Riddle (Ariz.)": "Embry-Riddle Arizona",
            "Embry-Riddle": "Embry-Riddle Arizona",
            "Park (Mo.)": "Park U.",
            "IU East (Ind.)": "Indiana East",
            "IU East": "Indiana East",
            "Haskell": "Haskell Indian",
            "Northwest (Wash.)": "Northwest U.",
            "Northwest": "Northwest U.",
            "Lewis-Clark State (Idaho)": "Lewis-Clark",
            "Lewis-Clark State": "Lewis-Clark",
            "Southeastern (Fla.)": "Southeastern U.",
            "Southeastern": "Southeastern U.",
            "Saint Mary (Kan.)": "St. Mary (Kan.)",
            "College of Saint Mary (Neb.)": "St. Mary (Neb.)",
            "College of Saint Mary": "St. Mary (Neb.)",
            "Saint Francis (Ind.)": "St. Francis (Ind.)",
            "Tennessee Southern": "UT Southern",
            "SCAD (Ga.)": "SCAD",
        },
    },
}

# Back-compat for older imports / tests.
TEAM_ALIASES = POLL_BY_DIVISION["d3"]["aliases"]
SNAPSHOT_PATH = POLL_BY_DIVISION["d3"]["snapshot"]
PAGE_MEN = POLL_BY_DIVISION["d3"]["pages"]["m"]
PAGE_WOMEN = POLL_BY_DIVISION["d3"]["pages"]["f"]

# "(Ky.)", "(Mich.)", "(B.C.)", "(Calif.)", "(Ill.)", etc.
_STATE_SUFFIX = re.compile(
    r"""
    \s*\(
      (?:
        [A-Z][a-z]+(?:\.[a-z]+)?\.?   # Ky. / Calif. / Mich.
        | [A-Z]{2}(?:\.[A-Z]{2})?\.?  # BC / B.C.
        | [A-Z]\.[A-Z]\.              # B.C. explicit
      )
    \)\s*$
    """,
    re.VERBOSE,
)


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


def _poll_config(division_key: str = "d3") -> dict[str, Any]:
    key = (division_key or "d3").strip().lower()
    if key in ("diii", "div3", "ncaa-d3", "ncaa_d3"):
        key = "d3"
    if key not in POLL_BY_DIVISION:
        raise ValueError(f"No USTFCCCA poll config for division {division_key!r}")
    return POLL_BY_DIVISION[key]


def strip_ustfccca_state_suffix(name: str) -> str:
    """Remove trailing '(State)' disambiguators USTFCCCA adds to team labels."""
    return _STATE_SUFFIX.sub("", name).strip()


def map_ustfccca_team_name(name: str, division_key: str = "d3") -> str:
    """Map a USTFCCCA team label onto the local TFRRS team_name when known."""
    aliases = _poll_config(division_key)["aliases"]
    if name in aliases:
        return aliases[name]
    stripped = strip_ustfccca_state_suffix(name)
    if stripped in aliases:
        return aliases[stripped]
    if stripped.startswith("Saint "):
        st_form = "St. " + stripped[len("Saint ") :]
        if st_form in aliases:
            return aliases[st_form]
        return st_form
    return stripped if stripped != name else name


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


def fetch_latest_poll(gender: str, division_key: str = "d3") -> dict:
    """
    Live-fetch the latest National Coaches Poll for gender 'm' or 'f'.

    Returns {"teams": [...], "source": "live", "released": ..., "page": url}.
    """
    cfg = _poll_config(division_key)
    sport = SPORT_MEN if gender == "m" else SPORT_WOMEN
    url = API_LATEST.format(
        sport=sport,
        division=cfg["api_division"],
        type_id=TYPE_NATIONAL_COACHES_POLL,
    )
    payload = _http_get_json(url)
    teams = _rows_from_api_payload(payload)
    if not teams:
        raise RuntimeError("USTFCCCA poll response had no ranked teams")
    collection = payload.get("collection") if isinstance(payload, dict) else None
    released = None
    page = cfg["pages"]["m" if gender == "m" else "f"]
    week = None
    if isinstance(collection, dict):
        released = collection.get("release_date")
        week = collection.get("week")
        coll_id = collection.get("id")
        if coll_id:
            page = f"https://web4.ustfccca.org/iz/polls-rankings/collection/{coll_id}"
    return {
        "gender": gender,
        "division": division_key,
        "teams": teams,
        "source": "live",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "page": page,
        "released": released,
        "week": week,
        "label": cfg["source"],
    }


def load_snapshot_poll(
    gender: str,
    path: Optional[Path] = None,
    division_key: str = "d3",
) -> dict:
    """Load a checked-in poll snapshot (offline / API failure fallback)."""
    cfg = _poll_config(division_key)
    snap_path = path or cfg["snapshot"]
    raw = json.loads(Path(snap_path).read_text(encoding="utf-8"))
    block = (raw.get("genders") or {}).get(gender) or {}
    teams = block.get("teams") or []
    if not teams:
        raise RuntimeError(f"No snapshot poll teams for gender={gender}")
    return {
        "gender": gender,
        "division": division_key,
        "teams": teams,
        "source": "snapshot",
        "fetched_at": raw.get("fetched_at"),
        "released": block.get("released"),
        "page": block.get("page")
        or cfg["pages"]["m" if gender == "m" else "f"],
        "week": block.get("week"),
        "label": raw.get("source") or cfg["source"],
    }


def get_national_poll(gender: str, division_key: str = "d3") -> dict:
    """Prefer live USTFCCCA poll; fall back to the repo snapshot."""
    try:
        return fetch_latest_poll(gender, division_key=division_key)
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        RuntimeError,
        ValueError,
    ):
        return load_snapshot_poll(gender, division_key=division_key)


def write_snapshot(
    path: Optional[Path] = None, division_key: str = "d3"
) -> Path:
    """Refresh the checked-in snapshot from the live API (men + women)."""
    cfg = _poll_config(division_key)
    snap_path = Path(path) if path else cfg["snapshot"]
    men = fetch_latest_poll("m", division_key=division_key)
    women = fetch_latest_poll("f", division_key=division_key)
    payload = {
        "source": cfg["source"],
        "division": division_key,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "genders": {
            "m": {
                "released": men.get("released"),
                "page": men.get("page"),
                "week": men.get("week"),
                "teams": men["teams"],
            },
            "f": {
                "released": women.get("released"),
                "page": women.get("page"),
                "week": women.get("week"),
                "teams": women["teams"],
            },
        },
    }
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return snap_path


def write_all_snapshots() -> list[Path]:
    """Refresh DIII + NAIA poll snapshots."""
    return [write_snapshot(division_key=key) for key in POLL_BY_DIVISION]
