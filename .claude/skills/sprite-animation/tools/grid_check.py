"""Check a painted walk-cycle image against its pose guide, for any grid.

  python grid_check.py <guide.png> <painted.png> <cols> <rows> [--dirs S,SW,...] [--dir NW] [--ref reference.png]
                       [--json out.json]

Per cell:
  spread  width of the bottom 12 % of the figure (the feet) / its height. Tells the two halves of the stride apart in
          SW / W / NW (and SE / E / NE); "!" when off the guide's by more than 0.2.
  low     (lowest pixel left of the hips - lowest right of them) / height. Judged in S and N: "!" when its sign differs
          from the guide's where the guide's is beyond +-0.08.
  ghost   the largest washed-out blob in the legs (lower 40 % of the figure): opaque pixels with low saturation
          (< 0.36) and mid value (55-150), opened by 2 px. OpenAI sometimes paints the FAR boot (or arm) as a pale,
          desaturated, outline-less shape: opaque (alpha ~250), but it reads as a ghost, especially on a dark floor.
          "!" above GHOST_PX (scaled to the cell area). Calibrated on one image: it caught the clear case (957 px vs
          0-41 elsewhere) but NOT two milder ones, so also look at every image on a DARK backdrop. Also counted:
          see-through paint in the legs (alpha 25-230, eroded 4 px so the anti-aliased outline drops out), in case
          a model paints real transparency. Not the rest of the body: OpenAI's background removal leaves the narrow
          gaps between arm and torso half transparent (fixed by build_sheet.py's alpha clean-up, not a fault of the
          painting), which flagged 7 good S frames before this was limited to the legs.
--dirs names the direction of each row (one row per direction); --dir the one direction of a single-direction image
(S and N are judged by "low", the rest by spread); with neither, every cell is judged by spread.
--ref   colour drift: histogram intersection (6 x 6 x 6 RGB bins, opaque pixels) of the whole painting with the
        approved character reference. Calibrated on the ranger: repaints from the same description 0.74-0.84, a
        visibly different look 0.46, another model's ranger 0.17. "check" below 0.70, "DRIFT" below 0.55.
--json  also write the numbers (for board.py).
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

GHOST_PX = 300          # at a 384 x 512 cell; scaled by cell area


def load(path):
    im = np.asarray(Image.open(path).convert("RGBA")).astype(int)
    if (im[..., 3] < 128).mean() > 0.2:                       # real transparency
        return im[..., 3] > 128, im
    fg = ~((im[..., 0] > 190) & (im[..., 1] < 90) & (im[..., 2] > 190))
    return fg, im


def cell_stats(fg, im, cols, rows):
    H, W = fg.shape
    ch, cw = H / rows, W / cols
    out = []
    for r in range(rows):
        for c in range(cols):
            y0, y1, x0, x1 = round(r * ch), round((r + 1) * ch), round(c * cw), round((c + 1) * cw)
            m = fg[y0:y1, x0:x1]
            ys, xs = np.nonzero(m)
            if len(ys) == 0:
                out.append((np.nan, np.nan, 0)); continue
            top, bot = ys.min(), ys.max(); h = bot - top
            band = m[bot - int(h * 0.12):bot + 1]; bx = np.nonzero(band.any(0))[0]
            mid = int(np.nonzero(m[top + int(h * 0.45):top + int(h * 0.55)].any(0))[0].mean())
            lb = np.nonzero(m[:, :mid].any(1))[0]; rb = np.nonzero(m[:, mid:].any(1))[0]
            low = ((lb.max() if len(lb) else bot) - (rb.max() if len(rb) else bot)) / h
            rgb = im[y0:y1, x0:x1, :3].astype(float)
            mx, mn = rgb.max(-1), rgb.min(-1)
            sat = (mx - mn) / np.maximum(mx, 1)
            legs = np.zeros_like(m); legs[top + int(h * 0.6):] = True
            faded = ndimage.binary_opening(m & legs & (sat < 0.36) & (mx > 55) & (mx < 150), iterations=2)
            lab, n = ndimage.label(faded)
            ghost = int(max([0] + list(ndimage.sum(faded, lab, range(1, n + 1)))))
            a = im[y0:y1, x0:x1, 3]
            semi = (a > 25) & (a < 230) & legs & (a.min() < 128)   # only for images with real transparency
            ghost = max(ghost, int(ndimage.binary_erosion(semi, iterations=4).sum()))
            out.append(((bx.max() - bx.min()) / h, low, ghost))
    return out, ch * cw


def colour_hist(path):
    im = np.asarray(Image.open(path).convert("RGBA"))
    px = im[im[..., 3] > 200][:, :3].astype(int) // 43                  # 6 bins per channel
    h = np.bincount(px[:, 0] * 36 + px[:, 1] * 6 + px[:, 2], minlength=216).astype(float)
    return h / max(h.sum(), 1)


def drift(painted, ref):
    """1 = the same colours as the reference; see --ref."""
    return float(np.minimum(colour_hist(painted), colour_hist(ref)).sum())


def main():
    guide, painted, cols, rows = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    dirs = sys.argv[sys.argv.index("--dirs") + 1].split(",") if "--dirs" in sys.argv else None
    if "--dir" in sys.argv:
        dirs = [sys.argv[sys.argv.index("--dir") + 1]] * rows
    G, _ = cell_stats(*load(guide), cols, rows)
    P, area = cell_stats(*load(painted), cols, rows)
    gmax = GHOST_PX * area / (384 * 512)
    bad_stride = bad_ghost = 0
    offs, ghs = [], []
    print("cell  dir   guide spread/low   painted spread/low  ghost")
    for i, (g, p) in enumerate(zip(G, P)):
        r, c = divmod(i, cols)
        d = dirs[r] if dirs else "-"
        if d in ("S", "N"):
            off = abs(g[1]) > 0.08 and np.sign(g[1]) != np.sign(p[1])
        else:
            off = abs(g[0] - p[0]) > 0.2
        gh = p[2] > gmax
        bad_stride += off; bad_ghost += gh
        offs.append(bool(off)); ghs.append(bool(gh))
        print(f"{r + 1},{c + 1:<3} {d:<4}  {g[0]:5.2f} {g[1]:+5.2f}       {p[0]:5.2f} {p[1]:+5.2f}     {p[2]:5d} "
              f"{'!stride' if off else ''} {'!ghost' if gh else ''}")
    n = len(G)
    print(f"stride: {n - bad_stride} of {n} cells match; ghost limbs: {bad_ghost} cells (threshold {gmax:.0f} px)")
    res = dict(n=n, match=int(n - bad_stride), ghost=int(bad_ghost), gs=[round(float(g[0]), 3) for g in G],
               ps=[round(float(p[0]), 3) for p in P], off=offs, ghosts=ghs)
    if "--ref" in sys.argv:
        d = drift(painted, sys.argv[sys.argv.index("--ref") + 1])
        res["colour"] = round(d, 3)
        print(f"colour match with the reference: {d:.2f}" + ("  DRIFT" if d < 0.55 else "  check" if d < 0.70 else ""))
    if "--json" in sys.argv:
        import json
        open(sys.argv[sys.argv.index("--json") + 1], "w").write(json.dumps(res))


if __name__ == "__main__":
    main()
