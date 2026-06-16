---
name: presentation
description: How to build a single-file HTML "deck" — a presentation, slideshow, or multiple-choice test — in the repo's signature titanium / engineering style with a live reactive schematic background, a horizontally-paged slide deck, mouse-reactive chrome, and animated reveals. Use when creating a presentation, slides, a quiz/test, or any paged, navigable full-screen content. Worked examples: martin/money-positioning-presentation-01, martin/chemistry-test-01. Bundled runnable examples: example-presentation.html, example-test.html.
---

# Presentations & tests (titanium deck style)

Both presentations and tests in this repo share one self-contained `index.html`
look: a dark **titanium** surface over an **engineering** background (graph
paper + a live, mouse-reactive **schematic network** on a `<canvas>`), arranged
as a **horizontally paged deck** the user steps through. A test is just a deck
whose middle pages are questions and whose last page is a score.

**Start from the bundled examples** — they are complete, runnable, and already
implement the whole engine:

- [`example-presentation.html`](example-presentation.html) — a 5-slide deck:
  title, an animated SVG flow diagram, stat callouts, "check" bullet cards, and
  a closing line.
- [`example-test.html`](example-test.html) — a 3-question multiple-choice test
  with instant per-question feedback and an animated results ring.

Open them in a browser, then copy the one closest to your goal and replace the
content. The sections below explain the pieces so you can extend them.

## The visual language

- **Dark titanium** — near-black background (`--bg:#080b11`); surfaces (cards,
  nav, nodes) use a metallic blue/grey gradient with a light top edge
  (`border-top-color` lighter than the sides) and a soft drop shadow, giving a
  brushed-metal feel. Accent is a cyan/teal (`--accent:#4fd1e0`).
- **Graph-paper grid** — a fixed full-screen layer built from CSS
  `repeating`/`linear-gradient`s at two scales (fine 26px + bold 130px), faded
  toward the edges with a radial `mask-image`. It scrolls horizontally in sync
  with the slides via a `--gx` `background-position` variable.
- **Radial vignette** — a second fixed layer darkening the corners.
- **Reactive schematic network** — a live `<canvas id="schem">` drawing a
  connected graph of orthogonal "traces" with circle nodes. Hovering near a node
  charges it (a growing halo); moving away fires a bright **pulse** that travels
  the traces and **splits** at intersections. It scrolls with the deck. This is
  a background effect (drawn additively over faint resting traces). Copy the
  `genPoly`/`buildNetwork`/`emit`/`stepPulses`/`updateCharge`/`render`/`frame`
  block from either example verbatim — it is self-contained and content-agnostic.
- **Mouse-reactive chrome** — a `pointermove` handler sets a per-element
  proximity value `--p` (0–1) on every `.reactive` element (nav chevrons,
  progress ticks, optionally cards/buttons); the CSS uses `--p` to scale glow
  and lift as the cursor approaches.
- **Animated reveals** — slide content tagged `.reveal` with a staggered
  `--d` delay fades/translates in when its slide gains `.active`.

## Deck structure & navigation (shared by both)

```html
<div class="bg">
  <div class="bg-grid"></div>
  <canvas class="bg-schem" id="schem"></canvas>
  <div class="bg-vignette"></div>
</div>
<div class="brand">…</div>                <!-- top-left wordmark -->
<div class="counter mono"><b id="curNo">01</b> / <span id="totNo">--</span></div>
<div class="deck" id="deck"></div>        <!-- slides injected here -->
<div class="nav prev reactive hide" id="prev">…chevron…</div>
<div class="nav next reactive" id="next">…chevron…</div>
<div class="progress" id="progress"></div><!-- clickable ticks -->
```

- Slides are `<section class="slide">` in a horizontal flex `.deck`; they are
  usually **built in JS** from a data array (a `SLIDES`/`QUESTIONS` array), which
  becomes the single source of truth.
- `go(i)` sets `deck.style.transform = translateX(-i*100%)`, syncs the grid
  (`--gx = -i*100vw`) and the canvas scroll, toggles `.active`, updates ticks
  and the counter, and hides `prev`/`next` at the ends. Transitions slide in the
  travel direction.
- Navigation: right/left chevrons, a clickable progress-tick bar, keyboard
  (`←` `→`, space, `PageUp`/`PageDown`, `Home`/`End`), and horizontal
  touch-swipe. (A test adds number keys `1`–`4` to pick an answer.)

## Presentation-specific elements

The presentation example demonstrates the element types money-positioning uses:

- **Hero/title slide** — eyebrow, large `h1` with a `.gradtext` accent word,
  `.sub` subtitle, footer attribution.
- **Stat callouts** — a row of metallic `.card`s each with a big number and a
  label, for figures you want to land.
- **"Check" bullet cards** — a list of cards each led by a ✓, for
  benefits/decisions/tradeoffs.
- **Animated SVG diagram** — a small flow of `box` nodes joined by edges whose
  `stroke-dashoffset` animates on slide entry, with a flowing accent dash. The
  example includes a minimal `buildFlow` you can extend (money-positioning's full
  engine adds `db`/`decision`/`config` node shapes and timelines).
- **Closing slide** — restate the one big idea, optionally calling back an
  earlier diagram dimmed behind the text.

Keep on-screen copy concise (the speaker elaborates). Use the deck width: one
idea per slide.

## Test-specific behaviour

The test example demonstrates:

- Questions defined in a `QUESTIONS` array (`topic`, `q`, `options[]`, `answer`
  index, `explain`); the deck = an intro slide + one slide per question + a
  results slide.
- **Instant feedback** — selecting an option **locks** the question (one
  attempt): the correct option turns green with ✓, a wrong pick turns red with
  ✗, the rest dim, and an explanation panel slides in. The progress tick turns
  green once answered.
- **Running score** in a header pill.
- **Results slide** — an animated circular SVG score ring fills to the
  percentage, the number counts up, and a banded verdict/message is shown
  (100 / ≥80 / ≥60 / ≥40 / below). A "Retake" button resets answers, ticks,
  score, and ring.

## Building a new deck

1. Copy `example-presentation.html` (or `example-test.html`) into the new
   project as `index.html`.
2. Keep the whole `<style>` block and the background/engine `<script>` parts as
   they are — they are generic.
3. Replace the content array (`SLIDES` / `QUESTIONS`) and the brand wordmark.
4. Tune accent colors via the `:root` CSS variables only if needed.
5. Document the project's actual content in its README, and link back to this
   skill for the generic style/engine rather than re-describing it.
