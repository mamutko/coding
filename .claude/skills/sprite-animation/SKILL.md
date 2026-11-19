---
name: sprite-animation
description: Make walking characters for an isometric (or any top-down 3/4) browser game with AI-painted art — an approved character reference, a mannequin pose guide rendered from motion capture (or an algorithmic stick figure for monsters), one direction at a time painted over the guide by an image model, automatic stride / faded-limb / colour-drift checks, a review board kept as an Artifact, and a sprite sheet built for the game (8 or 12 frames, 8 directions, mirrored or not). Use when creating a new character or monster sprite, a walk / jog cycle, a custom pose guide (other clip, child proportions, foot size), or fixing sprites that float, slide, stutter or face the wrong way. Worked example: martin/dungeon-crawler-01.
---

# Sprite animation: AI walk cycles for 8-direction characters

Everything reusable lives in this folder; read `learnings.md` for why each step is the way it is.

```
SKILL.md        this workflow
learnings.md    what works and what doesn't (evidence, dated)
datasets.md     motion-capture sources and their licences (Quaternius, CC0)
datasets/quaternius-ual1/   UAL1_Standard.glb (in place, use this), UAL1_Standard_RM.glb (root motion), License.txt
guides/         pre-rendered guides, see guides/README.md: walk, formal-walk, jog (8f / 12f, all 8 directions,
                shaded clay, adult 1.82 m, EU 43 feet) and stick-walk (algorithmic stick figure)
tools/
  render_guide.py    mocap mannequin guide: --clip, --frames, --shaded, --shoe, --preset child-8 / child-12, ...
  walk_cycle.py      the algorithmic stick-figure guide (per-character gaits in CHARS) and the projection
  default_guides.py  regenerates guides/
  guide_prompt.py    the painting prompt: --plain (shaded guide), --character, --ref, --match
  grid_check.py      checks a painting against its guide: stride, faded limbs, colour drift (--ref)
  board.py + board_template.html   the character board (review page, published as an Artifact)
  build_sheet.py     painted directions -> game sprite sheet + meta.json entry
tests/          a known guide + painting pair for grid_check (a real faded boot), see Verifying the tools
```

Images are painted with the **ai-media-generation** skill in Martin's **notes** repo
(`notes/.claude/skills/ai-media-generation/openai_media.py`, OpenAI, transparent output). It holds API keys: call
it by path, never copy it, its scripts or keys into this public repo. Follow its cost rules: ask before a call over
$0.20 or a turn over $3.00, and report the spend at the end of every turn. Run the tools with the Python that has
numpy, Pillow, scipy (and numba, which makes the shaded render fast).

## The workflow for a new character

Make characters **one at a time**. Each has a folder in its project, e.g. `<project>/art/characters/<id>/`, holding
`character.json` (see `tools/board.py` for the fields: description, decisions, references, directions, spend,
artifact URL), the reference images, any custom guide, and `paint/<DIR>.png` (plus `attempts/`).

**Keep the board current.** After every step below, rebuild it and republish it to the same Artifact URL
(`python tools/board.py <character.json> board.html`, then publish `board.html`; the first publish stores the URL in
character.json). It shows the reference candidates, the guide and the painted walk for every direction on one clock,
the checks, the decisions and the spend, so the user can look before each approval.

**Approvals.** Stop for the user's approval where marked. The user may waive approvals ("go ahead without asking");
then run straight through, still running every check and updating the board, and report at the end.

### 1. Reference picture (approval)

Paint 2-3 candidates of a **turnaround**: the same character three times side by side (front, side facing left,
back), full body, standing relaxed with the arms a little away from the body, on a transparent background.

```
python <notes>/.claude/skills/ai-media-generation/openai_media.py image "<prompt>" --size 1536x1024 \
    --quality medium --background transparent -o <char>/reference-1.png
```

Prompt: "Character turnaround sheet for a hand-drawn 2D isometric RPG: the same character three times side by side,
FRONT view, SIDE view facing left, BACK view; full body, standing relaxed, arms slightly away from the body, feet
visible. CHARACTER: <design paragraph: build, face, hair, every garment with its colour and length, what each hand
holds>. STYLE: hand-drawn 2D game sprite art, clean dark ink outlines, painterly watercolour-and-gouache shading,
light from the upper left. NOT pixel art, NOT 3D. Transparent background. No text."

- **Style consistency across characters** (the user may ask for several references at once): use `edit` with
  approved references of other characters as inputs and add "in exactly the style of the attached characters (line
  weight, shading, palette, proportions), but this new design". Prefer this whenever approved references exist.
- The user approves one (mark it `"approved"` in character.json). The design paragraph becomes `"description"`.

### 2. Decisions (ask, record in character.json)

- **Frames per direction: 8 or 12.** 12 looks more natural (shoulder and hip rotation), 8 is lighter. The 12-frame
  guides are 2304 × 1024 (~$0.046 per direction, estimated) against 1536 × 1024 for 8 ($0.034).
- **Mirror SE / E / NE from SW / W / NW, or paint all 8?** Mirroring costs 5 images instead of 8 but swaps held items
  and asymmetric clothing to the other side.
- **Guide:** the default `walk` unless the character calls for another (next step).

### 3. Guide (approval only for a custom one)

- **Default:** `guides/walk/<8|12>f/<DIR>.png`: adult 1.82 m, EU 43 feet, normal walk. Also committed:
  `formal-walk` (upright, measured: nobles, guards), `jog`, and `stick-walk` (algorithmic, 8 frames, 5 directions).
- **Custom** (render it into `<char>/guide/`, show it on the board, wait for approval before painting):
  - another clip: `--clip Jog_Fwd_Loop | Sprint_Loop | Walk_Formal_Loop | ...` (all 43 in datasets.md);
  - other body: `--preset child-12 | child-8`, `--shoe <EU size>`, or `--head --legs --arms --torso --shoulders --neck`
    (lengths; each also scales that part's thickness with it), and `--girth` (+ `--legs-girth --arms-girth
    --torso-girth`) for thickness alone. Stocky: `--legs 0.88 --shoulders 1.15 --neck 0.6 --head 1.05 --girth 1.35
    --torso-girth 1.25`;
  - a monster with a made-up gait: `walk_cycle.py guide <CHAR> <DIR> out.png --magenta --limbs` (add the gait to
    `CHARS`: lean, crouch, stride, arm swing; then use `guide_prompt.py` without `--plain`).

```
python tools/render_guide.py datasets/quaternius-ual1/UAL1_Standard.glb <DIR> <char>/guide/<DIR>.png --shaded \
    --frames 12 --cols 6 --cell 384x512 [--clip ...] [--preset ...] [--shoe ...]      # 8 frames: --cols 4
```

### 4. Paint, one direction at a time (approval after the first)

Start with a three-quarter view (SW or NW: the hardest and most telling). For each direction:

```
python tools/guide_prompt.py <DIR> --plain --frames 12 --cols 6 --character <char>/character.json --ref \
    [--match <first approved DIR>] > prompt.txt
python <notes>/.../openai_media.py edit "$(cat prompt.txt)" -i <guide>.png <char>/reference.png [<char>/paint/<first>.png] \
    --size 2304x1024 --quality medium --background transparent -o <char>/paint/<DIR>.png      # 8 frames: 1536x1024
python tools/grid_check.py <guide>.png <char>/paint/<DIR>.png 6 2 --dir <DIR> --ref <char>/reference.png
```

- Input order matters: **guide first** (the image being edited), the **reference** second, from the second direction
  on a frame sheet of the **first approved direction** third (`--match`).
- **Check every image** (Read it, and look at it on the board's dark floor): every stride frame matches, no faded
  limbs, colour ≥ 0.70, right view, no leftover grey mannequin, items in the right hands. On a failed check, paint that
  direction once more (prompt fixes in learnings.md); after a second failure, ask.
- **After the first direction: stop for approval.** After that, continue direction by direction, updating the board
  after each; approvals for the rest are optional unless the user wants them.

### 5. Build the sheet

```
python tools/build_sheet.py <char>/character.json <project>/assets/<id>.webp --meta <project>/assets/meta.json \
    [--height 118 --fw 144 --fh 152 --foot-y 128]
```

Then copy the meta entry wherever the game inlines it, run the game, and watch the character walk in every
direction at its real speed (feet on the ground, no sliding, legs alternating).

## Animating in the game

- **Row order** S, SW, W, NW, N, NE, E, SE. Pick the row from the movement direction *projected to screen space*
  and rounded to 45° sectors.
- **Advance frames by distance walked, not time:** `anim += distance × fpt / scale`, frame = `floor(anim) % frames`.
  `fpt` = 5 for 8 frames (one stride per 1.6 tiles), 7.5 for 12. Feet never slide, whatever the speed.
- **Idle frame:** a feet-together pose (build_sheet picks the guide frame with the feet closest).
- **Draw:** `dx = sx − fw·s/2`, `dy = sy − footY·s`, plus a shadow ellipse at the ground point (the painted ground
  shadow is removed in the build).

## Cost per character (OpenAI medium, guides render free)

| Item | Cost |
|---|---|
| Reference, 2-3 candidates | ~$0.10-0.15 |
| Walk, 5 painted directions (mirrored), 8 frames / 12 frames | ~$0.17 / ~$0.23 |
| Walk, all 8 painted, 8 frames / 12 frames | ~$0.27 / ~$0.37 |
| Retries, about 1 direction in 5 | ~$0.03-0.07 |
| **Walk only** | **~$0.30-0.60** |
| Each further animation (jog, attack, death), per set of directions | as the walk |

A batch of characters easily passes the $3.00 turn cap: get a budget approved first.

## Verifying the tools

- After changing `render_guide.py`, re-render one committed guide and diff it (`default_guides.py --only walk`
  rewrites all; `git diff --stat guides/` should show only what you meant to change).
- `grid_check.py` on the known pair in `tests/`: `python tools/grid_check.py tests/faded-boot-guide-NW.png
  tests/faded-boot-painted-NW.png 4 2 --dir NW` must report 8 of 8 stride matches and 1 faded cell (frame 4: the
  far boot, pale and outline-less; frames 6 and 8 have milder ones it does not catch).
- Build a sheet, preview it on a dark background with the ground point marked in every cell; then run the game
  headless (Playwright, `python -m http.server`), walk in several directions, and confirm no page errors.
