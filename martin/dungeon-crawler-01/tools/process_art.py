"""Turn the raw AI-generated magenta-background sheets into game-ready assets.

Usage:  python process_art.py <raw_dir> <out_dir>

Characters with an 8-frame walk cycle (hero, and any monster already built by walk_cycle.py) are
skipped and their meta.json entries kept; walk_cycle.py builds those sheets.

raw_dir must contain: skeleton.png ghoul.png spider.png wraith.png demon.png
(1024x1536, 4 cols x 8 rows), items.png (1536x1024, 6x4), props.png (1536x1024, 4x2),
floor.png, wall.png (1024x1024 textures).
"""
import json, sys, pathlib
from PIL import Image
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from walk_cycle import components, FOOT_Y

raw, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
KEY = np.array([255.0, 0.0, 255.0])


def key_out(img):
    """Soft chroma key on magenta with colour un-mixing and despill -> RGBA float array."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # "magentaness": high when r and b are high and g is low
    m = np.minimum(r, b) - g
    alpha = np.clip((200.0 - m) / (200.0 - 70.0), 0, 1)
    # un-mix edge pixels: C = (P - (1-a)K) / a
    safe = np.maximum(alpha, 1e-3)[..., None]
    col = (a - (1 - alpha)[..., None] * KEY) / safe
    col = np.clip(col, 0, 255)
    # despill: limit min(r,b) to g + small margin where it still looks magenta
    r, g, b = col[..., 0], col[..., 1], col[..., 2]
    spill = np.maximum(np.minimum(r, b) - g - 4, 0)
    col[..., 0] -= spill
    col[..., 2] -= spill
    alpha[alpha < 0.06] = 0
    return np.dstack([col, alpha * 255]).astype(np.uint8)


def keep_main(cell, frac=0.12, drop_edge=False):
    """Drop alpha islands smaller than frac x the largest one (fragments of neighbour cells)."""
    from collections import deque
    m = cell[..., 3] > 20
    h, w = m.shape
    lab = np.zeros((h, w), np.int32)
    sizes = [0]
    for y0 in range(h):
        row = m[y0]
        for x0 in np.nonzero(row & (lab[y0] == 0))[0]:
            if lab[y0, x0]:
                continue
            n = len(sizes); sizes.append(0)
            q = deque([(y0, x0)]); lab[y0, x0] = n
            while q:
                y, x = q.popleft(); sizes[n] += 1
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = n; q.append((yy, xx))
    if len(sizes) <= 2:
        return cell
    sizes = np.array(sizes)
    good = sizes >= sizes.max() * frac
    good[0] = False
    if drop_edge:  # islands touching the cell border (other than the largest) are neighbour bleed
        edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        big = int(np.argmax(sizes))
        for e in edge:
            if e and e != big:
                good[e] = False
    out = cell.copy()
    drop = ~good[lab] & (cell[..., 3] > 0)
    # also drop faint pixels near dropped islands: simplest is zero all alpha not in good comps,
    # except faint (<=20) pixels, which are kept only if a good pixel is within the cell bbox
    out[drop & m, 3] = 0
    return out


def bbox(arr):
    ys, xs = np.nonzero(arr[..., 3] > 20)
    if len(xs) == 0:
        return None
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


meta = {"characters": {}, "items": {}, "props": {}}
_old = out / "meta.json"
old_chars = json.loads(_old.read_text()).get("characters", {}) if _old.exists() else {}
for n, e in old_chars.items():
    if e.get("frames") == 8:          # built by walk_cycle.py
        meta["characters"][n] = e

# ---- monsters: 4 frames x 8 directions -------------------------------------------------
# Each figure is found as a whole connected component of the whole sheet and assigned to the grid cell
# holding its centroid, so grid lines never cut a figure (the AI sheets let heads and legs cross them).
# Only the base rows S, SW, W, NW, N are used; SE, E, NE are their mirrors (the AI's right-facing rows
# were often wrong). Frames are placed with the head-and-shoulders centred and the lowest pixel at
# FOOT_Y + 4 (the nearer foot hangs slightly below the ground point in this view).
FH_M, TALL = 152, 124              # frame height; 90th-percentile figure height in px
BASE_ROWS, MIRROR_ROWS = [0, 1, 2, 3, 4], {5: 3, 6: 2, 7: 1}


def figures(arr, cols, rows):
    H, W = arr.shape[:2]
    cw, ch = W / cols, H / rows
    lab, sizes = components(arr[..., 3] > 20)
    big = sizes.max()
    owner = np.zeros_like(lab)       # label image -> cell index + 1
    yy, xx = np.indices(lab.shape)
    gridcell = (np.minimum(rows - 1, (yy / ch).astype(int)) * cols + np.minimum(cols - 1, (xx / cw).astype(int)))
    for n in range(1, len(sizes)):
        if sizes[n] < big * 0.02:
            continue
        m = lab == n
        ys, xs = np.nonzero(m)
        if np.ptp(xs) > 1.4 * cw or np.ptp(ys) > 1.4 * ch:   # two figures touching: split along the grid
            owner[m] = gridcell[m] + 1
        else:
            r = min(rows - 1, int(ys.mean() / ch)); c = min(cols - 1, int(xs.mean() / cw))
            owner[m] = r * cols + c + 1
    out = []
    for i in range(rows * cols):
        keep = owner == i + 1
        if not keep.any():
            raise SystemExit(f"no figure in cell {i}")
        ys, xs = np.nonzero(keep)
        rgba = arr.copy(); rgba[~keep, 3] = 0
        out.append(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    return out


for name in ["skeleton", "ghoul", "spider", "wraith", "demon"]:
    if name in meta["characters"]:
        print(name, "kept (walk cycle)")
        continue
    figs = figures(key_out(Image.open(raw / f"{name}.png")), 4, 8)
    base = [figs[r * 4 + c] for r in BASE_ROWS for c in range(4)]
    s_ = TALL / np.percentile([f.shape[0] for f in base], 90)
    placed = {}
    for r in BASE_ROWS:
        for c in range(4):
            im = Image.fromarray(figs[r * 4 + c], "RGBA")
            im = im.resize((max(1, round(im.width * s_)), max(1, round(im.height * s_))), Image.LANCZOS)
            a = np.asarray(im)[..., 3].astype(np.float32)
            cols_ = a[: max(1, int(a.shape[0] * 0.45))].sum(0)
            cx = (cols_ * np.arange(len(cols_))).sum() / max(cols_.sum(), 1)
            placed[r, c] = (im, cx)
    half = max(max(cx, im.width - cx) for im, cx in placed.values())
    fw = int(np.ceil(half)) * 2 + 4
    top = max(im.height for im, _ in placed.values()) - (FOOT_Y + 4)
    if top > 0:
        raise SystemExit(f"{name}: tallest frame {top}px too tall for FOOT_Y")
    sheet = Image.new("RGBA", (fw * 4, FH_M * 8))
    for (r, c), (im, cx) in placed.items():
        x, y = round(fw / 2 - cx), FOOT_Y + 4 - im.height
        f = Image.new("RGBA", (fw, FH_M)); f.paste(im, (x, y), im)
        sheet.paste(f, (c * fw, r * FH_M))
        if r in MIRROR_ROWS.values():
            for mr, br in MIRROR_ROWS.items():
                if br == r:
                    sheet.paste(f.transpose(Image.FLIP_LEFT_RIGHT), (c * fw, mr * FH_M))
    sheet.save(out / f"{name}.webp", quality=88, method=6)
    meta["characters"][name] = {"fw": fw, "fh": FH_M, "frames": 4, "footY": FOOT_Y, "fpt": 2}
    print(name, fw, FH_M, "scale %.3f" % s_)

# ---- item icons: 6 x 4 ------------------------------------------------------------------
ICON = 96
ITEM_NAMES = ["shortsword", "longsword", "greatsword", "handaxe", "battleaxe", "execaxe",
              "shortbow", "longbow", "bonebow", "leathercap", "greathelm", "leathertunic",
              "platemail", "leathergloves", "gauntlets", "leatherboots", "ironboots", "silverring",
              "rubyring", "skullring", "sapphireamulet", "bloodamulet", "bonetalisman", "potion"]
arr = key_out(Image.open(raw / "items.png"))
H, W = arr.shape[:2]
cw, ch = W // 6, H // 4
atlas = Image.new("RGBA", (ICON * 6, ICON * 4))
for i, n in enumerate(ITEM_NAMES):
    r, c = divmod(i, 6)
    cell = keep_main(arr[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw], 0.3, True)
    b = bbox(cell)
    im = Image.fromarray(cell[b[1]:b[3], b[0]:b[2]], "RGBA")
    k = (ICON - 6) / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    atlas.paste(im, (c * ICON + (ICON - im.width) // 2, r * ICON + (ICON - im.height) // 2))
    meta["items"][n] = [c * ICON, r * ICON]
atlas.save(out / "items.webp", quality=90, method=6)
meta["iconSize"] = ICON

# ---- props: 4 x 2, keep natural size (scaled) with bottom-centre anchor ---------------
PROP_NAMES = ["chest", "chestopen", "door", "stairs", "brazier", "bones", "urn", "gold"]
arr = key_out(Image.open(raw / "props.png"))
H, W = arr.shape[:2]
cw, ch = W // 4, H // 2
pieces = []
for i, n in enumerate(PROP_NAMES):
    r, c = divmod(i, 4)
    cell = keep_main(arr[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw], 0.12, True)
    b = bbox(cell)
    im = Image.fromarray(cell[b[1]:b[3], b[0]:b[2]], "RGBA")
    im = im.resize((round(im.width * 0.45), round(im.height * 0.45)), Image.LANCZOS)
    pieces.append((n, im))
# boss-room furnishings: decor.png (1264 x 848, 4 x 2, same style; generated from props.png as a style
# reference). Cell 8 (a summoning circle) is not used; the game draws its own rune circle. Figures are found
# as whole components (figures()), so loose rubble and candle flames stay with their prop.
DECOR_NAMES = ["throne", "altar", "candelabrum", "skullpile", "banner", "pillar", "sarcophagus"]
if (raw / "decor.png").exists():
    dfigs = figures(key_out(Image.open(raw / "decor.png")), 4, 2)
    k = 0.45 * 1536 / 1264      # same pixel scale as props.png
    for i, n in enumerate(DECOR_NAMES):
        im = Image.fromarray(dfigs[i], "RGBA")
        pieces.append((n, im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)))
pw = sum(p.width for _, p in pieces) + 2 * len(pieces)
ph = max(p.height for _, p in pieces)
patlas = Image.new("RGBA", (pw, ph))
x = 0
for n, im in pieces:
    patlas.paste(im, (x, 0))
    meta["props"][n] = [x, 0, im.width, im.height]
    x += im.width + 2
patlas.save(out / "props.webp", quality=90, method=6)

# ---- textures -------------------------------------------------------------------------
for n in ["floor", "wall"]:
    Image.open(raw / f"{n}.png").convert("RGB").resize((512, 512), Image.LANCZOS).save(
        out / f"{n}.jpg", quality=85)

(out / "meta.json").write_text(json.dumps(meta, indent=1))
print(json.dumps(meta))
