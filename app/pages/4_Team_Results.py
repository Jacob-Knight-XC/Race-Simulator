import streamlit as st

from ui_helpers import get_db, show_table, selected_course

db = get_db()

st.title("Team Results")
st.subheader("Predicted team finishes")

if not st.session_state.get("team_tuple"):
    st.warning("Add teams on the Team Race page first.")
    st.stop()

course = selected_course()
rating = db.get_course_rating(course)
st.write(f"Course: **{course}** — rating {db.describe_course_rating(rating)}")
st.caption(
    "Each athlete uses the weighted Riegel prediction; NCAA scoring applies "
    "(top 5 score, top 7 displace)."
)

athletes = []
for gender, team_name, roster in st.session_state.team_tuple:
    for entry in roster:
        # Support both legacy [name, ...] and current (name, athlete_id)
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

team_order = [row[1] for row in scored_rows]
team_final = db.score_teams(team_order)

if team_final:
    show_table({
            "Place": list(range(1, len(team_final) + 1)),
            "Team Name": [row[0] for row in team_final],
            "Score": [row[1] for row in team_final],
        }
    )
else:
    st.info("Need at least one team with five scoring runners for a team score.")

show_table(
    {
        "Place": list(range(1, len(scored_rows) + 1)),
        "Team Name": [row[1] for row in scored_rows],
        "Athlete Name": [row[2] for row in scored_rows],
        "Predicted Time": [row[3] for row in scored_rows],
    }
)
