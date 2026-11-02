import streamlit as st

from ui_helpers import course_selector, ensure_session_defaults, get_db, show_table

db = get_db()
ensure_session_defaults()

st.title("Team Race")
st.write("Pick teams to simulate, then open **Team Results**.")
st.subheader("Team Selection")

course_selector(db)

gender = st.radio("Select Gender (m = Male, f = Female): ", ("m", "f"))
team_names = [name for name, _ in db.get_teams(gender)]
team = st.selectbox("Select Team: ", team_names)

team_id = db.get_team_id(team, gender)
roster = db.get_roster(team_id) if team_id else []
athlete_names = [name for name, _ in roster]

col1, col2 = st.columns([0.25, 1])
with col1:
    if st.button("Submit Team") and athlete_names:
        # Store roster as (name, athlete_id) so results can batch-query.
        st.session_state.team_tuple.append([gender, team, roster])
with col2:
    if st.button("Delete Team") and st.session_state.team_tuple:
        st.session_state.team_tuple.pop()

show_table({
        "Gender": [entry[0] for entry in st.session_state.team_tuple],
        "Team Name": [entry[1] for entry in st.session_state.team_tuple],
        "Runners": [len(entry[2]) for entry in st.session_state.team_tuple],
    })
