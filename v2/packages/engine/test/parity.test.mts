/**
 * PHASE 0 GATE — the TypeScript port must reproduce the shipped v1 engine exactly.
 *
 * Both implementations are handed the same raw ERA5 archive and the same frozen clock, and their
 * entire output object is compared with deepStrictEqual. Nothing is sampled and nothing is rounded
 * for the comparison: if a single per-year count, threshold, anomaly or label differs, this fails.
 *
 * The frozen clock is the whole reason this test can exist. v1 called Date.now() inside the
 * algorithm, so two runs a millisecond apart could legitimately differ; the port takes the clock as
 * an input, which is what makes it verifiable.
 *
 *   node --experimental-strip-types --test test/parity.test.mts
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { makeReference } from "../src/reference.mjs";
import { computeRecord, ThinRecordError } from "../src/record.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const FIX = join(HERE, "..", "fixtures");

// A fixed instant so both implementations see the same "today". 2026-08-02T12:00:00Z.
const FROZEN = Date.UTC(2026, 7, 2, 12, 0, 0);
const LAST_FULL_YEAR = 2025;

/** Cities chosen to exercise different shapes of record, not to flatter the engine. */
const CITIES = [
  { slug: "lucknow",   name: "Lucknow",   lat: 26.84, lon: 80.92, note: "record fell — the honest hard case" },
  { slug: "madrid",    name: "Madrid",    lat: 40.42, lon: -3.70, note: "clear warming" },
  { slug: "reykjavik", name: "Reykjavik", lat: 64.15, lon: -21.94, note: "high latitude, low thresholds" },
];

async function archiveFor(c: (typeof CITIES)[number]) {
  const path = join(FIX, `${c.slug}.json`);
  if (existsSync(path)) return JSON.parse(readFileSync(path, "utf8"));
  const end = new Date(FROZEN - 6 * 864e5).toISOString().slice(0, 10);
  const url =
    `https://archive-api.open-meteo.com/v1/archive?latitude=${c.lat}&longitude=${c.lon}` +
    `&start_date=1940-01-01&end_date=${end}&daily=temperature_2m_max,temperature_2m_min&timezone=auto`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`archive ${c.slug}: HTTP ${r.status}`);
  const j = await r.json();
  mkdirSync(FIX, { recursive: true });
  writeFileSync(path, JSON.stringify(j));
  return j;
}

for (const c of CITIES) {
  test(`port matches v1 exactly — ${c.name} (${c.note})`, async () => {
    const archive = await archiveFor(c);
    const reference = makeReference(() => FROZEN, LAST_FULL_YEAR);

    const forecast = 31.4; // any fixed value; it drives the percentile branch in both
    const expected = reference(archive, forecast, c.name);
    const actual = computeRecord(archive, forecast, c.name, {
      nowMs: FROZEN,
      lastFullYear: LAST_FULL_YEAR,
    });

    assert.deepStrictEqual(actual, expected);
  });
}

test("port matches v1 when there is no forecast (percentile must stay null)", async () => {
  const archive = await archiveFor(CITIES[0]);
  const reference = makeReference(() => FROZEN, LAST_FULL_YEAR);
  const expected = reference(archive, null, "Lucknow");
  const actual = computeRecord(archive, null, "Lucknow", { nowMs: FROZEN, lastFullYear: LAST_FULL_YEAR });
  assert.deepStrictEqual(actual, expected);
  assert.equal(actual.t.pct, null);
});

test("a too-thin baseline is refused, not guessed at — in both", async () => {
  const thin = { daily: { time: ["1951-01-01"], temperature_2m_max: [20], temperature_2m_min: [10] } };
  const reference = makeReference(() => FROZEN, LAST_FULL_YEAR);
  assert.throws(() => reference(thin, null, "Nowhere"), /record too thin/);
  assert.throws(() => computeRecord(thin as never, null, "Nowhere", { nowMs: FROZEN, lastFullYear: LAST_FULL_YEAR }), ThinRecordError);
});

test("the clock is genuinely injected — a different instant gives a different window", async () => {
  const archive = await archiveFor(CITIES[1]);
  const a = computeRecord(archive, null, "Madrid", { nowMs: FROZEN, lastFullYear: LAST_FULL_YEAR });
  const b = computeRecord(archive, null, "Madrid", { nowMs: FROZEN + 40 * 864e5, lastFullYear: LAST_FULL_YEAR });
  assert.notEqual(a.V.anchorISO, b.V.anchorISO);
  // ...but the place's own record must NOT move with the reader's clock
  assert.deepStrictEqual(a.V.G, b.V.G);
  assert.deepStrictEqual(a.V.thr, b.V.thr);
});
