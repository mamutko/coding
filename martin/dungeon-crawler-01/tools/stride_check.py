"""Stride check for an AI walk-cycle image (see the sprite-animation skill, "Verifying").

  python stride_check.py <CHAR> <DIR> <raw.png> [--guide guide.png]

--guide compares against a given guide image (e.g. ranger_test/guide-mocap-NW.png) instead of the stick figure.
A painted image with real transparency (OpenAI --background transparent) is measured on its alpha channel.

Compares the painted 4 x 2 image with the pose guide walk_cycle.py makes for that character and direction, per
frame, on two numbers measured from the silhouette (flat magenta background):
  spread  the width of the bottom 12 % of the figure (the feet) / its height. In the three-quarter views (SW, NW)
          it tells the two halves of the stride apart: the feet are in line when the near leg leads and wide
          apart when the far leg does (or the other way round). A held item reaching the feet (a bow tip) adds to it.
  low     (lowest pixel left of the hips - lowest pixel right of them) / height: which foot is lower in the image.
          In the front and back views (S, N) its sign must flip between frames 0-3 and 4-7, as in the guide.
Each view is judged on the number that tells its two half-strides apart: spread in SW, W and NW (a frame is marked
"!" when it is off the guide's by more than 0.2: a copy of the other half of the stride is off by 0.3 or more,
while painted legs are often a little closer or wider than the mannequin's), low in S and N (marked when its sign
differs from the guide's where the guide's is beyond +-0.08; painted feet differ less in height than the guide's).
"""
import sys, pathlib, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import walk_cycle as wc

def measure(path):
    src = Image.open(path)
    im = np.asarray(src.convert('RGBA')).astype(int); H, W, _ = im.shape
    if (im[:, :, 3] < 128).mean() > 0.2:                  # real transparency: the alpha channel is the silhouette
        fg = im[:, :, 3] > 128
    else:
        fg = ~((im[:, :, 0] > 190) & (im[:, :, 1] < 90) & (im[:, :, 2] > 190))
    out = []
    for f in range(8):
        c = fg[(f // 4) * H // 2:(f // 4 + 1) * H // 2, (f % 4) * W // 4:(f % 4 + 1) * W // 4]
        ys, xs = np.nonzero(c); top, bot = ys.min(), ys.max(); h = bot - top
        band = c[bot - int(h * 0.12):bot + 1]; bx = np.nonzero(band.any(0))[0]
        mid = int(np.nonzero(c[top + int(h * 0.45):top + int(h * 0.55)].any(0))[0].mean())
        lb = np.nonzero(c[:, :mid].any(1))[0].max(); rb = np.nonzero(c[:, mid:].any(1))[0].max()
        out.append(((bx.max() - bx.min()) / h, (lb - rb) / h))
    return out

if __name__ == '__main__':
    char, d, raw = sys.argv[1], sys.argv[2], sys.argv[3]
    if '--guide' in sys.argv:
        g = sys.argv[sys.argv.index('--guide') + 1]
    else:
        wc.use(char); g = pathlib.Path(tempfile.mkdtemp()) / 'guide.png'
        wc.STYLE.update(thick=1.9, left=(55, 55, 60), right=(175, 175, 180), mid=(115, 115, 120))
        wc.guide(d, str(g), (255, 0, 255), False)
    G, P = measure(g), measure(raw)
    print('frame   guide spread/low   painted spread/low')
    for f in range(8):
        bad = (abs(G[f][0] - P[f][0]) > 0.2) if d in ('SW', 'W', 'NW') else (abs(G[f][1]) > 0.08 and np.sign(G[f][1]) != np.sign(P[f][1]))
        print(f'  {f}       {G[f][0]:5.2f} {G[f][1]:+5.2f}        {P[f][0]:5.2f} {P[f][1]:+5.2f}  {"!" if bad else ""}')
