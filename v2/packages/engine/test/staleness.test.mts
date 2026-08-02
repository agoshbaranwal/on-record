import { test } from "node:test";
import assert from "node:assert/strict";
import { freshness } from "../src/staleness.ts";
const at = (iso: string) => Date.parse(`${iso}T12:00:00Z`);

test("a recent figure is fresh", () => {
  assert.equal(freshness("2026-08-01", 21, at("2026-08-02")).state, "fresh");
});
test("past its window it starts announcing its age", () => {
  // 28 days old against a 21-day window: past it, but not yet past twice it
  const f = freshness("2026-07-05", 21, at("2026-08-02"));
  assert.equal(f.state, "ageing");
  assert.match((f as { note: string }).note, /has not published/);
});
test("well past, it says plainly it is out of date", () => {
  const f = freshness("2026-01-01", 21, at("2026-08-02"));
  assert.equal(f.state, "stale");
  assert.match((f as { note: string }).note, /out of date/);
});
test("a future date is never negative age", () => {
  assert.equal(freshness("2026-09-01", 21, at("2026-08-02")).ageDays, 0);
});
