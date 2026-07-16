#!/usr/bin/env python3
"""Executability spike: fetch the verified live feeds and compute the core numbers
   (The Number, vital signs, per-city today-vs-record percentiles) end to end.
   Downloads are modest (~15-20 MB total). All sources CC-BY / public domain."""
import json, csv, io, math, statistics, time, urllib.request, datetime, pathlib

OUT = pathlib.Path(__file__).parent
CACHE = OUT / "cache"; CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "climate-spike/0.1 (research prototype; agoshbaranwal@gmail.com)"}

def fetch(url, cache_key=None, tries=4):
    if cache_key and (CACHE / cache_key).exists():
        print(f"  cached      {cache_key}")
        return (CACHE / cache_key).read_text()
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read().decode("utf-8", "replace")
                print(f"  {r.status} {len(data):>9,} B  {url[:95]}")
                if cache_key: (CACHE / cache_key).write_text(data)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < tries - 1:
                wait = 65 * (attempt + 1)
                print(f"  429 rate-limited; sleeping {wait}s")
                time.sleep(wait)
            else:
                raise

summary = {"fetched_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "sources": {}}

# ── 1. Copernicus Climate Pulse: status + daily global 2m temp + SST ──────────
print("[1] Climate Pulse (C3S/ECMWF, CC-BY)")
status = json.loads(fetch("https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json"))
summary["sources"]["climate_pulse_status"] = status

t2 = fetch("https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv")
rows = [r for r in csv.reader(io.StringIO(t2)) if r and not r[0].startswith("#")]
hdr = rows[0]; data = rows[1:]
# columns: date, value(abs C), climatology(1991-2020), anomaly vs 1991-2020, status flag (inspect header)
print("   2t columns:", hdr)
t2s = [(r[0], float(r[1]), float(r[3])) for r in data if r[1] and r[3]]
latest_date, latest_abs, latest_anom9120 = t2s[-1]
# C3S convention: 1991-2020 global climatology is ~0.88 C warmer than 1850-1900 pre-industrial
PREIND_OFFSET = 0.88  # ASSUMPTION to verify against C3S bulletins before any launch
last365 = [a for _, _, a in t2s[-365:]]
number = statistics.fmean(last365) + PREIND_OFFSET
days_ge_15 = sum(1 for a in last365 if a + PREIND_OFFSET >= 1.5)
summary["the_number"] = {
    "warming_12mo_vs_1850_1900_C": round(number, 3),
    "days_at_or_above_1.5C_last_365": days_ge_15,
    "latest_day": {"date": latest_date, "abs_C": latest_abs,
                   "anom_vs_1991_2020": latest_anom9120,
                   "anom_vs_1850_1900": round(latest_anom9120 + PREIND_OFFSET, 3)},
    "preindustrial_offset_assumed": PREIND_OFFSET,
    "series_start": t2s[0][0], "n_days": len(t2s),
}

sst = fetch("https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_sst_60S-60N_ocean.csv")
srows = [r for r in csv.reader(io.StringIO(sst)) if r and not r[0].startswith("#")][1:]
ss = [(r[0], float(r[1]), float(r[3])) for r in srows if r[1] and r[3]]
summary["sst_60S_60N"] = {"date": ss[-1][0], "abs_C": ss[-1][1], "anom_vs_1991_2020": ss[-1][2]}

# ── 2. NOAA GML daily global CO2 trend ────────────────────────────────────────
print("[2] NOAA GML CO2 (public domain)")
co2 = fetch("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_trend_gl.csv")
crows = [r for r in csv.reader(io.StringIO(co2)) if r and not r[0].startswith("#")]
crows = [r for r in crows if len(r) >= 4 and r[0].strip().isdigit()]
y, m, d, ppm = int(crows[-1][0]), int(crows[-1][1]), int(crows[-1][2]), float(crows[-1][3])
# same calendar day previous year for the delta
prev = [r for r in crows if int(r[0]) == y - 1 and int(r[1]) == m and int(r[2]) == d]
summary["co2"] = {"date": f"{y}-{m:02d}-{d:02d}", "ppm": ppm,
                  "ppm_1yr_ago": float(prev[0][3]) if prev else None,
                  "yoy_delta": round(ppm - float(prev[0][3]), 2) if prev else None}

# ── 3. NSIDC sea-ice extent, both poles (v4) ──────────────────────────────────
print("[3] NSIDC Sea Ice Index v4 (NOAA open data)")
for pole, url in [("arctic", "https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv"),
                  ("antarctic", "https://noaadata.apps.nsidc.org/NOAA/G02135/south/daily/data/S_seaice_extent_daily_v4.0.csv")]:
    txt = fetch(url)
    irows = [r for r in csv.reader(io.StringIO(txt))][2:]  # 2 header lines
    irows = [r for r in irows if len(r) >= 4 and r[3].strip()]
    last = irows[-1]
    summary.setdefault("sea_ice", {})[pole] = {
        "date": f"{last[0].strip()}-{last[1].strip():0>2}-{last[2].strip():0>2}",
        "extent_Mkm2": float(last[3])}

# ── 4. Per-city: full daily record 1940->present (Open-Meteo ERA5 archive) ────
print("[4] Open-Meteo ERA5 archive + forecast (CC-BY)")
CITIES = {
    "Delhi":   (28.61, 77.21),
    "Seville": (37.39, -5.99),
    "Phoenix": (33.45, -112.07),
    "Jakarta": (-6.21, 106.85),
}
summary["cities"] = {}
today = datetime.date.today()
for name, (lat, lon) in CITIES.items():
    arch = json.loads(fetch(
        f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
        f"&start_date=1940-01-01&end_date={today - datetime.timedelta(days=6)}"
        f"&daily=temperature_2m_max,temperature_2m_min&timezone=auto",
        cache_key=f"archive_{name}.json"))
    fc = json.loads(fetch(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min&forecast_days=1&timezone=auto"))
    dates = arch["daily"]["time"]; tmax = arch["daily"]["temperature_2m_max"]; tmin = arch["daily"]["temperature_2m_min"]
    recs = [(datetime.date.fromisoformat(dt), x, n) for dt, x, n in zip(dates, tmax, tmin) if x is not None]
    fx_tmax = fc["daily"]["temperature_2m_max"][0]; fx_tmin = fc["daily"]["temperature_2m_min"][0]

    # today's forecast vs the historical distribution for this calendar date +/- 7 days
    window = [x for (dt, x, _) in recs
              if abs((dt.replace(year=2000) - today.replace(year=2000)).days) <= 7]
    pct = 100.0 * sum(1 for x in window if x <= fx_tmax) / len(window)
    hotter_days = sorted(window, reverse=True)
    rank_note = sum(1 for x in window if x > fx_tmax)

    # fixed-baseline warming: mean annual tmax, 1951-1980 vs last 10 full years
    def annual_mean(y0, y1):
        vals = [x for (dt, x, _) in recs if y0 <= dt.year <= y1]
        return statistics.fmean(vals)
    warm = annual_mean(today.year - 10, today.year - 1) - annual_mean(1951, 1980)

    # threshold counts per year: days >= 35C and warm nights >= 25C, then vs now
    def per_year(pred, y0, y1):
        yrs = {}
        for (dt, x, n) in recs:
            if y0 <= dt.year <= y1:
                yrs.setdefault(dt.year, 0)
                if pred(x, n): yrs[dt.year] += 1
        return statistics.fmean(yrs.values())
    hot_then = per_year(lambda x, n: x >= 35, 1951, 1980)
    hot_now  = per_year(lambda x, n: x >= 35, today.year - 10, today.year - 1)
    wn_then  = per_year(lambda x, n: n is not None and n >= 25, 1951, 1980)
    wn_now   = per_year(lambda x, n: n is not None and n >= 25, today.year - 10, today.year - 1)

    summary["cities"][name] = {
        "forecast_today": {"date": str(today), "tmax_C": fx_tmax, "tmin_C": fx_tmin},
        "today_percentile_vs_1940_present_same_fortnight": round(pct, 1),
        "days_in_window_hotter_than_today": rank_note,
        "window_n": len(window),
        "warming_last10y_vs_1951_1980_C": round(warm, 2),
        "days_ge_35C_per_year": {"1951_1980": round(hot_then, 1), "last_10y": round(hot_now, 1)},
        "warm_nights_ge_25C_per_year": {"1951_1980": round(wn_then, 1), "last_10y": round(wn_now, 1)},
        "record_start": str(recs[0][0]), "n_days": len(recs),
    }

path = OUT / "spike-summary.json"
path.write_text(json.dumps(summary, indent=2))
print("\n=== SPIKE SUMMARY ===")
print(json.dumps(summary, indent=2)[:4000])
print(f"\nwritten: {path}")
