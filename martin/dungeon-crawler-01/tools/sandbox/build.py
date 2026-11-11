#!/usr/bin/env python3
"""Builds the sandbox as a Claude artifact page from the current game (see README, Sandbox).

    python tools/sandbox/build.py <out-dir>

Writes <out-dir>/index.html (index.html without its document wrapper, manifest and touch-icon links, with
sandbox.js inlined in place of the ?sandbox loader and the title "Crypt Music Sandbox"), copies the assets the
page uses into <out-dir>/assets/, and writes <out-dir>/files.json: the published path -> source file map for
the Artifact tool's `files`. Nothing in the game is copied by hand, so a rebuild always matches the game.
"""
import json, os, shutil, sys

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out = os.path.abspath(sys.argv[1])
s = open(os.path.join(GAME, 'index.html'), encoding='utf-8').read()

# the artifact viewer wraps the page in its own document (doctype, html, head with charset and viewport, body)
drop = ['<!DOCTYPE html>\n', '<html lang="en">\n', '<head>\n', '</head>\n', '<body>\n', '</body>\n', '</html>\n',
        '<meta charset="utf-8">\n', '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
        '<link rel="manifest" href="manifest.webmanifest">\n', '<link rel="apple-touch-icon" href="assets/icons/apple-touch-icon.png">\n']
for t in drop:
    assert s.count(t) == 1, 'not found once in index.html: ' + repr(t)
    s = s.replace(t, '')
s = s.replace('<title>Dungeon Crawler</title>', '<title>Crypt Music Sandbox</title>')

# the artifact's address passes no query string: inline sandbox.js in place of the ?sandbox loader
start = s.index('<script>\n// ?sandbox in the address')
end = s.index('</script>', start) + len('</script>')
sandbox = open(os.path.join(GAME, 'sandbox.js'), encoding='utf-8').read()
s = s[:start] + '<script>\n' + sandbox + '</script>' + s[end:]

os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(s)
shutil.rmtree(os.path.join(out, 'assets'), ignore_errors=True)
files = {}
for root, _, names in os.walk(os.path.join(GAME, 'assets')):
    for n in sorted(names):
        rel = os.path.relpath(os.path.join(root, n), GAME).replace(os.sep, '/')
        if rel == 'assets/meta.json' or (rel.startswith('assets/icons/') and rel != 'assets/icons/icon-192.png'):
            continue   # meta.json is inlined in the game as META; only the favicon is used of the icons
        dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(os.path.join(root, n), dst)
        files[rel] = dst
json.dump(files, open(os.path.join(out, 'files.json'), 'w'), indent=1)
print(f'sandbox artifact written to {out} ({len(files)} asset files, {len(s) // 1024} KB page)')
