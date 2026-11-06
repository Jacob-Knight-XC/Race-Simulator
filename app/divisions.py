"""College-division registry: separate TFRRS league → separate SQLite DB."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

APP_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Division:
    key: str
    label: str
    short: str
    tfrrs_league_id: int
    db_filename: str
    # "ustfccca" = National Coaches Poll field; "model" = strongest predicted teams
    national_teams_mode: str
    poll_snapshot: Optional[str] = None

    @property
    def db_path(self) -> Path:
        return APP_DIR / self.db_filename

    @property
    def tfrrs_league_url(self) -> str:
        return f"https://tfrrs.org/leagues/{self.tfrrs_league_id}.html"


DIVISIONS: dict[str, Division] = {
    "d3": Division(
        key="d3",
        label="NCAA Division III",
        short="DIII",
        tfrrs_league_id=51,
        db_filename="racedata.db",
        national_teams_mode="ustfccca",
        poll_snapshot="ustfccca_national_poll.json",
    ),
    "naia": Division(
        key="naia",
        label="NAIA",
        short="NAIA",
        tfrrs_league_id=53,
        db_filename="racedata-naia.db",
        national_teams_mode="ustfccca",
        poll_snapshot="ustfccca_naia_national_poll.json",
    ),
}

# Aliases for CLI / spider `-a division=…`
DIVISION_ALIASES = {
    "d3": "d3",
    "diii": "d3",
    "div3": "d3",
    "ncaa-d3": "d3",
    "ncaa_d3": "d3",
    "naia": "naia",
}

DEFAULT_DIVISION = "d3"
DIVISION_ORDER = ("d3", "naia")


def normalize_division_key(value: str | None) -> str:
    if not value:
        return DEFAULT_DIVISION
    key = DIVISION_ALIASES.get(str(value).strip().lower())
    if key is None:
        raise ValueError(
            f"Unknown division {value!r}. "
            f"Expected one of: {', '.join(DIVISION_ORDER)}"
        )
    return key


def get_division(key: str | None = None) -> Division:
    return DIVISIONS[normalize_division_key(key)]


def db_path_for(key: str | None = None) -> Path:
    return get_division(key).db_path


def league_id_for(key: str | None = None) -> int:
    return get_division(key).tfrrs_league_id
