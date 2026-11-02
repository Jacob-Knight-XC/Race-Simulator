import streamlit as st

from ui_helpers import course_selector, ensure_session_defaults, get_db, show_table

db = get_db()
ensure_session_defaults()

st.title("Individual Race")
st.write("Pick athletes to simulate, then open **Individual Results**.")
st.subheader("Athlete Selection")

course_selector(db)

gender = st.radio("Select Gender (m = Male, f = Female): ", ("m", "f"))
team_names = [name for name, _ in db.get_teams(gender)]
team = st.selectbox("Select Team: ", team_names)

team_id = db.get_team_id(team, gender)
roster = db.get_roster(team_id) if team_id else []
athlete_names = [name for name, _ in roster]
athlete = st.selectbox("Select Athlete: ", athlete_names)

col1, col2 = st.columns([0.25, 1])
with col1:
    if st.button("Submit Athlete") and athlete:
        st.session_state.gender_lst.append(gender)
        st.session_state.team_lst.append(team)
        st.session_state.athlete_lst.append(athlete)
with col2:
    if st.button("Delete Athlete") and st.session_state.athlete_lst:
        st.session_state.gender_lst.pop()
        st.session_state.team_lst.pop()
        st.session_state.athlete_lst.pop()

show_table({
        "Gender": st.session_state.gender_lst,
        "Team Name": st.session_state.team_lst,
        "Athlete Name": st.session_state.athlete_lst,
    })
