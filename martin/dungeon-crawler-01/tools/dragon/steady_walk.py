"""Keeps the dragon's body still in a painted walk sheet: only the legs (and the body right around them) change from
frame to frame; the back, spikes and scales everywhere else come from one master frame, so they don't shimmer.

    python tools/dragon/steady_walk.py <DIR> [--master 0] [--grow 16] [--soft 6] [--line 0.55]

Reads art/characters/dragon/paint/walk/<DIR>.png (8 frames, 4 x 2 cells of 384 x 512) and the legs-only guide
guide/walk/<DIR>.legs.png (node tools/dragon/render_guides.js walk); writes paint/walk/<DIR>.steady.png.
For each frame, the moving region is the guide's legs in that frame and in the master frame, grown by --grow px (the
painting doesn't follow the guide exactly) and softened by --soft px; inside it the frame's own pixels are kept, outside
it the master frame's. Above a still line (--line: that share of the way down from the top of the body to the belly, both
from the guide's body without legs, which every frame shares) nothing moves at all, so the back, the spike row and the
upper flanks are the master's in every frame. The master frame is copied unchanged.
"""
import argparse, os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'art', 'characters', 'dragon')
CW, CH = 384, 512


def cells(im):
    return [im.crop(((f % 4) * CW, (f // 4) * CH, (f % 4) * CW + CW, (f // 4) * CH + CH)) for f in range(8)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir')
    ap.add_argument('--master', type=int, default=0)
    ap.add_argument('--grow', type=int, default=16)
    ap.add_argument('--line', type=float, default=0.55)
    ap.add_argument('--soft', type=int, default=6)
    a = ap.parse_args()
    paint = cells(Image.open(os.path.join(ROOT, 'paint', 'walk', a.dir + '.png')).convert('RGBA'))
    legs = cells(Image.open(os.path.join(ROOT, 'guide', 'walk', a.dir + '.legs.png')).convert('L'))
    k = a.grow * 2 + 1
    grown = [g.point(lambda v: 255 if v < 250 else 0).filter(ImageFilter.MaxFilter(k if k % 2 else k + 1)) for g in legs]
    guide = cells(Image.open(os.path.join(ROOT, 'guide', 'walk', a.dir + '.png')).convert('L'))
    # the body without legs: the guide's figure minus its legs, over all frames (each frame's legs hide other parts)
    body = np.zeros((CH, CW), bool)
    for g, l in zip(guide, legs): body |= (np.asarray(g) < 250) & ~(np.asarray(l) < 250)
    ys = np.nonzero(body.any(axis=1))[0]
    line = ys[0] + a.line * (ys[-1] - ys[0])
    below = np.clip((np.arange(CH)[:, None] - line) / (2 * a.soft) + 0.5, 0, 1).astype(np.float32)   # 0 above the line, 1 below
    master = np.asarray(paint[a.master], dtype=np.float32)
    out = Image.new('RGBA', (CW * 4, CH * 2))
    for f in range(8):
        m = np.maximum(np.asarray(grown[f]), np.asarray(grown[a.master]))
        m = np.asarray(Image.fromarray(m).filter(ImageFilter.GaussianBlur(a.soft)), dtype=np.float32) / 255
        m = (m * below)[..., None]
        if f == a.master: m[:] = 1
        fr = np.asarray(paint[f], dtype=np.float32)
        # blend premultiplied, so a transparent pixel's colour doesn't bleed into the edge
        pa, pm = fr[..., 3:] / 255, master[..., 3:] / 255
        alpha = pa * m + pm * (1 - m)
        rgb = (fr[..., :3] * pa * m + master[..., :3] * pm * (1 - m)) / np.maximum(alpha, 1e-6)
        cell = np.concatenate([rgb, alpha * 255], axis=2).clip(0, 255).astype(np.uint8)
        out.paste(Image.fromarray(cell, 'RGBA'), ((f % 4) * CW, (f // 4) * CH))
    dst = os.path.join(ROOT, 'paint', 'walk', a.dir + '.steady.png')
    out.save(dst)
    print('wrote', dst)


if __name__ == '__main__':
    main()
