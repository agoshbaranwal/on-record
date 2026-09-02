#!/usr/bin/env python3
# Offline mirror of pipeline.py's build step. Lives IN THE REPO now: it sat in the session
# scratchpad and the OS temp reaper deleted it three times mid-session, twice silently
# invalidating a verification run. A tool the build depends on is not a temp file.
import json, re, pathlib, sys, hashlib, datetime, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import buildlib

UA = {"User-Agent": "on-record/1.0 (agoshbaranwal@gmail.com)"}
def fetch(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == tries - 1: raise

tpl = (ROOT / "instrument.html").read_text()
# the inline script must PARSE before anything is built — a broken template must never
# reach index.html (it did once: an edit was committed with a syntax error because this
# builder happily assembled it)
import subprocess as _sp, tempfile as _tf, re as _re
_js = _re.findall(r'<script(?![^>]*\bsrc=)(?![^>]*type="application/json")[^>]*>(.*?)</script>', tpl, _re.S)[0]
with _tf.NamedTemporaryFile("w", suffix=".js", delete=False) as _f:
    _f.write(_js); _jp = _f.name
_r = _sp.run(["node", "--check", _jp], capture_output=True, text=True)
import os as _os; _os.unlink(_jp)
assert _r.returncode == 0, "instrument.html inline script does not parse:\n" + _r.stderr[:500]
# One typeface for the whole site, and it is Helvetica — already on every machine, so there is
# no webfont to embed. This used to inline 68 KB of base64 Space Grotesk into every build.
css = ""
_d = json.loads((ROOT / "data" / "site-data.json").read_text())
# The instant table is maintained outside both builds (tools/ring_bake.py, the v2 ingest).
# site-data.json only carries a COPY of it — re-attach the file so an offline build never
# ships a stale one. (It shipped the pre-ring copy exactly once; hence this line.)
_inst = ROOT / "data" / "instant-places.json"
if _inst.exists():
    _d["instant"] = json.loads(_inst.read_text())
_today = datetime.date.fromisoformat(_d["_meta"]["today"])
_arch = datetime.date.fromisoformat(_d["_meta"]["archive_end"])
try:
    _d["impact"] = buildlib.impact_dict(fetch, _today, _arch, ROOT, _d["_meta"]["built_utc"])
    (ROOT / "data" / "impact.json").write_text(json.dumps(_d["impact"], separators=(",", ":")))
except Exception as e:
    print("impact: SKIPPED", e)

# the file on disk is what the site publishes as its data; keep it identical to what the
# page was built from, or the two drift and only one of them is checkable.
(ROOT / "data" / "site-data.json").write_text(json.dumps(_d, separators=(",", ":")))
data = json.dumps(_d, separators=(",", ":"))
old = (ROOT / "index.html").read_text()
ns = re.search(r'This page draws its instrument.*?Andre et al\. 2024\)\.', old, re.S).group(0)
body = tpl.replace("/*__FONTS__*/", css).replace("/*__DATA__*/ null", data).replace("/*__NOSCRIPT__*/", ns)
assert "__DATA__" not in body and "__FONTS__" not in body and "__NOSCRIPT__" not in body, "placeholder left"
(ROOT / "onrecord-heat-mockup.html").write_text(body)
_gen = _d["seville_generational"]["days_ge35_per_year"]
_strp = _d["seville_stripes"]
LAST_FULL = _strp["year0"] + len(_strp["anom"]) - 1
def _meanov(y0, y1):
    v = [r["n"] for r in _gen if y0 <= r["year"] <= y1]
    return sum(v) / len(v) if v else 0
_was = round(_meanov(1951, 1980)); _now = round(_meanov(LAST_FULL - 9, LAST_FULL))
OG = "https://agoshbaranwal.github.io/on-record/"
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
    '<link rel="manifest" href="manifest.webmanifest">'
    '<meta name="theme-color" content="#05171A">'
    '<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2032%2032%22%3E%3Cpath%20d%3D%22M6.5%2010.0%20L6.92%2010.33%20L7.35%2010.64%20L7.78%2010.92%20L8.2%2011.17%20L8.62%2011.37%20L9.05%2011.51%20L9.47%2011.59%20L9.9%2011.6%20L10.32%2011.54%20L10.75%2011.42%20L11.18%2011.24%20L11.6%2011.0%20L12.03%2010.73%20L12.45%2010.42%20L12.88%2010.1%20L13.3%209.77%20L13.72%209.45%20L14.15%209.16%20L14.57%208.9%20L15.0%208.68%20L15.43%208.53%20L15.85%208.43%20L16.27%208.4%20L16.7%208.44%20L17.12%208.54%20L17.55%208.71%20L17.98%208.92%20L18.4%209.19%20L18.82%209.49%20L19.25%209.81%20L19.68%2010.14%20L20.1%2010.46%20L20.52%2010.76%20L20.95%2011.03%20L21.38%2011.26%20L21.8%2011.43%20L22.23%2011.55%20L22.65%2011.6%20L23.07%2011.58%20L23.5%2011.5%22%20fill%3D%22none%22%20stroke%3D%22%23F2E7CC%22%20stroke-width%3D%222.4%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20opacity%3D%22.42%22%2F%3E%3Cpath%20d%3D%22M6.5%2024.25%20L6.86%2024.41%20L7.22%2024.52%20L7.59%2024.58%20L7.95%2024.6%20L8.31%2024.57%20L8.68%2024.49%20L9.04%2024.36%20L9.4%2024.19%20L9.76%2023.99%20L10.12%2023.75%20L10.49%2023.49%20L10.85%2023.22%20L11.21%2022.94%20L11.57%2022.66%20L11.94%2022.4%20L12.3%2022.15%20L12.66%2021.92%20L13.03%2021.73%20L13.39%2021.58%20L13.75%2021.48%20L14.11%2021.41%20L14.48%2021.4%20L14.84%2021.44%20L15.2%2021.52%20L15.56%2021.65%20L15.93%2021.82%20L16.29%2022.03%20L16.65%2022.26%20L17.01%2022.52%20L17.38%2022.8%20L17.74%2023.08%20L18.1%2023.35%20L18.46%2023.62%20L18.82%2023.87%20L19.19%2024.09%20L19.55%2024.28%20L19.91%2024.43%20L20.27%2024.53%20L20.64%2024.59%20L21.0%2024.6%22%20fill%3D%22none%22%20stroke%3D%22%23F2E7CC%22%20stroke-width%3D%222.4%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20opacity%3D%22.42%22%2F%3E%3Cpath%20d%3D%22M6.5%2017.15%20L6.97%2017.61%20L7.45%2018.01%20L7.92%2018.34%20L8.4%2018.56%20L8.88%2018.68%20L9.35%2018.69%20L9.82%2018.58%20L10.3%2018.36%20L10.78%2018.04%20L11.25%2017.64%20L11.73%2017.18%20L12.2%2016.69%20L12.68%2016.19%20L13.15%2015.7%20L13.62%2015.25%20L14.1%2014.87%20L14.57%2014.58%20L15.05%2014.39%20L15.53%2014.3%20L16.0%2014.34%20L16.48%2014.48%20L16.95%2014.73%20L17.42%2015.08%20L17.9%2015.5%20L18.38%2015.97%20L18.85%2016.47%20L19.33%2016.97%20L19.8%2017.45%20L20.27%2017.87%20L20.75%2018.23%20L21.23%2018.49%20L21.7%2018.65%20L22.17%2018.7%20L22.65%2018.63%20L23.12%2018.45%20L23.6%2018.17%20L24.07%2017.8%20L24.55%2017.36%20L25.02%2016.87%20L25.5%2016.37%22%20fill%3D%22none%22%20stroke%3D%22%23FF6B52%22%20stroke-width%3D%224%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E"><link rel="apple-touch-icon" href="og/icon-192.png">'
)
doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width, initial-scale=1">'
       + head_meta + '</head><body>' + body + "</body></html>")
# ── BAKE THE HEADLINE NUMBERS INTO THE STATIC DOCUMENT ────────────────────────────
# The built page shipped "about – billion tonnes" and "– then, – now": every headline figure was
# injected at runtime, so a JS-slow visitor, a search engine, or a reader on a bad connection met
# a page of dashes. The JS writes the SAME values a moment later, so this cannot disagree with
# itself — it only means the number is there before the script runs.
def _bake(doc):
    import re as _re
    _est = sorted(_d["budget"]["estimates"], key=lambda e: e["remaining_now_gt"])
    _lead = round(_est[0]["remaining_now_gt"])
    _gt = [r["n"] for r in _gen]
    _yrs = [r["year"] for r in _gen]
    def _mean(a, b):
        v = [n for y, n in zip(_yrs, _gt) if a <= y <= b]
        return round(sum(v) / len(v)) if v else 0
    _nights = _d["seville_generational"]["warm_nights_ge25_per_year"]
    _ny = [r["year"] for r in _nights]; _nv = [r["n"] for r in _nights]
    def _nmean(a, b):
        v = [x for y, x in zip(_ny, _nv) if a <= y <= b]
        return round(sum(v) / len(v)) if v else 0
    _hi = _est[-1]; _rate = _d["budget"]["rate_now_gt"]; _nowdec = _d["budget"]["now_dec"]
    def _src(e): return "IGCC 2025" if "IGCC" in (e.get("label") or "") else "GCB 2025"
    _ylo = _est[0]["remaining_now_gt"] / _rate; _yhi = _hi["remaining_now_gt"] / _rate
    _yspan = f"{_ylo:.1f}" if f"{_ylo:.1f}" == f"{_yhi:.1f}" else f"{_ylo:.1f}\u2013{_yhi:.1f}"
    _spend = round(_nowdec + _ylo)
    _P = _d["perception_gap"]
    subs = {"lead-gt": "%d\u2013%d" % (round(_est[0]["remaining_now_gt"]), round(_est[-1]["remaining_now_gt"])),
            "g-then": str(_mean(1951, 1980)),
            "g-now":  str(_mean(LAST_FULL - 9, LAST_FULL)),
            # the summary chapter's whole job is four numbers; it must not ship dashes
            "rc-1-n": f"{_mean(1951,1980)} \u2192 {_mean(LAST_FULL-9,LAST_FULL)} days a year",
            "n-big": "+%d " % round(_d["delhi_honesty"]["receipts"]["warm_nights_now"] - _d["delhi_honesty"]["receipts"]["warm_nights_then"]),
            "rc-2-n": "%d \u2192 %d nights a year" % (round(_d["delhi_honesty"]["receipts"]["warm_nights_then"]), round(_d["delhi_honesty"]["receipts"]["warm_nights_now"])),
            "rc-3-n": f"{round(_P['global_want_action_pct'])}% want action",
            "rc-4-n": f"{_yspan} years of budget left",
            # the flagship number's named sources, VISIBLE — not only in noscript and the drawer
            "spent": (f"{round(_est[0]['remaining_now_gt'])}\u2013{round(_hi['remaining_now_gt'])} Gt remain "
                      f"\u00b7 {_src(_est[0])} and {_src(_hi)} agree \u00b7 spent around {_spend}")}
    n_done = 0
    for eid, val in subs.items():
        pat = _re.compile(r'(id="%s"[^>]*>)[^<]*(<)' % _re.escape(eid))
        doc, k = pat.subn(lambda m: m.group(1) + val + m.group(2), doc, count=1)
        n_done += k
    print("  baked %d headline numbers into the static document" % n_done)
    return doc
doc = _bake(doc)
(ROOT / "index.html").write_text(doc)   # written AFTER the bake, not before

# "burned" retired with the live "burned while you've been here" counter: its scope was
# never checkable and P1 cut it. _KEEP catches ACCIDENTS, so a deliberate cut edits it.
_KEEP = ["years", "spent", "copysky", "share-btn", "t-budget", "takeaway", "g-verdict", "impact-know", "ledger-sr", "homepick", "gq-bar", "gq-ex", "homechip", "n-example", "pk-ask", "rc-1-n", "cmp-grid", "recap-list"]
_missing = [k for k in _KEEP if ('id="%s"' % k) not in doc]
assert not _missing, "PROTECTED elements dropped: %s" % _missing
assert doc.count("Padma Kumari et al. 2007, GRL)") == 1   # the citation, not one phrasing of the sentence around it
assert doc.count("navigator.geolocation.getCurrentPosition") == 1
assert 'setItem("onrecord_skyloc"' not in doc
_codes = {r.get("code") for r in (_d["perception_gap"].get("all") or _d["perception_gap"]["countries"])}
_bar = re.findall(r'\{s:"([a-z-]+)",n:"[^"]*",f:"[^"]*",la:[-\d.]+,lo:[-\d.]+,tz:"[^"]*",c:"([A-Z]{3})"', doc)
assert len(_bar) == 24, "expected 24 fallback cities, found %d" % len(_bar)
assert not sorted({c for s, c in _bar if c not in _codes})
assert not ({"seville","delhi"} & {s for s,c in _bar})
_swstamp = re.sub(r"[^0-9]", "", _d["_meta"]["built_utc"])[:14] + "-" + hashlib.sha1(doc.encode()).hexdigest()[:8]
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

reuse_css = css   # one family, no embedded faces
_rn = buildlib.build_reuse_html(ROOT, reuse_css, buildlib.reuse_data(_d, _d["_meta"]["today"]))
print("offline build: index.html", len(doc), "B | sw BUILD:", _swstamp)
