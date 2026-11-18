"""Character board: the review page kept up to date (as an Artifact) while a character is made.

  python board.py <character.json> <out.html>

Shows the reference candidates (the approved one marked), the mannequin guide and the painted walk for every
direction on one shared clock (pace presets, step, guide overlay, dark / light / checker floor), each direction's
checks (stride match, faded limbs, colour match with the reference) and status, and the decisions and spend so far.
Rebuild and republish to the same Artifact URL after every step. All images are embedded (WebP data URIs).

character.json (in the character's folder; paths are relative to it). Only "name" is required:
  {
    "name": "Ranger",
    "description": "a lean young ranger ...",          # the CHARACTER text for guide_prompt.py --character
    "frames": 12, "mirror": true,                      # decisions (null = not decided yet)
    "guide": "walk",                                   # a set in ../guides (walk, formal-walk, jog, stick-walk)
                                                       # or a folder of <DIR>.png (a custom render_guide.py set)
    "body": "adult 1.82 m, EU 43",                     # how the guide was rendered (shown only)
    "references": [{"file": "reference-1.png", "status": "approved", "note": "..."}],   # candidate / rejected
    "directions": {"NW": {"file": "paint/NW.png", "status": "approved"}},              # review / redo
    "next": "Paint SW",                                # shown at the top
    "spend": [{"what": "3 references", "usd": 0.13}],
    "artifact": "https://claude.ai/artifact/..."
  }
"""
import base64, io, json, pathlib, sys
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grid_check as gc  # noqa: E402

DIRS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
MIRROR = {"SE": "SW", "E": "W", "NE": "NW"}
VIEW = {"S": "toward the viewer", "SW": "toward the lower left", "W": "left, in profile",
        "NW": "away, to the upper left", "N": "away from the viewer", "NE": "away, to the upper right",
        "E": "right, in profile", "SE": "toward the lower right"}
FW, FH = 240, 320


def rgba(path):
    a = np.asarray(Image.open(path).convert("RGBA")).copy()
    if (a[..., 3] < 128).mean() < 0.2:                       # flat magenta guide -> transparent
        r, g, b = (a[..., i].astype(int) for i in range(3))
        m = np.clip(((np.minimum(r, b) - g) - 60) / 120, 0, 1)
        a[..., 3] = ((1 - m) * 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def cells(path, cols, rows):
    im = rgba(path); W, H = im.size; cw, ch = W / cols, H / rows
    return [im.crop((round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch)))
            for r in range(rows) for c in range(cols)]


def fit(cell, fw=FW, fh=FH):
    s = min(fh / cell.height, fw / cell.width)
    im = cell.resize((max(1, round(cell.width * s)), max(1, round(cell.height * s))), Image.LANCZOS)
    out = Image.new("RGBA", (fw, fh))
    out.alpha_composite(im, ((fw - im.width) // 2, fh - im.height))
    return out


def uri(im, q=86):
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=q, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def strip(frames):
    s = Image.new("RGBA", (frames[0].width * len(frames), frames[0].height))
    for i, f in enumerate(frames):
        s.alpha_composite(f, (i * f.width, 0))
    return uri(s)


def guide_path(ch, base, d):
    g = ch.get("guide") or "walk"
    folder = HERE.parent / "guides" / g / f"{ch.get('frames') or 8}f"
    if not folder.exists():
        folder = base / g
    p = folder / f"{d}.png"
    return p if p.exists() else None


def layout(path, n):
    side = path.with_suffix(".json")
    if side.exists():
        j = json.loads(side.read_text())
        return j["cols"], j["rows"]
    return (4, 2) if n == 8 else (6, 2)


def main():
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    ch = json.loads(src.read_text(encoding="utf-8")); base = src.parent
    n = ch.get("frames") or 8
    refs = []
    approved_ref = None
    for r in ch.get("references", []):
        p = base / r["file"]
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA"); im.thumbnail((900, 600), Image.LANCZOS)
        refs.append(dict(src=uri(im, 88), status=r.get("status", "candidate"), note=r.get("note", ""), file=r["file"]))
        if r.get("status") == "approved":
            approved_ref = p
    dirs = []
    dmeta = ch.get("directions", {})
    for d in DIRS:
        mirrored = bool(ch.get("mirror")) and d in MIRROR
        src_d = MIRROR[d] if mirrored else d
        gp = guide_path(ch, base, src_d)
        info = dmeta.get(src_d, {})
        pp = base / info["file"] if info.get("file") else None
        e = dict(d=d, view=VIEW[d], mirrored=mirrored, of=src_d if mirrored else None, n=n,
                 status=("mirror" if mirrored else info.get("status", "not painted" if not pp else "review")))
        if gp:
            cols, rows = layout(gp, n)
            e["guide"] = strip([fit(c) for c in cells(gp, cols, rows)][:n])
            if pp and pp.exists():
                e["paint"] = strip([fit(c) for c in cells(pp, cols, rows)][:n])
                G, _ = gc.cell_stats(*gc.load(str(gp)), cols, rows)
                P, area = gc.cell_stats(*gc.load(str(pp)), cols, rows)
                gmax = gc.GHOST_PX * area / (384 * 512)
                off = [bool(abs(g[1]) > 0.08 and np.sign(g[1]) != np.sign(p[1])) if src_d in ("S", "N")
                       else bool(abs(g[0] - p[0]) > 0.2) for g, p in zip(G, P)][:n]
                e.update(gs=[round(float(g[0]), 3) for g in G][:n], ps=[round(float(p[0]), 3) for p in P][:n],
                         off=off, ghost=[bool(p[2] > gmax) for p in P][:n], match=n - sum(off))
                if approved_ref:
                    e["colour"] = round(gc.drift(str(pp), str(approved_ref)), 2)
        dirs.append(e)
    spend = ch.get("spend", [])
    data = dict(name=ch.get("name", "Character"), description=ch.get("description", ""), frames=ch.get("frames"),
                mirror=ch.get("mirror"), guide=ch.get("guide") or "walk", body=ch.get("body", "adult 1.82 m, EU 43"),
                next=ch.get("next", ""), refs=refs, dirs=dirs, spend=spend,
                total=round(sum(s.get("usd", 0) for s in spend), 3))
    html = (HERE / "board_template.html").read_text(encoding="utf-8")
    html = html.replace("__TITLE__", f"{data['name']} Sprite Board").replace("__DATA__", json.dumps(data))
    out.write_text(html, encoding="utf-8")
    print(out, round(out.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
