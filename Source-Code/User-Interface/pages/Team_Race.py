from data_pull import DB
import streamlit as st

db = DB("racedata.db")

st.title("Team Race")
st.write("Pick teams to simulate in a race, then open Team Race Visual.")
st.subheader("Team Selection")

if "team_tuple" not in st.session_state:
    st.session_state["team_tuple"] = []
if "selected_course" not in st.session_state:
    st.session_state["selected_course"] = "Average / Neutral"

meet_options = ["Average / Neutral"] + db.get_meet_names()
course = st.selectbox(
    "Simulate on course:",
    meet_options,
    index=meet_options.index(st.session_state["selected_course"])
    if st.session_state["selected_course"] in meet_options
    else 0,
)
st.session_state["selected_course"] = course
st.caption(
    "Course rating: "
    + db.describe_course_rating(db.get_course_rating(course))
)

gender = st.radio("Select Gender (m = Male, f = Female): ", ("m", "f"))

teamlst = db.get_div_teams(gender)
team_names = [name for name, _ in teamlst]
team = st.selectbox("Select Team: ", team_names)

team_id = db.get_team_id(team, gender)
athletes = db.get_init_team_roster(team_id)
athlete_names = [name for name, _ in athletes] if athletes else []

col1, col2 = st.columns([0.25, 1])
with col1:
    if st.button("Submit Team") and athlete_names:
        st.session_state.team_tuple.append([gender, team, athlete_names])
with col2:
    if st.button("Delete Team") and st.session_state.team_tuple:
        st.session_state.team_tuple.pop(-1)

team_name = []
team_gender = []
for entry in st.session_state.team_tuple:
    team_gender.append(entry[0])
    team_name.append(entry[1])

st.table({"Gender": team_gender, "Team Name": team_name})

st.markdown(
    """
    <style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    </style>
    """,
    unsafe_allow_html=True,
)
