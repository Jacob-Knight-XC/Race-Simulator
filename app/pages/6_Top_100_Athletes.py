import streamlit as st

from ui_helpers import (
    add_athlete_exclusion,
    apply_theme,
    cached_top_athletes,
    content_frame,
    course_selector,
    current_division,
    gender_selector,
    get_athlete_exclusions,
    get_db,
    page_header,
    remove_icon_button,
    render_excluded_athletes_panel,
    stop_if_division_db_missing,
)

PAGE_EXCL = "top100"

apply_theme("Top 100 Athletes · XC Sim")
stop_if_division_db_missing()
db = get_db()
div = current_division()

with content_frame():
    page_header(
        "Top 100 Athletes",
        f"{div.short} individual board from predicted course-adjusted times. "
        "Scratch a runner with × and the next athlete moves into the Top 100.",
    )

    left, right = st.columns([1, 1], gap="large")
    with left:
        course = course_selector(db, key="national_athletes_course")
    with right:
        gender = gender_selector(key="national_athletes_gender")

    exclusions = get_athlete_exclusions(PAGE_EXCL, gender)
    rating = db.get_course_rating(course)
    rows = cached_top_athletes(
        gender, course, limit=100, exclude_keys=exclusions
    )
    distance = db.TARGET_LABEL.get(gender, "race")

    st.markdown(
        f"""
        <div class="xc-panel">
          <strong>{course}</strong><br/>
          <span class="xc-badge">Rating · {db.describe_course_rating(rating)}</span>
          <span class="xc-badge" style="margin-left:0.4rem;">
            Top {len(rows)} · {distance}
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_excluded_athletes_panel(PAGE_EXCL, gender)

    if not rows:
        st.warning("No predicted times available for this gender.")
        st.stop()

    team_counts: dict[str, int] = {}
    for row in rows:
        team_counts[row[1]] = team_counts.get(row[1], 0) + 1
    top_teams = sorted(team_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    st.markdown(
        "**Most represented teams:** "
        + ", ".join(f"{name} ({count})" for name, count in top_teams)
    )

    header = st.columns([0.8, 2.4, 2.8, 1.6, 0.55])
    for col, label in zip(header, ["Place", "Team", "Athlete", "Time", ""]):
        col.caption(label)
    for place, row in enumerate(rows, start=1):
        team, athlete, time_str = row[1], row[2], row[3]
        cols = st.columns([0.8, 2.4, 2.8, 1.6, 0.55])
        cols[0].write(str(place))
        cols[1].write(team)
        cols[2].write(athlete)
        cols[3].write(time_str)
        with cols[4]:
            if remove_icon_button(
                key=f"excl_top100_{gender}_{place}_{team}|{athlete}",
                help_text=f"Remove {athlete}",
            ):
                add_athlete_exclusion(PAGE_EXCL, gender, team, athlete)
                st.rerun()
