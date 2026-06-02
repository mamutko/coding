#!/usr/bin/env python3
"""Generate the tile sprites for Society.

Each sprite is a 96x96 RGBA PNG. The central 64x64 "core" maps exactly to a
board tile and is fully opaque. A 16px overhang surrounds the core on every
side; its alpha fades from opaque (at the core edge) to fully transparent (at
the sprite edge). Two neighbouring tiles each overhang 16px toward each other,
so their faded borders overlap across a 32px band and blend together.

Ground textures (ocean / grass / rock) receive the overhang alpha fade.
Features (trees, mountain peaks) are drawn on top at full opacity and may spill
past the core edge into the overhang.

Run with Python 3 and Pillow installed:

    python -m pip install Pillow
    python resources/generate_tiles.py

Output PNGs are written next to this script in the resources folder.
"""

import math
import os
import random
from PIL import Image, ImageDraw

SIZE = 96          # sprite is 96x96
CORE = 64          # opaque core maps to one board tile
OVER = (SIZE - CORE) // 2   # 16px overhang on each side

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------
# Alpha mask: 1.0 across the core, smoothly fading to 0.0 over the overhang.
# ----------------------------------------------------------------------------
def smoothstep(t):
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return t * t * (3 - 2 * t)


def edge_factor(i):
    """0 at the outer sprite edge, easing up to 1 at the core boundary."""
    c = i + 0.5
    if c < OVER:
        return smoothstep(c / OVER)
    if c > SIZE - OVER:
        return smoothstep((SIZE - c) / OVER)
    return 1.0


MASK = [[edge_factor(x) * edge_factor(y) for x in range(SIZE)] for y in range(SIZE)]


def clamp(v):
    return max(0, min(255, int(v)))


# ----------------------------------------------------------------------------
# Ground textures. Each returns an (r, g, b) tuple for pixel (x, y).
# Low-frequency components use periods that divide the core so tiles repeat
# without obvious seams; a little per-pixel jitter adds grain.
# ----------------------------------------------------------------------------
def ocean_px(x, y, rnd):
    base = (24, 90, 150)
    w = math.sin(x / CORE * 2 * math.pi * 2 + math.sin(y / CORE * 2 * math.pi * 2) * 0.9)
    h = 0.5 + 0.5 * w
    foam = max(0.0, w - 0.78) * 3.0
    j = rnd.uniform(-5, 5)
    return (
        clamp(base[0] + 18 * h + 70 * foam + j),
        clamp(base[1] + 24 * h + 60 * foam + j),
        clamp(base[2] + 22 * h + 40 * foam + j),
    )


def grass_px(x, y, rnd):
    base = (84, 146, 64)
    patch = math.sin(x / CORE * 2 * math.pi * 3) * math.sin(y / CORE * 2 * math.pi * 3)
    shade = 12 * patch
    j = rnd.uniform(-11, 11)
    col = (
        clamp(base[0] + shade + j * 0.6),
        clamp(base[1] + shade + j),
        clamp(base[2] + shade * 0.5 + j * 0.4),
    )
    if rnd.random() < 0.03:   # occasional brighter blade fleck
        col = (clamp(col[0] + 25), clamp(col[1] + 30), clamp(col[2] + 15))
    return col


# ----------------------------------------------------------------------------
# Features, drawn on a separate transparent layer at full opacity.
# ----------------------------------------------------------------------------
def draw_tree(d, cx, cy, s, rnd):
    # trunk
    tw = max(2, s * 0.2)
    d.rectangle(
        [cx - tw / 2, cy, cx + tw / 2, cy + s * 0.55],
        fill=(94, 64, 38, 255),
    )
    # canopy: a few overlapping blobs, darker base + lit top-left highlight
    dark = (28, 86, 44, 255)
    mid = (40, 104, 54, 255)
    lite = (74, 140, 80, 255)
    blobs = [
        (0, -s * 0.15, s * 0.62, dark),
        (-s * 0.28, -s * 0.05, s * 0.42, mid),
        (s * 0.26, -s * 0.02, s * 0.40, mid),
        (-s * 0.18, -s * 0.34, s * 0.34, lite),
    ]
    for ox, oy, r, col in blobs:
        bx, by = cx + ox, cy + oy
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=col)


def make_woods_feature(tree_specs):
    def feature(d, rnd):
        for cx, cy, s in tree_specs:
            draw_tree(d, cx, cy, s, rnd)
    return feature


def mountain_feature(d, rnd):
    cx = SIZE / 2
    base_y = 70
    w = 70
    h = 56
    apex = (cx, base_y - h)
    left = (cx - w / 2, base_y)
    right = (cx + w / 2, base_y)
    # lit face
    d.polygon([apex, left, right], fill=(122, 116, 120, 255))
    # shadowed right face
    d.polygon([apex, (cx, base_y), right], fill=(92, 88, 96, 255))
    # snow cap
    sh = h * 0.34
    ratio = sh / h
    sl = (apex[0] - (w / 2) * ratio, apex[1] + sh)
    sr = (apex[0] + (w / 2) * ratio, apex[1] + sh)
    d.polygon([apex, sl, sr], fill=(238, 242, 248, 255))
    # a small secondary crag for variety
    d.polygon([(cx - 26, base_y), (cx - 14, base_y - 24), (cx - 2, base_y)],
              fill=(104, 100, 108, 255))


# ----------------------------------------------------------------------------
# Compose ground + alpha mask + feature layer.
# ----------------------------------------------------------------------------
def build(ground_fn, feature_fn, seed):
    rnd = random.Random(seed)
    pixels = []
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b = ground_fn(x, y, rnd)
            a = int(round(255 * MASK[y][x]))
            pixels.append((r, g, b, a))
    img = Image.new("RGBA", (SIZE, SIZE))
    img.putdata(pixels)

    if feature_fn is not None:
        feat = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(feat, "RGBA")
        feature_fn(draw, random.Random(seed + 1000))
        img = Image.alpha_composite(img, feat)
    return img


def scatter_trees(seed, count, smin, smax):
    rnd = random.Random(seed)
    specs = []
    for _ in range(count):
        cx = rnd.uniform(20, SIZE - 20)
        cy = rnd.uniform(28, SIZE - 22)
        s = rnd.uniform(smin, smax)
        specs.append((cx, cy, s))
    # draw back-to-front so nearer (lower) trees overlap farther ones
    specs.sort(key=lambda t: t[1])
    return specs


def main():
    jobs = [
        ("ocean.png", ocean_px, None, 1),
        ("grassland.png", grass_px, None, 2),
        ("woods-1.png", grass_px, make_woods_feature(scatter_trees(11, 5, 17, 24)), 11),
        ("woods-2.png", grass_px, make_woods_feature(scatter_trees(12, 7, 14, 20)), 12),
        ("woods-3.png", grass_px, make_woods_feature(scatter_trees(13, 4, 20, 27)), 13),
        ("mountains.png", grass_px, mountain_feature, 3),
    ]
    for name, ground, feature, seed in jobs:
        img = build(ground, feature, seed)
        path = os.path.join(OUT_DIR, name)
        img.save(path)
        print("wrote", path)


if __name__ == "__main__":
    main()
