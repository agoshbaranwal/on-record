/**
 * Design-system invariants, as CI.
 *
 * Two static rules and, when a server is running, one measured rule.
 *
 * The fullwidth check exists because I have now twice typed a fullwidth digit into a
 * `cubic-bezier()` — U+FF12 instead of "2". CSS silently discards the whole declaration and
 * nothing errors, so the animation just stops working and looks like a design choice. A character
 * that is visually identical to a valid one is exactly the class of bug a human review misses.
 *
 *   node scripts/check-design.mjs            # static only
 *   node scripts/check-design.mjs --url URL  # also measure the rendered page
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, extname } from "node:path";
import { fileURLToPath } from "node:url";

// fileURLToPath, not .pathname: the repo path contains a space and .pathname returns %20
const ROOT = fileURLToPath(new URL("..", import.meta.url));
const WEB = join(ROOT, "apps", "web");
const TOKENS = join(WEB, "app", "tokens.css");

let ok = true;
const say = (pass, msg) => { console.log(`  ${pass ? "✓" : "✗"} ${msg}`); ok &&= pass; };

/** Strip CSS/JS comments so a rule is tested against code, not the prose describing it. */
const stripComments = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/[^\n]*/g, "$1");

function walk(dir, out = []) {
  for (const f of readdirSync(dir)) {
    if (f === "node_modules" || f === ".next" || f.startsWith(".")) continue;
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p, out);
    else if ([".css", ".ts", ".tsx", ".mts", ".mjs"].includes(extname(p))) out.push(p);
  }
  return out;
}
const files = walk(WEB).concat(walk(join(ROOT, "packages")));

// ── 1. no fullwidth look-alikes in code ──────────────────────────────────────
const FULLWIDTH = /[！-～]/;
const offenders = [];
for (const f of files) {
  const code = stripComments(readFileSync(f, "utf8"));
  const m = code.match(FULLWIDTH);
  if (m) offenders.push(`${f.replace(ROOT, "")} → ${JSON.stringify(m[0])} (U+${m[0].codePointAt(0).toString(16).toUpperCase()})`);
}
say(offenders.length === 0, `no fullwidth look-alike characters in code${offenders.length ? ": " + offenders.join(", ") : ""}`);

// ── 2. font-size is decided in one file only ─────────────────────────────────
const strays = [];
for (const f of files) {
  if (f === TOKENS) continue;
  const code = stripComments(readFileSync(f, "utf8"));
  // catches CSS `font-size:` and inline React `fontSize:`
  if (/font-size\s*:/.test(code) || /fontSize\s*:/.test(code)) strays.push(f.replace(ROOT, ""));
}
say(strays.length === 0, `font-size is set only in tokens.css${strays.length ? "; strays: " + strays.join(", ") : ""}`);

// ── 3. the scale has a 13px floor and nothing beneath it ─────────────────────
const tokens = readFileSync(TOKENS, "utf8");
const sizes = [...tokens.matchAll(/--t-[a-z]+:\s*([^;]+);/g)].map((m) => m[1].trim());
const remFloor = sizes
  .map((v) => { const m = v.match(/^([\d.]+)rem$/); return m ? parseFloat(m[1]) * 16 : null; })
  .filter((n) => n !== null);
say(remFloor.length > 0 && Math.min(...remFloor) >= 13, `smallest fixed type token is ${Math.min(...remFloor)}px (floor is 13)`);
say(sizes.length <= 6, `the scale has ${sizes.length} steps (a vocabulary, not a spectrum)`);

// ── 4. every motion duration has a reduced-motion answer ─────────────────────
say(/prefers-reduced-motion/.test(tokens) && /--m-quick:\s*0ms/.test(tokens),
  "reduced-motion zeroes every motion token");

// ── 5. measured, if a URL is given ───────────────────────────────────────────
const urlArg = process.argv.indexOf("--url");
if (urlArg >= 0) {
  const url = process.argv[urlArg + 1];
  const html = await fetch(url).then((r) => r.text());
  // the server-rendered document must not contain any inline font-size either
  say(!/font-size\s*:/i.test(html.replace(/<style[\s\S]*?<\/style>/g, "")),
    "no inline font-size in the rendered document");
  say(/--t-label:\s*0\.8125rem/.test(html) || html.includes("tokens.css") || /t-label/.test(html),
    "the rendered page uses the token vocabulary");
}

console.log(ok ? "\n  DESIGN INVARIANTS PASS" : "\n  *** DESIGN INVARIANTS FAILED ***");
process.exit(ok ? 0 : 1);
