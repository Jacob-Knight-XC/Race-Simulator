from codecs import getencoder
from data_pull import DB 
import streamlit as st 
import pandas as pd
import numpy as np

db = DB('racedata.db')

class StreamlitInterface:

    def __init__(self):
        st.title('Average Race Time')
        self.set_up()

    def set_up(self):
        
        #Select Gender to Load Male or Female teams
        self.gender = st.radio(
            "Select Gender (m = Male, f = Female): ",
            ('m', 'f'))
        
        #Loads Teams
        self.teamlst = db.get_div_teams(self.gender)
        self.team_names = [name for name, id in self.teamlst]
    
        #Team Selection Box
        self.team = st.selectbox(
            'Select Team: ', 
            self.team_names)
    
            #Loads Athletes
        self.team_id = db.get_team_id(self.team, self.gender)
        self.athletes = db.get_init_team_roster(self.team_id)
        self.athlete_names = [name for name, id in self.athletes]
        if len(self.athletes) > 0:
            self.athlete_names = [name for name, id in self.athletes]
        else:
            self.athlete_names = []
            self.ath_id = None
    
        #Athlete Selection Box
        self.athlete = st.selectbox(
            'Select Athlete: ', 
            self.athlete_names)
        
        #Load Athlete Races
        self.athlete_id = db.get_athlete_id(self.athlete, self.team_id)
        self.race_time_lst = db.get_athlete_races(self.athlete_id)
        
        distance = []
        race_time = []
        meet_name = []
        meet_date = []

        for i in range(len(self.race_time_lst)):
            distance.append(self.race_time_lst[i][0])
            race_time.append(self.race_time_lst[i][1])
            meet_name.append(self.race_time_lst[i][2])
            meet_date.append(self.race_time_lst[i][3])
    
        #Dataframe for races
        st.table({"Distance": distance, "Time": race_time, "Meet Name": meet_name, "Date": meet_date})
        
        #Avg Race Times
        #8k
        eight_avg = db.get_avg_8k(self.race_time_lst)
        st.write("Your average 8k time is:", eight_avg)
        
        #6k
        six_avg = db.get_avg_6k(self.race_time_lst)
        st.write("Your average 6k time is:", six_avg)
        
        #5k
        five_avg = db.get_avg_5k(self.race_time_lst)
        st.write("Your average 5k time is:", five_avg)
        
        self.submit_button(self.gender, self.team, self.athlete)
               
    def submit_button(self, gender, team, athlete):
        
        if st.button('Submit Athlete'):
            return self.make_lst(gender, team, athlete)
        
    def make_lst(self, gender, team, athlete):
        genderlst = []
        teamlst = []
        athletelst = []
        
        genderlst.append(gender)
        teamlst.append(team)
        athletelst.append(athlete)
        
        st.table({"Gender": genderlst, "Team": teamlst, "Athlete": athletelst})
        
    
if __name__ == "__main__":
    streaml = StreamlitInterface()
            
        