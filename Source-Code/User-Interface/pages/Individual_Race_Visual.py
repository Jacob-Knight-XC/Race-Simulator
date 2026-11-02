from data_pull import DB
import streamlit as st

db = DB("racedata.db")

st.title("Individual Simulation")
st.subheader("Predicted individual results")

if "athlete_lst" not in st.session_state or not st.session_state.athlete_lst:
    st.warning("Add athletes on the Individual Race page first.")
    st.stop()

course = st.session_state.get("selected_course", "Average / Neutral")
rating = db.get_course_rating(course)
st.write(f"Course: **{course}** — rating {db.describe_course_rating(rating)}")
st.caption(
    "Predictions convert each athlete's race history to an equivalent "
    f"{db.TARGET_LABEL.get(st.session_state.gender_lst[0], 'race')} time "
    "with Riegel scaling, recency/form weighting, and course difficulty."
)

tuple_lst = []
for i in range(len(st.session_state.gender_lst)):
    gender = st.session_state.gender_lst[i]
    team = st.session_state.team_lst[i]
    athlete = st.session_state.athlete_lst[i]

    team_id = db.get_team_id(team, gender)
    athlete_id = db.get_athlete_id(athlete, team_id)
    race_time_lst = db.get_athlete_races(athlete_id)
    predicted = db.predict_race_time(race_time_lst, gender, course)
    tuple_lst.append([gender, team, athlete, predicted])

sorted_lst = db.Sort(tuple_lst)

place = []
team_col = []
athlete_col = []
racetime = []
for i, row in enumerate(sorted_lst):
    place.append(i + 1)
    team_col.append(row[1])
    athlete_col.append(row[2])
    racetime.append(row[3])

st.table(
    {
        "Place": place,
        "Team Name": team_col,
        "Athlete Name": athlete_col,
        "Predicted Time": racetime,
    }
)

st.markdown(
    """
    <style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
    """,
    unsafe_allow_html=True,
)
