from data_pull import DB
import streamlit as st

db = DB("racedata.db")

st.title("Individual Race")
st.write("Pick athletes to simulate in a race, then open Individual Race Visual.")
st.subheader("Athlete Selection")

if "gender_lst" not in st.session_state:
    st.session_state["gender_lst"] = []
if "team_lst" not in st.session_state:
    st.session_state["team_lst"] = []
if "athlete_lst" not in st.session_state:
    st.session_state["athlete_lst"] = []
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

athlete = st.selectbox("Select Athlete: ", athlete_names)

col1, col2 = st.columns([0.25, 1])
with col1:
    if st.button("Submit Athlete") and athlete:
        st.session_state.gender_lst.append(gender)
        st.session_state.team_lst.append(team)
        st.session_state.athlete_lst.append(athlete)
with col2:
    if st.button("Delete Athlete") and st.session_state.athlete_lst:
        st.session_state.gender_lst.pop(-1)
        st.session_state.team_lst.pop(-1)
        st.session_state.athlete_lst.pop(-1)

st.table(
    {
        "Gender": st.session_state.gender_lst,
        "Team Name": st.session_state.team_lst,
        "Athlete Name": st.session_state.athlete_lst,
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
