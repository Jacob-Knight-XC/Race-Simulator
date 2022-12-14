from data_pull import DB
import streamlit as st

#setup stuff
db = DB('racedata.db')

st.title('Individual Simulation')
st.subheader('This page shows the individual results!')
tuple_lst = []

#Makes a tuple of each athletes info
for i in range(len(st.session_state.gender_lst)):
    tuple_lst.append([st.session_state.gender_lst[i], st.session_state.team_lst[i], st.session_state.athlete_lst[i]])
    
    #Load Athlete Races
    team_id = db.get_team_id(st.session_state.team_lst[i], st.session_state.gender_lst[i])
    athlete_id = db.get_athlete_id(st.session_state.athlete_lst[i], team_id)
    race_time_lst = db.get_athlete_races(athlete_id)
    
    #loads male or female races
    if st.session_state.gender_lst[i] == 'm':
        race_times = db.get_8k_times(race_time_lst)
        avg_time = db.fastest_times(race_times)
        tuple_lst[i].append(avg_time)
    else:
        race_times = db.get_6k_times(race_time_lst)
        avg_time = db.fastest_times(race_times)
        tuple_lst[i].append(avg_time)
 
#sorts the list of athletes by there time       
sorted_lst = db.Sort(tuple_lst)
        
place = []
team = []
athlete = []
racetime = []

#Pulls out data for formating reasons. Tuples wont work in streamlits table
for i in range(len(sorted_lst)):
    place.append(i + 1)
    team.append(sorted_lst[i][1])
    athlete.append(sorted_lst[i][2])
    racetime.append(sorted_lst[i][3])
    
st.table({"Place": place, "Team Name": team, "Athlete Name": athlete, "Race Time": racetime})

#Gets rid of the index column in the table
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)