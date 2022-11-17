from data_pull import DB
import streamlit as st

db = DB('racedata.db')

st.title('Simulation')
st.subheader('This page shows the results!')
gender_lst = []
team_lst = []
athlete_lst = []
avg_race_time = []

for i in range(len(st.session_state.gender_lst)):
    gender_lst.append(st.session_state.gender_lst[i])
    team_lst.append(st.session_state.team_lst[i])
    athlete_lst.append(st.session_state.athlete_lst[i])
    #Load Athlete Races
    team_id = db.get_team_id(st.session_state.team_lst[i], st.session_state.gender_lst[i])
    athlete_id = db.get_athlete_id(st.session_state.athlete_lst[i], team_id)
    race_time_lst = db.get_athlete_races(athlete_id)
    if st.session_state.gender_lst[i] == 'm':
        timeing = db.get_avg_8k(race_time_lst)
        avg_race_time.append(timeing)
    else:
        timeing = db.get_avg_6k(race_time_lst)
        avg_race_time.append(timeing)

#Dataframe for races
st.table({"Gender": gender_lst, "Team": team_lst, "Athlete": athlete_lst, 'Avergae Time': avg_race_time})