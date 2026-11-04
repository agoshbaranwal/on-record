#!/usr/bin/env python3
"""Bake HOT, HUMID DAYS into the instant table.

A hot day can be dry or humid, and for much of South Asia the dry kind has not risen while the humid
kind has (haze and irrigated fields hold the afternoons back and put water in the air: MoES 2020;
Mishra et al. 2020, Nature Geoscience). So the page counts both. A hot, humid day here is a day whose
highest WET-BULB temperature (heat and humidity in one number; ERA5 via Open-Meteo, computed by them)
is at or above that city's own 95th percentile of 1951-1980 — a percentile, never a fixed 31 or 35 C,
because a reanalysis grid cannot see the absolute peaks a station would.

Same method as the page's live engine (instrument.html compute()): threshold = sorted[floor(.95*(n-1))]
rounded to 0.1 C; a day counts when it is AT OR ABOVE it.

Only the two windows the page compares are fetched: 1951-1980 (sets the threshold, holds the 1970s)
and the last ten full years — one variable, ~104 API-call units per city, paced off X-RateLimit headers.
Writes tw (threshold), ka (counts 1951-1980), kb (counts, last ten full years) per city, and the two
examples (seville, delhi) under _hh. Saves after every city, so a rate limit loses nothing.

  python3 tools/hh_bake.py              # fetch whatever is missing or out of date, then write
  python3 tools/hh_bake.py --if-needed  # the nightly job: exit at once when nothing is missing
  python3 tools/hh_bake.py --cached-only
"""
import datetime, json, math, pathlib, sys, time, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "spike" / "cache" / "hh"; CACHE.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "on-record/1.0 (open climate site; agoshbaranwal@gmail.com)"}
P = ROOT / "data" / "instant-places.json"
T = json.loads(P.read_text())
CACHED_ONLY = "--cached-only" in sys.argv
# the nightly job must never be held up: stop cleanly after a budget (minutes), keeping what is done.
# On a shared GitHub runner the archive answers "too many requests" every minute or two (measured
# 4 Nov 2026: ~70 s a city); the waits are fine, the budget is what bounds them.
BUDGET_S = 60 * float(next((a.split("=")[1] for a in sys.argv if a.startswith("--budget-min=")), "10"))
T0 = time.time(); WAITS = [0]
# the last ten FULL years: ERA5 publishes with a ~6-day lag, so a year is full from mid-January
_t = datetime.date.today()
LAST_FULL = _t.year - 1 if _t >= datetime.date(_t.year, 1, 12) else _t.year - 2
B0 = LAST_FULL - 9
CITIES = [(s, float(c["la"]), float(c["lo"])) for s, c in T.items() if not s.startswith("_")]
EXTRA = [("seville", 37.39, -5.99), ("delhi", 28.61, 77.21)]
HH = T.setdefault("_hh", {"a0": 1951})

def rec(slug):
    return T[slug] if slug in T and not slug.startswith("_") else HH.get(slug)
def fresh(r):
    return bool(r and r.get("tw") is not None and len(r.get("ka") or []) == 30 and r.get("b0") == B0
                and len(r.get("kb") or []) == 10)
todo = [c for c in CITIES + EXTRA if not fresh(rec(c[0]))]
if "--if-needed" in sys.argv and not todo:
    print("hh_bake: every city is current (last ten years %d-%d)" % (B0, LAST_FULL)); sys.exit(0)

class Limited(Exception): pass
def fetch(slug, la, lo, tag, y0, y1):
    f = CACHE / ("wb_%s_%s_%d.json" % (slug, tag, y0))
    if f.exists(): return json.loads(f.read_text())
    if CACHED_ONLY: return None
    url = ("https://archive-api.open-meteo.com/v1/archive?latitude=%s&longitude=%s&start_date=%d-01-01"
           "&end_date=%d-12-31&daily=wet_bulb_temperature_2m_max&timezone=auto" % (la, lo, y0, y1))
    for _ in range(4):
        if time.time() - T0 > BUDGET_S: raise Limited("time budget spent")
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                rem = r.headers.get("X-RateLimit-Remaining"); j = json.loads(r.read().decode())
            f.write_text(json.dumps(j))
            try:
                if rem is not None and float(rem) < 120: time.sleep(62)
            except ValueError: pass
            return j
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:160]
            print("   %s %s: %s" % (slug, e.code, msg), flush=True)
            if "Daily" in msg or "Hourly" in msg: raise Limited(msg)
            WAITS[0] += 1; time.sleep(61)
        except Exception as e:
            print("   %s: %s" % (slug, str(e)[:120]), flush=True)
            time.sleep(15)
    raise Limited("gave up on " + slug)

def bake(slug, la, lo):
    A = fetch(slug, la, lo, "a", 1951, 1980); B = fetch(slug, la, lo, "b", B0, LAST_FULL)
    if not A or not B: return None
    def vals(j): return [(int(t[:4]), v) for t, v in zip(j["daily"]["time"], j["daily"]["wet_bulb_temperature_2m_max"]) if v is not None]
    va, vb = vals(A), vals(B)
    s = sorted(v for _, v in va)
    assert len(s) > 7300, (slug, len(s))
    tw = round(s[int(math.floor(0.95 * (len(s) - 1)))] * 10) / 10
    ka = [sum(1 for y2, v in va if y2 == y and v >= tw) for y in range(1951, 1981)]
    kb = [sum(1 for y2, v in vb if y2 == y and v >= tw) for y in range(B0, LAST_FULL + 1)]
    print("%-14s wet-bulb p95 %.1f C   1970s %5.1f  ->  %d-%d %5.1f"
          % (slug, tw, sum(ka[19:29]) / 10, B0, LAST_FULL, sum(kb) / 10), flush=True)
    return {"tw": tw, "ka": ka, "kb": kb, "b0": B0}

def save():
    HH.update({"a0": 1951, "src": "ERA5 via Open-Meteo, daily max wet-bulb temperature; threshold = the "
               "city's own 1951-1980 95th percentile; ka = counts 1951-1980, kb = counts from b0, ten years"})
    P.write_text(json.dumps(T, separators=(",", ":")))

done = 0
try:
    for slug, la, lo in todo:
        r = bake(slug, la, lo)
        if not r: continue
        if slug in T: T[slug].update(r)
        else: HH[slug] = r
        done += 1; save()
except Limited as e:
    print("hh_bake: stopped by the archive's limit (%s) — %d baked this run, the rest next run" % (e, done))
left = [c[0] for c in CITIES + EXTRA if not fresh(rec(c[0]))]
print("hh_bake: %d baked, %d still missing%s" % (done, len(left), (": " + ", ".join(left)) if left else ""))
