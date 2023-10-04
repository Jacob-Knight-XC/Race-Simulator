import sqlite3
import datetime
from datetime import timedelta
import numpy as np
from numpy import mean
from sklearn.linear_model import LinearRegression

class DB:

    def __init__(self, name = "racedata.db"):
        self.name = name
        
    def _start_connection(self):
        try:
            self.conn = sqlite3.connect(self.name)
            self.curr = self.conn.cursor()
        except:
            print('did not connect')

    def _close_connection(self):
        self.conn.close()
    
    #return all teams of selected gender
    def get_div_teams(self, gender):
        """ returns a list of team name and id tuples in a particular division and gender
            input: gender string of m or f
            output: list of tuples (name, id)
        """
        self._start_connection()
        teams = self.curr.execute("""SELECT team_name, team_id
                                    FROM Teams
                                    WHERE gender = ?
                                    ORDER BY team_name""",
                                    (gender))
        teams = teams.fetchall()
        return teams
    
    #finds out teams ID
    def get_team_id(self, name, gender):
        teamlst = self.get_div_teams(gender)
        for i in range(len(teamlst)):
            if teamlst[i][0] == name:
                return teamlst[i][1]
            
    #Grabs all athletes on a team
    def get_init_team_roster(self, team_id):
        self._start_connection()
        cmd = f"""SELECT (ath_first || ' ' || ath_last) as name, athlete_id
                                FROM Athletes
                                WHERE team_id = {team_id!r}
                                ORDER BY name"""
        roster = self.curr.execute(cmd)
        roster = roster.fetchall()
        self._close_connection()
        return roster
    
    #gets individual athletes id
    def get_athlete_id(self, name, team_id):
        athlst = self.get_init_team_roster(team_id)
        for i in range(len(athlst)):
            if athlst[i][0] == name:
                return athlst[i][1]
    
    #gets all of an athletes races based off athlete_id
    def get_athlete_races(self, athlete_id):
        self._start_connection()
        races = self.curr.execute("""SELECT distance, race_time, meet_name, meet_date
                                    FROM Races
                                    WHERE athlete_id = ?
                                    ORDER BY race_time""",
                                    (athlete_id,))
        races = races.fetchall()
        return races
    
    #grabs a specific race based off a meet name
    #Not in use yet
    def get_a_race(self, meet_name):
        self._start_connection()
        races = self.curr.execute("""SELECT distance, race_time, meet_name, meet_date, athlete_id
                                    FROM Races
                                    WHERE meet_name = ?
                                    ORDER BY race_time""",
                                    (meet_name,))
        races = races.fetchall()
        return races
    
    #returns all legal 8k performances
    def get_8k_times(self, race_time):
        eightk = []
        for x in range(len(race_time)):
            if race_time[x][0] == '8k' or race_time[x][0] == '4.98M' or race_time[x][0] == '4.97M' or race_time[x][0] == '4.96M' or race_time[x][0] == '4.95M':
                if race_time[x][1] != 'DNF' and race_time[x][1] != 'DNS' and race_time[x][1] != 'DQ' and race_time[x][1] != 'SCR' and race_time[x][1] != 'X':
                    eight_timestr = datetime.datetime.strptime(race_time[x][1], '%M:%S.%f')
                    eight_only_time = eight_timestr.strftime('%M:%S.%f')
                    eightk.append(eight_only_time)
        return eightk
    
    #returns all legal 6k performances      
    def get_6k_times(self, race_time):
        sixk = []
        for x in range(len(race_time)):
            if race_time[x][0] == '6k' or race_time[x][0] == '3.74M' or race_time[x][0] == '3.73M' or race_time[x][0] == '3.72M' or race_time[x][0] == '3.71M' or race_time[x][0] == '3.7M' and race_time[x][1]:
                if race_time[x][1] != 'DNF' and race_time[x][1] != 'DNS' and race_time[x][1] != 'DQ' and race_time[x][1] != 'SCR' and race_time[x][1] != 'X':
                    six_timestr = datetime.datetime.strptime(race_time[x][1], '%M:%S.%f')
                    six_only_time = six_timestr.strftime('%M:%S.%f')
                    sixk.append(six_only_time)
        return sixk
    
    #returns all legal 5k performances      
    def get_5k_times(self, race_time):
        fivek = []
        for x in range(len(race_time)):
            if race_time[x][0] == '5k' or race_time[x][0] == '3.11M' or race_time[x][0] == '3.1M':
                if race_time[x][1] != 'DNF' and race_time[x][1] != 'DNS' and race_time[x][1] != 'DQ' and race_time[x][1] != 'SCR' and race_time[x][1] != 'X':
                    five_timestr = datetime.datetime.strptime(race_time[x][1], '%M:%S.%f')
                    five_only_time = five_timestr.strftime('%M:%S.%f')
                    fivek.append(five_only_time)
        return fivek
    
    #Finds the avg time of lst of times
    def get_avg_time(self, time_lst):
        if len(time_lst) > 1:
            avg_seconds = self._str_to_seconds(time_lst)
            avg = mean(avg_seconds)
            time_str = str(timedelta(seconds = avg))
            return time_str[2:10]
        else:
            return "Less than One Race"
    
    #Uses Machine Learning to find a prediction time for athletes next race
    def new_predict(self, time_lst):
        
        if len(time_lst) > 2:
            previous_distances = [[8000] for _ in range(len(time_lst[:4]))]
            previous_times = time_lst[:4]
            regressor = LinearRegression()
            regressor.fit(previous_distances, self._str_to_seconds(previous_times))
            new_distance = 8000
            new_distance_array = np.array([[new_distance]])
            predicted_time = regressor.predict(new_distance_array)
            time_str = str(timedelta(seconds = predicted_time[0]))
            
            return time_str[2:10]
        else:
            return "Less Than Two Races"
        
    # returns an avg of an athletes fastest five races    
    def fastest_times(self, time_lst):
        if len(time_lst) > 1:
            fastest_five = time_lst[:4]
            avg_seconds = self._str_to_seconds(fastest_five)
            avg = mean(avg_seconds)
            time_str = str(timedelta(seconds = avg))
            return time_str[2:10]
        else:
            return "Less than One Race"
    
    # returns an athletes PR       
    def get_athlete_pr(self, time_lst):
        pr = time_lst[0]
        return pr
    
    #Python code to sort the lists using the fourth index of a sublist
    def Sort(self, sub_li):
        l = len(sub_li)
        for i in range(0, l):
            for j in range(0, l-i-1):
                if (sub_li[j][3] > sub_li[j + 1][3]):
                    tempo = sub_li[j]
                    sub_li[j]= sub_li[j + 1]
                    sub_li[j + 1]= tempo
        return sub_li
    
    #Python code to sort the lists using the second index of a sublist
    def Sorttwo(self, sub_li):
        l = len(sub_li)
        for i in range(0, l):
            for j in range(0, l-i-1):
                if (sub_li[j][1] > sub_li[j + 1][1]):
                    tempo = sub_li[j]
                    sub_li[j]= sub_li[j + 1]
                    sub_li[j + 1]= tempo
        return sub_li

    #converts time string into seconds so it can be averaged. 
    @staticmethod
    def _str_to_seconds(times):
        new_times = []
        for t in times:
            mins, sec, mil = float(t[:2]), float(t[3:5]), float(t[5:])
            new_times.append(60*mins + sec + mil)
        return new_times
    
    #Gives a lst of all teams and finds there score and sorts it
    def team_score_test(self, team):
        teams = []

        for i in team:
            if i not in teams:
                teams.append(i)
        
        lst = [[] for _ in range(len(teams))]
            
        for i in range(len(teams)):
            for x in range(len(team)):
                if teams[i] == team[x]:
                        lst[i].append(x+1)
        
        new_lst = []        
        for i in range(len(lst)):
            new_lst.append([teams[i], sum(lst[i][:5])])
            
        return self.Sorttwo(new_lst)
    
    # This sorts athletes placed in a race by there team so i can find 
    # out a teams top 7, then recalculate the score only using each teams
    # top 7
    def actual_score(self, team):
        teams = []

        for i in team:
            if i not in teams:
                teams.append(i)
        
        lst = [[] for _ in range(len(teams))]
            
        for i in range(len(teams)):
            for x in range(len(team)):
                if teams[i] == team[x]:
                        lst[i].append(x+1)
                        
        new_lst = []        
        for i in range(len(lst)):
            for x in range(7):
                new_lst.append([teams[i], lst[i][x]])
        
        team2 = []
        sorted = self.Sorttwo(new_lst)
        for i in range(len(sorted)):
            team2.append(sorted[i][0])
            
        return team2
                
                
if __name__ == "__main__":
    db = DB()