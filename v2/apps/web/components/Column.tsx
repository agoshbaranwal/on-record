/**
 * The record, as one column.
 *
 * 86 rows, 1940 at the top, the last full year at the bottom; bar LENGTH is that year's count of
 * days above the place's own 1951-80 95th percentile. One colour — length carries everything and
 * hue carries nothing, which is the colour-blind fix, the greyscale-screenshot fix and the honesty
 * fix in one: a record that COOLED draws with exactly the same dignity as one that warmed.
 *
 * NO TEXT INSIDE THE SVG. v1 put axis labels in a 940-wide viewBox that scaled into a ~350px
 * column, rendering them at about four pixels — illegible, and invisible to a type audit that only
 * looked at CSS. The scale is HTML beside the chart, at the same 13px floor as everything else.
 *
 * Server-rendered, no client JS, present in the first paint.
 */
export function Column({
  rows, max, label,
}: { rows: { year: number; hot_days: number }[]; max: number; label: string }) {
  const H = 460, W = 170, pitch = H / Math.max(1, rows.length), bar = Math.max(2, pitch - 1.3);
  const scale = (n: number) => (max > 0 ? (n / max) * W : 0);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} role="img" aria-label={label}
         preserveAspectRatio="none" style={{ maxWidth: W, display: "block" }}>
      {rows.map((r, i) => (
        <rect key={r.year} x={0} y={i * pitch} width={Math.max(0.6, scale(r.hot_days))} height={bar}
              fill="var(--c-accent)" opacity={0.9} rx={1} />
      ))}
    </svg>
  );
}
