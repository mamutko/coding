"""Add the newer props (searched bones, door leaves) and the dirt texture to the game's assets.

Usage:  python tools/add_props.py            (run from the game folder; needs Pillow + NumPy)

The original props (row 0 of assets/props.webp, from process_art.py) are kept as they are; this script
rebuilds row 1 from the raw sheets below, so running it again gives the same atlas:

  bones_searched.png  Google gemini-3.1-flash-image edit of the original bone pile: the same bones searched
                      through, flatter and spread out. Saved as the prop "bonesused".
  doors.png           Google gemini-3.1-flash-image edit of the original door's leaf: two flat-topped plank doors
                      (A: strap hinges and a ring; B: a cross brace and a barred grate). Saved as "doorA" and
                      "doorB", 192 x 256, fully opaque.

Dirt: tools/raw/dirt_b.png (Google gemini-3.1-flash-image edit with wall.jpg and floor.jpg as style references)
is made seamless (blended with a half-offset copy of itself) and saved as assets/dirt.jpg, 512 x 512, for the
tops of walls and the wall faces that face no room.
Then it rewrites assets/meta.json and the inline `const META = ...` line in index.html.
"""
import importlib.util, json, pathlib, re, sys
from PIL import Image
import numpy as np

HERE = pathlib.Path(__file__).parent
GAME = HERE.parent
RAW = HERE / "raw"
DIRT = "dirt_b.png"              # the dirt texture
BONES_W = 200                    # the searched pile's width in px (the full pile is 148)
DOOR_SIZE = (192, 256)           # the door leaves (drawn over one wall face, 1 tile x WALLH)

spec = importlib.util.spec_from_file_location("add_items", HERE / "add_items.py")
ai = importlib.util.module_from_spec(spec); spec.loader.exec_module(ai)
key_cell, keep_main, bbox = ai.key_cell, ai.keep_main, ai.bbox


def piece(rgb, x0, x1, whole=True):
    """Key a part of a sheet; whole: keep only the largest figure, else every piece (loose bones)."""
    cell = key_cell(rgb[:, x0:x1], 6)
    cell = keep_main(cell, 0.3, True) if whole else cell
    b = bbox(cell)
    return cell[b[1]:b[3], b[0]:b[2]]


def seamless(im):
    a = np.asarray(im.convert("RGB").resize((512, 512), Image.LANCZOS)).astype(np.float32)
    b = np.roll(np.roll(a, 256, 0), 256, 1)
    t = np.minimum(np.linspace(0, 1, 512), np.linspace(1, 0, 512)) * 2       # 0 at the edges, 1 in the middle
    m = np.clip(np.minimum.outer(t, t) * 1.6, 0, 1)[..., None]
    return Image.fromarray((a * m + b * (1 - m)).astype(np.uint8))


def main():
    # door leaves: the two doors of doors.png, cropped inside their edge to fully opaque rectangles
    rgb = np.asarray(Image.open(RAW / "doors.png").convert("RGB"))
    W = rgb.shape[1]
    leaves = []
    for x0, x1 in ((0, W // 2), (W // 2, W)):
        im = Image.fromarray(piece(rgb, x0, x1), "RGBA")
        leaves.append(im.crop((4, 4, im.width - 4, im.height - 4)).convert("RGBA").resize(DOOR_SIZE, Image.LANCZOS))
    rgb = np.asarray(Image.open(RAW / "bones_searched.png").convert("RGB"))
    bones = Image.fromarray(piece(rgb, 0, rgb.shape[1], False), "RGBA")
    bones = bones.resize((BONES_W, round(bones.height * BONES_W / bones.width)), Image.LANCZOS)

    meta = json.loads((GAME / "assets" / "meta.json").read_text())
    base_h = max(v[3] for v in meta["props"].values() if v[1] == 0)
    props = Image.open(GAME / "assets" / "props.webp").convert("RGBA")
    pieces = [("bonesused", bones), ("doorA", leaves[0]), ("doorB", leaves[1])]
    meta["props"] = {k: v for k, v in meta["props"].items() if v[1] == 0}
    row_h = max(p.height for _, p in pieces)
    atlas = Image.new("RGBA", (max(props.width, sum(p.width + 2 for _, p in pieces)), base_h + 2 + row_h))
    atlas.paste(props.crop((0, 0, props.width, base_h)), (0, 0))
    x = 0
    for n, im in pieces:
        atlas.paste(im, (x, base_h + 2))
        meta["props"][n] = [x, base_h + 2, im.width, im.height]
        x += im.width + 2
    atlas.save(GAME / "assets" / "props.webp", quality=90, method=6)
    meta.pop("doorHole", None)
    seamless(Image.open(RAW / DIRT)).save(GAME / "assets" / "dirt.jpg", quality=88)

    (GAME / "assets" / "meta.json").write_text(json.dumps(meta, indent=1))
    html = (GAME / "index.html").read_text()
    html, n = re.subn(r"^const META = .*;$", "const META = " + json.dumps(meta, separators=(",", ":")) + ";", html, count=1, flags=re.M)
    if n != 1:
        sys.exit("const META line not found in index.html")
    (GAME / "index.html").write_text(html)
    print(f"props.webp {atlas.size}; dirt.jpg from {DIRT}; META updated")


if __name__ == "__main__":
    main()
