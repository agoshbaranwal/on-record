/**
 * Schema invariants — the honesty charter, as CI.
 * These assert the DATABASE cannot represent a dishonest state, rather than trusting discipline.
 */
import { readFileSync } from "node:fs";
const s = readFileSync(new URL("../supabase/migrations/0001_foundation.sql", import.meta.url), "utf8");
// strip SQL comments first: a rule must be checked against the CODE, not the prose explaining it
const code = s.replace(/--[^\n]*/g, "");
const enumOf = (n) => (code.match(new RegExp(`create type ${n} as enum \\(([^)]*)\\)`)) || [, ""])[1];

const checks = {
  "AI imagery is unrepresentable (no enum value for it)":
    !/generated|ai_|synthetic/i.test(enumOf("image_origin")) && enumOf("image_origin").includes("photograph"),
  "an image may only assert causation with a study attached":
    /evidentiary_requires_study[\s\S]*?attribution_study_id is not null/.test(code),
  "a claim cannot exist without a source":
    /create table claims[\s\S]*?source_id\s+uuid not null references sources/.test(code),
  "an image cannot exist without a source":
    /create table images[\s\S]*?source_id\s+uuid not null references sources/.test(code),
  "image provenance is mandatory":
    ["photographer", "captured_on", "location", "licence", "credit", "caption"]
      .every((f) => new RegExp(`${f}\\s+\\w+(\\(\\d+\\))?\\s+not null`).test(code)),
  "nothing publishes without a named reviewer": /published_needs_reviewer/.test(code),
  "every indicator declares when it goes stale": /as_of\s+date not null/.test(code) && /stale_after_days/.test(code),
  "a repeat pair must have its partner": /repeat_pair_needs_partner/.test(code),
  "claims are anchored, so figures are citable": /unique \(article_id, anchor\)/.test(code),
  "coordinates are range-checked": /lat between -89 and 89/.test(code) && /lon between -180 and 180/.test(code),
};
let ok = true;
for (const [k, v] of Object.entries(checks)) { console.log(`  ${v ? "✓" : "✗"} ${k}`); ok &&= v; }
console.log(ok ? "\n  SCHEMA INVARIANTS PASS" : "\n  *** SCHEMA INVARIANTS FAILED ***");
process.exit(ok ? 0 : 1);
