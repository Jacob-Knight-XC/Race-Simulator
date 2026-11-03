# Cross Country Race Simulator

A Streamlit app for **NCAA Division III cross country** that turns TFRRS race
history into comparable predictions across athletes, teams, and courses.

The goal is fair head-to-head simulation even when runners have never raced
each other — East vs Midwest vs West, different calendars, different venues —
by normalizing distance, course difficulty, season timing, and (when available)
venue elevation/weather.

Live deploy (Streamlit Community Cloud) can point at this repo’s `main` branch
with main file `app/Home.py`.

It is currently already live at https://xc-race-simulator.streamlit.app

## What you can do

| Page | Purpose |
|------|---------|
| **Home** | Athlete lookup: race history, course ratings, neutral-course prediction |
| **Individual Race** | Build a mixed field (searchable team/athlete pickers, saved lineups) |
| **Individual Results** | Predicted places and times on the selected course |
| **Team Race** | Line up full team rosters; choose Top 7 / Top 10 / All athletes |
| **Team Results** | NCAA scoring, 1–5 / 1–7 spreads, scorer vs displacer breakdown, insights |
| **Top 30 Teams** | National team sim (each team’s top 7, then re-race the best 30) |
| **Top 100 Athletes** | National individual board for the selected gender/course |

Extras:

- Fuzzy search for teams, athletes, and courses (Streamlit ~1.39+)
- Saved lineups (local `app/saved_lineups.json`, gitignored)
- Course picker badges for rating, venue, elevation, and weather when scraped

## Project layout

```
app/                 Streamlit simulator (run from here)
  Home.py            Landing page + athlete lookup
  race_db.py         SQLite access, course ratings, predictions, scoring
  lineups.py         Saved lineup persistence
  ui_helpers.py      Theme, pickers, shared results UI
  pages/             Individual / team / national ranking pages
  racedata.db        TFRRS-backed SQLite database
scraper/             Scrapy project that refreshes TFRRS data
  tfrrs/             Spider, items, SQLite pipeline, Open-Meteo enrichment
scripts/             refresh_racedata.sh, enrich_meets.py
.github/workflows/   Weekly racedata refresh on GitHub Actions
data/                Archives + scrape error log
tests/               Algorithm smoke tests
```

## Setup

```bash
pip install -r requirements.txt
```

Python **3.11 or 3.12** is recommended (Streamlit Cloud may pick newer
interpreters; pin 3.12 in Cloud settings if builds get flaky).

## Run the simulator

```bash
cd app
streamlit run Home.py
```

## Race-time prediction — what goes into it

For each athlete, the model builds a course-adjusted predicted finish at the
standard collegiate distance (**8k men**, **6k women**):

1. **Distance normalization (Riegel)**  
   Every valid past race is converted to an equivalent time at the target
   distance:  
   `T2 = T1 × (D2 / D1)^1.06`

2. **Season-progress adjustment**  
   Early-season races are treated as ~**2.5% slower** than late-season peak
   fitness. That penalty fades from late August toward mid-November so
   September results don’t permanently look worse than November ones.

3. **Strip source-course difficulty**  
   Divide out the rating of the meet where the race was run, so performances
   become more comparable across venues.

4. **Weighted blend of history**  
   - **Recency** — newer races count more (half-life ~45 days)  
   - **Form** — mildly prefer stronger-than-average races (boost capped at ~18%)  
   - **Meet importance** — NCAA regionals / nationals / pre-nationals get
     extra weight; **conference championships are not boosted** (tactical /
     uneven conference depth)

5. **Apply the simulated course**  
   Multiply the flat prediction by the selected course’s difficulty factor.

Athletes with too little usable history show as insufficient data.

## Course difficulty rating — what goes into it

Course (meet) ratings are multiplicative factors:

- **`1.000`** = average  
- **Higher** = harder / slower  
- **Lower** = faster  

They are clipped to roughly **`0.95–1.08`** so a “hard” course slows a ~24:00
8k by about **1–2 minutes**, not extreme outliers.

### How a meet gets its rating

1. Use **collegiate XC distances only** (about **4k–10k**). Short mini-meets
   (e.g. ~2k) are excluded so they can’t invent fake “hard” courses.
2. Convert each performance to an **8k-equivalent** (Riegel) and
   **season-adjust** toward peak fitness.
3. Compare that time to the **athlete’s own median** equivalent  
   (“everyone slow vs themselves → hard course; lots of PRs → fast course”).
4. Take the **median** of those athlete ratios at the meet (need enough
   samples). Per-athlete ratios are winsorized before the median.
5. **Group by venue** when location is known:
   - prefer lat/lon from scraped meet pages  
   - else city/state  
   - else normalized meet name (years stripped so `2024 Foo` / `2025 Foo` share a key)
6. **Sparse meets** can get a mild nudge from environment before clipping:
   - elevation (higher → slightly harder)  
   - precipitation (wetter → slightly harder)  
   - hot temperatures (slightly harder)  
   Empirical athlete-vs-self ratios stay primary; weather/elev are a light prior.

Venue, elevation, and daily weather come from TFRRS meet pages + **Open-Meteo**
enrichment after the scrape.

## Team scoring

NCAA rules in the simulator:

- Top **five** score  
- Top **seven** displace  
- Team Results also show scoring places, **1–5 / 1–7 spreads**, scorers vs
  displacers, and short coaching insights  

On Team Race / Team Results you can limit each roster to **Top 7** (default),
**Top 10**, or **All athletes** by predicted time before scoring.

## Keeping the database up to date

Full TFRRS refresh (can take 45–60+ minutes):

```bash
# from repo root
scripts/refresh_racedata.sh

# or
cd scraper && scrapy crawl xc
```

The spider pulls teams, athletes, and races; follows meet result pages for
venue/location; then enriches meets with geocode, elevation, and daily weather.

**Weekly automation:**  
`.github/workflows/weekly-racedata-refresh.yml` runs every Monday (and on
manual `workflow_dispatch`), scrapes TFRRS, and commits an updated
`app/racedata.db` to `main` when data changes. Streamlit Cloud can redeploy
from that commit.

## Tests

```bash
make tests
```

## Deploy (Streamlit Community Cloud)

1. Connect this GitHub repo  
2. Branch: `main`  
3. Main file: `app/Home.py`  
4. Deploy  

Prefer pinning the Cloud runtime to **Python 3.12** for stability.
It is currently already live at https://xc-race-simulator.streamlit.app
