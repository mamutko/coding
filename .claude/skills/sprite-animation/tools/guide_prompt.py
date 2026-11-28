"""Prompt for painting a character over a colour-per-limb pose guide (render_guide.py or walk_cycle.py --limbs),
for any layout: one direction in a C x R grid of N frames, or several directions with one row each.
OpenAI wording (transparent background). Generalises nwprompt.py.

  python guide_prompt.py <DIR|DIR,DIR,...|all> [--frames N] [--cols C] [--plain] [--character FILE]
                         [--ref] [--match DIR] [--cloth "wide crimson cape"] [--she]
  --plain       for the shaded grey mannequin (render_guide.py --shaded, the default guides): no limb-colour key
  --stick       for the shaded grey stick figure (stick_guide.py): like --plain, and says the figure is only a pose
                skeleton (thin limbs, ball head): paint a sturdy natural body, legs straight under the body, head level
  --character   the character's description: a .txt file, or a .json with a "description" key (character.json)
  --ref         the 2nd input image is the approved character reference (turnaround): paint exactly that character
  --match DIR   the 3rd input image is this character already painted (and approved) walking DIR: match its look
  --cloth TEXT  the character wears wide cloth hung from the shoulders (cape, cloak): say, for this view, where it
                shows and how wide, and that it keeps the same width, colour and opacity in every figure and as in
                the matched direction (learnings.md, "Stable directions": without it the cape came out narrow,
                faint or missing in some directions)
  --she         a woman: the prompt says she / her instead of he / his / him
Input images go to the edit call in this order: guide, reference, matched direction.
Every prompt includes the STEADY FROM FRAME TO FRAME paragraph (same highlights, markings, cloth folds and hem
outline in every figure), which stopped shading shimmer and a jumping cape hem (learnings.md, "Shimmer").
"""
import json, pathlib, sys

ROWS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
VIEW = {
    "S":  "walks straight TOWARD the viewer (toward the bottom of the image): we see his FACE and FRONT",
    "SW": "walks diagonally toward the LOWER LEFT, turned about 45 degrees to the left: we see his face in three-quarter view and his LEFT side",
    "W":  "strict side profile walking to the LEFT: we see only his LEFT side, NOT turned toward the viewer",
    "NW": "walks diagonally AWAY toward the UPPER LEFT: we see his BACK and his LEFT side; the face is hidden",
    "N":  "walks straight AWAY from the viewer (toward the top of the image): we see only his BACK; the face is hidden",
    "NE": "walks diagonally AWAY toward the UPPER RIGHT: we see his BACK and his RIGHT side; the face is hidden",
    "E":  "strict side profile walking to the RIGHT: we see only his RIGHT side, NOT turned toward the viewer",
    "SE": "walks diagonally toward the LOWER RIGHT, turned about 45 degrees to the right: we see his face in three-quarter view and his RIGHT side",
}
SHORT = {"S": "toward the viewer", "SW": "toward the lower left", "W": "to the left, in profile",
         "NW": "away to the upper left", "N": "away from the viewer", "NE": "away to the upper right",
         "E": "to the right, in profile", "SE": "toward the lower right"}
# where wide cloth hung from both shoulders shows, per view (--cloth); {c} = the cloth's name
CLOTH_VIEW = {
    "S":  "In this front view it shows BEHIND him: over and behind both shoulders, and at both sides behind his body and legs.",
    "SW": "In this front three-quarter view it shows behind his body: over and behind both shoulders and as a band behind his legs and his RIGHT side.",
    "W":  "In this side view (facing left) it hangs down his BACK, on the RIGHT side of the figure, from the shoulder down, close to the body.",
    "NW": "In this three-quarter back view it covers the whole back: we see its near edge over his LEFT shoulder and arm, and its far edge beyond his RIGHT shoulder.",
    "N":  "In this back view it covers his WHOLE back from shoulder to shoulder, wider than the torso; only the backs of the shoulders, the head and the lower legs show.",
    "NE": "In this three-quarter back view it covers the whole back: we see its near edge over his RIGHT shoulder and arm, and its far edge beyond his LEFT shoulder.",
    "E":  "In this side view (facing right) it hangs down his BACK, on the LEFT side of the figure, from the shoulder down, close to the body.",
    "SE": "In this front three-quarter view it shows behind his body: over and behind both shoulders and as a band behind his legs and his LEFT side.",
}
CHARACTER = ("a lean young ranger/hunter, adult man about 25. Deep forest-green hooded cloak to mid-thigh, hood DOWN on "
             "his shoulders; short tousled auburn hair; brown leather jerkin laced over a cream linen shirt; dark leather "
             "bracers; wide brown belt with a pouch and a sheathed hunting knife at the hip; olive-brown trousers; "
             "knee-high scuffed brown leather boots. Hands EMPTY: NO bow, NO quiver, NO weapon held.")


def prompt(dirs, frames=8, cols=4, character=CHARACTER, plain=False, ref=False, match=None, cloth=None, stick=False):
    multi = len(dirs) > 1
    rows = len(dirs) if multi else -(-frames // cols)
    n = len(dirs) * frames if multi else frames
    h = frames // 2
    q1, q3 = frames // 4 + 1, frames * 3 // 4 + 1
    if multi:
        layout = (f"{n} mannequins in a grid of {len(dirs)} rows x {frames} columns. Each ROW is one walking direction "
                  f"and shows one complete walk cycle of {frames} figures, left to right.")
        where = "In EVERY row, counting the figures left to right:"
        view = ("DIRECTION, row by row, exactly as the mannequins are turned (all figures in a row face the same way; "
                "the body NEVER turns around within a row):\n" +
                "\n".join(f"Row {i + 1}: {VIEW[d]}." for i, d in enumerate(dirs)))
    else:
        layout = (f"{n} mannequins in a {cols} x {rows} grid showing one complete walk cycle, read left to right and "
                  f"top to bottom (figures 1-{cols} in the top row).")
        where = "Counting the figures in reading order:"
        view = (f"DIRECTION: every figure {VIEW[dirs[0]]}, exactly as the mannequins are turned. "
                "The body NEVER turns around between figures.")
    if plain or stick:
        key = ("The mannequins are smooth light-grey shaded figures; the darker side of the body is the side turned "
               "away from the viewer, and dark lines mark where a limb passes in front of the body.")
        if stick:
            key = ("The mannequins are simple light-grey shaded STICK FIGURES: rounded tubes for the limbs, a slab for "
                   "the torso and a ball for the head, with a small bump for the nose showing where the head faces. "
                   "They show ONLY THE POSE: where each foot, knee, hand and the head are. The darker side of each "
                   "part is turned away from the viewer, and dark lines mark where a limb passes in front of the "
                   "body.\n\nBODY: do NOT copy the stick figure's thin tubes. Paint a real, sturdy, well-built adult "
                   "man with natural human proportions and full muscular limbs, exactly as broad and solid as in the "
                   "reference. He walks UPRIGHT with a confident, relaxed stride: the leg carrying his weight is "
                   "STRAIGHT, the torso is upright, the HEAD is held LEVEL and looks straight ahead in the walking "
                   "direction (never tilted down toward the ground).")
        legs = f"""FOLLOW THE LEGS EXACTLY, they alternate. {where}
figure 1: one leg reaches forward, the other is stretched far back.
figure {h + 1}: the OPPOSITE: the leg that was back in figure 1 now reaches forward. It is NOT a copy of figure 1.
All other figures are in-between poses (a leg passing under the body, the other bent with its foot lifted): copy them exactly from the guide.
Arms swing opposite to the legs, following the mannequin's arms exactly; the hands are at clearly different positions from figure to figure, open and EMPTY."""
        near = {"SW": "LEFT", "W": "LEFT", "NW": "LEFT", "NE": "RIGHT", "E": "RIGHT", "SE": "RIGHT"}.get(dirs[0])
        if stick and near and not multi:
            # the stick guide draws the far leg and arm darker (stick_guide.py FAR_DARK); its gait starts with the
            # LEFT leg forward. Without naming which leg leads, the model painted the near leg in front in both halves
            # of the stride in side views (hero-6 E and W, first try): one foot seemed to drag behind.
            far = "RIGHT" if near == "LEFT" else "LEFT"
            a, b = ("NEAR (light grey)", "FAR (dark grey)") if near == "LEFT" else ("FAR (dark grey)", "NEAR (light grey)")
            import math as _m   # the stick gait: the left hip angle goes as cos(2 pi t); t = 0 is figure 1
            per = ", ".join(f"{i + 1} {('NEAR (light)' if (_m.cos(2 * _m.pi * i / frames) > 0) == (near == 'LEFT') else 'FAR (dark)') if abs(_m.cos(2 * _m.pi * i / frames)) > 0.3 else 'neither (legs passing)'}" for i in range(frames))
            legs = f"""FOLLOW THE LEGS EXACTLY, they alternate. In this view we see his {near} side: his {near} leg and arm are the NEAR ones, drawn LIGHT grey; his {far} leg and arm are on the FAR side of the body, drawn DARK grey. {where}
figure 1: his {a} leg reaches forward, his {b} leg is stretched far back.
figure {h + 1}: the OPPOSITE: his {b} leg reaches forward and his {a} leg is stretched far back. It is NOT a copy of figure 1: the legs have swapped places.
In figures 2-{h} the {b} leg swings forward past the other; in figures {h + 2}-{frames} the {a} leg swings forward past the other. Each leg in turn steps out in front: neither leg always trails behind.
Figure by figure, the leg that is IN FRONT (toward the walking direction): {per}.
Where the NEAR leg is in front, it is the near leg that reaches forward, seen over the far leg, while the far (dark) leg trails behind it, partly hidden: paint exactly that, even though it is less usual than the near leg trailing.
All other figures are in-between poses: copy them exactly from the guide, always checking which of the two legs (light or dark) is in front.
Arms swing opposite to the legs, following the stick figure's light and dark arms exactly; the hands are at clearly different positions from figure to figure, open and EMPTY.
The far leg and arm are darker in the guide only to tell them apart: paint them in the same clothing colours as the near ones, just a little more in shadow, fully opaque."""
        colours = ("The grey " + ("stick figure" if stick else "mannequin") + " is ONLY a pose guide: paint the character's own clothing, skin and hair colours "
                   "over it, with no grey " + ("stick figure" if stick else "mannequin") + " showing.")
    else:
        key = ("Each limb of the mannequin has its own colour so you can follow it from figure to figure: BLUE = his "
               "LEFT leg, ORANGE = his RIGHT leg, TEAL = his LEFT arm, YELLOW = his RIGHT arm, grey = torso, light "
               "grey = head. A red dot marks the face where it is visible.")
        legs = f"""FOLLOW THE LEGS EXACTLY, they alternate. {where}
figure 1: the BLUE leg reaches forward, the ORANGE leg stretched far back.
figure {q1}: the BLUE leg under the body; the ORANGE leg bent at the knee, foot lifted, swinging forward.
figure {h + 1}: the OPPOSITE of figure 1: now the ORANGE leg reaches forward and the BLUE leg is stretched far back. It is NOT a copy of figure 1.
figure {q3}: the ORANGE leg under the body; the BLUE leg bent, foot lifted, swinging forward.
All other figures are in-between poses: copy them from the guide.
Arms swing opposite to the legs, following the TEAL and YELLOW arms exactly; the hands are at clearly different positions from figure to figure, open and EMPTY."""
        colours = ("The colours are ONLY a pose guide: NONE of blue, orange, teal, yellow or the red dot may appear "
                   "anywhere in the painting; paint every limb in the character's own clothing colours.")
    inputs = ""
    if ref:
        inputs = ("\n\nTHE OTHER INPUT IMAGES: the FIRST image is the pose guide described above, the one to paint over "
                  "(keep its layout). The SECOND image is the CHARACTER REFERENCE: paint exactly this character in "
                  "every figure: the same face, hair, body build, clothes, colours, materials and accessories, and the "
                  "same length of cloak and other loose clothing. Copy only the design from it, never its pose or view.")
        if match:
            inputs += (f" The THIRD image is this same character already painted walking {SHORT[match]}: "
                       "match its look exactly (colours, shading, line weight, level of detail), but not its view.")
    loose = (" Clothing that hangs beyond the body (cloak, cape, skirt, long coat, sleeves) is painted at its FULL "
             "length and width, even where the mannequin has no shape there; it moves with the stride.")
    # Steadiness (learnings.md, "Shimmer"): without it the model redraws texture, cloth folds and ragged hems
    # differently in every figure, which flickers when the frames play.
    steady = f"""STEADY FROM FRAME TO FRAME (critical: these {n} figures play one after another as an animation, and anything that is redrawn differently in each figure will flicker):
- Paint the character as if it were ONE 3D model rendered {n} times: the SAME light from the upper left, the SAME highlight and shadow shapes in the SAME places on each surface, the SAME markings (dents, scuffs, stains, patches, patterns, trim) in the SAME spots, the SAME colours.
- Loose cloth (cloak, cape, skirt, coat tails) keeps the SAME width, the SAME outline and the SAME few broad folds in ALL {n} figures. It is heavy and hangs close to the body from the same points; only its bottom edge moves a little with the stride (swinging slightly opposite to the forward leg). It never flares, billows, puffs out or swings wide to one side, and folds never appear, vanish or rearrange between figures.
- Hems and edges keep the SAME outline in every figure (the same frayed or torn edge, the same stains), simply moving with the cloth. Never redraw new tears, new jagged points or new stain blotches in each figure.
- Show shine, wear and texture with a few BOLD shapes, never with fine noise, speckles or scratch texture."""
    if cloth:
        where = (" ".join(CLOTH_VIEW[d] for d in dirs) if len(dirs) == 1 else
                 " ".join(f"Row {i + 1}: {CLOTH_VIEW[d]}" for i, d in enumerate(dirs)))
        same = " and exactly as in the third image" if match else ""
        steady = (f"THE {cloth.upper()} is exactly as in the reference: fastened at BOTH shoulders and draped over "
                  f"both shoulders, wider than the torso, at its full length. {where} It keeps the SAME width, the "
                  f"SAME rich colour and is fully OPAQUE in every figure{same}: never thin, faded, see-through or "
                  f"missing.\n\n" + steady)
    return f"""This image is a POSE GUIDE: {layout} Paint over EVERY mannequin, keeping each one's EXACT position, size and pose of legs, arms, torso and head. Do not move, add or remove any figure, and do not change any pose.{inputs}

{key}

{view}

{legs}

CHARACTER (identical in all {n} figures): {character} Copy only the pose from the mannequins, not their shapes: give him natural human proportions and clothing.{loose}

{steady}

STYLE: hand-drawn 2D game sprite art for an isometric RPG, clean dark ink outlines, painterly watercolour-and-gouache shading, light from the upper left. NOT pixel art, NOT 3D.

{colours} Every part of the character is fully OPAQUE: no faded, ghostly or see-through limbs, even a leg or arm partly behind the body.
Transparent background (remove the magenta). No text, numbers or grid lines."""


if __name__ == "__main__":
    a = sys.argv[1]
    dirs = ROWS if a == "all" else a.split(",")
    f = int(sys.argv[sys.argv.index("--frames") + 1]) if "--frames" in sys.argv else 8
    c = int(sys.argv[sys.argv.index("--cols") + 1]) if "--cols" in sys.argv else (f if len(dirs) > 1 else 4)
    character = CHARACTER
    if "--character" in sys.argv:
        cf = pathlib.Path(sys.argv[sys.argv.index("--character") + 1])
        character = json.loads(cf.read_text(encoding="utf-8"))["description"] if cf.suffix == ".json" else cf.read_text(encoding="utf-8").strip()
    match = sys.argv[sys.argv.index("--match") + 1] if "--match" in sys.argv else None
    cloth = sys.argv[sys.argv.index("--cloth") + 1] if "--cloth" in sys.argv else None
    out = prompt(dirs, f, c, character, plain="--plain" in sys.argv, ref="--ref" in sys.argv or bool(match),
                 match=match, cloth=cloth, stick="--stick" in sys.argv)
    if "--she" in sys.argv:
        import re
        out = re.sub(r"\b(himself|him|his|His|he|He)\b",
                     lambda m: {"he": "she", "He": "She", "his": "her", "His": "Her", "him": "her", "himself": "herself"}[m.group(1)], out)
    print(out)
