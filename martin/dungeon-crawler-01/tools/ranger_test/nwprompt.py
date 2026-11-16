import sys
mode, prov = sys.argv[1], sys.argv[2]
if mode == "grey":
    LL, RL, LA, RA = "the DARK GREY leg", "the LIGHT GREY leg", "the dark grey arm", "the light grey arm"
    key = "Dark grey limbs = his LEFT arm and leg; light grey limbs = his RIGHT arm and leg; the mid-grey block is the torso."
    clean = "The grey shades are only a pose guide, NOT colours: no flat grey mannequin parts may remain."
else:
    LL, RL, LA, RA = "the BLUE leg", "the ORANGE leg", "the TEAL arm", "the YELLOW arm"
    key = ("Each limb of the mannequin has its own colour so you can follow it from figure to figure: BLUE = his LEFT leg, "
           "ORANGE = his RIGHT leg, TEAL = his LEFT arm, YELLOW = his RIGHT arm, grey = torso and head.")
    clean = ("The colours are ONLY a pose guide: NONE of blue, orange, teal or yellow may appear anywhere in the painting; "
             "paint every limb in the character's own clothing colours.")
bg = ("Transparent background (remove the magenta)." if prov == "openai"
      else "Keep the flat solid pure magenta #FF00FF background; no floor, no shadows.")
print(f"""This image is a POSE GUIDE: 8 mannequins in a 4 x 2 grid showing one complete walk cycle, figures 1-4 on top and 5-8 below, left to right. Paint over EVERY mannequin, keeping each one's EXACT position, size and pose of legs, arms, torso and head. Do not move, add or remove any figure, and do not change any pose.

{key}

DIRECTION: every figure walks diagonally AWAY from the viewer toward the UPPER LEFT, exactly as the mannequins are turned: we see his BACK and his LEFT side; the face is hidden (at most a sliver of cheek). The body NEVER turns around between figures.

FOLLOW THE LEGS EXACTLY, they alternate:
1: {LL} reaches forward, {RL} stretched far back.
3: {LL} under the body; {RL} bent at the knee, foot lifted, swinging forward.
5: the OPPOSITE of 1: now {RL} reaches forward and {LL} is stretched far back. Figure 5 is NOT a copy of figure 1.
7: {RL} under the body; {LL} bent, foot lifted, swinging forward.
Figures 2, 4, 6, 8 are the in-between poses: copy them from the guide.
Arms swing opposite to the legs, following {LA} and {RA} exactly; the hands are at clearly different positions from figure to figure, open and EMPTY.

CHARACTER (identical in all 8): a lean young ranger/hunter, adult man about 25. Deep forest-green hooded cloak to mid-thigh, hood DOWN on his shoulders; short tousled auburn hair; brown leather jerkin laced over a cream linen shirt; dark leather bracers; wide brown belt with a pouch and a sheathed hunting knife at the hip; olive-brown trousers; knee-high scuffed brown leather boots. Hands EMPTY: NO bow, NO quiver, NO weapon held. Copy only the pose from the mannequins, not their shapes: give him natural human proportions and clothing.

STYLE: hand-drawn 2D game sprite art for an isometric RPG, clean dark ink outlines, painterly watercolour-and-gouache shading, light from the upper left. NOT pixel art, NOT 3D.

{clean}
{bg} No text, numbers or grid lines.""")
