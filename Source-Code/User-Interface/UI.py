from data_pull import DB
import streamlit as st

db = DB("racedata.db")

st.title("Cross Country Race Simulator")
st.write(
    "Simulate collegiate cross country races with TFRRS result history, "
    "course difficulty ratings, and a weighted race-prediction algorithm."
)
st.write(
    "Use **Individual Race** or **Team Race** to pick competitors and a "
    "course, then open the matching **Visual** page for predicted results."
)

st.subheader("Quick athlete lookup")

gender = st.radio("Select Gender (m = Male, f = Female): ", ("m", "f"))

teamlst = db.get_div_teams(gender)
team_names = [name for name, _ in teamlst]
team = st.selectbox("Select Team: ", team_names)

team_id = db.get_team_id(team, gender)
athletes = db.get_init_team_roster(team_id)
athlete_names = [name for name, _ in athletes] if athletes else []

athlete = st.selectbox("Select Athlete: ", athlete_names)
if not athlete:
    st.info("No athletes found for this team.")
    st.stop()

athlete_id = db.get_athlete_id(athlete, team_id)
race_time_lst = db.get_athlete_races(athlete_id)

distance = []
race_time = []
meet_name = []
meet_date = []
course_rating = []
for dist, time_str, meet, date in race_time_lst:
    distance.append(dist)
    race_time.append(time_str)
    meet_name.append(meet)
    meet_date.append(date)
    course_rating.append(db.describe_course_rating(db.get_course_rating(meet)))

st.table(
    {
        "Distance": distance,
        "Time": race_time,
        "Meet Name": meet_name,
        "Date": meet_date,
        "Course Rating": course_rating,
    }
)

predicted = db.predict_race_time(race_time_lst, gender)
st.write(
    f"Predicted next {db.TARGET_LABEL[gender]} (neutral course): **{predicted}**"
)
st.write("Average 8k:", db.get_avg_8k(race_time_lst))
st.write("Average 6k:", db.get_avg_6k(race_time_lst))
st.write("Average 5k:", db.get_avg_5k(race_time_lst))
