---
name: artifact-sandbox
description: Side-by-side vibe coding — show a project from this repo as a private Claude artifact that is republished after every change, so the user sees it at once instead of waiting for the GitHub Pages deploy, optionally opening on a sandbox of test scenarios (sandbox.js, also reachable on the site with ?sandbox) that drop the user straight into the situation being worked on. Covers the project setup, the shared build script (build.py, here), the edit → build → publish → look → push loop, how to write scenarios, the artifact viewer's limits, and local testing. Use when the user wants to see changes right away or side by side, asks for a sandbox, test scenario or artifact of a project, or a project's README lists a sandbox artifact that a change should update. Worked example: martin/dungeon-crawler-01 (sandbox.js, README "Sandbox").
---

# Artifact sandbox: side-by-side vibe coding

A project in this repo is deployed by GitHub Pages on every push to `main`, which takes a minute or more (and
sometimes times out). For quick iteration, the same project is also published as a **Claude artifact**: a
private page on claude.ai that Claude republishes in seconds, at the same URL, after each change. The user keeps
it open next to the chat and sees every change at once.

On top of that, a project can have a **sandbox**: test scenarios that skip the start screen and drop the user
straight into the situation being worked on (a fight, a boss room, a full inventory, a level-up), with a status
bar for the feature under test and buttons to fast-forward it. The same scenarios run on the deployed site with
`?sandbox` in the address.

There is **one copy of the code**: the artifact is built from the project's own `index.html` (plus
`sandbox.js`) by `build.py` in this skill folder. Nothing is retyped or copied by hand.

Cost: publishing artifacts is free (no API fees); only the session's own work.

## Project setup

```
user/project-NN/
  index.html        the project, unchanged except for the loader below
  sandbox.js        the scenarios (optional)
  assets/           images, sounds, ... (optional; copied into the artifact)
  README.md         a "Sandbox" section with the artifact URL
```

1. **`sandbox.js`** next to `index.html`: one IIFE that runs after the project's script and uses its globals
   (top-level `let`/`const`/`function` of a classic script are global, and a global function declaration can be
   reassigned, which is how a sandbox wraps one). The project itself never uses it.
2. **The loader**, the last thing in `<body>` of `index.html`, between the two markers `build.py` looks for:
   ```html
   <!-- sandbox:start -->
   <script>
   // ?sandbox in the address: load the test scenarios (sandbox.js, see README, Sandbox)
   if (new URLSearchParams(location.search).has('sandbox')) { const sb = document.createElement('script'); sb.src = 'sandbox.js'; document.body.appendChild(sb); }
   </script>
   <!-- sandbox:end -->
   ```
   Without `?sandbox` nothing changes for players. A project without a sandbox needs no markers: its artifact is
   then a plain live preview.
3. **README**: a "Sandbox" section with the artifact URL, the build command (with its options), what each
   scenario sets up, and the rule that the artifact is rebuilt and republished after a change. Add `sandbox.js`
   to the README's file list. (The README rule of `working-with-projects` applies to `sandbox.js` like any code.)

## Build

```bash
python .claude/skills/artifact-sandbox/build.py <project-dir> <out-dir> [--title "Name"] [--skip GLOB ...] [--preview]
```

Put `<out-dir>` in the session's scratchpad (it is build output, never committed). It writes:

- `index.html` — the page to publish. The viewer wraps every page in its own document (doctype, `<html>`, a
  `<head>` with charset and a `viewport-fit=cover` viewport, `<body>`), so the script removes those, plus the
  web-app manifest and apple-touch-icon links; sets `--title`; and replaces the loader block with `sandbox.js`
  inlined, because **the artifact's address carries no query string** (only a plain `#name` hash).
  A project whose `<body>` has attributes must set them from a script instead (the build stops otherwise).
- `assets/...` — copies of the files under `assets/` (or the `--assets` folders), minus `--skip` patterns
  (files the page doesn't load: data already inlined, unused icon sizes).
- `files.json` — published path → source file, the Artifact tool's `files` map (`{}` with no assets).
- `preview.html` (with `--preview`) — the page in a minimal document shell, for a local check (below). It is not
  in `files.json`, so it is never published.

## Publish

First publish (once per project): call the Artifact tool with `file_path: <out-dir>/index.html`, `files` = the
contents of `files.json`, an `icon` (one generic word, e.g. `game`) and a one-sentence `description`. Write the
returned URL into the project README. Keep the `<title>` (`--title`) the same from then on.

Republish (after every change): rebuild, then publish **to the same URL**:

- in the same session: the same `file_path` again (it keeps the URL) — but only while the first publish is still
  in the conversation: after the context was compacted or summarized, a publish without `url` makes a *new*
  artifact, so then treat it as a later session (below). When in doubt, pass `url`;
- in a later session: `action: "read"` on the URL from the README first (a publish to an artifact the session
  hasn't read is refused), then publish with `url` set to it. Without `url` a *new* artifact is created.

`files` adds or replaces the listed files and keeps the others; send `files.json` whole each time (unchanged
files cost little). In a session that didn't publish them (or after a compaction), replacing a published file is refused
until the session has seen it: `action: "list"` with `scope: "files"` on the URL first, then publish. Limits: 16 MB for the page and each text file, 15 MB per binary file, 64 MB and 255 files per
publish (more goes up in several publishes to the same URL). The artifact is **private**: only its owner can
open it unless they share it from the page's Share menu.

## The loop

1. Edit the project (and `sandbox.js` if the change needs a scenario).
2. Build with `--preview` and check it locally (below).
3. **Republish** — before pushing, so the user sees the change at once.
4. The user looks, and comments; repeat.
5. When the change is done: README, version bump and whatever else the project's workflow asks, commit and push
   to `main` (`working-with-projects`). Then the deployed `?sandbox` is current too.

Make the republish part of every change to a project that has a sandbox artifact, the way generated files are
rebuilt: otherwise the artifact silently stays on an old version. Tell the user the artifact was updated.

## Writing scenarios

- **A picker instead of the start screen**: a full-screen overlay with one button per scenario (a bold name
  and one sentence on what it shows), plus **Normal game**, which closes it. Keep a small button on the normal
  start screen that brings the picker back (there is no other way short of reloading). Disable the scenario
  buttons until the project has finished loading (poll a global that start-up sets).
- **A scenario** = build the state, then start. Prefer the project's own functions (new game, build level, make
  monster, give item) over hand-made objects, so the scenario keeps working as the project changes. Make the test
  character strong enough to survive what you throw at it, and put it where the action is (next to the boss room,
  among five pursuers). Clear what would get in the way.
- **Never save test state**: a sandbox shares the browser storage with real saves (on the site even with the
  user's real progress). Mark the test character (e.g. `saveId: 'sandbox'`) and wrap the save function to skip
  it; wrap game-over too, so it returns to the picker.
- **A status bar** for the feature under test: show the state that is otherwise invisible (which track plays and
  why, a timer, a counter), updated a few times a second. Highlight the state the change is about.
- **Fast-forward buttons** for anything slow to reach by playing ("Next loop", "+1 level", "Spawn wave"), and a
  **Scenarios** button that pauses and reopens the picker.
- **One scenario per feature being worked on.** Keep older ones while they still work; adapt or drop them when
  the project changes under them. Describe each in the README's Sandbox section.
- Leave the project's own code alone: a scenario that needs a hook the project lacks is a sign to expose a
  small function in the project (documented in its README), not to copy logic into `sandbox.js`.

## What the artifact viewer allows

The page runs in a locked-down frame (CSP); these hold for every viewer:

- **Network**: `fetch` of the page's own published files by relative URL works (assets, sounds, JSON). Scripts
  load only from cdnjs.cloudflare.com, cdn.jsdelivr.net/npm, unpkg.com, cdn.tailwindcss.com and code.jquery.com,
  pinned to an exact version; stylesheets only from Google Fonts. Everything else is blocked silently — including
  a project's own backend (e.g. Supabase): stub or skip it in the sandbox and say so.
- **Address**: no query string or path reaches the page, only a plain `#name` hash.
- **Not available**: downloads (`<a download>`, blob saves — the publish result warns about them), `alert` /
  `confirm` / `prompt` (return at once), `window.print`, service workers, WebRTC, iframes of other sites, device
  APIs (camera, microphone, location) and Web Share.
- **Works**: canvas, WebAudio (after a click — start sound from a scenario button), `localStorage` (its own,
  per artifact, may throw: wrap in `try`), fullscreen from a click on desktop, keyboard after the user clicks
  into the page (some browser shortcuts, e.g. Ctrl+D, may be taken by the browser).
- The page is shown inside claude.ai, at desktop and phone sizes: the project's own responsive layout applies.

## Testing before publishing

`fetch` doesn't work from `file://`, so serve the build over http and drive `preview.html` with Playwright
(pre-installed in cloud sessions):

```bash
cd <out-dir> && (python3 -m http.server 8766 >/dev/null 2>&1 &) ; sleep 1
node test.js      # page.goto('http://localhost:8766/preview.html'), wait for the scenario buttons, click one, check state
pkill -f "http.server 8766"
```

Check the scenario's state through the project's globals (`page.evaluate`), take one screenshot, and look for
page errors. For audio in headless Chromium, launch with `--autoplay-policy=no-user-gesture-required`. Test the
`?sandbox` route of the project folder the same way, and that the plain page shows no sandbox.

## Worked example: martin/dungeon-crawler-01

- `sandbox.js`: a scenario picker (Pack fight, Pit Demon level, Normal game), a level-12 test hero that is never
  saved (`saveHero` and `showDeath` wrapped), a music status bar, Next loop and Scenarios buttons.
- Build: `python .claude/skills/artifact-sandbox/build.py martin/dungeon-crawler-01 <out-dir> --title "Crypt Music
  Sandbox" --skip assets/meta.json assets/icons/icon-512.png assets/icons/apple-touch-icon.png`
- The README's "Sandbox" section holds the artifact URL and describes the scenarios.
