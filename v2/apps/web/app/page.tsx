import Link from "next/link";
import s from "./place.module.css";
import { places, baselines, records, indicators, sources, manifest, multiple } from "@/lib/seed";
import { freshness } from "@onrecord/engine/staleness";

export default function Home() {
  const m = manifest();
  const src = new Map(sources().map((x) => [x.slug, x]));
  const base = new Map(baselines().map((b) => [b.place_slug, b]));
  const byPlace = new Map<string, ReturnType<typeof records>>();
  for (const r of records()) { const a = byPlace.get(r.place_slug) ?? []; a.push(r); byPlace.set(r.place_slug, a); }

  return (
    <main className="wrap">
      <h1 className="t-head">What the record shows</h1>
      <p className="t-lead">Every number here is measured, and says where it came from.</p>

      {indicators().map((i) => {
        const f = freshness(i.as_of, i.stale_after_days, Date.now());
        return (
          <section key={i.slug} style={{ marginTop: "var(--s-8)" }}>
            <div className="t-display num accent">{i.value}<span className="t-aside"> {i.unit}</span></div>
            <div className="t-body">{i.label}</div>
            <p className="t-label">
              {f.state === "fresh" ? `measured ${i.as_of}` : <span className={s.badge}>{f.note}</span>}
              {" · "}{src.get(i.source_slug)?.organisation}
            </p>
          </section>
        );
      })}

      <hr className="rule" />
      <h2 className="t-label">Places on record</h2>
      {places().map((p) => {
        const rows = byPlace.get(p.slug) ?? [];
        const b = base.get(p.slug);
        const { then, now, mult, direction } = multiple(rows, m.last_full_year);
        return (
          <div key={p.slug} className={s.row}>
            <div className={s.rowTop}>
              <Link className="t-body" href={`/place/${p.slug}`}>{p.name}</Link>
              <span className="t-head num accent">
                {mult ? `${(mult >= 1 ? mult : 1 / mult).toFixed(1)}× ${direction}` : "—"}
              </span>
            </div>
            <p className="t-aside">
              days above {b?.threshold_hot}&nbsp;°C: about {Math.round(then)} a year in 1951–80, about {Math.round(now)} now
            </p>
          </div>
        );
      })}

      <hr className="rule" />
      <nav className={s.nav} aria-label="Sections">
        <Link className="t-body" href="/whats-left">What&rsquo;s left &mdash; the world&rsquo;s carbon budget</Link>
        <Link className="t-body" href="/whats-coming">What&rsquo;s coming</Link>
        <Link className="t-body" href="/why-it-matters">Why it matters</Link>
        <Link className="t-body" href="/whats-working">What&rsquo;s working</Link>
        <Link className="t-body" href="/how-we-know">How we know</Link>
        <Link className="t-body" href="/privacy">What we collect</Link>
      </nav>

      <p className={`t-label ${s.meta}`}>
        Ingested {m.ingested_at.slice(0, 10)} · archive complete to {m.archive_end} · last full year {m.last_full_year}
      </p>
    </main>
  );
}
