"""Shared Streamlit helpers for the race simulator UI."""

from __future__ import annotations

import streamlit as st

from race_db import RaceDB

NEUTRAL_COURSE = "Average / Neutral"


@st.cache_resource
def get_db() -> RaceDB:
    return RaceDB()


def show_table(data: dict) -> None:
    """Render a compact results table without a pandas index column."""
    st.dataframe(data, hide_index=True, use_container_width=True)


def ensure_session_defaults() -> None:
    defaults = {
        "gender_lst": [],
        "team_lst": [],
        "athlete_lst": [],
        "team_tuple": [],
        "selected_course": NEUTRAL_COURSE,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def course_selector(db: RaceDB) -> str:
    """Render course dropdown + rating caption; persist selection."""
    ensure_session_defaults()
    meet_options = [NEUTRAL_COURSE] + db.get_meet_names()
    current = st.session_state["selected_course"]
    index = meet_options.index(current) if current in meet_options else 0
    course = st.selectbox("Simulate on course:", meet_options, index=index)
    st.session_state["selected_course"] = course
    st.caption(
        "Course rating: " + db.describe_course_rating(db.get_course_rating(course))
    )
    return course


def selected_course() -> str:
    ensure_session_defaults()
    return st.session_state.get("selected_course", NEUTRAL_COURSE)
