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
    remove_icon_button,
    roster_depth_selector,
    selectbox_compat,
    stop_if_division_db_missing,
    stretch_kwargs,
    team_selectbox,
)

apply_theme("Team Race · XC Sim")
stop_if_division_db_missing()
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
        st.session_state.team_tuple.append([g, tname, list(roster)])
    course = pending.get("course")
    if course:
        st.session_state.selected_course = course
        st.session_state["team_course"] = course
    if missing:
        st.session_state["team_load_missing"] = missing

with content_frame():
    page_header(
        "Team Race",
        "Select full team rosters and a course. Scratch injured / unavailable "
        "runners from a team’s roster before opening Team Results.",
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

        add_col, clear_col = st.columns(2)
        with add_col:
            if st.button("Add team", **stretch_kwargs()) and roster:
                st.session_state.team_tuple.append([gender, team, list(roster)])
        with clear_col:
            if st.button(
                "Clear meet",
                **stretch_kwargs(),
                disabled=not st.session_state.team_tuple,
            ):
                clear_team_field()
                st.rerun()

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
                if st.button("Save meet", **stretch_kwargs()):
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
                    **stretch_kwargs(),
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
                if st.button("Load", **stretch_kwargs(), disabled=not pick):
                    st.session_state.pending_team_load = get_lineup("team", pick)
                    st.rerun()

    with right:
        depth_limit = roster_depth_selector(key="team_roster_depth")
        st.markdown(f"**Meet size:** {len(st.session_state.team_tuple)} team(s)")
        if not st.session_state.team_tuple:
            st.caption("No teams added yet.")
        else:
            for idx, entry in enumerate(list(st.session_state.team_tuple)):
                g, tname, team_roster = entry
                gender_label = "Men" if g == "m" else "Women"
                in_race = (
                    len(team_roster)
                    if depth_limit is None
                    else min(len(team_roster), depth_limit)
                )
                top = st.columns([5.2, 0.55])
                top[0].markdown(
                    f"**{tname}** · {gender_label} · "
                    f"{len(team_roster)} on roster · {in_race} in race"
                )
                with top[1]:
                    if remove_icon_button(
                        key=f"rm_team_{idx}_{tname}",
                        help_text=f"Remove {tname}",
                    ):
                        st.session_state.team_tuple.pop(idx)
                        st.rerun()

                with st.expander(
                    f"Edit roster · {tname}",
                    expanded=False,
                ):
                    if not team_roster:
                        st.caption("No athletes left on this roster.")
                    for j, athlete_entry in enumerate(list(team_roster)):
                        if (
                            isinstance(athlete_entry, (list, tuple))
                            and len(athlete_entry) >= 2
                        ):
                            ath_name, ath_id = athlete_entry[0], athlete_entry[1]
                        else:
                            ath_name, ath_id = str(athlete_entry), j
                        cols = st.columns([5.2, 0.55])
                        cols[0].write(ath_name)
                        with cols[1]:
                            if remove_icon_button(
                                key=f"rm_roster_{idx}_{j}_{ath_id}",
                                help_text=f"Scratch {ath_name}",
                            ):
                                del entry[2][j]
                                st.rerun()

        if st.session_state.team_tuple:
            if st.button(
                "View team results",
                **stretch_kwargs(),
            ):
                st.switch_page("pages/4_Team_Results.py")
