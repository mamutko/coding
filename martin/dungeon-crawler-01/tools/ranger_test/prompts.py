"""Prompt builder for the hunter walk-cycle test. usage: prompts.py oneshot|dir <openai|google> [DIR] [refdir]"""
import sys
STYLE = ("Hand-drawn 2D game sprite art for an isometric RPG: clean dark ink outlines, painterly watercolour-and-gouache "
         "shading, soft light from the upper left. NOT pixel art, NOT a 3D render, NOT a photo. "
         "Camera: isometric 3/4 view from above at about 30 degrees elevation, the same camera for every figure; "
         "every figure shows the full body from head to boots.")
DESIGN = ("CHARACTER (identical in every figure: same face, proportions, colours, clothing and gear): a lean young "
          "ranger/hunter, an adult man of about 25. Deep forest-green hooded cloak falling to mid-thigh, hood DOWN on "
          "his shoulders; short tousled auburn hair and light stubble; brown leather jerkin laced up the front over a "
          "cream linen shirt; dark leather bracers on both forearms; a wide brown belt with a small pouch and a "
          "sheathed hunting knife at the hip; olive-brown trousers; knee-high scuffed brown leather boots. "
          "His hands are EMPTY: NO bow, NO quiver, NO arrows, NO weapon held.")
BG = {"openai": "Transparent background.",
      "google": "Flat solid pure magenta #FF00FF background filling the whole image behind every figure; "
                "never use magenta or pink on the character."}
# per direction: view sentence, what 'A' and 'B' legs are (A leads in frame 1)
DIRS = {
 "S":  ("Every figure walks straight TOWARD the viewer (toward the bottom of the image): we see his FRONT, face and chest, "
        "body square to the viewer.", "the leg on the LEFT side of the image", "the leg on the RIGHT side of the image",
        "The leading foot is closer to the viewer, so its boot appears clearly LOWER in the image than the other boot."),
 "N":  ("Every figure walks straight AWAY from the viewer (toward the top of the image): we see his BACK, the cloak and the "
        "back of his head; the face is NOT visible.", "the leg on the LEFT side of the image",
        "the leg on the RIGHT side of the image",
        "The leading foot is farther from the viewer, so its boot appears clearly HIGHER in the image than the other boot."),
 "SW": ("Every figure walks diagonally toward the LOWER LEFT of the image, body turned about 45 degrees to the image's left: "
        "we see his front AND his left side. NOT facing the viewer straight on, NOT in full profile.",
        "his NEAR leg (closer to the viewer)", "his FAR leg",
        "The forward boot is far to the lower LEFT in the image, the back boot to the upper RIGHT."),
 "SE": ("Every figure walks diagonally toward the LOWER RIGHT of the image, body turned about 45 degrees to the image's right: "
        "we see his front AND his right side. NOT facing the viewer straight on, NOT in full profile.",
        "his NEAR leg (closer to the viewer)", "his FAR leg",
        "The forward boot is far to the lower RIGHT in the image, the back boot to the upper LEFT."),
 "W":  ("Every figure walks to the LEFT of the image in strict side profile: we see only his LEFT side, nose pointing left; "
        "NOT turned toward the viewer.", "his NEAR leg (closer to the viewer)", "his FAR leg (partly hidden behind the near one)",
        "The forward boot is far to the LEFT in the image, the back boot far to the right."),
 "E":  ("Every figure walks to the RIGHT of the image in strict side profile: we see only his RIGHT side, nose pointing right; "
        "NOT turned toward the viewer.", "his NEAR leg (closer to the viewer)", "his FAR leg (partly hidden behind the near one)",
        "The forward boot is far to the RIGHT in the image, the back boot far to the left."),
 "NW": ("Every figure walks diagonally AWAY toward the UPPER LEFT of the image, turned about 45 degrees: we see his BACK and "
        "his left side, the face hidden or barely in profile. NOT straight from behind, NOT full profile.",
        "his NEAR leg (closer to the viewer)", "his FAR leg",
        "The forward boot is to the upper LEFT in the image, the back boot to the lower RIGHT."),
 "NE": ("Every figure walks diagonally AWAY toward the UPPER RIGHT of the image, turned about 45 degrees: we see his BACK and "
        "his right side, the face hidden or barely in profile. NOT straight from behind, NOT full profile.",
        "his NEAR leg (closer to the viewer)", "his FAR leg",
        "The forward boot is to the upper RIGHT in the image, the back boot to the lower LEFT."),
}
ORDER = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]

def cycle(d):
    _, A, B, cue = DIRS[d]
    return (f"WALK CYCLE: the 8 figures are ONE complete walking stride (two steps), in order. Every figure is a DIFFERENT "
     f"moment; no two may be identical. Figures 5-8 repeat 1-4 with the OTHER leg leading: they are NOT copies of 1-4. "
     f"Call A = {A} and B = {B}. "
     f"1 contact: A reaches far forward, heel touching down; B stretched far back on its toes; widest stance. {cue} "
     f"Arms swing opposite to the legs. "
     f"2 down: weight drops onto A, knee bent; B's foot peeling off behind; body at its lowest. "
     f"3 passing: A straight under the body; B bent at the knee, its foot OFF the ground swinging forward past A; arms close to the body. "
     f"4 up: body at its highest; A pushing off on its toes behind, B reaching forward. "
     f"5 contact, the OPPOSITE of 1: now B reaches far forward, heel down, and A is stretched far back; widest stance. "
     f"6 down: weight on B, knee bent; A's foot peeling off behind. "
     f"7 passing: B under the body; A bent, its foot OFF the ground swinging forward past B. "
     f"8 up: highest; B pushing off behind, A reaching forward; then the cycle loops to 1. "
     f"Throughout: the body bobs, shoulders twist against the hips, the empty hands swing naturally.")

def dir_prompt(prov, d, ref=None):
    view = DIRS[d][0]
    p = [STYLE, DESIGN, f"DIRECTION: {view} ALL 8 figures face exactly this same direction; only the legs, arms and the "
         f"body's bob change from figure to figure. The body NEVER turns around between figures.", cycle(d),
         "LAYOUT: exactly 8 full-body figures in a 4 x 2 grid (4 columns, 2 rows): figures 1-4 in the top row left to right, "
         "5-8 in the bottom row left to right. Each figure centred in its own equal cell with clear empty space around it; "
         "no figure touches a cell edge or another figure. All 8 the same size, feet on the same baseline in their cell. "
         "No ground, no floor, no shadows, no text, no numbers, no grid lines, no borders.", BG[prov]]
    if ref:
        p.insert(0, f"The attached image shows THIS SAME CHARACTER walking in another direction ({ref}). Copy ONLY his design "
                    f"from it: face, hair, clothing, colours, proportions, art style, line weight and figure size. Do NOT copy "
                    f"its facing direction or body angle; this image is a NEW direction, described below.")
    return "\n\n".join(p)

def oneshot_prompt(prov):
    rows = " ".join(f"Row {i+1}: {d}: {DIRS[d][0].replace('Every figure', 'he')}" for i, d in enumerate(ORDER))
    return "\n\n".join([STYLE, DESIGN,
        "SPRITE SHEET: a grid of 8 rows x 8 columns = 64 small full-body figures of this one character, each centred in its "
        "own equal cell, none touching a cell edge or another figure, all the same size. Each ROW is one walking direction; "
        "each row's 8 columns, left to right, are the 8 frames of one complete walk cycle (two steps).",
        "ROWS (top to bottom): " + rows,
        "FRAMES in every row: 1 contact, the leading leg far forward and the other far back (widest stance); 2 down, weight on "
        "the front leg; 3 passing, the back foot lifted and swinging forward; 4 up, highest point; 5 contact with the OTHER leg "
        "forward (the opposite of 1); 6 down; 7 passing with the other foot lifted; 8 up. Frames 5-8 must NOT copy 1-4. "
        "Arms swing opposite to the legs; the body bobs.",
        "No ground, shadows, text, labels, numbers or grid lines.", BG[prov]])

if __name__ == "__main__":
    kind, prov = sys.argv[1], sys.argv[2]
    print(oneshot_prompt(prov) if kind == "oneshot" else dir_prompt(prov, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None))
