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
fonts = json.loads((ROOT / "fonts" / "fonts-b64.json").read_text())
css = "".join(
    "@font-face{font-family:'SpaceGroteskX';font-style:normal;font-weight:%d;font-display:swap;"
    "src:url(data:font/woff2;base64,%s) format('woff2')}\n" % (w, fonts[k])
    for k, w in [("SpaceGrotesk-normal-400", 400), ("SpaceGrotesk-normal-500", 500)])
_d = json.loads((ROOT / "data" / "site-data.json").read_text())
_today = datetime.date.fromisoformat(_d["_meta"]["today"])
_arch = datetime.date.fromisoformat(_d["_meta"]["archive_end"])
try:
    _d["impact"] = buildlib.impact_dict(fetch, _today, _arch, ROOT, _d["_meta"]["built_utc"])
    (ROOT / "data" / "impact.json").write_text(json.dumps(_d["impact"], separators=(",", ":")))
except Exception as e:
    print("impact: SKIPPED", e)

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
DESC = ("An honest climate instrument: the world&#39;s carbon budget as a living sky, and one city&#39;s heat record "
        "measured against its own past. Every number measured, every source shown.")
CARD = (f"In Seville, days at or above 35&#176;C rose from {_was} a year (1951–80 average) to {_now} "
        f"({LAST_FULL-9}–{LAST_FULL}). Every number sourced — ERA5 via Open-Meteo.")
ALT = f"On Record card: in Seville, days at or above 35C rose from {_was} a year to {_now}."
head_meta = (
    "<title>On Record — the carbon budget, drawn as a living sky</title>"
    '<meta name="description" content="' + DESC + '">'
    '<link rel="canonical" href="' + OG + '">'
    '<meta property="og:type" content="website">'
    '<meta property="og:site_name" content="On Record">'
    '<meta property="og:title" content="On Record — Seville, on record">'
    '<meta property="og:description" content="' + CARD + '">'
    '<meta property="og:url" content="' + OG + '">'
    '<meta property="og:image" content="' + OG + 'og/seville.png">'
    '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
    '<meta property="og:image:alt" content="' + ALT + '">'
    '<meta name="twitter:card" content="summary_large_image">'
    '<meta name="twitter:title" content="On Record — Seville, on record">'
    '<meta name="twitter:description" content="' + CARD + '">'
    '<meta name="twitter:image" content="' + OG + 'og/seville.png">'
    '<link rel="manifest" href="manifest.webmanifest">'
    '<meta name="theme-color" content="#05171A">'
    '<link rel="apple-touch-icon" href="og/icon-192.png">'
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
    subs = {"lead-gt": str(_lead),
            "g-then": str(_mean(1951, 1980)),
            "g-now":  str(_mean(LAST_FULL - 9, LAST_FULL))}
    n_done = 0
    for eid, val in subs.items():
        pat = _re.compile(r'(id="%s"[^>]*>)[^<]*(</)' % _re.escape(eid))
        doc, k = pat.subn(lambda m: m.group(1) + val + m.group(2), doc, count=1)
        n_done += k
    print("  baked %d headline numbers into the static document" % n_done)
    return doc
doc = _bake(doc)
(ROOT / "index.html").write_text(doc)   # written AFTER the bake, not before

_KEEP = ["years", "burned", "spent", "copysky", "share-btn", "t-budget", "takeaway", "g-verdict", "impact-know", "ledger-sr", "homepick", "gq-bar", "gq-ex", "homechip", "n-example", "pk-ask", "rc-1-n", "recap-list"]
_missing = [k for k in _KEEP if ('id="%s"' % k) not in doc]
assert not _missing, "PROTECTED elements dropped: %s" % _missing
assert doc.count("haze over the Indo-Gangetic") == 1
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
(ROOT / "sw.js").write_text(_sw)
reuse_css = css + ("@font-face{font-family:'InstrumentSerifX';font-style:normal;font-weight:400;font-display:swap;"
                   "src:url(data:font/woff2;base64,%s) format('woff2')}\n" % fonts["InstrumentSerif-normal-400"])
_rn = buildlib.build_reuse_html(ROOT, reuse_css, buildlib.reuse_data(_d, _d["_meta"]["today"]))
print("offline build: index.html", len(doc), "B | sw BUILD:", _swstamp)
