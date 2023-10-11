from data_pull import DB
import streamlit as st

db = DB('racedata.db')

st.title('Race Predictor')
st.write('This is a race predictor where you can simulate two types of races.')
st.write('A Team race or an Individual race. You can pick by selecting a tab.')
st.write('Go to the Race tab and then after enetering the teams or athletes you want to race')
st.write('Select the respective Visual tab to see how that race would pan out.')
 
#Select Gender to Load Male or Female teams
gender = st.radio(
    "Select Gender (m = Male, f = Female): ",
    ('m', 'f'))

#Loads Teams
teamlst = db.get_div_teams(gender)
team_names = [name for name, id in teamlst]

#Team Selection Box
team = st.selectbox(
    'Select Team: ',
    team_names)

#Loads Athletes
team_id = db.get_team_id(team, gender)
athletes = db.get_init_team_roster(team_id)
athlete_names = [name for name, id in athletes]
if len(athletes) > 0:
    athlete_names = [name for name, id in athletes]
else:
    athlete_names = []
    ath_id = None

#Athlete Selection Box
athlete = st.selectbox(
    'Select Athlete: ',
    athlete_names)

athlete_id = db.get_athlete_id(athlete, team_id)
race_time_lst = db.get_athlete_races(athlete_id)

st.write(race_time_lst)