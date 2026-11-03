import streamlit as st

from ui_helpers import apply_theme, content_frame, page_header

apply_theme("About · XC Sim")

with content_frame():
    page_header(
        "About",
        "What this simulator is for, and how course difficulty and predicted times are built.",
    )

    st.markdown(
        """
        <div class="xc-panel">
          <strong>Purpose</strong>
          <p style="margin:0.75rem 0 0;color:#5b6d66;">
            College cross country is hard to compare across regions. An East Coast
            invitational in September is not the same race as a Midwest regional in
            November. This app uses TFRRS Division III history to estimate how
            athletes and teams would stack up on a chosen course — even when they
            have never raced each other.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### What you can simulate")
    st.markdown(
        """
- **Individual races** — build a mixed field and see predicted finishes  
- **Team races** — NCAA scoring with scorers, displacers, and pack spreads  
- **National boards** — USTFCCCA Top 30 poll field (top 7 each) and Top 100 athletes  
- **Athlete lookup** on Home — one runner’s history and a neutral-course estimate  
        """
    )

    st.markdown("#### Course difficulty")
    st.markdown(
        """
Course ratings are multiplicative factors around average:

- **`1.000`** — average course  
- **Higher** — harder / slower  
- **Lower** — faster  

Ratings are kept in a realistic band (about **`0.95–1.08`**), so a hard course
might add roughly **1–2 minutes** to a collegiate 8k — not extreme outliers.

**How a meet gets rated**

1. Use collegiate distances only (about **4k–10k**). Short mini-meets are skipped.  
2. Convert each performance to an **8k-equivalent** with Riegel’s formula, then
   nudge early-season races toward peak fitness.  
3. Compare that time to **the same athlete’s median** equivalent  
   (“everyone slow vs themselves → hard course; lots of PRs → fast course”).  
4. Take the **median** of those ratios across the meet.  
5. When venue data exists, group by **location** (coordinates, else city/state,
   else meet name with years stripped).  
6. Thinly sampled meets can get a mild nudge from **elevation / weather**
   (Open-Meteo). Athlete-vs-self ratios stay the main signal.
        """
    )

    st.markdown("#### Time predictions")
    st.markdown(
        """
For each athlete the model predicts a finish at the standard collegiate distance
(**8k men**, **6k women**):

1. **Distance** — convert past races with Riegel  
   (`T2 = T1 × (D2 / D1)^1.06`)  
2. **Season** — early races treated as ~2.5% slower than late-season peak fitness  
3. **Course strip** — divide out the rating of the meet where each race was run  
4. **Blend history** with weights for:
   - **Recency** (newer races count more)  
   - **Form** (mild preference for stronger races)  
   - **Meet importance** (NCAA regionals / nationals / pre-nationals weighted
     higher; conference meets are **not** boosted)  
5. **Apply** the selected course’s difficulty factor to the flat prediction  

Team scores then follow NCAA rules: top five score, top seven displace.
        """
    )

    st.markdown("#### Data")
    st.markdown(
        """
Results come from **TFRRS** via the project scraper. Meet pages supply venue
text; elevation and daily weather are enriched when available. The database can
be refreshed with the weekly GitHub Action or a local scrape
(`scripts/refresh_racedata.sh`).
        """
    )
