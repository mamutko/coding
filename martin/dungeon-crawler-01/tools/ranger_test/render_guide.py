"""Render a pose guide from a real 3D animation (Quaternius Universal Animation Library, CC0). The defaults give
exactly the format of `walk_cycle.py guide hero <DIR> out.png --magenta --limbs`: 1200 x 880, flat magenta, 4 x 2
cells of 300 x 440, the body centred in each cell, standing on a ground line 70 px above the cell bottom, ~360 px tall.

  python render_guide.py <UAL1_Standard.glb> <DIR> <out.png> [options]
    DIR              one direction (S SW W NW N NE E SE), a comma list, or "all" (the 8 rows of a game sheet in
                     walk_cycle.ROWS order: S SW W NW N NE E SE). Several directions = one row per direction.
    --clip NAME      animation clip (default Walk_Loop; also Walk_Formal_Loop, Jog_Fwd_Loop, Sprint_Loop, ...)
    --frames N       samples over one loop (default 8)
    --cols C         columns for a single direction (default 4; several directions always use N columns)
    --cell WxH       cell size in px (default 300x440); the figure height and ground offset scale with H
    --start strike|0 frame 1 at the left heel strike (default; walk / jog / sprint loops) or at t = 0 (other clips)

Pure numpy + PIL (no Blender / three.js): parses the GLB, samples the clip at N evenly spaced phases of one loop,
skins the mesh (linear blend skinning), removes root drift, colours each triangle by the limb its vertices are
mostly weighted to, and draws the triangles far to near with walk_cycle.project()'s 30 deg camera.
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
def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    glb, dirarg, out = sys.argv[1], sys.argv[2], sys.argv[3]
    clip = opt("--clip", "Walk_Loop")
    frames = int(opt("--frames", FRAMES))
    cw, ch = map(int, opt("--cell", "300x440").split("x"))
    start = opt("--start", "strike")
    dirs = wc.ROWS if dirarg == "all" else dirarg.split(",")
    cols = frames if len(dirs) > 1 else int(opt("--cols", 4))
    rows_per_dir = -(-frames // cols)
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

    # character frame: up = +Y; right = thigh_r - thigh_l; forward from the walk itself
    _, g0 = rig.skin(0.0)
    right = rig.joint_pos(g0, "thigh_r") - rig.joint_pos(g0, "thigh_l")
    right[1] = 0; right /= np.linalg.norm(right)
    up = np.array([0.0, 1.0, 0.0])
    fwd = np.cross(right, up)
    ts = np.linspace(0, rig.dur, 240, endpoint=False)
    gl = [rig.globals_(t) for t in ts]
    rel = lambda g, b: rig.joint_pos(g, b) - rig.joint_pos(g, "pelvis")
    lf = np.array([rel(g, "foot_l") @ fwd for g in gl])
    lh = np.array([rig.joint_pos(g, "foot_l")[1] for g in gl])
    # a stance foot is low and slides backward relative to the pelvis: if the low foot moves +fwd, flip
    if np.mean(np.gradient(lf)[lh < np.percentile(lh, 30)]) > 0:
        fwd = -fwd; lf = -lf
    if start == "strike":
        t0 = ts[int(np.argmax(lf))]               # left heel strike = left foot furthest forward
        rf = np.array([rel(g, "foot_r") @ fwd for g in gl])
        print(f"clip {clip}: {rig.dur:.3f}s, left strike at {t0:.3f}s, right strike at {ts[int(np.argmax(rf))]:.3f}s "
              f"(one cycle per loop if this is {(t0 + rig.dur / 2) % rig.dur:.3f}s)")
    else:
        t0 = 0.0
        print(f"clip {clip}: {rig.dur:.3f}s, from t = 0")
    times = [(t0 + rig.dur * i / frames) % rig.dur for i in range(frames)]
    pel = np.mean([rig.joint_pos(g, "pelvis") for g in gl], 0)     # in place: cycle-mean pelvis (horizontal)
    height = rig.pos[:, 1].max() - rig.pos[:, 1].min()           # standing (bind pose) height
    skins = [rig.skin(t) for t in times]

    def screen(vs, kdir, k):
        a = math.radians(45 * kdir)
        f_scr = np.array([math.sin(a), 0, math.cos(a)]); r_scr = np.array([-f_scr[2], 0, f_scr[0]])
        d = vs - [pel[0], 0, pel[2]]
        loc = np.c_[d @ right, d @ up, d @ fwd] * k
        loc[:, 1] -= loc[:, 1].min()                 # lowest point on the ground (natural bob), as pose()
        w = loc[:, :1] * r_scr + loc[:, 1:2] * up + loc[:, 2:3] * f_scr
        sy = -w[:, 1] * math.cos(wc.ELEV) + w[:, 2] * math.sin(wc.ELEV)
        dep = w[:, 2] * math.cos(wc.ELEV) + w[:, 1] * math.sin(wc.ELEV)   # larger = nearer the camera
        return w, w[:, 0], sy, dep

    # scale: one for all directions, so the mocap figure's mean on-screen height over the 5 base directions matches
    # the stick-figure guide's (the mannequin's head and neck are proportionally longer than the stick figure's)
    wc.use("hero")
    kd = lambda d: (8 - wc.ROWS.index(d)) % 8
    ph = np.array([[wc.metrics(kd(d), i / 8) for i in range(8)] for d in wc.BASE]) / wc.PX_PER_M  # (dir, frame, 2)
    hs = [np.ptp(screen(vs, kd(d), 1.0)[2]) for d in wc.BASE for vs, _ in skins]
    k = ph[..., 1].mean() / np.mean(hs)
    print(f"bind-pose height {height:.3f}; scale {k:.3f} (bind pose = {height * k:.2f} m)")

    ss = 2
    fig = 360 * ch / 440                                # figure height and ground offset scale with the cell
    gy = 70 * ch / 440
    scale = fig * ss / (1.75 * math.cos(wc.ELEV))
    W, H = cw * cols, ch * rows_per_dir * len(dirs)
    im = Image.new("RGB", (W * ss, H * ss), (255, 0, 255))
    dr = ImageDraw.Draw(im)
    light = np.array([0.3, 0.8, 0.5]); light /= np.linalg.norm(light)
    cam = np.array([0, math.sin(wc.ELEV), math.cos(wc.ELEV)])     # toward the camera
    for di, dname in enumerate(dirs):
        kdir = kd(dname)
        # the mannequin's feet hang less far below the ground line than the stick figure's: shift it down by a
        # constant per direction so its head sits where the stick figure's does (mirrored directions use their base)
        base = wc.MIRROR.get(dname, dname)
        tops = [screen(vs, kdir, k)[2].min() for vs, _ in skins]
        y_off = ph[wc.BASE.index(base), :, 0].mean() - np.mean(tops)
        ext = []
        for i, (vs, g) in enumerate(skins):
            w, sx, sy, dep = screen(vs, kdir, k)
            sy = sy + y_off
            r_, c_ = divmod(i, cols)
            r_ += di * rows_per_dir
            cx, fy = (c_ + 0.5) * cw * ss, (r_ * ch + ch - gy) * ss
            X, Y = cx + sx * scale, fy + sy * scale
            ext.append((round((Y.min() - fy) / ss), round((Y.max() - fy) / ss)))
            tri = rig.tri
            p0, p1, p2 = w[tri[:, 0]], w[tri[:, 1]], w[tri[:, 2]]
            nrm = np.cross(p1 - p0, p2 - p0)
            nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
            shade = 0.82 + 0.18 * np.clip(nrm @ light, 0, 1)
            for ti in np.argsort(dep[tri].mean(1)):        # painter's order, far to near
                if nrm[ti] @ cam < -0.02:
                    continue                               # back face (glTF CCW winding)
                col = tuple(int(v) for v in np.clip(tri_col[ti] * shade[ti], 0, 255))
                a_, b_, c3 = tri[ti]
                dr.polygon([(X[a_], Y[a_]), (X[b_], Y[b_]), (X[c3], Y[c3])], fill=col)
            # face marker, as walk_cycle: a red dot at the front of the head when it clearly faces the camera
            hd = rig.joint_pos(g, "Head") - [pel[0], 0, pel[2]]
            ground = ((vs - [pel[0], 0, pel[2]]) @ up * k).min()
            hc = np.array([hd @ right, hd @ up, hd @ fwd]) * k + [0, 0.09 - ground, 0]
            pc, pn = wc.project(hc, kdir), wc.project(hc + [0, -0.01, 0.12], kdir)
            if pn[2] > pc[2] + 0.06:
                nx, ny = cx + pn[0] * scale, fy + (pn[1] + y_off) * scale
                rr = 0.11 * scale * 0.35
                dr.ellipse([nx - rr, ny - rr, nx + rr, ny + rr], fill=RED)
        print(f"  {dname}: head top / lowest point, px from the ground line:", ext)
    im.resize((W, H), Image.LANCZOS).save(out)
    print(f"guide (mocap) {clip} {','.join(dirs)} {frames} frames {W}x{H} -> {out}")


if __name__ == "__main__":
    main()
