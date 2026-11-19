"""Build a game sprite sheet from a character's painted directions (generalises walk_cycle.py build).

  python build_sheet.py <character.json> <out.webp> [--meta meta.json] [--key NAME]
                        [--height 118] [--fw 144] [--fh 152] [--foot-y 128] [--fpt F] [--idle I] [--tile-px 67.88]
                        [--plant-check feet.png]

Reads character.json (see board.py): "frames", "mirror", "guide" and "directions" {DIR: {"file": ...}}. For each
painted direction it uses that direction's guide and the guide's sidecar .json (written by render_guide.py:
grid, ground line, standing-figure height in px, ground covered per loop, feet). With "from_guide": true the
guides themselves are the frames (a plain mannequin sheet, no painting).

Per painted image:
  alpha    OpenAI's transparent output leaves narrow gaps (between arm and torso) and painted ground shadows half
           transparent: alpha is remapped so < 96 is clear and > 224 opaque. A flat-magenta image is chroma-keyed.
  figures  connected components of the whole image, each assigned to the grid cell holding its centroid (never cut
           by grid lines; specks under 2 % of the largest dropped).
  scale    one per direction: median over frames of (guide figure height / painted figure height), times
           height / the guide's standing-figure px, so every clip and body (jog, child) ends at --height px for a
           standing figure (the hero: 118).
  register every painted figure is put back where its guide figure is. The model drifts: in a 6 x 2 sheet the
           figures of a row creep left by up to ~30 guide px from the first to the last, and the bottom row sits up
           to ~30 px low (learnings.md, "Translation drift"). Vertically the painted lowest pixel (the sole on the
           ground) goes on the guide's lowest pixel; horizontally the feet band (bottom 30 % of the figure) is
           slid over the guide's feet band to the best overlap, then refined (+-15 px) on the planted foot alone. The guide's own position in its cell is kept: it is
           the in-place mocap (cycle-mean pelvis at the cell centre, ground line = the ground point), so the body's
           natural sway stays and the planted foot slides backward at exactly the walking speed.
  place    scaled with LANCZOS straight from the painting, at sub-pixel position (no rounding jitter).
fpt      frames per tile walked, from the guide's cycle_px (ground covered per loop): frames / (cycle_px x scale /
         --tile-px), --tile-px = a tile's ground length in screen px (96 x 48 iso tiles: 96 / sqrt 2). With it, a
         game that advances frames by distance (anim += distance x fpt) keeps the planted foot still on the ground.
         Older sidecars without cycle_px: 5 x frames / 8.
Rows are written in the game order S SW W NW N NE E SE. With "mirror": true, SE / E / NE are flips of SW / W / NW
(the legs swap, which in a walk cycle is a half-stride phase shift). Missing directions are left empty (a warning).
--meta writes {fw, fh, frames, idle, footY, fpt} under "characters"[--key] (default: the character's name, lower
case). idle defaults to the guide frame with the feet closest.
Prints per direction where each figure went in its guide cell. --plant-check writes the feet check: per stance,
the feet of its frames one under the other, shifted by the ground walked, with a red line at the guide's planted
foot: the painted planted foot should stay on the line (a couple of px is normal; the guide's own is within 0.1 px).
"""
import json, math, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw
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


def guide_mask(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    return ~((a[..., 0] > 190) & (a[..., 1] < 90) & (a[..., 2] > 190))


def register(frame, s, gcell, plant=None):
    """Where the painted figure, scaled by s, goes in its guide cell (bool mask): its top-left in guide px.
    Vertically the soles go on the guide's soles; horizontally the feet band (bottom 30 %) is slid over the guide's
    to the best overlap, then, with plant = the planted foot's x in the cell (guide px), refined within +-15 px on
    that foot alone (the lowest 12 % of the guide figure within +-50 px of it), so the foot on the ground lands
    exactly where the guide's is even when the painted stride is a little longer or shorter."""
    im = Image.fromarray(frame, "RGBA")
    m = np.asarray(im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.BILINEAR))[..., 3] > 80
    gy, _ = np.nonzero(gcell)
    py, _ = np.nonzero(m)
    top = gy.max() - py.max() * im.height * s / m.shape[0]          # soles on the guide's soles
    cw, pw = gcell.shape[1], m.shape[1]

    def slide(frac, xs, cols=None):
        gb = gcell[int(gy.max() - frac * np.ptp(gy)):gy.max() + 1].astype(np.float32)
        pb = m[int(py.max() - frac * np.ptp(py)):py.max() + 1].astype(np.float32)
        h = min(len(gb), len(pb)); gb, pb = gb[-h:], pb[-h:]
        if cols is not None:
            gb[:, :max(0, cols[0])] = 0; gb[:, cols[1]:] = 0
        sc = [(gb[:, max(0, x):min(cw, x + pw)] * pb[:, max(0, -x):min(pw, cw - x)]).sum() for x in xs]
        return xs[int(np.argmax(sc))]
    left = slide(0.3, list(range(-pw + 1, cw)))
    if plant is not None:
        left = slide(0.12, list(range(left - 15, left + 16)), (int(plant - 50), int(plant + 50)))
    return left, float(top)


def place(frame, sc, x, y, fw, fh):
    """The frame scaled by sc, its top-left at (x, y) in a fw x fh frame: sub-pixel exact (no rounding jitter)."""
    pad = 4
    src = Image.fromarray(np.pad(frame, ((pad, pad), (pad, pad), (0, 0))), "RGBA")
    x0, y0 = x - pad * sc, y - pad * sc                             # the padded frame's top-left, frame px
    ix, iy = int(np.floor(x0)) + 1, int(np.floor(y0)) + 1           # the first whole frame px inside it
    bx, by = (ix - x0) / sc, (iy - y0) / sc                         # ... in source px (the sub-pixel offset)
    w, h = int((src.width - bx) * sc), int((src.height - by) * sc)
    small = src.resize((w, h), Image.LANCZOS, box=(bx, by, bx + w / sc, by + h / sc))
    a = np.asarray(small)[..., 3]
    ys, xs = np.nonzero(a > 8)
    if len(xs) and (ix + xs.min() < 0 or iy + ys.min() < 0 or ix + xs.max() >= fw or iy + ys.max() >= fh):
        print("  warning: frame clipped", (ix + xs.min(), iy + ys.min(), ix + xs.max(), iy + ys.max()),
              "- use a bigger --fw / --fh")
    out = Image.new("RGBA", (fw, fh))
    out.paste(small, (ix, iy), small)
    return out


def plant_panels(frames, side, d, k, fw, foot_y, band=46):
    """The feet check: for each stance (one foot the lower in the guide), the feet of its frames one under the
    other, each shifted by the ground walked since the stance began, with a red line at the guide's planted ball
    of the foot. A planted foot stays on the line; a sliding one drifts along it."""
    feet = side.get("feet")
    if not feet or "cycle_px" not in side:
        return []
    feet = feet[d] if isinstance(feet, dict) else feet
    n = len(frames)
    a = math.radians(45 * ((8 - ROWS.index(d)) % 8))
    step = side["cycle_px"] * k / n * np.array([math.sin(a), 0.5 * math.cos(a)])   # ground per frame, screen px
    out = []
    for foot in (0, 1):
        down = [i for i in range(n) if (feet[i][2] < -3 if foot == 0 else feet[i][2] > 3)]   # this foot the lower
        if not down:
            continue
        if down[0] == 0 and down[-1] == n - 1:                      # a stance across the loop's end: unwrap
            gap = next(j for j in range(len(down)) if down[j] != j)
            down = down[gap:] + [i + n for i in down[:gap]]
        panel = Image.new("RGBA", (fw + 120, band * len(down)), (30, 28, 34, 255))
        dr = ImageDraw.Draw(panel)
        gx = 60 + fw / 2 + feet[down[0] % n][foot][0] * k
        for j, t in enumerate(down):
            off = step * (t - down[0])
            y0 = int(foot_y - 30 + off[1])
            panel.alpha_composite(frames[t % n].crop((0, y0, fw, y0 + band)), (int(60 + off[0]), j * band))
        dr.line([(gx, 0), (gx, panel.height)], fill=(255, 60, 60, 255))
        out.append((f"{d} {'left' if foot == 0 else 'right'}", panel))
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
    tile_px = float(opt("--tile-px", 96 / math.sqrt(2)))
    rows, idle, cycle, panels = {}, None, None, []
    for d in ROWS:
        if ch.get("mirror") and d in MIRROR:
            continue
        gp = guide_for(ch, base, d)
        info = ch.get("directions", {}).get(d, {})
        pp = gp if ch.get("from_guide") else base / info["file"] if info.get("file") else None
        if pp is None:
            print(d, "not painted: left empty"); continue
        side = json.loads(gp.with_suffix(".json").read_text())
        g = guide_cells(gp, side)
        gmask = guide_mask(gp)
        fr = figures(load_rgba(pp), side["cols"], side["rows"])[:n]
        k = H / side["fig_px"]
        s = float(np.median([g[i][0] / fr[i].shape[0] for i in range(n)]))
        cw, chh = side["cell"]
        feet = side.get("feet")
        feet = feet.get(d) if isinstance(feet, dict) else feet
        row, shifts = [], []
        for i in range(n):
            r, c = divmod(i, side["cols"])
            plant = None
            if feet and abs(feet[i][2]) > 3:                        # one foot clearly the lower: it is planted
                plant = cw / 2 + feet[i][0 if feet[i][2] < 0 else 1][0]
            left, top = register(fr[i], s, gmask[r * chh:(r + 1) * chh, c * cw:(c + 1) * cw], plant)
            row.append(place(fr[i], s * k, fw / 2 + (left - cw / 2) * k, foot_y + (top - side["ground_y"]) * k, fw, fh))
            shifts.append((left, round(top)))
        rows[d] = row
        if idle is None:                                            # the feet closest together on the ground
            idle = int(np.argmin([math.hypot(f[0][0] - f[1][0], 2 * (f[0][1] - f[1][1])) for f in feet]) if feet
                       else np.argmin([x[2] for x in g[: n // 2]]))
        if cycle is None and "cycle_px" in side:
            cycle = side["cycle_px"] * k / tile_px
        panels += plant_panels(row, side, d, k, fw, foot_y)
        print(d, "scale %.3f" % (s * k), "left, top in the guide cell:", shifts)
    if ch.get("mirror"):
        for m, b in MIRROR.items():
            if b in rows:
                rows[m] = [f.transpose(Image.FLIP_LEFT_RIGHT) for f in rows[b]]
    sheet = Image.new("RGBA", (fw * n, fh * 8))
    for r, d in enumerate(ROWS):
        for c, f in enumerate(rows.get(d, [])):
            sheet.paste(f, (c * fw, r * fh))
    sheet.save(out, quality=90, method=6)
    if "--plant-check" in sys.argv and panels:
        W = sum(p.width + 8 for _, p in panels); H = max(p.height for _, p in panels) + 14
        im = Image.new("RGBA", (W, H), (12, 12, 15, 255)); dr = ImageDraw.Draw(im); x = 0
        for label, p in panels:
            im.alpha_composite(p, (x, 14)); dr.text((x + 2, 1), label, fill=(225, 225, 225)); x += p.width + 8
        im.resize((W * 2, H * 2), Image.NEAREST).save(opt("--plant-check", ""))
        print("feet check ->", opt("--plant-check", ""))
    fpt = round(n / cycle, 2) if cycle else round(5 * n / 8, 2)
    if cycle:
        print(f"ground per loop {cycle:.3f} tiles -> fpt {fpt}")
    entry = {"fw": fw, "fh": fh, "frames": n, "idle": int(opt("--idle", idle or 0)), "footY": foot_y,
             "fpt": float(opt("--fpt", fpt))}
    print(out, entry)
    if "--meta" in sys.argv:
        mp = pathlib.Path(opt("--meta", "")); meta = json.loads(mp.read_text()) if mp.exists() else {"characters": {}}
        meta.setdefault("characters", {})[opt("--key", ch["name"].lower())] = entry
        mp.write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
