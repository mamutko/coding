"""Join two half-cycle paintings (one step each, painted over stick_guide.py --halves) into one full painted sheet in
the full guide's layout, so grid_check, review.py, board.py and build_sheet.py read it like any other painting.

  python join_halves.py <h1.png> <h2.png> <out.png> [--frames 12] [--cols 6] [--cell 384x512]

Each half is a 3 x 2 grid of cells (frames/2 figures); its figures go, in order, to frames 1..frames/2 and
frames/2+1..frames of the full cols x rows grid. Figures are moved whole: each is found as connected pieces and given
to the half's cell holding its centroid (like build_sheet.figures), then pasted at the same offset in its new cell,
so a figure that strays a little over its cell edge is not cut.
"""
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, __import__("pathlib").Path(__file__).parent.as_posix())
from build_sheet import load_rgba
from walk_cycle import components


def opt(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def main():
    h1, h2, out = sys.argv[1:4]
    n, cols = int(opt("--frames", 12)), int(opt("--cols", 6)); rows = -(-n // cols)
    cw, ch = map(int, opt("--cell", "384x512").split("x"))
    hn = n // 2; hc = -(-hn // 2)
    full = np.zeros((rows * ch, cols * cw, 4), np.uint8)
    for h, path in ((0, h1), (1, h2)):
        a = load_rgba(path)
        a = np.asarray(Image.fromarray(a).resize((hc * cw, 2 * ch), Image.LANCZOS)) if a.shape[:2] != (2 * ch, hc * cw) else a
        mask = a[..., 3] > 20
        lab, sizes = components(mask)
        big = sizes.max()
        for k in range(1, len(sizes)):
            if sizes[k] < big * 0.01:
                continue
            ys, xs = np.nonzero(lab == k)
            cc, rr = min(hc - 1, int(xs.mean() // cw)), min(1, int(ys.mean() // ch))
            j = rr * hc + cc
            if j >= hn:
                continue
            i = h * hn + j; r, c = divmod(i, cols)
            ty, tx = ys + (r - rr) * ch, xs + (c - cc) * cw
            ok = (ty >= 0) & (ty < full.shape[0]) & (tx >= 0) & (tx < full.shape[1])
            full[ty[ok], tx[ok]] = a[ys[ok], xs[ok]]
    Image.fromarray(full, "RGBA").save(out)
    print("joined", h1, "+", h2, "->", out)


if __name__ == "__main__":
    main()
