"""Render a pose guide from a real 3D walk (Quaternius Universal Animation Library, CC0), in exactly the format of
`walk_cycle.py guide hero <DIR> out.png --magenta --limbs`: 1200 x 880, flat magenta, 4 x 2 cells of 300 x 440,
the body centred in each cell and standing on a ground line 70 px above the cell bottom, ~360 px tall.

  python render_guide.py <UAL1_Standard.glb> <DIR> <out.png> [--clip Walk_Loop] [--frames-dir DIR]

Pure numpy + PIL (no Blender / three.js): parses the GLB, samples the clip at 8 evenly spaced phases of one full
cycle starting at the LEFT heel strike, skins the mesh (linear blend skinning), removes root drift, colours each
triangle by the limb its vertices are mostly weighted to, and draws it with walk_cycle.project() (30 deg camera).
Use the non-root-motion file (UAL1_Standard.glb, not _RM).
"""
import json, math, struct, sys, pathlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import walk_cycle as wc  # noqa: E402

BLUE, ORANGE, TEAL, YELLOW = (30, 90, 230), (245, 130, 0), (0, 190, 200), (245, 215, 0)
GREY, HEAD, RED = (120, 120, 125), (205, 205, 205), (200, 30, 30)
FRAMES = 8


# ------------------------------------------------------------------ glTF -----------------
def load_glb(path):
    b = pathlib.Path(path).read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    off = 20 + n
    blen = struct.unpack("<I", b[off:off + 4])[0]
    binc = b[off + 8: off + 8 + blen]
    return j, binc


CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def accessor(j, binc, i):
    a = j["accessors"][i]
    bv = j["bufferViews"][a["bufferView"]]
    dt, nc = np.dtype(CT[a["componentType"]]), NC[a["type"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", dt.itemsize * nc)
    raw = np.frombuffer(binc, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * nc, offset=start)
    rows = np.lib.stride_tricks.as_strided(raw, (a["count"], dt.itemsize * nc), (stride, 1))
    out = np.ascontiguousarray(rows).view(dt).reshape(a["count"], nc)
    if a.get("normalized"):
        out = out.astype(np.float32) / np.iinfo(dt).max
    return out


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs(t, r, s):
    m = np.eye(4)
    m[:3, :3] = quat_mat(r) * np.asarray(s)
    m[:3, 3] = t
    return m


class Rig:
    def __init__(self, path, clip):
        j, binc = load_glb(path)
        self.j = j
        self.nodes = j["nodes"]
        self.parent = {c: i for i, n in enumerate(self.nodes) for c in n.get("children", [])}
        mi = next(i for i, n in enumerate(self.nodes) if "mesh" in n and "skin" in n)
        mesh, skin = j["meshes"][self.nodes[mi]["mesh"]], j["skins"][self.nodes[mi]["skin"]]
        self.joints = skin["joints"]
        self.ibm = accessor(j, binc, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        P, J, W, I = [], [], [], []
        for prim in mesh["primitives"]:
            at = prim["attributes"]
            base = sum(len(p) for p in P)
            P.append(accessor(j, binc, at["POSITION"]).astype(np.float64))
            J.append(accessor(j, binc, at["JOINTS_0"]).astype(np.int64))
            W.append(accessor(j, binc, at["WEIGHTS_0"]).astype(np.float64))
            I.append(accessor(j, binc, prim["indices"]).reshape(-1, 3).astype(np.int64) + base)
        self.pos, self.jnt, self.wt, self.tri = map(np.concatenate, (P, J, W, I))
        self.wt /= self.wt.sum(1, keepdims=True)
        anim = next(a for a in j["animations"] if a["name"] == clip)
        self.tracks = {}
        self.dur = 0.0
        for ch in anim["channels"]:
            s = anim["samplers"][ch["sampler"]]
            tin = accessor(j, binc, s["input"])[:, 0].astype(np.float64)
            vout = accessor(j, binc, s["output"]).astype(np.float64)
            self.tracks[(ch["target"]["node"], ch["target"]["path"])] = (tin, vout)
            self.dur = max(self.dur, tin[-1])
        self.name_idx = {n.get("name"): i for i, n in enumerate(self.nodes)}

    def sample(self, node, path, t, default):
        tr = self.tracks.get((node, path))
        if tr is None:
            return np.asarray(default, float)
        tin, v = tr
        if t <= tin[0]:
            return v[0]
        if t >= tin[-1]:
            return v[-1]
        k = np.searchsorted(tin, t) - 1
        u = (t - tin[k]) / (tin[k + 1] - tin[k])
        a, b = v[k], v[k + 1]
        if path == "rotation":                       # nlerp, shortest arc
            if np.dot(a, b) < 0:
                b = -b
            q = a * (1 - u) + b * u
            return q / np.linalg.norm(q)
        return a * (1 - u) + b * u

    def globals_(self, t):
        cache = {}

        def g(i):
            if i in cache:
                return cache[i]
            n = self.nodes[i]
            if "matrix" in n:
                m = np.array(n["matrix"]).reshape(4, 4).T
            else:
                m = trs(self.sample(i, "translation", t, n.get("translation", [0, 0, 0])),
                        self.sample(i, "rotation", t, n.get("rotation", [0, 0, 0, 1])),
                        self.sample(i, "scale", t, n.get("scale", [1, 1, 1])))
            if i in self.parent:
                m = g(self.parent[i]) @ m
            cache[i] = m
            return m
        return g

    def skin(self, t):
        g = self.globals_(t)
        mats = np.stack([g(ji) @ self.ibm[k] for k, ji in enumerate(self.joints)])   # (J,4,4)
        hp = np.c_[self.pos, np.ones(len(self.pos))]
        out = np.zeros((len(self.pos), 3))
        for c in range(4):
            m = mats[self.jnt[:, c]]                                                 # (V,4,4)
            out += self.wt[:, c:c + 1] * np.einsum("vij,vj->vi", m, hp)[:, :3]
        return out, g

    def joint_pos(self, g, name):
        return g(self.name_idx[name])[:3, 3]


def limb_colour(name):
    n = name.lower()
    side = "l" if n.endswith("_l") else "r" if n.endswith("_r") else ""
    if any(k in n for k in ("thigh", "calf", "foot", "ball")):
        return BLUE if side == "l" else ORANGE
    if any(k in n for k in ("upperarm", "lowerarm", "hand", "index", "middle", "pinky", "ring", "thumb")):
        return TEAL if side == "l" else YELLOW
    if n == "head":
        return HEAD
    return GREY                                       # root, pelvis, spine, neck, clavicles


# ------------------------------------------------------------------ render ---------------
def main():
    glb, dirname, out = sys.argv[1], sys.argv[2], sys.argv[3]
    clip = sys.argv[sys.argv.index("--clip") + 1] if "--clip" in sys.argv else "Walk_Loop"
    rig = Rig(glb, clip)
    names = [rig.nodes[ji].get("name", "") for ji in rig.joints]
    jcol = [limb_colour(n) for n in names]
    # each triangle takes the colour of the bone its three vertices are most weighted to (summed)
    V = len(rig.pos)
    acc = np.zeros((V, len(rig.joints)))
    for c in range(4):
        np.add.at(acc, (np.arange(V), rig.jnt[:, c]), rig.wt[:, c])
    tri_j = acc[rig.tri].sum(1).argmax(1)
    tri_col = np.array([jcol[k] for k in tri_j], float)

    # character frame from the rest skeleton: up = +Y; right = thigh_r - thigh_l; forward from the walk itself
    _, g0 = rig.skin(0.0)
    right = rig.joint_pos(g0, "thigh_r") - rig.joint_pos(g0, "thigh_l")
    right[1] = 0; right /= np.linalg.norm(right)
    up = np.array([0.0, 1.0, 0.0])
    fwd = np.cross(right, up)                         # candidate; sign checked below against the stance foot
    N = 240
    ts = np.linspace(0, rig.dur, N, endpoint=False)
    gl = [rig.globals_(t) for t in ts]
    rel = lambda g, b: rig.joint_pos(g, b) - rig.joint_pos(g, "pelvis")
    lf = np.array([rel(g, "foot_l") @ fwd for g in gl])
    lh = np.array([rig.joint_pos(g, "foot_l")[1] for g in gl])
    # a stance foot is low and slides backward relative to the pelvis: if the low foot moves +fwd, flip
    low = lh < np.percentile(lh, 30)
    dv = np.gradient(lf)
    if np.mean(dv[low]) > 0:
        fwd = -fwd
        lf = -lf
    # left heel strike = left foot furthest forward
    t0 = ts[int(np.argmax(lf))]
    rf = np.array([rel(g, "foot_r") @ fwd for g in gl])
    print(f"clip {clip}: {rig.dur:.3f}s, left strike at {t0:.3f}s, right strike at {ts[int(np.argmax(rf))]:.3f}s "
          f"(expected {(t0 + rig.dur / 2) % rig.dur:.3f}s)")

    # height normalisation: the STANDING mannequin (bind pose = the mesh's own vertex positions) is scaled to
    # 1.75 m, the stick figure's standing height
    height = rig.pos[:, 1].max() - rig.pos[:, 1].min()
    k = 1.75 / height
    # in-place: subtract the cycle-mean pelvis position (horizontal)
    pel = np.mean([rig.joint_pos(g, "pelvis") for g in gl], 0)

    kdir = (8 - wc.ROWS.index(dirname)) % 8
    # then match the stick-figure guide's mean on-screen height (head top to lowest point) in this direction,
    # so the figure fills the cell the same way (the mannequin's head and neck are proportionally longer)
    wc.use("hero")
    sm = np.array([wc.metrics(kdir, i / FRAMES) for i in range(FRAMES)]) / wc.PX_PER_M   # (top, height), metres
    a = math.radians(45 * kdir)
    f_scr = np.array([math.sin(a), 0, math.cos(a)])
    r_scr = np.array([-f_scr[2], 0, f_scr[0]])
    hs, tops = [], []
    for i in range(FRAMES):
        vs, _ = rig.skin((t0 + rig.dur * i / FRAMES) % rig.dur)
        d = vs - [pel[0], 0, pel[2]]
        d[:, 1] -= d[:, 1].min()
        w = (d @ right)[:, None] * r_scr + (d @ up)[:, None] * up + (d @ fwd)[:, None] * f_scr
        sy = -w[:, 1] * math.cos(wc.ELEV) + w[:, 2] * math.sin(wc.ELEV)
        hs.append(sy.max() - sy.min()); tops.append(sy.min())
    k = sm[:, 1].mean() / np.mean(hs)
    # the mannequin's feet hang less far below the ground line than the stick figure's (its lowest point is
    # nearly under the body), so shift it down by a constant to sit in the cell where the stick figure does
    y_off = sm[:, 0].mean() - np.mean(tops) * k
    print(f"bind-pose height {height:.3f}; scale {k:.3f} (bind pose = {height * k:.2f} m); "
          f"shifted down {y_off * 360 / (1.75 * math.cos(wc.ELEV)):.0f} px")
    cw, ch, ss = 300, 440, 2
    scale = 360 * ss / (1.75 * math.cos(wc.ELEV))
    im = Image.new("RGB", (cw * 4 * ss, ch * 2 * ss), (255, 0, 255))
    dr = ImageDraw.Draw(im)
    a = math.radians(45 * kdir)
    f_scr = np.array([math.sin(a), 0, math.cos(a)])
    r_scr = np.array([-f_scr[2], 0, f_scr[0]])
    light = np.array([0.3, 0.8, 0.5]); light /= np.linalg.norm(light)
    frames_dir = sys.argv[sys.argv.index("--frames-dir") + 1] if "--frames-dir" in sys.argv else None
    for i in range(FRAMES):
        t = (t0 + rig.dur * i / FRAMES) % rig.dur
        vs, g = rig.skin(t)
        d = vs - [pel[0], 0, pel[2]]
        # local coords as walk_cycle.pose(): x = character right, y = up, z = forward (metres)
        loc = np.c_[d @ right, d @ up, d @ fwd] * k
        loc[:, 1] -= loc[:, 1].min()                   # lowest point on the ground (natural bob), as pose()
        w = loc[:, :1] * r_scr + loc[:, 1:2] * up + loc[:, 2:3] * f_scr
        sx = w[:, 0]
        sy = -w[:, 1] * math.cos(wc.ELEV) + w[:, 2] * math.sin(wc.ELEV) + y_off
        dep =w[:, 2] * math.cos(wc.ELEV) + w[:, 1] * math.sin(wc.ELEV)   # larger = nearer the camera
        r_, c_ = divmod(i, 4)
        cx, fy = (c_ + 0.5) * cw * ss, (r_ * ch + ch - 70) * ss
        X, Y = cx + sx * scale, fy + sy * scale
        print("  frame", i, "top %.0f bottom %.0f px from ground" % ((Y.min() - fy) / ss, (Y.max() - fy) / ss))
        tri = rig.tri
        # back-face cull + mild shading (world-space normals, light from above/front)
        p0, p1, p2 = w[tri[:, 0]], w[tri[:, 1]], w[tri[:, 2]]
        nrm = np.cross(p1 - p0, p2 - p0)
        nl = np.linalg.norm(nrm, axis=1, keepdims=True); nrm = nrm / np.maximum(nl, 1e-12)
        cam = np.array([0, math.sin(wc.ELEV), math.cos(wc.ELEV)])     # toward the camera
        shade = 0.82 + 0.18 * np.clip(nrm @ light, 0, 1)
        order = np.argsort(dep[tri].mean(1))
        for ti in order:
            if nrm[ti] @ cam < -0.02:
                continue                               # facing away (glTF CCW winding)
            col = tuple(int(v) for v in np.clip(tri_col[ti] * shade[ti], 0, 255))
            a_, b_, c3 = tri[ti]
            dr.polygon([(X[a_], Y[a_]), (X[b_], Y[b_]), (X[c3], Y[c3])], fill=col)
        # face marker, as walk_cycle: a red dot at the front of the head when it faces the camera
        hd = (rig.joint_pos(g, "Head") - [pel[0], 0, pel[2]])
        hl = np.array([hd @ right, hd @ up, hd @ fwd]) * k
        ground = (d @ up * k).min()
        hc = hl + [0, 0.09 - ground, 0]                      # head centre a little above the head joint
        nose = hc + [0, -0.01, 0.12]
        pc, pn = wc.project(hc, kdir), wc.project(nose, kdir)
        if pn[2] > pc[2] + 0.06:                             # clearly facing the camera (not in NW)
            nx, ny = cx + pn[0] * scale, fy + pn[1] * scale
            rr = 0.11 * scale * 0.35
            dr.ellipse([nx - rr, ny - rr, nx + rr, ny + rr], fill=RED)
    im = im.resize((cw * 4, ch * 2), Image.LANCZOS)
    im.save(out)
    print("guide (mocap)", dirname, "->", out)
    if frames_dir:
        pathlib.Path(frames_dir).mkdir(parents=True, exist_ok=True)
        for i in range(FRAMES):
            r_, c_ = divmod(i, 4)
            im.crop((c_ * cw, r_ * ch, (c_ + 1) * cw, (r_ + 1) * ch)).save(f"{frames_dir}/f{i}.png")


if __name__ == "__main__":
    main()
