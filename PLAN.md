# On Record — shipping P1

Decision, 2026-09-01: **P1 (answer-first) is the architecture.** Your city's number and the
season ring are the first screen; the other six chapters are questions you tap open.

Live site: build `20260901075146`. P1 lives only at `prototypes/p1.html`.

---

## The one thing to understand first

The site is **generated**. `instrument.html` is the template; a build script turns it into
`index.html`, and a job re-runs that every night. P1 was built by editing `index.html` — the
generated file, not the template.

So P1 as it stands would be erased by tonight's build. Nothing else on this plan can ship until
that is fixed. That is Phase 0, and it is a gate, not a step.

---

## Phase 0 — Put P1 into the template  ·  the gate

Re-apply P1's changes to `instrument.html` so the build produces them:
- the answer screen (headline + then/now bars + season ring in one card)
- the six disclosure rows, built at runtime, each labelled "Chapter N of 7"
- the summary numbers moved into the row previews
- the contents page and the separate Summary chapter removed
- the rail driven by which row is open

**Done when:** running the build produces a file that matches `prototypes/p1.html` in structure,
the sky/sound/rail still work, there are no JS errors, and a nightly run leaves it intact.

## Phase 1 — Three defects that are wrong on the live site today

These are P1's top three blockers AND live-site problems. They are the only items here that are
about honesty rather than polish.

1. **"Hot days" means two different things in the largest type on the page.** Seville and Delhi
   use an absolute 35 °C. London uses 22.6 °C, Reykjavik 14.8 °C — each city's own 95th
   percentile. The headline says "hot days" for all of them. Fix: the headline says what it
   measured, per city.
2. **The compare chart draws two cities on one shared axis** while its own caption says each
   city has a different threshold, so the comparison the picture makes is one the caption
   retracts. Fix: draw the multiple (2.5x, 6.7x) — the number that IS comparable — not the raw
   counts on a shared scale.
3. **The world outranks your city.** "2.4–2.5" is about four times larger than any number about
   the reader, and the only thing you can play with — the emissions slider — belongs to the
   world. Asked what they took away, the reader said the budget number, not their own city.
   Fix: your city gets the biggest number and the interaction.

## Phase 2 — The rest of P1's blocker list

4. **One "now" per card.** Chapter 1 shows "2016–2025" in the bars, "the last 10 years" in the
   headline, and "1996–2025" in the ring — three labels, two periods, one card.
5. **Chart labels collide.** At 1280px "hot days — climbing" and "hot nights — climbing" print on
   the same pixels; on a phone both vanish and leave two unlabelled coloured lines.
6. **The rail lies.** Scrolled deep into the questions it still reads "01/07 YOUR CITY", the
   landing screen has no rail at all, and nothing says how long the page is.
7. **The phone's sound button is an unlabelled circle**, and the phone has no permanent
   "Set your city" control at all.
8. **The phone chapter strip cuts off mid-word** ("03 OTHER CIT") with nothing showing it scrolls.
9. **Copy that explains the product**: "set your city and this becomes yours", "The band is that
   gap, drawn to scale", "OR SCROLL FOR AN EXAMPLE".
10. **The count-up animation shows numbers that were never true** — 0.3s after choosing London it
    read "15 → 14" before settling on "19 → 47", showing the trend going the wrong way.
11. **A teaser quotes the wrong number**: the header promises "89% want government action" while
    the chapter asks about giving 1% of income.

## Phase 3 — Left over from the earlier audit, still true

- Printing gives 19 pages, 13 of them blank.
- The kiosk loop can never reach the season ring.
- `?embed` shows the site's chrome, which `reuse.html` promises it will not.
- The ring's month ticks are below the 3:1 contrast floor for graphics.
- The ring block has no heading, so heading-navigation skips it.
- 29 February folds onto 28 February, so that one spoke draws from 38 chances in a "30-year"
  era. Tiny, but it should be said out loud or fixed.

## Phase 4 — Prove it, then ship

1. Three **fresh** readers, one version each, on their own phones. The original testers have
   spent their comprehension — they cannot be surprised twice.
2. Ask six questions, then message them ten minutes later and ask what they remember.
   Unprompted recall is the real score.
3. Ship to the plain URL, confirm the plain URL serves it, then delete `/prototypes/`.

---

## Order, and why

Phase 0 first, because nothing survives the night without it. Then Phase 1, because those three
are wrong on the live site right now and they suppressed every prototype score. Then 2, then 4.
Phase 3 can ride along or wait — none of it is on a path a reader takes by accident.

## What is not in this plan

The carbon-budget graphic and the ridge chart. P1 puts the budget behind a tap, so a new graphic
for it is lower value than it was when it opened the site. Revisit after Phase 4.
