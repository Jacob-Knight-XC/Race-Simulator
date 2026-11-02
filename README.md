# Cross Country Race Simulator

Simulate collegiate cross country team and individual races from TFRRS
result history. The app rates course difficulty from relative athlete
paces and predicts finish times with a weighted Riegel conversion.

## Setup

```bash
pip install -r requirements.txt
```

## Run the UI

```bash
cd Source-Code/User-Interface
streamlit run UI.py
```

The browser opens automatically. Use the sidebar pages:

1. **Individual Race** / **Team Race** — pick athletes or teams and a course
2. **Individual Race Visual** / **Team Race Visual** — see predicted results

Home (`UI.py`) also has a quick athlete lookup with race history, course
ratings, averages, and a neutral-course prediction.

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

Only needed if you want newer season data. From `Source-Code/`:

```bash
pip install scrapy itemadapter
scrapy crawl xc
```

The crawl can take 20–30 minutes. Existing databases live under
`Source-Code/User-Interface/racedata.db` and `Source-Code/Datasets/`.
