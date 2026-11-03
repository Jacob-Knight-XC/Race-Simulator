import streamlit as st

from ui_helpers import (
    apply_theme,
    content_frame,
    get_db,
    page_header,
    roster_depth_selector,
    selected_course,
    show_table,
)

apply_theme("Team Results · XC Sim")
db = get_db()

with content_frame():
    page_header(
        "Team Results",
        "NCAA team scores from predicted finishes — top five score, top seven displace.",
    )

    if not st.session_state.get("team_tuple"):
        st.warning("Add teams on the Team Race page first.")
        st.link_button("Go to Team Race", "/Team_Race")
        st.stop()

    course = selected_course()
    rating = db.get_course_rating(course)
    depth_limit = roster_depth_selector()

    st.markdown(
        f"""
        <div class="xc-panel">
          <strong>{course}</strong><br/>
          <span class="xc-badge">Rating · {db.describe_course_rating(rating)}</span>
          <span class="xc-badge" style="margin-left:0.4rem;">
            Field · {"Top 10 / team" if depth_limit else "All athletes"}
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    athletes = []
    for gender, team_name, roster in st.session_state.team_tuple:
        for entry in roster:
            if (
                isinstance(entry, (list, tuple))
                and len(entry) >= 2
                and isinstance(entry[1], int)
            ):
                ath_name, athlete_id = entry[0], entry[1]
            else:
                ath_name = entry if isinstance(entry, str) else entry[0]
                team_id = db.get_team_id(team_name, gender)
                athlete_id = db.get_athlete_id(ath_name, team_id)
                if athlete_id is None:
                    continue
            athletes.append((gender, team_name, athlete_id, ath_name))

    rows = db.sort_by_time(db.predict_many(athletes, course))
    limited_rows = db.limit_athletes_per_team(rows, depth_limit)
    analysis = db.analyze_team_meet(limited_rows)
    teams = analysis["teams"]
    incomplete = analysis["incomplete_teams"]
    board = analysis["board"]

    st.markdown("#### Insights")
    for note in analysis["insights"]:
        st.markdown(f"- {note}")

    st.markdown("#### Team scores")
    if teams:
        show_table(
            {
                "Place": [t["place"] for t in teams],
                "Team": [t["team"] for t in teams],
                "Score": [t["score"] for t in teams],
                "Scoring places": [
                    "-".join(str(p) for p in t["scoring_places"]) for t in teams
                ],
                "1–5 spread": [t["spread_1_5_str"] for t in teams],
                "1–7 spread": [t["spread_1_7_str"] for t in teams],
                "Gap to next": [
                    "—" if t["gap_to_next"] is None else t["gap_to_next"] for t in teams
                ],
            }
        )
    else:
        st.info("Need at least one team with five scoring runners for a team score.")

    if incomplete:
        st.caption(
            "Teams short of five scorers: "
            + ", ".join(t["team"] for t in incomplete)
        )

    st.markdown("#### Scoring breakdown")
    for team in teams + incomplete:
        label = team["team"]
        if team["score"] is not None:
            label = f"{team['place']}. {team['team']} — {team['score']} pts"
        else:
            label = f"{team['team']} — incomplete (need 5 scorers)"
        with st.expander(label, expanded=team.get("place") == 1):
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
                        r["scoring_place"] if r["scoring_place"] is not None else "—"
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
