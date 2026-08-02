/**
 * What's coming.
 *
 * THE HONEST CONSTRAINT, stated first: this site has no downscaled projection dataset. It cannot
 * tell a reader how many hot days their city will have in 2050, and it must not pretend to. v1's
 * own limits page says exactly that, and it stays true here.
 *
 * What the site CAN say is bounded and still worth saying: published warming levels, and the
 * TCRE relationship between cumulative CO2 and global temperature — which is arithmetic, not a
 * pathway model, and is labelled as such wherever it appears.
 *
 * So the type system refuses a bare number. Every projected quantity is a RANGE with a named
 * basis. There is no way to express "2.8 °C in 2100" here; the only expressible form is
 * "2.2–3.3 °C, likely range, TCRE per IPCC AR6". check-projection.mjs enforces it in CI.
 */

export interface Range {
  low: number;
  high: number;
  /** What kind of interval this is, in the source's own words. */
  interval: string;      // e.g. "likely (17–83%)"
  unit: string;
  basis: string;         // e.g. "TCRE per IPCC AR6, held-rate arithmetic"
  sourceSlug: string;
}

/** IPCC AR6 transient climate response to cumulative emissions, °C per 1000 GtCO₂. */
export const TCRE = { best: 0.45, low: 0.27, high: 0.63, interval: "likely (17–83%)" } as const;

/** Human-induced warming to date, IGCC 2025. */
export const WARMING_NOW = 1.37;

/**
 * Warming by a horizon year if the current rate simply continues. Held-rate arithmetic — NOT a
 * pathway model, and never returned as a single figure.
 */
export function warmingAt(yearsAhead: number, gtPerYear: number): Range {
  const cumulative = (yearsAhead * gtPerYear) / 1000; // thousands of GtCO₂
  return {
    low: round1(WARMING_NOW + cumulative * TCRE.low),
    high: round1(WARMING_NOW + cumulative * TCRE.high),
    interval: TCRE.interval,
    unit: "°C above pre-industrial",
    basis: "held-rate arithmetic × TCRE (IPCC AR6) — not a pathway model",
    sourceSlug: "igcc-2025",
  };
}

const round1 = (n: number) => Math.round(n * 10) / 10;

export const formatRange = (r: Range) => `${r.low}–${r.high} ${r.unit}`;

/** Risk rises continuously; these are labels on a gradient, never thresholds crossed. */
export function band(r: Range): string {
  const mid = (r.low + r.high) / 2;
  if (mid < 1.5) return "inside 1.5 °C — no current pathway reaches this";
  if (mid < 2) return "past 1.5 °C, short of 2 — every tenth of a degree adds risk";
  if (mid < 3) return "past 2 °C — the range the Paris agreement was written to avoid";
  return "past 3 °C — beyond anything the modern world has lived in";
}
