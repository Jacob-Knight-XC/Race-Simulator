from data_pull import DB
import streamlit as st

db = DB('racedata.db')

st.title('Race Predictor')
st.write('Pick athletes to simulate in a race!')

st.subheader('Athlete Selection')
#Stores lists of selected athletes
if 'gender_lst' not in st.session_state:
    st.session_state['gender_lst'] = []
    
if 'team_lst' not in st.session_state:
    st.session_state['team_lst'] = []
    
if 'athlete_lst' not in st.session_state:
    st.session_state['athlete_lst'] = []

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

if st.button("Submit Athlete"):
    st.session_state.gender_lst.append(gender)
    st.session_state.team_lst.append(team)
    st.session_state.athlete_lst.append(athlete)

st.table({"Gender": st.session_state.gender_lst, 
          "Team Name": st.session_state.team_lst,
          "Athlete Name": st.session_state.athlete_lst})
