import Link from "next/link";
import dynamic from "next/dynamic";

// Lazily loaded, client-only: the interactive part must never block the first paint of this or
// any other page. Everything above it is server-rendered and readable without JS.
const Dial = dynamic(() => import("@/components/Dial").then((m) => m.Dial));

export const metadata = { title: "What's left — On Record" };

export default function WhatsLeft() {
  return (
    <main className="wrap">
      <p className="t-label"><Link href="/">On Record</Link></p>
      <h1 className="t-head">What&rsquo;s left</h1>
      <p className="t-lead">
        Two independent teams published a remaining carbon budget for a coin-flip chance at 1.5 °C.
        They land about a week apart.
      </p>

      <section id="budget" style={{ marginTop: "var(--s-8)" }}>
        <div className="t-display num accent">103–105<span className="t-aside"> billion tonnes</span></div>
        <p className="t-body">of CO₂ from now. At today&rsquo;s rate that is about two and a half years of burning —
          not the end of anything, the end of a coin-flip chance of stopping at 1.5 °C.</p>
        <p className="t-label">
          <a href="#budget">#</a> Global Carbon Budget 2025 and IGCC 2025 (Forster et al.) — both shown, never averaged.
        </p>
      </section>

      <hr className="rule" />
      <section id="dial">
        <h2 className="t-label">Change how fast the world burns</h2>
        <Dial />
        <p className="t-label"><a href="#dial">#</a> Held-rate arithmetic, not a pathway model.</p>
      </section>
    </main>
  );
}
