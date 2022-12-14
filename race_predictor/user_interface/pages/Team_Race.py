from data_pull import DB
import streamlit as st

db = DB('racedata.db')

st.title('Team Race')
st.write('Pick Teams to simulate in a race!')
st.subheader('Team Selection')

#Stores lists of selected athletes
if 'team_tuple' not in st.session_state:
    st.session_state['team_tuple'] = []

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
 
#Puts buttons side by side   
col1, col2 = st.columns([.25,1])

with col1:
    if st.button("Submit Team"):
        st.session_state.team_tuple.append([gender, team, athlete_names])
with col2:
    if st.button("Delete Team"):
        st.session_state.team_tuple.pop(-1)
    
team_name = []
team_gender = []

for i in range(len(st.session_state.team_tuple)):
    team_gender.append(st.session_state.team_tuple[i][0])
    team_name.append(st.session_state.team_tuple[i][1])

st.table({"Gender": team_gender, 
          "Team Name": team_name})

#hides table first column
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)