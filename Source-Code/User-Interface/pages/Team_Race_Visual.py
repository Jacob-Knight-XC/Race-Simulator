from data_pull import DB
import streamlit as st

db = DB('racedata.db')

st.title('Team Simulation')
st.subheader('This page shows the team results!')

#tuple of each athletes info
tuple_lst = []

#Creates tuple of athlete info
for i in range(len(st.session_state.team_tuple)):
    for x in range(len(st.session_state.team_tuple[i][2])):
        ath_name = st.session_state.team_tuple[i][2][x]
    
        #Load Athlete Races
        team_id = db.get_team_id(st.session_state.team_tuple[i][1], st.session_state.team_tuple[i][0])
        athlete_id = db.get_athlete_id(ath_name, team_id)
        race_time_lst = db.get_athlete_races(athlete_id)
        
        if st.session_state.team_tuple[i][0] == 'm':
            race_times = db.get_8k_times(race_time_lst)
            avg_time = db.new_predict(race_times)
            tuple_lst.append([st.session_state.team_tuple[i][0], st.session_state.team_tuple[i][1], ath_name, avg_time])
        else:
            race_times = db.get_6k_times(race_time_lst)
            avg_time = db.new_predict(race_times)
            tuple_lst.append([st.session_state.team_tuple[i][0], st.session_state.team_tuple[i][1], ath_name, avg_time])

#sorts tuple by racetime        
sorted_lst = db.Sort(tuple_lst)

place = []
team = []
athlete = []
racetime = []

#pulls out data for formating
for i in range(len(sorted_lst)):
    place.append((i + 1))
    team.append(sorted_lst[i][1])
    athlete.append(sorted_lst[i][2])
    racetime.append(sorted_lst[i][3])
  
#Calculates team score  
team_scores = db.actual_score(team)
team_final = db.team_score_test(team_scores)

place2 = []
team2 = []
score = []

#for streamlit formating
for i in range(len(team_final)):
    place2.append((i + 1))
    team2.append(team_final[i][0])
    score.append(team_final[i][1])

st.table({"Place": place2, "Team Name": team2, "Score": score})

# Display an interactive table
st.table({"Place": place, "Team Name": team, "Athlete Name": athlete, "Race Time": racetime})

#hides first column of both tables
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)
            