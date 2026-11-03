import streamlit as st

from ui_helpers import (
    apply_theme,
    cached_top_teams_race,
    content_frame,
    course_selector,
    gender_selector,
    get_db,
    page_header,
    render_team_meet_analysis,
)

apply_theme("Top 30 Teams · XC Sim")
db = get_db()

with content_frame():
    page_header(
        "Top 30 Teams",
        "National team ranking from predicted times — each team enters its top 7, "
        "then the best 30 scoring teams are re-raced together.",
    )

    left, right = st.columns([1, 1], gap="large")
    with left:
        course = course_selector(db, key="national_teams_course")
    with right:
        gender = gender_selector(key="national_teams_gender")

    rating = db.get_course_rating(course)
    result = cached_top_teams_race(gender, course, db.path, n_teams=30, per_team=7)

    st.markdown(
        f"""
        <div class="xc-panel">
          <strong>{course}</strong><br/>
          <span class="xc-badge">Rating · {db.describe_course_rating(rating)}</span>
          <span class="xc-badge" style="margin-left:0.4rem;">Top 7 / team</span>
          <span class="xc-badge" style="margin-left:0.4rem;">
            {result["n_teams"]} teams · {result["race_athletes"]} athletes
          </span>
          <p style="margin:0.75rem 0 0;color:#5b6d66;">
            Ranked {result["teams_scored_nationally"]} scoring teams nationally, then
            simulated a race with the top {result["n_teams"]}.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not result["teams"]:
        st.warning("Not enough teams with five predicted scorers for this gender.")
        st.stop()

    render_team_meet_analysis(result, show_incomplete=False, expand_winner=True)
