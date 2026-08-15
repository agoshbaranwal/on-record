#!/usr/bin/env python3
"""Bake the SEASON RING into the instant table.

The ring needs something no other part of the baked record needs: WHICH CALENDAR DAYS were hot,
not how many. So this walks each city's 86-year daily archive once and writes, per city, two
365-slot counts — hot-day frequency per day-of-year in 1951-80 and in the last 30 full years — using
that city's OWN already-published threshold (`th` in instant-places.json). No new thresholds are
minted here; if the threshold moves, this file's numbers move with it.

Feb 29 folds into Feb 28 so every year maps to exactly 365 slots.
Counts are 0..30, stored one character each from a 31-char alphabet — 730 chars a city.

  python3 tools/ring_bake.py            # cached fetches, rewrites data/instant-places.json
"""
import json, pathlib, sys, time, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "spike" / "cache" / "ring"
CACHE.mkdir(parents=True, exist_ok=True)
ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTU"   # 31 symbols: a 30-year era can hit 30
ML = [31,28,31,30,31,30,31,31,30,31,30,31]

DOY = {}
s = 0
for m in range(12):
    for d in range(1, ML[m] + 1):
        DOY["%02d-%02d" % (m + 1, d)] = s; s += 1
DOY["02-29"] = DOY["02-28"]
assert s == 365

def archive(slug, la, lo, end):
    f = CACHE / (slug + ".json")
    if f.exists():
        return json.loads(f.read_text())
    url = ("https://archive-api.open-meteo.com/v1/archive?latitude=%s&longitude=%s"
           "&start_date=1940-01-01&end_date=%s&daily=temperature_2m_max&timezone=auto" % (la, lo, end))
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                j = json.loads(r.read().decode())
            f.write_text(json.dumps(j)); return j
        except Exception as e:
            if attempt == 5: raise
            print('   retry %s (%s)' % (slug, str(e)[:40]), flush=True)
            time.sleep(45 * (attempt + 1))

def main():
    P = ROOT / "data" / "instant-places.json"
    T = json.loads(P.read_text())
    end = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 6 * 86400))
    lastFull = time.gmtime().tm_year - 1
    eraB0 = lastFull - 29
    done = []
    for slug, c in list(T.items()):
        if slug.startswith("_"): continue
        j = archive(slug, c["la"], c["lo"], end)
        dates = j["daily"]["time"]; tx = j["daily"]["temperature_2m_max"]
        A = [0] * 365; B = [0] * 365
        for i, dt in enumerate(dates):
            t = tx[i]
            if t is None or t < c["th"]: continue
            y = int(dt[:4]); sl = DOY.get(dt[5:])
            if sl is None: continue
            if 1951 <= y <= 1980: A[sl] += 1
            elif eraB0 <= y <= lastFull: B[sl] += 1
        assert max(A) <= 30 and max(B) <= 30, slug
        c["ra"] = "".join(ALPHA[v] for v in A)
        c["rb"] = "".join(ALPHA[v] for v in B)
        done.append("%-14s then %3d  now %3d" % (c["n"], sum(1 for v in A if v >= 15), sum(1 for v in B if v >= 15)))
        print(done[-1], flush=True)
    T["_ring"] = {"eraA": "1951–80", "eraB": "%d–%d" % (eraB0, lastFull), "years": 30, "alpha": ALPHA}
    P.write_text(json.dumps(T, separators=(",", ":")))
    print("\nwrote %s  %.1f KB" % (P.name, P.stat().st_size / 1024))

main()
