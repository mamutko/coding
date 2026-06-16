# Chemistry Test

## Purpose

A single-page, self-contained `index.html` multiple-choice test on introductory
chemistry. The questions are sourced from a hand-written Grade-8 science study guide
covering the Kinetic Molecular Theory, states and changes of matter, the atom,
classification of matter, and physical &amp; chemical properties. The test gives the
student instant feedback per question and a final score.

The visual style (dark titanium look, animated engineering background, reactive chrome,
paged navigation) deliberately reuses the look and feel of the
`money-positioning-presentation-01` project.

## Style &amp; Effects

The test uses the repo's shared **titanium / engineering deck** style (dark graph-paper
background, a live mouse-reactive schematic `<canvas>`, metallic cards, a horizontally
paged deck, and animated reveals) — the same engine as `money-positioning-presentation-01`.
The generic style and its reusable engine are documented in the **`presentation` skill**
(`.claude/skills/presentation/`), which also ships runnable example decks. Only the
test-specific behaviour is described below.

## Navigation

- Right-edge "next" and left-edge "prev" chevrons (prev hidden on the first page, next
  hidden on the last).
- A clickable progress-tick bar at the bottom; a tick turns green once its question has
  been answered, and highlights the current page.
- Keyboard: `←` `→`, `space`, `PageUp`/`PageDown`, `Home`/`End`. Number keys `1`&ndash;`4`
  select the corresponding answer on a question page.
- Touch-swipe (horizontal) on touch devices.
- A header counter shows the current page number and total; a score pill appears once the
  first question is answered.

## Test Behaviour

- The deck is built dynamically in JavaScript from a `QUESTIONS` array, so the content is
  the single source of truth for the test.
- Each question shows the topic, the question text, and four lettered answer options as
  reactive cards.
- **Instant feedback** &mdash; selecting an option locks the question (one attempt). The
  correct option turns green with a ✓; if the chosen option was wrong it turns red with a
  ✗, and the other options dim. An explanation panel slides in below.
- The running score is tracked and shown in the header score pill.
- **Results page** &mdash; an animated circular score ring fills to the percentage, the
  score counts up, and a verdict + message is shown based on the percentage band
  (100% / ≥80% / ≥60% / ≥40% / below). A "Retake test" button resets all answers, ticks,
  the score, and the ring, and returns to the intro page.

## Question Content

The test contains the following question topics (the correct answer and a short
explanation accompany each in code):

1. **Kinetic Molecular Theory** &mdash; central idea (all matter is particles in constant
   motion).
2. **States of Matter** &mdash; the solid state (particles close together, only vibrate).
3. **States of Matter** &mdash; behaviour of gas particles (far apart, fast, straight
   lines, random directions).
4. **Changes of State** &mdash; sublimation (dry ice &rarr; vapour).
5. **Changes of State** &mdash; condensation (dew forming on grass).
6. **Changes of State** &mdash; deposition (frost forming, gas &rarr; solid).
7. **Energy &amp; Particles** &mdash; effect of adding heat (particles spread and speed up).
8. **The Atom** &mdash; which particle is positive (proton).
9. **The Atom** &mdash; atomic number = number of protons.
10. **The Atom** &mdash; electrons in the first shell (2).
11. **Atomic Models** &mdash; Rutherford (mostly empty space, positive core).
12. **Atomic Models** &mdash; Bohr (electrons orbit in fixed circles like planets).
13. **Ions** &mdash; cation (positive ion, mostly metals).
14. **Periodic Table** &mdash; group with a &minus;1 charge (halogens).
15. **Classification of Matter** &mdash; element (one type of atom).
16. **Classification of Matter** &mdash; compound (H₂O, magnesium chloride).
17. **Classification of Matter** &mdash; the two main branches (mixtures vs. pure
    substances).
18. **Physical vs Chemical** &mdash; chemical change (burning wood).
19. **Properties** &mdash; qualitative property (colour).
20. **Reactions** &mdash; which sign is NOT chemical (change of shape only).
21. **Measurement** &mdash; indirect measurement (speed = distance ÷ time).
22. **Density** &mdash; calculate density of a 386 g gold bracelet at 2.0 cm³ (193 g/cm³).

## Implementation

Implemented as a single self-contained `index.html` file with no external dependencies.
All styling, the quiz logic, and the animated `<canvas>` background engine are inline.
