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

The results slide also offers **Publish Score** and **Leaderboard** (see below).
A **Retake quiz** button resets answers, ticks, score, the ring, and the publish
state so the score can be published again on a fresh attempt.

## Leaderboard

After the quiz concludes, the results slide lets the player **publish the score
they achieved** to a leaderboard that is **shared across all players**, in the
same spirit as the worm-03 leaderboard. The board lists the **top 20 scores**,
highest first, each showing the player name, the score (e.g. `18 / 20`), and the
date/time it was published.

### Publishing

- A **name field** (pre-filled from the previous publish, saved in
  `localStorage`) sits next to a **Publish Score** button and a **Leaderboard**
  button.
- **Publish Score** validates the name, then inserts a row with the name, the
  number of correct answers, and the quiz length. On success the button becomes
  **Published ✓** (one publish per attempt), the leaderboard opens with the new
  entry highlighted, and the name is saved for next time.
- **Leaderboard** opens the same modal at any time without publishing. It is
  closed with its **×**, by clicking the backdrop, or with **Esc**.
- Each published score is its own row, so the same player can appear more than
  once. After each insert the table is **pruned to the top 20** rows shown.

### Name validation

The name is validated in the browser before publishing and is rejected if it is
empty, longer than **18 characters**, or contains anything other than letters,
spaces and dashes. The same limits are enforced at the database with `CHECK`
constraints (see below). There is no profanity list.

### Backend

The leaderboard is stored in the repo's shared **Supabase** project and read and
written directly from the browser over its REST (PostgREST) Data API with raw
`fetch`. All network calls are **best-effort** — on failure they are logged to
the console and the quiz keeps working offline. The generic backend setup (project
URL/key, the per-project table-slug convention, RLS, and how migrations
auto-apply on merge to `main`) is documented in the
[`database-backend` skill](../../.claude/skills/database-backend/SKILL.md).

#### Table: `mes1_high_score`

- Slug `mes1` = `martin/earth-science-01`.
- Columns: `id`, `name`, `score` (correct answers), `total` (quiz length), and
  `timestamp` (`timestamptz` defaulting to `now()`).
- **Row-level security** is enabled with **permissive** policies granting the
  anonymous role read / insert / delete, so the board is effectively world
  read/write (the quiz is unauthenticated).
- `CHECK` constraints enforce the name rules (1..18 chars, letters/spaces/dashes,
  plus `*` reserved for manual owner redaction), `total > 0`, and
  `0 ≤ score ≤ total`.
- The client reads with `order=score.desc,id.desc&limit=20`, `POST`s new scores,
  and after each insert prunes rows outside the top 20.
- The table, policies, and constraints are created by a migration under
  `supabase/migrations/`.

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
