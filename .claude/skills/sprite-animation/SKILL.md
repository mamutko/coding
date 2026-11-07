---
name: sprite-animation
description: How to make and animate walking characters for an isometric (or any top-down 3/4) browser game with AI-generated art — an 8-direction × 8-frame walk-cycle sprite sheet built from a 3D stick-figure pose guide that an image model paints over, robust slicing (no cut-off heads, feet on the ground), mirroring, cleanup of AI mistakes, and distance-driven animation in the game loop. Use when generating or fixing character / monster sprite sheets, walk cycles, facing directions, or sprites that float, slide, stutter or face the wrong way. Worked example: martin/dungeon-crawler-01 (tools/walk_cycle.py, README "Walk cycles").
---

# Sprite animation: AI walk cycles for 8-direction characters

Worked example: `martin/dungeon-crawler-01`. The tool is `tools/walk_cycle.py` (copy it into a new project),
the raw AI images are in `tools/raw/`, and the README sections **Walk cycles (hero, skeleton, ghoul)** and
**Characters** document every number. This skill is the *why* and the recipe; read the README for the exact
parameters.

Image generation goes through the `ai-media-generation` skill in Martin's **notes** repo (Google
`gemini-3.1-flash-image` `edit`, ~$0.07 per image). That skill holds API keys: never copy it, its scripts or
its key files into this public repo. Only call it by path from the notes repo.

## What doesn't work (learned the hard way)

- **Asking for a whole sprite sheet** ("8 rows of directions × 4 walk frames") gives the same pose in every
  frame (always left foot forward). Several rows also face the wrong way (an "E" row facing SE, an "NW" row
  facing NE). And figures cross the grid lines, so cutting by grid slices heads into the cell above, leaving
  a sprite with its head missing and floating.
- **The character as the main image and a pose guide as a reference:** the model copies the reference pose
  and you get 8 nearly identical frames.
- **Coloured guide limbs** (blue left, orange right) leak into the art as blue and orange armour.
- **"Make the arms swing"** without per-frame detail gives stiff, hanging arms even if the guide swings them.
- **A long shared design reference is not enough** to keep the design: without an explicit design paragraph
  the model drifted (flat-topped helm, light-grey armour) in one direction.

## The recipe that works

1. **3D pose model** (`pose(t)` in `walk_cycle.py`): a 1.75 m stick figure with hips, knees, ankles, toes,
   shoulders, elbows, wrists and fists. 8 phases cover one full stride (two steps):
   0 left foot forward, 1 down, 2 passing, 3 up, 4 right foot forward, 5 down, 6 passing, 7 up.
   - Legs: hip swing ±24° (cosine); knee bends up to ~52° in the swing phase.
   - Upper body (this is what makes it not look stiff): pelvis yaw ±6°, shoulders counter-rotate ±8°, the
     torso sways 3.5 cm over the stance leg (hips half as much), leans a few degrees forward (a rotation
     about the hip axis), and the head follows at 60 %.
   - Arms swing ±20° opposite to the same-side leg; the elbow bends more when the arm is forward.
   - Lower the figure so its lowest point touches the ground; that gives the natural bob.
   - Per-character settings (`CHARS`): lean, constant knee bend (crouch), stride, per-arm swing, arm
     offset and elbow. Skeleton: shield forearm held bent in front and barely moving, short sword swing.
     Ghoul: 25° hunch, 24° knee bend, shorter stride, dangling arms.
2. **Projection:** rotate to the facing angle k × 45° and project with a 30° camera elevation (the 2:1
   dimetric view): `screen_x = X`, `screen_y = −Y·cos30° + Z·sin30°`. Draw parts far to near.
3. **Placeholders first.** Render the stick figures at game scale into the real sheet layout, so the game
   animates correctly before any art exists, and so you can check the gait and facing in the game itself.
4. **Guide image per direction** (`guide <CHAR> <DIR> out.png --magenta --mannequin`): the 8 poses in a 4 × 2
   grid on flat magenta, drawn as a **grey mannequin** with thick limbs: dark grey = left, light grey =
   right. One image per direction; generate only the 5 base directions S, SW, W, NW, N.
5. **Generate with `edit`** at aspect 4:3 and 1K. Inputs, in order:
   1. the guide, as the image being edited;
   2. a crop of the character in the same view, as a design reference (from an older sheet or concept art;
      mirror it if that source faced the wrong way);
   3. after the first finished direction: a close-up crop of one finished frame, so all directions match.

   Prompt checklist (see the README for full text):
   - "Paint over EVERY mannequin, keeping each one's exact position, size and pose of legs, arms and torso."
   - "Dark grey limbs = its left arm and leg, light grey = its right." Name what each hand holds per side.
   - Per-frame legs: frame 1 left leg far forward and right far back, frame 3 right knee bent with the foot
     lifted, frame 5 the reverse, frame 7 left foot lifted.
   - Per-frame arms: which arm is forward in frames 1 and 5, both arms close to the body in frames 3 and 7,
     "hands at clearly different positions from frame to frame".
   - Torso: shoulders twist against the hips, slight lean and shift over the supporting leg, "not stiff".
   - **An explicit design paragraph** (shapes, colours, materials, held items), plus "copy only the design,
     not the pose".
   - **An explicit view sentence**, e.g. W: "strict side profile, walks to the LEFT; we see only its LEFT
     side, NOT turned toward the viewer". Side visibility: facing SW/W/NW (screen left) shows the character's
     *left* side; facing S shows the front; N the back.
   - "The grey shades are only a guide, not colours; no grey mannequin parts may remain."
   - "Flat solid pure magenta #FF00FF background, no floor, no shadows, no text."
6. **Review every image** (Read it) before building. Typical faults and fixes:
   - **Leftover flat grey mannequin limbs** (common in the S view): run a second `edit` on the result:
     "remove every flat grey mannequin shape; where it is in the place of a leg, repaint it as <leg
     description>; change nothing else". To find them automatically, look for large flat, unsaturated regions
     with values 150–240.
   - **Duplicate props** (two shields in profile): a cleanup edit that removes the extra one.
   - **A limb lost in cleanup:** paste it from the neighbouring frame with the same pose, aligned on the head,
     filling only empty pixels.
   - **Wrong view** (three-quarter instead of profile): regenerate with a stronger view sentence.
   - **Hunch invisible from behind:** the model draws back views upright. Accept it and give the character
     a taller frame, or don't rely on the back view to show the hunch.
   Do one direction first (SW), review it with the user, then generate the rest in parallel.
7. **Build** (`build <CHAR> tools/raw assets`):
   - **Chroma key** magenta with colour un-mixing and despill.
   - **Find figures as connected components** of the whole image (on a 3× downsampled mask; drop specks
     under 2 % of the largest) and assign each to the grid cell holding its **centroid**. Never cut by grid
     lines. If a component spans more than about 1.4 cells (two figures touching), split it along the grid.
   - **Scale:** one per direction, the median of (pose-model bbox height ÷ AI figure height).
   - **Anchor:** horizontally centre the head-and-shoulders (top 45 % of the alpha centroid), so swinging legs
     don't shift the body. Vertically put the figure's **lowest pixel** where the pose model's lowest foot is
     for that frame. Anchoring by the head top left figures floating.
   - **Ground point below the frame bottom:** `footY` is 128 in a 152 px frame, because the foot nearer the
     camera hangs below the ground point in this view. Give a character a taller frame (`fh`, `foot_y`) if
     any frame clips, rather than shrinking it.
   - **Mirror** SW, W and NW into SE, E and NE. Mirroring swaps the legs, which in a walk cycle is just a
     half-stride phase shift, so it's free. Held items change hands (a sword in the left hand); usually
     acceptable at game size.
   - Write the sheet (WebP) and its `meta.json` entry `{fw, fh, frames, idle, footY, fpt}`, then copy it into
     the inlined `META` in `index.html`.
8. **Older 4-frame sheets** that won't be regenerated: re-cut them the same way (components, foot anchor,
   mirrored base rows) at no AI cost. That alone fixes cut heads, floating and wrong-way rows.

## Animating in the game

- **Row order** S, SW, W, NW, N, NE, E, SE. Pick the row from the movement (or attack) direction *projected
  to screen space* and rounded to 45° sectors.
- **Advance frames by distance walked, not time:** `anim += distance × fpt / scale`. For the hero `fpt = 5`
  (8 frames = one stride per 1.6 tiles). Then feet never slide, whatever the move speed or slow-downs, and
  bigger monsters take longer strides. Compute the distance from the position before and after the update.
- **Idle frame:** pick a feet-together pose (frame 3, "up"), not frame 0.
- **Draw:** `dx = sx − fw·s/2`, `dy = sy − footY·s` (scale `s` per monster), plus a shadow ellipse at the
  ground point.
- **Glows / tiers:** use a canvas `filter` such as `drop-shadow(0 0 7px rgba(...))` on the sprite draw:
  red for champions, green for bosses.

## Verifying

- Preview each sheet on a dark background with the ground point marked in every cell, and look at it.
  Check feet on the marker, no clipping, consistent size between directions, and correct facing per row.
- Check the raw images for leftover flat-grey guide pieces before building.
- Rebuild an existing sheet after refactoring the tool and diff it against the old one (expect only
  sub-pixel differences).
- Run the game headless (Playwright with `channel: 'msedge'`, served by `python -m http.server`), make
  characters walk in several directions, take screenshots, and confirm `anim` advances only while moving
  and that there are no page errors.

## Cost and planning

- One `edit` image is one direction: about $0.07, and 8 frames cost the same as 4. A character is 5 images
  (~$0.37) plus 1–3 retries or cleanup passes, so budget about $0.40–0.75 per character.
- The ai-media-generation skill asks before any call over $0.20 or a turn total over $3.00, and the user may
  set a project budget. Keep a spend ledger and report the spend at the end of the turn.
- Non-walking characters (floating wraiths, ghosts): skip the walk cycle; use one pose per direction plus
  a code-driven bob or sway. Many-legged creatures (spiders) need a different pose model (alternating
  tetrapod gait); the humanoid mannequin doesn't fit them.
