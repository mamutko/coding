"""Review sheets for one painted direction: what to LOOK AT before accepting it (SKILL.md, "Review every direction").

  python review.py <character.json> <DIR> [--out DIR] [--paint paint/E.png]

Writes, next to the painting unless --out:
  review-<DIR>-frames.png  every frame: the guide cell over the painted cell on a dark floor, labelled with the frame
                           number and which leg should be IN FRONT (stick guide: NEAR / FAR in side and diagonal
                           views, L / R in S and N; '-' = legs passing). Look at it at full size.
  review-<DIR>-legs.png    the legs only (lower half of each figure), guide over painting, 2x, same labels: here
                           decide for EVERY frame which painted leg is in front (the near leg is the one drawn over
                           the other where they cross, its hip end the lower on screen) and compare with the label.
and prints per frame the expected leading leg, and the LEG SHADE check: the mean brightness of the back leg minus
the front leg (the two legs found as two blobs in the shin-and-knee band of the figure, matched to the guide's feet by their order
on screen). A painting whose back leg is clearly darker (mean below -12 over the frames with the feet apart) is
flagged, and so is one whose FAR leg is (side and diagonal views): Martin noticed the back leg painted much darker,
which came from a guide that drew the far leg dark (hero-6 v174: far minus near -16 to -20 in E, W, SE). Both legs
should be painted alike (within about 12).

Guide cells come from the character's guide set (character.json "guide", as build_sheet.py finds it) and its
sidecar (feet per frame); the expected leading leg from stick_guide.leading (stick guides) or from the sidecar's feet.
"""
import json, math, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import stick_guide as sg
from build_sheet import guide_for, figures, load_rgba

FLOOR = (44, 42, 48, 255)


def opt(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def lead_labels(side, d, n):
    if side.get("stick"):
        sg.wc.use("hero")
        return [x.upper() if x != "-" else "-" for x in sg.leading(n, d)]
    # mocap guides: which ball of the foot is further along the walking direction on screen (rough)
    a = math.radians(45 * ((8 - sg.ROWS.index(d)) % 8))
    fwd = np.array([math.sin(a), 0.5 * math.cos(a)])                  # walking direction on screen (S: down)
    out = []
    for f in side["feet"][:n]:
        dl = np.dot(np.array(f[0]) - np.array(f[1]), fwd)
        out.append("-" if abs(dl) < 15 else ("L" if dl > 0 else "R"))
    return out


def feet_blobs(cell_rgba, lo=0.06, hi=0.26):
    """The two legs of a painted figure: (x centre, mean luminance) of the left and right blob in a band of the
    figure's height (lo..hi from the soles: the shins and knees, where a darker painted leg shows most)."""
    a = cell_rgba[..., 3] > 200
    ys, xs = np.nonzero(a)
    if len(ys) == 0:
        return None
    top, bot = ys.min(), ys.max(); y0, y1 = int(bot - hi * (bot - top)), int(bot - lo * (bot - top))
    band = a[y0:y1 + 1]; L = cell_rgba[y0:y1 + 1, :, :3].astype(float).mean(-1)
    cols = np.nonzero(band.any(0))[0]
    gaps = np.diff(cols)
    if len(gaps) == 0 or gaps.max() <= 4:
        return None                                                    # feet together / overlapping
    cut = cols[np.argmax(gaps)] + gaps.max() / 2
    X = np.arange(cell_rgba.shape[1])[None, :]
    l, r = band & (X < cut), band & (X >= cut)
    return [(float(np.nonzero(l)[1].mean()), float(L[l].mean())), (float(np.nonzero(r)[1].mean()), float(L[r].mean()))]


def main():
    src = pathlib.Path(sys.argv[1]); d = sys.argv[2]
    ch = json.loads(src.read_text(encoding="utf-8")); base = src.parent
    paint = pathlib.Path(opt("--paint")) if opt("--paint") else base / ch["directions"][d]["file"]
    gp = guide_for(ch, base, d); side = json.loads(gp.with_suffix(".json").read_text())
    n, cols, (cw, chh) = ch["frames"], side["cols"], side["cell"]
    out = pathlib.Path(opt("--out", str(paint.parent)))
    g = Image.open(gp).convert("RGBA"); p = Image.open(paint).convert("RGBA")
    labels = lead_labels(side, d, n)
    feet = side.get("feet")
    # frames sheet and legs sheet
    fr_sheet = Image.new("RGBA", (cw * cols, chh * 2 * side["rows"] + 24 * side["rows"]), FLOOR)
    lg_h, K = int(chh * 0.64), 1.3                                 # from above the hips down: the crossing shows
    LW, LH = int(cw * K), int(lg_h * K)
    lg_sheet = Image.new("RGBA", (LW * cols, (LH * 2 + 28) * side["rows"]), FLOOR)
    df, dl = ImageDraw.Draw(fr_sheet), ImageDraw.Draw(lg_sheet)
    shade = []
    parr = np.asarray(p)
    for i in range(n):
        r, c = divmod(i, cols); box = (c * cw, r * chh, (c + 1) * cw, (r + 1) * chh)
        gc = g.crop(box); pc = Image.new("RGBA", (cw, chh), FLOOR); pc.alpha_composite(p.crop(box))
        y = r * (chh * 2 + 24)
        df.text((c * cw + 6, y + 4), f"{i + 1}: in front {labels[i]}", fill=(240, 220, 120, 255))
        fr_sheet.paste(gc, (c * cw, y + 24)); fr_sheet.paste(pc, (c * cw, y + 24 + chh))
        # legs: the lower half of the cell, 2x, cropped to the cell width
        yl = r * (LH * 2 + 28)
        dl.text((c * LW + 6, yl + 4), f"{i + 1}: in front {labels[i]}", fill=(240, 220, 120, 255))
        plc = pc.crop((0, chh - lg_h, cw, chh)).resize((LW, LH), Image.LANCZOS)
        glc = gc.crop((0, chh - lg_h, cw, chh)).resize((LW, LH), Image.LANCZOS)
        lg_sheet.paste(glc, (c * LW, yl + 28)); lg_sheet.paste(plc, (c * LW, yl + 28 + LH))
        dl.line([(c * LW, yl), (c * LW, yl + 28 + 2 * LH)], fill=(90, 90, 100, 255), width=2)
        # leg shade: back boot minus front boot
        fb = feet_blobs(parr[box[1]:box[3], box[0]:box[2]])
        if fb and feet:
            a = math.radians(45 * ((8 - sg.ROWS.index(d)) % 8)); fwd = np.array([math.sin(a), 0.5 * math.cos(a)])
            gl_, gr_ = np.array(feet[i][0]), np.array(feet[i][1])
            if abs(np.dot(gl_ - gr_, fwd)) > 15 and abs(gl_[0] - gr_[0]) > 8:
                left_is_L = gl_[0] < gr_[0]                              # the guide's left foot is the image-left one
                front_L = np.dot(gl_ - gr_, fwd) > 0
                front_img_left = front_L == left_is_L
                fl, fr_ = (fb[0], fb[1]) if front_img_left else (fb[1], fb[0])
                bf = fr_[1] - fl[1]                                     # back minus front
                nf = (-bf if labels[i] == "FAR" else bf) if labels[i] in ("NEAR", "FAR") else None   # far minus near
                shade.append((i + 1, bf, nf))
    fr_sheet.save(out / f"review-{d}-frames.png"); lg_sheet.save(out / f"review-{d}-legs.png")
    print(d, "in front, figure by figure:", " ".join(f"{i + 1}:{x}" for i, x in enumerate(labels)))
    if shade:
        m = float(np.mean([s for _, s, _ in shade]))
        flag = "  !BACK LEG DARKER" if m < -12 else ""
        print(f"{d} leg shade, back leg minus front leg (luminance): mean {m:+.0f} over {len(shade)} frames "
              f"[{' '.join(f'{i}:{s:+.0f}' for i, s, _ in shade)}]{flag}")
        nf = [x for _, _, x in shade if x is not None]
        if nf:
            m2 = float(np.mean(nf))
            print(f"{d} leg shade, far leg minus near leg: mean {m2:+.0f}" + ("  !FAR LEG DARKER" if m2 < -10 else ""))
    print("->", out / f"review-{d}-frames.png", out / f"review-{d}-legs.png")


if __name__ == "__main__":
    main()
