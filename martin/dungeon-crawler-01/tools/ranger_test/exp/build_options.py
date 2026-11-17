"""Build the options comparison page (options_template.html + embedded WebP frame strips + grid_check numbers).

  python build_options.py <out.html>
Run from tools/ranger_test/exp. Inputs: the guides and OpenAI paintings in this folder and ../ (see SETS).
"""
import base64, io, json, pathlib, sys
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import grid_check as gc  # noqa: E402

DIRS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
VIEW = {"S": "toward the viewer", "SW": "toward the lower left", "W": "left, in profile", "NW": "away, to the upper left",
        "N": "away from the viewer", "NE": "away, to the upper right", "E": "right, in profile",
        "SE": "toward the lower right"}


def rgba(path):
    a = np.asarray(Image.open(path).convert("RGBA")).copy()
    if (a[..., 3] < 128).mean() < 0.2:            # flat magenta guide -> transparent
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        m = np.clip(((np.minimum(r, b) - g) - 60) / 120, 0, 1)
        a[..., 3] = ((1 - m) * 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def cells(path, cols, rows):
    im = rgba(path); W, H = im.size; cw, ch = W / cols, H / rows
    return [im.crop((round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch)))
            for r in range(rows) for c in range(cols)]


def fit(cell, fw, fh):
    s = fh / cell.height
    im = cell.resize((max(1, round(cell.width * s)), fh), Image.LANCZOS)
    out = Image.new("RGBA", (fw, fh))
    out.alpha_composite(im, (round((fw - im.width) / 2), 0)) if im.width <= fw else \
        out.alpha_composite(im.crop(((im.width - fw) // 2, 0, (im.width - fw) // 2 + fw, fh)))
    return out


def strip(frames):
    s = Image.new("RGBA", (frames[0].width * len(frames), frames[0].height))
    for i, f in enumerate(frames):
        s.alpha_composite(f, (i * f.width, 0))
    buf = io.BytesIO(); s.save(buf, "WEBP", quality=86, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def stats(guide, paint, cols, rows, dirs=None):
    G, _ = gc.cell_stats(*gc.load(guide), cols, rows)
    P, area = gc.cell_stats(*gc.load(paint), cols, rows)
    gmax = gc.GHOST_PX * area / (384 * 512)
    off, ghost = [], []
    for i, (g, p) in enumerate(zip(G, P)):
        d = dirs[i // cols] if dirs else None
        if d in ("S", "N"):
            o = abs(g[1]) > 0.08 and np.sign(g[1]) != np.sign(p[1])
        else:
            o = abs(g[0] - p[0]) > 0.2
        off.append(bool(o)); ghost.append(bool(p[2] > gmax))
    return [round(float(g[0]), 3) for g in G], [round(float(p[0]), 3) for p in P], off, ghost


def nw_set(name, guide, paint, cols, rows, n, facts, fw=300, fh=400):
    gs, ps, off, ghost = stats(guide, paint, cols, rows)
    gfr = [fit(c, fw, fh) for c in cells(guide, cols, rows)][:n]
    pfr = [fit(c, fw, fh) for c in cells(paint, cols, rows)][:n]
    print(name, "match", n - sum(off), "faded", sum(ghost))
    return dict(name=name, n=n, fw=fw, fh=fh, guide=strip(gfr), paint=strip(pfr), gs=gs[:n], ps=ps[:n], off=off[:n],
                ghost=ghost[:n], match=n - sum(off[:n]), facts=facts)


def main():
    out = pathlib.Path(sys.argv[1])
    os_ = lambda p: str(HERE / p)
    nw = [
        nw_set("8 frames · first prompt", os_("../guide-mocap-NW.png"), os_("../openai-mocap-NW.png"), 4, 2, 8,
               "4 × 2 · 1536 × 1024 · far boot faded in frames 4 and 6, arm in 8"),
        nw_set("8 frames · opaque prompt", os_("../guide-mocap-NW.png"), os_("openai-walk-NW-8.png"), 4, 2, 8,
               "4 × 2 · 1536 × 1024 · $0.034"),
        nw_set("10 frames", os_("guide-walk-NW-10.png"), os_("openai-walk-NW-10.png"), 5, 2, 10,
               "5 × 2 · 1520 × 960 · $0.031"),
        nw_set("12 frames", os_("guide-walk-NW-12.png"), os_("openai-walk-NW-12.png"), 6, 2, 12,
               "6 × 2 · 1536 × 960 · $0.031"),
    ]
    g8, p8 = os_("guide-walk-8x8.png"), os_("openai-walk-8x8.png")
    gs, ps, off, ghost = stats(g8, p8, 8, 8, DIRS)
    gc_, pc_ = cells(g8, 8, 8), cells(p8, 8, 8)
    rows = {}
    for r, d in enumerate(DIRS):
        sl = slice(r * 8, r * 8 + 8)
        o = off[sl]
        rows[d] = dict(n=8, fw=240, fh=320, guide=strip([fit(c, 240, 320) for c in gc_[sl]]),
                       paint=strip([fit(c, 240, 320) for c in pc_[sl]]), gs=gs[sl], ps=ps[sl], off=o, ghost=ghost[sl],
                       match=8 - sum(o), view=VIEW[d],
                       facts=("judged by which foot is lower (front / back view)" if d in ("S", "N")
                              else "judged by foot spread"))
    rows["S"]["facts"] += "; frames 2 and 3: feet nearly level where the guide has the left foot clearly lower"
    rows["N"]["facts"] += "; frames 4 and 8: feet nearly level where the guide has one clearly lower"
    match8 = 64 - sum(off)
    summary = [
        dict(name="NW 4 × 2 · first prompt", size="1536 × 1024", fig="~390 px", stride="8 / 8", strideOk=True,
             ghost="3 frames", ghostOk=False, cost="$0.034", note="The faded far boot (frames 4, 6) and arm (8)."),
        dict(name="NW 4 × 2 · opaque prompt", size="1536 × 1024", fig="~390 px", stride="8 / 8", strideOk=True,
             ghost="none", ghostOk=True, cost="$0.034", note="Same guide, one added line: every part fully opaque."),
        dict(name="NW 5 × 2 · 10 frames", size="1520 × 960", fig="~390 px", stride="10 / 10", strideOk=True,
             ghost="none", ghostOk=True, cost="$0.031", note="Smoother at villager pace; game needs fpt × 1.25."),
        dict(name="NW 6 × 2 · 12 frames", size="1536 × 960", fig="~390 px", stride="12 / 12", strideOk=True,
             ghost="none", ghostOk=True, cost="$0.031", note="Smoothest at villager pace; game needs fpt × 1.5."),
        dict(name="All 8 directions · 8 × 8", size="1536 × 2048", fig="~200 px", stride=f"{match8} / 64",
             strideOk=match8 == 64, ghost="none", ghostOk=True, cost="$0.055",
             note="One consistent character; E, NE, SE painted, not mirrored. 5 directions one by one: ~$0.17."),
    ]
    data = dict(nw=nw, sheet=dict(rows=rows), summary=summary)
    html = (HERE / "options_template.html").read_text(encoding="utf-8").replace("__DATA__", json.dumps(data))
    out.write_text(html, encoding="utf-8")
    print(out, round(out.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
