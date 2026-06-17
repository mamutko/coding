# Earth Science Quiz — Ecosystems & Nutrient Cycles

A single-file, self-contained `index.html` multiple-choice quiz for a **Grade 9
Earth Science** class. It reviews ecosystem energy flow, food chains and webs,
the energy pyramid, biomes, and the four nutrient cycles. The content is drawn
from a student study sheet (food chain/web/pyramid, biomes, and the carbon,
nitrogen, water and phosphorus cycles).

## Look & feel

Built in the repo's **titanium / engineering deck** style — a dark titanium
surface over a graph-paper grid with a live, mouse-reactive schematic network on
a `<canvas>`, arranged as a horizontally paged deck. See the
[`presentation` skill](../../.claude/skills/presentation/SKILL.md) for the
generic style and engine (background canvas, navigation, reveals, results ring);
this README only describes what is specific to this quiz.

- Brand wordmark: **EARTH SCIENCE — ECOSYSTEMS & CYCLES · GRADE 9**.
- Accent colors use the skill defaults (cyan `--accent`, green for correct, amber
  for wrong).

## Structure

The deck is an intro slide, one slide per question, and a results slide. All
content comes from a single `QUESTIONS` array — the source of truth — where each
entry has `topic`, `q`, four `options`, the `answer` index, and an `explain`
string shown after answering.

### Navigation

Right/left chevrons, a clickable progress-tick bar, keyboard (`←` `→`, space,
`PageUp`/`PageDown`, `Home`/`End`), number keys `1`–`4` to pick an answer, and
horizontal touch-swipe. A counter (top-right) and a running score pill are shown.

### Answering & feedback

Each question allows **one attempt**. Selecting an option locks the question: the
correct option turns green with a ✓, a wrong pick turns red with a ✗, the rest
dim, and an explanation panel slides in. The question's progress tick turns green
once answered, and the running score updates.

### Results

An animated circular score ring fills to the percentage and the number counts up.
The verdict is banded by percentage:

- **100%** — "Perfect score!"
- **≥ 80%** — "Great work!"
- **≥ 60%** — "Good effort"
- **≥ 40%** — "Keep studying"
- **below 40%** — "Time to review"

A **Retake quiz** button resets answers, ticks, score, and the ring.

## Content covered

There are 20 questions across these topics:

- **Energy flow & roles** — producers, consumers, detritivores, decomposers,
  trophic levels.
- **Photosynthesis & cellular respiration** — the two reactions and what they
  convert (CO₂ + H₂O ⇄ O₂ + glucose, plus energy).
- **Food chains & food webs** — why a web models an ecosystem better than a
  single chain.
- **Energy pyramid** — ~80–90% of energy lost as heat between trophic levels, and
  why fewer organisms are supported at higher levels.
- **Biomes** — permanent ice, desert, tundra, boreal forest (and their
  characteristic plants and animals).
- **Nutrient cycles** — carbon (reservoirs/residence times and what releases
  CO₂), nitrogen (fixation, nitrification, uptake, denitrification), water
  (evaporation → condensation → precipitation), and phosphorus (the one cycle
  with no atmospheric stage).

To change the quiz, edit the `QUESTIONS` array in `index.html` (and update this
section to match).
