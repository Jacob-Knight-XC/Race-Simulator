import streamlit as st

from ui_helpers import (
    apply_theme,
    content_frame,
    gender_selector,
    get_db,
    metric_row,
    show_table,
    team_selectbox,
)

apply_theme("XC Race Simulator")
db = get_db()

with content_frame():
    st.markdown(
        """
        <section class="xc-hero">
          <div class="xc-hero-inner">
            <div class="xc-kicker">Collegiate Cross Country</div>
            <h1 class="xc-brand">XC Race<br>Simulator</h1>
            <p class="xc-lede">
              Predict finishes from TFRRS history with course difficulty and a
              weighted race model — then line up individuals or full teams.
            </p>
            <div class="xc-cta-row">
              <a class="xc-cta xc-cta-primary" href="/Individual_Race" target="_self">Individual Race</a>
              <a class="xc-cta" href="/Team_Race" target="_self">Team Race</a>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="xc-section">
          <h2 class="xc-section-title">Athlete Lookup</h2>
          <p class="xc-section-copy">
            Inspect one runner’s race history, course ratings, and a neutral-course prediction.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns([1, 1.4, 1.4])
    with col_a:
        gender = gender_selector()
    with col_b:
        teams = db.get_teams(gender)
        team_names = [name for name, _ in teams]
        team = team_selectbox(team_names)
    with col_c:
        team_id = db.get_team_id(team, gender)
        roster = db.get_roster(team_id) if team_id else []
        athlete_names = [name for name, _ in roster]
        athlete = st.selectbox("Athlete", athlete_names)

    if not athlete:
        st.info("No athletes found for this team.")
        st.stop()

    athlete_id = db.get_athlete_id(athlete, team_id)
    races = db.get_athlete_races(athlete_id)
    predicted = db.predict_race_time(races, gender)

    metric_row(
        [
            (f"Predicted {db.TARGET_LABEL[gender]}", predicted),
            ("Average 8k", db.get_avg_8k(races)),
            ("Average 6k", db.get_avg_6k(races)),
            ("Average 5k", db.get_avg_5k(races)),
        ]
    )

    show_table(
        {
            "Distance": [r[0] for r in races],
            "Time": [r[1] for r in races],
            "Meet": [r[2] for r in races],
            "Date": [r[3] for r in races],
            "Course": [
                db.describe_course_rating(db.get_course_rating(r[2])) for r in races
            ],
        }
    )
