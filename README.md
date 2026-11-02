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

1. **Individual Race** — pick athletes and a course
2. **Individual Results** — predicted individual finishes
3. **Team Race** — pick teams and a course
4. **Team Results** — NCAA team scores + individual board

## Race algorithm

For each athlete the simulator:

1. Converts every valid race to an equivalent flat time at 8k (men) or
   6k (women) with Riegel's formula (`T2 = T1 * (D2/D1)^1.06`)
2. Removes the source meet's course difficulty so performances are
   comparable across venues
3. Weights recent races more heavily and trusts stronger performances a
   bit more
4. Re-applies the selected course's difficulty for the simulated race

Course ratings are medians of `race_pace / athlete_typical_pace` across
meets with enough samples. `1.000` is average, higher is harder/slower,
lower is faster.

Team scores follow NCAA rules: top five score, top seven displace.

## Optional: refresh the scrape

Only needed for newer season data. From `scraper/`:

```bash
scrapy crawl xc
```

The crawl can take 20–30 minutes and writes to `app/racedata.db`.

## Tests

```bash
make tests
```
