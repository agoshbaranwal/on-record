#!/usr/bin/env python3
"""Shared build helpers for On Record (Phase 9).

Centralises how impact.json and reuse.html are derived so the citations and the
worksheet on reuse.html can never disagree with the instrument, and the impact
figures are computed in one audited place. pipeline.py is the consumer in the
nightly Action; a local offline-mirror build may import the same functions so
its output matches prod exactly.

Honesty rules baked in here:
  * impact.json is OUTCOME-SIDE ONLY — public traces the code and the archive
    leave in the open. Never the visitor.
  * a metric whose fetch fails is DROPPED and its reason recorded in `omitted` —
    never written as 0 / null / a stale value dressed as fresh.
"""
import json, datetime, subprocess, pathlib


def _mean(series, a, b):
    v = [r["n"] for r in series if a <= r["year"] <= b]
    return sum(v) / len(v) if v else 0


def impact_dict(fetch, today, archive_end, root, built_utc):
    """Build the outcome-side impact record. `fetch(url)` is pipeline.py's stdlib
    helper (raises on failure). Each external block degrades to `omitted`."""
    metrics, omitted = [], []

    # TIER A — GitHub public API (one unauthenticated GET; UA header already set)
    try:
        g = json.loads(fetch("https://api.github.com/repos/agoshbaranwal/on-record"))
        metrics += [
            {"id": "stars", "group": "code", "value": g["stargazers_count"],
             "label": "developers bookmarked the source",
             "caveat": "A star is a bookmark by someone with a GitHub account — not a reader, and not an outcome.",
             "source": "GitHub API · stargazers_count"},
            {"id": "forks", "group": "code", "value": g["forks_count"],
             "label": "copies taken to reuse or adapt",
             "caveat": "A fork is a copy of the code, not evidence it was used.",
             "source": "GitHub API · forks_count"},
            {"id": "watchers", "group": "code", "value": g["subscribers_count"],
             "label": "watching the repository for changes",
             "caveat": "Watchers, not stars — subscribers_count, because GitHub's watchers_count is a misnamed alias of the star count.",
             "source": "GitHub API · subscribers_count"},
        ]
    except Exception as e:
        omitted.append({"id": "github", "reason": "GitHub figures: couldn't reach the API in tonight's build"})

    # TIER A — Wayback CDX (distinct capture-days + first-seen)
    try:
        rows = json.loads(fetch("http://web.archive.org/cdx/search/cdx?url=agoshbaranwal.github.io/on-record*"
                                "&output=json&fl=timestamp&collapse=timestamp:8"))
        data_rows = rows[1:] if (rows and isinstance(rows[0], list) and rows[0] and rows[0][0] == "timestamp") else rows
        metrics.append(
            {"id": "wayback_snapshots", "group": "archive", "value": len(data_rows),
             "label": "days the public web archive holds a copy",
             "caveat": "A snapshot is the Internet Archive's robot capturing the page, not a person visiting it. Captures are irregular.",
             "source": "Internet Archive Wayback CDX"})
        if data_rows:
            ts = str(data_rows[0][0])
            metrics.append(
                {"id": "wayback_first", "group": "archive",
                 "value": ts[:4] + "-" + ts[4:6] + "-" + ts[6:8],
                 "label": "first preserved in the public archive",
                 "caveat": "Earliest capture the Archive holds — preservation, not readership.",
                 "source": "Internet Archive Wayback CDX"})
    except Exception as e:
        omitted.append({"id": "wayback", "reason": "Internet Archive figures: couldn't reach the Wayback API in tonight's build"})

    # TIER B — derived, no third party, cannot fail (renders unconditionally)
    metrics.append(
        {"id": "data_lag_days", "group": "cadence", "value": (today - archive_end).days,
         "label": "days the record trails real time",
         "caveat": "ERA5's publication lag — a property of the data, not a limitation we chose.",
         "source": "derived · today − archive_end"})
    metrics.append(
        {"id": "last_built", "group": "cadence", "value": str(today),
         "label": "the record was last rebuilt",
         "caveat": "When the nightly Action last ran. It says nothing about who saw the result.",
         "source": "derived · build date"})
    # commits — only from a full clone; a shallow clone would falsely show 1
    try:
        shallow = (pathlib.Path(root) / ".git" / "shallow").exists()
        cnt = int(subprocess.check_output(["git", "rev-list", "--count", "HEAD"],
                                          cwd=str(root)).decode().strip())
        if shallow and cnt <= 1:
            raise RuntimeError("shallow clone")
        metrics.append(
            {"id": "commits", "group": "cadence", "value": cnt,
             "label": "revisions to the public source",
             "caveat": "Our activity on the code, not its effect on anyone.",
             "source": "derived · git rev-list --count HEAD"})
    except Exception:
        omitted.append({"id": "commits", "reason": "commit count unavailable (shallow clone or git absent)"})

    return {"as_of": built_utc, "metrics": metrics, "omitted": omitted}


def reuse_data(out, build_iso):
    """Everything reuse.html injects — every citation/worksheet number derived
    from `out` (site-data), so the page can never drift from the instrument."""
    g35 = out["seville_generational"]["days_ge35_per_year"]
    gwn = out["seville_generational"]["warm_nights_ge25_per_year"]
    # LF = last COMPLETE calendar year, exactly as the instrument derives it (the Delhi
    # honesty array is filtered to <= LAST_FULL). The Seville generational array carries a
    # partial current year, so max(seville year) would wrongly pull the "now" window forward.
    LF = out["delhi_honesty"]["days_ge35_per_year"][-1]["year"]
    dr = out["delhi_honesty"]["receipts"]
    b = out["budget"]; est = b["estimates"]
    tn = out["the_number"]; pg = out["perception_gap"]; sf = out["seville_frequency"]
    bd = datetime.date.fromisoformat(build_iso)
    co2 = datetime.date.fromisoformat(tn["co2_date"])

    def human(d):
        return "%d %s %d" % (d.day, d.strftime("%B"), d.year)

    return {
        "build_iso": build_iso, "build_human": human(bd),
        "sev_days_was": round(_mean(g35, 1951, 1980)), "sev_days_now": round(_mean(g35, LF - 9, LF)),
        "sev_nights_was": round(_mean(gwn, 1951, 1980)), "sev_nights_now": round(_mean(gwn, LF - 9, LF)),
        "sev_rec_c": sf["same_date_record_C"], "sev_rec_y": sf["same_date_record_year"], "sev_bias": sf["bias_C"],
        "delhi_nights_was": round(dr["warm_nights_then"]), "delhi_nights_now": round(dr["warm_nights_now"]),
        "delhi_days_was": round(dr["days_ge35_then"]), "delhi_days_now": round(dr["days_ge35_now"]),
        "budget_lo": round(est[0]["remaining_now_gt"]), "budget_hi": round(est[1]["remaining_now_gt"]),
        # source names follow the SORT, exactly as the instrument's srcShort does — so a future annual
        # revision that swaps which team is lower can never mis-attribute one team's figure to the other
        "budget_lo_src": ("IGCC 2025" if "igcc" in est[0].get("label", "").lower() else "Global Carbon Budget 2025"),
        "budget_hi_src": ("IGCC 2025" if "igcc" in est[1].get("label", "").lower() else "Global Carbon Budget 2025"),
        "rate": round(b["rate_now_gt"]), "years_left": round(est[0]["years_at_now"], 1),
        "co2_ppm": round(tn["co2_ppm"]), "co2_date_human": human(co2),
        "want_action": pg["global_want_action_pct"], "countries": pg["countries"],
        "scc": b["scc"]["usd_per_t"],
        "eras_then": "1951–1980", "eras_now": "%d–%d" % (LF - 9, LF),
        "impact": out.get("impact"),   # the same outcome-side record Bedrock renders (no runtime fetch)
    }


def build_reuse_html(root, fonts_css, rdata):
    """Inject fonts + reuse-data into reuse-src.html (template) → reuse.html (deployed),
    mirroring the instrument.html → index.html split. Also SERVER-FILLS the data-rd spans so
    the document's prose numbers read correctly with JavaScript off (the interactive snippet /
    citation builders still enhance with JS)."""
    import re as _re
    root = pathlib.Path(root)
    tpl = (root / "reuse-src.html").read_text()
    doc = (tpl.replace("/*__FONTS__*/", fonts_css)
              .replace("/*__REUSE_DATA__*/ null", json.dumps(rdata, separators=(",", ":"))))

    def _fill_key(m):
        v = rdata.get(m.group(2))
        return m.group(1) + (str(v) if v is not None else m.group(3)) + "</"
    doc = _re.sub(r'(<[^>]*\bdata-rd="([a-z0-9_]+)"[^>]*>)([^<]*)</', _fill_key, doc)
    doc = _re.sub(r'(<[^>]*\bdata-rd-date\b[^>]*>)[^<]*</',
                  lambda m: m.group(1) + rdata["build_human"] + "</", doc)
    _ce = ", ".join("%s %d%% (guessed %d%%)" % (c["place"], c["actual"], c["guess"]) for c in rdata["countries"]) + "."
    doc = doc.replace('<span id="country-eg">–</span>', '<span id="country-eg">' + _ce + '</span>')
    doc = doc.replace('<span id="ws-q1">–</span>',
                      '<span id="ws-q1">%d</span>' % round(rdata["sev_days_now"] - rdata["sev_days_was"]))

    assert "__REUSE_DATA__" not in doc and "__FONTS__" not in doc, "reuse placeholder left"
    (root / "reuse.html").write_text(doc)
    return len(doc)
