# On Record

**What will a child born today face, and what has already changed since 1975?**
The page opens on the next generation in the reader's country — lifetime
heatwaves, crop failures and floods, from Grant et al. 2025 (Nature, per-country
tables, CC BY) and Thiery et al. 2021 (Science) — then what is different since
1975 in their city (hot days, hot and humid days, hot nights, the 1970s against
the last ten years, from the weather record) and in the world (glaciers, reefs,
record years). The city's full record, what heat means for a body, why it is
happening and how long the world has, and what you can do follow. Before the
reader picks a city, their device's time zone names their country — on the
device, with nothing sent anywhere — and the city shown is a labelled example.
Every number traces to a named open source; nothing is hand-typed. The sky
behind it is the world's remaining carbon budget, drawn live.

Data tools: `tools/futures_bake.py` (the per-country table + time zones →
`data/futures.json`, once), `tools/hh_bake.py` (hot, humid days for the stored
cities; the nightly job runs it when a city is missing or the year rolls over).

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
