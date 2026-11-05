"""Turn the raw AI-generated magenta-background sheets into game-ready assets.

Usage:  python process_art.py <raw_dir> <out_dir>

raw_dir must contain: hero.png skeleton.png ghoul.png spider.png wraith.png demon.png
(1024x1536, 4 cols x 8 rows), items.png (1536x1024, 6x4), props.png (1536x1024, 4x2),
floor.png, wall.png (1024x1024 textures).
"""
import json, sys, pathlib
from PIL import Image
import numpy as np

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

# ---- characters: 4 frames x 8 directions -------------------------------------------
FRAME_H = 128
for name in ["hero", "skeleton", "ghoul", "spider", "wraith", "demon"]:
    arr = key_out(Image.open(raw / f"{name}.png"))
    H, W = arr.shape[:2]
    cw, ch = W // 4, H // 8
    cells = [[keep_main(arr[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw], 0.04) for c in range(4)] for r in range(8)]
    # union bbox (cell-relative) over all frames keeps the model's own centring stable
    boxes = [bbox(cells[r][c]) for r in range(8) for c in range(4)]
    boxes = [b for b in boxes if b]
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    # make horizontally symmetric around the cell centre so the anchor is the centre
    half = max(cw / 2 - x0, x1 - cw / 2)
    x0, x1 = int(cw / 2 - half), int(cw / 2 + half)
    x0, x1 = max(0, x0), min(cw, x1)
    fw0, fh0 = x1 - x0, y1 - y0
    s = FRAME_H / fh0
    fw, fh = max(1, round(fw0 * s)), FRAME_H
    sheet = Image.new("RGBA", (fw * 4, fh * 8))
    for r in range(8):
        for c in range(4):
            crop = Image.fromarray(cells[r][c][y0:y1, x0:x1], "RGBA").resize((fw, fh), Image.LANCZOS)
            sheet.paste(crop, (c * fw, r * fh))
    sheet.save(out / f"{name}.webp", quality=88, method=6)
    meta["characters"][name] = {"fw": fw, "fh": fh, "frames": 4}
    print(name, fw, fh)

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
