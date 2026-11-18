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


def sheet(key, label, g8, p8, fw, fh, note):
    gs, ps, off, ghost = stats(g8, p8, 8, 8, DIRS)
    gG, _ = gc.cell_stats(*gc.load(g8), 8, 8)
    pP, _ = gc.cell_stats(*gc.load(p8), 8, 8)
    gc_, pc_ = cells(g8, 8, 8), cells(p8, 8, 8)
    rows = {}
    for r, d in enumerate(DIRS):
        sl = slice(r * 8, r * 8 + 8)
        o = off[sl]
        facts = "judged by which foot is lower (front / back view)" if d in ("S", "N") else "judged by foot spread"
        if d in ("S", "N"):
            lv = [i % 8 + 1 for i in range(r * 8, r * 8 + 8) if abs(gG[i][1]) > 0.08 and abs(pP[i][1]) < 0.04]
            if lv:
                facts += f"; frame{'s' if len(lv) > 1 else ''} {', '.join(map(str, lv))}: feet nearly level where the guide has one clearly lower"
        bad = [i + 1 for i, x in enumerate(o) if x]
        if bad and d not in ("S", "N"):
            facts += f"; frame{'s' if len(bad) > 1 else ''} {', '.join(map(str, bad))}: stride off the guide"
        rows[d] = dict(n=8, fw=fw, fh=fh, guide=strip([fit(c, fw, fh) for c in gc_[sl]]),
                       paint=strip([fit(c, fw, fh) for c in pc_[sl]]), gs=gs[sl], ps=ps[sl], off=o, ghost=ghost[sl],
                       match=8 - sum(o), view=VIEW[d], facts=facts)
    match = 64 - sum(off)
    print(key, "match", match)
    return dict(key=key, label=label, note=note, rows=rows, match=match)


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
        nw_set("8 frames · shaded mannequin", os_("guide-shaded-NW.png"), os_("openai-shaded-NW-8.png"), 4, 2, 8,
               "4 × 2 · 1536 × 1024 · $0.034 · grey clay guide, no limb colours (render_guide.py --shaded)"),
        nw_set("12 frames · shaded mannequin", os_("guide-shaded-NW-12.png"), os_("openai-shaded-NW-12.png"), 6, 2, 12,
               "6 × 2 · 1536 × 960 · $0.031 · grey clay guide, no limb colours"),
    ]
    sheets = [
        sheet("lo", "1536 × 2048", os_("guide-walk-8x8.png"), os_("openai-walk-8x8.png"), 240, 320,
              "Cells 192 × 256, figure ~200 px. Bright default guide colours: the right trouser leg comes out lighter and "
              "warmer (orange guide colour shows through)."),
        sheet("hi", "2400 × 3200", os_("guide-walk-8x8-hi.png"), os_("openai-walk-8x8-hi.png"), 300, 400,
              "Cells 300 × 400, figure ~320 px: crisp outlines and faces. Same bright guide colours, so the right leg is "
              "still lighter."),
        sheet("bal", "2400 × 3200 · balanced", os_("guide-walk-8x8-hi-bal.png"), os_("openai-walk-8x8-hi-bal.png"),
              300, 400, "As 2400 × 3200, but the guide's orange and yellow are darkened to the lightness of the blue and "
              "teal (render_guide.py --balanced): both legs now the same shade. The 7 faded-limb flags in S are false "
              "alarms (dark olive trousers), not faded legs."),
    ]
    m = {k['key']: k['match'] for k in sheets}
    summary = [
        dict(name="NW 4 × 2 · first prompt", size="1536 × 1024", fig="~390 px", stride="8 / 8", strideOk=True,
             ghost="3 frames", ghostOk=False, cost="$0.034", note="The faded far boot (frames 4, 6) and arm (8)."),
        dict(name="NW 4 × 2 · opaque prompt", size="1536 × 1024", fig="~390 px", stride="8 / 8", strideOk=True,
             ghost="none", ghostOk=True, cost="$0.034", note="Same guide, one added line: every part fully opaque."),
        dict(name="NW 5 × 2 · 10 frames", size="1520 × 960", fig="~390 px", stride="10 / 10", strideOk=True,
             ghost="none", ghostOk=True, cost="$0.031", note="Smoother at villager pace; game needs fpt × 1.25."),
        dict(name="NW 6 × 2 · 12 frames", size="1536 × 960", fig="~390 px", stride="12 / 12", strideOk=True,
             ghost="none", ghostOk=True, cost="$0.031", note="Smoothest at villager pace; game needs fpt × 1.5."),
        dict(name="NW 4 × 2 · shaded mannequin", size="1536 × 1024", fig="~390 px", stride="8 / 8", strideOk=True,
             ghost="none", ghostOk=True, cost="$0.034",
             note="No limb colours: legs the same shade, rounder shading. Cloak shrank to a capelet."),
        dict(name="NW 6 × 2 · shaded, 12 frames", size="1536 × 960", fig="~390 px", stride="12 / 12", strideOk=True,
             ghost="none", ghostOk=True, cost="$0.031",
             note="As above, 12 frames: the most natural shoulder and hip motion so far."),
        dict(name="8 × 8 · 1536 × 2048", size="1536 × 2048", fig="~200 px", stride=f"{m['lo']} / 64",
             strideOk=m['lo'] == 64, ghost="none", ghostOk=True, cost="$0.055",
             note="Soft, smudgy shading; right leg lighter (guide colour shows through)."),
        dict(name="8 × 8 · 2400 × 3200", size="2400 × 3200", fig="~320 px", stride=f"{m['hi']} / 64",
             strideOk=m['hi'] == 64, ghost="none", ghostOk=True, cost="$0.104",
             note="Near OpenAI's maximum (~8.3 MP). Much crisper; right leg still lighter. NW frame 2: short stride."),
        dict(name="8 × 8 · 2400 × 3200 balanced", size="2400 × 3200", fig="~320 px", stride=f"{m['bal']} / 64",
             strideOk=m['bal'] == 64, ghost="none", ghostOk=True, cost="$0.104",
             note="Darker orange / yellow in the guide: legs even. Recommended."),
    ]
    data = dict(nw=nw, sheets=sheets, summary=summary)
    html = (HERE / "options_template.html").read_text(encoding="utf-8").replace("__DATA__", json.dumps(data))
    out.write_text(html, encoding="utf-8")
    print(out, round(out.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
