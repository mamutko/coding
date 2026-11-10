"""Make the home-screen icons from the hero sprite (front-facing idle frame on a dark crimson glow).

Usage:  python tools/make_icons.py      (run from the game folder; needs Pillow + NumPy)

Writes assets/icons/icon-192.png, icon-512.png (web app manifest, also used as maskable: the hero stays inside
the central safe zone) and apple-touch-icon.png (180 x 180, for iPhone / iPad "Add to Home Screen").
"""
import pathlib, json
import numpy as np
from PIL import Image, ImageFilter

GAME = pathlib.Path(__file__).parent.parent
OUT = GAME / "assets" / "icons"


def icon(size):
    meta = json.loads((GAME / "assets" / "meta.json").read_text())["characters"]["hero"]
    fw, fh, col = meta["fw"], meta["fh"], meta["idle"]
    sheet = Image.open(GAME / "assets" / "hero.webp").convert("RGBA")
    hero = sheet.crop((col * fw, 0, (col + 1) * fw, fh))            # row 0: facing the viewer
    hero = hero.crop(hero.getbbox())
    S = 1024                                                          # draw big, then shrink
    y, x = np.mgrid[0:S, 0:S] / S - 0.5
    r = np.sqrt(x * x + (y + 0.05) ** 2) / 0.7
    t = np.clip(1 - r, 0, 1)[..., None]
    bg = (np.array([8, 3, 5]) * (1 - t) + np.array([92, 18, 16]) * t).astype(np.uint8)
    im = Image.fromarray(bg, "RGB").convert("RGBA")
    h = int(S * 0.70); w = round(hero.width * h / hero.height)
    hero = hero.resize((w, h), Image.LANCZOS)
    glow = Image.new("RGBA", (S, S)); px, py = (S - w) // 2, int(S * 0.15)
    glow.paste(Image.new("RGBA", (w, h), (0, 0, 0, 255)), (px, py), hero)
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(18)))
    im.paste(hero, (px, py), hero)
    return im.convert("RGB").resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, size in (("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)):
        icon(size).save(OUT / name, optimize=True)
    print("icons written to", OUT)
