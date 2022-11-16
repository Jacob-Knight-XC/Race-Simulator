# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import TeamItem, AthleteItem, RaceItem
import sqlite3


class RacePredictorPipeline:
    
    def __init__(self):
        self.create_connection()
        self.create_team_table()
        self.create_athlete_table()
        self.create_race_table()
        
    def create_connection(self):
        self.conn = sqlite3.connect('racedata.db')
        self.curr = self.conn.cursor()
    
    def close_spider(self, spider):
        self.close_connection()
        
    def create_team_table(self):
        try:
            self.curr.execute("""CREATE TABLE IF NOT EXISTS Teams(
                                team_id TEXT,
                                team_name TEXT, 
                                gender TEXT,
                                PRIMARY KEY (team_id)
                                )""")
            self.conn.commit()
        except:
            pass
    
    
    def create_athlete_table(self):
        try:
            self.curr.execute("""CREATE TABLE IF NOT EXISTS Athletes(
                                athlete_id INTEGER,
                                ath_first TEXT,
                                ath_last TEXT,
                                team_id TEXT,
                                PRIMARY KEY (athlete_id),
                                FOREIGN KEY (team_id)
                                    REFERENCES Teams (team_id)
                                )""")
            self.conn.commit()
        except:
            pass
        
    def create_race_table(self):
        try:
            self.curr.execute("""CREATE TABLE IF NOT EXISTS Races(
                                athlete_id INTEGER,
                                distance TEXT,
                                race_time TEXT,
                                meet_name TEXT,
                                meet_date DATE,
                                CONSTRAINT unq UNIQUE(athlete_id,distance,race_time,meet_name,meet_date)
                                )""")
            self.conn.commit()
        except:
            pass
    
    def process_item(self, item, spider):
        if isinstance(item, TeamItem):
            self.store_team(item)
        elif isinstance(item, AthleteItem):
            self.store_athlete(item)
        elif isinstance(item, RaceItem):
            self.store_race(item)
        return item
    
    def store_team(self, item):
        try:
            self.curr.execute("""INSERT INTO Teams VALUES(?,?,?)""",(
                                item['team_id'],
                                item['team_name'],
                                item['gender']
                            ))
            self.conn.commit()
        except:
            pass
     
    
    def store_athlete(self, item):
        try:
            self.curr.execute("""INSERT INTO Athletes VALUES(?,?,?,?)""", (
                                item['athlete_id'],
                                item['ath_first'],
                                item['ath_last'],
                                item['team_id']
                            ))
            self.conn.commit()
        except: 
            pass

    def store_race(self, item):
        try:
            self.curr.execute("""INSERT INTO Races VALUES(?,?,?,?,?)""", (
                                item['athlete_id'],
                                item['distance'],
                                item['race_time'],
                                item['meet_name'],
                                item['meet_date']
                            ))
            self.conn.commit()
        except:
            pass
    
            
    def log_error(self, error):
        with open("sql_error_log.txt", 'a') as f:
            f.write(error)

    def close_connection(self):
        self.conn.close()