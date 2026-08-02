import { notFound } from "next/navigation";
import { Column } from "@/components/Column";
import { places, baselines, records, sources, manifest, multiple } from "@/lib/seed";
import s from "../../place.module.css";

export function generateStaticParams() { return places().map((p) => ({ slug: p.slug })); }

export default async function PlacePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const place = places().find((p) => p.slug === slug);
  if (!place) notFound();
  const m = manifest();
  const rows = records().filter((r) => r.place_slug === slug).sort((a, b) => a.year - b.year);
  const base = baselines().find((b) => b.place_slug === slug)!;
  const src = sources().find((x) => x.slug === base.source_slug)!;
  const { then, now, mult, direction } = multiple(rows, m.last_full_year);
  const max = Math.max(...rows.map((r) => r.hot_days), 1);

  // The headline is the MULTIPLE, never the pair: the 1951-80 count is ~5% of 365 by construction,
  // so presenting "19 → 56" implies two measurements of equal standing when the first is arithmetic.
  const factor = mult ? (mult >= 1 ? mult : 1 / mult).toFixed(1) : null;

  return (
    <main className="wrap">
      <p className="t-label">Your place</p>
      <h1 className="t-head" style={{ marginTop: "var(--s-1)" }}>{place.name}</h1>

      <section id="hot-days" style={{ marginTop: "var(--s-8)" }}>
        <div className="t-display num accent">{factor ? `${factor}×` : "—"}</div>
        <p className="t-lead">
          {direction === "fewer"
            ? <>fewer dangerously hot days a year than a lifetime ago. The record here went down, and we draw it that way.</>
            : direction === "more"
            ? <>more dangerously hot days a year than a lifetime ago.</>
            : <>about the same number of dangerously hot days as a lifetime ago.</>}
        </p>
        <p className="t-aside" style={{ marginTop: "var(--s-3)" }}>
          A dangerously hot day here means above <span className="num">{base.threshold_hot}&nbsp;°C</span> — hotter than
          95% of days were in 1951–80. About <span className="num">{Math.round(then)}</span> a year then;
          about <span className="num">{Math.round(now)}</span> now.
        </p>
        <p className="t-label">
          <a href={`#hot-days`}>#</a> {src.name} · {src.organisation} · {src.licence}
        </p>
      </section>

      <section id="the-record" style={{ marginTop: "var(--s-8)" }}>
        <h2 className="t-label">Every year since 1940</h2>
        <div className={s.chart}>
          {/* the scale is HTML at the 13px floor, never text inside the SVG */}
          <div className={`t-label num ${s.scale}`}>
            <span>1940</span><span>1980</span><span>{m.last_full_year}</span>
          </div>
          <Column rows={rows} max={max}
            label={`${place.name}: days above ${base.threshold_hot}°C each year from 1940 to ${m.last_full_year}. ` +
                   `About ${Math.round(then)} a year in 1951–80, about ${Math.round(now)} in the last ten years.`} />
        </div>
        <p className="t-label"><a href="#the-record">#</a> Bar length is that year&rsquo;s count. {src.citation}</p>
      </section>

      <p className={`t-label ${s.meta}`}>
        Archive complete to {m.archive_end}. This page cannot tell you why the record moved —
        for that, see the attribution studies listed in How we know.
      </p>
    </main>
  );
}
