# Learnings: what works and what doesn't

The evidence behind the workflow in SKILL.md. Dated where a model version matters; re-check old findings when the
models change. Worked example: `martin/dungeon-crawler-01` (hero, skeleton, ghoul, keepers, villagers, the
ranger tests of 2026-11-16/18, whose experiment folder was removed once its tools moved here: see the git history
of `martin/dungeon-crawler-01/tools/ranger_test` for the raw images and comparison pages).

## Guides

- **Always use a pose guide.** Without one (tested 2026-11-16 with OpenAI `gpt-image-2.6-flare` and Google
  `gemini-nano-banana-2.1`, a ranger from scratch) the stride was wrong in every direction for both models, whatever
  the per-frame wording, and Google could not draw a figure facing LEFT at all.
- **Mocap guides beat the stick figure.** Rendered from the Quaternius walk (`render_guide.py`), the guide has real
  shoulder and hip rotation, weight shift and foot roll; OpenAI matched 8 of 8 frames in NW on the first try.
  The algorithmic stick figure (`walk_cycle.py`) is still useful for monsters with a made-up gait (skeleton,
  ghoul: lean, crouch, stiff arms) where a natural walk isn't wanted.
- **Shaded clay mannequin (default since 2026-11-18) vs colour per limb.** With the colour guide, OpenAI keeps part of
  each colour's lightness: the bright orange right leg (luma 150 against the blue's 88) came out ~30 % lighter and
  warmer than the left in both 8 × 8 tests (`render_guide.py --balanced` evens the colours out). The shaded grey
  guide has no colours to bleed: both NW tests (8 and 12 frames) matched every frame, legs the same shade, rounder
  shading. Its cost: the model follows the mannequin's outline more closely, so a mid-thigh cloak shrank to a
  capelet; the prompt now says loose clothing is painted at full length, and the reference image shows it.
- **Without colours, the legs still alternate.** The fear was that the model can't tell the legs apart in grey;
  the mocap guide's depth (far side darker, ink lines where a limb crosses the body) was enough in NW.
- **The colour key, when used:** "Each limb of the mannequin has its own colour so you can follow it from figure to
  figure: BLUE = his LEFT leg ..." plus "The colours are ONLY a pose guide: NONE of blue, orange, teal, yellow ...
  may appear". Without that sentence the colours once leaked into armour.
- **The forward foot looks long at heel strike.** Not the mesh (its 3D length is constant to ±3 %): the toes point up
  16-30°, and from above and behind (NW) that tilt shows ~30 % more foot on screen than a flat one. The mannequin's
  own feet are also big (30.3 cm, ~EU 48); the default guides use EU 43 (`--shoe 43`, 27.2 cm).
- **Cells must hold the whole stride.** 12 frames in 256-wide cells (1536 × 960) cut the side views' feet off at the
  cell edge, and the jog's even at 384. The guides now use 384 × 512 cells everywhere and shrink a wide-striding clip
  (`render_guide.py` fit, 16 px margin) with the same factor in every direction.
- **Children:** `--preset child-12 / child-8` changes proportions (bigger head, shorter limbs and neck, narrower
  shoulders); the figure is drawn at the same height, the game draws it smaller. Before the presets existed,
  children were painted over the adult guide with "CHILD proportions (a big head, short limbs, small hands)".

## Painting

- **One direction per image.** A whole 8 × 8 sheet in one image does work with a guide (64 of 64 cells, every row
  facing right, one consistent character, $0.055 at 1536 × 2048, crisp at 2400 × 3200 for $0.104), but the shading of
  surfaces (cloth folds) is not consistent from frame to frame. Without a guide a whole sheet fails outright: same
  pose in every frame, rows facing the wrong way, figures across grid lines.
- **12 frames look more natural than 8:** the in-between poses show shoulder and hip rotation that 8 frames skip.
  10 and 12 frames matched every frame in NW. The game needs no change: frames come from meta.json and `fpt` scales
  with the frame count (fpt × 1.5 for 12).
- **Faded ("ghost") limbs:** OpenAI sometimes paints the FAR boot or arm pale, desaturated and without an outline. It is
  opaque (alpha ~250), not see-through, but reads as a ghost, especially on a dark floor. One prompt line removed it
  in every image since: "Every part of the character is fully OPAQUE: no faded, ghostly or see-through limbs, even a
  leg or arm partly behind the body." Keep it, and keep checking: `grid_check.py` flags the clear case (957 px vs
  0-41 elsewhere) but missed two milder ones, so look at every image on the dark floor too.
- **Half-transparent gaps:** OpenAI's background removal leaves the narrow gaps between arm and torso at alpha 50-200,
  and sometimes a faint painted ground shadow (alpha ~66). `build_sheet.py` remaps alpha (< 96 clear, > 224 opaque).
  These gaps made grid_check flag 7 good S frames as "faded" until its see-through test was limited to the legs.
- **The character as the main image and the guide as a reference** fails: the model copies the reference pose and you
  get 8 nearly identical frames. The guide is always the first image, the one being edited.
- **The second half of the stride painted like the first** (the classic failure with the old grey stick guide): the
  models follow the silhouette (how far apart the feet are) but not which leg is in front, so frames 5-8 copied 1-4.
  Fixed by guides that make the legs distinguishable, per-frame wording ("figure 7: the OPPOSITE of figure 1 ... NOT a
  copy") and checking every image. With the stick guide: picture cues beat leg names ("its boot far to the lower
  LEFT ... the widest stance of all 8 frames"), and near / far beat left / right. The front view (S) once alternated
  with no wording at all; assembling the row from two attempts' frames fixed it.
- **"The other leg leads in frames 5-8" read as "turn around".** Say: "the body NEVER turns around between figures".
- **Explicit view sentences**, e.g. W: "strict side profile walking to the LEFT: we see only his LEFT side, NOT turned
  toward the viewer". Facing SW / W / NW shows the character's left side, S the front, N the back.
- **The look reference sets the body angle** more strongly than the prompt: a side-view reference for a three-quarter
  sheet put some figures in profile. A turnaround (front, side, back) avoids this; say "copy only the design, never
  its pose or view".
- **An explicit design paragraph** is still needed with a reference: without one the model drifted (flat-topped helm,
  light-grey armour) in one direction. Name what each hand holds, and how an item looks in every view, or it
  appears in some frames only (a basket, a hammer).
- **Arms:** "make the arms swing" without per-frame detail gives stiff, hanging arms.
- **Repainting a character with another model** changes its look: redo all directions, not just the broken ones.
- **Models (2026-11-16/18):** OpenAI `gpt-image-2.6-flare` (medium, transparent output) is the default. Google
  `gemini-nano-banana-2.1` followed the guide too (7 of 8, frames 2-3 narrower) but has no transparency and a
  ranger with a long cape; Gemini also could not draw left-facing figures without a guide.

## Consistency between directions and characters

- So far the character was painted from the text description alone, and it drifted between images (face, cloak
  length, trouser shade). The workflow now sends an approved reference (a turnaround) with every direction, plus a
  frame of the first approved direction. Untested as of 2026-11-18: the first character made with the new workflow
  is the test.
- `grid_check.py --ref` measures colour drift (histogram intersection with the reference): same-description repaints
  scored 0.74-0.84, a visibly different look 0.46, another model's ranger 0.17. Thresholds 0.70 / 0.55 are provisional.

## Building and the game

- **Never cut by grid lines:** find figures as connected components and assign each to the cell holding its centroid.
- **Anchor by the feet, centre by the head and shoulders** (stick-figure sheets). Anchoring by the head top left
  figures floating; centring the whole figure made swinging legs shift the body. Mocap-guided sheets go further:
  see "Translation drift and planted feet".
- **Ground point below the frame bottom:** the foot nearer the camera hangs below the ground point in this view
  (footY 128 in a 152 px frame); give a character a taller frame rather than shrinking it.
- **Mirroring** SW / W / NW into SE / E / NE swaps the legs, which in a walk cycle is just a half-stride phase shift.
  Held items and asymmetric clothes change sides (a knife on the other hip): paint all 8 when that matters.
- **Advance frames by distance walked, not time** (`anim += distance × fpt / scale`): feet never slide, provided fpt
  matches the guide's stride (see "Translation drift and planted feet").
- **Older 4-frame sheets** can be re-cut (components, foot anchor, mirrored rows) at no AI cost; that alone fixed cut
  heads, floating and wrong-way rows.
- Non-walking characters (wraiths, ghosts): one pose per direction plus a code-driven bob. Many-legged creatures need
  another pose model; the humanoid mannequin doesn't fit them.

## Spend so far (for estimates)

- martin/dungeon-crawler-01, older models at ~$0.07 per image: the hero $0.83 (method being worked out), skeleton and
  ghoul ~$0.44 each, four keepers $1.58 (~$0.40 each), eight more characters ~$0.43 each.
- 2026-11 tests with `gpt-image-2.6-flare` medium: one direction 8 frames 1536 × 1024 $0.034; 12 frames 1536 × 960
  $0.031; 8 × 8 sheet 1536 × 2048 $0.055, 2400 × 3200 $0.104. Cost follows the image size, not the frame count
  (roughly $0.02 + $0.011 per megapixel).

## Shimmer (2026-11-18, dungeon-crawler hero)

- **A detailed reference makes the walk shimmer:** fine texture (mottled plate, speckled cloth) is repainted
  differently in every frame and flickers when the frames play. Measured at game scale (figure 118 px tall, mean
  edge strength over the figure): the detailed NW walk 45, the old in-game sprite 31.
- **Fix: a simple reference plus a consistency paragraph.** Redraw the approved reference with `edit` ("large clean
  areas of colour, 2-3 tones per material, NO texture, NO speckles"); it came back lighter (grey steel, bright red),
  so its colours were pulled back in Python (colour 0.85 against the original). Add to the prompt: "this is an
  animation ... every figure is shaded IDENTICALLY: the same highlight on the same plate, the same few broad folds".
  Result: 24, flat and steady from frame to frame. Make references simple from the start.
- **A "STEADY FROM FRAME TO FRAME" paragraph works on cloth** (2026-11-18, hero-2 NW, OpenAI): "paint him as if he
  were ONE 3D model rendered 12 times: the SAME highlight shapes in the SAME places, the SAME dents and rust ...; the
  cape has the SAME few broad folds ... only sways gently; the hem keeps the SAME outline ... do not redraw new tears
  or stain blotches in each figure". Cape outline overlap between neighbouring frames: 0.78, against 0.70 for the
  old in-game sprite and 0.74-0.75 for earlier attempts without it. The prompt is kept in hero-2/paint/NW.prompt.txt. Confirmed by eye (Martin: "the animation is steadier"); now built into guide_prompt.py for every prompt.
- **Stocky bodies:** `render_guide.py --preset stocky` (shorter legs, broad shoulders, short neck, `--girth`
  1.35). Girth thickens around the bones without changing lengths; the old length factors alone made a stocky
  build thinner (shorter legs came out thinner too).
- **"Never flares" for wide cloth** (2026-11-18, hero-2 NW): asking for a WIDE cape (as wide as the shoulders,
  covering the back) made it puff out in two frames (overlap 0.56 there, 0.73 mean). Adding "keeps the SAME width and
  outline in ALL figures ... never flares, billows, puffs out or swings wide; heavy, hangs close to the body; only its
  bottom edge moves a little" gave 0.86 mean, 0.81 worst pair: the steadiest cape so far. Now in guide_prompt.py.
  Asking for the cape's full width also turned the figure further toward the three-quarter back view.

## Stable directions (2026-11-18, dungeon-crawler hero-2, OpenAI, 12 frames, all 8 painted)

- **Recipe that worked:** approved reference (simple, bold shapes) + the approved NW walk as the third input
  (`--match NW`) + the STEADY paragraph + a per-view cape sentence (now `guide_prompt.py --cloth`). 7 of 8
  directions passed first time (stride 12/12, colour 0.80-0.89).
- **Say where wide cloth shows in each view.** The cape was designed and approved in NW; in the other views the
  model has to work out where a wide cape shows. Telling it per view ("front view: behind both shoulders and at both
  sides behind the legs"; "side view facing left: down the back, on the RIGHT of the figure") kept its width and
  placement the same all round.
- **The one failure (SE, first try):** frame 3 off the stride, a faint thin cape, the chainmail skirt missing.
  Repainted once with "the same rich deep crimson, fully opaque ... the chainmail skirt shows": 12/12, 0.80. Hence
  `--cloth` also asks for the same colour and full opacity in every figure.
- **Still to watch:** fine chainmail texture stays lumpy and can flicker a little; the cape in a front three-quarter
  view came out a shade darker.

## Translation drift and planted feet (2026-11-18, hero-2)

- **The model shifts figures inside the sheet.** Registered against the guide (mask correlation, 6 x 2 sheets of
  384 x 512 cells), every hero-2 direction drifted the same way: along each row the figures creep left by up to
  20-30 guide px from the first to the last, and the bottom row sits 10-30 px low. At game scale that is up to ~8 px
  of jumping, most visible in E and SE. The old build (centre the head and shoulders, feet on the guide's lowest
  point) kept the horizontal part, and removed the body's natural sway.
- **Fix in the build, not by repainting:** put each figure back on its guide frame. Soles on the guide's soles;
  horizontally the feet band (bottom 30 %) slid to the best overlap, then refined (+-15 px) on the planted foot
  alone, since the painted stride can be a little longer or shorter than the guide's. The guide's own position in
  its cell is kept: the in-place mocap (cycle-mean pelvis at the centre), so the body sways as it really does.
- **fpt must match the mocap's stride.** In the in-place guide the planted foot slides backward at exactly the
  walking speed; render_guide measures it (`cycle_px`: the stance foot's speed relative to the pelvis) and with
  fpt = frames / (loop length in tiles) the guide's planted ball of the foot stays within 0.1 px in the world.
  Stocky legs (0.88) take shorter steps: 1.405 tiles per loop, fpt 8.54; the standard mannequin 1.495 tiles, fpt
  8.02. The old fixed 7.5 for 12 frames let the feet slide about 1 px per frame.
- **Checking it:** an automatic "slip" number (the centroid of the lowest piece near the planted foot) was too noisy:
  it latched onto the cape hem or the other foot. The feet check image (`build_sheet.py --plant-check`) is reliable:
  hero-2's planted feet stay within a couple of game px of the line.

## Body presets and height (2026-11-19, hero-2)

- **`render_guide.py --preset stocky` is normalised to full height** (the stocky guide figure is as tall as the
  standard one), and build_sheet sizes every sheet to `--height`. Short legs at full height mean a bigger torso,
  head and shoulders: hero-2 looked larger than the original knight in the game. A short build has to be made
  short where it is drawn: the game's per-character draw scale (dungeon-crawler `CAST_SCALE.hero2`: 0.93, about
  the height lost to legs 0.88 and neck 0.6, looked too small; the user settled on 0.96), or `--height` in the build. The game's draw scale is simpler: the
  game resamples every sprite anyway (zoom, device pixel ratio), and the walk divides `fpt` by the scale.
