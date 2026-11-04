#!/usr/bin/env python3
"""Bake data/futures.json — what the page needs to say what a child born today will face, per country.

1. Grant et al. 2025, "Global emergence of unprecedented lifetime exposure to climate extremes",
   Nature 641:374-379, open access CC BY 4.0. Supplementary Tables 1-18 give, per country and birth
   cohort, the share of people who will live an UNPRECEDENTED lifetime of an extreme (exposure with
   less than a 1-in-10,000 chance in a world without human-caused warming), for six extremes at
   1.5, 2.5 and 3.5 C of warming by 2100. We keep the 1960 and 2020 cohorts.
2. The tz database's zone.tab (public domain): each time zone -> its country and coordinates, so a
   first visit can show the reader's COUNTRY without asking and without sending anything anywhere.
   Plus its alias links (Asia/Calcutta -> Asia/Kolkata), because browsers still report old names.
3. ISO 3166 two-letter -> three-letter codes, so a searched or located city finds its country row.

Needs pypdf + pycountry (a scratch venv is fine); the PDF is the supplement from Europe PMC
(PMC12058528). Nothing here runs nightly: the study does not change.

  python tools/futures_bake.py <supplement.pdf>
"""
import json, re, sys, pathlib
import pypdf, pycountry

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = sys.argv[1]
pages = [re.sub(r"[ \t]+", " ", (p.extract_text() or "")) for p in pypdf.PdfReader(PDF).pages]

START = {1: 8, 2: 14, 3: 20, 4: 26, 5: 31, 6: 36, 7: 41, 8: 47, 9: 53, 10: 58, 11: 63, 12: 68,
         13: 73, 14: 79, 15: 84, 16: 89, 17: 92, 18: 96, 19: 99}
HZ = ["hw", "rf", "dr", "cf", "wf", "tc"]   # heatwaves, river floods, droughts, crop failures, wildfires, tropical cyclones
PW = ["15", "25", "35"]
def which(k): return HZ[(k - 1) // 3], PW[(k - 1) % 3]
# the captions say which table is which; refuse to run if the PDF ever disagrees with this map
CAP = {"hw": "heatwaves", "rf": "floods", "dr": "droughts", "cf": "crop failures", "wf": "wildfires", "tc": "tropical cyclones"}
for k in range(1, 19):
    hz, pw = which(k)
    cap = re.sub(r"\s+", " ", pages[START[k] - 1])
    m = re.search(r"Table %d: (.{0,260})" % k, cap)
    assert m and CAP[hz] in m.group(1).replace("-", "") and ("%s.%s" % (pw[0], pw[1])) in m.group(1), (k, m and m.group(1))

PAIR = r"(\d+)\s*\((\d+)\)"
ROW = re.compile(r"([A-Za-z][A-Za-z'’\.\-,\s]*?)\s*" + r"\s+".join([PAIR] * 7))
OVR = {"Cote dIvoire": "CIV", "Democratic Republic of the Congo": "COD", "Republic of Congo": "COG",
       "Cape Verde": "CPV", "Hong Kong": "HKG", "Macedonia": "MKD", "The Gambia": "GMB", "Czech Republic": "CZE",
       "Swaziland": "SWZ", "Russia": "RUS", "Iran": "IRN", "Syria": "SYR", "Laos": "LAO", "Lao PDR": "LAO",
       "Vietnam": "VNM", "Bolivia": "BOL", "Venezuela": "VEN", "Tanzania": "TZA", "Moldova": "MDA",
       "South Korea": "KOR", "Republic of Korea": "KOR", "Dem. Rep. Korea": "PRK", "Russian Federation": "RUS", "Palestine": "PSE", "Taiwan": "TWN",
       "Micronesia": "FSM", "Brunei": "BRN", "Turkey": "TUR", "Kosovo": "XKX", "Bahamas": "BHS",
       "United States Virgin Islands": "VIR", "Libya": "LBY", "Western Sahara": "ESH"}
def iso3(n):
    n = re.sub(r"\s+", " ", n).strip().strip(",")
    if n in OVR: return OVR[n]
    try: return pycountry.countries.lookup(n).alpha_3
    except LookupError: pass
    try:
        hit = pycountry.countries.search_fuzzy(n)[0]
        FUZZY[n] = hit.alpha_3 + " " + hit.name     # every fuzzy match is printed for a human to check
        return hit.alpha_3
    except LookupError: return None
FUZZY = {}

C, NAMES, SEEN, miss = {}, {}, {}, set()
for k in range(1, 19):
    hz, pw = which(k)
    t = "\n".join(pages[START[k] - 1:START[k + 1] - 1])
    t = t[re.search(r"Country\s+1960\s+1970\s+1980\s+1990\s+2000\s+2010\s+2020", t).end():]
    nx = re.search(r"Table\s+%d:" % (k + 1), t)
    if nx: t = t[:nx.start()]
    for row in ROW.findall(t):
        nm = re.sub(r"\s+", " ", row[0]).strip()
        code = iso3(nm)
        if not code: miss.add(nm); continue
        v = list(map(int, row[1:])); N, CF = v[0::2], v[1::2]
        # "0 (0)" AFTER a non-zero earlier cohort is a hole in the cohort data (Comoros 2010-2020),
        # not a real zero: null, so the page falls back to the world rather than printing "0%"
        cf = [None if (N[i] == 0 and CF[i] == 0 and i > 0 and any(x > 0 for x in N[:i])) else CF[i] for i in range(7)]
        C.setdefault(code, {}).setdefault(hz, {})[pw] = [cf[0], cf[6]]   # born 1960, born 2020
        NAMES[code] = nm
        SEEN.setdefault(code, set()).add(nm)
assert not miss, "unmatched country names: %s" % sorted(miss)
print("fuzzy matches (check):", FUZZY)
dup = {c: v for c, v in SEEN.items() if len(v) > 1}
assert not dup, "two table rows mapped to one country: %s" % dup
assert C["IND"]["hw"]["15"] == [14, 46], C["IND"]["hw"]   # spot check against the printed table (p.10)

# display names: the table's spellings, made into what a reader would write
DISPLAY = {"CIV": "Côte d’Ivoire", "PRK": "North Korea", "KOR": "South Korea", "LAO": "Laos", "COG": "Congo",
           "COD": "DR Congo", "MKD": "North Macedonia", "SWZ": "Eswatini", "CZE": "Czechia", "TUR": "Türkiye",
           "RUS": "Russia", "VIR": "the US Virgin Islands", "GMB": "The Gambia", "FSM": "Micronesia",
           "USA": "the United States", "GBR": "the United Kingdom", "ARE": "the United Arab Emirates",
           "NLD": "the Netherlands", "PHL": "the Philippines", "CAF": "the Central African Republic",
           "DOM": "the Dominican Republic", "BHS": "the Bahamas", "COM": "the Comoros", "MDV": "the Maldives",
           "SLB": "the Solomon Islands", "CPV": "Cabo Verde", "HKG": "Hong Kong"}
for k, v in DISPLAY.items():
    if k in NAMES: NAMES[k] = v
# ── time zones → country (+ the zone's own coordinates), and the alias links ──
ZT = pathlib.Path("/usr/share/zoneinfo/zone.tab").read_text()
A2 = {c.alpha_2: c.alpha_3 for c in pycountry.countries}
A2["XK"] = "XKX"
def dms(s):
    sg = -1 if s[0] == "-" else 1; s = s[1:]
    d, m, sec = (int(s[:2]), int(s[2:4]), int(s[4:6] or 0)) if len(s) in (4, 6) else (int(s[:3]), int(s[3:5]), int(s[5:7] or 0))
    return sg * (d + m / 60 + sec / 3600)
TZ = []
for line in ZT.splitlines():
    if not line or line.startswith("#"): continue
    cc, coord, tz = line.split("\t")[:3]
    m = re.match(r"([+-]\d{4,6})([+-]\d{5,7})", coord)
    la, lo = dms(m.group(1)), dms(m.group(2))
    TZ.append("%s|%s|%.2f|%.2f" % (tz, A2.get(cc, ""), la, lo))
ZI = pathlib.Path("/usr/share/zoneinfo/tzdata.zi").read_text()
known = {t.split("|")[0] for t in TZ}
ALIAS = []
for line in ZI.splitlines():
    if line.startswith("L "):
        _, target, alias = line.split()[:3]
        if target in known: ALIAS.append("%s>%s" % (alias, target))

out = {"_src": {"c": "Grant et al. 2025, Nature 641:374-379, Supplementary Tables 1-18 (CC BY 4.0), doi:10.1038/s41586-025-08907-1",
                "tz": "tz database zone.tab + tzdata.zi links (public domain)", "a2": "ISO 3166-1"},
       "_cols": "c[ISO3][hazard][pathway] = [% of the 1960 cohort, % of the 2020 cohort] facing unprecedented lifetime exposure; "
                "hazards hw heatwaves, rf river floods, dr droughts, cf crop failures, wf wildfires, tc tropical cyclones; "
                "pathways 15/25/35 = 1.5/2.5/3.5 C of warming by 2100",
       "c": C, "n": NAMES, "tz": ";".join(TZ), "tzl": ";".join(ALIAS),
       "a2": ";".join("%s:%s" % kv for kv in sorted(A2.items()))}
p = ROOT / "data" / "futures.json"
p.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
print("futures.json: %d countries, %d zones, %d aliases, %d B" % (len(C), len(TZ), len(ALIAS), p.stat().st_size))
