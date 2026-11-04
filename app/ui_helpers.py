"""Shared Streamlit helpers and visual system for the race simulator."""

from __future__ import annotations

import inspect
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import streamlit as st

from race_db import RaceDB

NEUTRAL_COURSE = "Average / Neutral"

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Sora:wght@400;500;600;700&display=swap');

:root {
  --pine: #12352c;
  --pine-deep: #0b241e;
  --canopy: #1f6b4f;
  --fog: #eef3f0;
  --chalk: #f7faf8;
  --ink: #15241f;
  --muted: #5b6d66;
  --signal: #c98512;
  --line: rgba(18, 53, 44, 0.12);
}

html, body, [class*="css"] {
  font-family: "Sora", sans-serif;
  color: var(--ink);
}

.stApp {
  background:
    radial-gradient(1200px 500px at 12% -10%, rgba(31, 107, 79, 0.18), transparent 55%),
    radial-gradient(900px 420px at 88% 0%, rgba(201, 133, 18, 0.12), transparent 50%),
    linear-gradient(180deg, #e7efea 0%, #eef3f0 42%, #f4f7f5 100%);
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg width='160' height='80' viewBox='0 0 160 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 60 C30 40, 50 70, 80 50 S130 20, 160 35' fill='none' stroke='%1212352c' stroke-width='2'/%3E%3Cpath d='M0 30 C40 10, 70 45, 100 25 S140 5, 160 18' fill='none' stroke='%1212352c' stroke-width='1.5'/%3E%3C/svg%3E");
  background-size: 320px 160px;
  z-index: 0;
}

[data-testid="stHeader"] {
  background: transparent;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f2f27 0%, #12352c 100%);
  border-right: 1px solid rgba(255,255,255,0.06);
}

[data-testid="stSidebar"] * {
  color: #e8f2ec !important;
}

[data-testid="stSidebarNav"] a {
  border-radius: 10px !important;
  margin: 0.15rem 0.4rem !important;
  font-family: "Sora", sans-serif !important;
  font-weight: 500 !important;
}

[data-testid="stSidebarNav"] a:hover {
  background: rgba(255,255,255,0.08) !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
  background: rgba(201, 133, 18, 0.22) !important;
  box-shadow: inset 3px 0 0 var(--signal);
}

/* Prefer Streamlit's centered layout; reinforce gutters if theme tries to go wide. */
div.stMainBlockContainer.block-container,
[data-testid="stMainBlockContainer"] {
  max-width: 100% !important;
  width: 100% !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  padding-top: 0.85rem !important;
  padding-bottom: 3.5rem !important;
  padding-left: 1.25rem !important;
  padding-right: 1.25rem !important;
  box-sizing: border-box !important;
}

.xc-hero {
  position: relative;
  width: 100%;
  margin: 0 0 2.25rem 0;
  min-height: 0;
  padding: 1.75rem clamp(1.35rem, 3.5vw, 2.25rem) 1.85rem;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  border-radius: 0;
  overflow: hidden;
  color: #f4faf7;
  background:
    linear-gradient(115deg, rgba(11, 36, 30, 0.94) 0%, rgba(18, 53, 44, 0.78) 52%, rgba(31, 107, 79, 0.45) 100%),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1600' height='900' viewBox='0 0 1600 900'%3E%3Crect fill='%120b241e' width='1600' height='900'/%3E%3Cpath d='M0 620 C220 540, 360 700, 560 610 S920 480, 1120 560 1440 700, 1600 620 L1600 900 L0 900 Z' fill='%121f6b4f' opacity='.35'/%3E%3Cpath d='M0 700 C260 640, 420 780, 680 700 S1100 560, 1340 660 1520 760, 1600 720 L1600 900 L0 900 Z' fill='%12c98512' opacity='.16'/%3E%3C/svg%3E");
  background-size: cover;
  background-position: center;
  animation: xc-rise 700ms ease-out both;
}

.xc-hero-inner {
  width: 100%;
  max-width: 40rem;
}

.xc-hero::after {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 4px;
  background: linear-gradient(90deg, var(--signal), transparent 70%);
}

.xc-brand {
  font-family: "Barlow Condensed", sans-serif;
  font-weight: 700;
  font-size: clamp(3.2rem, 7vw, 4.6rem);
  letter-spacing: 0.045em;
  line-height: 0.92;
  margin: 0 0 0.7rem 0;
  text-transform: uppercase;
  color: #f7fbf8 !important;
  text-shadow: 0 10px 40px rgba(0, 0, 0, 0.28);
}

.xc-kicker {
  display: inline-block;
  font-family: "Barlow Condensed", sans-serif;
  font-size: 0.95rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #f0d089;
  margin: 0 0 0.45rem 0;
}

.xc-lede {
  max-width: 34rem;
  font-size: 1.02rem;
  line-height: 1.5;
  color: rgba(244, 250, 247, 0.88);
  margin: 0 0 1.1rem 0;
}

.xc-cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.xc-cta {
  display: inline-block;
  padding: 0.7rem 1.15rem;
  border: 1px solid rgba(255,255,255,0.35);
  color: #fff !important;
  text-decoration: none !important;
  font-family: "Barlow Condensed", sans-serif;
  font-size: 1.05rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  transition: background 160ms ease, border-color 160ms ease, transform 160ms ease;
}

.xc-cta:hover {
  background: rgba(201, 133, 18, 0.28);
  border-color: #f0d089;
  transform: translateY(-1px);
}

.xc-cta-primary {
  background: var(--signal);
  border-color: var(--signal);
  color: #1a1408 !important;
}

.xc-section {
  margin: 2.25rem 0 1rem;
  animation: xc-fade 650ms ease-out both;
}

.xc-section h2, .xc-section-title {
  font-family: "Barlow Condensed", sans-serif;
  font-weight: 650;
  font-size: 2rem;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--pine);
  margin: 0 0 0.35rem 0;
}

.xc-section p, .xc-section-copy {
  color: var(--muted);
  max-width: 40rem;
  margin: 0 0 1.1rem 0;
}

.xc-panel {
  background: rgba(247, 250, 248, 0.78);
  border: 1px solid var(--line);
  border-left: 3px solid var(--canopy);
  padding: 1.1rem 1.2rem;
  margin: 0.85rem 0 1.25rem;
  backdrop-filter: blur(6px);
}

.xc-metric-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0 1.5rem;
}

.xc-metric {
  padding: 0.9rem 1rem;
  background: rgba(247, 250, 248, 0.9);
  border-top: 2px solid var(--canopy);
}

.xc-metric-label {
  font-family: "Barlow Condensed", sans-serif;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 0.85rem;
  color: var(--muted);
}

.xc-metric-value {
  font-family: "Barlow Condensed", sans-serif;
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--pine);
  line-height: 1.1;
  margin-top: 0.2rem;
}

.xc-badge {
  display: inline-block;
  font-family: "Barlow Condensed", sans-serif;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.9rem;
  padding: 0.2rem 0.55rem;
  border: 1px solid var(--line);
  color: var(--pine);
  background: rgba(255,255,255,0.55);
}

h1, h2, h3 {
  font-family: "Barlow Condensed", sans-serif !important;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--pine) !important;
}

h1.xc-brand,
.xc-brand {
  color: #f7fbf8 !important;
}

div[data-testid="stRadio"] label,
div[data-testid="stSelectbox"] label,
.stTextInput label {
  font-family: "Barlow Condensed", sans-serif !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.9rem !important;
  color: var(--muted) !important;
}

.stButton > button {
  font-family: "Barlow Condensed", sans-serif !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: 0 !important;
  border: 1px solid var(--pine) !important;
  background: var(--pine) !important;
  color: #f4faf7 !important;
  transition: transform 140ms ease, background 140ms ease;
}

.stButton > button:hover {
  background: var(--canopy) !important;
  transform: translateY(-1px);
}

[data-testid="stDataFrame"] {
  border: 1px solid var(--line);
  background: rgba(247, 250, 248, 0.92);
}

@keyframes xc-rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes xc-fade {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .xc-hero { padding: 1.35rem 1.15rem 1.5rem; }
  .xc-brand { font-size: 2.75rem; }
}
</style>
"""


@st.cache_resource
def get_db() -> RaceDB:
    return RaceDB()


def _db_mtime(db_path: str) -> float:
    try:
        return Path(db_path).stat().st_mtime
    except OSError:
        return 0.0


@st.cache_data(show_spinner="Simulating national field…", ttl=3600)
def cached_flat_gender_field(gender: str, db_path: str, db_mtime: float) -> list:
    """
    Neutral-course predictions for an entire gender.

    Course is applied later via scale_predictions_to_course so switching
    courses does not re-predict thousands of athletes.
    """
    return RaceDB(db_path).simulate_gender_field(gender, None)


def national_flat_field(gender: str) -> list:
    db = get_db()
    return cached_flat_gender_field(gender, db.path, _db_mtime(db.path))


def cached_top_teams_race(
    gender: str, course: str, n_teams: int = 30, per_team: int = 7
) -> dict:
    db = get_db()
    flat = national_flat_field(gender)
    return db.top_teams_race(
        gender,
        course,
        n_teams=n_teams,
        per_team=per_team,
        field=flat,
    )


@st.cache_data(show_spinner="Loading USTFCCCA national poll…", ttl=3600)
def cached_ustfccca_poll(gender: str) -> dict:
    from ustfccca_poll import get_national_poll

    return get_national_poll(gender)


def resolve_poll_teams_for_db(db: RaceDB, gender: str, poll: dict) -> list[dict]:
    """Map USTFCCCA poll labels onto local DB team names."""
    from ustfccca_poll import map_ustfccca_team_name

    known = {name for name, _team_id in db.get_teams(gender)}
    resolved: list[dict] = []
    for entry in poll.get("teams") or []:
        ust_name = entry.get("name")
        rank = entry.get("rank")
        if not ust_name or rank is None:
            continue
        mapped = map_ustfccca_team_name(ust_name)
        db_name = mapped if mapped in known else (ust_name if ust_name in known else None)
        resolved.append(
            {
                "rank": int(rank),
                "ustfccca_name": ust_name,
                "name": db_name or mapped,
                "matched": db_name is not None,
                "points": entry.get("points"),
            }
        )
    return resolved


@st.cache_data(show_spinner="Simulating USTFCCCA Top 30…", ttl=3600)
def _cached_ustfccca_top_teams_race(
    gender: str, course: str, per_team: int, db_path: str, db_mtime: float
) -> dict:
    """Cached Top 30 sim; db_mtime busts the cache when racedata.db changes."""
    db = RaceDB(db_path)
    from ustfccca_poll import get_national_poll

    poll = get_national_poll(gender)
    resolved = resolve_poll_teams_for_db(db, gender, poll)
    ranked = [row for row in resolved if row["matched"]]
    result = db.race_ranked_teams(
        gender, ranked, course_meet=course, per_team=per_team
    )
    result["poll"] = poll
    result["poll_resolved"] = resolved
    return result


def cached_ustfccca_top_teams_race(
    gender: str, course: str, per_team: int = 7
) -> dict:
    """Race the USTFCCCA Top 30 (not a full-field national sim)."""
    db = get_db()
    return _cached_ustfccca_top_teams_race(
        gender, course, per_team, db.path, _db_mtime(db.path)
    )


def cached_top_athletes(gender: str, course: str, limit: int = 100) -> list:
    db = get_db()
    flat = national_flat_field(gender)
    return db.top_athletes_field(gender, course, limit=limit, field=flat)


def render_team_meet_analysis(
    analysis: dict, *, show_incomplete: bool = True, expand_winner: bool = True
) -> None:
    """Shared Team Results / national team-race tables and breakdown."""
    teams = analysis.get("teams") or []
    incomplete = analysis.get("incomplete_teams") or [] if show_incomplete else []
    board = analysis.get("board") or []

    st.markdown("#### Insights")
    for note in analysis.get("insights") or []:
        st.markdown(f"- {note}")

    st.markdown("#### Team scores")
    if teams:
        payload = {
            "Place": [t["place"] for t in teams],
            "Team": [t["team"] for t in teams],
            "Score": [t["score"] for t in teams],
            "Scoring places": [
                "-".join(str(p) for p in t["scoring_places"]) for t in teams
            ],
            "1–5 spread": [t["spread_1_5_str"] for t in teams],
            "1–7 spread": [t["spread_1_7_str"] for t in teams],
            "Gap to next": [
                "—" if t["gap_to_next"] is None else str(t["gap_to_next"])
                for t in teams
            ],
        }
        if any(t.get("national_rank") for t in teams):
            payload = {
                "Place": payload["Place"],
                "Nat'l #": [
                    "—" if t.get("national_rank") is None else str(t["national_rank"])
                    for t in teams
                ],
                "Team": payload["Team"],
                "Score": payload["Score"],
                "Scoring places": payload["Scoring places"],
                "1–5 spread": payload["1–5 spread"],
                "1–7 spread": payload["1–7 spread"],
                "Gap to next": payload["Gap to next"],
            }
        show_table(payload)
    else:
        st.info("Need at least one team with five scoring runners for a team score.")

    if incomplete:
        st.caption(
            "Teams short of five scorers: "
            + ", ".join(t["team"] for t in incomplete)
        )

    st.markdown("#### Scoring breakdown")
    for team in teams + incomplete:
        if team.get("score") is not None:
            label = f"{team['place']}. {team['team']} — {team['score']} pts"
        else:
            label = f"{team['team']} — incomplete (need 5 scorers)"
        with st.expander(
            label, expanded=expand_winner and team.get("place") == 1
        ):
            scorers = ", ".join(team["scorer_names"]) or "—"
            displacers = ", ".join(team["displacer_names"]) or "—"
            st.markdown(
                f"**Scorers (1–5):** {scorers}  \n"
                f"**Displacers (6–7):** {displacers}  \n"
                f"**1–5 spread:** {team['spread_1_5_str']}  ·  "
                f"**1–7 spread:** {team['spread_1_7_str']}"
            )
            show_table(
                {
                    "Team #": [r["team_order"] for r in team["runners"]],
                    "Race place": [r["race_place"] for r in team["runners"]],
                    "Role": [r["role"] for r in team["runners"]],
                    "Athlete": [r["athlete"] for r in team["runners"]],
                    "Predicted Time": [r["time"] for r in team["runners"]],
                    "Scoring place": [
                        "—"
                        if r["scoring_place"] is None
                        else str(r["scoring_place"])
                        for r in team["runners"]
                    ],
                }
            )

    st.markdown("#### Individual board")
    show_table(
        {
            "Place": [r["race_place"] for r in board],
            "Team": [r["team"] for r in board],
            "Athlete": [r["athlete"] for r in board],
            "Predicted Time": [r["time"] for r in board],
            "Role": [r["role"] for r in board],
            "Team #": [r["team_order"] for r in board],
        }
    )


def apply_theme(page_title: str = "XC Race Simulator") -> None:
    st.set_page_config(
        page_title=page_title,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def stretch_kwargs() -> dict:
    """Prefer width='stretch'; fall back for older Streamlit installs."""
    params = set(inspect.signature(st.button).parameters)
    if "width" in params:
        return {"width": "stretch"}
    return {"use_container_width": True}


def show_table(data: dict) -> None:
    """Render a compact results table without a pandas index column."""
    # Stringify cells so Arrow never sees mixed int/"—" columns.
    clean = {
        key: [("" if value is None else str(value)) for value in values]
        for key, values in data.items()
    }
    kwargs = {"hide_index": True}
    df_params = set(inspect.signature(st.dataframe).parameters)
    if "width" in df_params:
        kwargs["width"] = "stretch"
    else:
        kwargs["use_container_width"] = True
    st.dataframe(clean, **kwargs)


ROSTER_DEPTH_TOP7 = "Top 7"
ROSTER_DEPTH_TOP10 = "Top 10"
ROSTER_DEPTH_ALL = "All athletes"
ROSTER_DEPTH_OPTIONS = (ROSTER_DEPTH_TOP7, ROSTER_DEPTH_TOP10, ROSTER_DEPTH_ALL)
ROSTER_DEPTH_LIMITS = {
    ROSTER_DEPTH_TOP7: 7,
    ROSTER_DEPTH_TOP10: 10,
    ROSTER_DEPTH_ALL: None,
}


def ensure_session_defaults() -> None:
    defaults = {
        "gender_lst": [],
        "team_lst": [],
        "athlete_lst": [],
        "team_tuple": [],
        "selected_course": NEUTRAL_COURSE,
        "team_roster_depth": ROSTER_DEPTH_TOP7,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    # Migrate older sessions that stored a removed/unknown depth choice.
    if st.session_state.get("team_roster_depth") not in ROSTER_DEPTH_OPTIONS:
        st.session_state["team_roster_depth"] = ROSTER_DEPTH_TOP7


def roster_depth_limit_for(choice: str | None) -> int | None:
    return ROSTER_DEPTH_LIMITS.get(choice or ROSTER_DEPTH_TOP7, 7)


def roster_depth_label(limit: int | None) -> str:
    if limit is None:
        return "All athletes"
    return f"Top {limit} / team"


def roster_depth_selector(key: str = "team_roster_depth") -> int | None:
    """Toggle how many predicted runners per team enter the scored field."""
    ensure_session_defaults()
    st.radio(
        "Athletes per team",
        list(ROSTER_DEPTH_OPTIONS),
        horizontal=True,
        key=key,
        help="Keep each team’s fastest predicted runners before NCAA scoring. "
        "Top 7 matches a typical scoring/displacing lineup.",
    )
    return roster_depth_limit_for(st.session_state.get(key))


def roster_depth_limit() -> int | None:
    ensure_session_defaults()
    return roster_depth_limit_for(st.session_state.get("team_roster_depth"))


def clear_individual_field() -> None:
    st.session_state.gender_lst = []
    st.session_state.team_lst = []
    st.session_state.athlete_lst = []


def clear_team_field() -> None:
    st.session_state.team_tuple = []


def course_selector(db: RaceDB, key: str = "course_picker") -> str:
    """Searchable course dropdown + rating caption; persist selection."""
    ensure_session_defaults()
    meet_options = [NEUTRAL_COURSE] + db.get_meet_names()
    current = st.session_state["selected_course"]
    if current not in meet_options:
        # Year-stripped / venue-keyed renames after a DB refresh.
        normalized = {db.normalize_meet_key(name): name for name in meet_options}
        current = normalized.get(db.normalize_meet_key(current), NEUTRAL_COURSE)
        st.session_state["selected_course"] = current
    course = course_selectbox_searchable(meet_options, current, key=key)
    st.session_state["selected_course"] = course
    rating = db.describe_course_rating(db.get_course_rating(course))
    badges = [f'<span class="xc-badge">Course rating · {rating}</span>']
    meta = db.get_meet_meta(course)
    if meta.get("city") or meta.get("state") or meta.get("venue_name"):
        place = ", ".join(
            p for p in (meta.get("venue_name"), meta.get("city"), meta.get("state")) if p
        )
        badges.append(f'<span class="xc-badge">{place}</span>')
    if meta.get("elevation_m") is not None:
        badges.append(
            f'<span class="xc-badge">Elev · {int(round(meta["elevation_m"]))} m</span>'
        )
    if meta.get("temp_c") is not None or meta.get("precip_mm") is not None:
        bits = []
        if meta.get("temp_c") is not None:
            bits.append(f"{meta['temp_c']:.0f}°C")
        if meta.get("precip_mm") is not None:
            bits.append(f"{meta['precip_mm']:.1f} mm precip")
        badges.append(f'<span class="xc-badge">Weather · {" · ".join(bits)}</span>')
    st.markdown(" ".join(badges), unsafe_allow_html=True)
    return course


def selected_course() -> str:
    ensure_session_defaults()
    return st.session_state.get("selected_course", NEUTRAL_COURSE)


def page_header(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="xc-section">
          <h2 class="xc-section-title">{title}</h2>
          <p class="xc-section-copy">{copy}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def content_frame() -> Iterator[None]:
    """Content uses the full main pane; side gap comes from container padding only."""
    yield


def metric_row(items: list[tuple[str, str]]) -> None:
    cells = "".join(
        f'<div class="xc-metric"><div class="xc-metric-label">{label}</div>'
        f'<div class="xc-metric-value">{value}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="xc-metric-row">{cells}</div>', unsafe_allow_html=True)


def gender_selector(label: str = "Gender", key: str | None = None) -> str:
    kwargs = {"horizontal": True}
    if key is not None:
        kwargs["key"] = key
    choice = st.radio(label, ("Men", "Women"), **kwargs)
    return "m" if choice == "Men" else "f"


DEFAULT_TEAM = "Wartburg"

# Newer Streamlit builds support searchable selectboxes via filter_mode.
# Older installs (common on Windows) do not — only pass supported kwargs.
_SELECTBOX_PARAMS = set(inspect.signature(st.selectbox).parameters)


def selectbox_compat(label: str, options, **kwargs):
    """st.selectbox wrapper that ignores unsupported kwargs like filter_mode."""
    safe = {k: v for k, v in kwargs.items() if k in _SELECTBOX_PARAMS}
    return st.selectbox(label, options, **safe)


def team_selectbox(
    team_names: list[str],
    label: str = "Team",
    preferred: str = DEFAULT_TEAM,
    key: str | None = None,
) -> str:
    """Team picker with alma-mater default; fuzzy search when Streamlit supports it."""
    if not team_names:
        selectbox_compat(label, ["—"], key=key, disabled=True)
        return ""
    if key and key not in st.session_state:
        st.session_state[key] = preferred if preferred in team_names else team_names[0]
    kwargs = {
        "placeholder": "Type to search teams…",
        "filter_mode": "fuzzy",
    }
    if key:
        kwargs["key"] = key
    else:
        kwargs["index"] = (
            team_names.index(preferred) if preferred in team_names else 0
        )
    return selectbox_compat(label, team_names, **kwargs)


def athlete_selectbox(
    athlete_names: list[str],
    label: str = "Athlete",
    key: str | None = None,
) -> str | None:
    """Athlete picker for the current roster; fuzzy search when supported."""
    if not athlete_names:
        selectbox_compat(label, ["—"], key=key, disabled=True)
        return None
    if key and key not in st.session_state:
        st.session_state[key] = athlete_names[0]
    elif key and st.session_state.get(key) not in athlete_names:
        st.session_state[key] = athlete_names[0]
    kwargs = {
        "placeholder": "Type to search athletes…",
        "filter_mode": "fuzzy",
    }
    if key:
        kwargs["key"] = key
    return selectbox_compat(label, athlete_names, **kwargs)


def course_selectbox_searchable(
    meet_options: list[str],
    current: str,
    key: str = "course_picker",
) -> str:
    if key not in st.session_state:
        st.session_state[key] = current if current in meet_options else meet_options[0]
    elif st.session_state[key] not in meet_options:
        st.session_state[key] = meet_options[0]
    return selectbox_compat(
        "Course",
        meet_options,
        key=key,
        placeholder="Type to search courses…",
        filter_mode="fuzzy",
    )
