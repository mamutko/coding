#!/usr/bin/env python3
"""Builds a project's Claude artifact (its live preview / sandbox) from the project's own files.

    python .claude/skills/artifact-sandbox/build.py <project-dir> <out-dir>
        [--title "Name"] [--page index.html] [--sandbox sandbox.js]
        [--assets assets ...] [--skip GLOB ...] [--preview]

What it writes into <out-dir> (see SKILL.md):
  index.html   the page, ready to publish: the document wrapper the artifact viewer adds itself (doctype, <html>,
               <head>, <body>, charset and viewport metas) and the links the viewer can't use (web app manifest,
               apple-touch-icon) are removed; the <title> is replaced when --title is given; and the block between
               <!-- sandbox:start --> and <!-- sandbox:end --> (the ?sandbox loader) is replaced by the sandbox
               script inlined, because the artifact's address carries no query string. No markers: no sandbox.
  assets/...   copies of every file under the --assets folders (default: assets, if it exists), minus --skip
  files.json   published path -> absolute source path, for the Artifact tool's `files` ({} when there are none)
  preview.html (--preview only) index.html inside a minimal document shell, the way the viewer shows it, for a
               local headless-browser check over http. It is not published (not in files.json).

Nothing of the project is edited or copied by hand, so a rebuild always matches the project.
"""
import argparse, fnmatch, json, os, re, shutil, sys

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('project'); ap.add_argument('out')
ap.add_argument('--title', help='replace the page <title> (keep it stable across republishes)')
ap.add_argument('--page', default='index.html'); ap.add_argument('--sandbox', default='sandbox.js')
ap.add_argument('--assets', nargs='*', default=None, help='asset folders, relative to the project (default: assets)')
ap.add_argument('--skip', nargs='*', default=[], help='glob patterns of asset paths to leave out, e.g. assets/meta.json')
ap.add_argument('--preview', action='store_true', help='also write preview.html for a local check')
a = ap.parse_args()

proj, out = os.path.abspath(a.project), os.path.abspath(a.out)
s = open(os.path.join(proj, a.page), encoding='utf-8').read()

# the viewer wraps the page in its own document with a charset and a viewport-fit=cover viewport
for pat in [r'<!DOCTYPE[^>]*>\s*', r'<html[^>]*>\s*', r'</html>\s*', r'<head>\s*', r'</head>\s*', r'<body[^>]*>\s*', r'</body>\s*',
            r'<meta charset[^>]*>\s*', r'<meta name="viewport"[^>]*>\s*', r'<link rel="manifest"[^>]*>\s*', r'<link rel="apple-touch-icon"[^>]*>\s*']:
    s = re.sub(pat, '', s, flags=re.I)
if '<body ' in s.lower():
    sys.exit('the page has <body> attributes: move them into a script (the viewer supplies <body>)')
if a.title:
    s, n = re.subn(r'<title>.*?</title>', '<title>' + a.title + '</title>', s, count=1, flags=re.S)
    if not n: s = '<title>' + a.title + '</title>\n' + s
if not re.search(r'<title>', s[:8192]): print('warning: no <title> in the first 8 KB (the viewer only looks there)')

m = re.search(r'<!-- sandbox:start -->.*?<!-- sandbox:end -->', s, flags=re.S)
if m:
    sb = open(os.path.join(proj, a.sandbox), encoding='utf-8').read()
    s = s[:m.start()] + '<script>\n' + sb.replace('</script', '<\\/script') + '</script>' + s[m.end():]
else:
    print('no <!-- sandbox:start --> ... <!-- sandbox:end --> markers: building the page without a sandbox')

os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(s)

files = {}
dirs = a.assets if a.assets is not None else (['assets'] if os.path.isdir(os.path.join(proj, 'assets')) else [])
for d in dirs:
    shutil.rmtree(os.path.join(out, d), ignore_errors=True)
    for root, _, names in os.walk(os.path.join(proj, d)):
        for n in sorted(names):
            rel = os.path.relpath(os.path.join(root, n), proj).replace(os.sep, '/')
            if any(fnmatch.fnmatch(rel, g) for g in a.skip): continue
            dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, n), dst); files[rel] = dst
json.dump(files, open(os.path.join(out, 'files.json'), 'w'), indent=1)

if a.preview:
    open(os.path.join(out, 'preview.html'), 'w', encoding='utf-8').write(
        '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, '
        'initial-scale=1, viewport-fit=cover"></head><body>' + s + '</body></html>')

big = [f for f in files if os.path.getsize(files[f]) > 15 * 2**20]
total = sum(os.path.getsize(f) for f in files.values())
print(f'{out}/index.html: {len(s) // 1024} KB page, {len(files)} asset files ({total / 2**20:.1f} MB)'
      + (', sandbox inlined' if m else '') + (', preview.html written' if a.preview else ''))
if big: print('warning: over the 15 MB per-file limit:', big)
if total > 64 * 2**20: print('warning: over 64 MB: publish the files in several calls to the same URL')
