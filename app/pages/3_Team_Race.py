import streamlit as st

from lineups import delete_lineup, get_lineup, list_lineups, save_lineup
from ui_helpers import (
    apply_theme,
    clear_team_field,
    content_frame,
    course_selector,
    ensure_session_defaults,
    gender_selector,
    get_db,
    page_header,
    roster_depth_selector,
    selectbox_compat,
    show_table,
    team_selectbox,
)

apply_theme("Team Race · XC Sim")
db = get_db()
ensure_session_defaults()

pending = st.session_state.pop("pending_team_load", None)
if pending:
    clear_team_field()
    missing = []
    for row in pending.get("teams") or []:
        g = row["gender"]
        tname = row["team"]
        tid = db.get_team_id(tname, g)
        roster = db.get_roster(tid) if tid else []
        if not roster:
            missing.append(tname)
            continue
        st.session_state.team_tuple.append([g, tname, roster])
    course = pending.get("course")
    if course:
        st.session_state.selected_course = course
        st.session_state["team_course"] = course
    if missing:
        st.session_state["team_load_missing"] = missing

with content_frame():
    page_header(
        "Team Race",
        "Select full team rosters and a course. Open Team Results for NCAA scoring.",
    )

    missing = st.session_state.pop("team_load_missing", None)
    if missing:
        st.warning("Loaded with missing rosters: " + ", ".join(missing))

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        course_selector(db, key="team_course")
        gender = gender_selector()
        team_names = [name for name, _ in db.get_teams(gender)]
        team = team_selectbox(team_names, key=f"team_race_team_{gender}")
        team_id = db.get_team_id(team, gender) if team else None
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

        with st.expander("Saved lineups", expanded=False):
            saved_names = list_lineups("team")
            name = st.text_input(
                "Lineup name",
                placeholder="e.g. ARC conference field",
                key="team_lineup_name",
            )
            pick = st.session_state.get("team_lineup_pick")
            if pick not in saved_names:
                pick = None

            save_col, delete_col = st.columns(2)
            with save_col:
                if st.button("Save meet", use_container_width=True):
                    if not st.session_state.team_tuple:
                        st.warning("Add at least one team before saving.")
                    elif not name.strip():
                        st.warning("Enter a lineup name.")
                    else:
                        payload = {
                            "course": st.session_state.selected_course,
                            "teams": [
                                {"gender": entry[0], "team": entry[1]}
                                for entry in st.session_state.team_tuple
                            ],
                        }
                        save_lineup("team", name, payload)
                        st.success(f"Saved “{name.strip()}”.")
                        st.rerun()
            with delete_col:
                if st.button(
                    "Delete",
                    use_container_width=True,
                    disabled=not pick,
                ):
                    delete_lineup("team", pick)
                    st.success(f"Deleted “{pick}”.")
                    st.rerun()

            pick_col, load_col = st.columns([4, 1])
            with pick_col:
                if saved_names:
                    pick = selectbox_compat(
                        "Saved lineup",
                        saved_names,
                        key="team_lineup_pick",
                        placeholder="Choose a saved lineup…",
                        filter_mode="fuzzy",
                    )
                else:
                    pick = None
                    st.caption("No saved team lineups yet.")
            with load_col:
                st.markdown("<div style='height: 1.7rem'></div>", unsafe_allow_html=True)
                if st.button("Load", use_container_width=True, disabled=not pick):
                    st.session_state.pending_team_load = get_lineup("team", pick)
                    st.rerun()

    with right:
        depth_limit = roster_depth_selector(key="team_roster_depth")
        st.markdown(f"**Meet size:** {len(st.session_state.team_tuple)} team(s)")
        show_table(
            {
                "Gender": [
                    "Men" if entry[0] == "m" else "Women"
                    for entry in st.session_state.team_tuple
                ],
                "Team": [entry[1] for entry in st.session_state.team_tuple],
                "Roster": [len(entry[2]) for entry in st.session_state.team_tuple],
                "In race": [
                    len(entry[2])
                    if depth_limit is None
                    else min(len(entry[2]), depth_limit)
                    for entry in st.session_state.team_tuple
                ],
            }
        )
        if st.session_state.team_tuple:
            st.link_button(
                "View team results",
                "/Team_Results",
                use_container_width=True,
            )
