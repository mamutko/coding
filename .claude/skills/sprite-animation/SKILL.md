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
                shaded clay, adult 1.82 m, EU 43 feet), stick-walk (algorithmic stick figure, a colour per limb) and
                stick (the same gait as a true one-grey stick figure with hip and shoulder T bars, 12 frames, 8 dirs)
tools/
  render_guide.py    mocap mannequin guide: --clip, --frames, --shaded, --shoe, --preset stocky / child-8 / child-12,
                     --girth (body thickness), ...
  walk_cycle.py      the algorithmic stick-figure guide (per-character gaits in CHARS) and the projection
  stick_guide.py     a walk_cycle.py gait drawn as a true stick figure (T bars at hips and shoulders, one grey) in the
                     mocap guides' layout and sidecar (fig_px, cycle_px, feet): paints with --stick, builds with build_sheet
  default_guides.py  regenerates guides/
  guide_prompt.py    the painting prompt: --plain (shaded guide), --stick (stick figure), --character, --ref, --match, --cloth, --she (a woman)
  grid_check.py      checks a painting against its guide: stride, faded limbs, colour drift (--ref)
  review.py          review sheets of one painted direction (every frame and the legs zoomed, guide over painting,
                     labelled with the leg that must be in front) + the leg shade check (a darker back / far leg)
  board.py + board_template.html   the character board (review page, published as an Artifact);
                     a direction can show several variants (e.g. one per reference candidate) side by side
  join_halves.py     two half-cycle paintings (stick_guide.py --halves, guide_prompt.py --half) -> one full sheet
  build_sheet.py     painted directions -> game sprite sheet + meta.json entry (aligned on the guide, fpt from
                     the stride, --plant-check feet image; "from_guide": a mannequin sheet)
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
    --quality medium --background transparent -o <char>/reference/round-1/candidate-1.png
```

Keep every candidate, in rounds (`reference/round-1/`, `round-2/` ...; a round = one set of candidates after a
round of feedback), and copy the approved one to `reference/reference.png`: that is the file every later step uses.

Prompt: "Character turnaround sheet for a hand-drawn 2D isometric RPG: the same character three times side by side,
FRONT view, SIDE view facing left, BACK view; full body, standing relaxed, arms slightly away from the body, feet
visible. CHARACTER: <design paragraph: build, face, hair, every garment with its colour and length, what each hand
holds>. STYLE: hand-drawn 2D game sprite art, clean dark ink outlines, painterly watercolour-and-gouache shading,
light from the upper left. Show shine, wear and texture with a FEW BOLD shapes (clear highlight shapes, a handful of
dents, worn edges or stains), never with fine noise, speckles or scratch texture, so it animates cleanly and reads at
120 px tall. NOT pixel art, NOT 3D. Transparent background. No text."

- **Keep the reference free of fine texture.** Whatever fine speckle, mottling or ragged detail the reference has,
  the walk repaints differently in every frame and it shimmers (learnings.md, "Shimmer"). Bold marks are fine.

- **Style consistency across characters** (the user may ask for several references at once): use `edit` with
  approved references of other characters as inputs and add "in exactly the style of the attached characters (line
  weight, shading, palette, proportions), but this new design". Prefer this whenever approved references exist.
- The user approves one (mark it `"approved"` in character.json). The design paragraph becomes `"description"`.

### 2. Decisions (ask, record in character.json)

- **Frames per direction: 8 or 12.** 12 looks more natural (shoulder and hip rotation), 8 is lighter. The 12-frame
  guides are 2304 × 1024 (~$0.03 per direction, measured on hero-2) against 1536 × 1024 for 8 ($0.034).
- **Mirror SE / E / NE from SW / W / NW, or paint all 8?** Mirroring costs 5 images instead of 8 but swaps held items
  and asymmetric clothing to the other side.
- **Guide:** the default `walk` unless the character calls for another (next step).

### 3. Guide (approval only for a custom one)

- **Default:** `guides/walk/<8|12>f/<DIR>.png`: adult 1.82 m, EU 43 feet, normal walk. Also committed:
  `formal-walk` (upright, measured: nobles, guards), `jog`, and `stick-walk` (algorithmic, 8 frames, 5 directions).
- **`stick`** (`guides/stick/12f`): the original knight's algorithmic gait as a true stick figure: thin sticks all
  of one grey, a T bar at the hips (wider than real hips, the legs hanging from its ends) and one at the shoulders
  (the arms from its ends), a stick spine between them, a ball head with a nose bump. Use it when the mocap
  mannequin's look carries into the painting (too slim, bent knees, head down: the user's verdict on the mocap
  heroes). Paint with `guide_prompt.py --stick` (it describes the T bars, says the sticks are only the pose, asks
  for a sturdy build, a straight standing leg, a level head and both legs painted alike, and in side and diagonal
  views names the near / far leg and which one is in front figure by figure), `"guide": "stick"` in
  character.json. Render another gait or size with `tools/stick_guide.py <DIR|all> <out_dir> --char <CHARS key>
  [--frames 8 --cols 4]`. Never shade one leg darker in a guide: it comes out as a darker painted leg. See
  learnings.md, "Shaded stick guide", "Near leg always trailing" and "True stick figure".
- **Custom** (render it into `<char>/guide/`, show it on the board, wait for approval before painting):
  - another clip: `--clip Jog_Fwd_Loop | Sprint_Loop | Walk_Formal_Loop | ...` (all 43 in datasets.md);
  - other body: `--preset stocky | child-12 | child-8`, `--shoe <EU size>`. Fine-tune any preset by hand:
    `--head --legs --arms --torso --shoulders --neck` set lengths (each also scales that part's thickness with it);
    `--girth` (+ `--legs-girth --arms-girth --torso-girth`) sets thickness alone, without changing bone lengths.
    `stocky` = legs 0.88, shoulders 1.15, neck 0.6, head 1.05, girth 1.35, torso girth 1.25 (a heavier build:
    `--preset stocky --girth 1.5`). The joint angles stay as captured, so shorter legs take shorter steps;
    record the body in character.json `"body"`. **Presets are rescaled to full height:** a stocky guide is as
    tall as the standard one, so short legs come out as a bigger torso, head and shoulders. Make a short build
    short where it is drawn (the game's per-character draw scale; hero-2: 0.96), see learnings.md "Body presets
    and height";
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
    [--match <first approved DIR>] [--cloth "wide crimson cape"] > <char>/paint/<DIR>.prompt.txt
python <notes>/.../openai_media.py edit "$(cat <char>/paint/<DIR>.prompt.txt)" -i <guide>.png \
    <char>/reference/reference.png [<char>/paint/<first>.png] --size 2304x1024 --quality medium \
    --background transparent -o <char>/paint/<DIR>.png                                        # 8 frames: 1536x1024
python tools/grid_check.py <guide>.png <char>/paint/<DIR>.png 6 2 --dir <DIR> --ref <char>/reference/reference.png
```

- Input order matters: **guide first** (the image being edited), the **reference** second, from the second direction
  on a frame sheet of the **first approved direction** third (`--match`).
- `guide_prompt.py` always adds a **STEADY FROM FRAME TO FRAME** paragraph: paint the character as one 3D model
  rendered N times (same highlights, markings and colours in the same places), loose cloth keeps the same few folds
  and only sways, hems keep the same outline. It made the cape and the shading steady (learnings.md); keep it when
  adding your own lines to the prompt. Save the exact prompt next to the painting (`paint/<DIR>.prompt.txt`).
- **Keeping the directions the same character** (learnings.md, "Stable directions"; all 8 of hero-2 passed, 7 on
  the first try):
  - paint the hardest view first (NW / SW), get it approved, then pass it as `--match` (third image) to every other
    direction: same colours, shading, detail level;
  - a character with a cape or cloak gets `--cloth "<its name>"`: per view, where the cloth shows and how wide, and
    the same width, colour and full opacity in every figure. Without it the cape came out narrow, faint or missing
    in some views;
  - one failed direction: repaint it once with a line naming what went missing (hero-2 SE: "the same rich deep
    crimson, fully opaque ... the chainmail skirt shows"); keep the failed try in `paint/attempts/` with its prompt.
- **Review every direction** before accepting it (and before showing it to the user). The automatic numbers
  (grid_check: stride, faded limbs, colour) catch only some failures: the stride check compares how far apart the
  feet are, which is the same whichever leg leads, so a walk with one leg ALWAYS trailing passes it (hero-6 E: the
  user saw "one foot always dragging behind, always the same side"; grid_check said 11/12). So:
  1. `python tools/review.py <char>/character.json <DIR>` writes `paint/review-<DIR>-frames.png` and
     `review-<DIR>-legs.png` and prints, figure by figure, which leg must be IN FRONT, and the leg shade check.
  2. **Read `review-<DIR>-legs.png` at full size and, for EVERY frame, decide which painted leg is in front and
     whether it is the near or the far one** (the near leg is drawn over the other where they cross; from the hip
     down its outline is unbroken; in a side view its foot sits a little lower on screen). Write the answer down
     frame by frame (e.g. "1 far ok, 2 far ok, ... 7 near WRONG") and compare with the printed labels. Pay most
     attention to frames 1 and N/2 + 1 (the widest stances): they must have DIFFERENT legs in front. In S and N
     the legs are told apart left / right on screen: the left foot forward in the guide must be the left one
     painted. One wrong contact frame, or the same leg in front in both halves, fails the direction.
  3. **Leg shade:** both legs painted alike. review.py flags a back leg (all views) or far leg (side and diagonal
     views) darker by more than about 10-12 luminance; also look at the legs sheet: one trouser leg or boot clearly
     darker than the other in most frames fails (the user noticed it at once).
  4. **The rest, on `review-<DIR>-frames.png`:** the right view (facing, which side shows), the head level and
     facing the walking direction (not looking down), natural sturdy proportions (no thin guide limbs, no grey,
     no bars), the standing leg straight, items in the right hands and on the right hips, the cloth the same in
     every frame, no faded limbs, no shimmer (also play it on the board at the character's pace).
  Known weak spot (learnings.md, "True stick figure"): the strict side views E and W, where the model tends to paint
  the same leg in front in both halves whatever the guide and prompt say: review them with extra care. In N and S,
  don't pass `--match` with a three-quarter view (it pulled N into a three-quarter view).
  5. Record the result in character.json (the direction's "note": e.g. "legs 12/12 by eye, shade ok, stride 12/12,
     colour 0.91"). On a failure, paint that direction once more with a line naming what went wrong (prompt
     fixes in learnings.md; keep the failed try in `paint/attempts/`); after a second failure, ask.
- **After the first direction: stop for approval.** After that, continue direction by direction, updating the board
  after each; approvals for the rest are optional unless the user wants them.

### 5. Build the sheet

```
python tools/build_sheet.py <char>/character.json <project>/assets/<id>.webp --meta <project>/assets/meta.json \
    --key <id> [--height 118 --fw 144 --fh 152 --foot-y 128] [--plant-check feet.png]
```

- **Frame size:** keep the game's other characters' (hero: 118 px tall in 144 x 152, foot at 128) so the new sheet
  looks the same in the game; the 384 x 512 guide cells are downsampled (LANCZOS) about 3.6x.
- **Alignment is automatic:** the model drifts figures (a row creeps left by up to ~30 guide px, the bottom row sits
  low), so the build puts every figure back on its guide frame (soles on the guide's soles, feet over the guide's
  feet, then on the planted foot) and keeps the guide's own in-place position. No repaint for a shifted frame.
- **fpt comes from the guide:** the guide's sidecar records the ground covered per loop (`cycle_px`), and the build
  turns it into frames per tile (hero-2, stocky legs: 8.54; the standard mannequin 8.02). Use it as is: with it the
  planted foot stays still on the ground.
- **Check the feet:** `--plant-check feet.png` shows, for every stance, the feet of its frames one under the other,
  shifted by the ground walked, with a red line at the guide's planted foot. The planted foot should stay on the
  line (a couple of game px is normal).
- **A mannequin sheet:** a character.json with `"from_guide": true` builds the guide itself as a walking sheet (no
  painting): a placeholder look, or a test of a game's animation.
- **Folders:** everything in `<char>/` is source (`reference/` with its rounds, `guide/`, `paint/` with prompts and
  `attempts/`, the board) and is never loaded by the game; only `<project>/assets/<id>.webp` and its meta entry ship.

Then copy the meta entry wherever the game inlines it, run the game, and watch the character walk in every
direction at its real speed (feet on the ground, no sliding, legs alternating).

## Animating in the game

- **Row order** S, SW, W, NW, N, NE, E, SE. Pick the row from the movement direction *projected to screen space*
  and rounded to 45° sectors.
- **Advance frames by distance walked, not time:** `anim += distance × fpt / scale`, frame = `floor(anim) % frames`.
  `fpt` from build_sheet (the guide's own stride; the old stick-figure sheets used 5 for 8 frames, one stride per
  1.6 tiles). Feet never slide, whatever the speed.
- **Draw scale per character:** every sheet is built to the same height (`--height`); a character that should be
  shorter or taller (a child, a stocky build) gets a draw scale in the game (dungeon-crawler: `CAST_SCALE`), and
  the frames advance by `fpt / scale` so its feet stay planted. The game resamples every sprite anyway (zoom,
  device pixel ratio), so this looks the same as building a smaller sheet.
- **Idle frame:** a feet-together pose (build_sheet picks the guide frame with the feet closest).
- **Draw:** `dx = sx − fw·s/2`, `dy = sy − footY·s`, plus a shadow ellipse at the ground point (the painted ground
  shadow is removed in the build).

## Cost per character (OpenAI medium, guides render free)

| Item | Cost |
|---|---|
| Reference, 2-3 candidates | ~$0.10-0.15 |
| Walk, 5 painted directions (mirrored), 8 frames / 12 frames | ~$0.17 / ~$0.15 |
| Walk, all 8 painted, 8 frames / 12 frames | ~$0.27 / ~$0.24 |
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
