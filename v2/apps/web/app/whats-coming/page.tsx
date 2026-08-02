import Link from "next/link";
import { warmingAt, formatRange, band, TCRE } from "@/lib/projection";

export const metadata = { title: "What's coming — On Record" };

export default function WhatsComing() {
  const RATE = 42.2;
  const horizons = [
    { years: 25, label: "in 25 years" },
    { years: 50, label: "in 50 years" },
    { years: 74, label: "by 2100" },
  ];
  return (
    <main className="wrap">
      <p className="t-label"><Link href="/">On Record</Link></p>
      <h1 className="t-head">What&rsquo;s coming</h1>
      <p className="t-lead">
        If the world keeps burning at today&rsquo;s rate. This is arithmetic, not a forecast — and it is
        given as a range because the science gives a range.
      </p>

      {horizons.map((h) => {
        const r = warmingAt(h.years, RATE);
        return (
          <section key={h.years} id={`h-${h.years}`} style={{ marginTop: "var(--s-8)" }}>
            <p className="t-label">{h.label}</p>
            <div className="t-display num accent">{r.low}–{r.high}<span className="t-aside"> °C</span></div>
            <p className="t-body">{band(r)}</p>
            <p className="t-label">
              <a href={`#h-${h.years}`}>#</a> {r.interval} · {r.basis}
            </p>
          </section>
        );
      })}

      <hr className="rule" />
      <div className="stack">
        <p className="t-body"><strong>What this page cannot tell you.</strong> It cannot tell you how many hot days
          your own city will have in 2050. That needs a downscaled projection dataset, which this site does not
          carry — so it does not guess.</p>
        <p className="t-aside">
          The figures above hold today&rsquo;s emission rate constant and multiply by the transient climate response
          to cumulative emissions ({TCRE.low}–{TCRE.high} °C per 1000&nbsp;Gt, {TCRE.interval}, IPCC AR6). Holding the
          rate constant is an assumption, and it is stated rather than buried.
        </p>
      </div>
    </main>
  );
}
