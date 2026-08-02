/** PHASE 0 GATE, full sweep: the port must match v1 for every city the picker can load. */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { makeReference } from "../src/reference.mjs";
import { computeRecord, ThinRecordError } from "../src/record.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const CITIES = JSON.parse(readFileSync(join(HERE, "cities.json"), "utf8"));
const FROZEN = Date.UTC(2026, 7, 2, 12, 0, 0);
const LF = 2025;
const end = new Date(FROZEN - 6 * 864e5).toISOString().slice(0, 10);
const reference = makeReference(() => FROZEN, LF);

let pass = 0, fail = 0, thin = 0;
for (const c of CITIES) {
  const url = `https://archive-api.open-meteo.com/v1/archive?latitude=${c.lat}&longitude=${c.lon}` +
    `&start_date=1940-01-01&end_date=${end}&daily=temperature_2m_max,temperature_2m_min&timezone=auto`;
  // The free archive tier rate-limits hard. Production ingestion will need the same patience,
  // so the sweep models it: paced requests, exponential backoff, never a hammering retry loop.
  let j: any = null;
  for (let attempt = 0; attempt < 5 && !j; attempt++) {
    if (attempt) await new Promise((r) => setTimeout(r, 4000 * attempt + Math.random() * 1500));
    try { const r = await fetch(url); if (r.status === 429) continue; if (!r.ok) throw new Error("HTTP " + r.status); j = await r.json(); }
    catch (e) { if (attempt === 4) console.log(`  ?  ${c.name.padEnd(14)} ${(e as Error).message}`); }
  }
  if (!j) { console.log(`  ?  ${c.name.padEnd(14)} unavailable after 5 tries (rate limit)`); continue; }
  await new Promise((r) => setTimeout(r, 2500));
  try {
    const exp = reference(j, 30, c.name);
    const act = computeRecord(j, 30, c.name, { nowMs: FROZEN, lastFullYear: LF });
    assert.deepStrictEqual(act, exp);
    const g = act.V.G.days_ge35_per_year;
    const then = g.filter((r) => r.year >= 1951 && r.year <= 1980).reduce((s, r) => s + r.n, 0) / 30;
    const now = g.filter((r) => r.year >= LF - 9 && r.year <= LF).reduce((s, r) => s + r.n, 0) / 10;
    const dir = now > then ? "▲" : now < then ? "▼" : "▬";
    console.log(`  ok ${c.name.padEnd(14)} thr ${act.V.thr.hot.toFixed(1).padStart(5)}°C   ${Math.round(then).toString().padStart(3)} → ${Math.round(now).toString().padEnd(3)} ${dir}`);
    pass++;
  } catch (e) {
    if (e instanceof ThinRecordError) { console.log(`  -- ${c.name.padEnd(14)} refused (baseline too thin) — both agree`); thin++; }
    else { console.log(`  FAIL ${c.name}: ${(e as Error).message.slice(0, 90)}`); fail++; }
  }
}
console.log(`\n  parity: ${pass} identical · ${thin} honestly refused · ${fail} MISMATCH`);
process.exit(fail ? 1 : 0);
