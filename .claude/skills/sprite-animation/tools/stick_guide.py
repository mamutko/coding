"""Stick-figure pose guide: the algorithmic walk of walk_cycle.py (the original hero's gait, or any CHARS gait)
drawn as a true stick figure, in the layout of the mocap guides, so it paints with guide_prompt.py --stick and builds
with build_sheet.py.

  python stick_guide.py <DIR|all> <out_dir> [--char hero] [--frames 12] [--cols 6] [--cell 384x512]
  python stick_guide.py --stand <out.png>               # standing still, all 8 directions in a 4 x 2 grid
                         # (S SW W NW / N NE E SE), for the stand frame (stand_prompt, add_stand.py)
  python stick_guide.py <DIR|all> <out_dir> --halves     # also <DIR>-h1.png / <DIR>-h2.png: each half of the
                         # cycle (one step, frames/2 figures in a 3 x 2 grid) to paint on its own (join_halves.py)

The figure (learnings.md, "True stick figure"): thin round sticks, every part the SAME light grey (only lit from
the upper left, never darker for the far side: a darker far leg came out as a darker painted leg), a T at the hips
(a bar wider than real hips, HIP_T, with the legs hanging from its ends, so the two legs start well apart and their
order is easy to follow), a T at the shoulders with the arms hanging from its ends, one stick for the spine between
the two bars, a neck stick, a ball head with a nose bump showing where it faces, small balls at the joints and
hands, and a stick for each foot. Dark ink lines outline the figure and mark where one stick passes in front of
another (which leg is the near one). A stick figure reads as a pose guide only: less of it carries into the paint
than the shaded clay body of the first version (thin limbs and dark far legs did).

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
HIP_T = 0.17                             # half the hip bar (m): the legs hang from its ends (real hips: ~0.11)


def joints(t):
    """Named joints (local metres) of the walk_cycle gait at phase t, ground at y = 0."""
    segs, head, ground = wc.pose(t)
    P = lambda i, j: segs[i][j] - [0, ground, 0]
    J = dict(hipL=P(0, 0), kneeL=P(0, 1), ankL=P(1, 1), toeL=P(2, 1), hipR=P(3, 0), kneeR=P(3, 1), ankR=P(4, 1),
             toeR=P(5, 1), shL=P(6, 0), elL=P(6, 1), wrL=P(7, 1), fistL=P(8, 1), shR=P(9, 0), elR=P(9, 1),
             wrR=P(10, 1), fistR=P(11, 1), neck=P(13, 1))
    J["pelvis"] = (J["hipL"] + J["hipR"]) / 2
    # the hip T: the bar's ends HIP_T out from the pelvis; each leg starts at an end and the knee moves out half as
    # far, the foot stays where the gait puts it (the legs taper in a little, the feet keep a natural track)
    lat = J["hipL"] - J["hipR"]; lat[1] = 0; lat /= np.linalg.norm(lat)
    for s_, sg in (("L", 1), ("R", -1)):
        out = J["pelvis"] + lat * sg * HIP_T - J["hip" + s_]; out[1] = 0
        J["hip" + s_] = J["hip" + s_] + out
        J["knee" + s_] = J["knee" + s_] + out * 0.5
    h = head - [0, ground, 0]
    J["head"] = np.array([h[0], J["neck"][1] + 0.17, J["neck"][2] + 0.02])   # upright: straight above the neck
    return J


def spheres(J):
    """The stick figure as spheres (centre, radius, part id): sticks are rows of spheres; part ids tell where an ink
    line goes (0 the T bars and spine, 1 / 2 the left / right leg, 3 / 4 the left / right arm, 5 the head)."""
    out = []

    def stick(a, b, r, part, step=0.25):
        L = np.linalg.norm(b - a); n = max(2, int(L / (r * step)) + 1)
        for u in np.linspace(0, 1, n):
            out.append((a + (b - a) * u, r, part))
    R, J_ = 0.034, 0.046                                            # stick radius, joint ball radius
    for s, p in (("L", 1), ("R", 2)):
        stick(J["hip" + s], J["knee" + s], R, p); stick(J["knee" + s], J["ank" + s], R, p)
        f = J["toe" + s] - J["ank" + s]; f /= np.linalg.norm(f)
        stick(J["ank" + s] - f * 0.05, J["toe" + s], R, p)         # the foot, heel to toe
        for j in ("hip", "knee", "ank"):
            out.append((J[j + s], J_, p))
        q = 3 if s == "L" else 4
        stick(J["sh" + s], J["el" + s], R * 0.9, q); stick(J["el" + s], J["fist" + s], R * 0.9, q)
        out.append((J["sh" + s], J_, q)); out.append((J["el" + s], J_ * 0.9, q))
        out.append((J["fist" + s], 0.048, q))                       # the hand
    stick(J["hipL"], J["hipR"], R, 0)                               # the hip T bar
    stick(J["shL"], J["shR"], R, 0)                                 # the shoulder T bar
    sh_mid = (J["shL"] + J["shR"]) / 2
    stick(J["pelvis"], sh_mid, R * 1.1, 0)                          # the spine
    hd = J["head"]
    stick(sh_mid, hd - [0, 0.09, 0], R * 0.9, 5)                    # the neck
    out.append((hd, 0.11, 5))
    out.append((hd + [0, 0.012, 0.105], 0.03, 5))                   # nose: shows where the head faces
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
    shade = 0.40 + 0.70 * lam                                       # one grey everywhere: near and far alike
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


def stand_joints():
    """A relaxed standing pose (local metres, ground y = 0): legs straight under the hips, feet a little apart and
    turned out, weight even, arms hanging with a slight bend at the elbow, the head level. Same skeleton as the gait
    (and the same hip T: the legs hang from the bar's ends and taper in to the feet)."""
    J = {}
    ank_y, hip_y = 0.075, 0.95
    for s_, sg_ in (("L", -1), ("R", 1)):
        J["hip" + s_] = np.array([HIP_T * sg_, hip_y, 0.0])
        J["ank" + s_] = np.array([0.12 * sg_, ank_y, 0.0])
        J["knee" + s_] = (J["hip" + s_] + J["ank" + s_]) / 2 + [0, 0, 0.012]
        out = math.radians(9) * sg_                                   # toes turned out a little
        J["toe" + s_] = J["ank" + s_] + 0.17 * np.array([math.sin(out), -0.42, math.cos(out)])
        J["sh" + s_] = np.array([0.21 * sg_, 1.45, 0.0])
        J["el" + s_] = J["sh" + s_] + [0.03 * sg_, -0.29, -0.02]
        J["fist" + s_] = J["el" + s_] + [0.01 * sg_, -0.30, 0.05]
        J["wr" + s_] = J["fist" + s_] - [0, -0.05, 0.01]
    J["neck"] = np.array([0, 1.50, 0.02]); J["pelvis"] = (J["hipL"] + J["hipR"]) / 2
    J["head"] = np.array([0, 1.67, 0.03])
    m = min(J["toeL"][1], J["toeR"][1], J["ankL"][1] - 0.05)
    for k in J:
        J[k] = J[k] - [0, m - 0.03, 0]
    return J


NEAR = {"SW": "L", "W": "L", "NW": "L", "NE": "R", "E": "R", "SE": "R"}   # the side we see (S, N: none)


def leading(n, d=None, gap=0.12):
    """Per frame, the leg in front (its foot further forward by more than gap metres): 'L' / 'R', or '-' (passing);
    with a direction d of NEAR, 'near' / 'far' / '-'. guide_prompt.py --stick and review.py use it."""
    out = []
    for i in range(n):
        J = joints(i / n); dz = ball(J, "L")[2] - ball(J, "R")[2]
        s = "-" if abs(dz) < gap else ("L" if dz > 0 else "R")
        if d in NEAR and s != "-":
            s = "near" if s == NEAR[d] else "far"
        out.append(s)
    return out


def main():
    opt = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    wc.use(opt("--char", "hero"))
    if sys.argv[1] == "--stand":
        cw, ch = map(int, opt("--cell", "384x512").split("x")); gy = round(ch * 0.84, 2)
        stand = joints(0.25)
        ys = [wc.project(c, 0)[1] - r * math.cos(wc.ELEV) for c, r, _ in spheres(stand)]
        ye = [wc.project(c, 0)[1] + r for c, r, _ in spheres(stand)]
        scale = 0.818 * ch / (max(ye) - min(ys))
        sheet = np.zeros((2 * ch * SS, 4 * cw * SS, 3)); cov = np.zeros(sheet.shape[:2], bool)
        for j, d in enumerate(ROWS):
            img, fg = render(stand_joints(), (8 - ROWS.index(d)) % 8, scale, cw, ch, gy)
            r, c = divmod(j, 4)
            sheet[r * ch * SS:(r + 1) * ch * SS, c * cw * SS:(c + 1) * cw * SS] = img
            cov[r * ch * SS:(r + 1) * ch * SS, c * cw * SS:(c + 1) * cw * SS] = fg
        sheet[~cov] = [255, 0, 255]
        Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8)).resize((4 * cw, 2 * ch), Image.LANCZOS).save(sys.argv[2])
        print("stand ->", sys.argv[2]); return
    a = sys.argv[1]; out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
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
        if "--halves" in sys.argv:                                   # each step on its own sheet, 3 x 2
            hn = n // 2; hc = -(-hn // 2)
            for h in (1, 2):
                hs = np.zeros((2 * ch * SS, hc * cw * SS, 3)); hv = np.zeros((2 * ch * SS, hc * cw * SS), bool)
                for j in range(hn):
                    i = (h - 1) * hn + j; r, c = divmod(i, cols); rr, cc = divmod(j, hc)
                    hs[rr * ch * SS:(rr + 1) * ch * SS, cc * cw * SS:(cc + 1) * cw * SS] = sheet[r * ch * SS:(r + 1) * ch * SS, c * cw * SS:(c + 1) * cw * SS]
                    hv[rr * ch * SS:(rr + 1) * ch * SS, cc * cw * SS:(cc + 1) * cw * SS] = True
                hs[~hv] = [255, 0, 255]
                Image.fromarray(np.clip(hs, 0, 255).astype(np.uint8)).resize((hc * cw, 2 * ch), Image.LANCZOS).save(out / f"{d}-h{h}.png")
        print(d, "->", out / f"{d}.png", "cycle %.3f m (%.1f px), fig %.0f px" % (cyc, cyc * scale, fig_px))


if __name__ == "__main__":
    main()
