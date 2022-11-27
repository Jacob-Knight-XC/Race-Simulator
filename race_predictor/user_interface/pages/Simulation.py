from data_pull import DB
import streamlit as st

db = DB('racedata.db')

st.title('Simulation')
st.subheader('This page shows the results!')
tuple_lst = []

for i in range(len(st.session_state.gender_lst)):
    tuple_lst.append([st.session_state.gender_lst[i], st.session_state.team_lst[i], st.session_state.athlete_lst[i]])
    
    #Load Athlete Races
    team_id = db.get_team_id(st.session_state.team_lst[i], st.session_state.gender_lst[i])
    athlete_id = db.get_athlete_id(st.session_state.athlete_lst[i], team_id)
    race_time_lst = db.get_athlete_races(athlete_id)
    
    if st.session_state.gender_lst[i] == 'm':
        race_times = db.get_8k_times(race_time_lst)
        avg_time = db.get_avg_time(race_times)
        tuple_lst[i].append(avg_time)
    else:
        race_times = db.get_6k_times(race_time_lst)
        avg_time = db.get_avg_time(race_times)
        tuple_lst[i].append(avg_time)
        
sorted_lst = db.Sort(tuple_lst)
        
gender = []
team = []
athlete = []
racetime = []

for i in range(len(sorted_lst)):
    gender.append(sorted_lst[i][0])
    team.append(sorted_lst[i][1])
    athlete.append(sorted_lst[i][2])
    racetime.append(sorted_lst[i][3])
    
st.table({"Gender": gender, "Team Name": team, "Athlete Name": athlete, "Race Time": racetime})
