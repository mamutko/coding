"""Makes the neck and tail's scale texture tile: python tools/dragon/scale_tile.py [--period 85.5] [--n 8] [--seam 40]

art/characters/dragon/paint/scales.png is a square of the body's scales painted flat (scales.prompt.txt; the game adds
the shading). The scales repeat every --period px across and down (found by autocorrelation), so a crop of --n periods
nearly tiles on its own; the leftover mismatch at its edges is hidden by blending it with itself shifted half a tile,
whose seams are in the middle: the shifted copy is used within --seam px of an edge, the crop everywhere else.
Writes paint/scales.tile.png.
"""
import argparse, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'art', 'characters', 'dragon', 'paint')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', type=float, default=85.5)
    ap.add_argument('--n', type=int, default=8)
    ap.add_argument('--seam', type=int, default=40)
    a = ap.parse_args()
    im = np.asarray(Image.open(os.path.join(ROOT, 'scales.png')).convert('RGB')).astype(np.float32)
    S = round(a.period * a.n); o = (im.shape[0] - S) // 2
    t = im[o:o + S, o:o + S]
    r = np.roll(t, (S // 2, S // 2), axis=(0, 1))
    d = np.minimum(np.arange(S), S - 1 - np.arange(S)).astype(np.float32)   # distance to the nearest edge
    w = np.clip(d / a.seam, 0, 1); w = np.minimum(w[:, None], w[None, :])[..., None]   # 1: the crop, 0: the shifted copy
    out = t * w + r * (1 - w)
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(os.path.join(ROOT, 'scales.tile.png'))
    print('wrote scales.tile.png', S, 'px')


if __name__ == '__main__':
    main()
