/**
 * Staleness.
 *
 * v1 had one honesty bug of exactly this shape: the colophon said "data frozen at 3 July" while the
 * build stamped August, and nothing caught it because no number knew how old it was allowed to be.
 * Here every indicator declares `stale_after_days`, and the UI is required to render what this
 * returns — so a stale figure announces itself instead of quietly presenting last month as today.
 */
export type Freshness =
  | { state: "fresh"; ageDays: number }
  | { state: "ageing"; ageDays: number; note: string }
  | { state: "stale"; ageDays: number; note: string };

export function freshness(asOf: string, staleAfterDays: number, nowMs: number): Freshness {
  const age = Math.floor((nowMs - Date.parse(`${asOf}T00:00:00Z`)) / 864e5);
  const ageDays = Math.max(0, age);
  if (ageDays <= staleAfterDays) return { state: "fresh", ageDays };
  if (ageDays <= staleAfterDays * 2)
    return { state: "ageing", ageDays, note: `measured ${ageDays} days ago; the source has not published since` };
  return { state: "stale", ageDays, note: `measured ${ageDays} days ago — treat as out of date` };
}
