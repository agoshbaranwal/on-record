import { places, baselines, records, indicators, sources, manifest, multiple } from "@/lib/seed";
import { freshness } from "../../../packages/engine/src/staleness";

export default function Home() {
  const m = manifest(), src = new Map(sources().map((s) => [s.slug, s]));
  const base = new Map(baselines().map((b) => [b.place_slug, b]));
  const byPlace = new Map<string, ReturnType<typeof records>>();
  for (const r of records()) { const a = byPlace.get(r.place_slug) ?? []; a.push(r); byPlace.set(r.place_slug, a); }

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "48px 20px" }}>
      <h1 style={{ fontSize: 30, fontWeight: 600, margin: "0 0 6px" }}>On Record — v2 foundation</h1>
      <p style={{ color: "rgba(242,231,204,.82)", margin: "0 0 28px", fontSize: 15 }}>
        Ingested {m.ingested_at.slice(0, 10)} · archive complete to {m.archive_end} · last full year {m.last_full_year}
      </p>

      {indicators().map((i) => {
        const f = freshness(i.as_of, i.stale_after_days, Date.now());
        const s = src.get(i.source_slug);
        return (
          <section key={i.slug} style={{ marginBottom: 28 }}>
            <div style={{ fontSize: 34, fontWeight: 600 }}>{i.value} <span style={{ fontSize: 16 }}>{i.unit}</span></div>
            <div style={{ fontSize: 14, color: "rgba(242,231,204,.82)" }}>{i.label}</div>
            <div style={{ fontSize: 12, marginTop: 6, color: f.state === "fresh" ? "rgba(242,231,204,.7)" : "#F0BC62" }}>
              {f.state === "fresh" ? `measured ${i.as_of}` : f.note} · {s?.organisation}
            </div>
          </section>
        );
      })}

      <h2 style={{ fontSize: 13, letterSpacing: ".14em", textTransform: "uppercase", color: "rgba(242,231,204,.66)", margin: "34px 0 10px" }}>
        Places ingested
      </h2>
      {places().map((p) => {
        const rows = byPlace.get(p.slug) ?? [], b = base.get(p.slug);
        const { then, now, mult, direction } = multiple(rows, m.last_full_year);
        return (
          <div key={p.slug} style={{ padding: "12px 0", borderTop: "1px solid rgba(242,231,204,.14)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
              <span style={{ fontSize: 17, fontWeight: 600 }}>{p.name}</span>
              <span style={{ fontSize: 19, fontWeight: 600, color: "#F0BC62", fontVariantNumeric: "tabular-nums" }}>
                {mult ? `${(mult >= 1 ? mult : 1 / mult).toFixed(1)}× ${direction}` : "—"}
              </span>
            </div>
            <div style={{ fontSize: 13, color: "rgba(242,231,204,.8)" }}>
              days above {b?.threshold_hot}&nbsp;°C: about {Math.round(then)} a year in 1951–80, about {Math.round(now)} now
            </div>
          </div>
        );
      })}
    </main>
  );
}
