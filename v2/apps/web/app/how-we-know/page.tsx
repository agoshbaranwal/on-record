import Link from "next/link";
import { sources, manifest, places } from "@/lib/seed";
import s from "../place.module.css";

export const metadata = { title: "How we know — On Record" };

export default function HowWeKnow() {
  const m = manifest();
  return (
    <main className="wrap">
      <p className="t-label"><Link href="/">On Record</Link></p>
      <h1 className="t-head">How we know</h1>
      <p className="t-lead">Every figure on this site resolves to one of these, and every figure has a link you can cite.</p>

      <hr className="rule" />
      <h2 className="t-label">Sources</h2>
      {sources().map((x) => (
        <div key={x.slug} id={`source-${x.slug}`} className={s.row}>
          <div className={s.rowTop}>
            <span className="t-body">{x.name}</span>
            <a className="t-label" href={`#source-${x.slug}`} aria-label={`Permalink to ${x.name}`}>#</a>
          </div>
          <p className="t-aside">{x.organisation}</p>
          <p className="t-label">{x.citation}</p>
          <p className="t-label">{x.licence} · <a href={x.url} rel="noopener">{x.url}</a></p>
        </div>
      ))}

      <hr className="rule" />
      <h2 className="t-label">What this page cannot tell you</h2>
      <div className="stack" style={{ marginTop: "var(--s-3)" }}>
        <p className="t-body"><strong>The grid is coarse.</strong> ERA5 averages over about 30&nbsp;km, so it smooths
          valley heat. These are reconstructed records, not a thermometer on your street.</p>
        <p className="t-body"><strong>We show the record, not the cause.</strong> Nothing here says a particular day or
          year was caused by climate change. For that, published attribution studies are the only honest answer.</p>
        <p className="t-body"><strong>A place that cooled is shown as cooled.</strong> Of the places on record here,
          some went down. They are drawn exactly like the ones that went up.</p>
      </div>

      <hr className="rule" />
      <h2 className="t-label">Places on record</h2>
      <p className="t-aside">{places().length} places · archive complete to {m.archive_end} · built {m.ingested_at.slice(0, 10)}</p>
    </main>
  );
}
