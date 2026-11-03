import streamlit as st

from lineups import delete_lineup, get_lineup, list_lineups, save_lineup
from ui_helpers import (
    apply_theme,
    athlete_selectbox,
    clear_individual_field,
    content_frame,
    course_selector,
    ensure_session_defaults,
    gender_selector,
    get_db,
    page_header,
    selectbox_compat,
    show_table,
    team_selectbox,
)

apply_theme("Individual Race · XC Sim")
db = get_db()
ensure_session_defaults()

# Apply pending lineup before widgets are created (Streamlit key rule).
pending = st.session_state.pop("pending_individual_load", None)
if pending:
    clear_individual_field()
    for row in pending.get("athletes") or []:
        st.session_state.gender_lst.append(row["gender"])
        st.session_state.team_lst.append(row["team"])
        st.session_state.athlete_lst.append(row["athlete"])
    course = pending.get("course")
    if course:
        st.session_state.selected_course = course
        st.session_state["individual_course"] = course

with content_frame():
    page_header(
        "Individual Race",
        "Build a field of athletes and choose the course they’ll race on. "
        "Open Individual Results when the lineup is ready.",
    )

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        course_selector(db, key="individual_course")
        gender = gender_selector()
        team_names = [name for name, _ in db.get_teams(gender)]
        team = team_selectbox(team_names, key=f"individual_team_{gender}")
        team_id = db.get_team_id(team, gender) if team else None
        roster = db.get_roster(team_id) if team_id else []
        athlete_names = [name for name, _ in roster]
        athlete = athlete_selectbox(
            athlete_names, key=f"individual_athlete_{gender}_{team}"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Add athlete", use_container_width=True) and athlete:
                st.session_state.gender_lst.append(gender)
                st.session_state.team_lst.append(team)
                st.session_state.athlete_lst.append(athlete)
        with c2:
            if (
                st.button("Remove last", use_container_width=True)
                and st.session_state.athlete_lst
            ):
                st.session_state.gender_lst.pop()
                st.session_state.team_lst.pop()
                st.session_state.athlete_lst.pop()

        with st.expander("Saved lineups", expanded=False):
            saved_names = list_lineups("individual")
            name = st.text_input(
                "Lineup name",
                placeholder="e.g. Wartburg dual preview",
                key="individual_lineup_name",
            )
            pick = st.session_state.get("individual_lineup_pick")
            if pick not in saved_names:
                pick = None

            save_col, delete_col = st.columns(2)
            with save_col:
                if st.button("Save field", use_container_width=True):
                    if not st.session_state.athlete_lst:
                        st.warning("Add at least one athlete before saving.")
                    elif not name.strip():
                        st.warning("Enter a lineup name.")
                    else:
                        payload = {
                            "course": st.session_state.selected_course,
                            "athletes": [
                                {
                                    "gender": g,
                                    "team": t,
                                    "athlete": a,
                                }
                                for g, t, a in zip(
                                    st.session_state.gender_lst,
                                    st.session_state.team_lst,
                                    st.session_state.athlete_lst,
                                )
                            ],
                        }
                        save_lineup("individual", name, payload)
                        st.success(f"Saved “{name.strip()}”.")
                        st.rerun()
            with delete_col:
                if st.button(
                    "Delete",
                    use_container_width=True,
                    disabled=not pick,
                ):
                    delete_lineup("individual", pick)
                    st.success(f"Deleted “{pick}”.")
                    st.rerun()

            pick_col, load_col = st.columns([4, 1])
            with pick_col:
                if saved_names:
                    pick = selectbox_compat(
                        "Saved lineup",
                        saved_names,
                        key="individual_lineup_pick",
                        placeholder="Choose a saved lineup…",
                        filter_mode="fuzzy",
                    )
                else:
                    pick = None
                    st.caption("No saved individual lineups yet.")
            with load_col:
                st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
                if st.button("Load", use_container_width=True, disabled=not pick):
                    st.session_state.pending_individual_load = get_lineup(
                        "individual", pick
                    )
                    st.rerun()

    with right:
        st.markdown(
            f"**Field size:** {len(st.session_state.athlete_lst)} athlete(s)"
        )
        show_table(
            {
                "Gender": [
                    "Men" if g == "m" else "Women"
                    for g in st.session_state.gender_lst
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
