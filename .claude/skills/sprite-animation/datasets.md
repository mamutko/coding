# Datasets

Motion data that `tools/render_guide.py` turns into mannequin pose guides. Add a section for every new source:
where it comes from, its licence, the files kept here and what they contain.

## Quaternius: Universal Animation Library (Standard)

- **Source:** [quaternius.com](https://quaternius.com) by Quaternius ([Patreon](https://www.patreon.com/quaternius)).
  Browse every clip in the [Animation Viewer](https://quaternius.com/animviewer.html).
- **Licence:** [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) (public domain dedication):
  free to use, change and redistribute, also commercially, no attribution required. The original
  `License.txt` is kept next to the files.
- **Files** in `datasets/quaternius-ual1/` (glTF binary, 7.6 MB each; the pack's Unity `.fbx` copies are not kept):
  - `UAL1_Standard.glb`: **in place** (no root motion). Use this one for guides: the character stays on its spot.
  - `UAL1_Standard_RM.glb`: the same clips with **root motion** baked in (the character travels forward).
- **Model:** one rigged, skinned mannequin, 1.83 m tall, 8,546 vertices, 13,744 triangles, two materials (body and
  joint rings). Unreal-style skeleton: `root`, `pelvis`, `spine_01-03`, `neck_01`, `Head`, `clavicle_*`, `upperarm_*`,
  `lowerarm_*`, `hand_*` with fingers, `thigh_*`, `calf_*`, `foot_*`, `ball_*` (`_l` / `_r`). Its feet are 30.3 cm
  (~EU 48); the guides shrink them to EU 43 by default.
- **Clips (43),** durations in seconds. Loops play one full cycle per loop.

  | Group | Clips |
  |---|---|
  | Locomotion | `Walk_Loop` 1.333 · `Walk_Formal_Loop` 1.333 · `Jog_Fwd_Loop` 0.933 · `Sprint_Loop` 0.667 · `Crouch_Fwd_Loop` 2.000 · `Swim_Fwd_Loop` 1.333 · `Roll` 1.467 |
  | Idles | `Idle_Loop` 2.500 · `Idle_Talking_Loop` 2.933 · `Idle_Torch_Loop` 1.267 · `Crouch_Idle_Loop` 2.933 · `Swim_Idle_Loop` 3.333 · `Dance_Loop` 1.000 |
  | Jumping | `Jump_Start` 1.333 · `Jump_Loop` 2.500 · `Jump_Land` 1.267 |
  | Melee | `Sword_Idle` 1.667 · `Sword_Attack` 1.533 · `Punch_Jab` 0.867 · `Punch_Cross` 1.000 |
  | Magic | `Spell_Simple_Enter` 0.533 · `Spell_Simple_Idle_Loop` 2.100 · `Spell_Simple_Shoot` 0.500 · `Spell_Simple_Exit` 0.433 |
  | Pistol | `Pistol_Idle_Loop` 1.667 · `Pistol_Aim_Up` / `_Neutral` / `_Down` 0.167 · `Pistol_Shoot` 0.633 · `Pistol_Reload` 1.667 |
  | Hit and death | `Hit_Chest` 0.333 · `Hit_Head` 0.433 · `Death01` 2.400 |
  | Sitting | `Sitting_Enter` 1.300 · `Sitting_Idle_Loop` 1.667 · `Sitting_Talking_Loop` 2.933 · `Sitting_Exit` 1.033 |
  | Interaction | `Interact` 2.000 · `PickUp_Table` 0.833 · `Push_Loop` 2.667 · `Fixing_Kneeling` 5.200 · `Driving_Loop` 1.667 |
  | Reference | `A_TPose` 2.500 |

- **Used for:** the committed guides `guides/walk` (`Walk_Loop`), `guides/formal-walk` (`Walk_Formal_Loop`) and
  `guides/jog` (`Jog_Fwd_Loop`). Any other clip: `render_guide.py ... --clip <name>`; for clips that aren't walk-like
  loops add `--start 0` (frame 1 at t = 0 instead of the left heel strike).
