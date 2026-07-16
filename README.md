# On Record — a living atmosphere

The world's remaining carbon budget, drawn as a living sky — with one city's
86-year temperature record on the ground beneath it. Every number traces to a
named open source; nothing is hand-typed.

**Live in two tiers:**
- every visitor's browser fetches today's forecast (Open-Meteo, CC-BY) and the
  page scores it against the local record client-side; the carbon budget counts
  down against the visitor's own clock
- a nightly GitHub Action re-runs `pipeline.py` (stdlib only): fresh ERA5
  archive, NOAA CO₂, per-day distributions, rebuilt `index.html`

**Deploy (once):** push this repo to GitHub → Settings → Pages → deploy from
branch `main`, root. The Action keeps it fresh from then on.

Sources: ERA5 via Open-Meteo · NOAA GML · IGCC 2025 · Global Carbon Budget 2025 ·
Andre et al. 2024 (via Our World in Data) · full list in the site's Bedrock chamber.

Made by Agosh Baranwal · agoshbaranwal@gmail.com
