"""Append the newer item icons to the item atlas (assets/items.webp) and the META item table.

Usage:  python tools/add_items.py            (run from the game folder; needs Pillow + NumPy)

The original 24 icons (the first 4 rows of items.webp, from process_art.py) are kept as they are; this
script rebuilds the rows after them from the raw sheets below, so running it again gives the same atlas.

Raw sheets (tools/raw):
  items2.png  Google gemini-3.1-flash-image edit with the old atlas as a style reference, 6 x 4 cells.
              The model kept the reference's 4-row layout, copied some old icons and painted rows 1-2 on dark
              purple instead of magenta, so only the cells listed below are used, keyed against each
              cell's own background.
  items3.png  OpenAI gpt-image-2 (medium), 3 x 2 cells on magenta (cell 6, a belt pouch, is unused).
  firebombs.png  OpenAI gpt-image-2 (medium), 3 x 2 cells on magenta: six fire bomb designs (firebomb1-6),
              the look options for the fire bomb (see README, Fire bombs).
Then it rewrites assets/meta.json and the inline `const META = ...` line in index.html.
"""
import ast, json, pathlib, re, sys
from PIL import Image
import numpy as np

HERE = pathlib.Path(__file__).parent
GAME = HERE.parent
RAW = HERE / "raw"
ICON = 96
BASE_ROWS = 4   # rows of the original atlas to keep

# reuse keep_main() and bbox() from process_art.py without running that script
src = (HERE / "process_art.py").read_text()
ns = {"np": np}
for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef) and node.name in ("keep_main", "bbox"):
        exec(compile(ast.Module([node], []), "process_art.py", "exec"), ns)
keep_main, bbox = ns["keep_main"], ns["bbox"]

# (sheet, cols, rows, [(cell index, item key), ...]) in atlas order
SHEETS = [
    ("items2.png", 6, 4, [(0, "broadsword"), (1, "bastardsword"), (2, "knightsword"), (3, "beardedaxe"),
                          (4, "greataxe"), (5, "huntingbow"), (9, "ironhelm"), (10, "visoredhelm"),
                          (11, "studded"), (13, "platedgloves"), (14, "heavygloves"), (17, "chainmail"),
                          (23, "quiver")]),
    ("items3.png", 3, 2, [(0, "warbow"), (1, "compositebow"), (2, "fullplate"), (3, "greaves"),
                          (4, "heavygreaves")]),
    ("firebombs.png", 3, 2, [(0, "firebomb1"), (1, "firebomb2"), (2, "firebomb3"), (3, "firebomb4"),
                             (4, "firebomb5"), (5, "firebomb6")]),
]


def key_cell(rgb, inset):
    """Key out a cell's background: the colour of its border, flood-filled from the border."""
    a = rgb[inset:-inset, inset:-inset].astype(np.float32)
    h, w = a.shape[:2]
    ring = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3), a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    bg = np.median(ring, axis=0)
    dist = np.sqrt(((a - bg) ** 2).sum(-1))
    near = dist < 45
    # background = near-colour pixels connected to the border (iterative dilation inside `near`)
    fill = np.zeros((h, w), bool)
    fill[0], fill[-1], fill[:, 0], fill[:, -1] = near[0], near[-1], near[:, 0], near[:, -1]
    while True:
        g = fill.copy()
        g[1:] |= fill[:-1]; g[:-1] |= fill[1:]; g[:, 1:] |= fill[:, :-1]; g[:, :-1] |= fill[:, 1:]
        g &= near
        if (g == fill).all():
            break
        fill = g
    # enclosed background (e.g. between a bow and its string): near-colour pixels not reached from the border
    fill |= dist < 32
    alpha = np.where(fill, 0.0, 1.0)
    # soft edge: foreground pixels touching the background get alpha from their colour distance
    edge = np.zeros((h, w), bool)
    edge[1:] |= fill[:-1]; edge[:-1] |= fill[1:]; edge[:, 1:] |= fill[:, :-1]; edge[:, :-1] |= fill[:, 1:]
    edge &= ~fill
    alpha[edge] = np.clip((dist[edge] - 45) / 50, 0.25, 1)
    # plus the magenta key of process_art.py (strongly magenta pixels are background on any sheet; the dark
    # purple background of items2.png rows 1-2 isn't magenta enough to trip it)
    m = np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
    alpha = np.minimum(alpha, np.clip((200.0 - m) / 130.0, 0, 1))
    alpha[alpha < 0.06] = 0
    # un-mix the edge colour from the background, then remove leftover background tint
    safe = np.maximum(alpha, 1e-3)[..., None]
    col = np.clip((a - (1 - alpha)[..., None] * bg) / safe, 0, 255)
    r, g_, b = col[..., 0], col[..., 1], col[..., 2]
    spill = np.maximum(np.minimum(r, b) - g_ - 6, 0)   # no item here is purple, so despill everywhere
    col[..., 0] -= spill; col[..., 2] -= spill
    return np.dstack([col, alpha * 255]).astype(np.uint8)


def main():
    base = Image.open(GAME / "assets" / "items.webp").convert("RGBA").crop((0, 0, ICON * 6, ICON * BASE_ROWS))
    icons = []
    for name, cols, rows, cells in SHEETS:
        rgb = np.asarray(Image.open(RAW / name).convert("RGB"))
        H, W = rgb.shape[:2]
        for idx, key in cells:
            r, c = divmod(idx, cols)
            y0, y1, x0, x1 = round(r * H / rows), round((r + 1) * H / rows), round(c * W / cols), round((c + 1) * W / cols)
            cell = keep_main(key_cell(rgb[y0:y1, x0:x1], 6), 0.3, True)
            b = bbox(cell)
            im = Image.fromarray(cell[b[1]:b[3], b[0]:b[2]], "RGBA")
            k = (ICON - 6) / max(im.size)
            icons.append((key, im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)))
    meta = json.loads((GAME / "assets" / "meta.json").read_text())
    keep = {k: v for k, v in meta["items"].items() if v[1] < ICON * BASE_ROWS}
    start = len(keep)   # the original atlas is full (24 cells), so new icons start at row 4
    rows = BASE_ROWS + -(-len(icons) // 6)
    atlas = Image.new("RGBA", (ICON * 6, ICON * rows)); atlas.paste(base, (0, 0))
    for i, (key, im) in enumerate(icons):
        r, c = divmod(start + i, 6)
        atlas.paste(im, (c * ICON + (ICON - im.width) // 2, r * ICON + (ICON - im.height) // 2))
        keep[key] = [c * ICON, r * ICON]
    atlas.save(GAME / "assets" / "items.webp", quality=90, method=6)
    meta["items"] = keep
    (GAME / "assets" / "meta.json").write_text(json.dumps(meta, indent=1))
    html = (GAME / "index.html").read_text()
    html, n = re.subn(r"^const META = .*;$", "const META = " + json.dumps(meta, separators=(",", ":")) + ";", html, count=1, flags=re.M)
    if n != 1:
        sys.exit("const META line not found in index.html")
    html, n = re.subn(r"^const ATLAS_W = \d+, ATLAS_H = \d+;", f"const ATLAS_W = {ICON * 6}, ATLAS_H = {ICON * rows};", html, count=1, flags=re.M)
    if n != 1:
        sys.exit("const ATLAS_W / ATLAS_H line not found in index.html")
    (GAME / "index.html").write_text(html)
    print(f"items.webp: {len(keep)} icons, {rows} rows; META updated")


if __name__ == "__main__":
    main()
