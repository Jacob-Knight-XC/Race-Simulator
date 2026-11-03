# Cross Country Race Simulator

Simulate collegiate cross country team and individual races from TFRRS
result history. The app rates course difficulty from relative athlete
paces and predicts finish times with a weighted Riegel conversion.

## Layout

```
app/                 Streamlit simulator (run from here)
  Home.py            Landing page + athlete lookup
  race_db.py         Database access, course ratings, predictions
  pages/             Individual / team race setup and results
scraper/             Scrapy project that refreshes TFRRS data
  tfrrs/             Spider, items, and SQLite pipeline
data/
  archives/          Older season database snapshots
  scrape_errors.log  Teams skipped during a scrape (no roster)
tests/               Algorithm smoke tests
```

## Setup

```bash
pip install -r requirements.txt
```

## Run the simulator

```bash
cd app
streamlit run Home.py
```

Sidebar pages:

1. **Individual Race** — pick athletes and a course (fuzzy search + saved lineups)
2. **Individual Results** — predicted individual finishes
3. **Team Race** — pick teams and a course (fuzzy search + saved lineups)
4. **Team Results** — NCAA team scores + individual board

Team, athlete, and course pickers support type-to-search when your
Streamlit version includes selectbox filtering (roughly 1.39+). Older
Streamlit installs still run; dropdowns just won’t filter as you type.
On the race pages, open **Saved lineups** to name and reuse a field or
meet. Lineups are stored locally in `app/saved_lineups.json` (gitignored).

## Race algorithm

For each athlete the simulator:

1. Converts every valid race to an equivalent flat time at 8k (men) or
   6k (women) with Riegel's formula (`T2 = T1 * (D2/D1)^1.06`)
2. Season-adjusts early meets toward peak fitness (~2.5% early-season
   slowdown fading by mid-November) so September races don’t look
   permanently worse than November ones
3. Removes the source meet's course difficulty so performances are
   comparable across venues
4. Weights recent races more, gives a mild boost to stronger races, and
   trusts NCAA regional/national (and pre-national) results more than
   regular-season invites — conference championships are not boosted
5. Re-applies the selected course's difficulty for the simulated race

Course ratings compare each athlete’s season-adjusted Riegel 8k-equivalent
at a meet to that athlete’s median (collegiate distances only, 4k–10k),
then take the meet median. When meet pages have been scraped, ratings group
by venue coordinates (else city/state, else normalized meet name). Sparse
meets get a mild elevation/weather nudge. Factors are clipped to about
`0.95–1.08`.

Team scores follow NCAA rules: top five score, top seven displace.

## Optional: refresh the scrape

Only needed for newer season data. From `scraper/`:

```bash
scrapy crawl xc
```

Or run `scripts/refresh_racedata.sh`. The crawl can take 20–30+ minutes and
writes to `app/racedata.db`. It now also visits meet pages for venue/location
and enriches meets with elevation + daily weather (Open-Meteo).

A GitHub Actions workflow (`.github/workflows/weekly-racedata-refresh.yml`)
runs that refresh every Monday and commits DB updates back to `main`. You can
also trigger it manually from the Actions tab (`workflow_dispatch`).

## Tests

```bash
make tests
```
