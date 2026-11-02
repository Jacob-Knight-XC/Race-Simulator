"""Shared Streamlit helpers and visual system for the race simulator."""

from __future__ import annotations

import streamlit as st

from race_db import RaceDB

NEUTRAL_COURSE = "Average / Neutral"

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Sora:wght@400;500;600;700&display=swap');

:root {
  --pine: #12352c;
  --pine-deep: #0b241e;
  --canopy: #1f6b4f;
  --fog: #eef3f0;
  --chalk: #f7faf8;
  --ink: #15241f;
  --muted: #5b6d66;
  --signal: #c98512;
  --line: rgba(18, 53, 44, 0.12);
}

html, body, [class*="css"] {
  font-family: "Sora", sans-serif;
  color: var(--ink);
}

.stApp {
  background:
    radial-gradient(1200px 500px at 12% -10%, rgba(31, 107, 79, 0.18), transparent 55%),
    radial-gradient(900px 420px at 88% 0%, rgba(201, 133, 18, 0.12), transparent 50%),
    linear-gradient(180deg, #e7efea 0%, #eef3f0 42%, #f4f7f5 100%);
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg width='160' height='80' viewBox='0 0 160 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 60 C30 40, 50 70, 80 50 S130 20, 160 35' fill='none' stroke='%1212352c' stroke-width='2'/%3E%3Cpath d='M0 30 C40 10, 70 45, 100 25 S140 5, 160 18' fill='none' stroke='%1212352c' stroke-width='1.5'/%3E%3C/svg%3E");
  background-size: 320px 160px;
  z-index: 0;
}

[data-testid="stHeader"] {
  background: transparent;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f2f27 0%, #12352c 100%);
  border-right: 1px solid rgba(255,255,255,0.06);
}

[data-testid="stSidebar"] * {
  color: #e8f2ec !important;
}

[data-testid="stSidebarNav"] a {
  border-radius: 10px !important;
  margin: 0.15rem 0.4rem !important;
  font-family: "Sora", sans-serif !important;
  font-weight: 500 !important;
}

[data-testid="stSidebarNav"] a:hover {
  background: rgba(255,255,255,0.08) !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
  background: rgba(201, 133, 18, 0.22) !important;
  box-shadow: inset 3px 0 0 var(--signal);
}

.block-container {
  padding-top: 0 !important;
  padding-bottom: 4rem !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  max-width: 100% !important;
}

section.main .block-container {
  overflow: visible !important;
}

.xc-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 clamp(1.25rem, 4vw, 2.5rem);
}

.xc-hero {
  position: relative;
  width: 100%;
  margin: 0 0 2.75rem 0;
  min-height: min(78vh, 720px);
  padding: clamp(2.5rem, 8vh, 5.5rem) clamp(1.5rem, 6vw, 5rem) 3rem;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  border-radius: 0;
  overflow: hidden;
  color: #f4faf7;
  background:
    linear-gradient(115deg, rgba(11, 36, 30, 0.94) 0%, rgba(18, 53, 44, 0.78) 52%, rgba(31, 107, 79, 0.45) 100%),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1600' height='900' viewBox='0 0 1600 900'%3E%3Crect fill='%120b241e' width='1600' height='900'/%3E%3Cpath d='M0 620 C220 540, 360 700, 560 610 S920 480, 1120 560 1440 700, 1600 620 L1600 900 L0 900 Z' fill='%121f6b4f' opacity='.35'/%3E%3Cpath d='M0 700 C260 640, 420 780, 680 700 S1100 560, 1340 660 1520 760, 1600 720 L1600 900 L0 900 Z' fill='%12c98512' opacity='.16'/%3E%3C/svg%3E");
  background-size: cover;
  background-position: center;
  animation: xc-rise 700ms ease-out both;
}

.xc-hero-inner {
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
}

.xc-hero::after {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 4px;
  background: linear-gradient(90deg, var(--signal), transparent 70%);
}

.xc-brand {
  font-family: "Barlow Condensed", sans-serif;
  font-weight: 700;
  font-size: clamp(4rem, 10vw, 7rem);
  letter-spacing: 0.045em;
  line-height: 0.9;
  margin: 0 0 1rem 0;
  text-transform: uppercase;
  color: #f7fbf8 !important;
  text-shadow: 0 10px 40px rgba(0, 0, 0, 0.28);
}

.xc-kicker {
  display: inline-block;
  font-family: "Barlow Condensed", sans-serif;
  font-size: 0.95rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #f0d089;
  margin-bottom: 0.7rem;
}

.xc-lede {
  max-width: 34rem;
  font-size: 1.05rem;
  line-height: 1.55;
  color: rgba(244, 250, 247, 0.88);
  margin: 0 0 1.4rem 0;
}

.xc-cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.xc-cta {
  display: inline-block;
  padding: 0.7rem 1.15rem;
  border: 1px solid rgba(255,255,255,0.35);
  color: #fff !important;
  text-decoration: none !important;
  font-family: "Barlow Condensed", sans-serif;
  font-size: 1.05rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  transition: background 160ms ease, border-color 160ms ease, transform 160ms ease;
}

.xc-cta:hover {
  background: rgba(201, 133, 18, 0.28);
  border-color: #f0d089;
  transform: translateY(-1px);
}

.xc-cta-primary {
  background: var(--signal);
  border-color: var(--signal);
  color: #1a1408 !important;
}

.xc-section {
  margin: 2.25rem 0 1rem;
  animation: xc-fade 650ms ease-out both;
}

.xc-section h2, .xc-section-title {
  font-family: "Barlow Condensed", sans-serif;
  font-weight: 650;
  font-size: 2rem;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--pine);
  margin: 0 0 0.35rem 0;
}

.xc-section p, .xc-section-copy {
  color: var(--muted);
  max-width: 40rem;
  margin: 0 0 1.1rem 0;
}

.xc-panel {
  background: rgba(247, 250, 248, 0.78);
  border: 1px solid var(--line);
  border-left: 3px solid var(--canopy);
  padding: 1.1rem 1.2rem;
  margin: 0.85rem 0 1.25rem;
  backdrop-filter: blur(6px);
}

.xc-metric-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin: 1rem 0 1.5rem;
}

.xc-metric {
  padding: 0.9rem 1rem;
  background: rgba(247, 250, 248, 0.9);
  border-top: 2px solid var(--canopy);
}

.xc-metric-label {
  font-family: "Barlow Condensed", sans-serif;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 0.85rem;
  color: var(--muted);
}

.xc-metric-value {
  font-family: "Barlow Condensed", sans-serif;
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--pine);
  line-height: 1.1;
  margin-top: 0.2rem;
}

.xc-badge {
  display: inline-block;
  font-family: "Barlow Condensed", sans-serif;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.9rem;
  padding: 0.2rem 0.55rem;
  border: 1px solid var(--line);
  color: var(--pine);
  background: rgba(255,255,255,0.55);
}

h1, h2, h3 {
  font-family: "Barlow Condensed", sans-serif !important;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--pine) !important;
}

h1.xc-brand,
.xc-brand {
  color: #f7fbf8 !important;
}

div[data-testid="stRadio"] label,
div[data-testid="stSelectbox"] label,
.stTextInput label {
  font-family: "Barlow Condensed", sans-serif !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.9rem !important;
  color: var(--muted) !important;
}

.stButton > button {
  font-family: "Barlow Condensed", sans-serif !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: 0 !important;
  border: 1px solid var(--pine) !important;
  background: var(--pine) !important;
  color: #f4faf7 !important;
  transition: transform 140ms ease, background 140ms ease;
}

.stButton > button:hover {
  background: var(--canopy) !important;
  transform: translateY(-1px);
}

[data-testid="stDataFrame"] {
  border: 1px solid var(--line);
  background: rgba(247, 250, 248, 0.92);
}

@keyframes xc-rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes xc-fade {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .xc-hero { padding: 1.8rem 1.25rem; }
  .xc-brand { font-size: 3rem; }
}
</style>
"""


@st.cache_resource
def get_db() -> RaceDB:
    return RaceDB()


def apply_theme(page_title: str = "XC Race Simulator") -> None:
    st.set_page_config(
        page_title=page_title,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(THEME_CSS, unsafe_allow_html=True)


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
    course = st.selectbox("Course", meet_options, index=index)
    st.session_state["selected_course"] = course
    rating = db.describe_course_rating(db.get_course_rating(course))
    st.markdown(
        f'<span class="xc-badge">Course rating · {rating}</span>',
        unsafe_allow_html=True,
    )
    return course


def selected_course() -> str:
    ensure_session_defaults()
    return st.session_state.get("selected_course", NEUTRAL_COURSE)


def page_header(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="xc-wrap">
          <div class="xc-section">
            <h2 class="xc-section-title">{title}</h2>
            <p class="xc-section-copy">{copy}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def begin_content() -> None:
    st.markdown('<div class="xc-wrap">', unsafe_allow_html=True)


def end_content() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def metric_row(items: list[tuple[str, str]]) -> None:
    cells = "".join(
        f'<div class="xc-metric"><div class="xc-metric-label">{label}</div>'
        f'<div class="xc-metric-value">{value}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="xc-metric-row">{cells}</div>', unsafe_allow_html=True)


def gender_selector(label: str = "Gender") -> str:
    choice = st.radio(label, ("Men", "Women"), horizontal=True)
    return "m" if choice == "Men" else "f"
