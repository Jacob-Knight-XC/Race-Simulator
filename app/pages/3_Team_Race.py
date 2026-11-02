import streamlit as st

from ui_helpers import (
    apply_theme,
    content_frame,
    course_selector,
    ensure_session_defaults,
    gender_selector,
    get_db,
    page_header,
    show_table,
)

apply_theme("Team Race · XC Sim")
db = get_db()
ensure_session_defaults()

with content_frame():
    page_header(
        "Team Race",
        "Select full team rosters and a course. Open Team Results for NCAA scoring.",
    )

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown('<div class="xc-panel">', unsafe_allow_html=True)
        course_selector(db)
        gender = gender_selector()
        team_names = [name for name, _ in db.get_teams(gender)]
        team = st.selectbox("Team", team_names)
        team_id = db.get_team_id(team, gender)
        roster = db.get_roster(team_id) if team_id else []

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Add team", use_container_width=True) and roster:
                st.session_state.team_tuple.append([gender, team, roster])
        with c2:
            if (
                st.button("Remove last", use_container_width=True)
                and st.session_state.team_tuple
            ):
                st.session_state.team_tuple.pop()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(f"**Meet size:** {len(st.session_state.team_tuple)} team(s)")
        show_table(
            {
                "Gender": [
                    "Men" if entry[0] == "m" else "Women"
                    for entry in st.session_state.team_tuple
                ],
                "Team": [entry[1] for entry in st.session_state.team_tuple],
                "Runners": [len(entry[2]) for entry in st.session_state.team_tuple],
            }
        )
        if st.session_state.team_tuple:
            st.link_button(
                "View team results",
                "/Team_Results",
                use_container_width=True,
            )
