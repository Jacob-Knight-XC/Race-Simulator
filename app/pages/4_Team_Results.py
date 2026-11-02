import streamlit as st

from ui_helpers import apply_theme, get_db, page_header, selected_course, show_table

apply_theme("Team Results · XC Sim")
db = get_db()

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

st.markdown(
    f"""
    <div class="xc-panel">
      <strong>{course}</strong><br/>
      <span class="xc-badge">Rating · {db.describe_course_rating(rating)}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

athletes = []
for gender, team_name, roster in st.session_state.team_tuple:
    for entry in roster:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2 and isinstance(entry[1], int):
            ath_name, athlete_id = entry[0], entry[1]
        else:
            ath_name = entry if isinstance(entry, str) else entry[0]
            team_id = db.get_team_id(team_name, gender)
            athlete_id = db.get_athlete_id(ath_name, team_id)
            if athlete_id is None:
                continue
        athletes.append((gender, team_name, athlete_id, ath_name))

rows = db.sort_by_time(db.predict_many(athletes, course))
scored_rows = [row for row in rows if db.parse_race_seconds(row[3]) is not None]
team_final = db.score_teams([row[1] for row in scored_rows])

st.markdown("#### Team scores")
if team_final:
    show_table(
        {
            "Place": list(range(1, len(team_final) + 1)),
            "Team": [row[0] for row in team_final],
            "Score": [row[1] for row in team_final],
        }
    )
else:
    st.info("Need at least one team with five scoring runners for a team score.")

st.markdown("#### Individual board")
show_table(
    {
        "Place": list(range(1, len(scored_rows) + 1)),
        "Team": [row[1] for row in scored_rows],
        "Athlete": [row[2] for row in scored_rows],
        "Predicted Time": [row[3] for row in scored_rows],
    }
)
