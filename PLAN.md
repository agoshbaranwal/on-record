# On Record — the plan after the first test readers

Status written 2026-08-16, against build `1064cae6`.

## Correction, 2026-08-16 — what "too much going on" meant

I read it as the atmosphere. It is not. **The sky, the sound and the rail are what the test
readers liked — the site's redeeming qualities.** They stay, untouched, in everything below.
"Too much going on" is about CONTENT: too many ideas competing, none landing.

That sharpens one count. Set the sky aside as atmosphere and a reader is still asked to learn
**seven chart grammars** in five minutes — the season ring, the spaghetti record window, the
country lollipop, the 100-person grid, the then/now bars, the impact wedges, the warming
stripes. No caption survives being the seventh new thing a stranger has ever seen.

## The route: three prototypes, tested cold

Chosen 2026-08-16. Not one architecture picked on my taste — three built with the real data,
inside the real sky, handed to strangers. The one that survives gets built properly.

| | Thesis | What a reader gets |
|---|---|---|
| **P1 answer-first** | Your city's answer IS the page | One screen that answers it; everything else opens on demand |
| **P2 five screens** | A story, but finite | 16 screens cut to 5, one idea each, position impossible to misread |
| **P3 report** | Use a form people have read | Masthead, findings, sections, sources — numbers first, prose second |

All three keep the sky, the sound and the rail. Only the content architecture differs, so the
test compares the thing actually in question.

## The one diagnosis

Three readers said different things that are the same thing. The site is built as **an
instrument with chapters**. They came for **an answer to one question**. Every complaint below
falls out of that single mismatch:

| What they said | What it actually is |
|---|---|
| "Couldn't figure out what was going on" | The masthead promises *your city*; chapter 01 is the world's carbon budget |
| "Pages don't connect / can't tell when a topic ends" | Chapters have labels but no openers and no endings |
| "Couldn't understand what I was looking at" | Screens carry graphics that never state the question they answer |
| "Too many pages, some weak" | 16 screens; the inventory found 5 that are filler |
| "Home page weakest" | Fixed in part — a front page now exists — but the order still contradicts it |
| "Pretentious, poetic" | 91 lines replaced; the voice will return unless a check forbids it |

**The bar, from here on:** a screen earns its place only if a stranger can say *what question it
answers* and *what they take away*. If it cannot, it merges or it dies. No exceptions for screens
that took a long time to build.

---

## Step 1 — Reorder the site so it answers its own question

**The change.** Your city first. Order becomes:

1. **Hot days** — your city, then vs now
2. **Hot nights** — the part people miss
3. **Public opinion** — almost everyone wants this
4. **Carbon budget** — why it keeps rising  *(was chapter 01)*
5. **What you can do**
6. **Summary**
7. **Sources**

**Why first.** It is the only change that makes the promise and the page agree. Every other fix
is smaller if this one lands first, and wasted effort if it lands last.

**Concretely:** move the `.pane` elements; update the `CH` array, the no-JS rail copy, the
front-page contents list, `scrollToChamber` indices, the kiosk loop order, and `?embed=<name>`.
Keep the old chapter names as **aliases** so shared links never 404.

**Risk:** medium. The rail, the intro hand-off and the share cards all read chapter indices.
Mitigate with an executable invariant: a build assertion that the rail order, the contents list
and the `CH` array are the same seven ids in the same order.

## Step 2 — One question per screen

**The change.** Every screen's heading becomes the question it answers, and the screen answers
it in one sentence plus one graphic. Not a theme, not a statement — a question a person would ask.

- "Today vs this date since 1940" → three graphics and 180 words under a heading naming only the
  first. Split: *"Is today unusual here?"* (today vs 86 years) and *"When do hot days happen?"*
  (the ring). The unlabelled year chart gets a title or goes.
- Every graphic gets a one-line "what you're looking at" above it, in the same place every time.

**Test that decides it:** show one screen to someone cold. If they cannot state the question,
the screen is wrong — not the caption.

## Step 3 — Merge down to about ten screens

From the inventory, already argued:

- rate slider → into the carbon-budget screen (it is that screen's own readout)
- city picker → into the hot-days bars (a screen of settings promising data it does not show)
- Personal changes → into Take action (same subject, same list, same source line)
- What's improving → into Summary (two facts on a 77%-empty card; the Summary already holds four)
- download footer → into Sources (a footer given a whole screen, so the site just stops)

**16 → 11.** Then re-run the bar from Step 2 on all 11 and expect to lose one more.

## Step 4 — Give every chapter an opening and an ending

**The change.** A reader must always know which chapter they are in, what it will answer, and
that it has ended.

- **Opener:** chapter number + name + the question it answers, at full width, on the sky — not
  inside a card. It should be impossible to miss the boundary.
- **Closer:** the one number to carry out of that chapter, and the next chapter's question.
- The rail keeps position; the openers and closers carry the *sense* of position.

This is the direct answer to "the pages don't connect" and "where did I start and where did I end".

## Step 5 — The front page carries the answer, not just the contents

**The change.** A reader who scrolls no further should still leave with the finding. Put the four
measured numbers on the front page as a preview strip — your hot days then/now, your hot nights,
what people want, years of budget left — each linking to its chapter.

Also: **give the site an ending.** It currently stops on a download list. It should end on what
you now know, one action, and the sources.

## Step 6 — Build the graphics that were only ever mockups

In priority order, each judged by Step 2's bar before any of it is drawn:

1. **Carbon budget** — chapter is still a big number and a slider. Needs the one image that makes
   "102 billion tonnes" mean something: the budget as a bar being spent at 42.2 Gt/yr, with the
   ordinary-thing benchmarks that started this whole idea.
2. **The "is today unusual" screen** — today against 86 versions of the same date, drawn once and
   plainly.
3. **The ridge / volcano chart** — only if it answers a question the ring does not.

**Rule I broke and will not break again:** a mockup is not a deliverable. Nothing is reported as
done until it is in `instrument.html`, built, pushed, and served by the plain URL.

## Step 7 — Lock the voice so the poetry cannot come back

**The change.** A banned-pattern check in `pipeline.py` and `tools/build_offline.py` that **fails
the build**: aphorism shapes ("X is not Y, it is Z"), internal codenames (sky/ground/people/
cohort/instrument/chamber/beat as reader-facing nouns), self-praise ("honest", "every number
shown" about itself), and the house slogan outside its one home.

Three copy passes have been undone by drift. A check is the only thing that has ever held.

## Step 8 — Re-test with strangers, on a protocol

**The change.** A repeatable stranger run, before every ship that touches structure:

1. Fresh profile, no query string, phone width. Let the intro play.
2. Scroll the way a person does; screenshot every scroll.
3. Answer three questions from the screenshots alone: *What is this? What is it telling me? Where
   am I?*
4. Read the heading outline alone. If it does not read like a table of contents, stop.

Then real people again — the same three readers, plus one who has never seen it.

---

## Order and why

Step 1 → 4 → 3 → 2 → 5 → 6 → 7 → 8.

Structure before content: reordering and chapter boundaries change what each screen has to do, so
doing the merges or the graphics first means doing them twice. Step 7 goes in before the last copy
pass so the pass is enforced rather than remembered.

## What this plan deliberately does not do

- **No new features.** Every step removes, reorders or clarifies. The site's problem is not that
  it lacks capability.
- **No visual redesign.** The type, the palette and the cards are not what the readers complained
  about. Changing them would hide whether the structural fixes worked.
- **No new chapters.** Seven is already two too many by the readers' account.
