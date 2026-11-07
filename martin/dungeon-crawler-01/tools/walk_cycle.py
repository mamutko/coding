"""Walk-cycle pipeline (hero, skeleton, ghoul): 3D stick-figure pose guides / placeholders + sheet builder.

  python walk_cycle.py guide <CHAR> <DIR> <out.png> [--magenta] [--mannequin]  # 4x2 pose guide
  python walk_cycle.py build <CHAR> <raw_dir> <out_dir>  # assemble assets/<CHAR>.webp + update meta.json
  python walk_cycle.py placeholders <CHAR> <out.png>     # preview: all 8 directions as stick figures

CHAR is a key of CHARS (per-character gait and frame settings). DIR is one of S SW W NW N (the five
"base" directions). SE, E and NE are horizontal mirrors of SW, W and NW. For each base direction,
build uses raw_dir/<CHAR>_walk_<DIR>.png (an AI image with 8 frames in a 4x2 grid on flat magenta)
if it exists, otherwise a stick-figure placeholder.

The walk cycle has 8 frames covering a full stride (two steps):
  0 left foot forward (contact)  1 down  2 passing  3 up
  4 right foot forward (contact) 5 down  6 passing  7 up
"""
import json, math, sys, pathlib
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

FRAMES = 8
FH = 152                    # default output frame height (width is per character; fh / foot_y override)
FOOT_Y = 128                # default ground point (entity position) inside the frame; feet nearer the camera hang below it
# Gait settings per character. Angles in degrees. arm_amp / arm_off / elbow are (left, right):
# swing amplitude, constant forward offset of the upper arm, and base elbow bend.
CHARS = {
    "hero":     dict(fw=144, idle=3, fpt=5, lean=4, crouch=0, hip_amp=24, arm_amp=(20, 20), arm_off=(0, 0),
                     elbow=(18, 18)),
    # shield on the left forearm held in front, sword in the right hand with a short swing
    "skeleton": dict(fw=176, idle=3, fpt=5, lean=4, crouch=0, hip_amp=22, arm_amp=(5, 12), arm_off=(12, 4),
                     elbow=(75, 28)),
    # hunched and lurching: strong forward lean, bent knees, shorter stride, arms dangling in front
    # taller frame: seen from behind (N, NW) the hunched figure leans away and stands taller on screen
    "ghoul":    dict(fw=160, fh=162, foot_y=138, idle=3, fpt=5.5, lean=25, crouch=24, hip_amp=19, arm_amp=(14, 14), arm_off=(8, 8),
                     elbow=(14, 14)),
}
G = dict(CHARS["hero"])     # active character's settings (set by use())


def use(name):
    global FH, FOOT_Y
    G.clear(); G.update(CHARS[name]); G["name"] = name
    FH, FOOT_Y = G.get("fh", 152), G.get("foot_y", 128)
ELEV = math.radians(30)     # 2:1 dimetric camera elevation
PX_PER_M = 118 / (1.75 * math.cos(ELEV))   # knight ~118 px tall on screen
# sheet row -> screen direction; row r faces ground angle k*45deg, k = (8 - r) % 8 (k: 0=S, 1=SE, 2=E, ...)
ROWS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
MIRROR = {"SE": "SW", "E": "W", "NE": "NW"}
BASE = ["S", "SW", "W", "NW", "N"]
LEFT, RIGHT, MID = (40, 110, 230), (240, 120, 20), (90, 90, 90)
STYLE = {"thick": 1.0, "left": LEFT, "right": RIGHT, "mid": MID}   # guide --mannequin swaps in greys


# ---------------------------------------------------------------- 3D stick figure ----------
def pose(t):
    """Joint positions (local: x = character's right, y = up, z = forward), metres, for phase t in [0,1)."""
    cr = math.radians(G["crouch"])      # constant knee bend; half of it is taken up at the hip

    def leg(side, p):
        hip_ang = math.radians(G["hip_amp"]) * math.cos(2 * math.pi * p) + cr / 2  # + = forward
        swing = max(0.0, -math.sin(2 * math.pi * (p + 0.04)))                      # 1 just before mid-swing
        knee_ang = math.radians(6 + 46 * swing ** 1.3) + cr
        hip = np.array([0.11 * side, 0.95, 0.0])
        knee = hip + 0.46 * np.array([0, -math.cos(hip_ang), math.sin(hip_ang)])
        sh = hip_ang - knee_ang
        ankle = knee + 0.46 * np.array([0, -math.cos(sh), math.sin(sh)])
        toe_ang = sh + math.radians(90) + cr / 2 - math.radians(12 * swing)
        toe = ankle + 0.17 * np.array([0, -math.cos(toe_ang), math.sin(toe_ang)])
        return hip, knee, ankle, toe

    c = math.cos(2 * math.pi * t)          # +1 at left-foot contact, -1 at right-foot contact
    s_ = math.sin(2 * math.pi * t)         # +1 mid-stance on the left leg, -1 on the right leg

    def yaw(p, ang):  # rotate about the vertical body axis; + turns the left side forward
        return np.array([p[0] * math.cos(ang) + p[2] * math.sin(ang), p[1], -p[0] * math.sin(ang) + p[2] * math.cos(ang)])

    # upper body: shoulders counter-rotate against the hips, weight shifts over the stance leg,
    # a slight constant forward lean, and the head stays a little steadier than the shoulders
    pelvis_yaw, shoulder_yaw = math.radians(6) * c, -math.radians(8) * c
    sway = -0.035 * s_                     # toward the stance leg (left = -x)
    lean = math.radians(G["lean"])

    def upper(p, follow=1.0):              # p relative to the pelvis centre, upper-body joints
        q = yaw(p, shoulder_yaw * follow)
        q[0] += sway * follow
        dy, dz = q[1] - 0.95, q[2]         # lean: rotate forward about the hip axis
        q[1] = 0.95 + dy * math.cos(lean) - dz * math.sin(lean)
        q[2] = dy * math.sin(lean) + dz * math.cos(lean)
        return q

    def arm(side, p):
        i = 0 if side < 0 else 1
        amp = math.radians(G["arm_amp"][i])
        a = -amp * math.cos(2 * math.pi * p) + math.radians(G["arm_off"][i])     # opposite to same-side leg
        sh = upper(np.array([0.21 * side, 1.45, 0.0]))
        el = sh + 0.30 * np.array([0, -math.cos(a), math.sin(a)])
        fwd = max(0.0, -math.cos(2 * math.pi * p))                                 # 1 when the arm is fully forward
        b = a + math.radians(G["elbow"][i] + 14 * fwd)                              # elbow bends more in front
        wr = el + 0.28 * np.array([0, -math.cos(b), math.sin(b)])
        fist = wr + 0.06 * np.array([0, -math.cos(b), math.sin(b)])
        return sh, el, wr, fist

    def hip_pt(side):
        q = yaw(np.array([0.11 * side, 0.95, 0.0]), pelvis_yaw)
        q[0] += sway * 0.5
        return q

    L, R = leg(-1, t), leg(1, t + 0.5)
    # move each leg so it hangs from the rotated/shifted hip joint
    L = tuple(p + (hip_pt(-1) - L[0]) for p in L)
    R = tuple(p + (hip_pt(1) - R[0]) for p in R)
    La, Ra = arm(-1, t), arm(1, t + 0.5)
    pelvis = (L[0] + R[0]) / 2
    neck = upper(np.array([0, 1.50, 0.03]))
    head = upper(np.array([0, 1.64, 0.04]), 0.6)
    segs = [  # (a, b, colour, width)
        (L[0], L[1], LEFT, 7), (L[1], L[2], LEFT, 6), (L[2], L[3], LEFT, 5),
        (R[0], R[1], RIGHT, 7), (R[1], R[2], RIGHT, 6), (R[2], R[3], RIGHT, 5),
        (La[0], La[1], LEFT, 6), (La[1], La[2], LEFT, 5), (La[2], La[3], LEFT, 9),
        (Ra[0], Ra[1], RIGHT, 6), (Ra[1], Ra[2], RIGHT, 5), (Ra[2], Ra[3], RIGHT, 9),
        (L[0], R[0], MID, 8), (pelvis, neck, MID, 16), (La[0], Ra[0], MID, 8),
    ]
    pts = [p for s in segs for p in s[:2]]
    ground = min(p[1] for p in pts)
    return segs, head, ground


def project(p, k):
    """local -> screen (x right, y down, depth toward camera) for ground facing angle k*45deg."""
    a = math.radians(45 * k)
    f = np.array([math.sin(a), 0, math.cos(a)])          # facing, Z = toward camera
    r = np.array([-f[2], 0, f[0]])                       # character's right = f x up
    w = p[0] * r + p[1] * np.array([0, 1, 0]) + p[2] * f
    return (w[0], -w[1] * math.cos(ELEV) + w[2] * math.sin(ELEV), w[2] * math.cos(ELEV) + w[1] * math.sin(ELEV))


def draw_figure(dr, k, t, cx, foot_y, scale, ss):
    segs, head, ground = pose(t)
    hd = None
    items = []
    for a, b, col, wid in segs:
        a = a - [0, ground, 0]; b = b - [0, ground, 0]
        pa, pb = project(a, k), project(b, k)
        items.append(((pa[2] + pb[2]) / 2, "seg", pa, pb, col, wid))
    hp = project(head - [0, ground, 0], k)
    nose = project(head - [0, ground, 0] + [0, -0.01, 0.12], k)
    items.append((hp[2], "head", hp, nose, MID, 0))
    recol = {LEFT: STYLE["left"], RIGHT: STYLE["right"], MID: STYLE["mid"]}
    for depth, kind, pa, pb, col, wid in sorted(items, key=lambda i: i[0]):
        col = recol[col]; wid = wid * STYLE["thick"]
        X = lambda p: (cx + p[0] * scale, foot_y + p[1] * scale)
        if kind == "seg":
            lw = wid / 7 * 0.075 * scale
            dr.line([X(pa), X(pb)], fill=col, width=max(1, round(lw)))
            for p in (pa, pb):
                x, y = X(p); rr = lw / 2
                dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
        else:
            x, y = X(pa); rr = 0.11 * scale
            dr.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(205, 205, 205), outline=MID, width=max(1, round(2 * ss)))
            nx, ny = X(pb)  # face marker: shows which way the head is looking
            if pb[2] > pa[2] - 0.02:
                dr.ellipse([nx - rr * 0.35, ny - rr * 0.35, nx + rr * 0.35, ny + rr * 0.35], fill=(200, 30, 30))


def metrics(k, t):
    """(head-top y, bbox height) in output px, relative to the ground point, for one pose (bottom = top + height)."""
    segs, head, ground = pose(t)
    ys = [project(p - [0, ground, 0], k)[1] for s_ in segs for p in s_[:2]]
    top = project(head - [0, ground, 0], k)[1] - 0.11
    return top * PX_PER_M, (max(ys) + 0.04 - top) * PX_PER_M


def render_placeholder(k, t):
    ss = 4
    FW = G["fw"]
    im = Image.new("RGBA", (FW * ss, FH * ss), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    draw_figure(dr, k, t, FW * ss / 2, FOOT_Y * ss, PX_PER_M * ss, ss)
    return im.resize((FW, FH), Image.LANCZOS)


def guide(dirname, out, bg=(255, 255, 255), shadow=True):
    k = (8 - ROWS.index(dirname)) % 8
    cw, ch, ss = 300, 440, 2
    im = Image.new("RGB", (cw * 4 * ss, ch * 2 * ss), bg)
    dr = ImageDraw.Draw(im)
    scale = 360 * ss / (1.75 * math.cos(ELEV))
    for i in range(FRAMES):
        r, c = divmod(i, 4)
        cx, fy = (c + 0.5) * cw * ss, (r * ch + ch - 70) * ss
        if shadow:
            dr.ellipse([cx - 60 * ss, fy - 14 * ss, cx + 60 * ss, fy + 14 * ss], fill=(228, 228, 228))
        draw_figure(dr, k, i / FRAMES, cx, fy, scale, ss)
    im.resize((cw * 4, ch * 2), Image.LANCZOS).save(out)
    print("guide", dirname, "->", out)


# ---------------------------------------------------------------- AI image -> frames -------
KEY = np.array([255.0, 0.0, 255.0])


def key_out(img):
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = np.minimum(r, b) - g
    alpha = np.clip((200.0 - m) / (200.0 - 70.0), 0, 1)
    col = np.clip((a - (1 - alpha)[..., None] * KEY) / np.maximum(alpha, 1e-3)[..., None], 0, 255)
    spill = np.maximum(np.minimum(col[..., 0], col[..., 2]) - col[..., 1] - 4, 0)
    col[..., 0] -= spill; col[..., 2] -= spill
    alpha[alpha < 0.06] = 0
    return np.dstack([col, alpha * 255]).astype(np.uint8)


def components(mask, step=3):
    """Connected components on a downsampled mask -> (full-res label image, sizes)."""
    h, w = mask.shape
    hs, ws = (h + step - 1) // step, (w + step - 1) // step
    pad = np.zeros((hs * step, ws * step), bool); pad[:h, :w] = mask
    small = pad.reshape(hs, step, ws, step).any(axis=(1, 3))
    lab = np.zeros((hs, ws), np.int32); sizes = [0]
    for y0, x0 in zip(*np.nonzero(small)):
        if lab[y0, x0]:
            continue
        n = len(sizes); sizes.append(0); lab[y0, x0] = n; q = deque([(y0, x0)])
        while q:
            y, x = q.popleft(); sizes[n] += 1
            for yy in (y - 1, y, y + 1):
                for xx in (x - 1, x, x + 1):
                    if 0 <= yy < hs and 0 <= xx < ws and small[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = n; q.append((yy, xx))
    full = np.repeat(np.repeat(lab, step, 0), step, 1)[:h, :w] * mask
    return full, np.array(sizes)


def extract_frames(path):
    """8 RGBA crops (whole figures, never cut by a grid line), ordered like the 4x2 layout."""
    arr = key_out(Image.open(path))
    H, W = arr.shape[:2]
    mask = arr[..., 3] > 20
    lab, sizes = components(mask)
    big = sizes.max()
    cells = [[] for _ in range(FRAMES)]
    for n in range(1, len(sizes)):
        if sizes[n] < big * 0.02:
            continue  # specks
        ys, xs = np.nonzero(lab == n)
        c = min(3, int(xs.mean() / (W / 4))); r = min(1, int(ys.mean() / (H / 2)))
        cells[r * 4 + c].append(n)
    frames = []
    for i, comps in enumerate(cells):
        if not comps:
            raise SystemExit(f"{path}: no figure found in cell {i}")
        keep = np.isin(lab, comps)
        rgba = arr.copy(); rgba[~keep, 3] = 0
        # faint fringe pixels (alpha<=20) next to the figure are kept: dilate keep by the label step
        ys, xs = np.nonzero(keep)
        frames.append(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    return frames


def place(frame, scale, bottom):
    """Scale a figure crop into an FWxFH frame. Vertical: the lowest pixel (the foot nearest the camera)
    goes where the 3D pose model puts its lowest foot for this pose, relative to the ground point FOOT_Y;
    the AI drawing supplies the body bob. Horizontal: head + shoulders centred."""
    FW = G["fw"]
    im = Image.fromarray(frame, "RGBA")
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    a = np.asarray(im)[..., 3].astype(np.float32)
    top = a[: max(1, int(a.shape[0] * 0.45))]          # head + shoulders: stable while legs swing
    cols = top.sum(0)
    cx = (cols * np.arange(len(cols))).sum() / max(cols.sum(), 1)
    out = Image.new("RGBA", (FW, FH))
    x, y = round(FW / 2 - cx), round(FOOT_Y + bottom - im.height)
    if x < 0 or y < 0 or x + im.width > FW or y + im.height > FH:
        print("  warning: frame clipped", (x, y, im.width, im.height))
    out.paste(im, (x, y), im)
    return out


def build(raw, out):
    name, FW = G["name"], G["fw"]
    rows = {}
    for d in BASE:
        k = (8 - ROWS.index(d)) % 8
        src = raw / f"{name}_walk_{d}.png"
        if src.exists():
            fr = extract_frames(src)
            m = [metrics(k, i / FRAMES) for i in range(FRAMES)]
            ratios = sorted(m[i][1] / fr[i].shape[0] for i in range(FRAMES))
            scale = ratios[FRAMES // 2]                 # one scale per direction (median)
            rows[d] = [place(fr[i], scale, m[i][0] + m[i][1]) for i in range(FRAMES)]
            print(d, "from", src.name, "heights", [f.shape[0] for f in fr], "scale %.3f" % scale)
        else:
            rows[d] = [render_placeholder(k, i / FRAMES) for i in range(FRAMES)]
            print(d, "placeholder")
    for m, b in MIRROR.items():
        rows[m] = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in rows[b]]
    sheet = Image.new("RGBA", (FW * FRAMES, FH * 8))
    for r, d in enumerate(ROWS):
        for c, f in enumerate(rows[d]):
            sheet.paste(f, (c * FW, r * FH))
    sheet.save(out / f"{name}.webp", quality=90, method=6)
    meta_p = out / "meta.json"
    meta = json.loads(meta_p.read_text())
    meta["characters"][name] = {"fw": FW, "fh": FH, "frames": FRAMES, "idle": G["idle"], "footY": FOOT_Y,
                                "fpt": G["fpt"]}
    meta_p.write_text(json.dumps(meta, indent=1))
    print(name, meta["characters"][name])


if __name__ == "__main__":
    cmd = sys.argv[1]
    use(sys.argv[2])
    FW = G["fw"]
    if cmd == "guide":
        magenta = "--magenta" in sys.argv
        if "--mannequin" in sys.argv:
            STYLE.update(thick=1.9, left=(55, 55, 60), right=(175, 175, 180), mid=(115, 115, 120))
        guide(sys.argv[3], sys.argv[4], (255, 0, 255) if magenta else (255, 255, 255), not magenta)
    elif cmd == "build":
        build(pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4]))
    elif cmd == "placeholders":  # preview: all 8 directions as placeholders
        out = pathlib.Path(sys.argv[3]); sheet = Image.new("RGBA", (FW * 8, FH * 8), (60, 60, 60, 255))
        for r, d in enumerate(ROWS):
            for i in range(FRAMES):
                f = render_placeholder((8 - r) % 8, i / FRAMES); sheet.alpha_composite(f, (i * FW, r * FH))
        sheet.save(out)
