/** Phase 2 output, read straight from disk. Phase 4 swaps this for Supabase; nothing else changes. */
import { readFileSync } from "node:fs";
import { join } from "node:path";
const SEED = join(process.cwd(), "..", "..", "seed");
const read = <T,>(f: string): T => JSON.parse(readFileSync(join(SEED, f), "utf8")) as T;

export interface Place { slug: string; name: string; iso3: string }
export interface Baseline { place_slug: string; threshold_hot: number; source_slug: string }
export interface Record_ { place_slug: string; year: number; hot_days: number; warm_nights: number }
export interface Indicator { slug: string; label: string; value: number; unit: string; as_of: string; stale_after_days: number; source_slug: string }
export interface Source { slug: string; name: string; organisation: string; url: string; licence: string; citation: string }

export const places = () => read<Place[]>("places.json");
export const baselines = () => read<Baseline[]>("place_baselines.json");
export const records = () => read<Record_[]>("place_records.json");
export const indicators = () => read<Indicator[]>("indicators.json");
export const sources = () => read<Source[]>("sources.json");
export const manifest = () => read<{ ingested_at: string; archive_end: string; last_full_year: number }>("manifest.json");

/** The framing the sweep taught us: the baseline count is ~5% of 365 by construction, so the
 *  number worth showing is the MULTIPLE, not the pair. Computed once, here. */
export function multiple(rows: Record_[], lastFullYear: number) {
  const mean = (a: number, b: number) => {
    const xs = rows.filter((r) => r.year >= a && r.year <= b);
    return xs.reduce((s, r) => s + r.hot_days, 0) / Math.max(1, xs.length);
  };
  const then = mean(1951, 1980), now = mean(lastFullYear - 9, lastFullYear);
  return { then, now, mult: then > 0 ? now / then : null, direction: now > then ? "more" : now < then ? "fewer" : "level" as const };
}
