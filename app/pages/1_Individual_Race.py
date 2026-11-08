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
    remove_icon_button,
    selectbox_compat,
    stop_if_division_db_missing,
    stretch_kwargs,
    team_selectbox,
)

apply_theme("Individual Race · XC Sim")
stop_if_division_db_missing()
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

        add_col, clear_col = st.columns(2)
        with add_col:
            if st.button("Add athlete", **stretch_kwargs()) and athlete:
                st.session_state.gender_lst.append(gender)
                st.session_state.team_lst.append(team)
                st.session_state.athlete_lst.append(athlete)
        with clear_col:
            if st.button(
                "Clear field",
                **stretch_kwargs(),
                disabled=not st.session_state.athlete_lst,
            ):
                clear_individual_field()
                st.rerun()

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
                if st.button("Save field", **stretch_kwargs()):
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
                    **stretch_kwargs(),
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
                if st.button("Load", **stretch_kwargs(), disabled=not pick):
                    st.session_state.pending_individual_load = get_lineup(
                        "individual", pick
                    )
                    st.rerun()

    with right:
        st.markdown(
            f"**Field size:** {len(st.session_state.athlete_lst)} athlete(s)"
        )
        if not st.session_state.athlete_lst:
            st.caption("No athletes added yet.")
        else:
            hdr = st.columns([1.1, 2.2, 2.6, 0.55])
            for col, label in zip(hdr, ["Gender", "Team", "Athlete", ""]):
                col.caption(label)
            for idx, (g, tname, aname) in enumerate(
                zip(
                    st.session_state.gender_lst,
                    st.session_state.team_lst,
                    st.session_state.athlete_lst,
                )
            ):
                cols = st.columns([1.1, 2.2, 2.6, 0.55])
                cols[0].write("Men" if g == "m" else "Women")
                cols[1].write(tname)
                cols[2].write(aname)
                with cols[3]:
                    if remove_icon_button(
                        key=f"rm_individual_{idx}_{aname}",
                        help_text=f"Remove {aname}",
                    ):
                        st.session_state.gender_lst.pop(idx)
                        st.session_state.team_lst.pop(idx)
                        st.session_state.athlete_lst.pop(idx)
                        st.rerun()
        if st.session_state.athlete_lst:
            if st.button(
                "View individual results",
                **stretch_kwargs(),
            ):
                st.switch_page("pages/2_Individual_Results.py")
