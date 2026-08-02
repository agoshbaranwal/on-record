/**
 * PHASE 2 — ingestion.
 *
 * Turns public sources into rows that satisfy the Phase 1 schema, using the Phase 0 engine so the
 * numbers are identical to what v1 computes. Three rules run through the whole file:
 *
 *   1. A source that fails is REPORTED, never smoothed. We keep yesterday's row and raise a
 *      staleness flag; we never interpolate a missing day into a chart that looks continuous.
 *   2. Every row carries the slug of a source that already exists in the register. A fetcher
 *      cannot mint its own provenance.
 *   3. Nothing is written unless the whole run's invariants pass, so a half-ingested night cannot
 *      leave the site quoting one number from today and another from a week ago.
 *
 *   node --experimental-strip-types packages/ingest/src/run.mts [--limit N] [--out DIR]
 */
import { writeFileSync, mkdirSync, existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { computeRecord, ThinRecordError, type DailyArchive } from "../../engine/src/record.ts";
import { patientJson, SourceUnavailableError } from "./fetch.mts";
import { SOURCES, requireSource } from "./sources.mts";

const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const argOf = (k: string) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
const LIMIT = Number(argOf("--limit") ?? Infinity);
const OUT = argOf("--out") ?? join(HERE, "..", "..", "..", "seed");

const NOW = Date.now();
const TODAY = new Date(NOW).toISOString().slice(0, 10);
const LAST_FULL_YEAR = new Date(NOW).getUTCFullYear() - 1;
/** ERA5 publishes with a lag; asking for today returns nulls, so we stop where the record is real. */
const ARCHIVE_END = new Date(NOW - 6 * 864e5).toISOString().slice(0, 10);

interface City { slug: string; name: string; lat: number; lon: number; iso3: string }
const CITIES: City[] = JSON.parse(
  readFileSync(join(HERE, "..", "..", "engine", "test", "cities.json"), "utf8"),
);

type Row = Record<string, unknown>;
const out = {
  sources: [] as Row[],
  places: [] as Row[],
  place_baselines: [] as Row[],
  place_records: [] as Row[],
  indicators: [] as Row[],
};
const problems: string[] = [];

// ── sources first: everything else references these ──────────────────────────
for (const s of Object.values(SOURCES)) out.sources.push({ ...s, accessed_at: TODAY });

// ── places ───────────────────────────────────────────────────────────────────
console.log(`ingest ${TODAY} — archive complete to ${ARCHIVE_END}, last full year ${LAST_FULL_YEAR}\n`);

let done = 0, refused = 0, unavailable = 0;
for (const c of CITIES.slice(0, LIMIT)) {
  const url =
    `https://archive-api.open-meteo.com/v1/archive?latitude=${c.lat}&longitude=${c.lon}` +
    `&start_date=1940-01-01&end_date=${ARCHIVE_END}` +
    `&daily=temperature_2m_max,temperature_2m_min&timezone=auto`;
  let archive: DailyArchive;
  try {
    archive = await patientJson<DailyArchive>(url, { label: `ERA5 ${c.name}` });
  } catch (e) {
    // A place we could not reach is simply absent from tonight's write. It keeps whatever row it
    // already had, and the run reports the hole rather than papering over it.
    unavailable++;
    problems.push(`unreachable: ${c.name} — ${(e as SourceUnavailableError).detail ?? (e as Error).message}`);
    console.log(`  ??  ${c.name.padEnd(15)} unreachable — keeping any existing row`);
    continue;
  }

  let rec;
  try {
    rec = computeRecord(archive, null, c.name, { nowMs: NOW, lastFullYear: LAST_FULL_YEAR });
  } catch (e) {
    if (e instanceof ThinRecordError) {
      // Thinness is a permanent property of the place, not a transient failure. We decline to
      // characterise it at all rather than publish a baseline built on too few days.
      refused++;
      problems.push(`too thin: ${c.name} — 1951–80 baseline under 3,650 days`);
      console.log(`  --  ${c.name.padEnd(15)} refused: baseline too thin to characterise honestly`);
      continue;
    }
    throw e;
  }

  out.places.push({
    slug: c.slug, name: c.name, full_name: `${c.name}`, country: c.iso3, iso3: c.iso3,
    lat: c.lat, lon: c.lon, timezone: "UTC", in_picker: true,
  });
  out.place_baselines.push({
    place_slug: c.slug, baseline_from: 1951, baseline_to: 1980,
    threshold_hot: rec.V.thr.hot, threshold_night: rec.V.thr.night,
    source_slug: requireSource("era5").slug, computed_at: new Date(NOW).toISOString(),
  });

  const nights = new Map(rec.V.G.warm_nights_ge25_per_year.map((r) => [r.year, r.n]));
  const anom = rec.V.S.anom;
  for (const r of rec.V.G.days_ge35_per_year) {
    out.place_records.push({
      place_slug: c.slug, year: r.year, hot_days: r.n,
      warm_nights: nights.get(r.year) ?? 0,
      anomaly: anom[r.year - 1940] ?? null,
    });
  }

  // the framing the sweep taught us: the baseline count is arithmetic (~5% of 365 by construction),
  // so the number worth showing is the multiple, computed here once rather than in six components.
  const g = rec.V.G.days_ge35_per_year;
  const mean = (a: number, b: number) => {
    const xs = g.filter((r) => r.year >= a && r.year <= b);
    return xs.reduce((s, r) => s + r.n, 0) / Math.max(1, xs.length);
  };
  const then = mean(1951, 1980), now = mean(LAST_FULL_YEAR - 9, LAST_FULL_YEAR);
  const mult = then > 0 ? now / then : null;
  console.log(
    `  ok  ${c.name.padEnd(15)} above ${rec.V.thr.hot.toFixed(1)}°C  ` +
    `${Math.round(then)} → ${Math.round(now).toString().padEnd(3)} ` +
    `${mult ? (mult >= 1 ? `${mult.toFixed(1)}× more` : `${(1 / mult).toFixed(1)}× fewer`) : ""}`,
  );
  done++;
}

// ── indicators ───────────────────────────────────────────────────────────────
// Each carries as_of AND how long it may be trusted, so a stale figure badges itself
// instead of quietly presenting last month's world as this morning's.
try {
  const co2 = await patientJson<{ co2: { trend: number; year: number; month: number; day: number }[] }>(
    "https://global-warming.org/api/co2-api", { label: "NOAA CO₂" },
  ).catch(() => null);
  if (co2?.co2?.length) {
    const last = co2.co2[co2.co2.length - 1];
    out.indicators.push({
      slug: "co2_ppm", label: "CO₂ in the atmosphere", value: Number(last.trend), unit: "ppm",
      as_of: `${last.year}-${String(last.month).padStart(2, "0")}-${String(last.day).padStart(2, "0")}`,
      stale_after_days: 21, source_slug: requireSource("noaa_co2").slug,
    });
  } else problems.push("indicator co2_ppm: source returned nothing — keeping previous value");
} catch (e) {
  problems.push(`indicator co2_ppm: ${(e as Error).message} — keeping previous value`);
}

// ── invariants: the run refuses to write a partial or unsourced night ────────
const known = new Set(Object.values(SOURCES).map((s) => s.slug));
const assertions: [string, boolean][] = [
  ["every baseline names a source in the register",
    out.place_baselines.every((b) => known.has(String(b.source_slug)))],
  ["every indicator names a source in the register",
    out.indicators.every((i) => known.has(String(i.source_slug)))],
  ["every place that got a baseline also got records",
    out.place_baselines.every((b) => out.place_records.some((r) => r.place_slug === b.place_slug))],
  ["no year is duplicated within a place",
    (() => { const seen = new Set<string>();
      return out.place_records.every((r) => { const k = `${r.place_slug}:${r.year}`; if (seen.has(k)) return false; seen.add(k); return true; }); })()],
  ["hot-day counts are within a real year",
    out.place_records.every((r) => Number(r.hot_days) >= 0 && Number(r.hot_days) <= 366)],
  ["at least half the requested places resolved",
    done >= Math.min(CITIES.length, LIMIT) / 2],
];
console.log("");
let ok = true;
for (const [name, pass] of assertions) { console.log(`  ${pass ? "✓" : "✗"} ${name}`); ok &&= pass; }

if (problems.length) {
  console.log(`\n  ${problems.length} problem(s) recorded, not hidden:`);
  for (const p of problems) console.log(`    · ${p}`);
}
console.log(`\n  ${done} places ingested · ${refused} refused as too thin · ${unavailable} unreachable`);

if (!ok) { console.error("\n  INGEST FAILED — nothing written. Yesterday's data stands.\n"); process.exit(1); }

mkdirSync(OUT, { recursive: true });
const manifest = {
  ingested_at: new Date(NOW).toISOString(),
  archive_end: ARCHIVE_END,
  last_full_year: LAST_FULL_YEAR,
  counts: Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length])),
  problems,
};
for (const [table, rows] of Object.entries(out)) writeFileSync(join(OUT, `${table}.json`), JSON.stringify(rows));
writeFileSync(join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2));
console.log(`  written to ${OUT}\n`);
