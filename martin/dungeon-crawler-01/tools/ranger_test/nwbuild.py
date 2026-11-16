import json, pathlib, sys
src = (pathlib.Path(__file__).parent / "build.py").read_text()
src = src.split("sets = []")[0].replace("OUT = pathlib.Path(sys.argv[1]); DST = pathlib.Path(sys.argv[2])", "")
exec(src)
NW = pathlib.Path(sys.argv[1]); DST = pathlib.Path(sys.argv[2])
CHECK = {  # stride_check.py hero NW: frames off the guide by > 0.2 in foot spread (1-based)
  "openai-grey": [1], "openai-color": [1], "google-grey": [3], "google-color": [3]}
SPREAD = {  # (guide, painted) foot spread per frame, from stride_check.py
  "openai-grey": [.13,.56,.39,.16,.14,.11,.12,.43], "openai-color": [.15,.55,.43,.15,.14,.12,.15,.45],
  "google-grey": [.32,.35,.09,.20,.13,.11,.17,.42], "google-color": [.49,.56,.09,.19,.13,.11,.17,.43]}
GUIDE = [.50,.54,.37,.13,.12,.10,.16,.41]
# Anchoring like walk_cycle.py's build: the guide is cut by its exact cells (body origin at the cell centre,
# ground 70 px above the cell bottom), so it keeps the 3D model's real motion. Each painted frame copies its
# guide frame's lowest-pixel offset below the ground and its head x, instead of a fixed ground line.
FW, FH, FOOT = 160, 214, 186
CW, CH, GY = 300, 440, 70
def head_x(alpha):
    ys, xs = np.nonzero(alpha > 128); top, h = ys.min(), ys.max() - ys.min()
    band = alpha[top:top + int(h * 0.15)] > 128
    return np.nonzero(band)[1].mean()
def guide_row(path):
    a = rgba(path); frames, info = [], []
    hs = []
    for i in range(8):
        r, c = divmod(i, 4); cell = a[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW]
        ys, xs = np.nonzero(cell[..., 3] > 128); hs.append(ys.max() - ys.min())
    s = FIG_H / float(np.median(hs))
    for i in range(8):
        r, c = divmod(i, 4); cell = a[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW]
        ys, xs = np.nonzero(cell[..., 3] > 128)
        low = ys.max() - (CH - GY)                          # px below the ground line (near foot hangs lower)
        hx = head_x(cell[..., 3]) - CW / 2                  # head x relative to the body origin
        info.append((low * s, hx * s))
        im = Image.fromarray(cell.astype(np.uint8), "RGBA").resize((round(CW * s), round(CH * s)), Image.LANCZOS)
        fr = Image.new("RGBA", (FW, FH)); fr.paste(im, (round(FW / 2 - CW * s / 2), round(FOOT - (CH - GY) * s)), im)
        frames.append(fr)
    return frames, info
def painted_row(path, info):
    figs = figures(rgba(path), 2, 4)
    crops = [figs[(r, c)] for r in range(2) for c in range(4)]
    s = FIG_H / float(np.median([c.shape[0] for c in crops]))
    frames = []
    for crop, (low, hx) in zip(crops, info):
        im = Image.fromarray(crop.astype(np.uint8), "RGBA")
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        cx = head_x(np.array(im)[..., 3])
        fr = Image.new("RGBA", (FW, FH)); fr.paste(im, (round(FW / 2 + hx - cx), round(FOOT + low - im.height)), im)
        frames.append(fr)
    return frames
def strip(frames):
    s_ = Image.new("RGBA", (FW * len(frames), FH))
    for i, f in enumerate(frames): s_.paste(f, (i * FW, 0))
    return "data:image/webp;base64," + enc(s_, quality=88, method=6)
INFO = {}
out = {"fw": None, "fh": None, "foot": None, "guideSpread": GUIDE, "guides": {}, "sets": []}
for g in ["grey", "color"]:
    fr, INFO[g] = guide_row(NW / f"guide-{g}-NW.png"); out["guides"][g] = {"strip": strip(fr), "n": 8, "raw": raw_thumb(NW / f"guide-{g}-NW.png", 720)}
    print(g, "low/headx per frame:", [(round(a), round(b)) for a, b in INFO[g]])
for prov in ["openai", "google"]:
    for g in ["grey", "color"]:
        key = f"{prov}-{g}"; fr = painted_row(NW / f"{prov}-{g}-NW.png", INFO[g]); n = 8
        out["sets"].append({"key": key, "prov": prov, "guide": g, "strip": strip(fr), "n": n,
                            "raw": raw_thumb(NW / f"{prov}-{g}-NW.png", 720), "flag": CHECK[key], "spread": SPREAD[key]})
        print(key, n)
out.update(fw=FW, fh=FH, foot=FOOT)
DST.write_text("window.NW = " + json.dumps(out) + ";\n"); print(DST.stat().st_size)
