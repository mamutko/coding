"""Add the Keepers of the Crypt and their stall's furnishings to the props atlas (assets/props.webp).

Usage:  python tools/add_market.py            (run from the game folder, after add_props.py; needs Pillow + NumPy)

Rows 1-2 of the atlas (process_art.py, add_props.py) are kept as they are; this script rebuilds the rows after them
from the raw sheets below, so running it again gives the same atlas:

  keepers.png      OpenAI gpt-image-2 (medium, 1536 x 1024), 4 x 1 cells on magenta: four human merchants
                   (keeper1 a travelling merchant in a green fur-trimmed cloak, keeper2 a stout smith in a leather
                   apron, keeper3 a peddler woman in a blue hooded cloak, keeper4 an old scholar with spectacles).
  keeper_decor.png Google gemini-3.1-flash-image edit (1K, 3:2) with the props as a style reference, 4 x 2 cells:
                   mtable (trestle table with wares), mrack (weapon rack), mchest (open chest of trinkets), mshelf
                   (shelf of potions), mcrates (crates and sacks), mbarrel (barrel of swords), mlantern (lantern on a
                   post), mrug (round red rug, drawn flat on the floor).
Each figure is keyed out, cropped and scaled so its longest side (or its height, for the upright ones) is the size
below; the game scales them again when drawing (PROP_STYLE). Then it rewrites assets/meta.json and the inline
`const META = ...` line in index.html.
"""
import importlib.util, json, pathlib, re, sys
from PIL import Image
import numpy as np

HERE = pathlib.Path(__file__).parent
GAME = HERE.parent
RAW = HERE / "raw"
WIDTH = 1935                      # the atlas width (unchanged)

spec = importlib.util.spec_from_file_location("add_items", HERE / "add_items.py")
ai = importlib.util.module_from_spec(spec); spec.loader.exec_module(ai)
key_cell, keep_main, bbox = ai.key_cell, ai.keep_main, ai.bbox

# (sheet, cols, rows, [(cell, key, ('h' | 'w', px)), ...]): scale to that height or width
SHEETS = [
    ("keepers.png", 4, 1, [(0, "keeper1", ("h", 230)), (1, "keeper2", ("h", 220)), (2, "keeper3", ("h", 225)), (3, "keeper4", ("h", 228))]),
    ("keeper_decor.png", 4, 2, [(0, "mtable", ("w", 230)), (1, "mrack", ("h", 230)), (2, "mchest", ("w", 170)), (3, "mshelf", ("w", 190)),
                                (4, "mcrates", ("w", 190)), (5, "mbarrel", ("h", 190)), (6, "mlantern", ("h", 230)), (7, "mrug", ("w", 260))]),
]


def main():
    meta = json.loads((GAME / "assets" / "meta.json").read_text())
    ours = {k for _, _, _, cells in SHEETS for _, k, _ in cells}
    keep = {k: v for k, v in meta["props"].items() if k not in ours}
    base_h = max(v[1] + v[3] for v in keep.values()) + 2
    base = Image.open(GAME / "assets" / "props.webp").convert("RGBA").crop((0, 0, WIDTH, base_h))
    figs = []
    for name, cols, rows, cells in SHEETS:
        rgb = np.asarray(Image.open(RAW / name).convert("RGB"))
        H, W = rgb.shape[:2]
        for idx, key, (dim, px) in cells:
            r, c = divmod(idx, cols)
            y0, y1, x0, x1 = round(r * H / rows), round((r + 1) * H / rows), round(c * W / cols), round((c + 1) * W / cols)
            cell = keep_main(key_cell(rgb[y0:y1, x0:x1], 6), 0.3, True)
            b = bbox(cell)
            im = Image.fromarray(cell[b[1]:b[3], b[0]:b[2]], "RGBA")
            k = px / (im.height if dim == "h" else im.width)
            figs.append((key, im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)))
    # shelf packing into rows below the existing ones
    placed, x, y, row_h = [], 0, base_h, 0
    for key, im in figs:
        if x + im.width > WIDTH: x, y, row_h = 0, y + row_h + 2, 0
        placed.append((key, im, x, y)); x += im.width + 2; row_h = max(row_h, im.height)
    atlas = Image.new("RGBA", (WIDTH, y + row_h)); atlas.paste(base, (0, 0))
    for key, im, px, py in placed:
        atlas.paste(im, (px, py)); keep[key] = [px, py, im.width, im.height]
    atlas.save(GAME / "assets" / "props.webp", quality=90, method=6)
    meta["props"] = keep
    (GAME / "assets" / "meta.json").write_text(json.dumps(meta, indent=1))
    html = (GAME / "index.html").read_text()
    html, n = re.subn(r"^const META = .*;$", "const META = " + json.dumps(meta, separators=(",", ":")) + ";", html, count=1, flags=re.M)
    if n != 1:
        sys.exit("const META line not found in index.html")
    (GAME / "index.html").write_text(html)
    print(f"props.webp: {WIDTH} x {atlas.height}, {len(placed)} market props added; META updated")


if __name__ == "__main__":
    main()
