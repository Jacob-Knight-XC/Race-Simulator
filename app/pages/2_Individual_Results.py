import streamlit as st

from ui_helpers import (
    apply_theme,
    content_frame,
    get_db,
    page_header,
    selected_course,
    show_table,
)

apply_theme("Individual Results · XC Sim")
db = get_db()

with content_frame():
    page_header(
        "Individual Results",
        "Predicted finishes for the athletes you lined up, adjusted for the selected course.",
    )

    if not st.session_state.get("athlete_lst"):
        st.warning("Add athletes on the Individual Race page first.")
        if st.button("Go to Individual Race"):
            st.switch_page("pages/1_Individual_Race.py")
        st.stop()

    course = selected_course()
    rating = db.get_course_rating(course)
    gender0 = st.session_state.gender_lst[0]

    st.markdown(
        f"""
        <div class="xc-panel">
          <strong>{course}</strong><br/>
          <span class="xc-badge">Rating · {db.describe_course_rating(rating)}</span>
          <p style="margin:0.75rem 0 0;color:#5b6d66;">
            Equivalent {db.TARGET_LABEL.get(gender0, 'race')} times use Riegel scaling,
            recency/form weighting, and course difficulty.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    athletes = []
    for gender, team, athlete in zip(
        st.session_state.gender_lst,
        st.session_state.team_lst,
        st.session_state.athlete_lst,
    ):
        team_id = db.get_team_id(team, gender)
        athlete_id = db.get_athlete_id(athlete, team_id)
        if athlete_id is not None:
            athletes.append((gender, team, athlete_id, athlete))

    rows = db.sort_by_time(db.predict_many(athletes, course))

    show_table(
        {
            "Place": list(range(1, len(rows) + 1)),
            "Team": [r[1] for r in rows],
            "Athlete": [r[2] for r in rows],
            "Predicted Time": [r[3] for r in rows],
        }
    )
