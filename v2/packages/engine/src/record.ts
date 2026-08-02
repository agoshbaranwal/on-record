/**
 * The place-record engine.
 *
 * Ported from the v1 single-file build (`instrument.html`, `compute()`), which computes any city's
 * whole 1940→today heat record in the browser from a raw ERA5 daily archive. That algorithm is
 * hard-won and is kept EXACTLY — this port changes the plumbing around it, not the arithmetic:
 *
 *   1. The clock is injected. v1 called `Date.now()` in four places, which made the function
 *      non-deterministic and therefore untestable. `nowMs` is now a required input.
 *   2. `LF` (the last full year of record) is injected rather than read from a global.
 *   3. Types, so a caller cannot silently pass the wrong shape.
 *
 * `test/parity.test.mjs` asserts this produces output deep-equal to the extracted v1 reference for
 * real archives. If you change the arithmetic here, that test fails — which is the point.
 */

/** A raw Open-Meteo daily archive response. */
export interface DailyArchive {
  daily: {
    time: string[];                        // ISO dates, ascending
    temperature_2m_max: (number | null)[];
    temperature_2m_min: (number | null)[];
  };
}

export interface YearCount { year: number; n: number }

export interface PlaceRecord {
  V: {
    custom: true;
    place: string;
    anchorISO: string;
    ydom: [number, number];
    ticks: number[];
    RW: {
      labels: string[];
      spaghetti: Record<string, (number | null)[]>;
      old_normal_1951_1980: (number | null)[];
      new_normal_last30: (number | null)[];
      record_envelope: (number | null)[];
      new_normal_label: string;
    };
    S: { year0: 1940; anom: number[] };
    G: { days_ge35_per_year: YearCount[]; warm_nights_ge25_per_year: YearCount[] };
    thr: { hot: number; night: number; hotLabel: string; nightLabel: string };
  };
  t: {
    mode: "live";
    tmax: number | null;
    comparable: number | null;
    dateISO: string;
    dateLabel: string;
    fetched: string;
    rec: number | null;
    recy: number | null;
    n: number;
    pct: number | null;
    bias: 0; h40a: 0; h40b: 0;
  };
}

export interface ComputeOptions {
  /** Wall clock, injected. v1 read Date.now() directly, which made it impossible to test. */
  nowMs: number;
  /** Last full year of the record. */
  lastFullYear: number;
}

const MONS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"] as const;

/** v1's percentile: nearest-rank on a pre-sorted array. Kept exactly — changing it moves every threshold. */
function qtile(sorted: number[], p: number): number | null {
  if (!sorted.length) return null;
  return sorted[Math.min(sorted.length - 1, Math.floor((p / 100) * (sorted.length - 1)))];
}

function dLabel(iso: string): string {
  const p = iso.split("-");
  return `${+p[2]} ${MONS[+p[1] - 1]}`;
}

/** Thrown when the 1951–80 baseline is too sparse to characterise a place honestly. */
export class ThinRecordError extends Error {
  constructor() { super("record too thin"); this.name = "ThinRecordError"; }
}

export function computeRecord(
  archive: DailyArchive,
  forecast: number | null,
  placeName: string,
  { nowMs, lastFullYear: LF }: ComputeOptions,
): PlaceRecord {
  const d = archive.daily;
  const N = d.time.length, date = d.time, tx = d.temperature_2m_max, tn = d.temperature_2m_min;

  const md: Record<string, [number, number][]> = {};
  const annual: Record<number, number[]> = {};
  const oldTx: number[] = [], oldTn: number[] = [];

  for (let i = 0; i < N; i++) {
    const v = tx[i];
    if (v == null) continue;
    const y = +date[i].slice(0, 4);
    const k = date[i].slice(5);
    (md[k] = md[k] || []).push([y, v]);
    (annual[y] = annual[y] || []).push(v);
    if (y >= 1951 && y <= 1980) { oldTx.push(v); const nv = tn[i]; if (nv != null) oldTn.push(nv); }
  }
  // A place needs ~10 years of baseline days before we will characterise it at all.
  if (oldTx.length < 3650) throw new ThinRecordError();

  oldTx.sort((a, b) => a - b); oldTn.sort((a, b) => a - b);
  const thrHot = Math.round(qtile(oldTx, 95)! * 10) / 10;
  const thrNight = Math.round(qtile(oldTn, 95)! * 10) / 10;

  const cH: Record<number, number> = {}, cN: Record<number, number> = {};
  for (let i = 0; i < N; i++) {
    const y = +date[i].slice(0, 4);
    const vx = tx[i], vn = tn[i];
    if (vx != null && vx >= thrHot) cH[y] = (cH[y] || 0) + 1;
    if (vn != null && vn >= thrNight) cN[y] = (cN[y] || 0) + 1;
  }
  const series = (c: Record<number, number>): YearCount[] => {
    const out: YearCount[] = [];
    for (let y = 1940; y <= LF; y++) out.push({ year: y, n: c[y] || 0 });
    return out;
  };

  // the window: 25 days back to 25 days ahead of "today"
  const WN = 51, anchorMs = nowMs - 25 * 864e5;
  const anchorISO = new Date(anchorMs).toISOString().slice(0, 10);
  const labels: string[] = [], keys: string[] = [];
  for (let i = 0; i < WN; i++) {
    const dd = new Date(anchorMs + i * 864e5);
    labels.push(`${MONS[dd.getUTCMonth()]} ${dd.getUTCDate()}`);
    keys.push(dd.toISOString().slice(5, 10));
  }

  const spag: Record<string, (number | null)[]> = {};
  const oldB: (number | null)[] = [], newB: (number | null)[] = [], env: (number | null)[] = [];
  let lo = 99, hi = -99;
  const m2 = (a: number[]): number | null => {
    if (!a.length) return null;
    let t = 0; for (let j = 0; j < a.length; j++) t += a[j];
    return Math.round((t / a.length) * 10) / 10;
  };
  for (let i = 0; i < WN; i++) {
    const rows = md[keys[i]] || [], olds: number[] = [], news: number[] = [], all: number[] = [];
    for (let r = 0; r < rows.length; r++) {
      const yy = rows[r][0], v = rows[r][1];
      let s = spag[yy];
      if (!s) { s = spag[yy] = []; for (let z = 0; z < WN; z++) s.push(null); }
      s[i] = Math.round(v * 10) / 10;
      all.push(v);
      if (yy >= 1951 && yy <= 1980) olds.push(v);
      if (yy >= LF - 29 && yy <= LF) news.push(v);
      if (v < lo) lo = v; if (v > hi) hi = v;
    }
    oldB.push(m2(olds)); newB.push(m2(news));
    env.push(all.length ? Math.round(Math.max.apply(null, all) * 10) / 10 : null);
  }

  const ydom: [number, number] = [Math.floor((lo - 2) / 5) * 5, Math.ceil((hi + 2) / 5) * 5];
  const ticks: number[] = [];
  for (let i = ydom[0]; i <= ydom[1]; i += 5) ticks.push(i);

  // annual anomaly vs the 1951–80 mean of annual means
  const base: number[] = [];
  for (let y = 1951; y <= 1980; y++) {
    const a = annual[y];
    if (a) { let t = 0; for (let i = 0; i < a.length; i++) t += a[i]; base.push(t / a.length); }
  }
  const bmean = base.length ? base.reduce((a, b) => a + b, 0) / base.length : 0;
  const anom: number[] = [];
  for (let y = 1940; y <= LF; y++) {
    const a = annual[y];
    if (a && a.length > 300) {
      let t = 0; for (let i = 0; i < a.length; i++) t += a[i];
      anom.push(Math.round((t / a.length - bmean) * 100) / 100);
    } else anom.push(0);
  }

  // today against its own date
  const todayISO = new Date(nowMs).toISOString().slice(0, 10), tk = todayISO.slice(5);
  const exact = md[tk] || [];
  let rec: number | null = null, recy: number | null = null;
  for (let i = 0; i < exact.length; i++) if (rec == null || exact[i][1] > rec) { rec = exact[i][1]; recy = exact[i][0]; }

  const wvals: number[] = [];
  for (let i = -7; i <= 7; i++) {
    const wd = new Date(nowMs + i * 864e5).toISOString().slice(5, 10);
    (md[wd] || []).forEach((rv) => wvals.push(rv[1]));
  }
  wvals.sort((a, b) => a - b);
  let pct: number | null = null;
  if (forecast != null && wvals.length) {
    let le = 0;
    for (let i = 0; i < wvals.length; i++) if (wvals[i] <= forecast) le++;
    pct = Math.min(100, Math.round((100 * le) / wvals.length));
  }

  return {
    V: {
      custom: true, place: placeName, anchorISO, ydom, ticks,
      RW: {
        labels, spaghetti: spag,
        old_normal_1951_1980: oldB, new_normal_last30: newB,
        record_envelope: env, new_normal_label: `${LF - 29}–${LF}`,
      },
      S: { year0: 1940, anom },
      G: { days_ge35_per_year: series(cH), warm_nights_ge25_per_year: series(cN) },
      thr: {
        hot: thrHot, night: thrNight,
        hotLabel: `hotter than 95% of days here in 1951–80 (above ${thrHot.toFixed(1)} °C)`,
        nightLabel: `below ${thrNight.toFixed(1)} °C — warmer than 95% of nights here in 1951–80`,
      },
    },
    t: {
      mode: "live", tmax: forecast, comparable: forecast,
      dateISO: todayISO, dateLabel: dLabel(todayISO), fetched: todayISO,
      rec, recy, n: exact.length, pct, bias: 0, h40a: 0, h40b: 0,
    },
  };
}
