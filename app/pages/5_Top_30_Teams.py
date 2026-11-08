import streamlit as st

from ui_helpers import (
    apply_theme,
    cached_national_top_teams_race,
    content_frame,
    course_selector,
    current_division,
    gender_selector,
    get_athlete_exclusions,
    get_db,
    page_header,
    render_excluded_athletes_panel,
    render_team_meet_analysis,
    stop_if_division_db_missing,
)

PAGE_EXCL = "top30"

apply_theme("Top 30 Teams · XC Sim")
stop_if_division_db_missing()
db = get_db()
div = current_division()

if div.national_teams_mode == "ustfccca":
    subtitle = (
        f"USTFCCCA {div.short} National Coaches Poll field — each ranked team "
        "enters its top 7, then we simulate that meet on the selected course. "
        "Nat'l # is the official poll ranking. Scratch a runner with × and the "
        "next teammate fills that Top 7 slot."
    )
else:
    subtitle = (
        f"Model Top 30 for {div.label} — the strongest predicted teams in the "
        f"{div.short} database (top 7 each). Scratch a runner with × and the "
        "next teammate fills that slot."
    )

with content_frame():
    page_header("Top 30 Teams", subtitle)

    left, right = st.columns([1, 1], gap="large")
    with left:
        course = course_selector(db, key="national_teams_course")
    with right:
        gender = gender_selector(key="national_teams_gender")

    exclusions = get_athlete_exclusions(PAGE_EXCL, gender)
    rating = db.get_course_rating(course)
    result = cached_national_top_teams_race(
        gender,
        course,
        n_teams=30,
        per_team=7,
        exclude_keys=exclusions,
    )
    poll = result.get("poll") or {}
    unmatched = [
        row
        for row in (result.get("poll_resolved") or [])
        if not row.get("matched")
    ] + (result.get("unmatched_poll_teams") or [])

    released = poll.get("released") or "latest"
    source = poll.get("source") or "live"
    page_url = poll.get("page") or div.tfrrs_league_url
    poll_label = poll.get("label") or (
        "USTFCCCA National Coaches Poll"
        if div.national_teams_mode == "ustfccca"
        else f"Model top teams ({div.short})"
    )

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
            Field from {poll_label} ({released}, {source}).
            <a href="{page_url}" target="_blank" rel="noopener">Source</a>
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

    render_excluded_athletes_panel(PAGE_EXCL, gender)

    if not result["teams"]:
        st.warning(
            "Not enough teams with five predicted scorers for this gender "
            f"in the {div.short} database."
        )
        st.stop()

    render_team_meet_analysis(
        result,
        show_incomplete=True,
        expand_winner=True,
        exclude_page=PAGE_EXCL,
        exclude_gender=gender,
    )
