import Link from "next/link";
export const metadata = { title: "What's working — On Record" };

export default function WhatsWorking() {
  return (
    <main className="wrap">
      <p className="t-label"><Link href="/">On Record</Link></p>
      <h1 className="t-head">What&rsquo;s working</h1>
      <p className="t-lead">Not a promise — a list of what has already moved. Each sourced, each still short of safe.</p>

      <section id="renewables" style={{ marginTop: "var(--s-8)" }}>
        <div className="t-display num accent">33.8%</div>
        <p className="t-body">of the world&rsquo;s electricity came from renewables in 2025 — passing coal for the first time.</p>
        <p className="t-label"><a href="#renewables">#</a> Ember, Global Electricity Review 2026 · CC BY 4.0</p>
      </section>

      <section id="expected-warming" style={{ marginTop: "var(--s-8)" }}>
        <div className="t-display num accent">3.6 → 2.6</div>
        <p className="t-body">°C of expected warming under current policies, 2015 compared with now. Still far from safe — and moving the right way.</p>
        <p className="t-label"><a href="#expected-warming">#</a> Climate Action Tracker</p>
      </section>

      <hr className="rule" />
      <p className="t-aside">The biggest levers are collective — a vote, a voice, where money goes. Personal cuts are
        real and smaller, and saying so is not giving up; hiding it turns out to be both the dishonest move and the
        less effective one.</p>
    </main>
  );
}
