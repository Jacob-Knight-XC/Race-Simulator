from data_pull import DB
import streamlit as st

#set up
db = DB('racedata.db')

st.title('Individual Race')
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

#places buttons side by side
col1, col2 = st.columns([.25,1])

with col1: 
    if st.button("Submit Athlete"):
        st.session_state.gender_lst.append(gender)
        st.session_state.team_lst.append(team)
        st.session_state.athlete_lst.append(athlete)
with col2:    
    if st.button("Delete Athlete"):
        st.session_state.gender_lst.pop(-1)
        st.session_state.team_lst.pop(-1)
        st.session_state.athlete_lst.pop(-1)

st.table({"Gender": st.session_state.gender_lst, 
          "Team Name": st.session_state.team_lst,
          "Athlete Name": st.session_state.athlete_lst})

#hides first column of table
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)