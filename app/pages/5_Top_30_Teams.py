import streamlit as st

from ui_helpers import (
    apply_theme,
    cached_ustfccca_top_teams_race,
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
        "USTFCCCA NCAA DIII National Coaches Poll field — each ranked team enters "
        "its top 7, then we simulate that meet on the selected course. Nat'l # is "
        "the official poll ranking.",
    )

    left, right = st.columns([1, 1], gap="large")
    with left:
        course = course_selector(db, key="national_teams_course")
    with right:
        gender = gender_selector(key="national_teams_gender")

    rating = db.get_course_rating(course)
    result = cached_ustfccca_top_teams_race(gender, course, per_team=7)
    poll = result.get("poll") or {}
    unmatched = [
        row
        for row in (result.get("poll_resolved") or [])
        if not row.get("matched")
    ] + (result.get("unmatched_poll_teams") or [])

    released = poll.get("released") or "latest release"
    source = poll.get("source") or "live"
    page_url = poll.get("page") or "https://web4.ustfccca.org/iz/polls-rankings/xc"

    st.markdown(
        f"""
        <div class="xc-panel">
          <strong>{course}</strong><br/>
          <span class="xc-badge">Rating · {db.describe_course_rating(rating)}</span>
          <span class="xc-badge" style="margin-left:0.4rem;">Top 7 / team</span>
          <span class="xc-badge" style="margin-left:0.4rem;">
            {result["n_teams"]} poll teams · {result["race_athletes"]} athletes
          </span>
          <p style="margin:0.75rem 0 0;color:#5b6d66;">
            Field from the USTFCCCA National Coaches Poll ({released}, {source}).
            <a href="{page_url}" target="_blank" rel="noopener">View poll</a>
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if unmatched:
        missing = ", ".join(
            f"#{row.get('rank')} {row.get('ustfccca_name') or row.get('name')}"
            for row in unmatched
        )
        st.warning(f"Could not match poll teams in the local DB: {missing}")

    if not result["teams"]:
        st.warning("Not enough poll teams with five predicted scorers for this gender.")
        st.stop()

    render_team_meet_analysis(result, show_incomplete=True, expand_winner=True)
