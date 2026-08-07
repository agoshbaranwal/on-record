import Link from "next/link";
import { places, baselines, records, manifest, multiple } from "@/lib/seed";
import s from "../place.module.css";

export const metadata = { title: "Every place on record — On Record" };

/**
 * The index a reference site cannot be without: every place, its headline multiple, sortable by
 * eye. Server-rendered, complete without JS.
 *
 * (Recreated: the original was lost to a `git reset --hard` during a nightly-refresh race —
 * uncommitted work and race resolution must never happen in the same step.)
 */
export default function Places() {
  const m = manifest();
  const base = new Map(baselines().map((b) => [b.place_slug, b]));
  const byPlace = new Map<string, ReturnType<typeof records>>();
  for (const r of records()) { const a = byPlace.get(r.place_slug) ?? []; a.push(r); byPlace.set(r.place_slug, a); }

  const rows = places().map((p) => {
    const { then, now, mult, direction } = multiple(byPlace.get(p.slug) ?? [], m.last_full_year);
    return { ...p, then, now, mult, direction, factor: mult ? (mult >= 1 ? mult : 1 / mult) : 0 };
  }).sort((a, b) => b.factor - a.factor);

  return (
    <main className="wrap">
      <p className="t-label"><Link href="/">On Record</Link></p>
      <h1 className="t-head">Every place on record</h1>
      <p className="t-lead">
        Sorted by how much the record moved. A place that cooled is listed with the same standing
        as one that warmed.
      </p>

      <div style={{ marginTop: "var(--s-6)" }}>
        {rows.map((p) => (
          <div key={p.slug} className={s.row} data-name={p.name.toLowerCase()}>
            <div className={s.rowTop}>
              <Link className="t-body" href={`/place/${p.slug}`}>{p.name}</Link>
              <span className={`t-head num ${p.direction === "fewer" ? "" : "accent"}`}>
                {p.mult ? `${p.factor.toFixed(1)}× ${p.direction}` : "—"}
              </span>
            </div>
            <p className="t-aside">
              dangerously hot days: about {Math.round(p.then)} a year in 1951–80, about {Math.round(p.now)} now
              · threshold {base.get(p.slug)?.threshold_hot}&nbsp;°C
            </p>
          </div>
        ))}
      </div>

      <p className={`t-label ${s.meta}`}>
        {rows.length} places · archive complete to {m.archive_end} · every figure computed from that
        place&rsquo;s own ERA5 record; thresholds are its own 1951–80 95th percentile.
      </p>
    </main>
  );
}
