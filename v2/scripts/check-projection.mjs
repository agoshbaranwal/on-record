/**
 * No single-value futures.
 *
 * v1's dial printed "2100 arrives about 2.8 °C hotter" — one number, where TCRE is a published
 * RANGE and the honest answer is 2.2–3.3. Stating the midpoint as the answer is the most
 * respectable-looking overclaim on a climate site, and it is exactly what an expert closes the tab
 * over. The type here cannot express a bare number; this proves the implementation agrees.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
const ROOT = fileURLToPath(new URL("..", import.meta.url));
const src = readFileSync(join(ROOT, "apps/web/lib/projection.ts"), "utf8");

let ok = true;
const say = (p, m) => { console.log(`  ${p ? "✓" : "✗"} ${m}`); ok &&= p; };

say(/interface Range[\s\S]*?low: number;[\s\S]*?high: number;/.test(src), "a projection is a range, structurally");
say(/interval: string/.test(src) && /basis: string/.test(src),
  "every range names its interval and its basis");
say(/warmingAt\([^)]*\): Range/.test(src), "warmingAt cannot return a scalar");
say(/not a pathway model/.test(src), "the arithmetic is labelled as arithmetic");
say(!/return\s+round1\(WARMING_NOW \+ cumulative \* TCRE\.best\)/.test(src),
  "the best estimate is never returned alone");

// live behaviour
const mod = await import(join(ROOT, "apps/web/lib/projection.ts"));
const r = mod.warmingAt(74, 42.2);
say(typeof r === "object" && "low" in r && "high" in r, `warmingAt returns a range (${r.low}–${r.high})`);
say(r.high > r.low, "the range has real width");
say(/AR6/.test(r.basis), "the basis cites a source");
console.log(`      74 years at 42.2 Gt/yr → ${mod.formatRange(r)} · ${r.interval}`);
console.log(`      band: ${mod.band(r)}`);

console.log(ok ? "\n  PROJECTION INVARIANTS PASS" : "\n  *** PROJECTION INVARIANTS FAILED ***");
process.exit(ok ? 0 : 1);
