import streamlit as st

from ui_helpers import (
    apply_theme,
    begin_content,
    course_selector,
    end_content,
    ensure_session_defaults,
    gender_selector,
    get_db,
    page_header,
    show_table,
)

apply_theme("Individual Race · XC Sim")
db = get_db()
ensure_session_defaults()

page_header(
    "Individual Race",
    "Build a field of athletes and choose the course they’ll race on. "
    "Open Individual Results when the lineup is ready.",
)

begin_content()
left, right = st.columns([1.1, 1])
with left:
    st.markdown('<div class="xc-panel">', unsafe_allow_html=True)
    course_selector(db)
    gender = gender_selector()
    team_names = [name for name, _ in db.get_teams(gender)]
    team = st.selectbox("Team", team_names)
    team_id = db.get_team_id(team, gender)
    roster = db.get_roster(team_id) if team_id else []
    athlete_names = [name for name, _ in roster]
    athlete = st.selectbox("Athlete", athlete_names)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Add athlete", use_container_width=True) and athlete:
            st.session_state.gender_lst.append(gender)
            st.session_state.team_lst.append(team)
            st.session_state.athlete_lst.append(athlete)
    with c2:
        if st.button("Remove last", use_container_width=True) and st.session_state.athlete_lst:
            st.session_state.gender_lst.pop()
            st.session_state.team_lst.pop()
            st.session_state.athlete_lst.pop()
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        f"**Field size:** {len(st.session_state.athlete_lst)} athlete(s)"
    )
    show_table(
        {
            "Gender": [
                "Men" if g == "m" else "Women" for g in st.session_state.gender_lst
            ],
            "Team": st.session_state.team_lst,
            "Athlete": st.session_state.athlete_lst,
        }
    )
    if st.session_state.athlete_lst:
        st.link_button(
            "View individual results",
            "/Individual_Results",
            use_container_width=True,
        )
end_content()
