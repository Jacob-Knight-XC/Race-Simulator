import streamlit as st

from ui_helpers import (
    apply_theme,
    cached_top_athletes,
    content_frame,
    course_selector,
    gender_selector,
    get_db,
    page_header,
    show_table,
)

apply_theme("Top 100 Athletes · XC Sim")
db = get_db()

with content_frame():
    page_header(
        "Top 100 Athletes",
        "National individual board from predicted course-adjusted times.",
    )

    left, right = st.columns([1, 1], gap="large")
    with left:
        course = course_selector(db, key="national_athletes_course")
    with right:
        gender = gender_selector(key="national_athletes_gender")

    rating = db.get_course_rating(course)
    rows = cached_top_athletes(gender, course, limit=100)
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

    show_table(
        {
            "Place": list(range(1, len(rows) + 1)),
            "Team": [row[1] for row in rows],
            "Athlete": [row[2] for row in rows],
            "Predicted Time": [row[3] for row in rows],
        }
    )
