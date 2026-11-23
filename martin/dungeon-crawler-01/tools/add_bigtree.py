"""Build a big surface tree in three layers: roots (a floor decal), trunk (depth-sorted) and crown (always on top).

Usage:  python tools/add_bigtree.py            (run from the game folder; needs Pillow + NumPy)

Raw images (tools/raw), see README "Assets": OpenAI gpt-image-2.6-flare (medium, 1024 x 1536, transparent
background), each a big tree with a wide, sparse crown and a partly exposed root system:
  bigtree_oak.png, bigtree_pine.png (Scots pine), bigtree_birch.png (silver birch), bigtree_maple.png (autumn
  maple), bigtree_dead.png (a dead tree). bigtree_*_alt.png: the other candidate of each, not used.

The picture is cut at hand-picked lines (TREES below, in the raw image's pixels):
  - the ground point (gx, gy): where the trunk meets the ground; the tree stands on its tile with it;
  - the trunk band: a polygon around the trunk, from row `cut` (above where the hero's head reaches when standing
    right in front of the trunk) down to the ground point. Inside it: the trunk layer;
  - above row `cut`, and beside the trunk above row `low` (low branches): the crown layer;
  - the rest (below `low`, outside the band, and everything below the ground point): the roots layer. The painted
    roots sink into the ground toward their tips: over an ellipse around the ground point, their colour fades out
    (from f0 to f1 of the ellipse) while the same root shapes, blurred and embossed (light from the upper left), come
    in as transparent shadow and highlight only: strongest across the transition (where the roots are half
    transparent), lighter where the colour is gone, so farther out they show as soft bumps on whatever grass they
    lie on; the bumps fade out at the tips (t0 to t1). Nothing is added beyond the painted roots. A soft dark contact
    shadow sits under the trunk, and the tree's cast shadow lies on the ground toward the lower right (light from
    the upper left, the art's light, taken as the moon's): the trunk's and crown's silhouette sheared onto the
    ground (kx, ky) and blurred, a soft dappled shade that fades toward its far end. Big trees are never mirrored,
    so the shadow and the bump shading keep the scene's light.

Writes:
  assets/bigtrees.webp     the three layers of each tree, each cropped to its pixels, at SCALE of the raw picture
and adds META.bigtrees (key -> { s, roots, trunk, crown }, each layer [x, y, w, h, ox, oy]: its box in bigtrees.webp
and the offset of its top-left corner from the ground point, in sheet pixels; s: sheet pixels to game pixels) to
assets/meta.json and the inline `const META = ...` line in index.html.
"""
import json, pathlib, re, sys
from PIL import Image, ImageFilter
import numpy as np

HERE = pathlib.Path(__file__).parent
GAME = HERE.parent
RAW = HERE / "raw"

# raw image -> sheet scale, and sheet -> game scale: the crown (970 raw px) comes out about 4.5 tiles (430 px) wide
SCALE = 0.667          # the sheet keeps 1.5 x the game's size, so it stays sharp when zoomed in or on a 2x screen
GAME_S = 0.445 / SCALE

# Each tree: its raw file; the ground point (gx, gy); `cut` (about 300 raw px above the ground point: over the
# hero's head) and `low` (the top of the root spread); the trunk band: (row, left x, right x), linearly interpolated
# between rows; the roots' ellipse around (gx, gy + fy), radii rx, ry (the painted roots end at about 0.9 of it).
TREES = {
    "oak": dict(file="bigtree_oak.png", gx=528, gy=1095, cut=800, low=1035,
                band=[(800, 440, 615), (900, 452, 610), (1000, 445, 615), (1060, 400, 650), (1095, 380, 680)],
                rx=420, ry=150, fy=20),
    "pine": dict(file="bigtree_pine.png", gx=540, gy=1330, cut=1030, low=1240,
                 band=[(1030, 495, 590), (1240, 490, 600), (1300, 440, 650), (1330, 420, 670)],
                 rx=420, ry=135, fy=40),
    "birch": dict(file="bigtree_birch.png", gx=520, gy=1280, cut=980, low=1235,
                  band=[(980, 488, 562), (1150, 483, 557), (1230, 440, 600), (1280, 400, 650)],
                  rx=400, ry=130, fy=70),
    "maple": dict(file="bigtree_maple.png", gx=520, gy=1170, cut=870, low=1120,
                  band=[(870, 470, 575), (1000, 470, 570), (1100, 450, 590), (1170, 380, 660)],
                  rx=430, ry=135, fy=50),
    "dead": dict(file="bigtree_dead.png", gx=540, gy=1260, cut=960, low=1170,
                 band=[(960, 440, 615), (1100, 445, 625), (1200, 380, 690), (1260, 340, 740)],
                 rx=500, ry=165, fy=60),
}
# The same for every tree: the roots' colour fades from f0 to f1 of the ellipse (then bumps only), the bumps fade
# out from t0 to t1; the cast shadow (light from the upper left, the art's light, taken as the moon's): a point h px
# above the ground point falls h * kx to the right and h * ky down; its opacity and blur (raw px)
COMMON = dict(f0=0.22, f1=0.6, t0=0.7, t1=1.0, kx=0.55, ky=0.26, shadow=0.6, sblur=26)


def band_lr(band, y):
    for (y0, l0, r0), (y1, l1, r1) in zip(band, band[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return l0 + (l1 - l0) * t, r0 + (r1 - r0) * t
    return None


def blur(a, r):
    """Gaussian blur of a float array 0-1."""
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(float) / 255


def shift(a, dx, dy):
    out = np.zeros_like(a)
    h, w = a.shape
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = a[max(0, -dy):h + min(0, -dy), max(0, -dx):w + min(0, -dx)]
    return out


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def layers(spec):
    im = np.asarray(Image.open(RAW / spec["file"]).convert("RGBA")).astype(float)
    im = np.pad(im, ((0, 420), (0, 820), (0, 0)))                         # room for the cast shadow (right, below)
    h, w = im.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    inband = np.zeros((h, w), bool)
    for y in range(spec["cut"], spec["gy"] + 1):
        l, r = band_lr(spec["band"], y)
        inband[y, int(l):int(r) + 1] = True
    crown = (yy < spec["cut"]) | ((yy < spec["low"]) & ~inband)
    trunk = inband & ~crown
    roots = ~crown   # the trunk's base too: under the trunk layer, it hides the seam where the two layers meet
    out = {}
    for name, m in (("crown", crown), ("trunk", trunk)):
        L = im.copy(); L[..., 3] *= m; out[name] = L
    # roots: the painted colour fades out over the ellipse, and the same shapes fade in as bumps (emboss only)
    gx, gy = spec["gx"], spec["gy"] + spec["fy"]
    d = np.hypot((xx - gx) / spec["rx"], (yy - gy) / spec["ry"])
    sink = smooth((d - spec["f0"]) / (spec["f1"] - spec["f0"]))          # 0: on the ground, 1: sunk into it
    tips = 1 - smooth((d - spec["t0"]) / (spec["t1"] - spec["t0"]))
    ra0 = roots * im[..., 3] / 255                                        # the painted roots, unfaded
    R = im.copy(); R[..., 3] *= roots * (1 - sink)
    ra = R[..., 3] / 255
    bump = blur(ra0, 3)
    emb = shift(bump, -2, -3) - shift(bump, 2, 3)          # > 0: lit (faces the upper left), < 0: in shade
    # the shading comes in early, where the colour is only starting to fade (full by a third of the way), and
    # eases off where the colour is gone (to 45 %), so the sunk roots stay light
    keep = smooth(sink / 0.35) * (1 - 0.55 * smooth((sink - 0.5) / 0.5)) * tips
    hi = np.clip(emb * 3, 0, 1) * keep * 0.13
    sh = np.clip(-emb * 3.5, 0, 1) * keep * 0.4
    # a soft contact shadow under the trunk
    dc = np.hypot((xx - spec["gx"]) / 190, (yy - spec["gy"] - 10) / 75)
    contact = (1 - smooth(dc)) * 0.45
    # the tree's cast shadow on the ground: the trunk's and crown's silhouette sheared onto the ground plane (a point
    # h px above the ground point lands h * kx to the right and h * ky below it), blurred, so the sparse crown casts
    # a soft, dappled shade; it fades toward its far end
    sil = Image.fromarray(np.clip(im[..., 3] * (crown | trunk), 0, 255).astype(np.uint8))
    kx, ky, g0x, g0y = spec["kx"], spec["ky"], spec["gx"], spec["gy"]
    # output (X, Y) -> source: h = (Y - gy) / ky, x = X - h * kx, y = gy - h
    cast = sil.transform((w, h), Image.AFFINE, (1, -kx / ky, kx / ky * g0y, 0, -1 / ky, g0y + g0y / ky), Image.BILINEAR)
    cast = np.asarray(cast.filter(ImageFilter.GaussianBlur(spec["sblur"]))).astype(float) / 255
    far = np.clip((yy - g0y) / (ky * (g0y - 150)), 0, 1)                 # 0 at the ground point, 1 under the crown's top
    cast = np.clip(cast * 1.6, 0, 1) * (1 - 0.45 * far) * (yy >= g0y - 60) * spec["shadow"]
    contact = np.maximum(contact, cast)
    # bumps and contact shadow under the roots (premultiplied "over")
    def over(top_rgb, top_a, base_rgb, base_a):
        a = top_a + base_a * (1 - top_a)
        rgb = (top_rgb * top_a[..., None] + base_rgb * (base_a * (1 - top_a))[..., None]) / np.maximum(a, 1e-6)[..., None]
        return rgb, a
    dark = np.array([12.0, 14, 6]); light = np.array([205.0, 215, 150])   # shade; sunlit grass
    rgb, a = over(np.broadcast_to(dark, (h, w, 3)), contact, np.zeros((h, w, 3)), np.zeros((h, w)))
    rgb, a = over(np.broadcast_to(dark, (h, w, 3)), sh, rgb, a)
    rgb, a = over(np.broadcast_to(light, (h, w, 3)), hi, rgb, a)
    rgb, a = over(R[..., :3], ra, rgb, a)
    out["roots"] = np.dstack([rgb, a * 255])
    return out


def to_img(L):
    return Image.fromarray(np.clip(L, 0, 255).astype(np.uint8), "RGBA")


def main():
    parts, meta = [], {}
    for key, spec in TREES.items():
        spec = dict(COMMON, **spec)
        ls = layers(spec)
        m = {"s": round(GAME_S, 4)}
        for name in ("roots", "trunk", "crown"):
            img = to_img(ls[name])
            img = img.resize((round(img.width * SCALE), round(img.height * SCALE)), Image.LANCZOS)
            a = np.asarray(img)[..., 3]
            ys, xs = np.nonzero(a > 2)
            x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
            parts.append((key, name, img.crop((x0, y0, x1, y1))))
            m[name] = [0, 0, int(x1 - x0), int(y1 - y0), int(x0 - round(spec["gx"] * SCALE)), int(y0 - round(spec["gy"] * SCALE))]
        meta[key] = m
    # pack: one row per tree, its three layers side by side
    rows = [[p for p in parts if p[0] == k] for k in TREES]
    W = max(sum(p[2].width + 2 for p in r) for r in rows)
    H = sum(max(p[2].height for p in r) + 2 for r in rows)
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = 0
    for r in rows:
        x = 0
        for key, name, img in r:
            sheet.paste(img, (x, y)); meta[key][name][0] = x; meta[key][name][1] = y; x += img.width + 2
        y += max(p[2].height for p in r) + 2
    sheet.save(GAME / "assets" / "bigtrees.webp", "WEBP", quality=80, method=6)
    mj = json.loads((GAME / "assets" / "meta.json").read_text()); mj["bigtrees"] = meta
    (GAME / "assets" / "meta.json").write_text(json.dumps(mj, indent=1))
    html = (GAME / "index.html").read_text()
    html, n = re.subn(r"^const META = .*;$", "const META = " + json.dumps(mj, separators=(",", ":")) + ";", html, count=1, flags=re.M)
    if not n:
        sys.exit("const META line not found in index.html")
    (GAME / "index.html").write_text(html)
    size = (GAME / "assets" / "bigtrees.webp").stat().st_size
    print(f"bigtrees.webp: {W} x {H}, {size // 1024} KB; META.bigtrees:", json.dumps(meta))


if __name__ == "__main__":
    main()
