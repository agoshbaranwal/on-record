"use client";
/**
 * The dial — v1's single best interaction, and the only place the sky earns its cost.
 *
 * In v1 the WebGL atmosphere was the site's chrome: it ran behind all six chambers and cost about
 * two seconds of dead screen on a phone before anything painted, at the worst possible moment.
 * Here it lives on ONE route and is loaded lazily, so every other page paints server-rendered in
 * the first frame and this one costs what it is worth.
 *
 * The answer is a RANGE, always. v1 printed "2100 arrives about 2.8 °C hotter" — a single figure
 * where the science gives 2.2–3.3, which is the most respectable-looking overclaim it made.
 */
import { useState } from "react";
import { warmingAt, formatRange, band } from "@/lib/projection";

const MIN = 8, MAX = 63, NOW = 42.2;

export function Dial() {
  const [rate, setRate] = useState(NOW);
  const r = warmingAt(74, rate);
  const atToday = Math.abs(rate - NOW) < 0.5;
  return (
    <div>
      <label className="t-label" htmlFor="rate">
        The world burns about <span className="num">{rate.toFixed(1)}</span> billion tonnes of CO₂ a year.
        Move it.
      </label>
      <input id="rate" type="range" min={MIN} max={MAX} step={0.1} value={rate}
             onChange={(e) => setRate(Number(e.target.value))}
             style={{ width: "100%", marginTop: "var(--s-3)", accentColor: "var(--c-accent)" }} />
      <div className="t-label" style={{ display: "flex", justifyContent: "space-between" }}>
        <span>{MIN} · deep cuts</span><span>{MAX} · half again</span>
      </div>

      <div style={{ marginTop: "var(--s-6)" }}>
        <div className="t-display num accent">{r.low}–{r.high}<span className="t-aside"> °C</span></div>
        <p className="t-body">by 2100 {atToday ? "at today's rate" : "at the rate you have set"}. {band(r)}</p>
        <p className="t-label">{r.interval} · {r.basis}</p>
      </div>
    </div>
  );
}
