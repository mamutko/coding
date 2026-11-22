"""Cuts the painted legs off the dragon's 16-direction body: the game draws its own legs (painted bones and feet,
placed by IK), so the body sprite keeps only the torso, the short neck and tail ends, and the tops of the legs.

    python tools/dragon/cut_body.py [body16|body32] [--grow 5] [--soft 2]

Reads art/characters/dragon/paint/<name>.png (painted over guide/<name>.full.png: the body with whole legs, 3 x 3
cells, so the image model paints a real dragon rather than a grub) and guide/<name>.png (the same body with only
shoulder and haunch knobs where the legs join). Keeps the painting inside the knobbed body's outline grown by --grow px
(the painting doesn't follow the guide exactly) and softened by --soft px, and everything above that outline's lower
edge (the painted back and spikes stand higher than the guide's), and the upper half of the cell down to the middle of
that outline (the painting is a little wider than the guide); writes paint/<name>.cut.png. body16: the 9
views S ... N of 32 directions 0, 2 ... 16; body32: the 8 between them, 1, 3 ... 15 (its 9th cell is empty).
"""
import argparse, os
import numpy as np
from PIL import Image, ImageFilter

CW, CH = 512, 341
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'art', 'characters', 'dragon')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name', nargs='?', default='body16')
    ap.add_argument('--grow', type=int, default=5)
    ap.add_argument('--soft', type=int, default=2)
    a = ap.parse_args()
    paint = Image.open(os.path.join(ROOT, 'paint', a.name + '.png')).convert('RGBA')
    guide = Image.open(os.path.join(ROOT, 'guide', a.name + '.png')).convert('L')
    body = np.asarray(guide) < 250
    # everything above the body's lower edge counts (the painted back and spikes reach higher than the guide's)
    for r in range(3):
        for c in range(3):
            cell = body[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW]
            low = np.where(cell.any(axis=0), CH - 1 - np.argmax(cell[::-1], axis=0), -1)
            ys = np.nonzero(cell.any(axis=1))[0]
            if not len(ys): continue   # an empty cell
            cell |= np.arange(CH)[:, None] <= low[None, :]
            cell[:int(ys[0] + 0.5 * (ys[-1] - ys[0]))] = True   # and the upper half whole (the painting is a little wider)
    m = Image.fromarray((body * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(a.grow * 2 + 1)).filter(ImageFilter.GaussianBlur(a.soft))
    px = np.asarray(paint).astype(np.float32)
    px[..., 3] *= np.asarray(m, dtype=np.float32) / 255
    dst = os.path.join(ROOT, 'paint', a.name + '.cut.png')
    Image.fromarray(px.clip(0, 255).astype(np.uint8), 'RGBA').save(dst)
    print('wrote', dst)


if __name__ == '__main__':
    main()
