"""Build the hero knight as a skinned 3D model on the Quaternius UAL1 mannequin skeleton (CC0).

  python build_knight.py            -> knight.glb (next to this script), and knight.txt (the same, gzip + base64:
                                       the viewer's copy, as Artifacts don't serve .glb files; not committed)

The knight is generated, not modelled by hand: every armour shell is fitted to the mannequin's own surface by
casting rays from its bones (so the plate follows the body), the helm, pauldrons, belt, tassets, mail skirt and cape
are procedural, and every vertex takes its skin weights from the nearest mannequin vertices (or from a fixed bone
for rigid parts). The output GLB keeps the mannequin's skeleton and all 43 animation clips, so any clip drives the
knight. It is one skinned mesh (one primitive per material), so render_guide.py's Rig can load it too.

Extra bones (not animated, children of spine_03): cape_c, cape_l, cape_r. They hang the cape from the shoulders;
the viewer swings them (walk drag, legs and arms pushing the cloth); in any other renderer the cape stays rigid.

Pure numpy + scipy + Pillow. Coordinates: bind pose (T-pose), metres, Y up, the figure faces +Z, its left is +X.
"""
import io, json, math, pathlib, struct, sys
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[5]
SKILL = REPO / ".claude/skills/sprite-animation"
GLB_IN = SKILL / "datasets/quaternius-ual1/UAL1_Standard.glb"
sys.path.insert(0, str(SKILL / "tools"))
import render_guide as rg  # noqa: E402  (GLB parsing and skinning)

rng = np.random.default_rng(7)

# ------------------------------------------------------------------ the mannequin -------------
rig = rg.Rig(GLB_IN, "Walk_Loop")
FOOT_SCALE = (43 / 1.5 - 1.5) / rg.Rig.FOOT_CM          # EU 43 feet, as the default guides (render_guide --shoe)
rig.scale_feet(FOOT_SCALE)
BODY_P, BODY_N, BODY_T = rig.pos, rig.nrm, rig.tri
NAMES = [rig.nodes[ji]["name"] for ji in rig.joints]
JI = {n: k for k, n in enumerate(NAMES)}
NJ0 = len(NAMES)
CAPE_BONES = ["cape_c", "cape_l", "cape_r"]
NJ = NJ0 + len(CAPE_BONES)
for k, n in enumerate(CAPE_BONES):
    JI[n] = NJ0 + k
BIND = {n: np.linalg.inv(rig.ibm[k]) for k, n in enumerate(NAMES)}
bp = lambda n: BIND[n][:3, 3].copy()

WB = np.zeros((len(BODY_P), NJ))
for c in range(4):
    np.add.at(WB, (np.arange(len(BODY_P)), rig.jnt[:, c]), rig.wt[:, c])
DOM = WB.argmax(1)
TRI_DOM = WB[BODY_T].sum(1).argmax(1)

ARM = {n for n in NAMES if any(k in n for k in ("upperarm", "lowerarm", "hand", "index", "middle", "pinky",
                                                     "ring", "thumb"))}
HANDS = {n for n in ARM if not n.startswith(("upperarm", "lowerarm"))}
LEGS = {n for n in NAMES if any(k in n for k in ("thigh", "calf", "foot", "ball"))}
TORSO = {"pelvis", "spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r"}


def tris_of(bones):
    ks = [JI[b] for b in bones]
    sel = np.isin(TRI_DOM, ks)
    return BODY_P[BODY_T[sel]]


# ------------------------------------------------------------------ geometry helpers ----------
def raycast(O, D, tris):
    """Farthest hit distance along each ray (O, D: (R,3)) against triangles (T,3,3); nan for a miss."""
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    out = np.full(len(O), np.nan)
    for s in range(0, len(O), 128):
        o, d = O[s:s + 128, None], D[s:s + 128, None]
        p = np.cross(d, e2[None])
        det = (e1[None] * p).sum(-1)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        sv = o - v0[None]
        u = (sv * p).sum(-1) * inv
        q = np.cross(sv, e1[None])
        v = (d * q).sum(-1) * inv
        t = (e2[None] * q).sum(-1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        tt = np.where(hit, t, -np.inf).max(1)
        out[s:s + 128] = np.where(np.isfinite(tt), tt, np.nan)
    return out


def fill_nan(r, wrap=True):
    r = r.copy()
    for _ in range(200):
        m = np.isnan(r)
        if not m.any():
            break
        acc, cnt = np.zeros_like(r), np.zeros_like(r)
        for ax, sh in ((0, 1), (0, -1), (1, 1), (1, -1)):
            if ax == 1 and not wrap:
                rr = np.roll(r, sh, ax)
                if sh == 1: rr[:, 0] = np.nan
                else: rr[:, -1] = np.nan
            elif ax == 0:
                rr = np.roll(r, sh, ax)
                if sh == 1: rr[0] = np.nan
                else: rr[-1] = np.nan
            else:
                rr = np.roll(r, sh, ax)
            g = ~np.isnan(rr)
            acc[g] += rr[g]; cnt[g] += 1
        fill = m & (cnt > 0)
        r[fill] = acc[fill] / cnt[fill]
    return r


def smooth(r, s_t, s_a, wrap=True):
    return ndimage.gaussian_filter(r, (s_t, s_a), mode=("nearest", "wrap" if wrap else "nearest"))


def fitted(O, D, tris, offset, s_t=1.0, s_a=1.0, wrap=True, rmin=0.0):
    """Shell over the body: per ray the outermost body hit (filled, smoothed) plus an offset."""
    sh = O.shape[:2]
    r = raycast(O.reshape(-1, 3), D.reshape(-1, 3), tris).reshape(sh)
    r = smooth(fill_nan(r, wrap), s_t, s_a, wrap)
    r = np.maximum(r, rmin)
    return O + D * (r + offset)[..., None], r


def convex_rows(r, th):
    """Per row, replace the radii by the ray distances to the convex hull of the row's points (2D, around the
    ray origin): armour spans hollows instead of following them."""
    from scipy.spatial import ConvexHull
    out = r.copy()
    d = np.c_[np.sin(th), np.cos(th)]
    for i in range(len(r)):
        q = d * r[i][:, None]
        hull = q[ConvexHull(q).vertices]
        a, b = hull, np.roll(hull, -1, 0)
        # ray t*d against segment a + s*(b - a): solve t*d - s*e = a
        e = b - a
        det = d[:, None, 0] * -e[None, :, 1] - d[:, None, 1] * -e[None, :, 0]
        det = np.where(np.abs(det) < 1e-12, 1e-12, det)
        t = (a[None, :, 0] * -e[None, :, 1] - a[None, :, 1] * -e[None, :, 0]) / det
        s = (d[:, None, 0] * a[None, :, 1] - d[:, None, 1] * a[None, :, 0]) / det
        ok = (s >= -1e-6) & (s <= 1 + 1e-6) & (t > 0)
        out[i] = np.where(ok, t, np.inf).min(1)
    return np.where(np.isfinite(out), out, r)


def superellipse_rows(r, th, n=2.3, s=1.5):
    """Per row, fit a superellipse (half-width, front and back depth, smoothed over the rows) that encloses the
    row's points: x = r sin(th), z = r cos(th). Returns the ray distances to it."""
    sx, cz = np.abs(np.sin(th)), np.cos(th)
    a = (r * sx).max(1)
    f = (r * np.clip(cz, 0, None)).max(1)
    b = (r * np.clip(-cz, 0, None)).max(1)
    a, f, b = (ndimage.gaussian_filter1d(v, s, mode="nearest") for v in (a, f, b))
    c = np.where(cz[None] >= 0, f[:, None], b[:, None])
    se = 1 / ((sx[None] / a[:, None]) ** n + (np.abs(cz)[None] / c) ** n) ** (1 / n)
    # never inside the body: scale each row up until it clears the hull (by at most a few cm)
    k = np.clip((r / se).max(1), 1, 1.25)
    return se * k[:, None]


def frame_for(axis, hint):
    a = axis / np.linalg.norm(axis)
    e1 = hint - a * (hint @ a); e1 /= np.linalg.norm(e1)
    return a, e1, np.cross(a, e1)


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ mesh accumulation --------
class Part:
    """One piece: grid or triangle soup with per-vertex colour multiplier and full skin weights."""

    def __init__(self, name, mat, P, F, UV, W, C=None, N=None):
        self.name, self.mat = name, mat
        self.P, self.F, self.UV, self.W = P, F, UV, W
        self.C = np.ones((len(P), 3)) if C is None else C
        self.N = vertex_normals(P, F) if N is None else N


def vertex_normals(P, F):
    n = np.zeros_like(P)
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    for c in range(3):
        np.add.at(n, F[:, c], fn)
    # weld: coincident vertices (seams) share a normal
    key = np.round(P * 2e4).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    acc = np.zeros((inv.max() + 1, 3))
    np.add.at(acc, inv, n)
    n = acc[inv]
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def grid_faces(nu, nv, closed_v=False):
    """Faces of an nu x nv grid of vertices (index i*nv + j). closed_v: wrap j (no seam duplicate)."""
    F = []
    jm = nv if closed_v else nv - 1
    for i in range(nu - 1):
        for j in range(jm):
            a, b = i * nv + j, i * nv + (j + 1) % nv
            c, d = (i + 1) * nv + j, (i + 1) * nv + (j + 1) % nv
            F += [(a, c, b), (b, c, d)]
    return np.array(F, np.int64)


def grid_part(name, mat, G, W, C=None, outward=None, uv_scale=(1, 1), drop=None):
    """G: (nu, nv, 3) grid; nv columns include a seam duplicate when closed. outward: (nu, nv, 3) points
    inside the shell (faces are flipped so normals point away from them). drop: (nu-1, nv-1) bool cells to skip."""
    nu, nv = G.shape[:2]
    P = G.reshape(-1, 3)
    F = grid_faces(nu, nv)
    if drop is not None:
        keep = ~np.repeat(drop.reshape(-1), 2)
        F = F[keep]
    if outward is not None:
        fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
        cen = P[F].mean(1) - outward.reshape(-1, 3)[F].mean(1)
        if (np.sign((fn * cen).sum(1)) < 0).mean() > 0.5:
            F = F[:, [0, 2, 1]]
    u, v = np.meshgrid(np.linspace(0, 1, nu), np.linspace(0, 1, nv), indexing="ij")
    UV = np.c_[v.reshape(-1) * uv_scale[0], u.reshape(-1) * uv_scale[1]]
    Cc = None if C is None else C.reshape(-1, 3)
    return Part(name, mat, P, F, UV, W.reshape(-1, NJ), Cc)


# ------------------------------------------------------------------ skin weights -------------
_kd_cache = {}


def transfer(P, bones=None, k=6):
    """Skin weights from the nearest mannequin vertices (inverse-distance blend), optionally only from vertices
    whose main bone is in `bones`."""
    key = None if bones is None else tuple(sorted(bones))
    if key not in _kd_cache:
        sel = np.arange(len(BODY_P)) if bones is None else np.where(np.isin(DOM, [JI[b] for b in bones]))[0]
        _kd_cache[key] = (cKDTree(BODY_P[sel]), sel)
    tree, sel = _kd_cache[key]
    shp = P.shape[:-1]
    d, i = tree.query(P.reshape(-1, 3), k=k)
    w = 1 / np.maximum(d, 1e-4) ** 2
    w /= w.sum(1, keepdims=True)
    out = (WB[sel[i]] * w[..., None]).sum(1)
    return out.reshape(shp + (NJ,))


def rigid(shape, bone):
    W = np.zeros(tuple(shape) + (NJ,))
    W[..., JI[bone]] = 1
    return W


def mix(*pairs):
    """mix((w0, W0), (w1, W1), ...): per-vertex blend; w are arrays broadcastable to W[..., 0]."""
    out = 0
    for w, W in pairs:
        out = out + np.asarray(w)[..., None] * W
    return out


# ------------------------------------------------------------------ colours ------------------
# Vertex colour multiplies the material colour. Plate: dark body, bright worn edges and ridges.
PLATE, EDGE = 0.36, 1.0


def edge_colour(G_shape, axis_edges=(True, True), width=1.2, base=PLATE, hi=EDGE, extra=None):
    nu, nv = G_shape
    i = np.arange(nu)[:, None] * np.ones((1, nv))
    d = np.full((nu, nv), 99.0)
    if axis_edges[0]:
        d = np.minimum(d, i)
    if axis_edges[1]:
        d = np.minimum(d, nu - 1 - i)
    if extra is not None:
        d = np.minimum(d, extra)
    t = np.exp(-(d / width) ** 2)
    v = base + (hi - base) * t
    v = v * (1 + 0.0 * rng.standard_normal((nu, nv)))                    # (no mottling: it blotches on metal)
    return np.repeat(v[..., None], 3, -1)


PARTS = []


def add(p):
    PARTS.append(p)
    return p


# ------------------------------------------------------------------ landmarks -----------------
HEAD, NECK = bp("Head"), bp("neck_01")
SP1, SP2, SP3, PELV = bp("spine_01"), bp("spine_02"), bp("spine_03"), bp("pelvis")
SIDES = (("l", 1.0), ("r", -1.0))


# ================================================================== underlayer ===============
def underlayer():
    """The mannequin body itself: dark padded cloth under the plate (fills every gap). Hands become gauntlets."""
    hand_t = np.isin(TRI_DOM, [JI[b] for b in HANDS])
    body_F = BODY_T[~hand_t]
    add(Part("gambeson", "cloth_dark", BODY_P.copy(), body_F, np.zeros((len(BODY_P), 2)), WB.copy(),
             N=BODY_N.copy()))
    # gauntlets: the hand surface pushed out 5 mm, steel, knuckle ridges brighter
    used = np.unique(BODY_T[hand_t])
    remap = -np.ones(len(BODY_P), np.int64); remap[used] = np.arange(len(used))
    P = BODY_P[used] + BODY_N[used] * 0.005
    F = remap[BODY_T[hand_t]]
    C = np.full((len(P), 3), PLATE * 1.15)
    add(Part("gauntlets", "steel", P, F, np.zeros((len(P), 2)), WB[used].copy(), C=C))


# ================================================================== cuirass ==================
def cuirass():
    """Breast- and backplate in one shell: horizontal rays from the spine axis below the chest, a fan of rays
    tilting up toward the neck above it (so the plate rolls over the shoulders), shallow X ridge in front."""
    nt_lo, nt_hi, na = 30, 22, 128
    zc = -0.02
    th = np.linspace(0, 2 * np.pi, na + 1)                     # 0 = front (+z), seam duplicate
    ys = np.linspace(0.975, 1.30, nt_lo)
    el = np.radians(np.linspace(0, 68, nt_hi + 1)[1:])
    O = np.zeros((nt_lo + nt_hi, na + 1, 3)); D = np.zeros_like(O)
    for i, y in enumerate(ys):
        O[i] = (0, y, zc)
        D[i] = np.c_[np.sin(th), np.zeros_like(th), np.cos(th)]
    for k, e in enumerate(el):
        O[nt_lo + k] = (0, 1.30, zc)
        D[nt_lo + k] = np.c_[np.sin(th) * np.cos(e), np.full_like(th, np.sin(e)), np.cos(th) * np.cos(e)]
    tris = tris_of(TORSO | {"neck_01"})
    G, r = fitted(O, D, tris, 0.0, s_t=2.0, s_a=2.0)
    r = convex_rows(r, th)                                     # plate bridges every hollow (sternum, spine)
    r = superellipse_rows(r, th, n=2.3, s=3.6)                 # clean plate: one smooth section per height
    r = smooth(r, 2.0, 1.6)
    # offset along the ray: thicker over the chest, a waist that flares a little at the bottom edge
    i = np.arange(len(G))[:, None]
    off = 0.034 + 0.008 * ss(8, 0, i) + 0.006 * np.cos(th)[None] ** 2 * (np.cos(th)[None] > 0)
    G = O + D * (r + off)[..., None]
    # X ridge on the front: two diagonals crossing at the sternum, raised 9 mm
    x, y, z = G[..., 0], G[..., 1], G[..., 2]
    yc = 1.25
    d1 = np.abs((x * 0.9) - (y - yc)) / math.hypot(0.9, 1)
    d2 = np.abs((-x * 0.9) - (y - yc)) / math.hypot(0.9, 1)
    front = ss(0.0, 0.06, z - zc) * ss(1.02, 1.08, y) * ss(1.47, 1.40, y)
    ridge = (np.exp(-(d1 / 0.014) ** 2) + np.exp(-(d2 / 0.014) ** 2)).clip(0, 1) * front
    # a vertical crest down the middle too (medieval breastplates have one)
    crest = np.exp(-(x / 0.012) ** 2) * front * ss(1.40, 1.20, y) * 0.6
    bump = np.maximum(ridge, crest)
    G = G + D * (0.013 * bump)[..., None]
    C = edge_colour(G.shape[:2], width=2.0)
    C *= (1 + 1.6 * bump)[..., None]
    W = transfer(G, TORSO | {"neck_01"})
    add(grid_part("cuirass", "steel", G, W, C, outward=O))
    return G


# ================================================================== gorget ===================
def gorget():
    nt, na = 6, 40
    th = np.linspace(0, 2 * np.pi, na + 1)
    ys = np.linspace(1.43, 1.575, nt)
    G = np.zeros((nt, na + 1, 3))
    for i, y in enumerate(ys):
        t = (y - ys[0]) / (ys[-1] - ys[0])
        rx = 0.125 - 0.045 * ss(0, 0.6, t)
        rz = 0.130 - 0.040 * ss(0, 0.6, t)
        G[i] = np.c_[rx * np.sin(th), np.full_like(th, y), -0.02 + rz * np.cos(th) + 0.01 * t]
    O = G.copy(); O[..., 0] = 0; O[..., 2] = -0.02
    t = ((G[..., 1] - ys[0]) / (ys[-1] - ys[0]))
    W = mix((1 - ss(0.2, 0.9, t), rigid(G.shape[:2], "spine_03")), (ss(0.2, 0.9, t), rigid(G.shape[:2], "neck_01")))
    ring = np.minimum(np.abs(np.arange(nt) - 2), np.abs(np.arange(nt) - 4))[:, None] * np.ones((1, na + 1))
    C = edge_colour(G.shape[:2], width=0.8, extra=ring)
    add(grid_part("gorget", "steel", G, W, C, outward=O))


# ================================================================== helm =====================
def helm():
    """Rounded dome great helm: a near-cylindrical face and skull plate under a hemispherical dome, a raised
    ridge from the face over the crown, a raised band above a narrow horizontal visor slit."""
    na, nt = 64, 40
    th = np.linspace(-np.pi, np.pi, na + 1)                    # 0 = front
    y0, ybrow, ytop = 1.505, 1.745, 1.905
    cz = 0.012
    a0, b0 = 0.123, 0.140
    slit = (1.698, 1.724)
    ys = np.r_[np.linspace(y0, slit[0], 15), np.linspace(slit[0], slit[1], 3)[1:],
               np.linspace(slit[1], ybrow, 5)[1:]]
    dome = np.linspace(0, 1, nt - len(ys) + 1)[1:]
    G, slit_rows = [], []
    for i, y in enumerate(ys):
        flare = 1 + 0.06 * ss(1.56, y0, y)                     # flares out a little over the gorget
        taper = 1 - 0.05 * ss(1.62, 1.52, y)
        a, b = a0 * flare * taper, b0 * flare * taper
        G.append(np.c_[a * np.sin(th), np.full_like(th, y), cz + b * np.cos(th)])
        if slit[0] < y <= slit[1] + 1e-9:
            slit_rows.append(i - 1)
    for u in dome:
        ang = u * np.pi / 2
        a, b = a0 * np.cos(ang), b0 * np.cos(ang)
        y = ybrow + (ytop - ybrow) * np.sin(ang)
        G.append(np.c_[a * np.sin(th), np.full_like(th, y), cz + b * np.cos(th)])
    G = np.array(G)
    G[-1, :, 0] = 0; G[-1, :, 2] = cz
    # superellipse-ish front: a gentle prow down the face (the face plates meet in a vertical ridge)
    prow = np.exp(-(th / 0.55) ** 2)[None] * 0.012 * ss(ytop, ybrow - 0.05, G[..., 1])
    G[..., 2] += prow
    # ridge over the crown (front to back) and around the brow
    ridge = np.exp(-(np.sin(th) / 0.05) ** 2)[None] * np.ones((len(G), 1))
    ridge *= ss(1.60, 1.70, G[..., 1])
    brow = np.exp(-((G[..., 1] - (ybrow + 0.008)) / 0.006) ** 2)
    nrm = G - np.array([0, ybrow, cz]); nrm[..., 1] *= 0.4
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    G = G + nrm * (0.007 * np.maximum(ridge, brow))[..., None]
    C = edge_colour(G.shape[:2], axis_edges=(True, False), width=1.0)
    C *= (1 + 1.8 * np.maximum(ridge, brow))[..., None]
    # rivets on the brow band
    W = rigid(G.shape[:2], "Head")
    O = np.zeros_like(G); O[..., 1] = G[..., 1]; O[..., 2] = cz
    drop = np.zeros((len(G) - 1, na), bool)
    for r_ in slit_rows:
        drop[r_] = np.abs(th[:-1] + np.pi / na) < np.radians(72)
    add(grid_part("helm", "steel", G, W, C, outward=O, drop=drop))
    # the slit: a dark recessed strip just inside the opening, and a dark inner shell (no face visible)
    k0 = slit_rows[0]
    S = np.array([G[k0], G[slit_rows[-1] + 1]]) - nrm[[k0, slit_rows[-1] + 1]] * 0.004
    S = S - np.array([0, 0, 0.0])
    Si = np.array([S[0] - nrm[k0] * 0.02, S[1] - nrm[slit_rows[-1] + 1] * 0.02])
    sel = np.abs(th) < np.radians(78)
    for sheet in (np.array([S[0][sel], Si[0][sel]]), np.array([Si[1][sel], S[1][sel]]),
                  np.array([Si[0][sel], Si[1][sel]])):
        add(grid_part("visor", "dark", sheet, rigid(sheet.shape[:2], "Head")))


# ================================================================== pauldrons ================
def pauldrons():
    """A dome over the shoulder joint and three lames down the upper arm, each overlapping the next, every lower
    edge rolled bright. Built in the T-pose (arm along +-X); the dome follows the clavicle, the lames the arm."""
    for s, sg in SIDES:
        sh = bp(f"upperarm_{s}")
        cen = sh + np.array([sg * -0.01, 0.0, 0.0])
        # (x start, x end along the arm from the joint, half-height, half-depth, rise)
        bands = [(-0.090, 0.085, 0.135, 0.148, 0.060),
                 (0.055, 0.115, 0.122, 0.136, 0.040),
                 (0.095, 0.155, 0.112, 0.126, 0.028),
                 (0.135, 0.195, 0.102, 0.116, 0.016)]
        na = 36
        al = np.linspace(-np.radians(150), np.radians(150), na)   # around the arm, 0 = up; open underneath
        for bi, (x0, x1, hy, hz, rise) in enumerate(bands):
            nt = 14 if bi == 0 else 6
            xs = np.linspace(x0, x1, nt)
            G = np.zeros((nt, na, 3))
            for i, x in enumerate(xs):
                if bi == 0:
                    # dome: a squashed sphere around the shoulder, rounded off toward the neck
                    u = (x - x0) / (x1 - x0)                       # 0 inner (neck side), 1 outer
                    shape = np.sqrt(np.clip(1 - ((u - 0.55) / 0.62) ** 2, 0.05, 1))
                    ky, kz = hy * shape, hz * shape
                    yoff = rise * shape
                else:
                    u = (x - x0) / (x1 - x0)
                    ky, kz = hy * (1 + 0.05 * u), hz * (1 + 0.05 * u)
                    yoff = rise
                G[i] = np.c_[np.full(na, cen[0] + sg * x), cen[1] + yoff * 0.4 + ky * np.cos(al),
                             cen[2] + kz * np.sin(al)]
            # the dome tilts down toward the neck side (follows the shoulder slope)
            O = G.copy(); O[..., 1] = cen[1]; O[..., 2] = cen[2]
            dx = (G[..., 0] - sh[0]) * sg
            G[..., 1] -= 0.10 * np.clip(-dx, 0, None)
            # weights: dome mostly clavicle / spine, lames progressively the upper arm
            wa = ss(0.02, 0.12, dx)
            Wc = rigid(G.shape[:2], f"clavicle_{s}")
            Wa = rigid(G.shape[:2], f"upperarm_{s}")
            W = mix((1 - wa, Wc), (wa, Wa))
            C = edge_colour(G.shape[:2], axis_edges=(bi == 0, True), width=0.9)
            sidee = np.minimum(np.arange(na), na - 1 - np.arange(na))[None] * np.ones((nt, 1))
            C = np.maximum(C, edge_colour(G.shape[:2], axis_edges=(False, False), width=0.9, extra=sidee))
            add(grid_part(f"pauldron_{s}{bi}", "steel", G, W, C, outward=O))


# ================================================================== limb plates ==============
def limb_tube(name, bone_a, bone_b, t0, t1, bones, offset, nt=12, na=28, hint=(0, 1, 0), flare=None,
              lames=(), weights=None, mat="steel", open_cells=None):
    a, b = bp(bone_a), bp(bone_b)
    ax, e1, e2 = frame_for(b - a, np.array(hint, float))
    ts = np.linspace(t0, t1, nt)
    L = np.linalg.norm(b - a)
    th = np.linspace(0, 2 * np.pi, na + 1)
    O = (a + np.outer(ts, b - a))[:, None, :] * np.ones((1, na + 1, 1))
    D = (np.outer(np.cos(th), e1) + np.outer(np.sin(th), e2))[None] * np.ones((nt, 1, 1))
    G, r = fitted(O, D, tris_of(bones), 0.0, s_t=1.2, s_a=1.5)
    off = np.full(r.shape, offset)
    if flare is not None:
        off = off + flare(ts)[:, None]
    lame = np.zeros(r.shape)
    for tl in lames:                                           # rolled lame edges: small steps
        lame += 0.004 * np.exp(-((ts - tl) * L / 0.008) ** 2)[:, None]
    G = O + D * (r + off + lame)[..., None]
    extra = None
    if lames:
        idx = np.arange(nt)
        extra = np.min([np.abs(ts - tl) * L / (L * (t1 - t0) / nt) for tl in lames], 0)[:, None] * np.ones((1, na + 1))
    C = edge_colour(G.shape[:2], width=0.9, extra=extra)
    W = transfer(G, bones) if weights is None else weights(G, ts)
    return add(grid_part(name, mat, G, W, C, outward=O, drop=open_cells))


def limbs():
    for s, sg in SIDES:
        ua, la, hd = f"upperarm_{s}", f"lowerarm_{s}", f"hand_{s}"
        # rerebrace (upper arm below the pauldron), vambrace, flared gauntlet cuff
        limb_tube(f"rerebrace_{s}", ua, la, 0.45, 0.93, {ua}, 0.016, nt=9, lames=(0.6,))
        limb_tube(f"vambrace_{s}", la, hd, 0.10, 0.92, {la}, 0.014, nt=12)
        limb_tube(f"cuff_{s}", la, hd, 0.86, 1.10, {la, hd}, 0.018, nt=7,
                  flare=lambda t: 0.020 * ss(0.92, 1.10, t))
        # couter: a cup on the back of the elbow (the elbow points -z in the T-pose)
        e = bp(la)
        ax, e1, e2 = frame_for(bp(hd) - e, np.array([0, 0, -1.0]))
        na, nt = 22, 12
        u = np.linspace(-1, 1, nt)[:, None]; v = np.linspace(-1, 1, na)[None]
        rr = np.sqrt(np.clip(1 - u ** 2 * 0.85 - v ** 2 * 0.85, 0, 1))
        G = (e + 0.0 * ax)[None, None] + u[..., None] * ax * 0.075 + v[..., None] * e2 * 0.062 \
            + (0.040 + 0.040 * rr)[..., None] * e1
        # the fan (a wing on the outer side): bulge v>0 a bit more
        Wt = transfer(G, {ua, la})
        C = edge_colour(G.shape[:2], width=0.9, extra=np.minimum(np.arange(na), na - 1 - np.arange(na))[None] * np.ones((nt, 1)))
        C *= (1 + 0.6 * np.exp(-(u / 0.15) ** 2 - (v / 0.2) ** 2))[..., None]
        O = np.broadcast_to(e, G.shape)
        add(grid_part(f"couter_{s}", "steel", G, Wt, C, outward=O))

        th_, ca, ft = f"thigh_{s}", f"calf_{s}", f"foot_{s}"
        # cuisse (thigh plate, mostly under the mail skirt), greave, knee cop
        limb_tube(f"cuisse_{s}", th_, ca, 0.30, 0.86, {th_}, 0.020, nt=12, hint=(0, 0, 1), lames=(0.72,))
        limb_tube(f"greave_{s}", ca, ft, 0.12, 1.02, {ca}, 0.016, nt=16, hint=(0, 0, 1),
                  flare=lambda t: 0.014 * ss(0.85, 1.02, t), lames=(0.20,))
        k = bp(ca)
        ax, e1, e2 = frame_for(bp(ft) - k, np.array([0, 0, 1.0]))   # e1 = forward
        nt, na = 14, 26
        u = np.linspace(-1, 1, nt)[:, None]; v = np.linspace(-1, 1, na)[None]
        rr = np.sqrt(np.clip(1 - u ** 2 * 0.9 - v ** 2 * 0.9, 0, 1))
        point = np.exp(-(u / 0.35) ** 2 - (v / 0.35) ** 2)      # a pointed boss
        G = k[None, None] + u[..., None] * ax * 0.085 + v[..., None] * e2 * 0.080 \
            + (0.035 + 0.055 * rr + 0.022 * point)[..., None] * e1
        Wk = transfer(G, {th_, ca})
        C = edge_colour(G.shape[:2], width=0.9, extra=np.minimum(np.arange(na), na - 1 - np.arange(na))[None] * np.ones((nt, 1)))
        C *= (1 + 0.9 * point)[..., None]
        add(grid_part(f"poleyn_{s}", "steel", G, Wk, C, outward=np.broadcast_to(k, G.shape)))
        # knee strap (red-brown leather) around the back of the knee
        a_, b_ = bp(th_), bp(ca)
        limb_tube(f"kneestrap_{s}", th_, ca, 0.94, 1.0, {th_, ca}, 0.026, nt=3, mat="leather")


def sabatons():
    """The foot surface pushed out 12 mm; brighter lines across the foot for the lames."""
    fb = {f"foot_{s}" for s, _ in SIDES} | {f"ball_{s}" for s, _ in SIDES}
    sel_t = np.isin(TRI_DOM, [JI[b] for b in fb]) & (BODY_P[BODY_T].mean(1)[:, 1] < 0.135)
    used = np.unique(BODY_T[sel_t])
    remap = -np.ones(len(BODY_P), np.int64); remap[used] = np.arange(len(used))
    P = BODY_P[used] + BODY_N[used] * 0.012
    P[:, 1] = np.maximum(P[:, 1], 0.0)
    F = remap[BODY_T[sel_t]]
    zf = P[:, 2]
    lam = np.zeros(len(P))
    for zl in (0.03, 0.065, 0.10, 0.135):
        lam = np.maximum(lam, np.exp(-((zf - zl) / 0.004) ** 2) * (P[:, 1] > 0.02))
    C = np.repeat((PLATE + 0.6 * lam)[:, None], 3, 1)
    add(Part("sabatons", "steel", P, F, np.zeros((len(P), 2)), WB[used].copy(), C=C))


# ================================================================== belt, skirt, tassets =====
def waist_profile(ys, na, offset):
    """Fitted ring around the hips at the heights ys (rays from the body axis)."""
    th = np.linspace(0, 2 * np.pi, na + 1)
    O = np.zeros((len(ys), na + 1, 3)); O[..., 1] = np.asarray(ys)[:, None]; O[..., 2] = -0.005
    D = np.zeros_like(O)
    D[...] = np.c_[np.sin(th), np.zeros_like(th), np.cos(th)][None]
    G, r = fitted(O, D, tris_of(TORSO | {"thigh_l", "thigh_r"}), offset, s_t=1.0, s_a=2.5)
    return G, O, th


def skirt_weights(G):
    """Pelvis at the top, each side blending to its thigh lower down (cloth between the legs splits the blend)."""
    y, x = G[..., 1], G[..., 0]
    down = ss(0.98, 0.70, y)
    side = np.clip(0.5 + x / 0.16, 0, 1)                       # 1 = left thigh
    Wp = rigid(G.shape[:-1], "pelvis")
    Wl, Wr = rigid(G.shape[:-1], "thigh_l"), rigid(G.shape[:-1], "thigh_r")
    k = 0.85 * down
    return mix((1 - k, Wp), (k * side, Wl), (k * (1 - side), Wr))


def belt_and_skirt(cuirass_G):
    na = 64
    # mail skirt: a cone from under the belt flaring to mid-thigh
    nt = 14
    ys = np.linspace(1.00, 0.63, nt)
    top, Otop, th = waist_profile([1.0], na, 0.030)
    G = np.zeros((nt, na + 1, 3))
    for i, y in enumerate(ys):
        t = i / (nt - 1)
        c = np.array([0, y, 0.0])
        rel = top[0] - np.array([0, 1.0, -0.005])
        sx = 1 + 0.30 * t ** 1.2
        sz = 1 + 0.45 * t ** 1.2
        G[i] = c + rel * np.array([sx, 0, sz]) + np.array([0, 0, -0.005 + 0.025 * t])
        G[i, :, 1] = y
    # ragged, slightly uneven hem
    G[-1, :, 1] += 0.012 * np.sin(th * 7) + 0.006 * rng.standard_normal(na + 1)
    G[-1, -1] = G[-1, 0]
    O = G.copy(); O[..., 0] = 0; O[..., 2] = 0
    add(grid_part("mail_skirt", "mail", G, skirt_weights(G), outward=O, uv_scale=(28, 10)))
    # belt: wide leather band around the waist over the bottom edge of the cuirass
    yb = np.linspace(0.965, 1.035, 4)
    B, Ob, _ = waist_profile(yb, na, 0.052)
    Bc = np.repeat(np.array([[1.0, 1.0, 1.0]]) * np.r_[0.75, 1, 1, 0.75][:, None, None], na + 1, 1)
    add(grid_part("belt", "leather", B, transfer(B, TORSO), Bc, outward=Ob))
    # buckle: a dark rectangular frame on the front
    front = B[:, 0]                                         # th = 0 column
    zf = front[:, 2].max() + 0.008
    bx, by = 0.042, 0.032
    rect = [((-bx, -by), (bx, -by)), ((bx, -by), (bx, by)), ((bx, by), (-bx, by)), ((-bx, by), (-bx, -by))]
    for k, (p0, p1) in enumerate(rect):
        q = np.array([[[p0[0], 1.0 + p0[1], zf], [p1[0], 1.0 + p1[1], zf]],
                      [[p0[0], 1.0 + p0[1], zf + 0.008], [p1[0], 1.0 + p1[1], zf + 0.008]]])
        inset = np.array([0, 0, 0])
        d = np.array(p1) - np.array(p0); n2 = np.array([-d[1], d[0]]) / np.linalg.norm(d) * 0.010
        q2 = q.copy(); q2[..., 0] -= n2[0] * 0;
        band = np.array([[[p0[0], 1.0 + p0[1], zf + 0.008], [p1[0], 1.0 + p1[1], zf + 0.008]],
                         [[p0[0] + n2[0], 1.0 + p0[1] + n2[1], zf + 0.008],
                          [p1[0] + n2[0], 1.0 + p1[1] + n2[1], zf + 0.008]]])
        for sheet in (q, band):
            add(grid_part(f"buckle{k}", "steel", sheet, rigid(sheet.shape[:2], "pelvis"),
                          C=np.full(sheet.shape, 0.9)))
    # tassets: tattered leather flaps hanging from the belt over the mail
    flaps = [(-0.55, 0.55, 0.75, 0.05),                 # front centre (pointed)
             (0.42, 1.15, 0.79, 0.0), (-1.15, -0.42, 0.79, 0.0),   # front left / right
             (1.15, 1.90, 0.82, 0.0), (-1.90, -1.15, 0.82, 0.0)]   # hips
    for fi, (a0, a1, ybot, point) in enumerate(flaps):
        nu, nv = 10, 12
        th_f = np.linspace(a0, a1, nv)
        ys_f = np.linspace(1.02, ybot, nu)
        G = np.zeros((nu, nv, 3))
        for i, y in enumerate(ys_f):
            t = i / (nu - 1)
            # follow the skirt cone, 14 mm outside it
            ring = waist_profile([1.0], 96, 0.045)[0][0]
            ang = np.linspace(0, 2 * np.pi, 97)
            rel = ring - np.array([0, 1.0, -0.005])
            rx = np.interp(np.mod(th_f, 2 * np.pi), ang, rel[:, 0])
            rz = np.interp(np.mod(th_f, 2 * np.pi), ang, rel[:, 2])
            sx, sz = 1 + 0.30 * t ** 1.2, 1 + 0.45 * t ** 1.2
            G[i] = np.c_[rx * sx, np.full(nv, y), -0.005 + rz * sz + 0.03 * t]
        # tattered hem: each column ends at its own length; a pointed front flap
        w = np.linspace(-1, 1, nv)
        rag = 0.035 * rng.random(nv) + point * (1 - np.abs(w)) * 1.4
        span = 1.02 - ybot
        for j in range(nv):
            L = span * (1 + rag[j] / span) * (0.92 + 0.08 * (j % 2))
            G[:, j, 1] = 1.02 - np.linspace(0, 1, nu) * L
        O = G.copy(); O[..., 0] = 0; O[..., 2] = 0
        C = np.ones((nu, nv, 3)) * (0.85 + 0.25 * rng.random((nu, nv, 1)))
        C[0] *= 0.7
        add(grid_part(f"tasset{fi}", "leather", G, skirt_weights(G), C, outward=O, uv_scale=(1, 1)))


# ================================================================== cape =====================
def cape():
    """Dark crimson cloth over both shoulders like a mantle, hanging to the back of the knees with a torn hem.
    Columns run around the back (phi = 0 straight behind), rows from the collar down. The top rows sit on the
    shoulders (clavicles / spine); below the shoulder line they hang from the cape bones."""
    nu, nv = 34, 49
    phi = np.linspace(-1, 1, nv)
    G = np.zeros((nu, nv, 3))
    ys = np.r_[np.linspace(1.62, 1.44, 8), np.linspace(1.40, 0.50, nu - 8)]
    zc = -0.02
    for i, y in enumerate(ys):
        if y >= 1.44:                     # mantle over the shoulders: from the collar out to the pauldrons
            t = (1.62 - y) / 0.18
            pm = np.radians(132 - 20 * t)
            rx = 0.115 + 0.15 * ss(0, 1, t)
            rz = 0.115 + 0.07 * ss(0, 1, t)
        else:                             # hanging part: wraps less far forward, flares toward the hem
            t = (1.44 - y) / 0.94
            pm = np.radians(112 - 32 * ss(0, 0.35, t))
            rx = 0.255 + 0.085 * t
            rz = 0.185 + 0.11 * t ** 1.2
        a = phi * pm
        G[i] = np.c_[rx * np.sin(a), np.full(nv, y), zc - rz * np.cos(a)]
    # folds: vertical waves growing toward the hem
    hang = ss(1.45, 0.9, G[..., 1])
    a = phi[None] * np.ones((nu, 1))
    fold = 0.030 * np.sin(a * 9.0 + 0.6) + 0.012 * np.sin(a * 17 + 1.7)
    radial = G.copy(); radial[..., 1] = 0; radial[..., 2] -= zc
    radial /= np.maximum(np.linalg.norm(radial, axis=-1, keepdims=True), 1e-9)
    G = G + radial * (fold * hang)[..., None]
    # clear the armour: push out along the radial direction where the plate is closer than 1.2 cm
    armour = [p for p in PARTS if p.mat == "steel" and not p.name.startswith(("rerebrace", "vambrace", "cuff",
                                                                                "couter", "gauntlet"))
              and not (p.name.startswith("pauldron") and p.name[-1] in "23")]
    tris = np.concatenate([p.P[p.F] for p in armour] + [p.P[p.F] for p in PARTS if p.name.startswith("tasset")])
    for _ in range(2):
        O = G.copy(); O[..., 0] = 0; O[..., 2] = zc
        O[..., 1] = np.where(G[..., 1] > 1.44, 1.30, G[..., 1])
        Dv = G - O; dist = np.linalg.norm(Dv, axis=-1); Dv /= dist[..., None]
        hit = raycast(O.reshape(-1, 3), Dv.reshape(-1, 3), tris).reshape(G.shape[:2])
        need = np.where(np.isnan(hit), 0, hit + 0.028 - dist)
        need = ndimage.gaussian_filter(np.maximum(need, 0), (1.0, 1.0))
        G = G + Dv * need[..., None]
    # torn hem: columns end at their own length, deeper notches here and there
    rag = 0.05 * rng.random(nv) + 0.07 * (rng.random(nv) < 0.25) * rng.random(nv)
    rag = ndimage.uniform_filter1d(rag, 2)
    rag[::3] += 0.03
    hem_rows = 6
    for j in range(nv):
        for k in range(hem_rows):
            i = nu - hem_rows + k
            f = (k + 1) / hem_rows
            G[i, j, 1] = G[i, j, 1] + rag[j] * f * 0 + 0
        G[nu - hem_rows:, j, 1] = np.linspace(G[nu - hem_rows - 1, j, 1], 0.50 + rag[j] * -1 + 0.04, hem_rows + 1)[1:]
    # weights: on the shoulders follow the clavicles / spine; the hanging part follows the cape bones
    y = G[..., 1]
    on_sh = ss(1.36, 1.47, y)
    side = np.clip(0.5 + G[..., 0] / 0.5, 0, 1)
    Wsh = mix((side, rigid(G.shape[:2], "clavicle_l")), (1 - side, rigid(G.shape[:2], "clavicle_r")))
    wsp = 1 - ss(0.06, 0.16, np.abs(G[..., 0]))                 # the middle of the back follows the spine
    Wsh = mix((1 - wsp, Wsh), (wsp, rigid(G.shape[:2], "spine_03")))
    pa = np.abs(phi)[None] * np.ones((nu, 1))
    wside = ss(0.35, 0.85, pa)
    Wl, Wr, Wc = (rigid(G.shape[:2], b) for b in ("cape_l", "cape_r", "cape_c"))
    Wside = mix(((phi > 0)[None] * np.ones((nu, 1)), Wl), ((phi <= 0)[None] * np.ones((nu, 1)), Wr))
    Whang = mix((1 - wside, Wc), (wside, Wside))
    W = mix((on_sh, Wsh), (1 - on_sh, Whang))
    O = G.copy(); O[..., 0] = 0; O[..., 2] = zc
    C = np.ones((nu, nv, 3)) * (0.92 + 0.16 * rng.random((nu, nv, 1)))
    C *= (1 - 0.25 * np.clip(fold * hang / 0.028, -1, 1))[..., None]      # fold shading baked in lightly
    add(grid_part("cape", "cape", G, W, C, outward=O, uv_scale=(6, 8)))
    # brooches: two round studs where the mantle meets the front of the shoulders
    for s, sg in SIDES:
        jj = 2 if sg < 0 else nv - 3
        p = G[4, jj]
        n = np.array([0.35 * sg, 0.2, 1.0]); n /= np.linalg.norm(n)
        add(disc(f"brooch_{s}", p + n * 0.006, n, 0.020, f"clavicle_{s}"))
    return G


def disc(name, c, n, r, bone, na=16):
    _, e1, e2 = frame_for(n, np.array([0, 1.0, 0]) if abs(n[1]) < 0.9 else np.array([1.0, 0, 0]))
    th = np.linspace(0, 2 * np.pi, na + 1)
    rr = np.array([0.0, 0.6, 1.0])[:, None]
    h = np.array([0.008, 0.006, 0.0])[:, None]
    G = c + (rr * r)[..., None] * (np.cos(th)[None, :, None] * e1 + np.sin(th)[None, :, None] * e2) + h[..., None] * n
    C = np.repeat(np.array([1.0, 0.8, 0.5])[:, None, None], na + 1, 1) * np.ones((1, 1, 3))
    return grid_part(name, "steel", G, rigid(G.shape[:2], bone), C,
                     outward=np.broadcast_to(c - n * 0.05, G.shape))


# ================================================================== GLB writer ===============
MATERIALS = {
    # name: (base colour as sRGB 0-1, metallic, roughness, double sided, texture). Written linear (glTF).
    "steel": ([0.46, 0.39, 0.38], 0.85, 0.46, True, None),
    "dark": ([0.04, 0.035, 0.035], 0.0, 0.9, True, None),
    "cloth_dark": ([0.13, 0.10, 0.10], 0.0, 0.9, True, None),
    "leather": ([0.21, 0.065, 0.04], 0.0, 0.70, True, None),
    "mail": ([0.55, 0.50, 0.48], 0.8, 0.5, True, "mail"),
    "cape": ([0.30, 0.04, 0.045], 0.0, 0.88, True, None),
}


def lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def mail_texture(n=64):
    """A chainmail tile: rings in staggered rows, bright rims, dark gaps."""
    yy, xx = np.mgrid[0:n, 0:n] + 0.5
    v = np.zeros((n, n))
    for cy in range(0, n + 16, 16):
        for cx in range(0, n + 16, 16):
            for oy, ox in ((0, 0), (8, 8)):
                d = np.hypot((xx - cx - ox), (yy - cy - oy) * 1.15)
                ring = np.exp(-((d - 6.0) / 1.6) ** 2)
                v = np.maximum(v, ring * (0.75 + 0.25 * np.clip((cy + oy - yy) / 6, -1, 1)))
    img = np.clip(0.10 + 0.95 * v, 0, 1)
    rgb = (np.stack([img, img * 0.96, img * 0.94], -1) * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, "PNG")
    return buf.getvalue()


def write_glb(path):
    src_j, src_b = rg.load_glb(GLB_IN)
    j = {"asset": {"version": "2.0", "generator": "build_knight.py (dungeon-crawler hero)"},
         "scene": 0, "scenes": src_j["scenes"], "nodes": json.loads(json.dumps(src_j["nodes"])),
         "materials": [], "meshes": [], "skins": [], "animations": [], "accessors": [], "bufferViews": [],
         "buffers": [], "textures": [], "images": [], "samplers": []}
    blob = bytearray()

    def view(data, target=None):
        while len(blob) % 4:
            blob.append(0)
        bv = {"buffer": 0, "byteOffset": len(blob), "byteLength": len(data)}
        if target:
            bv["target"] = target
        blob.extend(data)
        j["bufferViews"].append(bv)
        return len(j["bufferViews"]) - 1

    def acc(arr, ctype, atype, target=None, minmax=False, normalized=False):
        arr = np.ascontiguousarray(arr)
        a = {"bufferView": view(arr.tobytes(), target), "componentType": ctype, "count": len(arr), "type": atype}
        if minmax:
            a["min"] = arr.min(0).tolist() if arr.ndim > 1 else [float(arr.min())]
            a["max"] = arr.max(0).tolist() if arr.ndim > 1 else [float(arr.max())]
        if normalized:
            a["normalized"] = True
        j["accessors"].append(a)
        return len(j["accessors"]) - 1

    # animations: copy every sampler's input / output accessor from the source
    amap, seen = {}, {}

    def copy_acc(i):
        """Copy an accessor's raw data (keeps its component type), sharing identical arrays (key times)."""
        if i in amap:
            return amap[i]
        a = dict(src_j["accessors"][i])
        bv = src_j["bufferViews"][a["bufferView"]]
        nc = rg.NC[a["type"]] * np.dtype(rg.CT[a["componentType"]]).itemsize
        assert "byteStride" not in bv or bv["byteStride"] == nc
        start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        raw = bytes(src_b[start:start + nc * a["count"]])
        key = (raw, a["componentType"], a["type"])
        if key not in seen:
            a["bufferView"] = view(raw); a.pop("byteOffset", None)
            j["accessors"].append(a)
            seen[key] = len(j["accessors"]) - 1
        amap[i] = seen[key]
        return amap[i]

    for an in src_j["animations"]:
        j["animations"].append({"name": an["name"], "channels": an["channels"],
                                "samplers": [{"input": copy_acc(s["input"]), "output": copy_acc(s["output"]),
                                              "interpolation": s.get("interpolation", "LINEAR")}
                                             for s in an["samplers"]]})
    # cape bones: children of spine_03, bind rotation = identity in world (so local X = the figure's left)
    nodes = j["nodes"]
    name_idx = {n.get("name"): i for i, n in enumerate(nodes)}
    sp3 = name_idx["spine_03"]
    sp3_bind = BIND["spine_03"]
    cape_bind = {"cape_c": np.array([0, 1.45, -0.17]), "cape_l": np.array([0.24, 1.45, -0.12]),
                 "cape_r": np.array([-0.24, 1.45, -0.12])}
    new_joint_nodes = []
    for n in CAPE_BONES:
        M = np.eye(4); M[:3, 3] = cape_bind[n]
        local = np.linalg.inv(sp3_bind) @ M
        R = local[:3, :3]
        # rotation matrix -> quaternion (x, y, z, w)
        w = math.sqrt(max(0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
        x = math.copysign(math.sqrt(max(0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
        y = math.copysign(math.sqrt(max(0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
        z = math.copysign(math.sqrt(max(0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
        nodes.append({"name": n, "translation": local[:3, 3].tolist(), "rotation": [x, y, z, w]})
        nodes[sp3].setdefault("children", []).append(len(nodes) - 1)
        new_joint_nodes.append(len(nodes) - 1)
    # mesh node: drop the mannequin's mesh, add ours under the same node
    mi = next(i for i, n in enumerate(nodes) if "mesh" in n)
    nodes[mi]["name"] = "Knight"
    src_skin = src_j["skins"][0]
    ibm = np.concatenate([rig.ibm, np.stack([np.linalg.inv(np.r_[np.c_[np.eye(3), cape_bind[n]], [[0, 0, 0, 1]]])
                                             for n in CAPE_BONES])])
    ibm_acc = acc(ibm.transpose(0, 2, 1).reshape(-1, 16).astype(np.float32), 5126, "MAT4")
    skin = {"joints": src_skin["joints"] + new_joint_nodes, "inverseBindMatrices": ibm_acc, "name": "Knight"}
    if "skeleton" in src_skin:
        skin["skeleton"] = src_skin["skeleton"]
    j["skins"].append(skin)
    nodes[mi]["skin"] = 0

    # materials + textures
    mat_idx = {}
    for name, (col, met, rough, ds, tex) in MATERIALS.items():
        m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": lin(col).tolist() + [1], "metallicFactor": met,
                                                     "roughnessFactor": rough}, "doubleSided": ds}
        if tex == "mail":
            png = mail_texture()
            j["images"].append({"bufferView": view(png), "mimeType": "image/png"})
            j["samplers"].append({"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497})
            j["textures"].append({"source": len(j["images"]) - 1, "sampler": len(j["samplers"]) - 1})
            m["pbrMetallicRoughness"]["baseColorTexture"] = {"index": len(j["textures"]) - 1}
        mat_idx[name] = len(j["materials"])
        j["materials"].append(m)

    prims, stats = [], {}
    for mname in MATERIALS:
        ps = [p for p in PARTS if p.mat == mname]
        if not ps:
            continue
        P, N, UV, C, W, F = [], [], [], [], [], []
        base = 0
        for p in ps:
            P.append(p.P); N.append(p.N); UV.append(p.UV); C.append(p.C); W.append(p.W)
            F.append(p.F + base); base += len(p.P)
        P, N, UV, C, W, F = map(np.concatenate, (P, N, UV, C, W, F))
        # top-4 weights
        top = np.argsort(-W, 1)[:, :4]
        tw = np.take_along_axis(W, top, 1)
        tw = np.clip(tw, 0, None); tw /= np.maximum(tw.sum(1, keepdims=True), 1e-9)
        top = np.where(tw > 0, top, 0)
        attrs = {"POSITION": acc(P.astype(np.float32), 5126, "VEC3", 34962, minmax=True),
                 "NORMAL": acc(N.astype(np.float32), 5126, "VEC3", 34962),
                 "TEXCOORD_0": acc(UV.astype(np.float32), 5126, "VEC2", 34962),
                 "COLOR_0": acc(lin(np.clip(C, 0, 1)).astype(np.float32), 5126, "VEC3", 34962),
                 "JOINTS_0": acc(top.astype(np.uint16), 5123, "VEC4", 34962),
                 "WEIGHTS_0": acc(tw.astype(np.float32), 5126, "VEC4", 34962)}
        idx = acc(F.reshape(-1).astype(np.uint32), 5125, "SCALAR", 34963)
        prims.append({"attributes": attrs, "indices": idx, "material": mat_idx[mname]})
        stats[mname] = (len(P), len(F))
    j["meshes"].append({"name": "Knight", "primitives": prims})
    nodes[mi]["mesh"] = 0
    for k in ("textures", "images", "samplers"):
        if not j[k]:
            del j[k]
    j["buffers"].append({"byteLength": len(blob)})
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    while len(blob) % 4:
        blob.append(0)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(blob), 0x004E4942) + bytes(blob)
    pathlib.Path(path).write_bytes(out)
    return stats, len(out)


def main():
    underlayer()
    cg = cuirass()
    gorget()
    helm()
    pauldrons()
    limbs()
    sabatons()
    belt_and_skirt(cg)
    cape()
    out = HERE / "knight.glb"
    stats, size = write_glb(out)
    for k, (v, f) in stats.items():
        print(f"  {k:10s} {v:6d} vertices {f:6d} triangles")
    print(f"{len(PARTS)} parts -> {out.name} ({size / 1e6:.2f} MB)")
    # the viewer's copy: Artifacts don't serve .glb, so the page loads it as gzip + base64 text
    import base64, gzip
    txt = HERE / "knight.txt"
    txt.write_bytes(base64.b64encode(gzip.compress(out.read_bytes(), 9)))
    print(f"  + {txt.name} (gzip + base64 for the viewer, {txt.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
