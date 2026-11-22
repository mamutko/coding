"""Builds the dragon's game art from the paintings in art/characters/dragon/: one atlas, assets/dragon.webp, and its
layout, written into dragon-prototype.html and index.html between the markers `// dragon-art:start` and `// dragon-art:end` (as
`const DRAGON_ART = {...}`) and into assets/dragon.json.     python tools/dragon/build_assets.py

What goes in (all at the game's own scale, 1 atlas px = 1 screen px at zoom 1 and size 1):
- walk: the body with its legs, paint/walk/<DIR>.steady.png for S, SW, W, NW, N (E, NE, SE are drawn mirrored), 8 frames
  each, cut to one box shared by all frames (guide scale 1.4 -> 1); `anchor` is the ground point under the torso
  centre inside a frame; `z` the torso height the guide was drawn at (none: the anchor is on the floor).
- head: paint/head.png (mouth closed) and paint/headopen.png, 8 directions each, one shared box (guide scale 2.4 ->
  1); `anchor` is the head node's ground point, the head drawn at height `z` (72) above it.
- wing: paint/wing.png (the right wing, flat), cut to its guide's bone points plus a margin, at 1/3; `points` are the
  bone points (root, elbow, wrist, 3 finger tips, trailing root) inside that image, for mapping it onto the panels.
- spike, club: the two pieces of paint/bits.png (the dorsal spike, the tail club pointing left).
- scales: a patch of the body's flank (SW walk, frame 0), mirrored 2 x 2 so it tiles: the neck and tail's texture.
"""
import json, os, re
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, '..', '..')
ART = os.path.join(PROJ, 'art', 'characters', 'dragon')
CW, CH = 384, 512
DIRS8 = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE']


def cells(path):
    im = Image.open(path).convert('RGBA')
    return [im.crop(((f % 4) * CW, (f // 4) * CH, (f % 4) * CW + CW, (f // 4) * CH + CH)) for f in range(8)]


def union_box(ims, pad=4):
    solid = [im.getchannel('A').point(lambda v: 255 if v > 16 else 0) for im in ims]   # faint haze doesn't count
    boxes = [m.getbbox() for m in solid if m.getbbox()]
    return (max(0, min(b[0] for b in boxes) - pad), max(0, min(b[1] for b in boxes) - pad),
            min(CW, max(b[2] for b in boxes) + pad), min(CH, max(b[3] for b in boxes) + pad))


def scaled(im, k):
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def main():
    guides = json.load(open(os.path.join(ART, 'guide', 'guides.json')))
    walkg = json.load(open(os.path.join(ART, 'guide', 'walk', 'walk.json')))
    pieces, meta = [], {}

    # the walk: 5 painted directions x 8 frames, one shared box
    walk = {d: cells(os.path.join(ART, 'paint', 'walk', d + '.steady.png')) for d in ['S', 'SW', 'W', 'NW', 'N']}
    box = union_box([c for cs in walk.values() for c in cs])
    k = 1 / walkg['scale']
    ax, ay = walkg['anchor']['S'][0]   # every frame's anchor is the same point of its cell
    ax, ay = ax % CW, ay % CH
    meta['walk'] = {'w': round((box[2] - box[0]) * k), 'h': round((box[3] - box[1]) * k), 'anchor': [round((ax - box[0]) * k, 1), round((ay - box[1]) * k, 1)],
                    'fpt': walkg['fpt'], 'frames': 8, 'dirs': {}}
    for d, cs in walk.items():
        meta['walk']['dirs'][d] = [None] * 8
        for f, c in enumerate(cs): pieces.append((('walk', d, f), scaled(c.crop(box), k)))

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

    # the scales: a flank patch, mirrored 2 x 2 so it tiles
    p = Image.open(os.path.join(ART, 'paint', 'walk', 'SW.png')).convert('RGBA').crop((192, 176, 256, 224))
    tile = Image.new('RGBA', (p.width * 2, p.height * 2))
    tile.paste(p, (0, 0)); tile.paste(ImageOps.mirror(p), (p.width, 0)); tile.paste(ImageOps.flip(p), (0, p.height)); tile.paste(ImageOps.flip(ImageOps.mirror(p)), (p.width, p.height))
    tile = scaled(tile, 0.75)
    pieces.append((('scales',), tile)); meta['scales'] = {'w': tile.width, 'h': tile.height}

    # pack: shelves, tallest first
    W, x, y, sh, rects = 2048, 0, 0, 0, {}
    for key, im in sorted(pieces, key=lambda t: -t[1].height):
        if x + im.width > W: x, y, sh = 0, y + sh + 2, 0
        rects[key] = (x, y, im.width, im.height); x += im.width + 2; sh = max(sh, im.height)
    atlas = Image.new('RGBA', (W, y + sh))
    for key, im in pieces: atlas.paste(im, rects[key][:2])
    for (kind, *rest), r in rects.items():
        r = list(r)
        if kind == 'walk': meta['walk']['dirs'].setdefault(rest[0], [None] * 8); meta['walk']['dirs'][rest[0]][rest[1]] = r
        elif kind == 'head': meta['head'][rest[0]].extend([None] * (8 - len(meta['head'][rest[0]]))); meta['head'][rest[0]][rest[1]] = r
        else: meta[kind]['rect'] = r
    atlas.save(os.path.join(PROJ, 'assets', 'dragon.webp'), quality=88, method=6)
    js = json.dumps(meta, separators=(',', ':'))
    open(os.path.join(PROJ, 'assets', 'dragon.json'), 'w').write(json.dumps(meta, indent=1))
    for name in ('dragon-prototype.html', 'index.html'):   # the prototype and the game
        page = os.path.join(PROJ, name); s = open(page).read()
        if 'dragon-art:start' not in s: raise SystemExit('no dragon-art markers in ' + name)
        s = re.sub(r'// dragon-art:start\n.*?// dragon-art:end', lambda m: '// dragon-art:start\nconst DRAGON_ART = ' + js + ';\n// dragon-art:end', s, flags=re.S)
        open(page, 'w').write(s)
    print('assets/dragon.webp', atlas.size, os.path.getsize(os.path.join(PROJ, 'assets', 'dragon.webp')) // 1024, 'KB')


if __name__ == '__main__':
    main()
