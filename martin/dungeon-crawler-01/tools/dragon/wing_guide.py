"""Draws the guide for painting the dragon's wing flat: the prototype's spread wing (WING_SPREAD in
dragon-prototype.html: root, elbow, wrist, 3 finger tips, trailing root; [forward, outward] in tiles) seen from directly
above, the right wing, outward to the right and forward up, grey membrane and dark bones on white, 1536 x 1024.
Writes art/characters/dragon/guide/wing.png and wing.json (each bone point's pixel position, for mapping the painting
onto the wing panels).    python tools/dragon/wing_guide.py
"""
import json, os
from PIL import Image, ImageDraw
SPREAD = [[0, 0], [0.25, 1.05], [0.45, 2.05], [-0.25, 3.4], [-1.05, 2.9], [-1.75, 2.0], [-2.0, 0.45]]
PANELS = [[0, 1, 2, 3], [2, 3, 4], [2, 4, 5], [2, 5, 6, 0]]
S, X0, Y0 = 380, 90, 250
pts = [(X0 + b * S, Y0 - u * S) for u, b in SPREAD]
im = Image.new('RGB', (1536, 1024), 'white'); d = ImageDraw.Draw(im)
for p in PANELS: d.polygon([pts[i] for i in p], fill=(150, 150, 150))
for a, b in [(0, 1), (1, 2), (2, 3), (2, 4), (2, 5)]: d.line([pts[a], pts[b]], fill=(60, 60, 60), width=14)
for p in pts[:6]: d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=(60, 60, 60))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'art', 'characters', 'dragon', 'guide')
im.save(os.path.join(out, 'wing.png'))
json.dump({'size': [1536, 1024], 'points': [[round(x, 1), round(y, 1)] for x, y in pts], 'panels': PANELS,
           'note': 'right wing from above: root, elbow, wrist, finger tips 1-3, trailing root; x outward, y backward'},
          open(os.path.join(out, 'wing.json'), 'w'), indent=1)
print('wrote wing guide')
