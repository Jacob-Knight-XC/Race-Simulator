from data_pull import DB
import streamlit as st

db = DB("racedata.db")

st.title("Team Simulation")
st.subheader("Predicted team results")

if "team_tuple" not in st.session_state or not st.session_state.team_tuple:
    st.warning("Add teams on the Team Race page first.")
    st.stop()

course = st.session_state.get("selected_course", "Average / Neutral")
rating = db.get_course_rating(course)
st.write(f"Course: **{course}** — rating {db.describe_course_rating(rating)}")
st.caption(
    "Each athlete is scored with the weighted Riegel prediction, then NCAA "
    "team scoring (top 5 score, top 7 displace) is applied."
)

tuple_lst = []
for gender, team_name, athlete_names in st.session_state.team_tuple:
    team_id = db.get_team_id(team_name, gender)
    for ath_name in athlete_names:
        athlete_id = db.get_athlete_id(ath_name, team_id)
        race_time_lst = db.get_athlete_races(athlete_id)
        predicted = db.predict_race_time(race_time_lst, gender, course)
        tuple_lst.append([gender, team_name, ath_name, predicted])

sorted_lst = db.Sort(tuple_lst)

# Drop athletes with no usable prediction before scoring
sortable = [row for row in sorted_lst if db.parse_race_seconds(row[3]) is not None]

place = []
team = []
athlete = []
racetime = []
for i, row in enumerate(sortable):
    place.append(i + 1)
    team.append(row[1])
    athlete.append(row[2])
    racetime.append(row[3])

team_scores = db.actual_score(team)
team_final = db.team_score_test(team_scores)

place2 = []
team2 = []
score = []
for i, row in enumerate(team_final):
    place2.append(i + 1)
    team2.append(row[0])
    score.append(row[1])

if team_final:
    st.table({"Place": place2, "Team Name": team2, "Score": score})
else:
    st.info("Need at least one team with five scoring runners for a team score.")

st.table(
    {
        "Place": place,
        "Team Name": team,
        "Athlete Name": athlete,
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
