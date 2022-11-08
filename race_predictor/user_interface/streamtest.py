from data_pull import DB 
import streamlit as st 

db = DB('racedata.db')

class TestInterface():
    
    def __init__(self):
        st.title('Race Predictor')
        self.setup()
    
    def setup(self):
        page_names = ['Athlete Race', 'Team Race']
        page = st.radio('Choose your Race!', page_names)

        if page == 'Athlete Race':
            st.subheader('Welcome to the Athlete Race Simulator')
            if self.start_simulation() == True:
                self.athlete_race()
        else:
            st.subheader('Welcome to the Team Race Simulator')
            if self.start_simulation() == True:
                self.team_race()
            
    def athlete_race(self):
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
        
        self.athlete_button(gender, team, athlete)
        
    def athlete_button(self, gender, team, athlete):
        if st.button('Submit Athlete'):
            return self.athlete_lst(gender, team, athlete)
    
    def team_race(self):
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
        
        st.table(athlete_names)
            
        if st.button('Submit Team'):
            return gender, team
        
    def start_simulation(self):
        if st.button('Start Simulation'):
            return False
        else:
            return True
        
    def athlete_lst(self, gender, team, athlete):
        genderlst = []
        teamlst = []
        athletelst = []
        
        genderlst.append(gender)
        teamlst.append(team)
        athletelst.append(athlete)
        
        st.table({"Gender": genderlst, "Team Name": teamlst, "Athlete Name": athletelst})
        
    
if __name__ == "__main__":
    ti = TestInterface()