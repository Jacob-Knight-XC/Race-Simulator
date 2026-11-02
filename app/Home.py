import streamlit as st

from ui_helpers import get_db, show_table

db = get_db()

st.title("Cross Country Race Simulator")
st.write(
    "Simulate collegiate cross country team and individual races from TFRRS "
    "result history, with course difficulty ratings and a weighted prediction "
    "algorithm."
)
st.write(
    "Use **Individual Race** or **Team Race** to pick competitors and a "
    "course, then open the matching **Results** page for predicted finishes."
)

st.subheader("Quick athlete lookup")

gender = st.radio("Select Gender (m = Male, f = Female): ", ("m", "f"))
teams = db.get_teams(gender)
team_names = [name for name, _ in teams]
team = st.selectbox("Select Team: ", team_names)

team_id = db.get_team_id(team, gender)
roster = db.get_roster(team_id) if team_id else []
athlete_names = [name for name, _ in roster]
athlete = st.selectbox("Select Athlete: ", athlete_names)

if not athlete:
    st.info("No athletes found for this team.")
    st.stop()

athlete_id = db.get_athlete_id(athlete, team_id)
races = db.get_athlete_races(athlete_id)

show_table({
        "Distance": [r[0] for r in races],
        "Time": [r[1] for r in races],
        "Meet Name": [r[2] for r in races],
        "Date": [r[3] for r in races],
        "Course Rating": [
            db.describe_course_rating(db.get_course_rating(r[2])) for r in races
        ],
    })

predicted = db.predict_race_time(races, gender)
st.write(
    f"Predicted next {db.TARGET_LABEL[gender]} (neutral course): **{predicted}**"
)
st.write("Average 8k:", db.get_avg_8k(races))
st.write("Average 6k:", db.get_avg_6k(races))
st.write("Average 5k:", db.get_avg_5k(races))
