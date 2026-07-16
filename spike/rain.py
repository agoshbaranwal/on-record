#!/usr/bin/env python3
"""Rain chapter spike + forecast-vs-reanalysis bias measurement.
   Adds per-city: 3-day rain totals vs the 1940-2025 record, dry spells, heavy-rain
   days then-vs-now, and a measured Open-Meteo-forecast vs ERA5-archive tmax offset."""
import json, statistics, time, urllib.request, datetime, pathlib

OUT = pathlib.Path(__file__).parent
CACHE = OUT / "cache"; CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "climate-spike/0.1 (research prototype; agoshbaranwal@gmail.com)"}
today = datetime.date(2026, 7, 3)

def fetch(url, cache_key=None, tries=4):
    if cache_key and (CACHE / cache_key).exists():
        print(f"  cached      {cache_key}")
        return (CACHE / cache_key).read_text()
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read().decode("utf-8", "replace")
                print(f"  {r.status} {len(data):>9,} B  {url[:100]}")
                if cache_key: (CACHE / cache_key).write_text(data)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < tries - 1:
                wait = 65 * (attempt + 1); print(f"  429; sleeping {wait}s"); time.sleep(wait)
            else: raise

CITIES = {"Seville": (37.39, -5.99), "Delhi": (28.61, 77.21), "Jakarta": (-6.21, 106.85)}
res = {}

for name, (lat, lon) in CITIES.items():
    print(f"[{name}]")
    arch = json.loads(fetch(
        f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
        f"&start_date=1940-01-01&end_date={today - datetime.timedelta(days=6)}"
        f"&daily=precipitation_sum&timezone=auto", cache_key=f"archive_rain_{name}.json"))
    fc = json.loads(fetch(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=precipitation_sum,temperature_2m_max&past_days=92&forecast_days=1&timezone=auto",
        cache_key=f"fc92_{name}.json"))

    dates = [datetime.date.fromisoformat(d) for d in arch["daily"]["time"]]
    pr = arch["daily"]["precipitation_sum"]
    recs = [(d, p) for d, p in zip(dates, pr) if p is not None]

    # --- 3-day rolling totals ---
    tot3 = []  # (end_date, total)
    for i in range(2, len(recs)):
        if (recs[i][0] - recs[i-2][0]).days == 2:
            tot3.append((recs[i][0], recs[i][1] + recs[i-1][1] + recs[i-2][1]))
    # same-fortnight distribution (end date within +/-7 days of today's calendar date)
    def near(d): return abs((d.replace(year=2000) - today.replace(year=2000)).days) <= 7
    fortnight = [t for (d, t) in tot3 if near(d)]
    # current 3-day total from the forecast series (last 3 completed days incl. yesterday)
    fdates = [datetime.date.fromisoformat(d) for d in fc["daily"]["time"]]
    fpr = fc["daily"]["precipitation_sum"]
    fpast = [(d, p) for d, p in zip(fdates, fpr) if p is not None and d < today]
    cur3 = sum(p for _, p in fpast[-3:]); cur3_dates = f"{fpast[-3][0]} → {fpast[-1][0]}"
    pct = 100.0 * sum(1 for t in fortnight if t <= cur3) / len(fortnight)
    wet_all = max(tot3, key=lambda x: x[1]); wet_fn = max([(d,t) for d,t in tot3 if near(d)], key=lambda x: x[1])

    # --- dry spells: per-year longest run of days < 1 mm ---
    runs_by_year, run, ry = {}, 0, None
    for d, p in recs:
        if p < 1.0:
            run += 1; ry = d.year
            runs_by_year[ry] = max(runs_by_year.get(ry, 0), run)
        else:
            run = 0
    # current active run including forecast past days
    cur_run = 0
    for d, p in recs + fpast:
        cur_run = cur_run + 1 if p < 1.0 else 0
    dry_then = statistics.fmean([runs_by_year[y] for y in runs_by_year if 1951 <= y <= 1980])
    dry_now  = statistics.fmean([runs_by_year[y] for y in runs_by_year if today.year-10 <= y <= today.year-1])
    dry_rec  = max(runs_by_year.items(), key=lambda kv: kv[1])

    # --- heavy-rain days >= 20 mm per year, then vs now ---
    def heavy(y0, y1):
        yrs = {}
        for d, p in recs:
            if y0 <= d.year <= y1:
                yrs.setdefault(d.year, 0)
                if p >= 20: yrs[d.year] += 1
        return statistics.fmean(yrs.values())
    hv_then, hv_now = heavy(1951, 1980), heavy(today.year-10, today.year-1)

    # --- forecast-vs-archive tmax bias over the ~86-day overlap ---
    ftx = {d: t for d, t in zip(fdates, fc["daily"]["temperature_2m_max"]) if t is not None}
    arch_tx = json.loads((CACHE / f"archive_{name}.json").read_text())["daily"]
    atx = {datetime.date.fromisoformat(d): t for d, t in zip(arch_tx["time"], arch_tx["temperature_2m_max"]) if t is not None}
    diffs = [ftx[d] - atx[d] for d in ftx if d in atx]
    bias = {"n_days": len(diffs), "mean_C": round(statistics.fmean(diffs), 2),
            "median_C": round(statistics.median(diffs), 2),
            "p90_abs_C": round(sorted(abs(x) for x in diffs)[int(len(diffs)*0.9)], 2)}

    res[name] = {
        "rain_3day": {"current_mm": round(cur3, 1), "dates": cur3_dates,
                      "percentile_vs_same_fortnight_since_1940": round(pct, 1),
                      "fortnight_n": len(fortnight),
                      "fortnight_share_zero": round(100*sum(1 for t in fortnight if t < 0.5)/len(fortnight)),
                      "wettest_3day_ever_mm": round(wet_all[1], 1), "wettest_3day_ever_end": str(wet_all[0]),
                      "wettest_3day_this_season_mm": round(wet_fn[1], 1), "wettest_3day_this_season_end": str(wet_fn[0])},
        "dry_spell": {"current_run_days": cur_run,
                      "longest_per_year_1951_1980": round(dry_then, 1),
                      "longest_per_year_last10": round(dry_now, 1),
                      "record_days": dry_rec[1], "record_year": dry_rec[0]},
        "heavy_days_ge20mm_per_year": {"1951_1980": round(hv_then, 1), "last_10y": round(hv_now, 1)},
        "forecast_vs_era5_tmax_bias": bias,
    }

pathlib.Path(OUT / "rain-summary.json").write_text(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
