"""Slice AI walk-cycle images into normalised frames and write data.js for the viewer.
Background: alpha if present, else chroma-key magenta. Figures = connected components assigned to the
grid cell holding their centroid (never cut by grid lines). Each frame: scaled per direction to a common
figure height, head-and-shoulders centred, lowest pixel on the ground line."""
import base64, io, json, sys, pathlib
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = pathlib.Path(sys.argv[1]); DST = pathlib.Path(sys.argv[2])
FW, FH, FOOT, FIG_H = 150, 196, 186, 168
D8 = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]

def rgba(path):
    im = Image.open(path).convert("RGBA")
    a = np.array(im).astype(np.float32)
    if a[..., 3].min() < 250:                # real alpha
        return a
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # magenta distance: high R and B, low G
    mag = np.clip(((np.minimum(r, b) - g) - 60) / 120, 0, 1)   # 1 = pure background
    alpha = 1 - mag
    # despill: pull magenta tint out of edge pixels
    spill = np.clip(np.minimum(r, b) - g, 0, None) * (1 - alpha)
    a[..., 0] -= spill * 0.8; a[..., 2] -= spill * 0.8
    a[..., 3] = alpha * 255
    return np.clip(a, 0, 255)

def figures(a, rows, cols):
    h, w = a.shape[:2]
    m = a[..., 3] > 40
    small = m[::3, ::3]
    small = ndimage.binary_closing(small, iterations=2)
    lab, n = ndimage.label(small)
    sizes = ndimage.sum(small, lab, range(1, n + 1))
    if n == 0: return {}
    keep = [i + 1 for i, s in enumerate(sizes) if s >= 0.02 * sizes.max()]
    cells = {}
    for k in keep:
        ys, xs = np.nonzero(lab == k)
        cy, cx = ys.mean() * 3, xs.mean() * 3
        cell = (min(rows - 1, int(cy / h * rows)), min(cols - 1, int(cx / w * cols)))
        cells.setdefault(cell, []).append(k)
    out = {}
    for cell, ks in cells.items():
        mask_s = np.isin(lab, ks)
        mask = np.kron(mask_s, np.ones((3, 3), bool))[:h, :w] & m | (np.kron(mask_s, np.ones((3, 3), bool))[:h, :w] & (a[..., 3] > 5))
        ys, xs = np.nonzero(mask)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        crop = a[y0:y1, x0:x1].copy(); crop[..., 3] *= mask[y0:y1, x0:x1]
        out[cell] = crop
    return out

def frame(crop, scale):
    im = Image.fromarray(crop.astype(np.uint8), "RGBA")
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    al = np.array(im)[..., 3].astype(float)
    top = al[: int(im.height * 0.45)]
    cx = (top.sum(0) * np.arange(im.width)).sum() / max(top.sum(), 1)
    canvas = Image.new("RGBA", (FW, FH))
    canvas.paste(im, (int(round(FW / 2 - cx)), FOOT - im.height), im)
    return canvas

def enc(im, fmt="WEBP", **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return base64.b64encode(b.getvalue()).decode()

def strip(frames):
    s = Image.new("RGBA", (FW * len(frames), FH))
    for i, f in enumerate(frames): s.paste(f, (i * FW, 0))
    return "data:image/webp;base64," + enc(s, quality=88, method=6)

def build_row(crops):
    hs = [c.shape[0] for c in crops]
    scale = FIG_H / float(np.median(hs))
    return [frame(c, scale) for c in crops]

def raw_thumb(path, width=640):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (52, 60, 70, 255)); bg.alpha_composite(im)
    bg = bg.convert("RGB").resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    return "data:image/jpeg;base64," + enc(bg, "JPEG", quality=80)

sets = []
def per_direction(key, label, prefix, note):
    dirs, raws, report = {}, {}, {}
    for d in D8:
        p = OUT / f"{prefix}{d}.png"
        figs = figures(rgba(p), 2, 4)
        crops = [figs[(r, c)] for r in range(2) for c in range(4) if (r, c) in figs]
        report[d] = len(crops)
        dirs[d] = {"strip": strip(build_row(crops)), "n": len(crops)}
        raws[d] = raw_thumb(p)
    sets.append({"key": key, "label": label, "note": note, "dirs": dirs, "raws": raws})
    print(key, report)

def oneshot(key, label, path, rows, cols, rowlabels, note):
    figs = figures(rgba(OUT / path), rows, cols)
    dirs = {}
    for r in range(rows):
        crops = [figs[(r, c)] for c in range(cols) if (r, c) in figs]
        dirs[rowlabels[r]] = {"strip": strip(build_row(crops)), "n": len(crops)}
    sets.append({"key": key, "label": label, "note": note, "dirs": dirs, "raws": {"sheet": raw_thumb(OUT / path, 900)},
                 "rows": rowlabels})
    print(key, {k: v["n"] for k, v in dirs.items()})

notes = json.loads((pathlib.Path(__file__).parent / "notes.json").read_text())
per_direction("openai-v2", "OpenAI · per direction, text only", "openai-v2-", notes["openai-v2"])
per_direction("google-v2", "Google · per direction, text only", "google-v2-", notes["google-v2"])
per_direction("openai-v1", "OpenAI · per direction, chained reference", "openai-", notes["openai-v1"])
per_direction("google-v1", "Google · per direction, chained reference", "google-", notes["google-v1"])
oneshot("openai-oneshot", "OpenAI · whole sheet in one image", "openai-oneshot.png", 8, 8,
        ["row 1 (S)", "row 2 (SW)", "row 3 (W)", "row 4 (NW)", "row 5 (N)", "row 6 (NE)", "row 7 (E)", "row 8 (SE)"], notes["openai-oneshot"])
oneshot("google-oneshot", "Google · whole sheet in one image", "google-oneshot.png", 6, 10,
        [f"row {i+1}" for i in range(6)], notes["google-oneshot"])
DST.write_text("window.SPRITES = " + json.dumps({"sets": sets, "fw": FW, "fh": FH, "foot": FOOT}) + ";\n")
print("bytes", DST.stat().st_size)
