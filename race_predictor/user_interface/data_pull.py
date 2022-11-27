import sqlite3
import datetime
from datetime import timedelta
from numpy import mean

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
    
    def get_div_teams(self, gender):
        """ returns a list of team name and id tuples in a particular division and gender
            input:  division: integer value of 1,2, or 3, gender string of m or f
            output: list of tuples (name, id)
        """
        self._start_connection()
        teams = self.curr.execute("""SELECT team_name, team_id
                                    FROM Teams
                                    WHERE gender = ?
                                    ORDER BY team_name""",
                                    (gender))
        teams = teams.fetchall()
        #print(teams)
        return teams
    
    def get_team_id(self, name, gender):
        teamlst = self.get_div_teams(gender)
        for i in range(len(teamlst)):
            if teamlst[i][0] == name:
                return teamlst[i][1]

    def get_init_team_roster(self, team_id):
        self._start_connection()
        cmd = f"""SELECT (ath_first || ' ' || ath_last) as name, athlete_id
                                FROM Athletes
                                WHERE team_id = {team_id!r}
                                ORDER BY name"""
        roster = self.curr.execute(cmd)
        roster = roster.fetchall()
        self._close_connection()
        #print(roster)
        return roster
    
    def get_athlete_ids(self, team_id):
        athlst = self.get_init_team_roster(team_id)
        ath_id = []
        #print(athlst)
        for i in range(len(athlst)):
            ath_id.append(athlst[i][1])
        #print(ath_id)
        return ath_id
    
    def get_athlete_id(self, name, team_id):
        athlst = self.get_init_team_roster(team_id)
        for i in range(len(athlst)):
            if athlst[i][0] == name:
                return athlst[i][1]
    
    def get_athlete_names(self, team_id):
        athlst = self.get_init_team_roster(team_id)
        ath_name = []
        #print(athlst)
        for i in range(len(athlst)):
            ath_name.append(athlst[i][0])
        #print(ath_name)
        return ath_name
    
    def get_athlete_races(self, athlete_id):
        self._start_connection()
        races = self.curr.execute("""SELECT distance, race_time, meet_name, meet_date
                                    FROM Races
                                    WHERE athlete_id = ?
                                    ORDER BY race_time""",
                                    (athlete_id,))
        races = races.fetchall()
        #print(races)
        return races
    
    def get_a_race(self, meet_name):
        self._start_connection()
        races = self.curr.execute("""SELECT distance, race_time, meet_name, meet_date, athlete_id
                                    FROM Races
                                    WHERE meet_name = ?
                                    ORDER BY race_time""",
                                    (meet_name,))
        races = races.fetchall()
        #print(races)
        return races
    
    def get_8k_times(self, race_time):
        eightk = []
        for x in range(len(race_time)):
            if race_time[x][0] == '8k' or race_time[x][0] == '4.98M' or race_time[x][0] == '4.97M' or race_time[x][0] == '4.96M' or race_time[x][0] == '4.95M':
                if race_time[x][1] != 'DNF' and race_time[x][1] != 'DNS' and race_time[x][1] != 'DQ' and race_time[x][1] != 'SCR' and race_time[x][1] != 'X':
                    eight_timestr = datetime.datetime.strptime(race_time[x][1], '%M:%S.%f')
                    eight_only_time = eight_timestr.strftime('%M:%S.%f')
                    eightk.append(eight_only_time)
        return eightk
            
    def get_6k_times(self, race_time):
        sixk = []
        for x in range(len(race_time)):
            if race_time[x][0] == '6k' or race_time[x][0] == '3.74M' or race_time[x][0] == '3.73M' or race_time[x][0] == '3.72M' or race_time[x][0] == '3.71M' or race_time[x][0] == '3.7M' and race_time[x][1]:
                if race_time[x][1] != 'DNF' and race_time[x][1] != 'DNS' and race_time[x][1] != 'DQ' and race_time[x][1] != 'SCR' and race_time[x][1] != 'X':
                    six_timestr = datetime.datetime.strptime(race_time[x][1], '%M:%S.%f')
                    six_only_time = six_timestr.strftime('%M:%S.%f')
                    sixk.append(six_only_time)
        return sixk
            
    def get_5k_times(self, race_time):
        fivek = []
        for x in range(len(race_time)):
            if race_time[x][0] == '5k' or race_time[x][0] == '3.11M' or race_time[x][0] == '3.1M':
                if race_time[x][1] != 'DNF' and race_time[x][1] != 'DNS' and race_time[x][1] != 'DQ' and race_time[x][1] != 'SCR' and race_time[x][1] != 'X':
                    five_timestr = datetime.datetime.strptime(race_time[x][1], '%M:%S.%f')
                    five_only_time = five_timestr.strftime('%M:%S.%f')
                    fivek.append(five_only_time)
        return fivek
    
    def get_avg_time(self, time_lst):
        if len(time_lst) > 1:
            avg_seconds = self._str_to_seconds(time_lst)
            avg = mean(avg_seconds)
            return str(timedelta(seconds = avg))
            """if avg % 60 >= 10:
                str = f"{avg // 60:.0f}:{avg % 60:.2f}"
                return str
            else:
                str = f"{avg // 60:.0f}:0{avg % 60:.2f}"
                return str"""
            
    def get_athlete_pr(self, time_lst):
        pr = time_lst[0]
        return pr
    
    # Python code to sort the lists using the second element of sublists
    def Sort(self, sub_li):
        l = len(sub_li)
        for i in range(0, l):
            for j in range(0, l-i-1):
                if (sub_li[j][3] > sub_li[j + 1][3]):
                    tempo = sub_li[j]
                    sub_li[j]= sub_li[j + 1]
                    sub_li[j + 1]= tempo
        return sub_li

    @staticmethod
    def _str_to_seconds(times):
        new_times = []
        for t in times:
            mins, sec, mil = float(t[:2]), float(t[3:5]), float(t[5:])
            new_times.append(60*mins + sec + mil)
        return new_times
        
    
if __name__ == "__main__":
    db = DB()