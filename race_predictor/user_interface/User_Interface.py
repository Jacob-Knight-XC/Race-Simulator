from data_pull import DB 
import streamlit as st 

db = DB('racedata.db')


class UserInterface():
    
    
    def __init__(self):
        st.title('Race Predictor')
        self.setup()
        athlete_lst = []
    
    def setup(self):
        page_names = ['Athlete Race', 'Team Race']
        page = st.radio('Choose your Race!', page_names)

        if page == 'Athlete Race':
            st.subheader('Welcome to the Athlete Race Simulator')
            self.athlete_race()
        else:
            st.subheader('Welcome to the Team Race Simulator')
            self.team_race()
            
    def athlete_race(self):
        self.select_gender()
        self.select_team()
        self.select_athlete()
        self.submit_athlete_button()
    
    def team_race(self):
        self.select_gender()
        self.select_team()
        self.submit_team_button()
        
    def select_gender(self):
        #Select Gender to Load Male or Female teams
        self.gender = st.radio(
            "Select Gender (m = Male, f = Female): ",
            ('m', 'f'))
    
    def select_team(self):
        #Loads Teams
        self.teamlst = db.get_div_teams(self.gender)
        self.team_names = [name for name, id in self.teamlst]
    
        #Team Selection Box
        self.team = st.selectbox(
            'Select Team: ', 
            self.team_names)
    
        self.team_id = db.get_team_id(self.team, self.gender)
        
    def select_athlete(self):
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
        
    def submit_athlete_button(self):
        if st.button('Submit Athlete'):
            tup = self.gender, self.team, self.athlete
            self.athlete_lst(tup)
            
    def submit_team_button(self):
        if st.button('Submit Team'):
            tup = self.gender, self.team
            self.team_lst(tup)
            
    def athlete_lst(self, tup):
        lst = []
        lst.append(tup)
        self.display_athlete(lst)
        
    def team_lst(self, tup):
        lst = []
        lst.append(tup)
        self.display_team(lst)
        
    def display_athlete(self, lst):
        gender = []
        team = []
        athlete = []
        
        for i in range(len(lst)):
            gender.append(lst[i][0])
            team.append(lst[i][1])
            athlete.append(lst[i][2])
        st.table({"Gender": gender, "Team": team, "Athlete": athlete})
        
    def display_team(self, lst):
        gender = []
        team = []
        
        for i in range(len(lst)):
            gender.append(lst[i][0])
            team.append(lst[i][1])
        st.table({"Gender": gender, "Team": team})
          
            
if __name__ == "__main__":
    UserI = UserInterface()
    