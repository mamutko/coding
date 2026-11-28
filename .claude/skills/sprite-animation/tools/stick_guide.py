"""Shaded stick-figure pose guide: the algorithmic walk of walk_cycle.py (the original hero's gait, or any CHARS
gait) drawn as ONE light-grey figure with round, lit volumes, in the layout of the mocap guides, so it paints
with guide_prompt.py --stick and builds with build_sheet.py.

  python stick_guide.py <DIR|all> <out_dir> [--char hero] [--frames 12] [--cols 6] [--cell 384x512]

Why (learnings.md, "Shaded stick guide"): the mocap mannequin's slim shapes, bent knees and lowered head carried
into the paintings; the colour-per-limb stick guide's colours bled into them. Here every part is the same grey,
and only lighting tells the parts apart: spheres swept along each bone (thick enough for a sturdy adult), Lambert
light from the upper left, the far side of the body darker, and dark ink lines where one part passes in front of
another and round the silhouette. The head is upright, with a nose bump showing which way it faces.

Writes <DIR>.png (cols x rows cells on flat magenta, frame 1 = left heel strike) and <DIR>.json, the sidecar
build_sheet.py and board.py read: grid, ground line, standing figure height (fig_px), ground covered per loop
(cycle_px, measured from the gait: the mean backward speed of the planted foot) and the feet per frame.
"""
import json, math, pathlib, sys
import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import walk_cycle as wc

ROWS = wc.ROWS
SS = 2                                   # supersampling
LIGHT = np.array([-0.55, -0.65, 0.52]); LIGHT /= np.linalg.norm(LIGHT)   # screen: x right, y down, z toward us
BASE = np.array([206.0, 206.0, 210.0])   # the clay grey
INK = np.array([62.0, 60.0, 66.0])
FAR_DARK = 0.75                          # the far leg and arm: this much darker in a side view (less on the diagonals)


def joints(t):
    """Named joints (local metres) of the walk_cycle gait at phase t, ground at y = 0."""
    segs, head, ground = wc.pose(t)
    P = lambda i, j: segs[i][j] - [0, ground, 0]
    J = dict(hipL=P(0, 0), kneeL=P(0, 1), ankL=P(1, 1), toeL=P(2, 1), hipR=P(3, 0), kneeR=P(3, 1), ankR=P(4, 1),
             toeR=P(5, 1), shL=P(6, 0), elL=P(6, 1), wrL=P(7, 1), fistL=P(8, 1), shR=P(9, 0), elR=P(9, 1),
             wrR=P(10, 1), fistR=P(11, 1), neck=P(13, 1))
    J["pelvis"] = (J["hipL"] + J["hipR"]) / 2
    h = head - [0, ground, 0]
    J["head"] = np.array([h[0], J["neck"][1] + 0.17, J["neck"][2] + 0.02])   # upright: straight above the neck
    return J


def spheres(J):
    """The body as spheres (centre, radius, part id): part ids tell where an ink line goes between parts."""
    out = []

    def bone(a, b, ra, rb, part, step=0.08):
        L = np.linalg.norm(b - a); n = max(2, int(L / (min(ra, rb) * step)) + 1)
        for u in np.linspace(0, 1, n):
            out.append((a + (b - a) * u, ra + (rb - ra) * u, part))
    for s, p in (("L", 1), ("R", 2)):
        bone(J["hip" + s], J["knee" + s], 0.095, 0.068, p)          # thigh
        bone(J["knee" + s], J["ank" + s], 0.066, 0.048, p)          # shin
        f = J["toe" + s] - J["ank" + s]; f /= np.linalg.norm(f)
        heel = J["ank" + s] - f * 0.045 + [0, -0.02, 0]
        bone(heel, J["toe" + s] - f * 0.02, 0.05, 0.042, p)        # foot, heel to toe
        q = 3 if s == "L" else 4
        bone(J["sh" + s], J["el" + s], 0.06, 0.05, q)             # upper arm
        bone(J["el" + s], J["wr" + s], 0.05, 0.04, q)             # forearm
        out.append((J["fist" + s], 0.055, q))                       # hand
    # torso: a rounded slab spanning hips and shoulders (chest a little deeper), then the neck and head
    inset = lambda p: J["neck"] + (p - J["neck"]) * [0.62, 1, 1]
    hl, hr, sl, sr = J["hipL"] * [0.8, 1, 1], J["hipR"] * [0.8, 1, 1], inset(J["shL"]), inset(J["shR"])
    sl, sr = sl - [0, 0.04, 0], sr - [0, 0.04, 0]
    for v in np.linspace(0, 1, 40):
        a, b = hl + (sl - hl) * v, hr + (sr - hr) * v
        r = 0.088 + 0.034 * math.sin(math.pi / 2 * min(1, v / 0.8)) ** 2   # waist to chest
        for u in np.linspace(0, 1, 12):
            out.append((a + (b - a) * u, r, 0))
    bone(J["shL"], J["shR"], 0.065, 0.065, 0)                       # shoulders
    bone(J["neck"] - [0, 0.04, 0], J["head"] - [0, 0.07, 0], 0.052, 0.052, 5)
    hd = J["head"]
    out.append((hd, 0.115, 5))
    out.append((hd + [0, -0.05, 0.03], 0.09, 5))                    # jaw
    out.append((hd + [0, 0.012, 0.105], 0.026, 5))                   # nose: shows where the head faces
    return out


def render(J, k, scale, cw, ch, gy):
    """One figure in a cw x ch cell (supersampled): colour image (float) and coverage."""
    W, H = cw * SS, ch * SS
    zb = np.full((H, W), -1e9); nx = np.zeros((H, W)); ny = np.zeros((H, W)); nz = np.zeros((H, W))
    part = np.full((H, W), -1, np.int8)
    yy, xx = np.mgrid[0:H, 0:W]
    s = scale * SS
    for c, r, p in spheres(J):
        X, Y, Z = wc.project(c, k)
        X, Y, Z, R = W / 2 + X * s, gy * SS + Y * s, Z * s, r * s
        x0, x1, y0, y1 = int(max(0, X - R - 1)), int(min(W, X + R + 2)), int(max(0, Y - R - 1)), int(min(H, Y + R + 2))
        if x0 >= x1 or y0 >= y1:
            continue
        dx, dy = xx[y0:y1, x0:x1] - X, yy[y0:y1, x0:x1] - Y
        d2 = dx * dx + dy * dy
        inside = d2 < R * R
        dz = np.sqrt(np.maximum(R * R - d2, 0))
        z = Z + dz
        win = inside & (z > zb[y0:y1, x0:x1])
        zb[y0:y1, x0:x1][win] = z[win]
        nx[y0:y1, x0:x1][win] = dx[win] / R; ny[y0:y1, x0:x1][win] = dy[win] / R; nz[y0:y1, x0:x1][win] = dz[win] / R
        part[y0:y1, x0:x1][win] = p
    fg = part >= 0
    # normals from the (slightly smoothed) depth surface, so the swept spheres read as one smooth body; the
    # spheres' own normals at the silhouette, where the depth gradient is unreliable
    zs = np.where(fg, zb, 0.0); m = fg.astype(float)
    for _ in range(2):
        zs = sum(np.roll(np.roll(zs, a_, 0), b_, 1) for a_ in (-1, 0, 1) for b_ in (-1, 0, 1))
        m2 = sum(np.roll(np.roll(m, a_, 0), b_, 1) for a_ in (-1, 0, 1) for b_ in (-1, 0, 1))
        zs = np.where(m2 > 0, zs / np.maximum(m2, 1), 0); m = fg.astype(float)
    gyz, gxz = np.gradient(zs)
    inner = fg.copy()
    for ax in (0, 1):
        for sh in (2, -2):
            inner &= np.roll(fg, sh, ax)
    gn = np.sqrt(gxz ** 2 + gyz ** 2 + 1)
    inner &= gn < 4
    nx = np.where(inner, -gxz / gn, nx); ny = np.where(inner, -gyz / gn, ny); nz = np.where(inner, 1 / gn, nz)
    lam = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    zf = zb[fg]; zmid, zr = np.median(zf), 0.35 * s                  # depth: the far side of the body darker
    depth = np.zeros((H, W)); depth[fg] = np.clip((zb[fg] - zmid) / zr, -1, 1)
    shade = (0.30 + 0.75 * lam) * (0.84 + 0.16 * depth)
    # the FAR leg and arm a clearly darker grey (FAR_DARK): in a side view the two legs otherwise have the same
    # outline in figure 1 and in figure 7, and the model painted the same leg in front in both halves of the stride
    # (hero-6 E and W, first try). How far a side is from us: the depth of the character's right vector.
    rd = wc.project(np.array([1.0, 0, 0]), k)[2] - wc.project(np.zeros(3), k)[2]
    far = (1, 3) if rd > 0 else (2, 4)                               # parts: 1 / 3 left leg / arm, 2 / 4 right
    if abs(rd) > 0.2:
        shade = np.where(np.isin(part, far), shade * (1 - FAR_DARK * abs(rd)), shade)
    img = BASE[None, None, :] * shade[..., None]
    # ink: the silhouette, and where one part passes in front of another (a depth step, or a part change)
    ink = np.zeros((H, W), bool)
    for ax in (0, 1):
        for sh in (1, -1):
            zn = np.roll(zb, sh, ax); pn = np.roll(part, sh, ax); fn = np.roll(fg, sh, ax)
            step = fg & fn & ((zn - zb) > 0.05 * s) & ((pn != part) | ((zn - zb) > 0.12 * s))
            ink |= step | (fg & ~fn)
    for _ in range(max(1, SS // 2)):                                 # a little thicker (numpy only)
        ink = ink | np.roll(ink, 1, 0) | np.roll(ink, -1, 0) | np.roll(ink, 1, 1) | np.roll(ink, -1, 1)
    ink &= fg
    img[ink] = INK
    return img, fg


def feet_px(J, k, scale):
    """[left ball, right ball] screen px from the cell centre and ground line, and left minus right height in px."""
    out = []
    for s in ("L", "R"):
        ball = J["ank" + s] + (J["toe" + s] - J["ank" + s]) * 0.7
        X, Y, _ = wc.project(ball, k)
        out.append([round(X * scale, 1), round(Y * scale, 1)])
    return out


def planted(t):
    """Left minus right 'height' for build_sheet (< 0: the left foot is planted): from the gait's phase, the foot
    moving backward is planted; when both are (double support), the lower one."""
    bl, br = back_speed(t, "L") > 0, back_speed(t, "R") > 0
    if bl != br:
        return -10.0 if bl else 10.0
    J = joints(t)
    return round((ball(J, "L")[1] - ball(J, "R")[1]) * 100, 1)


def ball(J, s):
    return J["ank" + s] + (J["toe" + s] - J["ank" + s]) * 0.7


def back_speed(t, s, dt=1e-3):
    """How fast foot s moves backward relative to the pelvis at phase t (metres per loop; > 0: backward)."""
    return (ball(joints(t - dt), s)[2] - ball(joints(t + dt), s)[2]) / (2 * dt)


def cycle_m(n=2400):
    """Ground covered in one loop (metres): the mean backward speed of a foot while it moves backward (its stance).
    The algorithmic gait lets the swinging foot dip as low as the planted one, so 'the lowest foot' won't do."""
    zs = [ball(joints(i / n), "L")[2] for i in range(n + 1)]
    back = [zs[i] - zs[i + 1] for i in range(n)]
    moving = [b for b in back if b > 0]
    return sum(moving) / (len(moving) / n)


def main():
    a = sys.argv[1]; out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    wc.use(opt("--char", "hero"))
    n, cols = int(opt("--frames", 12)), int(opt("--cols", 6)); rows = -(-n // cols)
    cw, ch = map(int, opt("--cell", "384x512").split("x"))
    gy = round(ch * 0.84, 2)                                          # ground line in the cell
    # scale: a standing figure (feet together, S view) is about 0.82 of the cell tall, like the mocap guides
    stand = joints(0.25)
    ys = [wc.project(c, 0)[1] - r * math.cos(wc.ELEV) for c, r, _ in spheres(stand)]
    ye = [wc.project(c, 0)[1] + r for c, r, _ in spheres(stand)]
    h_m = max(ye) - min(ys)
    scale = 0.818 * ch / h_m
    fig_px = round(h_m * scale, 2)
    cyc = cycle_m()
    for d in (ROWS if a == "all" else a.split(",")):
        k = (8 - ROWS.index(d)) % 8
        sheet = np.zeros((rows * ch * SS, cols * cw * SS, 3)); cov = np.zeros((rows * ch * SS, cols * cw * SS), bool)
        feet = []
        for i in range(n):
            J = joints(i / n)
            img, fg = render(J, k, scale, cw, ch, gy)
            r, c = divmod(i, cols)
            sheet[r * ch * SS:(r + 1) * ch * SS, c * cw * SS:(c + 1) * cw * SS] = img
            cov[r * ch * SS:(r + 1) * ch * SS, c * cw * SS:(c + 1) * cw * SS] = fg
            feet.append(feet_px(J, k, scale) + [planted(i / n)])
        sheet[~cov] = [255, 0, 255]
        im = Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8)).resize((cols * cw, rows * ch), Image.LANCZOS)
        im.save(out / f"{d}.png")
        side = {"cols": cols, "rows": rows, "frames": n, "dirs": [d], "cell": [cw, ch],
                "clip": f"walk_cycle.py gait '{wc.G['name']}' (algorithmic stick figure, shaded)", "ground_y": gy,
                "fig_px": fig_px, "fit": 1.0, "shaded": True, "stick": True, "cycle_px": round(cyc * scale, 2),
                "feet": feet,
                "note": "ground_y: ground line, px from the cell top; fig_px: a standing figure's height in px; cycle_px: "
                        "ground covered in one loop, in px of a screen-horizontal ground line; feet: per frame [left ball, "
                        "right ball] in px from the cell centre and the ground line, then < 0 when the left foot is planted, > 0 the right"}
        (out / f"{d}.json").write_text(json.dumps(side, indent=1))
        print(d, "->", out / f"{d}.png", "cycle %.3f m (%.1f px), fig %.0f px" % (cyc, cyc * scale, fig_px))


if __name__ == "__main__":
    main()
