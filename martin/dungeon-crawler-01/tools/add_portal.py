"""Build the Rift portal's art: the arch (depth-sorted), its platform (a floor decal) and the dial (a floor decal).

Usage:  python tools/add_portal.py            (run from the game folder; needs Pillow + NumPy)

Raw images (tools/raw), see README "Assets": OpenAI gpt-image-2.6-flare `edit` (medium, transparent background) with
tools/raw/crypt.png as the style reference:
  portal.png  (1024 x 1536)  a stone arch facing the viewer, its opening a violet vortex, at the back edge of a
              semicircular flagstone platform with two steps in front;
  dial.png    (1536 x 1024)  a flat round stone dial: a ring of twelve rune stones around a dark polished centre.
The other candidate of each is in assets/unused/portal/.

The portal picture is cut at one row, CUT: the bottom of the vortex, where the pillars stand on the platform. Above
it: the arch layer, drawn depth-sorted on the arch's base line; below it: the platform layer, drawn flat on the
ground first, so whoever stands on the platform is drawn over it and whoever walks behind the arch is hidden by it.
The anchor (the ground point at the middle of the arch's base line) is (AX, CUT) in the raw picture. The arch is
scaled so its outer width (ARCH_W raw px) is ARCH_TILES tiles across the screen (a tile along the line x + y = const
is TW = 96 px wide). The dial is squashed to a 2:1 ellipse (a circle on the iso ground) DIAL_R tiles in radius.
The vortex's box (where the swirl glows in the game) is found from its colour.

Writes:
  assets/portal.webp   the three layers at SHEET x the raw size, shelf-packed
and adds META.portal to assets/meta.json and the inline `const META = ...` line in index.html:
  { arch, base, dial: [x, y, w, h, ox, oy, gw, gh] (the box in portal.webp, the offset of its top-left corner from
  the anchor in game px, its size in game px), glow: [cx, cy, rx, ry] (the vortex's middle and half size, game px
  from the anchor), dialR (tiles) }.
"""
import json, pathlib, re, sys
from PIL import Image
import numpy as np

HERE = pathlib.Path(__file__).parent
GAME = HERE.parent
RAW = HERE / "raw"
TW = 96                     # the game's tile width (screen px)
SHEET = 0.6                 # raw -> sheet scale of the portal (the dial: its own)
CUT, AX = 1030, 511         # the cut row and the anchor's column in portal.png
ARCH_W, ARCH_TILES = 790, 4.2
DIAL_R = 2.0                # the dial's radius in tiles


def crop(im):
    a = np.asarray(im)[..., 3]; ys, xs = np.where(a > 8)
    return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)


def main():
    P = Image.open(RAW / "portal.png").convert("RGBA")
    D = Image.open(RAW / "dial.png").convert("RGBA")
    g = ARCH_TILES * TW / ARCH_W                     # raw -> game
    # the vortex: saturated blue-violet pixels
    a = np.asarray(P).astype(int); r, gg, b = a[..., 0], a[..., 1], a[..., 2]
    v = (a[..., 3] > 40) & (b > 140) & (b > gg + 50) & ((r > gg + 20) | (b > 200))
    ys, xs = np.where(v)
    glow = [((xs.min() + xs.max()) / 2 - AX) * g, ((ys.min() + ys.max()) / 2 - CUT) * g, (xs.max() - xs.min()) / 2 * g, (ys.max() - ys.min()) / 2 * g]
    parts = {}
    for name, box in (("arch", (0, 0, P.width, CUT)), ("base", (0, CUT, P.width, P.height))):
        im = P.crop(box); x0, y0, x1, y1 = crop(im); im = im.crop((x0, y0, x1, y1))
        ox, oy = (box[0] + x0 - AX) * g, (box[1] + y0 - CUT) * g
        parts[name] = (im.resize((round(im.width * SHEET), round(im.height * SHEET)), Image.LANCZOS), [ox, oy, im.width * g, im.height * g])
    x0, y0, x1, y1 = crop(D); dim = D.crop((x0, y0, x1, y1))
    gw = 2 * DIAL_R * (TW / 2) * 2 ** 0.5   # a radius of r tiles spans r · √2 · HW px to each side
    gh = gw / 2 / 0.96                      # its top a 2:1 ellipse, plus the rim's thickness below (about 4 %)
    sw = round(gw / 0.75); sh = round(sw * gh / gw)   # sheet px: game px / 0.75
    parts["dial"] = (dim.resize((sw, sh), Image.LANCZOS), [-gw / 2, -gw / 4, gw, gh])
    # shelf-pack
    W = max(p[0].width for p in parts.values()); H = sum(p[0].height + 2 for p in parts.values())
    sheet = Image.new("RGBA", (W, H)); y = 0; meta = {}
    for k, (im, geo) in parts.items():
        sheet.paste(im, (0, y)); meta[k] = [0, y, im.width, im.height] + [round(v, 1) for v in geo]; y += im.height + 2
    meta["glow"] = [round(v, 1) for v in glow]; meta["dialR"] = DIAL_R
    out = GAME / "assets" / "portal.webp"; sheet.save(out, quality=88, method=6)
    mj = json.loads((GAME / "assets" / "meta.json").read_text()); mj["portal"] = meta
    (GAME / "assets" / "meta.json").write_text(json.dumps(mj, indent=1))
    html = (GAME / "index.html").read_text()
    html, n = re.subn(r"^const META = .*;$", lambda _: "const META = " + json.dumps(mj, separators=(",", ":")) + ";", html, count=1, flags=re.M)
    if not n: sys.exit("const META line not found in index.html")
    (GAME / "index.html").write_text(html)
    print(f"portal.webp: {W} x {H}, {out.stat().st_size // 1024} KB; META.portal:", json.dumps(meta))


if __name__ == "__main__":
    main()
