---
name: presentation
description: How to build a single-file HTML "deck" — a presentation, slideshow, or multiple-choice test — in the repo's signature titanium / engineering style with a live reactive schematic background, a horizontally-paged slide deck, mouse-reactive chrome, animated reveals, a mobile-friendly footer nav, and an optional shared leaderboard. Use when creating a presentation, slides, a quiz/test, or any paged, navigable full-screen content. Worked examples: martin/money-positioning-presentation-01, martin/chemistry-test-01, martin/earth-science-01 (test with a shared leaderboard). Bundled runnable examples: example-presentation.html, example-test.html.
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
<header class="topbar">                     <!-- fixed top: wordmark + counter (+ score pill on a test) -->
  <div class="brand">…wordmark…</div>
  <div class="hud mono">
    <span class="counter"><b id="curNo">01</b> / <span id="totNo">--</span></span>
    <span class="scorepill empty" id="scorePill"></span>  <!-- tests only -->
  </div>
</header>
<div class="deck" id="deck"></div>          <!-- slides injected here -->
<div class="bottombar"></div>               <!-- fixed footer strip; only visible on mobile -->
<div class="nav prev reactive hide" id="prev">…chevron…</div>
<div class="nav next reactive" id="next">…chevron…</div>
<div class="progress" id="progress"></div>  <!-- clickable, equal-length ticks -->
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
- **Equal-length page indicators** — every `.tick` is the same fixed width; the
  active tick (`.tick.on`) is shown by colour and glow only, **never** by growing
  wider. (On a test, an answered tick also tints green.) Don't reintroduce a
  width change on `.tick.on`.

### Mobile / cell-phone layout

The chrome is built so the nav collapses into a **footer** on a phone, leaving
the slide content unobstructed:

- The top wordmark/counter (and the test's score pill) live in a fixed
  `.topbar`; the bottom holds a fixed `.bottombar` strip behind the `prev` /
  `progress` / `next` controls. On desktop both bars are transparent and the
  chevrons sit at the vertical centre of the screen edges.
- A `@media (max-width:760px)` block turns `.topbar` and `.bottombar` into
  semi-opaque, blurred bars, and **moves the chevrons down into the footer**
  (`top:auto; bottom:14px`) flanking the progress dots, so all navigation is
  thumb-reachable at the bottom. The ticks shrink (and shrink again under
  380px) but stay equal-length. A second small `@media` step tightens spacing on
  very narrow screens.
- Use `<meta name="viewport" content="width=device-width, initial-scale=1.0,
  viewport-fit=cover">` and give slide `.inner` extra top/bottom padding on
  mobile so content clears the two bars.
- Copy the chrome CSS + the two `@media` blocks from either bundled example
  verbatim — they are generic. The score pill is hidden with a `.scorepill.empty`
  class (toggled by a small `setScorePill()` helper) so it doesn't render as an
  empty bordered pill before the first answer.

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
- **Running score** in a header pill (hidden until the first answer).
- **Results slide** — an animated circular SVG score ring fills to the
  percentage, the number counts up, and a banded verdict/message is shown
  (100 / ≥80 / ≥60 / ≥40 / below). A "Retake" button resets answers, ticks,
  score, and ring. Keep the ring **compact** (the example uses ~188px, ~150px on
  mobile, with the `svg` set to `width/height:100%` so the `viewBox` math is
  untouched) so anything below it — notably a Publish Score panel — stays
  visible without scrolling.

## Shared leaderboard (optional, tests)

A test can let players **publish the score they achieved** to a leaderboard
shared across all players, shown on the results slide. The bundled
`example-test.html` does **not** wire this up (it needs a real backend table);
**martin/earth-science-01 is the worked example** — copy its publish panel,
leaderboard modal, and the `mes1_high_score` migration as a starting point.

- **Backend** — store scores in the shared Supabase project and call it directly
  from the browser; see the [`database-backend`](../database-backend/SKILL.md)
  skill for the table-slug convention, RLS policies, migrations, and the
  publishable key. Use a per-project slug table (e.g. `mes1_high_score`) with
  columns `name`, `score`, `total`, `timestamp`, and `CHECK` constraints that
  mirror the in-browser name validation. Make all network calls **best-effort**
  (try/catch + console log) so the quiz still works offline.
- **Results-slide UI** — below the (compact) score ring, add a name field plus
  **Publish Score** and **Leaderboard** buttons, then a small status line. The
  name pre-fills from `localStorage` and is saved on a successful publish.
- **Publishing** — validate the name (e.g. 1–18 chars, letters/spaces/dashes),
  `POST` a row, then open the leaderboard modal with the new entry highlighted.
  Lock to one publish per attempt and re-enable it in the "Retake" reset. After
  each insert, prune rows outside the displayed top N to keep the table in sync
  with the board.
- **Leaderboard modal** — a fixed backdrop + card listing the top N
  (`order=score.desc,id.desc&limit=N`), each row showing rank, name, score
  (`18 / 20`) and date. Close it via its ×, a backdrop click, or `Esc`. On mobile
  the publish buttons stack full-width and the modal caps its height.

## Building a new deck

1. Copy `example-presentation.html` (or `example-test.html`) into the new
   project as `index.html`.
2. Keep the whole `<style>` block and the background/engine `<script>` parts as
   they are — they are generic.
3. Replace the content array (`SLIDES` / `QUESTIONS`) and the brand wordmark.
4. Tune accent colors via the `:root` CSS variables only if needed.
5. Document the project's actual content in its README, and link back to this
   skill for the generic style/engine rather than re-describing it.
