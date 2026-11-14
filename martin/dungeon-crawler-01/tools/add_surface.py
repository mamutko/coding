"""Build the art of the surface (depth 0): grass textures and the surface atlas (assets/surface.webp).

Usage:  python tools/add_surface.py            (run from the game folder; needs Pillow + NumPy)

Raw images (tools/raw), see README "The surface":
  grass_a.png   Google gemini-3.1-flash-image edit (floor.jpg as a style reference): lush dark green grass.
  grass_b.png   OpenAI gpt-image-2 (medium): patchy olive meadow grass with bare spots.
  trees.png     OpenAI gpt-image-2 (medium), 4 x 1 cells on magenta: oak, fir, dead tree, birch.
  bushes.png    OpenAI gpt-image-2 (medium), 4 x 2 cells on magenta: four bushes; flowers, rocks, mushrooms, a grass tuft.
  crypt.png     OpenAI gpt-image-2 (medium), one isometric stone crypt on magenta, its entrance on the down-left wall.

Writes:
  assets/grass_a.jpg, assets/grass_b.jpg   512 x 512, made seamless (blended with a half-offset copy of themselves)
  assets/surface.webp                       the sprites, shelf-packed
and adds META.surface (key -> [x, y, w, h] in surface.webp, plus a tree's crown cut: the row where its trunk
begins) to assets/meta.json and the inline `const META = ...` line in index.html.
"""
import importlib.util, json, pathlib, re, sys
from PIL import Image, ImageFilter
import numpy as np

HERE = pathlib.Path(__file__).parent
GAME = HERE.parent
RAW = HERE / "raw"
WIDTH = 2048

spec = importlib.util.spec_from_file_location("add_items", HERE / "add_items.py")
ai = importlib.util.module_from_spec(spec); spec.loader.exec_module(ai)
key_cell, keep_main, bbox = ai.key_cell, ai.keep_main, ai.bbox

# (sheet, cols, rows, [(cell, key, height in px[, (x0, x1)[, crown cut as a share of the height]]), ...]): the optional
# (x0, x1) replaces the cell's columns (a tree's crown reaches past its cell), the optional cut replaces crown_cut's
# guess (the oak's wide roots fool it)
SHEETS = [
    ("trees.png", 4, 1, [(0, "tree1", 400, (0, 506), 0.56), (1, "tree2", 420, (506, 812)), (2, "tree3", 340, (812, 1185)),
                         (3, "tree4", 360, (1185, 1536))]),
    ("bushes.png", 4, 2, [(0, "bush1", 96), (1, "bush2", 92), (2, "bush3", 70), (3, "bush4", 100),
                          (4, "flowers", 56), (5, "rocks", 50), (6, "mushrooms", 54), (7, "tuft", 70)]),
    ("crypt.png", 1, 1, [(0, "crypt", 600)]),
]


def seamless(src, out, size=512):
    """Blend a texture with a half-offset copy of itself across a soft cross, so its edges wrap."""
    im = Image.open(RAW / src).convert("RGB").resize((size, size), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    b = np.roll(np.roll(a, size // 2, 0), size // 2, 1)
    t = np.abs(np.linspace(-1, 1, size))
    w = np.clip((np.maximum(t[None, :], t[:, None]) - 0.55) / 0.35, 0, 1)[..., None]   # 1 near the edges
    Image.fromarray((a * (1 - w) + b * w).astype(np.uint8)).save(GAME / "assets" / out, quality=88)


def crown_cut(cell):
    """The row where a tree's crown ends and its bare trunk begins (crown above, trunk below)."""
    m = cell[..., 3] > 40
    widths = np.array([np.ptp(np.nonzero(r)[0]) if r.any() else 0 for r in m])
    h = len(widths); top = widths[: int(h * 0.75)].max()
    for y in range(int(h * 0.8), 0, -1):        # up from above the roots: the first row as wide as half the crown
        if widths[y] > 0.45 * top:
            return y + 1
    return h // 2


def main():
    seamless("grass_a.png", "grass_a.jpg"); seamless("grass_b.png", "grass_b.jpg")
    figs = []
    for name, cols, rows, cells in SHEETS:
        rgb = np.asarray(Image.open(RAW / name).convert("RGB"))
        H, W = rgb.shape[:2]
        for idx, key, px, *opt in cells:
            r, c = divmod(idx, cols)
            y0, y1, x0, x1 = round(r * H / rows), round((r + 1) * H / rows), round(c * W / cols), round((c + 1) * W / cols)
            if opt: x0, x1 = opt[0]
            cell = keep_main(key_cell(rgb[y0:y1, x0:x1], 6), 0.05 if key == "rocks" else 0.3, key != "crypt")
            b = bbox(cell); cell = cell[b[1]:b[3], b[0]:b[2]]
            im = Image.fromarray(cell, "RGBA"); k = px / im.height
            im = im.resize((max(1, round(im.width * k)), px), Image.LANCZOS)
            extra = [round(px * opt[1]) if len(opt) > 1 else crown_cut(np.asarray(im))] if key.startswith("tree") else []
            figs.append((key, im, extra))
    placed, x, y, row_h = [], 0, 0, 0
    for key, im, extra in figs:
        if x + im.width > WIDTH: x, y, row_h = 0, y + row_h + 2, 0
        placed.append((key, im, x, y, extra)); x += im.width + 2; row_h = max(row_h, im.height)
    atlas = Image.new("RGBA", (WIDTH, y + row_h))
    meta = json.loads((GAME / "assets" / "meta.json").read_text()); meta["surface"] = {}
    for key, im, px, py, extra in placed:
        atlas.paste(im, (px, py)); meta["surface"][key] = [px, py, im.width, im.height] + extra
    atlas.save(GAME / "assets" / "surface.webp", quality=88, method=6)
    (GAME / "assets" / "meta.json").write_text(json.dumps(meta, indent=1))
    html = (GAME / "index.html").read_text()
    html, n = re.subn(r"^const META = .*;$", "const META = " + json.dumps(meta, separators=(",", ":")) + ";", html, count=1, flags=re.M)
    if n != 1:
        sys.exit("const META line not found in index.html")
    (GAME / "index.html").write_text(html)
    print(f"surface.webp: {WIDTH} x {atlas.height}, {len(placed)} sprites; grass_a.jpg, grass_b.jpg; META.surface:",
          {k: v for k, v in meta["surface"].items()})


if __name__ == "__main__":
    main()
