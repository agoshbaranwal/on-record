import Link from "next/link";
import { pairs } from "@/lib/media";
import { creditLine } from "@/lib/images";
import s from "../place.module.css";

export const metadata = { title: "Why it matters — On Record" };

export default function WhyItMatters() {
  const [pair] = pairs();
  return (
    <main className="wrap">
      <p className="t-label"><Link href="/">On Record</Link></p>
      <h1 className="t-head">Why it matters</h1>
      <p className="t-lead">Heat is not only uncomfortable. It is measurable in hospitals, in harvests and in wages.</p>

      <section id="seen" style={{ marginTop: "var(--s-8)" }}>
        <h2 className="t-label">What it looks like</h2>
        <div className={s.chart} style={{ gridTemplateColumns: "1fr 1fr", marginTop: "var(--s-3)" }}>
          {[pair.before, pair.after].map((img) => (
            <figure key={img.id} style={{ margin: 0 }}>
              <div style={{ aspectRatio: "4 / 3", background: "var(--c-surface)", borderRadius: 4 }} />
              <figcaption className="t-label" style={{ marginTop: "var(--s-2)" }}>{img.caption}</figcaption>
              <p className="t-label">{creditLine(img)}</p>
            </figure>
          ))}
        </div>
        <p className="t-aside" style={{ marginTop: "var(--s-3)" }}>
          The same viewpoint, sixty-three years apart. Nothing here is asserted — the two frames are the argument,
          and both are public-domain photographs with named photographers and dates.
        </p>
        <p className="t-label"><a href="#seen">#</a> Repeat photography, NSIDC and USGS.</p>
      </section>

      <hr className="rule" />
      <div className="stack">
        <p className="t-body"><strong>Nights are the danger people miss.</strong> A body recovers from heat overnight.
          When nights stop cooling, a hot spell stops giving anyone a break — which is what heat-health research
          warns about most.</p>
        <p className="t-body"><strong>We report the record, not the cause.</strong> Whether a particular summer was
          made likelier by climate change is a question for a published attribution study, and we link to those
          rather than answering it ourselves.</p>
      </div>
    </main>
  );
}
