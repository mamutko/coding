# Romeo &amp; Juliet — Quote Test

## Purpose

A single self-contained `index.html` multiple-choice test on quotations from
Shakespeare's *Romeo and Juliet*. A bank of **50 quotes** is held in the page; each time
the test is started, **20 are drawn at random and shown in random order**. For every quote
the player answers two multiple-choice questions and then sees the source passage.

The visual style (dark titanium look, animated engineering background, reactive chrome,
paged navigation) deliberately reuses the look and feel of the `chemistry-test-01` project.

## Test Format

For each of the 20 quotes the player answers:

1. **Who speaks this line?** — 4 choices: the correct character plus 3 other characters
   drawn at random from the play's cast.
2. **What does the quote mean in modern English?** — 4 choices: the correct paraphrase
   plus 3 paraphrases drawn at random from the other quotes in the bank.

Scoring:

- **1 point per correct answer**, so up to **2 points per quote** and **40 points** for a
  full 20-quote test.
- Each question locks after the first answer (one attempt). The correct option turns green
  with a ✓; a wrong choice turns red with a ✗; the rest dim.
- The running score is shown in the top-right score pill.

After **both** questions for a quote have been answered, the **full source passage** is
revealed below, labelled with the speaker and the act/scene reference.

The options for both questions are shuffled each time, and a fresh random set of 20 quotes
is generated whenever the test is (re)started, so the test is replayable.

## Quote Bank

The page contains 50 quotes. Each entry stores: the quote text, the speaker, the
act/scene reference, a modern-English meaning, and the fuller source passage it is taken
from. The cast used for speaker choices is: Romeo, Juliet, Mercutio, Friar Laurence,
Nurse, Tybalt, Benvolio, Lord Capulet, Lady Capulet, Prince Escalus, Paris, and the
Chorus. Quotes span the Prologue through Act 5, Scene 3 (the balcony scene, the
Mercutio/Tybalt fight, the Queen Mab speech, the Capulet household, and the tomb).

## Style &amp; Effects

Reuses the presentation style of `chemistry-test-01`:

- **Titanium look** — dark background layered with a fine + bold graph-paper grid (CSS
  repeating gradients) and a radial vignette; cards and controls use a metallic blue/grey
  gradient with a light top edge and soft shadow. Quotes and passages are set in an italic
  serif for contrast.
- **Reactive schematic network** — the background is a live `<canvas>` (`#schem`)
  generating a connected graph of orthogonal "traces" with circle nodes. Hovering near a
  node charges it (growing a soft halo); moving away fires a bright pulse that travels the
  traces and splits at intersections.
- **Scrolling grid** — the graph-paper grid and the schematic canvas scroll horizontally
  in sync with the paged navigation (via the `--gx` background-position variable and a
  per-page canvas offset).
- **Mouse-reactive chrome** — a `pointermove` handler sets a per-element proximity value
  (`--p`, 0–1) on `.reactive` elements (nav chevrons, progress ticks), scaling their glow.
- **Paged deck** — an intro page, one page per quote, and a results page live in a
  horizontal flex `.deck`; navigation slides horizontally with an eased transform.

## Navigation

- Right-edge "next" and left-edge "prev" chevrons (prev hidden on the first page, next
  hidden on the last).
- A clickable progress-tick bar; a tick turns green once both questions for its quote have
  been answered, and the current page's tick is highlighted.
- Keyboard: `←` `→`, `PageUp`/`PageDown`, `Home`/`End`, and keys `1`–`4` to answer the
  current (first unanswered) question on a quote page.
- Touch-swipe (horizontal) on touch devices.

## Mobile / Cell-phone Layout

The page is responsive and rearranges its chrome on narrow screens (≤ 760 px):

- **Top overlay** — a semi-opaque, blurred bar pinned to the top holds the headline
  (test title) on the left and the score tally on the right.
- **Bottom overlay** — a semi-opaque, blurred bar pinned to the bottom holds the
  navigational elements: the **previous** and **next** buttons (moved from the screen
  sides into the bottom corners) and the **progress indicator** (compact ticks) centered
  between them.
- Content padding is increased top and bottom so quotes and options never sit under the
  overlays, and each page scrolls vertically if its content is tall.
- The viewport meta uses `viewport-fit=cover` for edge-to-edge rendering on notched
  phones.

## Results

A results page shows an animated circular score ring that fills to the percentage, an
animated count-up of the score out of 40, and a verdict + message chosen from percentage
bands (100% / ≥80% / ≥60% / ≥40% / below). A **New test** button generates a fresh random
set of 20 quotes and returns to the intro page.

## Implementation

Implemented as a single self-contained `index.html` file with no external dependencies.
The quote bank, quiz logic, responsive chrome, and the animated `<canvas>` background
engine are all inline. The deck (intro + 20 quote pages + results) is built in JavaScript
from the quote bank, so the bank is the single source of truth for the test content.
