"""Build a game sprite sheet from a character's painted directions (generalises walk_cycle.py build).

  python build_sheet.py <character.json> <out.webp> [--meta meta.json] [--key NAME]
                        [--height 118] [--fw 144] [--fh 152] [--foot-y 128] [--fpt F] [--idle I]

Reads character.json (see board.py): "frames", "mirror", "guide" and "directions" {DIR: {"file": ...}}. For each
painted direction it uses that direction's guide and the guide's sidecar .json (written by render_guide.py:
grid, ground line, standing-figure height in px).

Per painted image:
  alpha    OpenAI's transparent output leaves narrow gaps (between arm and torso) and painted ground shadows half
           transparent: alpha is remapped so < 96 is clear and > 224 opaque. A flat-magenta image is chroma-keyed.
  figures  connected components of the whole image, each assigned to the grid cell holding its centroid (never cut
           by grid lines; specks under 2 % of the largest dropped).
  scale    one per direction: median over frames of (guide figure height / painted figure height), times
           height / the guide's standing-figure px, so every clip and body (jog, child) ends at --height px for a
           standing figure (the hero: 118).
  anchor   horizontally the head + shoulders (top 45 % of the figure) are centred, so swinging legs don't shift the
           body; vertically the painted lowest pixel goes where the guide's lowest pixel is relative to its ground
           line, measured from --foot-y (the entity's ground point in the frame).
Rows are written in the game order S SW W NW N NE E SE. With "mirror": true, SE / E / NE are flips of SW / W / NW
(the legs swap, which in a walk cycle is a half-stride phase shift). Missing directions are left empty (a warning).
--meta writes {fw, fh, frames, idle, footY, fpt} under "characters"[--key] (default: the character's name, lower
case). fpt (frames per tile walked) defaults to 5 x frames / 8; idle to the guide frame with the feet closest.
"""
import json, pathlib, sys
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = pathlib.Path(__file__).resolve().parent
ROWS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
MIRROR = {"SE": "SW", "E": "W", "NE": "NW"}


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def load_rgba(path):
    a = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
    if (a[..., 3] < 128).mean() > 0.2:                          # real transparency (OpenAI --background transparent)
        a[..., 3] = np.clip((a[..., 3] - 96) / (224 - 96), 0, 1) * 255
    else:                                                       # flat magenta: chroma key with un-mixing + despill
        key = np.array([255.0, 0.0, 255.0])
        m = np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
        al = np.clip((200.0 - m) / 130.0, 0, 1)
        col = np.clip((a[..., :3] - (1 - al)[..., None] * key) / np.maximum(al, 1e-3)[..., None], 0, 255)
        spill = np.maximum(np.minimum(col[..., 0], col[..., 2]) - col[..., 1] - 4, 0)
        col[..., 0] -= spill; col[..., 2] -= spill
        al[al < 0.06] = 0
        a = np.dstack([col, al * 255])
    return a.astype(np.uint8)


def figures(arr, cols, rows):
    """One RGBA crop per grid cell, in reading order: whole connected figures assigned by centroid."""
    H, W = arr.shape[:2]
    mask = arr[..., 3] > 20
    lab, n = ndimage.label(ndimage.binary_dilation(mask, iterations=2))
    lab = lab * mask
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    big = sizes.max() if n else 0
    cells = [[] for _ in range(cols * rows)]
    for k in range(1, n + 1):
        if sizes[k - 1] < big * 0.02:
            continue
        ys, xs = np.nonzero(lab == k)
        c = min(cols - 1, int(xs.mean() / (W / cols))); r = min(rows - 1, int(ys.mean() / (H / rows)))
        cells[r * cols + c].append(k)
    out = []
    for i, comps in enumerate(cells):
        if not comps:
            raise SystemExit(f"no figure in cell {i + 1}")
        keep = np.isin(lab, comps)
        rgba = arr.copy(); rgba[~keep, 3] = 0
        ys, xs = np.nonzero(keep)
        out.append(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    return out


def guide_cells(path, side):
    """Per frame: (figure height px, lowest pixel below the ground line px, feet spread) of the guide."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    fg = ~((a[..., 0] > 190) & (a[..., 1] < 90) & (a[..., 2] > 190))
    cw, ch = side["cell"]
    res = []
    for i in range(side["frames"]):
        r, c = divmod(i, side["cols"])
        m = fg[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
        ys, xs = np.nonzero(m)
        top, bot = ys.min(), ys.max(); h = bot - top
        band = np.nonzero(m[bot - int(h * 0.12):bot + 1].any(0))[0]
        res.append((h, bot - side["ground_y"], (band.max() - band.min()) / h))
    return res


def place(frame, scale, low, fw, fh, foot_y):
    im = Image.fromarray(frame, "RGBA")
    im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    a = np.asarray(im)[..., 3].astype(np.float32)
    top = a[: max(1, int(a.shape[0] * 0.45))].sum(0)
    cx = (top * np.arange(len(top))).sum() / max(top.sum(), 1)
    out = Image.new("RGBA", (fw, fh))
    x, y = round(fw / 2 - cx), round(foot_y + low - im.height)
    if x < 0 or y < 0 or x + im.width > fw or y + im.height > fh:
        print("  warning: frame clipped", (x, y, im.width, im.height), "- use a bigger --fw / --fh")
    out.paste(im, (x, y), im)
    return out


def guide_for(ch, base, d):
    g = ch.get("guide") or "walk"
    folder = HERE.parent / "guides" / g / f"{ch['frames']}f"
    return (folder if folder.exists() else base / g) / f"{d}.png"


def main():
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    ch = json.loads(src.read_text(encoding="utf-8")); base = src.parent
    n = ch["frames"]
    H = float(opt("--height", 118)); fw, fh, foot_y = int(opt("--fw", 144)), int(opt("--fh", 152)), int(opt("--foot-y", 128))
    rows, idle = {}, None
    for d in ROWS:
        if ch.get("mirror") and d in MIRROR:
            continue
        info = ch.get("directions", {}).get(d, {})
        if not info.get("file"):
            print(d, "not painted: left empty"); continue
        gp = guide_for(ch, base, d)
        side = json.loads(gp.with_suffix(".json").read_text())
        g = guide_cells(gp, side)
        fr = figures(load_rgba(base / info["file"]), side["cols"], side["rows"])[:n]
        k = H / side["fig_px"]
        scale = float(np.median([g[i][0] / fr[i].shape[0] for i in range(n)])) * k
        rows[d] = [place(fr[i], scale, g[i][1] * k, fw, fh, foot_y) for i in range(n)]
        if idle is None:
            idle = int(np.argmin([x[2] for x in g[: n // 2]]))
        print(d, "scale %.3f" % scale, "heights", [f.shape[0] for f in fr])
    if ch.get("mirror"):
        for m, b in MIRROR.items():
            if b in rows:
                rows[m] = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in rows[b]]
    sheet = Image.new("RGBA", (fw * n, fh * 8))
    for r, d in enumerate(ROWS):
        for c, f in enumerate(rows.get(d, [])):
            sheet.paste(f, (c * fw, r * fh))
    sheet.save(out, quality=90, method=6)
    entry = {"fw": fw, "fh": fh, "frames": n, "idle": int(opt("--idle", idle or 0)), "footY": foot_y,
             "fpt": float(opt("--fpt", round(5 * n / 8, 2)))}
    print(out, entry)
    if "--meta" in sys.argv:
        mp = pathlib.Path(opt("--meta", "")); meta = json.loads(mp.read_text()) if mp.exists() else {"characters": {}}
        meta.setdefault("characters", {})[opt("--key", ch["name"].lower())] = entry
        mp.write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
