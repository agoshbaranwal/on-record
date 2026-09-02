#!/usr/bin/env python3
"""ON RECORD — the live data pipeline.
Fetches the verified open feeds, recomputes every number on the site, and rebuilds
index.html. Designed to run nightly in a scheduled job (stdlib only, fail-loud).

Sources (all open):
  ERA5 daily via Open-Meteo archive API (CC-BY)  — Seville + Delhi records
  NOAA GML CO2 trend CSV (public domain)          — masthead ppm
  IGCC 2025 / Global Carbon Budget 2025           — carbon-budget constants (annual, in code, flagged)

Outputs:
  data/site-data.json       — everything the page computes from
  data/perday-seville.json  — per-calendar-day distributions so the BROWSER can
                              score any day's live forecast against 86 years
  index.html                — the built site (template + fonts + data injected)
"""
import json, csv, io, math, statistics, time, urllib.request, datetime, pathlib, sys, hashlib, re
import buildlib   # shared impact.json + reuse.html helpers (Phase 9)

ROOT = pathlib.Path(__file__).parent
CACHE = ROOT / "spike" / "cache"; CACHE.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
UA = {"User-Agent": "on-record/1.0 (open climate site; agoshbaranwal@gmail.com)"}
TODAY = datetime.date.today()
ARCHIVE_END = TODAY - datetime.timedelta(days=6)   # ERA5 publication lag

def fetch(url, tries=4):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read().decode("utf-8", "replace")
                print(f"  {r.status} {len(data):>9,} B  {url[:96]}")
                return data
        except Exception as e:
            if attempt < tries - 1:
                wait = 30 * (attempt + 1)
                print(f"  retry in {wait}s ({e})"); time.sleep(wait)
            else:
                raise

def fetch_archive(city, lat, lon):
    """Fresh ERA5 daily archive 1940->lag; falls back to cache if the fetch fails."""
    cachef = CACHE / f"archive_{city}.json"
    try:
        txt = fetch(f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
                    f"&start_date=1940-01-01&end_date={ARCHIVE_END}"
                    f"&daily=temperature_2m_max,temperature_2m_min&timezone=auto")
        cachef.write_text(txt)
    except Exception as e:
        if not cachef.exists(): raise
        print(f"  !! live fetch failed ({e}) — using cached archive {cachef.name}")
        txt = cachef.read_text()
    d = json.loads(txt)["daily"]
    return [(datetime.date.fromisoformat(dt), tx, tn)
            for dt, tx, tn in zip(d["time"], d["temperature_2m_max"], d["temperature_2m_min"])
            if tx is not None]

print(f"[pipeline] {TODAY} — archive through {ARCHIVE_END}")
sev = fetch_archive("Seville", 37.39, -5.99)
delhi = fetch_archive("Delhi", 28.61, 77.21)

# ---------------- NOAA CO2 (live) ----------------
co2_ppm, co2_date = None, None
try:
    txt = fetch("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_trend_gl.csv")
    rows = [r for r in csv.reader(io.StringIO(txt))
            if r and len(r) >= 4 and r[0].strip().isdigit()]
    y, m, d = int(rows[-1][0]), int(rows[-1][1]), int(rows[-1][2])
    co2_ppm, co2_date = float(rows[-1][3]), f"{y}-{m:02d}-{d:02d}"
except Exception as e:
    print(f"  !! CO2 fetch failed ({e}) — keeping previous value if any")
    prev = DATA / "site-data.json"
    if prev.exists():
        p = json.loads(prev.read_text())["the_number"]
        co2_ppm, co2_date = p["co2_ppm"], p["co2_date"]
    else:
        raise
print(f"  CO2 {co2_ppm} ppm ({co2_date})")

# ---------------- helpers ----------------
def per_year_counts(recs, pred, y0=1940, y1=None):
    y1 = y1 or TODAY.year
    yrs = {}
    for dt, tx, tn in recs:
        if y0 <= dt.year <= y1:
            yrs.setdefault(dt.year, 0)
            if pred(tx, tn): yrs[dt.year] += 1
    return [{"year": y, "n": yrs[y]} for y in sorted(yrs)]

def mean_over(series, a, b):
    v = [r["n"] for r in series if a <= r["year"] <= b]
    return sum(v) / len(v)

LAST_FULL = TODAY.year - 1   # last complete calendar year

# ---------------- Seville: the record window (fixed early-summer showcase) ----------------
WIN = 50; ANCHOR = (6, 8)
by_year = {}
for dt, tx, tn in sev:
    a = datetime.date(dt.year, *ANCHOR)
    off = (dt - a).days
    if 0 <= off <= WIN:
        by_year.setdefault(dt.year, {})[off] = tx
years = sorted(by_year)
spaghetti = {str(y): [round(by_year[y][o], 1) if o in by_year[y] else None
                      for o in range(WIN + 1)] for y in years}
old_band, new_band, rec_env = [], [], []
for o in range(WIN + 1):
    old = [by_year[y][o] for y in years if 1951 <= y <= 1980 and o in by_year[y]]
    new = [by_year[y][o] for y in years if LAST_FULL-29 <= y <= LAST_FULL and o in by_year[y]]
    allv = [by_year[y][o] for y in years if o in by_year[y]]
    old_band.append(round(statistics.fmean(old), 1) if old else None)
    new_band.append(round(statistics.fmean(new), 1) if new else None)
    rec_env.append(round(max(allv), 1) if allv else None)
labels = [(datetime.date(2001, *ANCHOR) + datetime.timedelta(days=o)).strftime("%b %-d") for o in range(WIN + 1)]

# ---------------- Seville per-calendar-day distributions (for the LIVE browser) ----------------
by_md = {}          # (m,d) -> list of tmax across years (exact date)
for dt, tx, tn in sev:
    by_md.setdefault((dt.month, dt.day), []).append((dt.year, tx))
def window_vals(m, d, half=7):
    ref = datetime.date(2000, m, d)
    out = []
    for k in range(-half, half + 1):
        dd = ref + datetime.timedelta(days=k)
        out.extend(v for _, v in by_md.get((dd.month, dd.day), []))
    return out
def year_window_max(y, m, d, half=7):
    ref = datetime.date(2000, m, d); best = None
    for k in range(-half, half + 1):
        dd = ref + datetime.timedelta(days=k)
        for yy, v in by_md.get((dd.month, dd.day), []):
            if yy == y and (best is None or v > best): best = v
    return best
perday = {}
ref_year = 2000  # leap year → all 366 dates
d0 = datetime.date(ref_year, 1, 1)
for i in range(366):
    dd = d0 + datetime.timedelta(days=i)
    m, d = dd.month, dd.day
    vals = sorted(window_vals(m, d))
    if not vals: continue
    q = [round(vals[min(len(vals)-1, int(p/100*(len(vals)-1)))], 1) for p in range(0, 101)]
    exact = by_md.get((m, d), [])
    rec_y, rec_v = max(exact, key=lambda z: z[1]) if exact else (None, None)
    h40a = sum(1 for y in range(1951, 1981) if (year_window_max(y, m, d) or -99) >= 40)
    h40b = sum(1 for y in range(LAST_FULL-29, LAST_FULL+1) if (year_window_max(y, m, d) or -99) >= 40)
    perday[f"{m:02d}-{d:02d}"] = {"q": q, "rec": round(rec_v, 1), "recy": rec_y,
                                  "n": len(exact), "h40a": h40a, "h40b": h40b}
(DATA / "perday-seville.json").write_text(json.dumps(
    {"meta": {"place": "Seville", "src": "ERA5 via Open-Meteo (CC-BY)",
              "window": "±7 days", "years": f"1940–{ARCHIVE_END}", "built": str(TODAY),
              "eras": ["1951–1980", f"{LAST_FULL-29}–{LAST_FULL}"]},
     "days": perday}, separators=(",", ":")))
print(f"  perday-seville.json: {len(perday)} days")

# ---------------- headline stats ----------------
g35 = per_year_counts(sev, lambda x, n: x >= 35)
gwn = per_year_counts(sev, lambda x, n: n is not None and n >= 25)
d35 = per_year_counts(delhi, lambda x, n: x >= 35)
dwn = per_year_counts(delhi, lambda x, n: n is not None and n >= 25)
amt = {}
for dt, tx, tn in sev: amt.setdefault(dt.year, []).append(tx)
amt = {y: statistics.fmean(v) for y, v in amt.items()}
base_s = statistics.fmean([amt[y] for y in amt if 1951 <= y <= 1980])
delhi_amt = {}
for dt, tx, tn in delhi: delhi_amt.setdefault(dt.year, []).append(tx)
delhi_amt = {y: statistics.fmean(v) for y, v in delhi_amt.items()}

# today's calendar-date snapshot values (page fallback when live fetch is blocked)
mdkey = f"{TODAY.month:02d}-{TODAY.day:02d}"
today_pd = perday.get(mdkey) or perday[sorted(perday)[0]]

# build-time forecast: the snapshot the page ships with (the browser re-fetches live on load)
BIAS_C = -0.38   # measured forecast-vs-ERA5 offset (spike, Apr-Jun 2026); comparable = fc - BIAS
fc_tmax, fc_date = None, None
try:
    fc = json.loads(fetch("https://api.open-meteo.com/v1/forecast?latitude=37.39&longitude=-5.99"
                          "&daily=temperature_2m_max&forecast_days=1&timezone=auto"))
    fc_tmax, fc_date = float(fc["daily"]["temperature_2m_max"][0]), fc["daily"]["time"][0]
except Exception as e:
    print(f"  !! forecast fetch failed ({e}) — snapshot will carry no today-value")
def pct_of(v, q):
    if v is None: return None
    lo_i = sum(1 for x in q if x <= v)
    return round(100 * lo_i / len(q))
fc_comparable = None if fc_tmax is None else round(fc_tmax - BIAS_C, 1)
fc_pct = pct_of(fc_comparable, today_pd["q"]) if fc_tmax is not None else None
print(f"  build-time forecast: {fc_tmax} °C on {fc_date} → {fc_pct}th pct (adjusted {fc_comparable})")

out = {
 "_meta": {"built_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "archive_end": str(ARCHIVE_END), "today": str(TODAY),
           "note": "descriptive record only, never causal attribution; all sources open"},
 "seville_record_window": {
   "anchor": "Jun 8", "window_days": WIN + 1, "labels": labels,
   "today_offset": (TODAY - datetime.date(TODAY.year, *ANCHOR)).days,
   "spaghetti": spaghetti, "old_normal_1951_1980": old_band,
   "new_normal_last30": new_band, "new_normal_label": f"{LAST_FULL-29}–{LAST_FULL}",
   "record_envelope": rec_env},
 "seville_generational": {"days_ge35_per_year": g35, "warm_nights_ge25_per_year": gwn},
 "seville_stripes": {"baseline": "1951-1980 mean annual daily-high", "year0": min(amt),
   "anom": [round(amt[y] - base_s, 2) for y in sorted(amt) if y <= LAST_FULL]},
 "seville_frequency": {
   "same_date_record_C": today_pd["rec"], "same_date_record_year": today_pd["recy"],
   "jul3_n_years": today_pd["n"], "newest_obs": ARCHIVE_END.strftime("%-d %b %Y"),
   "ge40_early": {"years": 30, "hit": today_pd["h40a"]},
   "ge40_recent": {"years": 30, "hit": today_pd["h40b"]},
   "forecast_percentile": fc_pct,
   "bias_C": BIAS_C,
 },
 "today_snapshot": {
   "tmax_C": fc_tmax, "date": fc_date, "fetched": str(TODAY),
   "note": "build-time forecast; the browser re-fetches live on every visit"},
 "delhi_honesty": {
   "baseline": f"1951-1980 vs {LAST_FULL-9}-{LAST_FULL}",
   "days_ge35_per_year": [r for r in d35 if r["year"] <= LAST_FULL],
   "warm_nights_ge25_per_year": [r for r in dwn if r["year"] <= LAST_FULL],
   "receipts": {
     "days_ge35_then": round(mean_over(d35, 1951, 1980), 1),
     "days_ge35_now": round(mean_over(d35, LAST_FULL-9, LAST_FULL), 1),
     "warm_nights_then": round(mean_over(dwn, 1951, 1980), 1),
     "warm_nights_now": round(mean_over(dwn, LAST_FULL-9, LAST_FULL), 1),
     "mean_tmax_then": round(statistics.fmean([delhi_amt[y] for y in delhi_amt if 1951 <= y <= 1980]), 2),
     "mean_tmax_now": round(statistics.fmean([delhi_amt[y] for y in delhi_amt if LAST_FULL-9 <= y <= LAST_FULL]), 2)}},
 "perception_gap": {
   "source": "Andre, Boneva, Chopra & Falk 2024, Nature Climate Change; per-country via Our World in Data (CC-BY)",
   "construct": "share saying they would contribute 1% of household income, every month; vs average guess",
   "global_want_action_pct": 89,
   "countries": [{"place": "India", "actual": 64, "guess": 36},
                 {"place": "Spain", "actual": 65, "guess": 41},
                 {"place": "Indonesia", "actual": 80, "guess": 44}],
   "_verify": "figures + exact item wording re-verified against the paper at build"},
 "the_number": {"co2_ppm": co2_ppm, "co2_date": co2_date},
 "how_we_know": {
   "what_is_era5": "ERA5 is the ECMWF's hour-by-hour reconstruction of global weather since 1940, built by feeding every available measurement (stations, ships, satellites) into a physics model on a ~30 km grid.",
   "seville_forecast_vs_reanalysis_bias_C": {"n_days": 70, "mean_C": -0.38, "median_C": -0.3, "p90_abs_C": 1.5},
   "bias_note": "measured in the spike, Apr–Jun 2026; remeasured periodically",
   "station_validation": "declared next step: cross-check vs a licence-clean nearby station series"},
}

# ---------------- carbon budget (annual constants; LIVE elapsed is computed in the browser) ----------------
RATE = 42.2
_est = [
 {"key": "igcc", "gt": 130, "anchor_dec": 2026.0, "odds": "50%", "target": "1.5 °C",
  "label": "IGCC 2025 — Forster et al., ESSD",
  "src": "Indicators of Global Climate Change 2025 — Forster et al., ESSD",
  "anchor": "counted from start of 2026"},
 {"key": "gcb", "gt": 170, "anchor_dec": 2025.0, "odds": "50%", "target": "1.5 °C",
  "label": "Global Carbon Budget 2025 (GCP)",
  "src": "Global Carbon Budget 2025 (Global Carbon Project)",
  "anchor": "counted from start of 2025"},
]
now_dec = TODAY.year + (TODAY.timetuple().tm_yday - 1) / 365.25
for e in _est:
    e["elapsed_gt"] = round(RATE * (now_dec - e["anchor_dec"]), 1)
    e["remaining_now_gt"] = round(e["gt"] - e["elapsed_gt"], 1)
    e["years_at_now"] = round(e["remaining_now_gt"] / RATE, 2)
_est.sort(key=lambda e: e["remaining_now_gt"])
out["budget"] = {
 "rate_now_gt": RATE, "now_dec": round(now_dec, 3), "now_label": TODAY.strftime("%-d %b %Y"),
 "rate_src": "Global Carbon Budget 2025 (Global Carbon Project) — total CO2 incl. land use; fossil alone 38.1",
 "estimates": _est,
 "human_induced": {"c": 1.37, "per_decade": 0.27,
                   "src": "IGCC 2025 (Forster et al.) — human-induced warming vs 1850-1900"},
 "tcre": {"c_per_1000gt": 0.45, "likely_lo": 0.27, "likely_hi": 0.63,
          "src": "IPCC AR6 WG1 — transient climate response to cumulative CO2 emissions, "
                 "best estimate 0.45 C per 1000 GtCO2 (likely 0.27-0.63)",
          "_verify": "re-check against AR6 WG1 SPM / Ch.5 wording at build"},
 "scc": {"usd_per_t": 190, "discount": "2% discount rate",
         "src": "US EPA, Dec 2023 — 2% discount rate; assumption-dependent range"},
 "notes": [
   "Budgets are re-estimated yearly and have been revised downward; we show both current estimates, never an average.",
   "1.5 °C is a dial of rising risk, not a cliff: worse at 1.6 than 1.5, worse again at 1.7.",
   "Years = remaining budget / rate, held from today - arithmetic, not a pathway model.",
   "Each budget is published against its own start date; we subtract emissions elapsed since that date at the current rate to bring both to one day. The subtraction is shown in the table.",
 ],
 "_verify": "figures, anchors and the held-rate assumption re-verified against the named releases annually"}

# ---------------- the real night sky ----------------
# Star positions from the Yale Bright Star Catalogue and IAU constellation figures,
# via d3-celestial (Olaf Frohn, BSD-3-Clause). The browser computes alt/az for Delhi
# at the visitor's clock — the night chamber's sky is a simulation, not decoration.
# The procession holds 13 constellations: the ecliptic genuinely crosses Ophiuchus.
def fetch_sky():
    def cached(url, name):
        cf = CACHE / name
        try:
            txt = fetch(url); cf.write_text(txt)
        except Exception as e:
            if not cf.exists(): raise
            print(f"  !! sky fetch failed ({e}) — using cached {name}")
            txt = cf.read_text()
        return json.loads(txt)
    stars = cached("https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/stars.6.json",
                   "sky_stars6.json")
    lines = cached("https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/constellations.lines.json",
                   "sky_clines.json")
    ss = []
    for f in stars["features"]:
        m = f["properties"].get("mag")
        if m is None or m > 5.0: continue
        ra, dec = f["geometry"]["coordinates"]
        try: bv = float(f["properties"].get("bv") or 0.0)
        except (TypeError, ValueError): bv = 0.0
        ss.append([round(ra % 360.0, 2), round(dec, 2), round(m, 1), round(bv, 2)])
    ss.sort(key=lambda s: s[2])
    ZOD = ["Ari","Tau","Gem","Cnc","Leo","Vir","Lib","Sco","Oph","Sgr","Cap","Aqr","Psc"]
    NAMES = {"Ari":"Aries","Tau":"Taurus","Gem":"Gemini","Cnc":"Cancer","Leo":"Leo","Vir":"Virgo",
             "Lib":"Libra","Sco":"Scorpius","Oph":"Ophiuchus","Sgr":"Sagittarius","Cap":"Capricornus",
             "Aqr":"Aquarius","Psc":"Pisces"}
    figs = {}
    for f in lines["features"]:
        if f["id"] not in ZOD: continue
        figs[f["id"]] = {"n": NAMES[f["id"]],
                         "l": [[[round(a % 360.0, 2), round(d, 2)] for a, d in seg]
                               for seg in f["geometry"]["coordinates"]]}
    missing = [z for z in ZOD if z not in figs]
    if missing: raise RuntimeError(f"constellation lines missing: {missing}")
    return {"stars": ss, "zod": figs, "order": ZOD,
            "src": "Yale Bright Star Catalogue via d3-celestial (Olaf Frohn, BSD-3-Clause); "
                   "alt/az computed in-browser for Delhi (Meeus / Schlyter low-precision algorithms)"}
# ---------------- perception gap: the full Andre et al. per-country dataset ----------------
# Andre, Boneva, Chopra & Falk 2024 (Nature Climate Change) — processed by Our World in Data,
# CC BY 4.0. One CSV holds actual + perceived willingness; a second the demand for government action.
def fetch_owid_pg():
    base = "https://ourworldindata.org/grapher/"
    def cached_csv(slug, name):
        cf = CACHE / name
        try:
            txt = fetch(base + slug + ".csv?v=1&csvType=full&useColumnShortNames=true")
            cf.write_text(txt)
        except Exception as e:
            if not cf.exists(): raise
            print(f"  !! OWID fetch failed ({e}) — using cached {name}")
            txt = cf.read_text()
        return list(csv.DictReader(io.StringIO(txt)))
    will = cached_csv("willingness-climate-action", "owid_willingness.csv")
    govt = cached_csv("support-political-climate-action", "owid_govt.csv")
    gmap = {}
    for r in govt:
        try: gmap[r["code"]] = round(float(r["demand_political_action_climate"]), 1)
        except (KeyError, ValueError, TypeError): pass
    allc, world = [], None
    for r in will:
        try:
            a = float(r["willingness_contribute_pct_climate"])
            g = float(r["willingness_contribute_1pct_climate_others"])
        except (KeyError, ValueError, TypeError): continue
        row = {"place": r["entity"], "code": r.get("code") or "",
               "actual": round(a, 1), "guess": round(g, 1)}
        if row["code"] in gmap: row["govt"] = gmap[row["code"]]
        if r["entity"] == "World": world = row
        else: allc.append(row)
    if len(allc) < 100 or world is None:
        raise RuntimeError(f"OWID perception data looks wrong: {len(allc)} countries, world={world}")
    allc.sort(key=lambda x: x["place"])
    return allc, world
_allc, _world = fetch_owid_pg()
out["perception_gap"]["all"] = _allc
out["perception_gap"]["world"] = _world
out["perception_gap"]["owid_attrib"] = ("Andre et al. (2024), Globally representative evidence on the "
    "actual and perceived support for climate action — processed by Our World in Data (CC BY 4.0)")
print(f"  perception gap: {len(_allc)} countries + World (actual {_world['actual']} / guess {_world['guess']})")

# Where money is vetted to move the needle — names re-checked annually, framings quoted with caveats.
out["giving"] = {
 "src": "Giving Green Top Climate Nonprofits 2025-26 (givinggreen.earth); Founders Pledge Climate Fund",
 "_verify": "recommendation lists and framings re-checked against the named pages annually",
 "orgs": [
  {"n": "Clean Air Task Force", "w": "policy advocacy for neglected low-carbon technology"},
  {"n": "Future Cleantech Architects", "w": "hard-to-abate industry research and EU policy"},
  {"n": "Good Food Institute", "w": "alternative proteins against livestock emissions"},
  {"n": "Opportunity Green", "w": "aviation and shipping decarbonisation law and policy"},
  {"n": "Project InnerSpace", "w": "next-generation geothermal"}],
 "funds": [{"n": "Giving Green Fund", "u": "givinggreen.earth/giving-green-fund"},
           {"n": "Founders Pledge Climate Fund", "u": "founderspledge.com/programs/climate-fund"}],
 "framing": ("Their vetters' own framing: the best picks average roughly $1 per tonne of EXPECTED CO2 "
             "avoided — a modelled expectation, not measured tonnes — and roughly ten times the impact "
             "of high-quality offsets. Systems change over offset math.")}

out["sky"] = fetch_sky()
print(f"  sky: {len(out['sky']['stars'])} stars ≤ mag 5.0 · {len(out['sky']['zod'])} zodiacal figures (incl. Ophiuchus)")

# Major annual meteor showers — IMO 2026 Meteor Shower Calendar (Rendtel ed., IMO_INFO(3-25),
# DOI 10.13140/RG.2.2.36179.08480); parent bodies per the IMO working list. Radiant RA/Dec in
# degrees at maximum (J2000); ZHR = zenithal hourly rate at peak under ideal dark skies.
# Peak dates are exact for 2026 only — re-enter from the new IMO calendar each year.
out["showers"] = {
 "src": "IMO Meteor Shower Calendar 2026, ed. J. Rendtel — imo.net; parents per IMO working list",
 "_verify": "windows, 2026 peaks, radiants and ZHRs re-checked against the IMO calendar annually",
 "list": [
  {"code":"QUA","name":"Quadrantids","a":"12-28","b":"01-12","peak":"2026-01-03","ra":230,"dec":49,"zhr":80,"parent":"asteroid 2003 EH1"},
  {"code":"LYR","name":"Lyrids","a":"04-14","b":"04-30","peak":"2026-04-22","ra":271,"dec":34,"zhr":18,"parent":"comet Thatcher, C/1861 G1"},
  {"code":"ETA","name":"eta Aquariids","a":"04-19","b":"05-28","peak":"2026-05-06","ra":338,"dec":-1,"zhr":50,"parent":"comet 1P/Halley"},
  {"code":"SDA","name":"Southern delta Aquariids","a":"07-12","b":"08-23","peak":"2026-07-31","ra":340,"dec":-16,"zhr":25,"parent":"comet 96P/Machholz, probable"},
  {"code":"CAP","name":"alpha Capricornids","a":"07-03","b":"08-15","peak":"2026-07-31","ra":307,"dec":-10,"zhr":5,"parent":"comet 169P/NEAT"},
  {"code":"PER","name":"Perseids","a":"07-17","b":"08-24","peak":"2026-08-13","ra":48,"dec":58,"zhr":100,"parent":"comet 109P/Swift-Tuttle"},
  {"code":"ORI","name":"Orionids","a":"10-02","b":"11-07","peak":"2026-10-21","ra":95,"dec":16,"zhr":20,"parent":"comet 1P/Halley"},
  {"code":"LEO","name":"Leonids","a":"11-06","b":"11-30","peak":"2026-11-17","ra":152,"dec":22,"zhr":15,"parent":"comet 55P/Tempel-Tuttle"},
  {"code":"GEM","name":"Geminids","a":"12-04","b":"12-20","peak":"2026-12-14","ra":112,"dec":33,"zhr":150,"parent":"asteroid 3200 Phaethon"},
  {"code":"URS","name":"Ursids","a":"12-17","b":"12-26","peak":"2026-12-22","ra":217,"dec":76,"zhr":10,"parent":"comet 8P/Tuttle"}]}

# ---------------- impact.json — outcome-side measurement only, NEVER the visitor ----------------
# Folded into `out` (so the page reads D.impact with no runtime fetch/beacon) AND written as a
# standalone artifact press can cite. A metric whose fetch fails is dropped + listed in `omitted`.
impact = buildlib.impact_dict(fetch, TODAY, ARCHIVE_END, ROOT, out["_meta"]["built_utc"])
out["impact"] = impact
(DATA / "impact.json").write_text(json.dumps(impact, separators=(",", ":")))
print(f"  impact.json: {len(impact['metrics'])} metrics, {len(impact['omitted'])} omitted")

# The instant-place table (20 cities baked from the v2 ingest) is maintained OUTSIDE this
# nightly build — attach it, never regenerate it here. Without this line the nightly would
# silently drop D.instant and the zero-latency picker + the compare feature die overnight.
# The season ring for the worked example. It lives in `out` like every other figure, because
# it was hand-added to site-data.json once and tonight's build would have silently deleted it —
# the ring would have vanished from the default view with every check still passing.
_ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTU"
_ML = [31,28,31,30,31,30,31,31,30,31,30,31]
_DOY, _s = {}, 0
for _m in range(12):
    for _dd in range(1, _ML[_m] + 1):
        _DOY["%02d-%02d" % (_m + 1, _dd)] = _s; _s += 1
_DOY["02-29"] = _DOY["02-28"]
_rA, _rB = [0] * 365, [0] * 365
for _dt, _tx, _tn in sev:
    if _tx is None or _tx < 35: continue
    _sl = _DOY.get("%02d-%02d" % (_dt.month, _dt.day))
    if _sl is None: continue
    if 1951 <= _dt.year <= 1980: _rA[_sl] += 1
    elif LAST_FULL - 29 <= _dt.year <= LAST_FULL: _rB[_sl] += 1
assert max(_rA) <= 30 and max(_rB) <= 30, "a 30-year era cannot hold more than 30 hits on one day"
out["seville_ring"] = {"a": "".join(_ALPHA[v] for v in _rA), "b": "".join(_ALPHA[v] for v in _rB),
                       "eraA": "1951\u201380", "eraB": f"{LAST_FULL-29}\u2013{LAST_FULL}",
                       "years": 30, "alpha": _ALPHA, "thr": 35}
print(f"  seville_ring: {sum(_rA)} \u2192 {sum(_rB)} hot days per 30-year era")

_inst = DATA / "instant-places.json"
if _inst.exists():
    out["instant"] = json.loads(_inst.read_text())
# data keys the page cannot render without — _KEEP guards ELEMENTS, and an element whose
# data has gone missing still passes that check while drawing nothing.
for _k in ("seville_ring", "instant", "seville_generational", "seville_stripes"):
    assert _k in out and out[_k], f"site-data.json would ship without {_k}"
assert "_ring" in out["instant"], "the instant table lost its ring metadata"
(DATA / "site-data.json").write_text(json.dumps(out, separators=(",", ":")))
print(f"  site-data.json written ({(DATA/'site-data.json').stat().st_size:,} B)")

# ---------------- build index.html ----------------
tpl = (ROOT / "instrument.html").read_text()
fonts = json.loads((ROOT / "fonts" / "fonts-b64.json").read_text())
css = ""   # Helvetica everywhere: no webfont to embed
lo, hi = out["budget"]["estimates"][0], out["budget"]["estimates"][1]
dr = out["delhi_honesty"]["receipts"]
ns = (f"This page draws its instrument with JavaScript. The core numbers, without it: the remaining carbon "
      f"budget for 1.5 °C is about {lo['remaining_now_gt']:.0f}–{hi['remaining_now_gt']:.0f} GtCO₂ from "
      f"{out['budget']['now_label']} — roughly {lo['years_at_now']:.1f}–{hi['years_at_now']:.1f} years at today's "
      f"~{RATE} GtCO₂/yr (IGCC 2025; Global Carbon Budget 2025). Seville: days ≥35 °C rose "
      f"{mean_over(g35,1951,1980):.0f}→{mean_over(g35,LAST_FULL-9,LAST_FULL):.0f} a year (1951–80 vs "
      f"{LAST_FULL-9}–{LAST_FULL}, ERA5). Delhi's hot nights rose {dr['warm_nights_then']:.0f}→"
      f"{dr['warm_nights_now']:.0f} while hot days edged down. 89% worldwide want stronger government "
      f"climate action (Andre et al. 2024).")
body = (tpl.replace("/*__FONTS__*/", css)
           .replace("/*__DATA__*/ null", json.dumps(out, separators=(",", ":")))
           .replace("/*__NOSCRIPT__*/", ns))
(ROOT / "onrecord-heat-mockup.html").write_text(body)
# ---- link-preview / OG meta (a real static preview image lives at og/seville.png, baked from the same card engine) ----
OG = "https://agoshbaranwal.github.io/on-record/"
_was = round(mean_over(g35, 1951, 1980))                    # same decade means the card/noscript use — never hand-typed
_now = round(mean_over(g35, LAST_FULL - 9, LAST_FULL))
DESC = ("We counted it from the weather record &mdash; every day since 1940. Pick your place and the page redraws around it: your hot days, your nights, your sky. Every number shows where it came from.")
CARD = (f"Seville: {_was} days a year above 35 \u00B0C in 1951\u201380, {_now} now. "
        f"Check your own city.")
ALT = f"On Record card: in Seville, days at or above 35C rose from {_was} a year to {_now}."
head_meta = (
    "<title>On Record \u2014 how many hot days does your city get?</title>"
    '<meta name="description" content="' + DESC + '">'
    '<link rel="canonical" href="' + OG + '">'
    '<meta property="og:type" content="website">'
    '<meta property="og:site_name" content="On Record">'
    '<meta property="og:title" content="On Record — how many hot days does your city get?">'
    '<meta property="og:description" content="' + CARD + '">'
    '<meta property="og:url" content="' + OG + '">'
    '<meta property="og:image" content="' + OG + 'og/seville.png">'
    '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
    '<meta property="og:image:alt" content="' + ALT + '">'
    '<meta name="twitter:card" content="summary_large_image">'
    '<meta name="twitter:title" content="On Record — how many hot days does your city get?">'
    '<meta name="twitter:description" content="' + CARD + '">'
    '<meta name="twitter:image" content="' + OG + 'og/seville.png">'
    # PWA: installable, offline-capable (network-first SW), zero tracking
    '<link rel="manifest" href="manifest.webmanifest">'
    '<meta name="theme-color" content="#05171A">'
    '<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2032%2032%22%3E%3Cpath%20d%3D%22M6.5%2010.0%20L6.92%2010.33%20L7.35%2010.64%20L7.78%2010.92%20L8.2%2011.17%20L8.62%2011.37%20L9.05%2011.51%20L9.47%2011.59%20L9.9%2011.6%20L10.32%2011.54%20L10.75%2011.42%20L11.18%2011.24%20L11.6%2011.0%20L12.03%2010.73%20L12.45%2010.42%20L12.88%2010.1%20L13.3%209.77%20L13.72%209.45%20L14.15%209.16%20L14.57%208.9%20L15.0%208.68%20L15.43%208.53%20L15.85%208.43%20L16.27%208.4%20L16.7%208.44%20L17.12%208.54%20L17.55%208.71%20L17.98%208.92%20L18.4%209.19%20L18.82%209.49%20L19.25%209.81%20L19.68%2010.14%20L20.1%2010.46%20L20.52%2010.76%20L20.95%2011.03%20L21.38%2011.26%20L21.8%2011.43%20L22.23%2011.55%20L22.65%2011.6%20L23.07%2011.58%20L23.5%2011.5%22%20fill%3D%22none%22%20stroke%3D%22%23F2E7CC%22%20stroke-width%3D%222.4%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20opacity%3D%22.42%22%2F%3E%3Cpath%20d%3D%22M6.5%2024.25%20L6.86%2024.41%20L7.22%2024.52%20L7.59%2024.58%20L7.95%2024.6%20L8.31%2024.57%20L8.68%2024.49%20L9.04%2024.36%20L9.4%2024.19%20L9.76%2023.99%20L10.12%2023.75%20L10.49%2023.49%20L10.85%2023.22%20L11.21%2022.94%20L11.57%2022.66%20L11.94%2022.4%20L12.3%2022.15%20L12.66%2021.92%20L13.03%2021.73%20L13.39%2021.58%20L13.75%2021.48%20L14.11%2021.41%20L14.48%2021.4%20L14.84%2021.44%20L15.2%2021.52%20L15.56%2021.65%20L15.93%2021.82%20L16.29%2022.03%20L16.65%2022.26%20L17.01%2022.52%20L17.38%2022.8%20L17.74%2023.08%20L18.1%2023.35%20L18.46%2023.62%20L18.82%2023.87%20L19.19%2024.09%20L19.55%2024.28%20L19.91%2024.43%20L20.27%2024.53%20L20.64%2024.59%20L21.0%2024.6%22%20fill%3D%22none%22%20stroke%3D%22%23F2E7CC%22%20stroke-width%3D%222.4%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20opacity%3D%22.42%22%2F%3E%3Cpath%20d%3D%22M6.5%2017.15%20L6.97%2017.61%20L7.45%2018.01%20L7.92%2018.34%20L8.4%2018.56%20L8.88%2018.68%20L9.35%2018.69%20L9.82%2018.58%20L10.3%2018.36%20L10.78%2018.04%20L11.25%2017.64%20L11.73%2017.18%20L12.2%2016.69%20L12.68%2016.19%20L13.15%2015.7%20L13.62%2015.25%20L14.1%2014.87%20L14.57%2014.58%20L15.05%2014.39%20L15.53%2014.3%20L16.0%2014.34%20L16.48%2014.48%20L16.95%2014.73%20L17.42%2015.08%20L17.9%2015.5%20L18.38%2015.97%20L18.85%2016.47%20L19.33%2016.97%20L19.8%2017.45%20L20.27%2017.87%20L20.75%2018.23%20L21.23%2018.49%20L21.7%2018.65%20L22.17%2018.7%20L22.65%2018.63%20L23.12%2018.45%20L23.6%2018.17%20L24.07%2017.8%20L24.55%2017.36%20L25.02%2016.87%20L25.5%2016.37%22%20fill%3D%22none%22%20stroke%3D%22%23FF6B52%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E"><link rel="apple-touch-icon" href="og/icon-192.png">'
)
doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width, initial-scale=1">'
       + head_meta +
       '</head><body>' + body + "</body></html>")
# ── bake the headline + recap numbers into the static document ─────────────────────
# Ported from tools/build_offline.py: without this, the nightly regeneration REVERTS every
# baked number to an em-dash and the served page claims nothing again. The JS writes the
# same values a moment later, so the two cannot disagree.
def _bake(doc):
    import re as _re
    _est = sorted(out["budget"]["estimates"], key=lambda e: e["remaining_now_gt"])
    _hi = _est[-1]; _rate = out["budget"]["rate_now_gt"]; _nowdec = out["budget"]["now_dec"]
    def _src(e): return "IGCC 2025" if "IGCC" in (e.get("label") or "") else "GCB 2025"
    _ylo = _est[0]["remaining_now_gt"] / _rate; _yhi = _hi["remaining_now_gt"] / _rate
    _yrs = f"{_ylo:.1f}" if f"{_ylo:.1f}" == f"{_yhi:.1f}" else f"{_ylo:.1f}\u2013{_yhi:.1f}"
    _nights = out["seville_generational"]["warm_nights_ge25_per_year"]
    def _nmean(a, b):
        v = [r["n"] for r in _nights if a <= r["year"] <= b]
        return round(sum(v) / len(v)) if v else 0
    _P = out["perception_gap"]
    subs = {"lead-gt": "%d\u2013%d" % (round(_est[0]["remaining_now_gt"]), round(_hi["remaining_now_gt"])),
            "g-then": str(round(mean_over(g35, 1951, 1980))),
            "g-now": str(round(mean_over(g35, LAST_FULL - 9, LAST_FULL))),
            "rc-1-n": f"{round(mean_over(g35,1951,1980))} \u2192 {round(mean_over(g35,LAST_FULL-9,LAST_FULL))} days a year",
            "n-big": "+%d " % round(out["delhi_honesty"]["receipts"]["warm_nights_now"] - out["delhi_honesty"]["receipts"]["warm_nights_then"]),
            "rc-2-n": "%d \u2192 %d nights a year" % (round(out["delhi_honesty"]["receipts"]["warm_nights_then"]), round(out["delhi_honesty"]["receipts"]["warm_nights_now"])),
            "rc-3-n": f"{round(_P['global_want_action_pct'])}% want action",
            "rc-4-n": f"{_yrs} years of budget left",
            "spent": (f"{round(_est[0]['remaining_now_gt'])}\u2013{round(_hi['remaining_now_gt'])} Gt remain "
                      f"\u00b7 {_src(_est[0])} and {_src(_hi)} agree \u00b7 spent around {round(_nowdec+_ylo)}")}
    n_done = 0
    for eid, val in subs.items():
        pat = _re.compile(r'(id="%s"[^>]*>)[^<]*(<)' % _re.escape(eid))
        doc, k = pat.subn(lambda m: m.group(1) + val + m.group(2), doc, count=1)
        n_done += k
    print(f"  baked {n_done} static numbers")
    return doc
doc = _bake(doc)
(ROOT / "index.html").write_text(doc)
# ---- protected-requirement invariant (Phase 10 kill-list): fail the build if a distinct capability is dropped ----
# ---- cities-lookup.json: names a located reader's city ON THEIR DEVICE ----
# The browser fetches this and finds the nearest city itself, so a coordinate is never sent to
# anyone to be identified. Non-fatal: if GeoNames is down, yesterday's file stands and the site
# simply calls a located reader "your place".
try:
    import zipfile as _zf
    _req = urllib.request.Request("https://download.geonames.org/export/dump/cities15000.zip",
                                  headers={"User-Agent": "on-record/1.0 (agoshbaranwal@gmail.com)"})
    _z = _zf.ZipFile(io.BytesIO(urllib.request.urlopen(_req, timeout=90).read()))
    _rows = [l.split("\t") for l in _z.read("cities15000.txt").decode("utf-8").splitlines()]
    _big = sorted([r for r in _rows if int(r[14] or 0) >= 100000], key=lambda r: -int(r[14]))
    assert len(_big) > 4000, "GeoNames returned an implausibly short city list: %d" % len(_big)
    (DATA / "cities-lookup.json").write_text(json.dumps(
        {"note": "GeoNames cities>=100k (CC BY 4.0). Used ON DEVICE to name a located reader's "
                 "nearest city; no coordinate is ever sent anywhere to be named.",
         "source": "GeoNames cities15000, CC BY 4.0", "n": len(_big),
         "c": [[r[1], round(float(r[4]), 3), round(float(r[5]), 3), r[8]] for r in _big]},
        separators=(",", ":"), ensure_ascii=False))
    print("cities-lookup:", len(_big), "cities")
except Exception as _e:
    print("cities-lookup: SKIPPED (keeping the existing file) —", _e)

# "burned" retired with the live "burned while you've been here" counter: its scope was
# never checkable and P1 cut it. _KEEP catches ACCIDENTS, so a deliberate cut edits it.
_KEEP = ["years", "spent", "copysky", "share-btn", "t-budget", "takeaway", "g-verdict", "impact-know", "ledger-sr", "homepick", "gq-bar", "gq-ex", "homechip", "n-example", "pk-ask", "rc-1-n", "cmp-grid", "recap-list"]
_missing = [k for k in _KEEP if ('id="%s"' % k) not in doc]
assert not _missing, "PROTECTED elements dropped from index.html: %s" % _missing

# ---- localization invariants: these are honesty guarantees, not style preferences ----
# The sourced aerosol explanation may exist exactly ONCE, inside buildNightExample(), whose only
# data source is Delhi's baked series. More than one copy means some code path can attach Delhi's
# physical cause to a reader's own city.
assert doc.count("Padma Kumari et al. 2007, GRL)") == 1   # the citation, not one phrasing of the sentence around it
# Exactly one place may raise a location prompt, and it must be __HOME.ask.
assert doc.count("navigator.geolocation.getCurrentPosition") == 1, \
    "getCurrentPosition must have exactly one caller (__HOME.ask)"
# The superseded per-chapter sky key must never be written again.
assert 'setItem("onrecord_skyloc"' not in doc, "the legacy onrecord_skyloc key must not be written"
# Every fallback city's country must be in the perception survey, or FIRST LIGHT dead-ends.
_codes = {r.get("code") for r in (out["perception_gap"].get("all") or out["perception_gap"]["countries"])}
_bar = re.findall(r'\{s:"([a-z-]+)",n:"[^"]*",f:"[^"]*",la:[-\d.]+,lo:[-\d.]+,tz:"[^"]*",c:"([A-Z]{3})"', doc)
assert len(_bar) == 24, "expected 24 fallback cities, found %d" % len(_bar)
_unsurveyed = sorted({c for s, c in _bar if c not in _codes})
assert not _unsurveyed, "fallback cities whose country is not in the survey: %s" % _unsurveyed
assert not ({"seville", "delhi"} & {s for s, c in _bar}), \
    "Seville and Delhi belong in the examples row, not the fallback bar"
# ---- stamp the service worker so every nightly build busts the offline cache ----
# BUILD changes when the build time OR the built HTML changes → sw.js differs byte-for-byte
# → the browser detects an update, the new cache name supersedes, old caches are purged.
_swstamp = re.sub(r"[^0-9]", "", out["_meta"]["built_utc"])[:14] + "-" + hashlib.sha1(doc.encode()).hexdigest()[:8]
_sw = (ROOT / "sw.js").read_text()
_sw = re.sub(r'const BUILD = "[^"]*";', 'const BUILD = "%s";' % _swstamp, _sw, count=1)
# the build id becomes visible ON THE PAGE (colophon) — "which build am I on" must never
# need DevTools again
_doc2 = (ROOT / "index.html").read_text()
if '<meta name="build"' not in _doc2:
    _doc2 = _doc2.replace("</head>", '<meta name="build" content="%s"></head>' % _swstamp, 1)
else:
    _doc2 = re.sub(r'<meta name="build" content="[^"]*">', '<meta name="build" content="%s">' % _swstamp, _doc2, count=1)
(ROOT / "index.html").write_text(_doc2)
(ROOT / "sw.js").write_text(_sw)
# CONFLICT-MARKER GUARD: sw.js shipped to production with unresolved merge markers for a
# day — a syntax error that silently broke every service-worker update while the deploy
# check read the first line of the broken file and said "live". Never again: any artifact
# containing conflict markers, or an unparseable sw.js, refuses to build.
for _name in ["index.html", "sw.js", "reuse.html", "onrecord-heat-mockup.html"]:
    _fp = ROOT / _name
    if _fp.exists():
        assert "<<<<<<<" not in _fp.read_text() and ">>>>>>>" not in _fp.read_text(), \
            _name + " contains merge conflict markers - REFUSING to ship"
        _vis = __import__("re").sub(r"<script[^>]*>.*?</script>", "", _fp.read_text(), flags=__import__("re").S)
        assert "\\n" not in __import__("re").sub(r"<[^>]*>", "", _vis) or _name != "index.html", \
            _name + " serves literal backslash-n as text"  # literal backslash-n guard
try:
    import subprocess as _sp
    _r = _sp.run(["node", "--check", str(ROOT / "sw.js")], capture_output=True)
    assert _r.returncode == 0, "sw.js does not parse: " + _r.stderr.decode()[:200]
except FileNotFoundError:
    pass  # no node on this runner; the marker check above still holds

print(f"[pipeline] built index.html ({len(doc):,} B) — sw BUILD {_swstamp} — done")

# ---------------- build reuse.html (teachers + press) ----------------
reuse_css = css   # one family, no embedded faces
_rn = buildlib.build_reuse_html(ROOT, reuse_css, buildlib.reuse_data(out, out["_meta"]["today"]))
print(f"[pipeline] built reuse.html ({_rn:,} B) — done")
