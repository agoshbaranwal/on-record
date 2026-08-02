import Link from "next/link";
export const metadata = { title: "What we collect — On Record" };

/**
 * The retraction. v1 promised on the page: "We do not know you are here. There is no analytics
 * script on this page, no pixel, no beacon, no cookie set for us to read." A server makes that
 * false, so it is withdrawn in public, dated, with the old wording still readable — never quietly
 * deleted, which is the only version of this that would actually damage trust.
 */
export default function Privacy() {
  return (
    <main className="wrap">
      <p className="t-label"><Link href="/">On Record</Link></p>
      <h1 className="t-head">What we collect</h1>

      <section id="retraction" style={{ marginTop: "var(--s-6)" }} className="stack">
        <p className="t-body"><strong>What changed, and when.</strong> Until August 2026 this site said:
          <em> &ldquo;We do not know you are here. There is no analytics script on this page, no pixel, no beacon,
          no cookie set for us to read.&rdquo;</em> That is no longer true. We are not deleting it quietly.</p>
        <p className="t-body"><strong>What we now collect.</strong> Page views, which pages, and the country your
          request came from. No cookies. No cross-site tracking. No profile of you. Nothing sold or shared.</p>
        <p className="t-body"><strong>Your location.</strong> If you allow it, your coordinates are rounded to about
          a kilometre. Your city is still named <em>on your own device</em> from a downloaded list — your position is
          not sent to us to be identified.</p>
        <p className="t-body"><strong>Advertising.</strong> None today. If it arrives it will be labelled, served from
          this domain, and will not be targeted using anything we know about you.</p>
        <p className="t-label"><a href="#retraction">#</a> Every change to this statement is dated and kept below.</p>
      </section>
    </main>
  );
}
