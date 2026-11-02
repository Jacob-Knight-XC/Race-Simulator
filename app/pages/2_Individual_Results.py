import streamlit as st

from ui_helpers import get_db, show_table, selected_course

db = get_db()

st.title("Individual Results")
st.subheader("Predicted individual finishes")

if not st.session_state.get("athlete_lst"):
    st.warning("Add athletes on the Individual Race page first.")
    st.stop()

course = selected_course()
rating = db.get_course_rating(course)
gender0 = st.session_state.gender_lst[0]
st.write(f"Course: **{course}** — rating {db.describe_course_rating(rating)}")
st.caption(
    "Predictions convert race history to an equivalent "
    f"{db.TARGET_LABEL.get(gender0, 'race')} time with Riegel scaling, "
    "recency/form weighting, and course difficulty."
)

athletes = []
for gender, team, athlete in zip(
    st.session_state.gender_lst,
    st.session_state.team_lst,
    st.session_state.athlete_lst,
):
    team_id = db.get_team_id(team, gender)
    athlete_id = db.get_athlete_id(athlete, team_id)
    if athlete_id is not None:
        athletes.append((gender, team, athlete_id, athlete))

rows = db.sort_by_time(db.predict_many(athletes, course))

show_table({
        "Place": list(range(1, len(rows) + 1)),
        "Team Name": [r[1] for r in rows],
        "Athlete Name": [r[2] for r in rows],
        "Predicted Time": [r[3] for r in rows],
    })
