from data_pull import DB
import streamlit as st

db = DB("racedata.db")


class StreamlitInterface:
    def __init__(self):
        st.title("Average Race Time")
        self.set_up()

    def set_up(self):
        self.gender = st.radio(
            "Select Gender (m = Male, f = Female): ",
            ("m", "f"),
        )

        self.teamlst = db.get_div_teams(self.gender)
        self.team_names = [name for name, _ in self.teamlst]
        self.team = st.selectbox("Select Team: ", self.team_names)

        self.team_id = db.get_team_id(self.team, self.gender)
        self.athletes = db.get_init_team_roster(self.team_id)
        self.athlete_names = [name for name, _ in self.athletes] if self.athletes else []

        self.athlete = st.selectbox("Select Athlete: ", self.athlete_names)
        if not self.athlete:
            st.info("No athletes found for this team.")
            return

        self.athlete_id = db.get_athlete_id(self.athlete, self.team_id)
        self.race_time_lst = db.get_athlete_races(self.athlete_id)

        distance = []
        race_time = []
        meet_name = []
        meet_date = []
        for row in self.race_time_lst:
            distance.append(row[0])
            race_time.append(row[1])
            meet_name.append(row[2])
            meet_date.append(row[3])

        st.table(
            {
                "Distance": distance,
                "Time": race_time,
                "Meet Name": meet_name,
                "Date": meet_date,
            }
        )

        st.write("Your average 8k time is:", db.get_avg_8k(self.race_time_lst))
        st.write("Your average 6k time is:", db.get_avg_6k(self.race_time_lst))
        st.write("Your average 5k time is:", db.get_avg_5k(self.race_time_lst))
        st.write(
            f"Predicted next {db.TARGET_LABEL[self.gender]}:",
            db.predict_race_time(self.race_time_lst, self.gender),
        )


if __name__ == "__main__":
    StreamlitInterface()
