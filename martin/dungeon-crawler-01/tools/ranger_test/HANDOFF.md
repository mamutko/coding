# Handoff: render a NW pose guide from a real 3D walk (Quaternius)

You are continuing work from a cloud session. It could not reach this PC. Everything you need is below.

## Setup
1. In the `coding` repo: `git fetch origin claude/ai-media-transparent-backgrounds-svotyu` and check that branch out.
   It has `martin/dungeon-crawler-01/tools/walk_cycle.py` with the new `--limbs` option, the updated
   `.claude/skills/sprite-animation/SKILL.md` (read it first), and the test scripts in `tools/ranger_test/` (see its README).
2. In the `notes` repo, check out the same branch name. It has the updated `ai-media-generation` skill: default OpenAI
   image model `gpt-image-2.6-flare` (real transparent backgrounds), `models` and `api` subcommands, and a price for
   `gemini-nano-banana-2.1`. Never read the `.key` files yourself; always call the scripts.
3. The model pack is at `C:\Users\marti\Downloads\Universal Animation Library[Standard]\Universal Animation Library[Standard]`
   (Quaternius, CC0). Find the glTF/GLB that holds the mannequin and its walk clip.

## What we learned so far (2026-11-16)
- Without a pose guide, every walk cycle from both models had a bad stride, whatever the prompt said. A whole 8 x 8 sheet
  in one image failed for both models.
- With the stick-figure guide from `walk_cycle.py` (NW only), both models followed the guide's foot spread in 7 of 8
  frames (`stride_check.py hero NW <img>`). Coloring each limb a different colour leaked nothing into the art, so
  `--limbs` is now the default.
- The user found the stick-figure guide's motion wobbly. Part of that was the review page's slicing, now fixed. The
  rest is the hand-made motion in `walk_cycle.py`: cosine leg curves, no heel strike or toe push-off, plus deliberate
  sway and shoulder twist. Hence this task: a guide rendered from a real, professionally made walk.

## The task
Render a NW pose guide from the Quaternius mannequin's walk clip, in exactly the format of
`python walk_cycle.py guide hero NW out.png --magenta --limbs`, so it can replace that file one for one:
- **Image:** 1200 x 880, flat magenta #FF00FF, 4 x 2 grid of 300 x 440 cells, 8 figures. Figures 1-4 go in the top
  row and 5-8 in the bottom row, left to right. In each cell the body is centred horizontally and stands on a ground
  line 70 px above the cell's bottom edge. The figure is about 360 px tall.
- **Frames:** 8 evenly spaced samples over ONE full walk cycle (two steps). Frame 1 = left heel strike (left leg
  forward); frame 5 = right heel strike. Make it an in-place walk: remove any root motion, so the figure doesn't drift.
- **Camera:** orthographic, 30 degrees above horizontal (2:1 dimetric), as in `walk_cycle.py` (`ELEV`, `project()`).
  NW = the figure walks away toward the upper LEFT of the image: we see its back and its LEFT side. Check against the
  stick-figure guide: the same facing in every cell.
- **Colours** (flat, unlit or nearly so; assign by the bone each vertex is mostly weighted to): left leg incl. foot
  BLUE (30, 90, 230); right leg ORANGE (245, 130, 0); left arm incl. hand TEAL (0, 190, 200); right arm YELLOW
  (245, 215, 0); torso, hips, neck GREY (120, 120, 125); head light grey (205, 205, 205), plus a small red dot on the
  face side if it is visible (it is barely visible in NW).
- **Tool suggestion:** three.js (GLTFLoader, AnimationMixer, OrthographicCamera, MeshBasicMaterial per limb) in a
  headless browser via Playwright, or Blender if it is installed. Save the script as
  `tools/ranger_test/render_guide.*` and the guide as `guide-mocap-NW.png`.

## Then
1. Show the user the new guide next to `walk_cycle.py guide hero NW --magenta --limbs` (both 4 x 2 sheets), and ideally
   as two side-by-side animations at about 2 fps.
2. If they like it: paint the ranger over it with both models, using the prompt from
   `python tools/ranger_test/nwprompt.py color openai` (and `... color google`). Commands (paths to the notes repo's
   `.claude/skills/ai-media-generation/`):
   - `python openai_media.py edit "<prompt>" -i guide-mocap-NW.png --quality medium --size 1536x1024 --background transparent -o openai-mocap-NW.png`
   - `python google_media.py edit "<prompt>" -i guide-mocap-NW.png -m gemini-nano-banana-2.1 --size 1K --aspect 4:3 -o google-mocap-NW.png`
   About $0.04 each. Report the spend at the end of the turn.
3. Check the stride (`stride_check.py` compares against the stick-figure guide, so treat it as a rough check only) and
   add the results to `ranger_test/review.html` / `nwbuild.py`.

## Rules
- The user wants to review each step before you go on. Ask before any single call over $0.20 or a turn over $3.
- Commit only on the `claude/ai-media-transparent-backgrounds-svotyu` branch for now, not `main`. The user will merge
  both repos' branches later.
- Don't copy the ai-media-generation skill or its key files into the public `coding` repo.
