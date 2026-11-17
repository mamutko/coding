"""Prompt for painting a character over a colour-per-limb pose guide (render_guide.py or walk_cycle.py --limbs),
for any layout: one direction in a C x R grid of N frames, or several directions with one row each.
OpenAI wording (transparent background). Generalises nwprompt.py.

  python guide_prompt.py <DIR|DIR,DIR,...|all> [--frames N] [--cols C]
"""
import sys

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
CHARACTER = ("a lean young ranger/hunter, adult man about 25. Deep forest-green hooded cloak to mid-thigh, hood DOWN on "
             "his shoulders; short tousled auburn hair; brown leather jerkin laced over a cream linen shirt; dark leather "
             "bracers; wide brown belt with a pouch and a sheathed hunting knife at the hip; olive-brown trousers; "
             "knee-high scuffed brown leather boots. Hands EMPTY: NO bow, NO quiver, NO weapon held.")


def prompt(dirs, frames=8, cols=4, character=CHARACTER):
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
    return f"""This image is a POSE GUIDE: {layout} Paint over EVERY mannequin, keeping each one's EXACT position, size and pose of legs, arms, torso and head. Do not move, add or remove any figure, and do not change any pose.

Each limb of the mannequin has its own colour so you can follow it from figure to figure: BLUE = his LEFT leg, ORANGE = his RIGHT leg, TEAL = his LEFT arm, YELLOW = his RIGHT arm, grey = torso, light grey = head. A red dot marks the face where it is visible.

{view}

FOLLOW THE LEGS EXACTLY, they alternate. {where}
figure 1: the BLUE leg reaches forward, the ORANGE leg stretched far back.
figure {q1}: the BLUE leg under the body; the ORANGE leg bent at the knee, foot lifted, swinging forward.
figure {h + 1}: the OPPOSITE of figure 1: now the ORANGE leg reaches forward and the BLUE leg is stretched far back. It is NOT a copy of figure 1.
figure {q3}: the ORANGE leg under the body; the BLUE leg bent, foot lifted, swinging forward.
All other figures are in-between poses: copy them from the guide.
Arms swing opposite to the legs, following the TEAL and YELLOW arms exactly; the hands are at clearly different positions from figure to figure, open and EMPTY.

CHARACTER (identical in all {n} figures): {character} Copy only the pose from the mannequins, not their shapes: give him natural human proportions and clothing.

STYLE: hand-drawn 2D game sprite art for an isometric RPG, clean dark ink outlines, painterly watercolour-and-gouache shading, light from the upper left. NOT pixel art, NOT 3D.

The colours are ONLY a pose guide: NONE of blue, orange, teal, yellow or the red dot may appear anywhere in the painting; paint every limb in the character's own clothing colours. Every part of the character is fully OPAQUE: no faded, ghostly or see-through limbs, even a leg or arm partly behind the body.
Transparent background (remove the magenta). No text, numbers or grid lines."""


if __name__ == "__main__":
    a = sys.argv[1]
    dirs = ROWS if a == "all" else a.split(",")
    f = int(sys.argv[sys.argv.index("--frames") + 1]) if "--frames" in sys.argv else 8
    c = int(sys.argv[sys.argv.index("--cols") + 1]) if "--cols" in sys.argv else (f if len(dirs) > 1 else 4)
    print(prompt(dirs, f, c))
