/**
 * The causation test.
 *
 * The whole point of putting photographs on a climate site is that they make a reader feel
 * something a number cannot. The whole risk is that a photograph asserts a cause the data does not
 * support. This test is the line between the two, and it runs on every build.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const src = readFileSync(join(ROOT, "apps/web/lib/images.ts"), "utf8");
const media = readFileSync(join(ROOT, "apps/web/lib/media.ts"), "utf8");
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/[^\n]*/g, "$1");

let ok = true;
const say = (p, m) => { console.log(`  ${p ? "✓" : "✗"} ${m}`); ok &&= p; };

say(!/"generated"|'generated'/.test(code(src).match(/type ImageOrigin[^;]*/)?.[0] ?? ""),
  "AI imagery is unrepresentable — no 'generated' member of ImageOrigin");
say(/mode: "evidentiary";[\s\S]*?study: \{/.test(src),
  "an evidentiary image cannot compile without a study attached");
say(/CAUSAL_TERMS/.test(src) && /captionProblem/.test(src),
  "illustrative captions are screened for causal verbs");

// every shipped image must survive its own rule
const ids = [...media.matchAll(/id:\s*"([^"]+)"/g)].map((m) => m[1]);
const captions = [...media.matchAll(/caption:\s*"([^"]+)"/g)].map((m) => m[1]);
const modes = [...media.matchAll(/mode:\s*"([^"]+)"/g)].map((m) => m[1]);
const CAUSAL = ["caused by", "because of", "due to climate", "climate change caused",
  "driven by climate", "a result of climate", "proof of climate", "shows climate change"];
const bad = captions.filter((c, i) => modes[i] === "illustrative" && CAUSAL.some((t) => c.toLowerCase().includes(t)));
say(bad.length === 0, `no illustrative caption asserts causation${bad.length ? ": " + bad.join(" / ") : ""}`);
say(captions.every((c) => /\d{4}/.test(c)), "every caption states a year");
say(ids.length > 0 && ["photographer", "capturedOn", "location", "licence", "credit"]
  .every((f) => (media.match(new RegExp(`${f}:`, "g")) ?? []).length >= ids.length),
  "every image carries full provenance");

console.log(ok ? "\n  IMAGE INVARIANTS PASS" : "\n  *** IMAGE INVARIANTS FAILED ***");
process.exit(ok ? 0 : 1);
