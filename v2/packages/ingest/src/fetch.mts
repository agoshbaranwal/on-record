/**
 * Patient HTTP.
 *
 * The v1 sweep taught us the hard way: the free archive tier returns 429 after roughly five rapid
 * requests. A naive loop over 24 cities loses two thirds of them and, worse, looks like a data
 * problem rather than a rate limit. So every fetch in this pipeline is paced and backs off, and a
 * failure is reported as a failure — never smoothed into a gap that a chart would draw through.
 */

export interface FetchOptions {
  /** Attempts before giving up. */
  tries?: number;
  /** Minimum gap between any two requests to the same host. */
  paceMs?: number;
  label?: string;
}

const lastCallAt = new Map<string, number>();

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Thrown when a source is unreachable. Callers must keep yesterday's row, not invent today's. */
export class SourceUnavailableError extends Error {
  // NOTE: written as explicit fields, not TS parameter properties. Node's --experimental-strip-types
  // only ERASES types; a parameter property would require it to EMIT an assignment, which it will not do.
  readonly label: string;
  readonly detail: string;
  constructor(label: string, detail: string) {
    super(`${label} unavailable: ${detail}`);
    this.name = "SourceUnavailableError";
    this.label = label;
    this.detail = detail;
  }
}

export async function patientJson<T = unknown>(url: string, opts: FetchOptions = {}): Promise<T> {
  const { tries = 5, paceMs = 2500, label = new URL(url).hostname } = opts;
  const host = new URL(url).hostname;

  for (let attempt = 0; attempt < tries; attempt++) {
    // pace: never hit the same host faster than paceMs, regardless of who is calling
    const since = Date.now() - (lastCallAt.get(host) ?? 0);
    if (since < paceMs) await sleep(paceMs - since);
    lastCallAt.set(host, Date.now());

    try {
      const res = await fetch(url, { headers: { "User-Agent": "on-record/2.0 (agoshbaranwal@gmail.com)" } });
      if (res.status === 429 || res.status === 503) {
        // jittered exponential backoff — the jitter matters when several jobs run on the same cron
        const wait = 4000 * (attempt + 1) + Math.random() * 1500;
        if (attempt === tries - 1) throw new SourceUnavailableError(label, `HTTP ${res.status} after ${tries} tries`);
        await sleep(wait);
        continue;
      }
      if (!res.ok) throw new SourceUnavailableError(label, `HTTP ${res.status}`);
      return (await res.json()) as T;
    } catch (e) {
      if (e instanceof SourceUnavailableError) throw e;
      if (attempt === tries - 1) throw new SourceUnavailableError(label, (e as Error).message);
      await sleep(3000 * (attempt + 1));
    }
  }
  throw new SourceUnavailableError(label, "exhausted");
}

export async function patientText(url: string, opts: FetchOptions = {}): Promise<string> {
  const { tries = 5, paceMs = 2500, label = new URL(url).hostname } = opts;
  for (let attempt = 0; attempt < tries; attempt++) {
    try {
      const res = await fetch(url, { headers: { "User-Agent": "on-record/2.0 (agoshbaranwal@gmail.com)" } });
      if (res.status === 429 || res.status === 503) {
        if (attempt === tries - 1) throw new SourceUnavailableError(label, `HTTP ${res.status}`);
        await sleep(4000 * (attempt + 1) + Math.random() * 1500);
        continue;
      }
      if (!res.ok) throw new SourceUnavailableError(label, `HTTP ${res.status}`);
      return await res.text();
    } catch (e) {
      if (e instanceof SourceUnavailableError) throw e;
      if (attempt === tries - 1) throw new SourceUnavailableError(label, (e as Error).message);
      await sleep(3000 * (attempt + 1));
    }
  }
  throw new SourceUnavailableError(label, "exhausted");
}
