"""Add the satchel (a closed and an opened leather satchel, the surface's satchel by the portal) to the props atlas.

Usage:  python tools/add_satchel.py            (run from the game folder; needs Pillow + NumPy)

Raw sheet tools/raw/satchels.png: Google gemini-3.1-flash-image edit with the chest, the opened chest, an urn and
the bone pile from props.webp on magenta as the style reference, 3 x 2 cells: three satchel designs, closed (top
row) and the same opened and empty (bottom row). Design 1 (brown leather, a brass buckle, a coiled shoulder strap)
is the game's satchel: props "satchel" and "satchelopen", scaled to SATCHEL_H px high (closed). All six are also
saved keyed out in assets/unused/satchels (satchel1-3.png, satchel1-3open.png) for later use.

The satchel goes in a row of its own below everything else in props.webp, so the other props (from process_art.py,
add_props.py, add_market.py) are untouched; running it again replaces that row. Then it rewrites assets/meta.json
and the inline `const META = ...` line in index.html.
"""
import importlib.util, json, pathlib, re, sys
from PIL import Image
import numpy as np

HERE = pathlib.Path(__file__).parent
GAME = HERE.parent
SATCHEL_H = 120                  # the closed satchel's height in px (the chest is 141)
KEYS = ("satchel", "satchelopen")

spec = importlib.util.spec_from_file_location("add_items", HERE / "add_items.py")
ai = importlib.util.module_from_spec(spec); spec.loader.exec_module(ai)


def cells():
    rgb = np.asarray(Image.open(HERE / "raw" / "satchels.png").convert("RGB"))
    H, W = rgb.shape[:2]
    out = []
    for r in range(2):
        for c in range(3):
            cell = ai.key_cell(rgb[r * H // 2:(r + 1) * H // 2, c * W // 3:(c + 1) * W // 3], 6)
            b = ai.bbox(cell)
            out.append(Image.fromarray(cell[b[1]:b[3], b[0]:b[2]], "RGBA"))
    return out   # 0-2 closed, 3-5 opened


def main():
    cs = cells()
    un = GAME / "assets" / "unused" / "satchels"; un.mkdir(parents=True, exist_ok=True)
    for i in range(3):
        cs[i].save(un / f"satchel{i + 1}.png"); cs[i + 3].save(un / f"satchel{i + 1}open.png")
    k = SATCHEL_H / cs[0].height   # the same scale for both, so the opened one matches the closed one
    pieces = [(n, im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)) for n, im in zip(KEYS, (cs[0], cs[3]))]

    meta = json.loads((GAME / "assets" / "meta.json").read_text())
    for n in KEYS: meta["props"].pop(n, None)
    bottom = max(v[1] + v[3] for v in meta["props"].values())
    props = Image.open(GAME / "assets" / "props.webp").convert("RGBA")
    row_h = max(p.height for _, p in pieces)
    atlas = Image.new("RGBA", (max(props.width, sum(p.width + 2 for _, p in pieces)), bottom + 2 + row_h))
    atlas.paste(props.crop((0, 0, props.width, bottom)), (0, 0))
    x = 0
    for n, im in pieces:
        atlas.paste(im, (x, bottom + 2)); meta["props"][n] = [x, bottom + 2, im.width, im.height]; x += im.width + 2
    atlas.save(GAME / "assets" / "props.webp", quality=90, method=6)
    (GAME / "assets" / "meta.json").write_text(json.dumps(meta, indent=1))
    html = (GAME / "index.html").read_text()
    html, n = re.subn(r"^const META = .*;$", "const META = " + json.dumps(meta, separators=(",", ":")) + ";", html, count=1, flags=re.M)
    if n != 1: sys.exit("const META line not found in index.html")
    (GAME / "index.html").write_text(html)
    print(f"props.webp {atlas.size}; satchel {meta['props']['satchel']}, satchelopen {meta['props']['satchelopen']}; META updated")


if __name__ == "__main__":
    main()
