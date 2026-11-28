"""Near / far leg check for a painting over the shaded stick guide (stick_guide.py, the far leg drawn dark).

  python leg_check.py <DIR> <painting.png> [--guide-dir guides/stick-shaded/12f]

In a side or diagonal view the model tends to paint the NEAR leg trailing in every frame, so one foot seems to
drag behind (learnings.md, "Near leg always trailing"). Per frame it finds the two feet (the lowest 16 % of the
figure, split at the widest gap) and reports which one is the light (near) foot in the guide and which boot is the
brighter in the painting (the near one, the far one painted a little in shadow): 'L' / 'R' (image left / right),
'.' when the feet overlap. A good painting agrees in most frames; one that always has the same side brighter has
the near leg in the same place all along. Rough (lighting on a planted boot can flip it): look at the frames it
disagrees on. Measured on hero-6: the dragging E 5/9 (always 'R'), repainted 9/9.
"""
import sys, numpy as np
from PIL import Image
import pathlib
SK=str(pathlib.Path(__file__).resolve().parent.parent / 'guides' / 'stick-shaded' / '12f') + '/'
if '--guide-dir' in sys.argv: SK = sys.argv[sys.argv.index('--guide-dir') + 1].rstrip('/') + '/'
def feet(cell, m):
    ys, xs = np.nonzero(m); top, bot = ys.min(), ys.max(); y0 = int(bot - 0.16*(bot-top))
    sub = m[y0:bot+1]; L = cell[y0:bot+1,:,:3].mean(-1)
    cols = np.nonzero(sub.any(0))[0]
    # split at the widest gap between the columns, else at the median
    gaps = np.diff(cols); cut = cols[np.argmax(gaps)] + gaps.max()/2 if gaps.max() > 3 else np.median(cols)
    X = np.arange(cell.shape[1])[None, :]
    l = L[sub & (X < cut)]; r = L[sub & (X >= cut)]
    return (l.mean() if len(l) else np.nan), (r.mean() if len(r) else np.nan), gaps.max()
d = sys.argv[1]; paint = sys.argv[2]
g = np.asarray(Image.open(SK+d+'.png').convert('RGB')).astype(float)
p = np.asarray(Image.open(paint).convert('RGBA')).astype(float)
res = []
for i in range(12):
    r, c = divmod(i, 6); sl = (slice(r*512, (r+1)*512), slice(c*384, (c+1)*384))
    gc = g[sl]; gm = ~((gc[...,0] > 190) & (gc[...,1] < 90) & (gc[...,2] > 190))
    pc = p[sl]; pm = pc[...,3] > 200
    gl, gr, gg = feet(gc, gm); pl, pr, pg = feet(pc, pm)
    gs = '.' if gg <= 3 else ('L' if gl > gr else 'R'); ps = '.' if pg <= 3 else ('L' if pl > pr else 'R')
    res.append((gs, ps, pl - pr))
ok = sum(1 for a, b, _ in res if a != '.' and b != '.' and a == b); n = sum(1 for a, b, _ in res if a != '.' and b != '.')
print(d, 'guide light foot:', ''.join(a for a, _, _ in res), ' painted brighter boot:', ''.join(b for _, b, _ in res), f' agree {ok}/{n}', ' '.join('%+.0f' % x for _, _, x in res))
