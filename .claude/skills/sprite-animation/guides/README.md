# Pre-rendered pose guides

Paint over these directly; no rendering needed. Regenerate the whole set with `python ../tools/default_guides.py`
(~5 min). Each `<DIR>.png` has a `<DIR>.json` beside it (grid, ground line, standing-figure height, clip, body, ground covered per loop `cycle_px` and the feet per frame),
which `build_sheet.py` and `board.py` read.

| Folder | Source | Frames / layout | Size |
|---|---|---|---|
| `walk/8f`, `walk/12f` | Quaternius `Walk_Loop` | 8: 4 × 2 · 12: 6 × 2 | 1536 × 1024 · 2304 × 1024 |
| `formal-walk/8f`, `/12f` | Quaternius `Walk_Formal_Loop` (upright, measured) | as above | as above |
| `jog/8f`, `/12f` | Quaternius `Jog_Fwd_Loop` (drawn at 0.77 so the wide stride fits its cells) | as above | as above |
| `stick/12f` | `stick_guide.py all guides/stick/12f` (the `hero` gait of walk_cycle.py as a true stick figure with hip and shoulder T bars, one grey) | 6 × 2 | 2304 × 1024 |
| `stick-walk/8f` | `walk_cycle.py guide hero <DIR> --magenta --limbs` (algorithmic stick figure) | 4 × 2 | 1200 × 880 |

- **Mocap guides** (`walk`, `formal-walk`, `jog`): shaded light-grey clay mannequin (`render_guide.py --shaded`),
  adult, 1.82 m, feet 27.2 cm (EU 43), all 8 directions S SW W NW N NE E SE, cells 384 × 512, flat magenta.
  Frame 1 is the left heel strike; row 1 is the first step, row 2 the second. Paint them with
  `guide_prompt.py --plain`.
- **Stick-figure guides**: one colour per limb (blue left leg, orange right leg, teal left arm, yellow right arm),
  only the 5 base directions (mirror the rest). Use them for characters that don't need a natural gait or have a
  per-character gait in `walk_cycle.py` `CHARS` (skeleton, ghoul): render a new set with
  `walk_cycle.py guide <CHAR> <DIR> out.png --magenta --limbs`. Paint them with `guide_prompt.py` (no `--plain`).
  If the right leg comes out lighter, that is the bright orange showing through (see learnings.md).
- **Stick guide** (`stick`): the algorithmic `hero` gait as a true stick figure: thin sticks all of ONE light grey
  (lit from the upper left, no darker far side), a hip T bar (0.34 m, wider than real hips) with the legs hanging
  from its ends, a shoulder T bar with the arms from its ends, a stick spine and neck, a ball head with a nose bump,
  small balls at the joints and hands, a stick per foot; ink lines round the sticks and where one crosses in front
  of another. All 8 directions, cells 384 × 512 on flat magenta, with the mocap guides' sidecar (`fig_px`,
  `cycle_px` from the gait's stance, `feet` with the planted foot from the phase). Paint it with
  `guide_prompt.py --stick`; review with `tools/review.py`.
