# Ranger walk-cycle test (2026-11-16)

A from-scratch test of AI walk cycles for a hooded ranger with empty hands, used to check the `sprite-animation`
skill's assumptions with `gpt-image-2.6-flare` (OpenAI) and `gemini-nano-banana-2.1` (Google). Not used by the game.
The findings are in the skill ("What doesn't work", recipe step 4 and the prompt checklist).

- `prompts.py`: guide-free prompts (whole 8 × 8 sheet, or one 4 × 2 image per direction). The stride was bad in every result.
- `nwprompt.py <grey|color> <openai|google>`: the prompt for painting the ranger over a NW pose guide
  (`../walk_cycle.py guide hero NW out.png --magenta --limbs`, or `--mannequin` for grey).
- `build.py` / `nwbuild.py`: slice AI images into frames (alpha or magenta key, connected components by cell).
  `nwbuild.py` anchors painted frames on the guide's per-frame foot drop and head x, as `walk_cycle.py build` does.
- `review.html`: the NW review page (loads `nwdata.js`, written by `nwbuild.py <dir> <dir>/nwdata.js`; expects
  `guide-{grey,color}-NW.png` and `{openai,google}-{grey,color}-NW.png` in `<dir>`).

Result (NW): with a guide, both models followed the stride in 7 of 8 frames (`../stride_check.py hero NW`); without one,
never. Colour per limb leaked nothing into the art. Next step: replace the stick-figure guide with a render of a real
rigged walk (Quaternius Universal Animation Library, CC0).
