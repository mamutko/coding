"""Builds the dragon's game art from the paintings in art/characters/dragon/: one atlas, assets/dragon.webp, and its
layout, written into index.html between the markers `// dragon-art:start` and `// dragon-art:end` (as
`const DRAGON_ART = {...}`) and into assets/dragon.json.     python tools/dragon/build_assets.py

What goes in (all at the game's own scale, 1 atlas px = 1 screen px at zoom 1 and size 1):
- body: the body without its lower legs, paint/body16.cut.png and paint/body32.cut.png (tools/dragon/cut_body.py): 17
  painted directions of 32, headings PI/4 + i * PI/16 for i = 0 (S) ... 16 (N) (body16 has the even i, body32 the odd;
  i = 17 ... 31 are i = 32 - i mirrored), cut to one shared box (guide scale 1.3 -> 1); `anchor` is the ground point
  under the torso centre, the torso drawn at its standing height.
- limbs: the four leg bones of paint/limbs.png (front upper, front lower, hind upper, hind lower), upright, each cut to its
  content (scale 7 -> 1), with `top` and `bottom`, its two joints, inside the piece; `len` the bone's length (px).
- foot: paint/feet.png, 8 directions (S, SW ... SE, the way the body faces), one shared box (scale 5.95 -> 1); `anchor` is
  the ankle's ground point, `ankle` the height (px) where the lower bone meets it.
- head: paint/head.png (mouth closed) and paint/headopen.png, 8 directions each, one shared box (guide scale 2.4 ->
  1); `anchor` is the head node's ground point, the head drawn at height `z` (72) above it.
- wing: paint/wing.png (the right wing, flat), cut to its guide's bone points plus a margin, at 1/3; `points` are the
  bone points (root, elbow, wrist, 3 finger tips, trailing root) inside that image, for mapping it onto the panels.
- spike, club: the two pieces of paint/bits.png (the dorsal spike, the tail club pointing left).
- scales: paint/scales.tile.png (the body's scales painted flat and made to tile, tools/dragon/scale_tile.py), 8 scales
  across at 13 px each (as big as the body painting's), stored at 2x (`res`): the neck and tail's texture.
- tone: the body views, the leg bones, the feet and the scales are brought to one colour: the hide's pixels (luminance
  under 130; the pale bone of spikes and claws, over 180, is left as it is, blended between) get the per-channel mean
  and spread of all the body views' hide together (two passes, since the hide pixels change), so the body keeps its
  shade as it turns and the parts match it; the scales, painted flat, get the mean and 0.6 of the spread.
"""
import json, os, re
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, '..', '..')
ART = os.path.join(PROJ, 'art', 'characters', 'dragon')
CW, CH = 384, 512
DIRS8 = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE']


def cells(path):
    im = Image.open(path).convert('RGBA')
    return [im.crop(((f % 4) * CW, (f // 4) * CH, (f % 4) * CW + CW, (f // 4) * CH + CH)) for f in range(8)]


def solid_box(im, pad=4):
    b = im.getchannel('A').point(lambda v: 255 if v > 16 else 0).getbbox()   # faint haze doesn't count
    return (max(0, b[0] - pad), max(0, b[1] - pad), min(im.width, b[2] + pad), min(im.height, b[3] + pad))


def union_box(ims, pad=4, w=CW, h=CH):
    solid = [im.getchannel('A').point(lambda v: 255 if v > 16 else 0) for im in ims]   # faint haze doesn't count
    boxes = [m.getbbox() for m in solid if m.getbbox()]
    return (max(0, min(b[0] for b in boxes) - pad), max(0, min(b[1] for b in boxes) - pad),
            min(w, max(b[2] for b in boxes) + pad), min(h, max(b[3] for b in boxes) + pad))


SCALES = {'n': 8, 'px': 13, 'sd': 0.6}
HIDE = (130, 180)   # luminance: below the first, scaled hide; above the second, bone (spikes, claws), left alone


def hide_px(im):
    a = np.asarray(im).astype(np.float32); px = a[..., :3][a[..., 3] > 200]
    return px[px.mean(1) < HIDE[0]]


def tone(im, mu, sd):
    """The piece's hide brought to the target colour statistics (per channel mean and spread, the same for every body
    view and part), so the body doesn't change shade as it turns and the legs, feet, neck and tail match it."""
    a = np.asarray(im).astype(np.float32); h = hide_px(im)
    m0, s0 = h.mean(0), h.std(0) + 1e-3
    rgb = a[..., :3]; L = rgb.mean(2, keepdims=True)
    w = np.clip((HIDE[1] - L) / (HIDE[1] - HIDE[0]), 0, 1)
    a[..., :3] = rgb + w * ((rgb - m0) * (sd / s0) + mu - rgb)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def scaled(im, k):
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def main():
    guides = json.load(open(os.path.join(ART, 'guide', 'guides.json')))
    pieces, meta = [], {}

    # the body: 17 painted directions of 32 (0 = S ... 16 = N; the other 15 mirrored), legs cut off, one shared box:
    # body16 has the even ones, body32 the odd ones between them
    b16 = json.load(open(os.path.join(ART, 'guide', 'body16.json')))
    bm = b16['body']; bw, bh = bm['cell']
    body = [None] * 17
    for name in ('body16', 'body32'):
        dirs = json.load(open(os.path.join(ART, 'guide', name + '.json')))['body']['dirs']
        im = Image.open(os.path.join(ART, 'paint', name + '.cut.png')).convert('RGBA')
        for i, di in enumerate(dirs): body[di] = im.crop(((i % 3) * bw, (i // 3) * bh, (i % 3) * bw + bw, (i // 3) * bh + bh))
    box = union_box(body, w=bw, h=bh)
    k = 1 / bm['scale']
    ax, ay = bm['anchor'][0]; ax, ay = ax % bw, ay % bh   # the same point of every cell
    meta['body'] = {'w': round((box[2] - box[0]) * k), 'h': round((box[3] - box[1]) * k), 'anchor': [round((ax - box[0]) * k, 1), round((ay - box[1]) * k, 1)],
                    'dirs': 32, 'rects': [None] * 17}
    for i, c in enumerate(body): pieces.append((('body', i), scaled(c.crop(box), k)))

    # the leg bones, upright, top joint up: each cut to its content, with its two joints inside the piece
    lm = b16['limbs']; k = 1 / lm['scale']
    im = Image.open(os.path.join(ART, 'paint', 'limbs.png')).convert('RGBA')
    meta['limbs'] = []
    for j, pc in enumerate(lm['pieces']):
        col = im.crop((j * 384, 0, j * 384 + 384, 1024)); bb = solid_box(col)
        meta['limbs'].append({'name': pc['name'], 'len': pc['len'], 'top': [round((pc['top'][0] - j * 384 - bb[0]) * k, 1), round((pc['top'][1] - bb[1]) * k, 1)],
                              'bottom': [round((pc['bottom'][0] - j * 384 - bb[0]) * k, 1), round((pc['bottom'][1] - bb[1]) * k, 1)]})
        pieces.append((('limb', j), scaled(col.crop(bb), k)))

    # the feet: 8 directions, one shared box; anchor = the ankle's ground point
    fm = b16['feet']; k = 1 / fm['scale']
    feet = cells(os.path.join(ART, 'paint', 'feet.png'))
    box = union_box(feet)
    ax, ay = fm['anchor'][0]; ax, ay = ax % CW, ay % CH
    meta['foot'] = {'w': round((box[2] - box[0]) * k), 'h': round((box[3] - box[1]) * k), 'anchor': [round((ax - box[0]) * k, 1), round((ay - box[1]) * k, 1)],
                    'ankle': fm['ankle'], 'rects': [None] * 8}
    for i, c in enumerate(feet): pieces.append((('foot', i), scaled(c.crop(box), k)))

    # the head, mouth closed and open: 8 directions each, one shared box
    heads = {'closed': cells(os.path.join(ART, 'paint', 'head.png')), 'open': cells(os.path.join(ART, 'paint', 'headopen.png'))}
    box = union_box(heads['closed'] + heads['open'])
    hp = guides['parts']['head']; k = 1 / hp['scale']
    meta['head'] = {'w': round((box[2] - box[0]) * k), 'h': round((box[3] - box[1]) * k), 'z': 72, 'anchor': [], 'closed': [], 'open': []}
    for i in range(8):
        ax, ay = hp['anchor'][i]; ax, ay = ax - (i % 4) * CW, ay - (i // 4) * CH
        meta['head']['anchor'].append([round((ax - box[0]) * k, 1), round((ay - box[1]) * k, 1)])
    for st, cs in heads.items():
        for i, c in enumerate(cs): pieces.append((('head', st, i), scaled(c.crop(box), k)))

    # the wing, flat, with its bone points
    wg = json.load(open(os.path.join(ART, 'guide', 'wing.json')))
    xs = [p[0] for p in wg['points']]; ys = [p[1] for p in wg['points']]
    box = (max(0, int(min(xs)) - 40), max(0, int(min(ys)) - 40), min(1536, int(max(xs)) + 60), min(1024, int(max(ys)) + 40))
    k = 1 / 3
    wing = scaled(Image.open(os.path.join(ART, 'paint', 'wing.png')).convert('RGBA').crop(box), k)
    meta['wing'] = {'points': [[round((x - box[0]) * k, 1), round((y - box[1]) * k, 1)] for x, y in wg['points']], 'panels': wg['panels']}
    pieces.append((('wing',), wing))

    # the spike and the club: the two halves of bits.png, each cut to its content
    bits = Image.open(os.path.join(ART, 'paint', 'bits.png')).convert('RGBA')
    spike = bits.crop((0, 0, 768, 1024)); spike = spike.crop(spike.getbbox())
    club = bits.crop((768, 0, 1536, 1024)); club = club.crop(club.getbbox())
    spike = scaled(spike, 70 / spike.height); club = scaled(club, 90 / club.height)
    pieces.append((('spike',), spike)); pieces.append((('club',), club))
    meta['spike'] = {'w': spike.width, 'h': spike.height}
    meta['club'] = {'w': club.width, 'h': club.height, 'note': 'points left; the tail joins at the right edge'}

    # the scales: the flat painted texture, tiling (tools/dragon/scale_tile.py), at 2x the game's scale: SCALES.n scales
    # across of SCALES.px each, as big as the body painting's
    t = Image.open(os.path.join(ART, 'paint', 'scales.tile.png')).convert('RGBA')
    tile = t.resize((SCALES['n'] * SCALES['px'] * 2,) * 2, Image.LANCZOS)
    pieces.append((('scales',), tile)); meta['scales'] = {'w': tile.width, 'h': tile.height, 'res': 2}

    # one shade: every body view, leg bone, foot and the neck and tail's scales to the body views' pooled statistics
    pool = np.concatenate([hide_px(im) for key, im in pieces if key[0] == 'body'])
    mu, sd = pool.mean(0), pool.std(0)
    pieces = [(key, tone(tone(im, mu, sd), mu, sd) if key[0] in ('body', 'limb', 'foot') else im) for key, im in pieces]
    # the scales are painted flat (the game shades the neck and tail), so they get the mean but only SCALES.sd of the spread
    pieces = [(key, tone(tone(im, mu, sd * SCALES['sd']), mu, sd * SCALES['sd']) if key[0] == 'scales' else im) for key, im in pieces]
    meta['tone'] = {'mean': [round(float(v), 1) for v in mu], 'sd': [round(float(v), 1) for v in sd]}

    # pack: shelves, tallest first
    W, x, y, sh, rects = 2048, 0, 0, 0, {}
    for key, im in sorted(pieces, key=lambda t: -t[1].height):
        if x + im.width > W: x, y, sh = 0, y + sh + 2, 0
        rects[key] = (x, y, im.width, im.height); x += im.width + 2; sh = max(sh, im.height)
    atlas = Image.new('RGBA', (W, y + sh))
    for key, im in pieces: atlas.paste(im, rects[key][:2])
    for (kind, *rest), r in rects.items():
        r = list(r)
        if kind == 'body': meta['body']['rects'][rest[0]] = r
        elif kind == 'limb': meta['limbs'][rest[0]]['rect'] = r
        elif kind == 'foot': meta['foot']['rects'][rest[0]] = r
        elif kind == 'head': meta['head'][rest[0]].extend([None] * (8 - len(meta['head'][rest[0]]))); meta['head'][rest[0]][rest[1]] = r
        else: meta[kind]['rect'] = r
    atlas.save(os.path.join(PROJ, 'assets', 'dragon.webp'), quality=88, method=6)
    js = json.dumps(meta, separators=(',', ':'))
    open(os.path.join(PROJ, 'assets', 'dragon.json'), 'w').write(json.dumps(meta, indent=1))
    for name in ('index.html',):
        page = os.path.join(PROJ, name); s = open(page).read()
        if 'dragon-art:start' not in s: raise SystemExit('no dragon-art markers in ' + name)
        s = re.sub(r'// dragon-art:start\n.*?// dragon-art:end', lambda m: '// dragon-art:start\nconst DRAGON_ART = ' + js + ';\n// dragon-art:end', s, flags=re.S)
        open(page, 'w').write(s)
    print('assets/dragon.webp', atlas.size, os.path.getsize(os.path.join(PROJ, 'assets', 'dragon.webp')) // 1024, 'KB')


if __name__ == '__main__':
    main()
