# On Record — v5 Master Pipeline (the groundbreaking update)

The single source of truth for the v5 rebuild. Every item traces to the owner's briefs,
the reviewed copy deck (`looks/copy-deck-v5.json`), the design research
(`looks/research-v5.json`), or the utility research (`looks/research-utility-v5.json`).
Rule of the build: plain first, one idea per screen, every claim sourced, every screen
measured for legibility, zero tracking forever.

## Platform decision (owner asked; decided 2026-07-24)
No new third-party services. GitHub Pages (free) + Open-Meteo keyless (per-IP quotas mean
client-side scales with traffic) + Search Console (free, DNS-verified) cover everything.
All "privacy-friendly" analytics refused — they would falsify the zero-tracking claim.
Future scale path, documented not needed yet: buy a custom domain (~$10/yr, the only money
this site should ever cost) and put Cloudflare's free tier in front of Pages if bandwidth
ever demands it. Nothing in this plan depends on any service that could later charge.

---

## Phase 1 — One document, one sky (architecture migration)
- Beats move to the ROOT scroller (research correction: never inner scroll divs).
  Sky canvas `position:fixed; inset:0; height:100lvh` behind everything; beats are
  `100svh` sections (never bare 100vh, never dvh). Delete all wheel-hijack code.
- Snap: `mandatory` + `snap-stop:always` on the root, with guards — any beat taller than
  the viewport (400% zoom, small phones) auto-swaps the page to `proximity`; Bedrock is
  a free-scrolling archive, unsnapped. Scrollbar stays visible; `scrollbar-gutter:stable`.
- Chamber transitions fire on IntersectionObserver (threshold .5) as timed 800–1200 ms
  eases — never scroll-scrubbed. Reduced motion: ≤200 ms crossfade.
- URL layer lands here because everything later depends on it:
  `#chapter` anchor ids, `?city=slug&lat&lon`, `?rate=`, and mode flags
  `?embed=`, `?kiosk=`, `?legibility`, `?ogcard`.
- The rail becomes real anchor links: numbered chapters 01–06, name + live fact,
  beat-progress ticks under the active chapter, "02 / 06" counter near the title,
  ≥44 px targets. First-visit scroll cue (chevron + "Scroll") that dies on first scroll.

## Phase 2 — The cinematography layer (readability + film, one system)
- Grade stack in the researched order (all constants in `looks/research-v5.json` → grade):
  scene-linear headroom → halation + glare on genuine light sources only (the 100 lamps'
  glow split into the two physical terms — the site's most cinematic moment) →
  cos⁴ vignette × **text-column darkening falloff, pre-curve, in linear** (sdRoundRect
  uniforms per text column; feather ≥1.5× heading size; +15% desat inside; depth per
  chapter: day .73 / afternoon .55 / morning .5 / night .3) → Hable curve retuned
  (A .22, B .30, C .10, D .20, E .025, F .30; EB 1.6; W 5.0) → luminance-preserving
  desaturation (.93–.97 base, highlights .70–.80 path-to-white) → faded floor
  lift (.018,.022,.030) + pow 1.06 → gamma + IGN dither. Constants are global; chapters
  vary only exposure (±1 stop), white balance, halation strength. Dev panel, then freeze.
- Type floor (broadcast standard): body ≥18 px mobile / 20 px desktop, weight ≥450;
  headings clamp(2rem, 6vh, 4rem); nothing bare on sky below 16 px. Halos stay as
  stacked em-based shadows (secondary layer). UI components (dial, unlit lamps, dots)
  ≥3:1 against both dial-extreme skies (WCAG 1.4.11).
- `prefers-contrast: more` → deeper scrim + solid backplates; `forced-colors` →
  Canvas backplates (declared last); reduced-motion tiers.
- GATE: `looks/contrast_check.py` + the `?legibility` harness — text-hidden/shown
  screenshot pairs across 6 chapters × rates {8, 63} × 3 shader times × 2 widths;
  worst-pixel WCAG 4.5:1 body / 3:1 large AND APCA |Lc| ≥75/60, halo assumed absent.
  Current baseline: every home-page region FAILS. v5 ships green.

## Phase 3 — Chambers in beats (copy deck drives every word)
Per chamber 2–4 beats, ≤4 elements per beat, Pudding rule: write the takeaway sentence
first, delete everything on that screen that does not serve it.
- SKY: thesis (injected Gt figure) + years hero + felt-unit line ("~1,331 tonnes every
  second · 42 billion a year" — always paired) → dial beat: notches (today 42 labeled,
  1.5 °C-consistent, historical peak), three futures, <300 ms consequence, one-time
  ghost-drag self-demo, verdict WITH efficacy clause ("…the sky you should fear.
  Drag left: at 8 Gt this century arrives ~2 °C cooler.") → the IS-IT-TOO-LATE readout
  (the audience's #1 measured question, answered from the dial's own math) → bridge.
  Colour-legend chip ("what is this colour?") bottom corner, states normalization.
- GROUND (built; upgrade): today-line slot (Phase 8 engine), personal payoff sentence
  ("hottest day on record: X °C, date — records set since 2020: N of the top 10"),
  birth-year anchor ("across your lifetime here, summers warmed by +X °C"),
  micro-efficacy line, how-we-know note, vivid year-trace.
- NIGHT: hero "+16 more hot nights — two extra weeks a year" → tonight's risk plainly
  (WHO-framed sleep/health line + vetted protective links) → the days-fell honesty beat
  ("we draw the falling line too; that is why you can trust the rising one").
  Astronomy = silent backdrop + one quiet line, nothing more. Micro-efficacy line
  (Ahmedabad Heat Action Plan, ~1,100+ avoided deaths/yr, Hess 2018). Validation
  sentence at the pivot to First Light.
- FIRST LIGHT: guess-first slider ON the lamp row (inviting, skippable, never gating —
  the evidence-validated mechanism) → dawn sweep → three markers (your guess, their
  guess, the truth) → lamps rebuilt to read as LAMPS (warm gradient, glow, halation) →
  gap auto-localized to the visitor's country once a city is chosen → universality line
  (US 66–80 real vs 37–43 guessed) → giving as a readable list with efficacy labels
  ("~$1–10 per expected tonne — expected impact, not offsets").
- MORNING: measured good news with date stamps and named human causes ("Still unsafe.
  Also falling." register) → the conversation kit: copyable script from your city +
  your country's numbers, with the Goldberg PNAS receipt → share button names your city.
- BEDROCK: unsnapped archive. Deck opening ("A claim you cannot check is an opinion.")
  → curated catalogue → how-we-know hub → CC-BY-4.0 declaration on all computed outputs
  → the falsifiable privacy line ("Zero tracking — verifiably. Open your browser's
  network tab…") → quiet Climate Psychology Alliance signpost → limitations.
- Masthead everywhere → wordmark + chapter marker only; the budget tagline lives on
  Sky and the intro. Bridges between all chapters from the deck.

## Phase 4 — The menace physics (the sky can cite its sources)
- One uniform `uTau` (aerosol optical depth): per-channel extinction (blue dies 1.6×
  faster), three-regime sun (white→ochre→red→gone above τ≈3, bloom dying, aureole
  growing), three-regime sky blend, gradient FLATTENING with τ (the eeriest real cue),
  Beer–Powder cloud decks (3 fbm layers, velocity parallax, bruised undersides from the
  math), light shafts lit by the transmitted sun colour that die when the beam does.
- HONESTY RULE: the dial never claims CO₂ colours air. Dial → frequency language
  ("at this rate, more seasons like 2020"); τ is driven by a labeled fire-day moment
  with the researched copy pattern + citations (Abatzoglou & Williams 2016; Burke 2023;
  Childs 2022) in Bedrock.
- The thin persistent budget band rides the top of every chapter with its years tick —
  the clock visibly follows you through the whole story.

## Phase 5 — The intro cold-open
Four plain beats from the deck (budget → spent ~2029 → 1.5 °C is a gradient → how this
site works), type materializing over the forming sky, skippable in one tap, reopenable
via a "What is this?" affordance. Optional 60-second "play the story" auto-mode.

## Phase 6 — The artifact layer (things that leave the site)
Per-city evidence card (canvas PNG 1200×630 + 1080×1920 story format, Web Share + download);
conversation card; cite-this button (ready-to-paste sentence + permalink); CSV download
with provenance headers; print stylesheet one-pager; screenshot self-sufficiency pass
(every stat card self-attributes inside its own crop); share staleness fix (rebuilds on
place change, deep-links `?city=`); OG: nightly-baked `?ogcard` frame, full meta block,
per-city stub pages for top cities (rename file on redesign — 7-day caches).

## Phase 7 — The action layer (arming the Willing-but-never-asked)
Impact-honest action menu (civic → vote → talk → give → lifestyle, magnitude bars,
Wynes & Nicholas caveats, the crowding-out disclosure line); "put it on the record"
letter builder (your city's computed numbers → a mailto draft to your representative —
never auto-sent; official directory links); plan card + .ics commitment file with
fresh-start default dates; PRIVATE pledge in localStorage replayed on return (never
public badges); optional skippable SASSY tuner reordering the menu (license check first);
donation routes with response-efficacy labels.

## Phase 8 — The return layer (days worth returning, no server)
Client-side notability engine on the chosen city: record broken / record within 1 °C
today / ≥p95 day / warm night / streaks & seasonal firsts / record anniversaries →
one calm today-line + `document.title` ● prefix; ordinary days say so ("An ordinary day
by the record.") — the honesty that makes loud days credible. "Since you were last
here" diff (budget burned, records missed, new good news). Nightly Action emits
`feed.xml` + `on-record.ics`; per-city calendar built in the browser. PWA manifest +
service worker (offline shows last data with an "as of" stamp) + the plain line:
"This site cannot and will not send notifications." Notable-day share card.

## Phase 9 — Reuse & honest measurement
`/reuse.html` (teachers + press: method in plain words, embeds, cite formats, license,
worksheet); `?embed=record` chrome-less iframe + copyable snippet; `?kiosk=1` auto-cycling
projector mode; nightly `impact.json` (repo stars, Search Console clicks via API,
Wayback count, donation platforms' public totals — outcome-side measurement only) +
a "What we can honestly know" page; Search Console DNS verification; consent-by-action
feedback strip (buttons that only open a prefilled mailto/GitHub issue — "nothing is
sent unless you press send").

## Phase 10 — Hardening & ship
Perf kit: 256² RG noise texture replaces hash-noise (biggest mobile win), DPR caps
2 desktop / 1.5 coarse, fbm octave tiers 5→3, 10-frame load probe → device tier, EMA
frame-time adaptive resolution (1 → .85 → .7 → .5), `failIfMajorPerformanceCaveat` →
static-image fallback, `mod(uT,300)`. Kill-list sweep (every element: keep / merge /
drawer / delete — odometer merges into ticker, duplicate horizon labels merge, copy-sky
merges into the share card). Beat deep links. Full a11y pass (focus order, 400% zoom,
keyboard matrix, aria on live regions). Mobile beat pass. The full legibility matrix,
green. Hindi is the first post-v5 milestone.

## Standing gates on every phase
`node --check` on the built script · `contrast_check.py` on probe captures ·
transition-frozen probe screenshots reviewed before commit · live-URL verification
after push · per-phase commits with honest messages.
