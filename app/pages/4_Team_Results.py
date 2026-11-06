import streamlit as st

from ui_helpers import (
    apply_theme,
    content_frame,
    get_db,
    page_header,
    render_team_meet_analysis,
    roster_depth_label,
    roster_depth_selector,
    selected_course,
    stop_if_division_db_missing,
)

apply_theme("Team Results · XC Sim")
stop_if_division_db_missing()
db = get_db()

with content_frame():
    page_header(
        "Team Results",
        "NCAA team scores from predicted finishes — top five score, top seven displace.",
    )

    if not st.session_state.get("team_tuple"):
        st.warning("Add teams on the Team Race page first.")
        if st.button("Go to Team Race"):
            st.switch_page("pages/3_Team_Race.py")
        st.stop()

    course = selected_course()
    rating = db.get_course_rating(course)
    depth_limit = roster_depth_selector()

    st.markdown(
        f"""
        <div class="xc-panel">
          <strong>{course}</strong><br/>
          <span class="xc-badge">Rating · {db.describe_course_rating(rating)}</span>
          <span class="xc-badge" style="margin-left:0.4rem;">
            Field · {roster_depth_label(depth_limit)}
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    athletes = []
    for gender, team_name, roster in st.session_state.team_tuple:
        for entry in roster:
            if (
                isinstance(entry, (list, tuple))
                and len(entry) >= 2
                and isinstance(entry[1], int)
            ):
                ath_name, athlete_id = entry[0], entry[1]
            else:
                ath_name = entry if isinstance(entry, str) else entry[0]
                team_id = db.get_team_id(team_name, gender)
                athlete_id = db.get_athlete_id(ath_name, team_id)
                if athlete_id is None:
                    continue
            athletes.append((gender, team_name, athlete_id, ath_name))

    rows = db.sort_by_time(db.predict_many(athletes, course))
    limited_rows = db.limit_athletes_per_team(rows, depth_limit)
    analysis = db.analyze_team_meet(limited_rows)
    render_team_meet_analysis(analysis)
