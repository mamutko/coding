"""Add a standing-still frame to a built walk sheet: one more column, the character standing at rest in each
direction, so a game shows it instead of a walk frame when the character stops (a walk frame, even the one with the
feet closest, is caught mid-step: a knee bent, a foot lifted).

  python add_stand.py <sheet.webp> <stand_painting.png> <out.webp> --frames 12 [--fw 144 --fh 152]
                      [--meta meta.json --key NAME]

stand_painting: the 8 directions standing, painted over stick_guide.py --stand (a 4 x 2 grid: S SW W NW on top,
N NE E SE below; guide_prompt.py --stand). The sheet keeps its walk frames 0..frames-1; the stand frame goes in
column `frames` (a sheet that already has it is replaced there). Per row:
  scale    the standing figure is as tall as the tallest walk frame of the row (a standing body is the walk's
           straight-leg height),
  place    its soles on the row's ground (the lowest pixel of the row's idle frame, from meta "idle", else the
           median over the row) and its head and shoulders over the walk frames' (the mean centre of the top 45 %).
--meta writes "stand": frames into the key's entry (a game draws column `stand` when the character is still).
"""
import json, pathlib, sys
import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build_sheet import load_rgba, figures

ROWS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]


def opt(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def stats(cell):
    a = cell[..., 3] > 128
    ys, xs = np.nonzero(a)
    if not len(ys):
        return None
    top, bot = ys.min(), ys.max()
    t = a[top:top + int((bot - top) * 0.45) + 1]
    cx = np.nonzero(t)[1].mean()
    return top, bot, cx


def main():
    sheet_p, stand_p, out_p = sys.argv[1:4]
    n = int(opt("--frames")); fw, fh = int(opt("--fw", 144)), int(opt("--fh", 152))
    sheet = np.asarray(Image.open(sheet_p).convert("RGBA"))
    meta_entry = {}
    if opt("--meta"):
        meta_entry = json.loads(pathlib.Path(opt("--meta")).read_text()).get("characters", {}).get(opt("--key"), {})
    idle = meta_entry.get("idle")
    figs = figures(load_rgba(stand_p), 4, 2)
    out = np.zeros((fh * 8, fw * (n + 1), 4), np.uint8)
    out[:, :fw * n] = sheet[:fh * 8, :fw * n]
    for r, d in enumerate(ROWS):
        cells = [sheet[r * fh:(r + 1) * fh, c * fw:(c + 1) * fw] for c in range(n)]
        st = [stats(c) for c in cells]
        st = [s for s in st if s]
        h = max(b - t for t, b, _ in st)
        ground = stats(cells[idle])[1] if idle is not None and stats(cells[idle]) else float(np.median([b for _, b, _ in st]))
        cx = float(np.mean([x for _, _, x in st]))
        f = figs[r]
        fy = np.nonzero(f[..., 3] > 128)[0]
        k = h / (fy.max() - fy.min())
        im = Image.fromarray(f, "RGBA")
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
        s = stats(np.asarray(im))
        x, y = round(fw / 2 + (cx - fw / 2) - s[2]), round(ground - s[1])
        cell = Image.new("RGBA", (fw, fh)); cell.alpha_composite(im, (max(0, x), max(0, y))) if x >= 0 and y >= 0 else cell.paste(im, (x, y), im)
        out[r * fh:(r + 1) * fh, n * fw:(n + 1) * fw] = np.asarray(cell)
        print(d, "stand: scale %.3f, at" % k, (x, y))
    Image.fromarray(out, "RGBA").save(out_p, quality=90, method=6)
    if opt("--meta"):
        mp = pathlib.Path(opt("--meta")); meta = json.loads(mp.read_text())
        meta["characters"][opt("--key")]["stand"] = n
        mp.write_text(json.dumps(meta, indent=1))
    print(out_p, "stand column", n)


if __name__ == "__main__":
    main()
