# Dungeon Crawler 01 — "Crypt of Endless Night"

An isometric, gothic dungeon crawler in a single `index.html` (vanilla JavaScript, HTML5 canvas, no build step).
A lone knight descends an endless crypt, fighting monsters that grow stronger on every level, collecting
and equipping gear, and levelling up. All art is AI-generated (see [Assets](#assets)).

## Files

| Path | Purpose |
|---|---|
| `index.html` | The whole game: markup, CSS, and JavaScript. Asset metadata (`META`) is inlined so the page also works from `file://`. |
| `assets/hero.webp`, `skeleton.webp`, `ghoul.webp`, `keeper1.webp`–`keeper4.webp` | 8-direction × 8-frame walk cycles (transparent): the hero, two monsters and the four Keepers of the Crypt. |
| `assets/hero2.webp`, `assets/mannequin.webp` | The hero's other two looks (see [Hero looks](#hero-looks)): 8-direction × 12-frame walk cycles, 144 × 152 frames like `hero.webp`. Built by the `sprite-animation` skill's `build_sheet.py` from `art/characters/hero-2/` and `art/characters/mannequin/`; loaded only when a hero uses them. |
| `assets/hunter.webp`, `huntress.webp`, `girl.webp`, `boy.webp`, `duke.webp`, `princess.webp`, `smithess.webp`, `sorcerer.webp` | The cast: 8-direction × 8-frame walk cycles of villagers and nobles not yet in the game, shown only in the sandbox's character viewer (loaded on demand). See [Walk cycles](#walk-cycles-hero-skeleton-ghoul). |
| `art/characters/hero/` | A first attempt at repainting the hero with the `sprite-animation` skill's workflow: `character.json` (design, decisions, spend, board URL), `source-knight.png` (front / side / back frames cut from the current sprite, the input for the references), `reference-1..3.png` (turnaround candidates; 2 approved, copied to `reference.png`), `paint/<DIR>.png` (12-frame walk per direction, all 8 painted) and `paint/attempts/` (rejected tries). `board.html` is the generated review page (not committed). |
| `art/characters/hero-2/` | Source art of the **stocky knight** look (`assets/hero2.webp`), made with the `sprite-animation` skill; nothing here is loaded by the game. `character.json` (design, decisions, per-direction notes, spend, board URL), `reference/` (`reference.png` = the approved turnaround; `round-1/` and `round-2/` = all candidates), `guide/<DIR>.png` + `.json` (the stocky mocap guide and its sidecar: grid, ground line, stride, feet), `paint/<DIR>.png` + `<DIR>.prompt.txt` (the painted 12-frame walk per direction and its exact prompt), `paint/attempts/` (rejected tries with their prompts). `board.html` is the generated review page (not committed). |
| `art/characters/mannequin/` | `character.json` for the **mannequin** look (`assets/mannequin.webp`): `"from_guide": true`, so the build uses the skill's standard 12-frame walk guide itself as the frames. |
| `art/characters/hero-3/` | Source art of a third hero look in the making, a **huntress** (no bow in hand), with the `sprite-animation` skill; laid out like `hero-2/`. So far `reference/round-1/` (three turnaround candidates and their prompts, `designs.json`) and `character.json`. Not in the game yet. |
| `art/characters/hero/3d/` | The hero as a 3D model instead of AI-painted frames: `build_knight.py` generates a skinned knight on the `sprite-animation` skill's Quaternius UAL1 mannequin skeleton (plate fitted to the mannequin by ray casts; procedural helm, pauldrons, belt, tassets, mail skirt and cape; EU 43 feet like the guides) and writes `knight.glb` (skeleton, all 43 mocap clips, three extra `cape_*` bones; `render_guide.py`'s `Rig` loads it too) plus `knight.txt` (the same, gzip + base64, for the viewer; not committed). `index.html` is the viewer, published as an [Artifact](https://claude.ai/artifact/626EuKeoCVR5LeKRMRfbuR): orbit, clip picker, the 8 game camera angles (orthographic, 30°), an in-game-size preview and a cape that swings clear of the legs and arms. Test shots: `index.html?dir=NW&t=0.25&clip=Walk_Loop`. |
| `tools/raw/cast_design1.png`, `cast_design2.png` | The cast's front-view design sheets (4 × 1 each, on magenta). |
| `assets/spider.webp`, `wraith.webp`, `demon.webp` | 8-direction × 4-frame monster sprite sheets (transparent). |
| `assets/items.webp` | 6 × 8 atlas of 96 px item icons (`ATLAS_W` × `ATLAS_H`; rows 1–4 from `process_art.py`, rows 5–8 from `add_items.py`). |
| `assets/props.webp` | Props: row 1 has the chest, open chest, door, stairs, brazier, bones, urn and gold, and the boss-room furnishings (throne, altar, candelabrum, skull pile, banner, pillar, sarcophagus), from `process_art.py`; row 2 has the searched bones (`bonesused`) and the door leaves (`doorA`, `doorB`), from `add_props.py`; rows 3 on have the four Keepers of the Crypt (`keeper1`–`keeper4`) and their stall's furnishings (`mtable`, `mrack`, `mchest`, `mshelf`, `mcrates`, `mbarrel`, `mlantern`, `mrug`), from `add_market.py`. |
| `assets/floor.jpg`, `assets/wall.jpg` | 512 px seamless floor and wall textures. |
| `assets/grass_a.jpg`, `assets/grass_b.jpg` | 512 px seamless grass textures of the surface (lush dark green; patchy olive meadow). See [The surface](#the-surface-depth-0). |
| `assets/surface.webp` | The surface's sprites: four trees (oak, fir, dead tree, birch; each with its crown cut), four bushes, four ground details (flowers, rocks, mushrooms, a grass tuft) and the crypt. Coordinates in `META.surface`. |
| `tools/add_surface.py`, `tools/raw/grass_a.png`, `grass_b.png`, `trees.png`, `bushes.png`, `crypt.png` | Builds the two grass textures and `assets/surface.webp` from the raw AI images, and writes `META.surface` into `assets/meta.json` and the inline `META`. |
| `assets/unused/` | AI images made but not used by the game, kept for later: `keepers-creepy.png` (the first, rejected Keepers of the Crypt). The five unused fire bomb designs are in `assets/items.webp` (`firebomb2`–`firebomb6`) and `tools/raw/firebombs.png`. Not loaded, and left out of the sandbox artifact. |
| `assets/dirt.jpg` | 512 px seamless dirt texture for wall tops and wall faces toward solid ground (from `add_props.py`). |
| `assets/meta.json` | Frame sizes and atlas coordinates written by the processing script (copied into `META` in `index.html`). |
| `tools/process_art.py` | Turns the raw AI images for the 4-frame monsters, items, props and textures into the files above (chroma-key, slicing, packing). Imports `walk_cycle.py`. |
| `tools/stride_check.py` | Checks an AI walk-cycle image against its pose guide, frame by frame (foot spread in the side views, which foot is lower in the front and back views), and marks frames that copy the other half of the stride. See [Walk cycles](#walk-cycles-hero-skeleton-ghoul). |
| `tools/walk_cycle.py` | Walk-cycle pipeline (hero, skeleton, ghoul): renders the 3D stick-figure pose guides and placeholders, and builds the 8-frame sheets. |
| `tools/add_items.py`, `tools/raw/items2.png`, `items3.png`, `firebombs.png` | Appends the icons of the newer item types (and a quiver), and the six fire bomb designs, to `assets/items.webp` from the three raw sheets, and updates `assets/meta.json` and the inline `META`. See [Assets](#assets). |
| `tools/add_market.py`, `tools/raw/keepers.png`, `keeper_decor.png` | Adds the Keepers of the Crypt and their furnishings to `assets/props.webp` (the rows after row 2) and updates `assets/meta.json` and the inline `META`. See [Keepers of the Crypt](#keepers-of-the-crypt-the-market). |
| `tools/add_props.py`, `tools/raw/bones_searched.png`, `doors.png`, `dirt_b.png` | Adds row 2 of `assets/props.webp` (searched bones, door leaves) and makes `assets/dirt.jpg` seamless; updates `assets/meta.json` and the inline `META`. |
| `tools/cut_sfx.py`, `tools/raw/sfx/` | Cuts the AI-voiced ghoul takes into the clips in `assets/sfx/`. |
| `assets/sfx/` | Ghoul moans and grunts (MP3). |
| `assets/music/explore-instrumental.mp3`, `combat-instrumental.mp3`, `explore.mp3`, `combat.mp3`, `surface-1.mp3`, `surface-2.mp3` | The music: exploration and combat loops, each instrumental and with a Latin choir, and two cheerful instrumental surface tracks. See [Music](#music). |
| `tools/raw/<char>_walk_<DIR>.png` | The raw AI walk-cycle images (`hero`, `skeleton`, `ghoul`, `keeper1`–`keeper4` and the cast × `S`, `SW`, `W`, `NW`, `N`) the 8-frame sheets are built from. |
| `lake-prototype.html` | A standalone prototype of underground lakes (not loaded by the game, which now has lakes: see [Lakes](#lakes)): still water set a few pixels below the floor, a mirrored reflection of the walls, props and characters, rock banks on the far shores, and ripples from drips. A panel compares the options (tile or rounded shore, ripple rings or refraction, water colour, depth, reflection strength). Published as a separate Claude artifact by the artifact-sandbox `build.py` with `--page lake-prototype.html --skip 'assets/*' --inline` (the seven images it uses). |
| `sandbox.js` | Test scenarios, loaded with `?sandbox` and inlined into the Claude artifact: see [Sandbox](#sandbox). |
| `catalog.html` | Monster and item catalog (bestiary, armory, potions, affixes, rarity, and what first appears at each depth), with sprites from `assets/`. **Generated** by `tools/catalog/build.js`: see [Catalog](#catalog). |
| `tools/catalog/` | `build.js` (reads the game's data in a headless browser and writes `catalog.html`) and `template.html` (the catalog page, edit this one). |
| `tools/simulation/` | Balance simulation: `simulate.js` runs simulated heroes through the real game and reports how hero and monsters compare per depth. How to use it: [`tools/simulation/README.md`](tools/simulation/README.md); dated results with conclusions: `results-YYYY-MM-DD.md`. |
| `manifest.webmanifest`, `assets/icons/`, `tools/make_icons.py` | Web app manifest and home-screen icons (made from the hero sprite by `make_icons.py`): see [Home screen app](#home-screen-app). |
| `todo.md` | Numbered list of ideas for future work (not yet implemented). |
| `versions.md` | What each version added, newest first, and how to get any version back from git history: see [Version](#version). |
| `backup/index.NN.html` | Old snapshots of `index.html`, numbered `01`, `02`, … in the order they were made; not used by the game and not described by this README. `index.01.html` is an early version of the game; `index.02.html` is v20, the last version before game time followed real time (see [Main loop](#main-loop)), kept to compare performance; it has a `<base href="../">` so it loads `assets/` from the game folder. |

## Sandbox

Test scenarios that drop a strong test hero straight into a situation being worked on, without playing up to
it. They live in `sandbox.js`, apart from the game; the game itself never uses them.

- **On the site:** `index.html?sandbox` (GitHub Pages:
  `https://mamutko.github.io/coding/martin/dungeon-crawler-01/?sandbox`). A small script at the end of
  `index.html`, between `<!-- sandbox:start -->` and `<!-- sandbox:end -->`, loads `sandbox.js` only when the
  address has `?sandbox`; without it nothing changes. The title screen's **Scenarios** button (bottom left) goes
  there: it reloads the page with `?sandbox`, or, when the sandbox is already loaded (`window.sandboxOpen`, set
  by `sandbox.js`), just opens the picker.
- **As a Claude artifact** (shows a change at once, without waiting for the Pages deploy):
  https://claude.ai/artifact/T9nJm2WxgZYWtneTWFVqHa (private to its owner). It is built from the current
  `index.html` and `sandbox.js` by the repo's shared script (see the `artifact-sandbox` skill, which also covers
  publishing and testing):
  `python .claude/skills/artifact-sandbox/build.py martin/dungeon-crawler-01 <out-dir> --title "Crypt Music Sandbox" --skip assets/meta.json assets/icons/icon-512.png assets/icons/apple-touch-icon.png 'assets/unused/*' --inline 'assets/*.webp' 'assets/*.jpg'`.
  It removes the document wrapper (the viewer adds its own) and the manifest and touch-icon links, inlines
  `sandbox.js` in place of the loader block (the artifact's address carries no query string), embeds the 26
  images (`assets/*.webp`, `*.jpg`, the cast's included) in the page as data URIs (about 7.6 MB; the claude.ai app on a phone failed
  to load them as separate files, every one and every retry), copies the other assets (sounds and music, minus
  `meta.json`, inlined as `META`, and the unused icon sizes) and writes `files.json` for publishing; the
  artifact is then republished to the same URL. Nothing is copied by hand, so a rebuild always matches the
  game; **after a change to the game the artifact is rebuilt and republished**, or it keeps the older version.

`sandbox.js` runs after the game's script and uses its globals. Instead of the title screen it shows a
**scenario picker**; a scenario makes a test hero (`saveId` `'sandbox'`: level 12, +35 STR, +25 DEX, +45 VIT,
a rare long sword, rare chain mail, a magic iron helm, 12 health potions) at a chosen depth. The test hero is
**never saved** (`saveHero` is wrapped; the saves share the browser storage with real heroes), and when it dies
the picker comes back instead of the title screen (`showDeath` is wrapped). **Normal game** closes the picker
and leaves the usual title screen, whose **Scenarios** button at its bottom left brings the picker back.

The scenario buttons (all but **Normal game**) stay off until the game's own start-up is done: all images
loaded (`LOADED` counts them) and a first level built. Until then the picker says `Loading the game: n / 18
images…` (with how many loads were retried, if any); if an image fails to load or start-up throws, it shows that message instead (the same text the title
screen's start button shows, which the picker covers) and the scenarios stay off; for a failed image it also
fetches the file once and adds what the server answered (an HTTP status, or the fetch error). Errors thrown later
(`error` and `unhandledrejection` events) are listed there too, the last three.

The picker (*Crypt Sandbox*) groups the scenarios:

- **Characters:**
  - **Character viewer** (depth 3, regenerated until it has a big room): the test hero stands in the middle of the
    big room, and every monster of the level is removed. A **Look** list in the bar holds every sheet in
    `META.characters` by name, in groups: Hero, Monsters (five), Keepers of the Crypt (four) and Villagers and
    nobles (the cast: hunter, huntress, village girl and boy, duke, princess, female blacksmith, sorcerer). A cast
    sheet loads when first picked (`loadCast`; until then the hero keeps its own look);
    the hero takes the picked look (`G.hero.look`, see [Rendering](#rendering)) and walks as that character. The
    bar shows the name, the frames per direction, the row (direction) and frame being drawn (or "idle") and the
    scale, and the walking speed in tiles per second. A **Speed** list sets that speed as a fraction of the hero's own
    (`G.hero.speedMul`: 0.05×, 0.1×, 0.15×, 0.25×, 0.35×, 0.5×, 0.75×, normal, 1.5×); the walk frames advance with the
    distance walked, so a slow walk steps through every frame (at 0.05× a stride takes about 8 s). On narrow screens, where the bar normally sits low above the HUD, this scenario keeps it at the top of
    the screen (over the HUD's top row), so it never covers the character. **Normal game** puts the hero's own look back.
- **Surface:**
  - **The surface** (depth 0): a new level-1 hero (never saved) a few steps from the crypt's entrance. The bar shows
    the world tile and super tile the hero is on, then the level's name once below, and the music track and play
    number. **Next loop** starts the next play at once (the other surface track).
- **Fire bombs** (the hero's longsword goes to the pack on key 1; the bombs are equipped, on key 2):
  - **Fire bombs: pack fight** (depth 3, 15 bombs): monsters within 18 tiles are removed, and four skeletons and
    three ghouls (no champions) are placed 5–8 tiles away in sight, already pursuing.
  - **Fire bombs: the last two** (depth 3, 2 bombs, three skeletons as above): shows running out and the bare
    hands until the longsword is equipped.
  - **Fire bombs: practice yard** (depth 2, 30 bombs): monsters within 22 tiles are removed, and three skeletons
    sleep 4–6.5 tiles away. Their calm never ends, so they ignore the hero until a hit or a burn wakes them. Two
    small stacks of bombs (2 and 3) lie at the hero's feet, to pick up.
- **Market:**
  - **Keeper of the Crypt** (depth 6, regenerated until it has a keeper): the test hero stands about two tiles from
    the keeper. It has 3000 gold, 60 % life (to try healing), and in the pack a common Iron Helm and Battle Axe, a
    magic Ruby Ring and 3 fire bombs, besides the bow and 12 health potions. Monsters within 16 tiles are removed.
- **Kiting:**
  - **Kiting with a bow** (depth 7, regenerated until the level has a big room): the test hero holds a common
    Hunting Bow (about 3 arrows per spider and 15 per Pit Demon there; the longsword in the pack, key 1).
    - **The room** is the level's big room, grown to 1.5× its area (`enlargeRoom`, sandbox only):
      - its sides grow by √1.5 around its centre (from 16–20 to about 20–24 tiles), kept inside the map;
      - everything in the new rectangle becomes floor: walls, doors (their door objects are removed) and any
        rooms or corridors it overlaps open up, while other props stay;
      - the floor's new edge gets walls, as `buildLevel` makes them.
    - The hero stands on the floor tile nearest its middle. Its monsters, and all others within 22 tiles, are
      removed.
    - Four cave spiders and two Pit Demons (no champions) are placed in the room at least 5 tiles from the hero,
      asleep: their calm never ends, so only a hit wakes one. Until then they wander slowly.
    - Shows the draw time and the charge, with room to run.
- **Lakes:**
  - **The underground lake** (depth 8, `LAKE_AT`, which always has the lake room): the hero stands on the dry
    shore where it faces the middle of the lake (the dry tile one step back from the water nearest the room's
    diagonal), facing the water, with 15 fire bombs in the pack on key 4 (the longsword stays equipped). Monsters
    within 14 tiles that aren't the lake's wraiths are removed. The bar
    shows the wraiths left, how many pursue, the nearest one's distance, whether ripple refraction is on (or off:
    under 28 fps) and the frame rate. Two pickers switch the lake sounds for the page's session: **Drip** (*Plink*,
    *Hollow*, *Glassy*, *Echo*) and **Bomb splash** (*Plunge*, *Heavy*, *Gurgle*); a click picks one and plays it.
    **Normal game** puts both back to the first.
- **Music:**
  - **Pack fight** (depth 3): monsters within 18 tiles are removed, and five skeletons (no champions) are placed
    3.5–6.5 tiles from the hero, already pursuing. Shows the combat music starting, ending at once when the last
    is killed, and holding 6 s when they lose interest.
  - **Pit Demon level** (depth 8, regenerated until the boss is a Pit Demon): the hero starts on the nearest floor
    tile 3–5 tiles outside the boss room's edge; other monsters within 10 tiles that aren't the boss room's are
    removed. Shows the choir plays and the boss-room track.

A status bar at the top (above the bottom HUD on narrow screens) shows what the scenario is about.

- **In the fire bomb scenarios** it shows:
  - the bombs carried, or what the hero holds instead (bare hands, the longsword);
  - how many fires burn;
  - "you are burning", with the seconds left (or "in the fire"), while the hero burns;
  - how many monsters are burning.

  It also has **Fire look** buttons (*Blaze*, *Ember bed*, *Oil pool*) that switch the fire's look for the next
  fires (see [Fire bombs](#fire-bombs)).
- **In the market scenario** it shows the keeper's name, the hero's gold and life, and "trading" while the market is
  open. **Keeper** buttons (*Aldric*, *Borin*, *Mirela*, *Old* Tobias) switch the keeper's look and name.
- **In the kiting scenario** it shows the weapon and its draw time, "drawing" while the hero draws, the
  distance to the nearest pursuer, and which monsters are charging.
- **In the music scenarios** it shows the music: mood, instrumental or choir (gold), play number, how many
  monsters pursue, the hold countdown and whether it is a Pit Demon level. **Next loop** (music and surface scenarios)
  starts the next play of the current track at once (to reach plays 2, 5 and 9 quickly).

**Scenarios** (always in the bar) pauses the game and shows the picker again.

## Version

`VERSION` (an integer near the top of the script) is shown at the bottom right of the title screen as `v<N>`
(16 px, a little muted; double-click it, or long-press it on a touch screen, to open the
[debug overlay](#debug-overlay)).
**Increment it before every push**, so a player can tell whether the page they have open is up to date.

Every version is recorded in [`versions.md`](versions.md) (the `version-tracking` skill): a bullet list of what
it added, with small follow-up changes merged into one entry (e.g. *v38–v40*), the commit of each entry, and
the git commands to go back to any version.

## Home screen app

**Full screen in the browser:** `F5`, or the **Full screen** button at the top right of the title screen,
toggles the browser's full-screen mode (Fullscreen API, with the `webkit` prefixed calls for older Safari;
`FS` in the code). The button is shown only where the browser supports it (desktop browsers, Android, iPad) and
not when the game already runs as a full-screen app; it reads **Exit full screen** while full screen is on
(Esc also leaves it). The iPhone has no full-screen mode for web pages: there the home-screen app below is the
way to hide the browser bars.

The game can be installed as a home-screen app, which then opens **without browser bars**:

- **iPhone / iPad:** in Safari, Share → **Add to Home Screen**. The `apple-mobile-web-app-*` meta tags make the
  icon open the game full screen (iOS has no full-screen mode for web pages in the browser itself). The status
  bar stays visible in portrait (style `black`, so nothing of the game is drawn under it); iOS hides it in
  landscape.
- **Android** (Chrome and others): menu → **Add to Home screen** / **Install app**. `manifest.webmanifest`
  asks for `"display": "fullscreen"`, so no status or navigation bar either.
- The manifest names the app *Crypt of Endless Night* (short name *Crypt*), with a near-black background and theme
  colour and the icons in `assets/icons/` (192 and 512 px, also usable as maskable; `apple-touch-icon.png`,
  180 px, for iOS). They show the hero facing the viewer on a dark crimson glow, made by
  `python tools/make_icons.py` from `assets/hero.webp`.
- The screen can be turned either way (no orientation lock): the game's layout handles portrait and landscape.
- There is no service worker, so the app still loads from the web (no offline play). Saved heroes live in the
  app's own storage: on iOS a home-screen app does **not** share `localStorage` with Safari, so heroes saved in
  the browser don't appear in the app, and the other way round.

## Catalog

`catalog.html` is a stand-alone page listing every monster (with its stats at any depth, via a slider), the champion
and boss multipliers, every item type, the potions, the affixes with their ranges, the rarity rules, and a
**depth by depth** table of what first appears where. It uses the game's sprites and floor texture and states the
game version it was built from.

It is generated from the game's own data, so **regenerate it whenever stats change or monsters, items, affixes or
potions are added** (and after bumping `VERSION`):

```
node tools/catalog/build.js
```

The script (Node.js + Playwright, like the simulation) opens `index.html` in headless Chromium, reads `MON`, `TIER`,
`BASES`, `AFFIX`, `POTIONS` and the depth rules, computes each monster's stats per depth with `makeMonster`, and
writes them into `tools/catalog/template.html`, saving the result as `catalog.html`. Change the page's look in the
template, never in `catalog.html`.

## Controls

| Input | Action |
|---|---|
| Left click on floor | Walk there (A* pathfinding). Holding the button keeps walking toward the cursor. |
| Left click on chest / door / urn / bones / gold / item / stairs | Walk to it and act on it: open, break, search, pick up, or descend. |
| Left click on a Keeper of the Crypt | Walk up to it and open the market (see [Keepers of the Crypt](#keepers-of-the-crypt-the-market)); `Esc`, ✕ or walking away closes it. |
| Double click / double tap on an item on the floor | Walk to it, pick it up and equip it at once; what it replaces goes into the pack slot it took. Needs a free pack slot, unless the item's equipment slot is empty (then it goes straight on). Potions are just picked up. |
| Right click, or `Shift` + left click, or a tap while a finger rests on the attack button (touch) | Attack with the equipped weapon (see [Combat](#combat)). Hold to keep attacking. With fire bombs equipped: throw one at the monster or the spot (see [Fire bombs](#fire-bombs)). |
| `I`, `C` or `Tab` | Toggle the equipment overlay (`Esc` closes it). |
| `1`–`9`, `0` | Quick keys: equip the bound weapon or use the bound potion (both are queued; see [Actions](#actions)). |
| `Q`, or a click / tap on the life orb | Drink a health potion (queued like a quick key). |
| `M` | Toggle the minimap. |
| `N` | Toggle sound (effects and music). |
| `F5` (or the title screen's **Full screen** button) | Toggle full screen, where the browser supports it (see [Home screen app](#home-screen-app)). F5 no longer reloads the page. |
| `Ctrl` + `D` (touch: hold the minimap and the life orb together; title screen: double-click or long-press the version) | Toggle the debug overlay (see [Debug overlay](#debug-overlay)). |
| Mouse wheel, or pinch with two fingers (touch) | Zoom (0.6×–1.5×). |

**Touchpads and touch screens.** A *modifier* turns any left click or tap into a right click, everywhere a
right click does something: attacking in the game view, dropping a pack item and clearing a quick key in the
equipment overlay. The modifier is the `Shift` key, or, on a touch screen, a finger resting on the **attack button** (its rim glows
gold while it is held). The game view and the button use pointer events (mouse, touchpad, touch and pen alike) with
`touch-action: none`, so a finger held on the screen keeps walking or attacking and dragging doesn't scroll
or zoom the page. A long press never opens iOS's "save image" / link menu: the page sets
`-webkit-touch-callout: none` (inherited everywhere), and the attack button cancels the default action of its
`touchstart` (a non-passive listener), so holding it alone for auto attack doesn't pop the menu up on iOS
(Safari, and Edge / Chrome on iOS, which use WebKit). Pointer events still arrive.

**HUD taps.** The HUD hotbar keys and the life orb act on a touch's `touchstart` (a non-passive listener; one
call per new finger on the element) instead of on `click`: iOS often fires no click for a second finger while
another one rests on the attack button, so drinking a potion during auto attack would fail. Cancelling the
`touchstart` also cancels the click that would follow (no double use), and the attack
button modifier does not apply there: a tap on a hotbar key while attacking uses the key (only `Shift` + click
or a right-click clears a HUD key).

- Each press remembers its `pointerId` (and, for a mouse, which button), so with several fingers down,
  lifting one never ends another's press: lifting the attack-button finger doesn't stop a walk or an attack already
  under way, and a press that started as a right click stays one until it is released.
- **Auto attack:** while the attack button is held with a melee weapon (and no finger is walking or attacking
  on the game view), the hero attacks the nearest monster within reach (`reach × 0.85`, as for a targeted
  attack) at once, with no tap on it, and keeps attacking (when it dies or steps out of reach, the next nearest
  in reach) until the button is released. It never walks toward a monster. With a bow it does nothing; tap a
  monster as before.
- **Pinch zoom:** touch pointers on the game view are tracked. When a second finger touches it, a pinch
  starts: the first finger's walk or attack is cancelled, and the zoom becomes the zoom at the start × the
  current finger distance ÷ the starting distance (clamped to 0.6×–1.5×). Until every finger on the game view
  is lifted, no finger there walks or attacks. A finger on the attack button is not on the game view, so it
  never starts a pinch.
- A second mouse button pressed or released while another is held arrives as a `pointermove` with
  `e.button` set (a "chorded" press), so the game treats those as presses and releases too. Holding left to
  walk and then holding right attacks, as before.

The title screen lists the controls and is also the hero picker (see [Saving](#saving)). The surface (depth 0)
is rendered behind it. The start button is enabled once all images have loaded (`loadAll`). An image that fails
to load is tried again up to 4 times (`IMG_RETRIES`), after 1, 2, 3 and 4 s, since a phone's connection can drop
a single request; if it still fails, or start-up throws, it shows *Failed to load …* or *Start-up failed: …* instead (also logged to the console). At its bottom left a
**Scenarios** button opens the test scenarios (see [Sandbox](#sandbox)); at its bottom right the version number
opens the debug overlay (see [Version](#version)).

## Saving

Progress is saved in the browser's `localStorage` under one key, `crypt-of-endless-night.save`:
`{ v: 1, last: <id of the hero played last>, heroes: { <id>: entry } }`, where an entry is
`{ id, name, depth, lvl, saved: <timestamp>, hero: { name, lvl, xp, base, equip, inv, gold, hotkeys, kills, hp, look } }`
(`look`: see [Hero looks](#hero-looks); missing in older saves, which means the original knight).
Items are plain data, so the hero's equipment, pack (potion stacks included) and quick keys are stored as they are.
**Older saves** kept health potions as a counter (`hero.potions`) and a `{ type: 'potion' }` quick key; on loading,
the counter becomes a health potion stack in the first free pack cell (if the pack is full, the stack is dropped
on the floor at the start of the level), with an id after the highest saved one, and the key becomes a
`{ type: 'use', pot: 'health' }` key. Items from before regeneration was removed lose their life regen bonus,
and an old *Bone Talisman* gets the current crit bonus instead (`3 × (1 + 0.1·(item level − 1))`, rounded; items from before fixed item stats carry an `ilvl`).
The iron skin effect is not saved. Every read and write
is wrapped in `try`; if storage is unavailable the game still plays, logs that progress could not be saved,
and the picker shows no saved heroes.

- **When it saves:** when a hero is created (at depth 0, the surface), and automatically on arrival at each new depth
  (after the descend XP; the log says "Progress saved."). Nothing else is saved: not the level layout, and
  nothing gained or lost partway through a level.
- **Hero picker** (the title screen): one box per saved hero, most recently saved first, showing name, level
  and depth, then a **New Hero** box. The hero played last (or the newest) is selected at start; the selected
  box is lit (gold border and glow, brighter background, a filled gold diamond), the others are dimmed with an
  empty diamond. Clicking a box only selects it; only the **Enter the Crypt** button starts the game.
  - **New Hero** turns into a name field with a **Create** button in the same box (Enter also works; Escape
    goes back when there are other heroes). Names are up to 20 characters, spaces collapsed; an empty name is
    refused with a red border. Creating saves the new hero (level 1, depth 1, starting kit) and selects it, and
    a fresh **New Hero** box appears below. With no saved heroes, the name field is shown straight away.
  - **The cogwheel** next to Enter the Crypt opens a box for the selected hero: rename it (**Rename** or
    Enter), export it, pick its **Look** (Knight, Stocky knight, Mannequin; the lit one is current; a click saves
    it at once, see [Hero looks](#hero-looks)), or **Erase hero**, which asks for confirmation ("… will be erased for good. This cannot be
    undone.") before deleting the save.
  - **Long lists:** the title screen scrolls, and the Enter the Crypt / cogwheel row sticks to the bottom edge,
    so it can always be reached, on wide and tall screens alike. On narrow screens a hero's details go under
    its name; on short screens the title and the controls text get smaller.
  - **Resuming** generates a *new* layout for the saved depth and restores the saved hero with the life it had
    when saved (capped at max life; saves made before life was saved start at full life). Item
    ids continue after the highest saved one, so new drops never clash with owned items.
- **Export / import** (`exportHero`, `importHero`):
  - **Export hero** in the cogwheel box saves the selected hero to a text file,
    `<name>-level<L>-depth<D>.crypt-hero.json`, as last saved (on arrival at its depth). It is a download; on
    iPhone / iPad (where downloads from a home-screen app are unreliable) it goes through the share sheet
    (*Save to Files*, AirDrop, mail, …) when the browser can share files.
  - The file is JSON:
    `{ "format": "crypt-of-endless-night-hero", "formatVersion": 1, "gameVersion": <VERSION>, "exported": <ISO date>,
    "hero": { "name", "depth", "lvl", "saved", "data": { the saved hero fields } } }`. `formatVersion`
    (`HERO_FILE_VERSION`) is the version of this layout: a layout change bumps it and adds a step to
    `upgradeHeroFile`, which brings older files up to date. `gameVersion` is only for information. The hero data
    itself goes through `migrateHero` on load like any save, so items in an old format keep working.
  - **Import Hero…** (a dashed box under **New Hero**) opens a file picker. The file is checked: valid JSON, the
    right `format`, a `formatVersion` this game knows (a newer one asks to update the game first), and the
    needed fields (name, depth, level, attributes, equipment, pack). An imported hero always gets a new id, so it
    never overwrites a hero (importing the same file twice gives two copies). It is selected, and a box says
    "<name> (level L, depth D) has joined your heroes." Problems are reported in the same box, and nothing is
    changed.
- **Death:** the scene keeps running for 4 s (`DEATH_DELAY`): the hero fades and sinks like a slain monster,
  enemy projectiles vanish, and every monster drops its chase and goes back to wandering (it can't notice the
  dead hero). Then the title screen returns with the fallen hero selected and a message
  ("<name> was slain at depth N … What was gained on this level is lost; <name> rises again at the start of
  depth M."). Starting again reloads the hero as saved on arrival at that depth, so the level's gold, items,
  XP, kills and potions are lost, and the layout is new.
- The equipment overlay's title shows the hero's name.

## Rendering

- **Isometric projection.** Tiles are 96 × 48 px diamonds. A world point `(x, y)` (in tile units) maps to screen
  `((x − y)·48, (x + y)·24)`. The camera follows the hero smoothly (25 % lerp per frame) and keeps them centred,
  with the view aimed 46 px above the feet. It snaps when the hero teleports (new level). The canvas renders at
  device-pixel ratio (max 2), lowered automatically on slow devices (see [Main loop](#main-loop)).
- **Floor.** Every visible floor and doorway tile is added to one path in iso-transformed space
  (`transform(48, 24, −48, 24)`). It is filled with the floor texture pattern, which spans 3 tiles, and faint
  seams are stroked.
- **Walls** are full-height blocks, 72 px tall (`WALLH`), south walls included, so the south and east walls of a
  room hide the floor right behind them (see Level generation for how props stay in view). Only the two faces
  facing the viewer (+y and +x) are drawn, and only where the neighbour on that side isn't a wall. A face that
  looks into a room or corridor (floor, open door or doorway in front of it, `roomSide`) shows the stone wall
  texture; a face toward solid ground (void) shows the **dirt** texture (`assets/dirt.jpg`). Faces are
  affine-mapped 128 × 75 cells of the texture, picked per tile so the pattern varies. The left face is shaded
  42 %, the right 18 % (`SHADE_Y`, `SHADE_X`). The top of every wall is dirt too, drawn in iso-transformed space
  like the floor (the pattern spans 1.5 tiles), darkened 25 %, with a faint edge line.
- **Doors** are wooden leaves with no frame, threshold or lintel, `DOOR_T` (0.09 tiles) thick: a full tile wide
  and as tall as the walls, so the knight fits through. Each door picks its look when the level is built: `doorA`
  (strap hinges and a ring) 75 % of the time, `doorB` (cross brace and barred grate) otherwise. A closed door
  stands on its doorway tile's room-side edge (`front`: the room is on the +y / +x side). An open one has swung
  90° into the corridor about the hinge on the side the camera sees (`x` for a door in a wall along x, `y` for
  one in a wall along y) and lies along that side of the doorway, leaving the whole tile open. Its top edge, and
  its free end when that faces the camera, show a hand-drawn wood strip (`doorEdge`: browns with grain lines,
  plank joints and wear, made once on a canvas). Depth keys: closed `x + y + 1.4` (front) or `+ 0.6` (back),
  open `+ 0.5`.
- **Searched bones** are drawn with their own sprite (`bonesused`): the same bones scattered flatter and wider.
- **Depth sorting.** Walls, doors, props, monsters, the hero and projectiles are sorted by `x + y`. A wall or prop on
  tile `(tx, ty)` uses `tx + ty + 1`; entities use their foot position. Stairs, bones, gold and floor items
  are drawn flat right after the floor.
- **Fog / exploration.** Tiles within ~6.8 tiles of the hero become "seen". Unseen tiles more than ~13 tiles
  away are not drawn.
- **Lighting.** An offscreen canvas is filled with 93 % near-black. Elliptical radial "holes" are then cut
  into it (`destination-out`): a 7.2-tile radius around the hero, about 4.2 tiles of flickering light per
  brazier, and a small glow per wraith bolt. The result is drawn over the scene, then each brazier adds a warm
  orange glow (`lighter`; green for a green brazier); candelabra light a 2.6-tile radius and the boss room's
  rune circle, faintly (strength 0.4), a 3-tile radius. Item labels, monster health bars and floating damage numbers are drawn after the
  lighting so they stay readable.
- **Characters.** Each sheet has 8 rows, one per direction, in the order S, SW, W, NW, N, NE, E, SE. The
  facing row comes from the movement or attack direction projected to screen space and rounded to 45°
  sectors. `META.characters.<name>` gives the frame size `fw × fh`, the frame count, an optional idle frame
  (default 0), an optional `footY`, the ground point's y inside the frame (default `fh − 6`), and `fpt`, walk
  frames per tile (default 2). The sprite is drawn horizontally centred with `footY` on the entity's position,
  scaled by the monster's `scale`. Characters have a soft shadow (see Prop shadows),
  sized per type (`CHAR_SHADOW`: half-width × half-height, opacity, softness, centre offset, in px × scale):
  hero and most monsters 32 × 15 at 55 % black, 2 px below the ground point; the wide-bodied spider 66 × 30 at
  60 %, extra soft (70 % shade reached at 0.3 of the radius instead of 0.55), 28 px above it; the demon 42 × 19
  at 60 %, 14 px above it. Those two sheets stand above their ground point, so their shadows move up under the
  body.
  - **The hero's look** (`heroLook`): normally its own sheet; the sandbox's character viewer can give it any sheet
    in `META.characters` (`G.hero.look`). It is then drawn at that character's scale (`lookScale`: a monster's
    `scale`, a keeper's `KEEPER.scale`, else 1), with its shadow, hovering like a wraith if it is one, its walk
    frames advancing by that sheet's `fpt`, and the same in a lake's reflection.
  - **Walk frames advance with distance walked**, `anim += distance × fpt / scale` (the hero's scale is 1), so
    feet don't slide at any move speed and bigger monsters take longer strides.
  - **Hero, skeleton, ghoul:** 8 frames per direction = one full stride (two steps): 0 left foot forward,
    1 down, 2 passing, 3 up, 4 right foot forward, 5 down, 6 passing, 7 up. `fpt` is 5 (a stride every 1.6
    tiles; the ghoul's shorter lurching stride uses 5.5). Idle uses frame 3. `footY` is 128 in a 152 px frame
    (ghoul: 138 in 162 px, as its hunched back views stand taller), because the foot nearer the camera hangs
    below the ground point in this view.
  - **Spider, wraith, demon:** 4 frames per direction, `fpt` 2, frame 0 is idle; `footY` 128 in a 152 px frame.
    The wraith hovers and bobs. Attacks show a short
  lunge toward the facing direction. A hit flashes the sprite white (`filter: brightness`), champions get
  a red glow and bosses a green glow (`drop-shadow`). Dead monsters sink and fade over about 1 s.
- **Prop shadows** are soft-edged ellipses (a radial gradient from 50 % black to transparent) under each prop's
  base, by shape. The sprite's bottom is the prop's front-most ground point, so: **boxes** (chest, sarcophagus,
  altar, throne) centre the shadow `w/4` above it (the middle of a `w`-wide base diamond), radii 0.62w × 0.32w;
  **mounds** (skull pile, bones) 0.2w above, 0.58w × 0.28w; **tripods** (brazier) 0.2w above (between the feet),
  0.44w × 0.2w and darker (75 %); **posts** (candelabrum, banner, pillar, urn) 0.08w above, 0.46w × 0.21w. Stairs and gold have none. A prop with `flip` (a throne on the right back
  wall) is drawn mirrored.
- **Green brazier** (see Dungeon generation): drawn with `hue-rotate(80deg) saturate(1.4)`, with green embers.
- **Rune circle** in the boss room: drawn on the floor, centred on the room, radius 0.24 × the room's shorter
  side. Static (no animation): a very faint green radial glow out to 1.45 × the radius, then two thin
  concentric rings, 24 rune ticks between them (every third one longer) and three arcs inside, in a muted green
  (40 % opacity), heavily blurred (`blur(3px)` plus a 26 px green shadow blur), all additive (`lighter`).
  **Drawn once, then pasted:** `bakeRuneCircle` draws it into an offscreen canvas per boss room and screen scale
  (zoom × render scale, rounded to 0.25; `RUNE_CACHE`), and each frame `drawRuneCircle` pastes that image only
  while it is on screen. Until v83 it was drawn live every frame, on screen or not; when the browser draws
  without the GPU (Chrome can fall back to that until it is restarted), the blur and shadow cost ~800 ms a frame:
  1 fps on every level with a boss room (from depth 5), while levels without one ran normally.
- **Effects.** Melee swings draw a sweeping crescent arc in the attack direction. Arrows are drawn as shafts with
  a tip, and wraith bolts as glowing green orbs. Hits spray blood-coloured sparks (green for wraiths), urns
  burst into shards, and level-ups emit an expanding golden ring. While a potion is being used, its icon (30 px, tinted
  like its stack) rises 18 px above the hero's head and fades out over the 0.4 s; iron skin gives the hero a
  steel-blue glow (`drop-shadow`).
- **Sprite effects without canvas filters.** The effects above (hit flash, hover brightening, champion / boss /
  iron skin / guardian's chest glows, potion tints, the green brazier, grey banners) are canvas filters (`ctx.filter`), which
  WebKit lacks: Safari, and every browser on iOS (Edge and Chrome there too). `drawSprite` draws each sprite
  with its filter where `ctx.filter` exists (`CANVAS_FILTER`), and otherwise imitates each effect: a glow
  becomes a canvas shadow (`shadowBlur` = 2 × the drop-shadow's blur), brightening extra copies of the sprite
  drawn with `lighter` (alpha = the brightness above 1), and a hue tint a cached copy of the sprite recoloured
  with the `color` blend (potions in their colour, the green brazier green, the big room's banners grey). The rune circle's `blur(3px)` has
  no fallback (its 26 px shadow blur still softens it).
- **Hover.** Monsters, items and interactable objects register screen-space hit boxes every frame. Monsters
  take priority over everything else. A hovered thing is brightened, objects show a name label, and the
  cursor becomes a crosshair over monsters or a pointer over interactables.
- **Minimap** (top right, toggled with `M`). An isometric overview of explored tiles, centred on the hero,
  redrawn 4× per second. Walls are tan, doors brown, floor dark, water dark blue, the stairs gold, and the hero red.

## Lakes

Still, dark, mirror-like underground water (`T_WATER`), so far only in the lake room (see
[Dungeon generation](#dungeon-generation)). The settings are `LAKE`: the water lies `drop` 8 px below the floor,
reflects at 70 % (`refl`), and a reflection fades by 45 % (`fade`) over 120 px of height (`fadeH`). Its colour is
*ink* (`WATER_LOOKS.ink`: deep `#030407`, tint `rgba(4,8,14,0.42)`); two more looks are kept for future lakes,
*teal* and *moss*. The way it is drawn was tried out first in the standalone `lake-prototype.html` (see Files).

- **The outline** (`lakeGeom`, once per level, `map.lake`): the water tiles' boundary edges, chained into loops,
  each edge marked when a wall is beyond it; then rounded by three rounds of Chaikin corner cutting (cuts at ¼ and
  ¾ of every edge), except edges along walls, which stay straight (the wall stands in the water). It is kept as
  a `Path2D` in screen (iso) coordinates and as segments, each `far` (the dry floor beyond it is farther from the
  camera: its outward normal has `nx + ny < 0`) or `near`. `inLake(x, y)` tests a world point against it.
- **Order of drawing** (in `render`, before the floor; the depth-sorted list is built first). The visible part
  (`lakeView`): water tiles and tiles next to water (a rounded shore reaches into them) that are seen or near the
  hero, as a path of their diamonds, with the range of `x + y` they cover. Everything of the water is clipped to
  the outline moved down by `drop`, and to that path.
  1. **The reflection** (`drawLake`, into its own canvas at half the resolution, which softens it on every browser,
     WebKit included): the walls, props and characters of the depth-sorted list whose reflection can reach the
     visible water (`x + y` from 10 below to 1 above its range) are drawn again as mirror images about the water
     plane: a point `h` px above the floor at screen y appears at `y + h + 2·drop`. For it `ctx` is switched to that
     canvas and `MIR` is set: `face` then mirrors a wall face (wall tops are not drawn); a sprite (`mirSprite`,
     via `mirrorProp`, `mirrorChar`) is first faded with height on a scratch canvas (`destination-out` gradient),
     then flipped about its ground point (a flipped prop also horizontally). Projectiles are mirrored too (`mirrorProj`): an arrow
     or a wraith bolt at its flight height of 44 px, a fire bomb at its arc's height (upside down, its rag's flame
     pointing down), each faded with height like the sprites (alpha `1 − fade · min(1, h / fadeH)`); a bolt's light
     is mirrored with the other lights. **Fire** is mirrored too: a fire's flames, smoke and sparks
     (`mirrorFirePart`, at 85 %; flames burning on the water are drawn at its level, so the same mirror line
     serves both) and the flames on a burning creature (with its mirror image). Flat props (stairs, bones, gold,
     rug) and doors have no reflection; dead monsters fade in it as they do above.
  2. **The water layer** (its own canvas, then drawn onto the scene): the deep colour; the lake bed (the floor
     texture) showing through near the shore, as three wide strokes along the outline (46, 28 and 12 px at 12, 16
     and 20 %), 5 px lower; the reflection at 70 %; the tint; a soft dark shadow (7 px) under the near shore's lip;
     at the foot of the far shores a dark contact line (3 px) and a faint light meniscus line; then the ripples.
  3. **The floor** is drawn on dry tiles and on the water tiles too (a rounded shore leaves dry corners on them),
     clipped to everything outside the outline (even-odd), with damp stone along the shore (two dark strokes, 12
     and 5 px, 22 %). The near shore's lip gets a faint light line.
  4. **Rock banks** (`drawBanks`): on the far shores the water's 8 px drop shows as a strip of rock (the wall
     texture, darkened by the direction it faces like a wall face, and 25 % for the wet), and its mirror image
     right under it. Walls standing in the water reach down to it (`face` from `-drop`, the wet part darker),
     and their reflections start there.
  5. **The lights** are mirrored too: after the usual lighting holes (see Rendering), every light is cut again,
     clipped to the visible water, at its mirror point (`lift → −(lift + 2·drop)`), 85 % as wide and 84 % as
     strong, so a light lights its own reflection. Then, additively, the braziers' and candelabra's flames leave
     long vertical streaks of glow on the water (green for a green brazier), flickering, and a burning fire a wider,
     warm one (radius `60 + 25 · r` px, stronger while it burns).
  - **No shadows** are drawn on water (a hovering wraith, a pillar in the lake).
- **Drips** (`updateLake`): on average 12 a minute (`LAKE.drips`, exponential gaps) a drop falls on a random point
  of the lake within 10 tiles of the hero that has been seen: a bright streak accelerating down from 320 px for
  0.55 s, then a splash (`splash`): a ripple, a smaller one 0.28 s later (the rebound droplet falling back, 45 %),
  6 droplets thrown up, and the `drip` sound. They are drawn after the lighting, additively, so they catch the eye
  in the dark.
- **Ripples** grow at 24 px/s (`rspeed`) and last 3.8 s (`rlife`), their strength rising over 0.08 s and then
  falling as `(1 − t / life)^1.6`. Two kinds, both on:
  - **Rings:** up to three ellipses 7.5 px apart (`lambda`), half as tall as wide (they lie on the water), each a
    light line (the look's `ring` colour) with a dark one 1.5 px below it.
  - **Refraction** (`refract`): for each ripple, the pixels of the water layer in the box around it
    (`getImageData` / `putImageData`) are displaced radially by a short wave packet (a sine of wavelength 7.5 px
    under a Gaussian envelope), so the reflections bend where it passes, and its slopes are lightened or darkened
    as if lit from the far side. Under 28 fps it is switched off for the session (see [Main loop](#main-loop)).
- **Loot over water.** A drop where a wraith dies over the lake washes ashore: `dropSpot` keeps searching, ring by
  ring up to 40 tiles, until it finds a free dry tile (the nearest ring with one, picked at random on it).
- **The minimap** shows explored water dark blue.

## Main loop

A `requestAnimationFrame` loop runs update → render → HUD every frame. The next frame is scheduled *before* the
work.

- **Game time follows real time.** A frame's elapsed time (capped at 0.25 s, so a stall or a hidden tab
  doesn't jump the game) is split into update steps of at most 50 ms. A slow device therefore shows fewer
  frames, but the hero and the monsters keep their real speed. (Before, `dt` was simply capped at 50 ms, so
  under 20 fps the whole game ran in slow motion.)
- **Frame timing** (`adaptRes`, `PERF`): over 2 s windows, the average frame time, the slowest frame, and how long
  the frame's own work took (the update steps; render + HUD). Every frame counts, however slow; only a hidden
  tab and gaps over 5 s (a sleeping tab, a debugger pause) are skipped. (Before v83 frames over 0.25 s were
  skipped, so at 1-2 fps the readout froze at its last good value and the render scale never dropped.)
- **Automatic render scale** (`adaptRes`): from the 2 s average frame time. While a level is being played, the debug switch **Auto resolution** is on (the default), and the average is
  under 25 fps (`SLOW_FRAME`; 20 fps is still playable, so the picture stays sharp as long as it can), the render scale (canvas pixels per CSS pixel, normally `min(2, devicePixelRatio)`) drops
  by 0.25 (`DPR_CAP`), down to 1, and the canvas is resized. It never goes back up during the session. On a
  phone with a 3× screen, 1.5 is still sharp, and each step cuts the pixels drawn a lot (2 → 1.75 is 23 %
  fewer). This matters most for the home-screen app, which has the whole screen to draw.
- **Ripple refraction off under 28 fps.** In the same check, a 2 s average under 28 fps (`SLOW_REFRACT`) while
  Auto resolution is on switches the lakes' ripple refraction off (`REFRACT`) for the session; only the cheaper
  rings are drawn then (see [Lakes](#lakes)). It comes first, before the render scale drops at 25 fps. Switching
  Auto resolution off turns refraction back on.

Update and render run inside a `try/catch`: if something goes wrong, the
canvas state is reset, the first error is logged to the console, and the game keeps running instead of
freezing.

## The surface (depth 0)

A new hero starts on **the surface**, a few steps from the crypt's entrance, on a moonlit night. It is an endless
grassland with woods, glades, bushes and the crypt building; clicking the crypt's dark doorway takes the hero down to
depth 1 (`descend`). It has its own music (see [Music](#music)). For now nothing else lives there: no monsters, loot or keepers. The level name is *The
Surface*, depth 0. (A hero saved at depth 1 or deeper never comes back up: going up is todo #11.)

- **Super tiles** (`SURF`): the land is made of squares of `SURF.chunk` (32) tiles, generated from their world
  position and a fixed seed (`SURF.seed`; `srand` is a seeded mulberry32 over a hash of the keys, `vnoise` a smooth
  value noise), so a place always looks the same, for every hero.
- **The window:** the game's map is the 3 × 3 super tiles around the hero (96 × 96 tiles, `buildSurfaceWindow`), so
  drawing, paths and collisions work as on any level.
  - When the hero walks into another super tile (`shiftSurface`, checked every step), the window moves by whole
    super tiles: everything's coordinates shift by the same amount (hero and path, items, projectiles, fires,
    effects, floating text and the camera, so nothing jumps on screen), and the new super tiles are generated
    (about 3 ms).
  - World tile = window tile + `G.surf.ox`, `oy`.
  - Items on the ground keep their world position and come back when their place is in the window again.
- **What a super tile holds** (`chunkThings`), at most one thing per tile:
  - **Trees** where a forest noise (cells 9 tiles across) is high, so there are dense woods and open glades: a tile's
    chance is `0.55 × (forest − 0.45)`. One of four kinds at 0.8–1.15 × size, mirrored half the time. They block
    their tile and keep the 8 tiles around them free.
  - **Bushes** (2.5–4.5 %, four kinds, 0.8–1.2 ×) block their tile.
  - **Ground details** (about 3.5 %: flowers, rocks, mushrooms, tufts of tall grass) don't block.
  - **The crypt** in super tile (0, 0): a 5 × 5-tile building (`SURF.crypt`, `cryptN`) that blocks its footprint.
    Its doorway tile (`cryptdoor`) is in the middle of its south-west wall, outside it, on the entrance steps.
    Nothing grows within 4 tiles of it, nor on the lawn 11 tiles deep in front of its door.
- **Drawing:**
  - **Ground** (`drawSurfaceGround`): grass A everywhere, and grass B over it through a smooth mask. The mask is a
    small canvas with one pixel per tile (alpha from a noise with cells 7 tiles across), stretched over the tiles
    with smoothing, so the patches fade into each other. Both textures span 4 tiles, so they line up again after
    the window moves.
  - **Trees** are cut in two at the row where the crown ends (`META.surface` tree entries' 5th number, found by
    `add_surface.py`: the first row from the roots up as wide as half the crown; the oak's set by hand).
    - The **trunk** is sorted with everything on the ground.
    - The **crown** is drawn after all of it (`drawCrowns`), so the hero walking under a tree is under its leaves.
    - A crown turns see-through (40 %, eased) while the hero stands under it.
  - Trees and bushes have soft ground shadows. Ground details lie flat, except the grass tuft, which is sorted like
    a bush.
  - **The crypt** (`drawCrypt`): its picture (98 px per tile of its width, `CRYPT_FIT`) is placed with its front
    corner on the footprint's south corner. It is sorted by its front corner.
- **Light:** a moonlit night: the darkness is a thin blue-black (62 % instead of 93 %), the hero's light reaches 9
  tiles (7.2 below), and a faint light glows at the crypt's door.
- **The minimap** shows the grass, trees and bushes as dots, and the crypt.
- **The doorway** shows *Crypt Entrance — Depth 1* on hover.

## Dungeon generation

Each depth `d` from 1 gets a freshly generated level (depth 0 is the surface, above).

- Map size `min(44 + 2d, 80)` square (16 tiles more at the lake room's depth, see below). Up to `min(9 + ⌊d/2⌋, 18)` rectangular rooms of 5–10 × 5–10 tiles,
  kept at least 3 tiles apart.
- Each room is joined to the nearest earlier room by an L-shaped corridor, so the whole level is connected.
  `2 + ⌊d/4⌋` extra random corridors add loops. A corridor is 1 tile wide, or 2 wide with 65 % chance
  (`WIDE_ODDS`); a wide corridor's mouths are 2 tiles wide, so they never get a door. Within 2 tiles of a boss or
  big room the second lane is left out, so a wide corridor narrows to 1 tile at that room's mouth.
- **Boss and big rooms are entered only through doors.** After carving, every floor tile on such a room's
  surrounding ring that isn't a 1-wide mouth straight out of the room (a corridor running along the room, a
  corner, a 2-wide mouth) is filled in, as long as every room stays reachable (BFS from the start room). Where
  the tile is needed, that bit of corridor is moved one tile further out (around a corner: the 5 outer tiles
  around it) and the tile is filled if the level stays connected. Up to 3 passes; in tests of 400 levels
  (depths 1–10) every boss and big room ended up with doors on all its openings.
- Every void tile next to floor (8-neighbourhood) becomes a wall.
- **Doors.** A corridor tile in a room's surrounding ring, with void on both sides along the ring, is a door
  candidate. On a boss or big room's ring it always becomes a closed door; elsewhere with 55 % probability
  (`DOOR_ODDS`), so rooms with champions may or may not have doors.
- **Stairs down** are placed in the centre of the room farthest from the start room (by BFS walking distance),
  never the boss room or the big room.
  The hero starts in the centre of the first room, which never has monsters or chests.
- **Props per room:**
  - brazier: 75 % chance, always in the start room; blocking
  - chest: 38 % chance; blocking
  - urns: 0–2; blocking
  - bones: 0–2
  - gold pile: 20 % chance, worth 3–12 × d × `LOOT`
- **Big rooms.** Right after the start room, the generator places this depth's big rooms: first the boss room
  (if the depth has one), 11–14 tiles a side (about 2.8× the area of a normal 5–10 room), then the big room (if
  it has one), 16–20 tiles a side (about twice the boss room's area). They get the first 300 placement tries; one that doesn't fit falls back to an existing
  room (see below).
- **Boss room** at depth 5 (`BOSS_ROOM_FROM`) and from depth 6 (`BOSS_FROM`) on (`bossRoomAt`); depths 1–4 have
  none, and no boss. If the big boss room doesn't fit, the room with the largest
  `area × (BFS distance from the start + 10)` other than the start, stairs and big rooms is used instead. The
  stairs never go in it. **At depth 5 it stands empty**, a premonition of what is to come: only the rune circle,
  the braziers and the furnishings, with no boss, guards, champion or guardian's chest. From depth 6 it holds:
  - the boss on the centre tile, standing on the **rune circle** (see Rendering);
  - at least 4 ordinary braziers and a **guardian's chest**, on the edge (blocking);
  - furnishings (non-interactive), each type only from its unlock depth (`DECOR_FROM`): 3 skull piles on
    inner tiles (not blocking) and 2 banners from depth 3, 2 candelabra from depth 4, 2 broken pillars from
    depth 5, a sarcophagus from depth 6, an altar from depth 7, and a throne from depth 8, all on the edge
    (blocking). The throne's sprite faces down-right (+x), so it always goes against a back wall, facing into
    the room: on the left back wall (`x = r.x`) as drawn, or on the right back wall (`y = r.y`) mirrored, never
    in a corner or next to a doorway;
  - 1–2 ordinary monsters and a 50 % chance of an extra champion (without escorts; of a type allowed to be one);
  - no chests, urns, bones or gold piles.
  The boss's type is drawn by weight from the types unlocked at depth `d + 1`, so it can be a type not yet
  seen at this depth (from depth 6 every type is already unlocked, so this only matters if bosses start earlier).
- **Big room** at depths 3, 5, 7, … (every second depth from 3, `bigRoomAt`). If the big one doesn't fit, the
  largest room other than the start, stairs and boss rooms is used. It has the props of a normal room plus
  **2 grey banners** (the banner sprite drawn with `grayscale(1) brightness(0.85)`; without canvas filters, tinted
  grey) on its edge, and a larger pack of easier monsters: `1.5 × (5–7 + ⌊(d − 3)/2⌋)`, rounded (9 on average at
  depth 3, 13 at depth 7), never champions, of the types unlocked at depth `d − 4` or earlier, skeletons always
  allowed and weighted ×3 (depth 3: skeletons only; depths 5 and 7: skeletons, ghouls, spiders; depth 9: also
  wraiths).
- **The lake room** (`LAKE_AT`: depth 8, the first depth after the first boss fight at depth 6 that has no big
  room; `lakeRoomAt`). See [Lakes](#lakes) for how it looks and behaves.
  - **Placement.** A huge room, 28–30 tiles a side (`LAKE_ROOM`), in the map's top-left corner (`x = y = 2`). Its
    spot is kept free from the start (the start room and the others are never placed within 3 tiles of it), and
    it is placed first, right after the start room, so it always fits. Its "centre" (`cx`, `cy`: where corridors
    lead, and what the connectivity checks use) is on its dry shore, 3 tiles in from its south-east corner. With
    nothing north or west of it, every corridor reaches it through its east or south wall. Like the boss and big
    rooms it is entered only through doors. It is never the stairs', boss, big, keeper or lone monster's room.
  - **The lake.** After the walls are built, its tiles become water (`T_WATER`) except a dry shore 4 tiles wide
    (`LAKE_SHORE`) along the east and south walls. The shoreline is a quarter superellipse around the north-west
    corner (`((lx + 0.5) / A)^2.4 + ((ly + 0.5) / B)^2.4 < 1 + n`, with `A`, `B` the room's sides minus 4.5 and `n` a
    sum of four sine waves of random phase, ±0.29 at most), and any dry pocket not connected to the shore is
    flooded as well. The water covers 55–62 % of the room. Its far shores are the room's north and west walls,
    20 and more tiles from the nearest dry tile: out of sight (see Fog) and out of reach.
  - **On the shore:** 5 braziers, 2 bone piles and (50 %) a chest with the big room's better loot, on dry tiles
    next to the water that the camera sees, at least 5 (bones and chest: 3) tiles apart.
  - **In the water:** 4 broken pillars (decor, blocking, no shadow) 2–7 tiles from the shore with water all
    around them, at least 5 tiles apart. From the shore they are what the lake visibly reflects.
  - **A group of wraiths** (8–10, `LAKE_WRAITHS`, never champions, `lake: true`) hovering over the water: within
    6.5 tiles of a point 45 % of the way from the north-west corner to the shore, on tiles with water all around,
    at least 1.6 tiles apart. They wake and fight like any wraith; only wraiths can cross water (see
    [Movement & pathfinding](#movement--pathfinding)). The room has no other monsters.
- **Lone monsters** (`LONE_AT`): a foretaste of a type one depth before it starts to appear. One random normal
  room (not the start room) holds a single one of it (normal tier, never a champion) and nothing else:
  - **depth 3:** a Wraith (wraiths appear from depth 4);
  - **depth 4:** a Pit Demon (demons appear from depth 5).
- **A Keeper of the Crypt** on every third depth (3, 6, 9, …; `keeperAt`): a normal room that is neither the stairs'
  room nor the lone monster's, preferably 7 × 7 or larger, becomes the keeper's stall, with no monsters, chests,
  urns, bones or gold. See [Keepers of the Crypt](#keepers-of-the-crypt-the-market).
- **Green banners.** Every room joined to the boss room by a corridor (also at depth 5, where it stands empty)
  gets a banner (the normal banner sprite: dark green with a skull) on its edge, as close as possible to the mouth
  of that corridor: the room's last tile on the carved corridor's way toward the boss room (corridors are
  recorded with their tiles; with several corridors to the boss room, the first counts). The spot follows the
  usual edge rule (solid wall behind it, no doorway next to it), so it never blocks the corridor.
- **Green brazier.** When there is a boss room, with 50 % chance one room joined to the boss room by a corridor gets an extra brazier
  with green flames, a hint of what lies next door.
- Props are only placed on dry floor (`T_FLOOR`), never on water, except the lake's pillars.
- Blocking props are only placed on a room's edge, against solid wall, and never next to a doorway or
  corridor mouth, so they can't cut off a path.
- **Props stay in view.** The full-height south and east walls hide about the last two rows and columns of a
  room, so every prop (chests, urns, braziers, banners, bones, gold, furnishings) goes where the camera sees it:
  edge props only on the north edge (`y = r.y`, not in its last 2 tiles) or the west edge (`x = r.x`, not in its
  last 2 tiles); inner props on `x ≤ r.x + r.w − 3`, `y ≤ r.y + r.h − 3` (`freeInner(r, edgeOnly, true)`).
  Green banners also use only the north and west edges. Monsters may stand anywhere. Loot dropped near a south
  or east wall can land out of sight; its name label still shows when the hero is close.
- **Monsters per room** (normal rooms: not the start, boss, big or lone-demon room): an even draw from 1 to
  `cap = min(7, 3 + ⌊(d − 1)/2⌋)` (3 at depths 1–2, 4 at 3–4, 5 at 5–6, …), plus 1 with 50 % chance in a room
  of 64+ tiles. So a single monster stays possible at every depth. The type is drawn by weight from the types
  unlocked at that depth. A **champion** also brings 2–3 escorts of its own type (never champions themselves)
  on free floor tiles within 2 tiles of it.
- **New types** (`roomLimit`, `NEW_LIMIT`): counting from the depth `L` where a type first appears (its
  `minD`: ghouls 1, wraiths 3, Pit Demons 5), a room holds at most **1** of it at `L` and at most **2** at
  `L+1` to `L+3`; from `L+4` there is no limit. Escorts and boss-room guards count; a draw that would break
  the limit picks another type, and a champion's escorts stop at the limit. Skeletons and spiders are exempt.
  Other types can share the room. (The lone Pit Demon at depth 4 is outside this rule.)
- **Champions only from `L+4`** (`canChamp`, `CHAMP_AFTER`): a type can be a champion only from 4 depths after
  it first appears: skeletons, ghouls and spiders from depth 5, wraiths from 7, Pit Demons from 9. So there
  are no champions at depths 1–4. The boss room's extra champion is drawn only from such types.

## Movement & pathfinding

- **Collision.** Entities are circles (hero radius 0.28). A position is valid when all four corners of the
  circle's bounding box are on walkable tiles: floor or open door, with no blocking prop.
- **Water** (`T_WATER`, a lake) blocks everyone but wraiths, which hover (`MON` `float`, `flies(e)`). `blocked`
  lets water through while the global `FLY` is set: during each flying monster's update (`updateMonster`, so its
  A\* paths, straight walks, wandering and retreats can cross a lake) and inside `moveEnt` for the entity it moves
  (pushes and separation). Water doesn't block sight or projectiles (only walls and closed doors do), so arrows
  and wraith bolts fly over it. A hero click on water walks to the nearest reachable dry tile (partial path). Movement resolves
  the x and y axes separately, so entities slide along walls.
- **A\*** runs on the 8-connected tile grid with a binary heap and octile heuristic. Diagonal steps are not
  allowed past corners. A "near" mode stops on any free tile adjacent to the goal from which the goal is one
  step away: a diagonal neighbour counts only when the diagonal isn't cut by a wall corner (otherwise a walker on
  the other side of an outside corner would count as arrived and stand still). It is used for walking up to
  blocking props, doors and monsters.
- **Already next to the goal.** When the path comes back empty (on the goal tile or next to it), the walker steps
  straight at the goal point if that line is free. Being on the next tile doesn't mean being in reach, e.g. of a
  wraith keeping its distance, or of a monster's attack. The hero's attack walk stops as soon as the target is in
  reach, and so does a monster's chase.
- **Hero clicks use partial paths.** If the goal can't be reached (for example behind a closed door), the hero
  walks to the reachable tile closest to it.
- **Smoothing.** Paths are string-pulled: waypoints are skipped while the straight line stays walkable. The
  final waypoint becomes the exact clicked point when possible.
- The hero walks at 4.2 tiles/s, plus move-speed bonuses. If the hero is stuck for 0.3 s, the path is dropped.

## Hero

- Starts with: STR 10, DEX 10, VIT 10, a *Rusty Short Sword* (equipped), a *Short Bow* in the pack, and a
  stack of 3 health potions in the pack. Quick keys start as 1 = sword, 2 = bow, 3 = health potion.
- **Maximum life:** `40 + 4·VIT + 6·level + life bonuses`.
- **No regeneration.** Life regeneration is switched off because it rewarded stalling: `REGEN` (the share of
  max life regenerated per second) is 0, and no item has a regen bonus. The mechanics stay in the code
  (`h.st.regen = REGEN × max life + item regen`, applied every frame) but always add 0, and the stats panel
  doesn't show it. Life comes back only from potions and level-ups. Life is shown in the red orb at the bottom
  left.
- **Critical chance:** `5 % + 0.2 %·DEX + item crit`. Criticals deal ×1.75.
- **Experience:** level `L` needs `round(72 · L^1.7)` XP (72, 234, 1111 … for levels 1, 2, 5; 40 % less than the original `120 · L^1.7`). On a level-up, STR, DEX and VIT each gain +2 and
  the hero heals 20 % of max life (not fully). XP comes from:

  | Source | XP |
  |---|---|
  | Killing a monster | the monster's XP value |
  | Opening a chest | 6·d (guardian's chest: 15·d) |
  | Breaking an urn | 2·d |
  | Searching bones | d |
  | Opening a door | d |
  | Picking up an item | 2·d |
  | Picking up a potion | 1 + d |
  | Descending stairs | 10 × the new depth |
- **Potions** (see [Potions](#potions)): the health potion restores 44 % of max life (`HEAL`); the iron skin potion hardens
  the hero's armor to armor × 3 + 60 for 20 s (`IRON`). Using one takes 0.4 s of the hero's action time (see [Actions](#actions)).
- **Death** returns to the title screen with the fallen hero selected; the hero resumes from its last save
  (see [Saving](#saving)).

### Hero looks

Each hero is drawn with one of three walk sheets (`HERO_LOOKS`), its **look**, saved with the hero as `hero.look`:

| Look | Key | Sheet | Frames | `fpt` | Drawn at |
|---|---|---|---|---|---|
| Knight (the original) | `hero` (or none) | `assets/hero.webp` | 8 | 5 | 1 |
| Stocky knight | `hero2` | `assets/hero2.webp` | 12 | 8.54 | 0.96 |
| Mannequin | `mannequin` | `assets/mannequin.webp` | 12 | 8.02 | 1 |

- **Picking it:** in the hero's cogwheel box on the title screen, or with **Look** in the debug overlay (the selected
  hero's on the title screen, the played hero's in the game). `setHeroLook` writes the look straight into the hero's
  save entry (nothing else is saved) and, for the hero being played, changes it at once.
- **Loading:** only `hero.webp` loads at start-up; the other two load on first use (`LOOK_SRC`, `loadCast`, also on
  entering the game with a hero that has one). Until a sheet has loaded the hero is drawn as the knight.
- **Drawing:** `heroLook(h)` picks the sheet in `drawChar` and in the equipment screen's turning portrait; every sheet
  is 118 px tall at scale 1 and uses the knight's shadow. The stocky knight is drawn at 0.96 (`CAST_SCALE.hero2`):
  the stocky mocap guide is normalised to full height, so at scale 1 his short legs made his torso, head and
  shoulders bigger than the knight's; at 0.96 he is a little shorter. The walk frames advance by
  distance walked with the look's own `fpt` (frames per tile) divided by its scale, so the feet stay planted.
- **The sandbox's character viewer** sets `G.hero.look` to any sheet; its list names these three "The hero: …".
- **How the two new sheets were made** (the `sprite-animation` skill, `art/characters/hero-2/`): the stocky knight
  was painted by OpenAI over a stocky mocap mannequin guide (`render_guide.py --preset stocky`, Quaternius
  Walk_Loop), all 8 directions × 12 frames. `build_sheet.py` puts every painted figure back on its guide frame (the
  model had drifted figures by up to ~8 game px, most visibly in E and SE), keeps the mocap's in-place position (the
  body's natural sway), and computes `fpt` from the mocap's own stride (1.405 tiles per loop for the stocky legs,
  1.495 for the mannequin), so the foot on the ground stays still while the hero walks. The mannequin look is the
  skill's standard (not stocky) guide built as a sheet.

## Combat

**Damage dealt by the hero:**

`weapon roll (min–max) × (1 + 0.02·STR) × (1 + damage% / 100)`

Bows use DEX instead of STR. One roll is made per target hit. Fire bombs deal no rolled damage: their fire burns
for a fixed amount (see [Fire bombs](#fire-bombs)).

**Armor mitigation** (both directions):

`damage × (1 − armor / (armor + 40 + 8 · attacker level))`

Every hit deals at least 1 damage.

**Melee (swords, axes, bare hands).** Right-click a monster to walk into range and strike it; holding the
button keeps attacking. Right-clicking empty ground swings at once toward the cursor. A swing hits *every*
monster within reach and inside the arc, 0.08 s into a 0.24 s animation. Monsters right next to the hero are
hit regardless of angle. Only the **main target** takes full damage; every other monster hit takes 25 %
(`CLEAVE`). The main target is the clicked monster; for a swing at the ground (or if the clicked monster isn't
in the swing), it is the hit monster closest to the aim direction (nearer one on a near-tie). Each monster
gets its own damage and crit roll, then its own armor reduction.

| Weapon type | Reach (tiles) | Half-arc |
|---|---|---|
| Sword | 1.55 | 0.9 rad |
| Axe | 1.45 | 1.25 rad (wide cleave) |
| Bare hands | 1.25 | 0.8 rad |

**Ranged (bows).** A right click fires an arrow at the hovered monster, or toward the cursor. The hero first
**draws the bow**, standing still, for `BOW_DRAW.base + BOW_DRAW.perCd × (cooldown − 0.6)` s (0.15 s for a Short
Bow, 0.24 s for a War Bow; `drawTime`). The draw is part of the shot's cooldown, so the rate of fire is
unchanged. The arrow is aimed when it is loosed (`releaseArrow`): at the target monster where it is then, or at
the clicked spot. The bow sound plays at release. A walk clicked meanwhile starts after the draw. Kiting (shoot,
run, shoot again) stays possible; each shot just costs a little ground. Arrows travel
15 tiles/s for up to 12 tiles, hit the first monster they touch, and stop at walls and closed doors.

**Attack speed.** Each weapon has a cooldown (attacks per second = 1 / cooldown). It is the action time of an
attack (see [Actions](#actions)).

### Actions

The hero has one action timeline (`h.atkCd`, the time until the hero is free) shared by attacks, weapon swaps
and item uses:

| Action | Action time |
|---|---|
| Attack | the weapon's cooldown |
| Equipping or unequipping a weapon (`SWAP_T`) | 0.2 s |
| Equipping or unequipping other gear (armor, rings, amulet) | none (it still waits its turn) |
| Potion use (`USE_T`) | 0.4 s |

- **The action queue.** Quick-key presses (weapon swaps and potions), `Q`, the life orb, and every equip,
  unequip and use in the equipment overlay (its buttons and double-clicks) add an action to `h.queue`
  (`{ kind: 'equip' | 'unequip', id }` or `{ kind: 'use', pot }`). Whenever the hero is free (no action time left and no
  swing in progress), queued actions run in order (`runQueue()`), and always before any attack; an action that takes
  no time lets the next one run at once: while the queue holds anything, no attack starts. The queue has no length cap, isn't cleared by other
  input, and isn't shown on screen; it is cleared on a new level.
- **Pointless uses are skipped.** When a queued action comes up and would do nothing, it is skipped and takes no
  time, and the next one runs at once: a health potion at full life ("You are already at full health."), an
  iron skin potion while iron skin is active ("Iron skin is already active."), a potion of a type no longer in
  the pack ("No health potions left."), an equip of an item no longer in the pack, or an unequip of an item no longer equipped (or with
  a full pack: "Your pack is full.").
  Pressing a potion key with no potions of that type at all logs the same message and queues nothing.
- **A potion in use shows as equipped:** for its 0.4 s its quick key lights up instead of the weapon's, the
  attack button shows the potion, and the potion's icon rises above the hero's head and fades. Then the weapon
  comes back.
- **Walking is independent of the queue.** The hero keeps walking while items are swapped and used (only a melee
  swing stops the hero, as before).
- **Click attacks are not queued:** at most one click attack waits. A right-click on a monster while the hero is
  busy keeps it as the target with an attack pending (as before); a right-click on the ground while busy keeps
  the point as the one pending ground attack (`h.pendingAt`), fired as soon as the hero is free. A newer click
  replaces the waiting one, and a left click (walk / interact) or a pinch clears it. Holding the button keeps
  attacking whenever the hero is free.
- The equipment overlay goes through the same queue, so an equip clicked while the hero is busy happens when
  the hero is free (at most one attack's time later). The ring slot and the pack cell the old item goes to are
  decided when the action runs.

**Monsters:**

- Monsters wake when the hero is within 8.5 tiles with line of sight, or when they are hit (a hit always starts
  pursuit). A monster that wakes also wakes idle monsters within 6 tiles of it; one that is **hit** also wakes
  every monster in the same room. Which ones it can wake depends on its type and on how it woke (`WAKES`), and
  some types notice only by chance (`NOTICE_ODDS`):

  | Type | Notices the hero | Wakes on sighting | Wakes when hit | Woken by others |
  |---|---|---|---|---|
  | Skeleton | at once | skeletons | skeletons | yes |
  | Ghoul | 20 % chance per second | none | none | never |
  | Spider | at once | skeletons, spiders, demons | skeletons, spiders, demons | yes |
  | Wraith | 50 % chance per second | none | none | yes |
  | Pit Demon | 50 % chance per second | none | skeletons, spiders, wraiths, demons | yes |
- They chase directly when the way is clear for their whole body (`lineWalkable` with 1.05 × their radius) and
  otherwise follow A\* paths, re-planned every 0.5–0.9 s. A waypoint within 0.12 tiles counts as reached.
  **Detour:** a chasing monster that has stayed within 0.5 tiles of one spot for 0.6 s (`DETOUR_AFTER`, e.g.
  sliding against a corner or a prop) follows a fresh A\* path for 2 s (`DETOUR_T`) instead of walking straight
  at the hero. They push apart from each other and from the hero, and give up beyond 20 tiles.
- **Charge** (spiders and Pit Demons only, `CHARGE`). Hit by an arrow while more than 2.5 tiles from the hero, the
  monster rushes at 1.6× its speed for 2 s, at most once every 5 s (`chargeOnShot`). A puff of dust rises, a
  spider's legs skitter, and while it charges it trails dust. It closes some of the gap on a kiting hero without stopping kiting. Other monsters,
  fire bombs and melee hits never trigger it.
- **Losing interest.** A chasing monster goes back to wandering when:
  - it is **stuck** for 3 s (`STUCK_GIVEUP`): it is trying to move toward the hero (not in reach, not winding
    up, not standing to shoot) but stays within 0.5 tiles (`STUCK_MOVE`) of one spot, e.g. a pack plugging a
    corridor mouth. Plugging is intended; giving up thins the plug out. A monster that gave up this way is
    **calm**: it ignores the hero and isn't woken by other monsters for at least 6 s (`CALM_MIN`) and until it is
    unstuck (it has walked 1 tile, `UNSTUCK`, of its own random walk; pushes don't count). **A hit always starts
    pursuit**, also of a calm monster (its calm ends at once);
  - it has **not seen** the hero for 8 s (`LOST_SIGHT`). It isn't calm afterwards, so it wakes again normally.
- Idle monsters wander slowly.
- A monster not damaged for 4 s regenerates 1.5 % of its max life per second.
- **Melee monsters** wind up for 0.32 s (a visible shake). The blow lands only if the hero is still in reach.
- **Wraiths** keep 3+ tiles away. They cast a 0.45 s green bolt at 7 tiles/s with a 6.5-tile range; walls
  block it.

| Monster | Life | Damage | Armor | Speed (× 0.85) | Attack every | XP | From depth |
|---|---|---|---|---|---|---|---|
| Skeleton Warrior | 26 | 3–6 | 5 | 2.71 | 1.2 s | 16 | 1 |
| Ghoul | 20 | 2–5 | 2 | 3.3 | 0.9 s | 13 | 1 |
| Cave Spider | 15 | 2–4 | 1 | 3.9 | 0.8 s | 11 | 1 |
| Wraith (ranged) | 22 | 4–7 | 3 | 2.3 | 1.9 s | 22 | 4 (one lone wraith at depth 3) |
| Pit Demon | 75 | 8–13 | 12 | 2.24 | 1.5 s | 60 | 5 (one lone demon at depth 4) |

Spawn weights are 3 : 3 : 2 : 2 : 1 in table order. Every monster's speed is the table value × 0.85 (`MON_SPEED`):
2.3 / 2.8 / 3.3 / 2.0 / 1.9 tiles/s at depth 1, so the hero (4.2) can outrun them all. Life and damage in the table are base values: at depth 1 a
monster has 1.2× them (`MON_BASE`), e.g. a depth-1 skeleton has 31 life and hits for 3.6–7.2.

**Scaling with depth `d`** (the dungeon is endless):

| Stat | Scaling |
|---|---|
| Life | × 1.2 × 1.12^(d−1) (`MON_BASE`, `MON_SCALE`) |
| Damage | × 1.2 × 1.12^(d−1) |
| Armor | + 3·(d−1) |
| Speed | × min(1.35, 1 + 0.015·(d−1)) |
| XP | × 1.17^(d−1) |
| Monster level | = d (used by armor mitigation) |

**Monster tiers** (`TIER` in the code):

| | Normal | Champion | Boss |
|---|---|---|---|
| Occurs | always | 10 % of monsters of a type at least 4 depths past its first depth (`canChamp`; none at depths 1–4; never in the big room, as a lone monster or as escorts) | one per level from depth 6, in the boss room |
| Name | type name | prefix + type, e.g. *Dread Ghoul* | *&lt;name&gt;, &lt;type&gt; Tyrant*, e.g. *Morgrath, Ghoul Tyrant* |
| Life / damage / XP | ×1 | ×2.5 / ×2 / ×4 | ×8 / ×3 / ×12 |
| Armor | — | — | + 4·d |
| Size | ×1 | ×1.15 (radius too) | ×1.35 drawn; radius ×1.15, at most 0.48 so it fits corridors |
| Look | — | red glow, gold health bar and target name | green glow, green health bar and target name |
| Loot | see Loot sources | see Loot sources | see Loot sources |

Boss names are drawn from Morgrath, Vexhollow, Ulthane, Skarn, Belmorah, Grisvald, Nythra, Corvane, Drokkar
and Ashmire.

## Items

**Slots:** weapon, helm, armor (chest), gloves, boots, two rings and an amulet. Only one weapon can be
equipped at a time. Potions are not equipped; they are used (see [Potions](#potions)).

**Item types.** An item's stats are fixed by its type: a Longsword is 7–14 damage wherever it drops (there are
no item levels). Each slot has a ladder of types; a type can drop once the **loot depth** reaches its unlock depth
(`lvl`). The loot depth is the current depth, + 1 for 30 % of a normal chest's items, and deeper for the richer
sources (`LOOT_PLUS`, below). Every type has its own icon.

| Item | Type | Stats | Unlocks at |
|---|---|---|---|
| Short Sword | sword | 4–8, 0.55 s | 1 |
| Longsword | sword | 7–14, 0.65 s | 2 |
| Broadsword | sword | 13–22, 0.7 s | 5 |
| Blackened Greatsword | sword | 20–34, 0.85 s | 8 |
| Bastard Sword | sword | 24–40, 0.8 s | 11 |
| Knight's Greatsword | sword | 32–52, 0.85 s | 15 |
| Hand Axe | axe | 5–10, 0.7 s | 1 |
| Bearded Axe | axe | 10–18, 0.8 s | 4 |
| Battle Axe | axe | 17–29, 0.9 s | 7 |
| Executioner's Axe | axe | 26–46, 1.05 s | 9 |
| Great Axe | axe | 34–58, 1.05 s | 14 |
| Short Bow | bow | 3–7, 0.6 s | 1 |
| Hunting Bow | bow | 5–10, 0.65 s | 2 |
| Yew Longbow | bow | 9–16, 0.75 s | 5 |
| Bone Bow | bow | 14–25, 0.9 s | 8 |
| Composite Bow | bow | 18–31, 0.85 s | 11 |
| War Bow | bow | 25–42, 0.9 s | 15 |
| Leather Cap | helm | armor 3 | 1 |
| Iron Helm | helm | armor 7 | 4 |
| Horned Great Helm | helm | armor 13 | 8 |
| Visored Helm | helm | armor 19 | 12 |
| Leather Tunic | armor | armor 6 | 1 |
| Studded Leather | armor | armor 11 | 4 |
| Chain Mail | armor | armor 18 | 7 |
| Plate Cuirass | armor | armor 28 | 11 |
| Full Plate | armor | armor 36 | 15 |
| Leather Gloves | gloves | armor 2 | 1 |
| Iron Gauntlets | gloves | armor 6 | 4 |
| Plated Gauntlets | gloves | armor 10 | 9 |
| Heavy Gauntlets | gloves | armor 13 | 14 |
| Leather Boots | boots | armor 2, +5 % move speed | 1 |
| Plated Boots | boots | armor 6 | 4 |
| Iron Greaves | boots | armor 10 | 9 |
| Heavy Greaves | boots | armor 13 | 14 |
| Silver Ring, Ruby Ring, Grave Ring | ring | none | 1 |
| Sapphire Amulet, Blood Amulet, Bone Talisman | amulet | none | 1 |

**Choosing a drop** (`genItem`): the rarity is rolled first (see below). Then a **group** is drawn evenly from
sword, axe, bow, helm, armor, gloves, boots, ring and amulet, and then a type of that group unlocked at the loot
depth, older types less likely (weight × 0.5 for every 4 depths since the type unlocked; e.g. at loot depth 6 a
sword is a Blackened Greatsword 38 % of the time, a Short Sword 16 %).

**Rings and amulets** have no stats of their own: they only drop as **magic or rare** items (a common roll never
picks them), and all their worth is in their affixes, whose ranges are doubled on them (`JEWEL_MULT`). With the
rarity gates below they appear from depth 4 at the earliest (amulets from depth 6, `AMULET_FROM`; rings from 4,
`RING_FROM`). Old saves keep their rings and amulets as they were.

**Rarity.**

| Rarity | Base chance | Affixes | Name |
|---|---|---|---|
| Common (white) | the rest | 0 | type name |
| Magic (blue) | (30 % + boost) × `MAGIC_ODDS` (0.25) | 1–2 | "Prefix Type Suffix", e.g. *Mighty Longsword of the Fox* |
| Rare (gold) | (7 % + half the boost) × `RARE_ODDS` (0.1) | 3–4 | random name, e.g. *Gravefang, Longsword* |

So a plain drop is 0.7 % rare and 7.5 % magic, at every depth where the rarity is allowed. Chests, champions and
bosses add a rarity boost (with a 0.35 boost: 2.45 % rare, 16.25 % magic). An item with a forced rarity (the
starting kit, the guardian's chest) skips the roll.

**Rarity gates by depth.** No magic items before depth 4 (`MAGIC_FROM`) and no rares before depth 8 (`RARE_FROM`);
a roll above what the depth allows is lowered to the best allowed rarity.

**Richer sources drop deeper loot** (`LOOT_PLUS`): their items are those allowed at a deeper depth, for everything
the depth decides (item types, affix tiers, the rarity gates and the ring and amulet gates):

| Source | Loot of depth |
|---|---|
| Champions | d + 2 |
| Chests in the big room | d + 2 |
| The boss | d + 3 |
| The guardian's chest (all its items) | d + 4 |

So a champion's drops can be magic from depth 2 and rare from depth 6, and bosses (from depth 6) can drop rares
from the start. Champions themselves appear from depth 5.

**Affixes** are the bonuses of magic and rare items: **prefixes** go before the type's name, **suffixes** after it.
Each kind has 3 tiers with fixed ranges and their own names. A tier can roll once the loot depth reaches 1, 7 or 12
(`AFFIX_FROM`); among the unlocked tiers, higher ones are likelier (weights 1 : 2 : 4). A kind appears at most once
per item. On rings and amulets every range is doubled.

| Stat | Tier 1 (from 1) | Tier 2 (from 7) | Tier 3 (from 12) |
|---|---|---|---|
| +STR | Mighty / of the Bear, 1–4 | Brutal / of the Boar, 5–8 | Titanic / of the Giant, 9–12 |
| +DEX | Nimble / of the Fox, 1–4 | Deft / of the Lynx, 5–8 | Lithe / of the Falcon, 9–12 |
| +VIT | Sturdy / of the Ox, 1–4 | Stalwart / of the Bull, 5–8 | Unyielding / of the Mountain, 9–12 |
| +Life | Hale / of Life, 5–16 | Robust / of Vigor, 17–30 | Vigorous / of Endurance, 31–45 |
| +Armor (not on weapons) | Warded / of Iron, 2–8 | Fortified / of Steel, 9–15 | Impregnable / of Adamant, 16–22 |
| +Crit % | Keen / of Precision, 1–3 | Precise / of Striking, 3–5 | Deadly / of Slaying, 5–8 |
| +Damage % | Cruel / of Slaughter, 5–15 | Savage / of Carnage, 16–26 | Merciless / of Ruin, 27–38 |
| +Move speed % (boots only) | Swift / of Haste, 3–6 | Fleet / of Speed, 7–10 | Windborne / of the Wind, 11–15 |

**Loot sources:**

`LOOT` (0.8) thins all loot by 20 %: each random item drop below happens only with probability `LOOT`
(`lootItem()`), and every gold amount is multiplied by `LOOT` (`dropGold()`, at least 1). Potion drops are not
affected by `LOOT`; instead every potion chance below is the base chance × 1.2 (`POTION_ODDS`): monsters 8.1 %,
chests 27 %, urns 10.8 %. A dropped potion is then an iron skin potion 15 % of the time and a health potion 85 % (`dropPotion()`). The guardian's chest's guaranteed item is not thinned.

| Source | Drops (item chances before `LOOT`) |
|---|---|
| Monster | 13 % item, 6.75 % × 1.2 potion, 30 % gold (2–8 × d), 2 % one fire bomb (from depth 2) |
| Champion | an item of depth d+2 (boost 0.35), plus a 50 % chance of a second (boost 0.2) |
| Boss | an item of depth d+3 (boost 0.35), gold (20–40 × d), plus the normal potion / gold rolls of a monster |
| Chest | 1–3 items (boost 0.15, 30 % chance of loot depth d+1; in the big room all of depth d+2), gold (10–30 × d), 22.5 % × 1.2 potion, 15 % 1–3 fire bombs (from depth 2) |
| Guardian's chest | **always** one item of depth d+4 that is rare (30 %) or else magic, gold (30–60 × d), plus everything a normal chest drops (its items also of depth d+4) |
| Urn | 35 % gold, 9 % × 1.2 potion, 8 % item, 5 % one fire bomb (from depth 2) |
| Bones | 20 % gold, 10 % item |

**Guardian's chest.** It glows green and is labelled *Guardian's Chest* on hover. While the boss lives it is
sealed: clicking it only logs "The chest is sealed while its guardian lives." When the boss dies, the log says
"<boss> is destroyed. The guardian's chest unseals."

Dropped things land on nearby free tiles. Floor items bob, glow in their rarity colour (potions in their
potion colour), and show a name label when within 7.5 tiles: in the item's colour with a black outline (no
background box). A magic or rare item's label also shows its affix tier (see below): tier 1 plain, tier 2
bold, tier 3 bold, 15 px instead of 13 and glowing in its colour. Gold is counted at the top left.

**Affix tier highlight.** A magic or rare item's highlight grows with its *affix tier* (`itemTier`): the tier
(1–3) of its best affix, worked out from the rolled values against the affix tier ranges (a ring's or amulet's
values are halved first, as they roll doubled; a value on the border of two ranges counts as the lower tier;
built-in bonuses don't count). It works for saved items too, as nothing new is stored.

| Tier | Floor glow (radius, strength) | Pack, paper doll and quick-key highlight |
|---|---|---|
| 1 | 26 px, 0.40 | faint inner glow (7 px, 40 %) |
| 2 | 33 px, 0.55 | inner glow (11 px, 65 %) |
| 3 | 40 px, 0.70, pulsing | strong inner glow (16 px, 95 %), an outer glow and a border in the rarity colour |

Blue for magic items, gold for rare ones, as before.

### Fire bombs

A **fire bomb** is a clay pot of lamp oil, stoppered with an oil-soaked rag. It is thrown, shatters where it
lands, and sets the ground on fire. The constants are `BOMB` and `FIRE` in the code. One that lands in a lake
doesn't shatter: it sinks with a big splash (a ripple 1.6× a drip's and its own sound, `plunge`) and starts no fire. But
something hard standing in the water breaks it: a bomb whose path passes within 0.45 tiles of the middle of a
blocking prop on a water tile (the lake's broken pillars) below that prop's top (its sprite height × scale, against
the bomb's height along its arc at that point) shatters there (`shatter(…, hard)`), and its fire burns on the water
around it. A fire
on the shore spreads over the water within its circle (the oil burns on the water's surface), and burns whatever
hovers there.

- **The item.** Fire bombs aren't in `BASES`, so they never drop as a random weapon. A stack of them is one item
  (`makeBombs(n)`: base `firebomb`, slot `weapon`, kind `bomb`, with a `count`), shown with its count like a
  potion stack. Bombs picked up join the hero's stack: the equipped one, else the first one in the pack
  (`bombStack()`); with none, they take a pack cell like any item (a double click equips them). Tooltip: what it
  does, the range, the fire's radius, damage and duration, throws per second, and how many the hero carries.
- **Equipping.** The stack must be equipped in the weapon slot to throw. It equips like a weapon (0.2 s, see
  [Actions](#actions)); the weapon it replaces goes into the pack. Bound to a quick key it becomes a **fire bomb
  key** (`{ type: 'bomb' }`, whatever the stack). Pressing it equips the hero's bombs from the pack, does nothing
  if they're already equipped, or logs "No fire bombs left.". The key shows the bomb icon and the number carried,
  dimmed at 0, and lights up while bombs are equipped.
- **Throwing.** With bombs equipped, a right click (and the other attack inputs) throws one at the clicked
  monster's position, or at the spot under the cursor, at most `BOMB.range` (7) tiles away. A target farther off
  is shortened to 7 tiles along the same line. Like a bow, it fires at once without walking into reach, and
  holding the button keeps throwing. One throw every `BOMB.cd` (1 s). Each throw uses one bomb.
  - **Running out.** When the last is thrown the weapon slot is empty: the hero fights bare-handed until another
    weapon is equipped (nothing is equipped automatically). The log says "That was your last fire bomb. Your
    hands are empty."
- **Flight.** Unlike an arrow, which flies on until it hits something, a bomb lands on the aimed spot:
  - It flies in an arc over monsters, taking 0.3 s + 0.065 s per tile.
  - Its height on screen is `44·(1 − u) + 4·peak·u·(1 − u)` px at `u` = time / flight time, with peak = 30 + 9 px
    per tile.
  - It tumbles, its rag burns with a small flame and trails sparks, and a small shadow follows it on the floor.
  - A wall or closed door in the way breaks it at the last open spot in front of it (the path is checked every
    0.1 tile).
- **Impact.** Terracotta shards and a burst of embers fly, and a **fire** starts centred where the bomb broke.
- **The fire.** A circle of radius `FIRE.r` (1.5 tiles) burns for `FIRE.dur` (12 s).
  - **Strength.** It flares up over the first 0.25 s (bigger flames), and its strength falls to 0 over the last
    `FIRE.fade` (1.5 s).
  - **Damage.** Anyone in it takes `FIRE.dps` (10) life per second: monsters and **the hero too**. A creature is
    in it when its centre is within the radius plus half its own radius.
    - **Burning on.** A creature that leaves the fire keeps burning for `FIRE.after` (10 s) at `FIRE.afterDps`
      (5 per second, 50 in all; `burnLeft`). Touching a fire again restarts the 10 s. Nothing stacks: in two
      fires, or in a fire while still burning, it is 10 per second.
    - **Monsters catch fire more slowly:** a monster has to stand in a fire for `FIRE.catchMon` (1.5 s) without a
      break (`fireT`) before it burns on after leaving. Until then the fire hurts it, but its burning stops when it
      steps out (a burn it already had runs on). The hero catches fire at once.
    - Damage comes in ticks of `FIRE.tick` (0.5 s), the first at once on catching fire. A tick's fraction carries
      over to the next (`burnCarry`): the afterburn's 2.5 per tick comes out as 2 and 3 alternately. The tick timer
      refills while not burning, so catching fire again and again never burns faster.
    - Armor doesn't reduce it, and it is never a critical.
    - **A burning creature shows flames:** five flickering flames up its body, full size while in a fire and
      shrinking as its burning runs out (`drawBurning`).
    - **The hero's burn badge:** while the hero burns, a flame badge sits on the life orb's top-left edge, showing
      the seconds left, or "in fire" (`#burnBadge`, in `updateHud`).
    - A burned monster shows orange damage numbers and starts pursuit like any hit (a calm monster too). A
      monster killed by fire gives its XP and loot as usual.
    - The hero gets the usual red numbers and red flash; a death by fire logs "You burned to death at depth N."
  - **Monsters don't avoid fire:** they walk through it after the hero.
  - **Scorch mark.** After the fire is out, a scorch mark stays for `FIRE.scorch` (20 s), fading.
- **Loot.** From depth 2 (`BOMB.from`): chests 15 % (1–3 bombs), urns 5 % (one), monsters 2 % (one). See
  *Loot sources* above.

**How the fire looks.** The look is **Blaze** (`LOOK.fire` 1 of `FIRE_LOOKS`). The other two, Ember bed and Oil
pool, are kept for comparison: the sandbox's fire scenarios have **Fire look** buttons that switch it (`setLook`)
for the page's session only (nothing is saved; **Normal game** puts Blaze back). A new fire takes the current look.

- **Common to all three:**
  - Flames, smoke and sparks are particles in world coordinates, spawned on walkable tiles inside the circle
    (`fireSpot`), and on a lake's water there too (the lamp oil floats and burns on it; drawn at the water's
    level, `LAKE.drop` lower), and depth-sorted with the walls, props and characters.
  - Flames are pre-drawn soft tongues (narrow tip, a pale hot core at the root) in four colours, from yellow
    through orange to dark red as they age (`flameSprites`, `FLAME_COL`), drawn additively. Smoke is a soft puff
    drawn normally, growing as it rises.
  - The fire lights its surroundings: a light hole of radius 2.2 + 1.3 × r tiles (flickering) and an additive
    orange glow.
  - Under it the floor darkens (the scorch).

| | 1 Blaze | 2 Ember bed | 3 Oil pool |
|---|---|---|---|
| Ground | scorched floor with an orange glow | the floor glows like coals: an orange-to-red disc with 70 flickering ember spots | a dark pool of oil (a wobbling 16-sided blob) with a burning orange surface and a bright rim |
| Flames | dense and tall over the whole circle: 110 / s, 24–42 px, rising 50–90 px/s, 0.45–0.85 s | short licks, 70 % at the rim: 65 / s, 14–26 px, 0.3–0.6 s | low and wide (× 1.35) with blue roots: 75 / s, 18–30 px, rising 14–30 px/s, 0.5–0.9 s |
| Smoke | grey, 10 / s | grey, 3 / s | thick black, 12 / s |
| Sparks | 4 / s | 14 / s | 3 / s |

**The bomb's look.** Design 1 of six AI-made designs, `firebomb1`: a round brown terracotta pot with a rag
stopper and twine around the neck. The other five (`firebomb2`–`firebomb6`) are in the item atlas, unused, for
stronger fire bombs later:
2. a green glazed flask in a rope net, with a wax seal;
3. a black clay sphere with iron bands and a wick;
4. a two-handled jug sealed with pitch;
5. a bone-white orb with a red flame mark;
6. a leather-strapped jar with an oil stain.

See [Assets](#assets).

## Keepers of the Crypt (the market)

On every third depth (3, 6, 9, …) a **Keeper of the Crypt**, a living human merchant, keeps a stall in a quiet room of
its own. It is an NPC: it never fights and nothing attacks it. Hovering shows its name; clicking it walks the hero up
to it and opens the **market** (`openMarket`). The constants are `KEEPER` in the code.

- **The four keepers** (`KEEPERS`), one drawn at random for each stall (`look`):
  - **Aldric the Wanderer**, a travelling merchant in a green fur-trimmed cloak with a lantern: "Long road down here,
    friend. Let us trade."
  - **Borin the Smith**, stout, in a leather apron with a hammer and tongs: "Steel for steel. What have you got?"
  - **Mirela the Peddler**, in a blue hooded cloak with a basket of potions: "Potions, trinkets, a little luck. Come
    and look."
  - **Old Tobias**, a scholar with spectacles and a satchel of scrolls: "Ah, a customer! Rare finds for rare folk."
- **The stall** (`furnishKeeper` in `buildLevel`):
  - the keeper stands on a round red rug, on the free tile nearest the room's middle that the camera sees, and
    blocks it (until it walks, see below);
  - on the north and west edges, each only where it fits: a trestle table with wares (as near the keeper as
    possible), a weapon rack, a shelf of potions, an open chest of trinkets, crates and sacks, a barrel of swords,
    and two lanterns on posts;
  - all furnishings are decor, not interactive. The keeper (light radius 3.4 tiles) and the lanterns (2.6) light the
    room.
- **The keeper walks** (`updateKeeper`, `drawKeeper`): each keeper has an 8-direction walk cycle (`keeper1`–
  `keeper4` in `META.characters`; see [Walk cycles](#walk-cycles-hero-skeleton-ghoul)), drawn at the hero's size
  (`KEEPER.scale` 1) with a character's shadow and depth-sorted like one (by its position `fx + fy`).
  - It **always faces the hero** (`setDir`, the same 8 screen sectors as the characters), standing on its idle
    frame.
  - **It walks up to the hero once:** the first time the hero is inside its room (the room's rectangle), the
    keeper walks straight toward the hero at 1.6 tiles/s (`KEEPER.speed`; walk frames advance with distance, `fpt`
    5, Old Tobias 5.5) and stops 1.4 tiles from the hero (`KEEPER.meet`). It also stops where its next step would
    leave its room (0.35 tiles in from the edge), run into a wall or a blocking prop, or after 8 s
    (`KEEPER.walkMax`). From then on it stays where it stopped (`state` `wait` → `come` → `done`) and only turns
    to keep facing the hero; it never follows the hero and never leaves its room.
  - Its tile doesn't block while it walks; where it stops it blocks again (unless the hero stands on that tile).
    Its tile (`x`, `y`) follows its position, so the market's reach (3 tiles), its light (3.4 tiles) and the
    walk-up click all use where it is now. The keeper's look switch in the sandbox changes the walking sprite too.
  - The market's portrait still uses the standing sprite (`keeper1`–`keeper4` in `META.props`).
- **The market screen** (`#market`, styled like the equipment overlay; it scales down to fit like it). The world
  doesn't pause. It closes with `Esc`, the ✕ button, opening the equipment, or by walking more than 3 tiles from the
  keeper (`KEEPER.reach`). It shows:
  - the keeper's portrait (its sprite's upper part), name and greeting, and the hero's gold;
  - **Wishes**, **Services**, **For sale** and **Your pack** (described below);
  - a **detail pane**: a click on any item (for sale, in the pack, or a wish's offer) shows its stats, its value
    and what can be done with it.
- **Wishes** (`KEEPER.wishes`, 2 per keeper, `makeWish`): something the keeper wants, and the item it gives for it.
  - **What it wants:** a piece of gear of a kind ("any helm", "any axe", …; from depth 6 sometimes "magic or rare
    gloves" and the like), 2–3 health potions, or 2–3 fire bombs. A keeper never wants the same kind twice.
  - **What it offers:** always a magic item of depth + 3, or a rare one (25 %) where depth + 3 allows rares. It is
    rolled when the level is built, so you can see it before trading.
  - **Trading:** the **Trade** button gives the least valuable matching item in the pack (gear), or that many from
    a stack, for the offered item. It goes into the pack, or onto the floor if the pack is full. The wish is then
    done. Equipped items never count.
- **For sale** (`KEEPER.stock`, 4–6 items, `makeMarket`): gear of depth + 3 (`KEEPER.plus`) rolled like loot with a
  0.25 rarity boost, so mostly common items, with magic and rare ones if you're lucky. Buying costs the item's
  value and needs a free pack cell. A bought item's cell stays empty.
- **Your pack** shows every pack item with its sell price. Selling gives `KEEPER.sell` (25 %) of the value, for
  one at a time from a stack (or the whole stack), and clears quick keys bound to a sold item.
- **Services:** **heal** to full life for `1 + 0.15 × depth` gold per missing life point (1.45 at depth 3, 1.9 at
  depth 6).
- **Values** (`itemValue`):
  - an item type unlocking at depth L is worth `12 × L² + 50` (a Short Sword 62, a Broadsword 350, a War Bow 2750);
  - rings and amulets count as L = 3 + 3 × their affix tier;
  - magic items are worth × 2.5 and rare ones × 5, plus 15 % per affix tier above 1;
  - potions and fire bombs have fixed prices per piece: health 40, iron skin 60, fire bomb 50.

  For comparison, a level holds about 250 × depth gold (100 at depth 1, 370 at 3, 1300 at 6, 2400 at 9), so a hero
  reaches the first keeper with about 500 gold.
- Nothing about the market is saved: a keeper's stock and wishes belong to its level.

## Equipment overlay

Opened with `I` / `C` / `Tab` or the **Equipment** button (the grid square at the end of the quick-key bar), closed with the same keys, `Esc`, the button,
or the **✕** in its header (for touch screens). It is a partly transparent dark panel
(`rgba(16, 11, 14, 0.78)`); **the game keeps running underneath** and can still be played around it.
If it doesn't fit the screen it is scaled down to fit (see HUD, Phones).

- **Paper doll:** eight slots around an animated portrait of the hero walking (12 frames/s) and slowly
  turning through all eight directions, drawn 128 px tall with the frame's aspect ratio kept.
- **Inventory:** 6 × 5 grid (30 items). Potion stacks sit in it like any item, with their count.
- **Clicking items** (an equipped item, a pack item, or a quick key in the overlay), with any pointer:
  - **a click or tap opens the action box:** the item's tooltip, without the mouse hints, placed centred on the
    element, below it if it fits, otherwise above it, with buttons: **Equip** (pack item) or **Use** (pack
    potion), **Drop** (pack item), **Unequip** (equipped item), **Equip** / **Use** and **Clear key** (bound
    quick key), always **Close**, and for weapons and potions a **Quick key: 1–0** row to bind it. A button acts
    and closes the box; a click or tap anywhere outside it also closes it. While the box is open, hovering other
    items doesn't show their tooltips.
  - **a mouse double-click acts without the box:** queues equipping a pack item (or using a potion), unequipping
    an equipped item, or using a quick key (see [Actions](#actions)); the box's **Equip** / **Use** /
    **Unequip** buttons queue the same way. The first click of the double-click
    opens the action box, and the second closes it. (On touch screens a tap always opens the box.)
  - Equipping swaps the previously equipped item into the same cell. Rings fill an empty ring slot first,
    otherwise they replace ring 1. Unequipping needs a free pack cell.
  - Right-click (or `Shift` + click) a pack item to drop it on the floor (this also clears its quick key), or a
    quick key to clear it; these act at once, without the box.
  - These are captured on the overlay before the elements' own click handlers. The last pointer type is tracked
    on every `pointerdown`; hover handlers ignore touch input (emulated mouse events would otherwise show, move
    or hide the tooltip). The HUD hotbar is not part of the overlay and still acts on a click or tap (see *HUD taps* under Controls).
- **Tooltips** (on mouse hover): name in rarity colour, type, damage and attacks per second or
  armor, and every bonus. For pack items it also compares with the equipped item in that slot: base DPS
  difference for weapons, armor difference otherwise. A potion's tooltip shows its name in its colour, "Potion ·
  instant use", its effect and the stack count. A hint line lists the mouse actions.
  A hover tooltip (here and on the HUD's quick keys) follows only the real mouse (`pointermove` with
  `pointerType` mouse, not the mouse events browsers make up from touches), closes as soon as the mouse is no
  longer over the element that opened it (`tipHover`), and closes on any touch. So on a device with both a mouse
  and a touch screen, a tooltip opened by the mouse can't get stuck when the game switches to touch.
- **Sound:** under the attributes, a **Music** and an **Effects** slider (0–100 % in steps of 5, default 60 % and
  100 %), with the value beside each. See [Music](#music) and [Sound](#sound).
- **Attributes:** level, XP, STR / DEX / VIT, life (live), armor, damage range, attack speed, crit,
  move speed, kills, gold. Most show where they come from (`statRows`, `breakdown`): `total (parts)`, e.g.
  `Armor 80 (50+10+20)`. The total is white; the parts are **character** (grey), **regular items** (darker
  grey: base armor, a weapon's own damage, built-in bonuses such as the Leather Boots' +5 % speed), **magic**
  (blue: affixes) and **temporary** (gold: iron skin). Only non-zero parts are listed, and the brackets only
  when there are two or more. A row with a temporary part has a gold glow on its label and total. The sources
  (`h.src`, filled in by `recalc`) are split as follows:
  - **Strength / Dexterity / Vitality:** the hero's own (start + 2 per level) + affixes.
  - **Life:** character 40 + 6 per level + 4 per own Vitality; magic: Life affixes and 4 per Vitality from
    affixes.
  - **Armor:** item base armor + Armor affixes + what iron skin adds.
  - **Damage** (a range; the formula multiplies, so it is split in order): the weapon's own damage (regular; with
    bare hands, the character's), what the hero's own STR (DEX for bows) adds at 2 % per point (character),
    and the rest, from affix STR / DEX and Damage % (magic).
  - **Critical:** character 5 % + 0.2 % per own Dexterity; magic: Critical affixes and 0.2 % per Dexterity
    from affixes.
  - **Move speed:** 100 % + built-in boot speed (regular) + Speed affixes (magic).
  - Level, experience, attack speed (the weapon's alone), kills and gold have no breakdown.
- **Quick keys:** hover a weapon (in the pack or the weapon slot) or a potion stack, then press `1`–`9` / `0`
  to bind it to that key (or use the action box's key row). A weapon, or a potion type, can only be on one key,
  and key tags show on bound items. A weapon key is `{ type: 'item', id }`; a potion key is
  `{ type: 'use', pot }`, bound to the potion type rather than the stack.
- Outside the overlay (or while hovering nothing in it), a quick key queues equipping its weapon from the pack,
  or queues a use of its potion (see [Actions](#actions)). The bottom hotbar shows the bound icons and the
  stack count on potion keys (dimmed at 0), highlights the equipped weapon (or the potion being used), and can
  also be clicked.

## Debug overlay

`Ctrl` + `D` opens and closes a small **Debug** panel at the top right, under the minimap (it works with the
game paused or running, and on the title screen; the browser's bookmark shortcut is suppressed). On touch screens,
holding one finger on the minimap and one on the life orb together for 0.8 s opens or closes it too
(`DBG_HOLD_MS`, `dbgHeld`; the phone vibrates briefly where supported). On the title screen, a double click on the
version number (bottom right), or a long press of 0.8 s on a touch screen, does the same. All of these call
`toggleDebug`. The panel is a fixed element of its own outside the HUD, above the title screen (z-index 42, the
title screen is 40), so it can be used there. While the minimap is held, touching the orb drinks no potion; on touch
screens the minimap takes touches for this (so touching it doesn't walk there). Its heading shows the game version
(`v<N>`, as on the title screen). Its switches are remembered in
`localStorage` (`dc01-debug`, wrapped in `try`):

- **Music** (always shown, under the frame rate) — the current mood, file and play number, e.g.
  `music: explore · explore (play 2) · demon level` (see [Music](#music)).
- **Frame rate** (always shown under the switches) — over the last 2 s: the average frames per second, the
  slowest frame, the average time per frame of the update steps and of render + HUD (main-thread time), and the
  current render scale, e.g. `58 fps · worst 21 ms · update 0.4 · render 3.2 ms · scale 2`, plus
  `· refraction off` once the lakes' ripple refraction has been switched off (see [Main loop](#main-loop)).
  Reading it when the game is slow: a large **render** time means drawing itself is slow (e.g. the browser fell
  back to drawing the canvas without the GPU); low update and render times at a low fps mean the time goes
  outside the game's code (the browser's compositing or GPU, or another tab).
- **Look** — the hero's look (see [Hero looks](#hero-looks)): on the title screen the selected hero's, in the game the
  played hero's. Saved with that hero, not in `dc01-debug`.
- **Pursuit indicator** — a red dot (5 px, black outline) above every monster that is pursuing the hero
  (`state === 'chase'`).
- **Auto resolution** (on by default) — the automatic render scale of [Main loop](#main-loop). Switching it off
  puts the scale back to `min(2, devicePixelRatio)` at once and keeps it there, and turns ripple refraction back
  on (the frame-time fix, real game speed at a low frame rate, stays on either way).

## HUD

- **Hero life bar** (`drawHeroBar`, `HERO_BAR`): a bar over the hero's head, shown for 2 s after each hit
  (`hurtAt`, set in `damageHero`) and then fading out over 0.8 s, whatever the hero's life (low life included).
  It is styled apart from the monsters' flat 50 × 4 px bars: 50 × 6 px, rounded, with a thin gold frame
  and a glossy crimson gradient fill (one piece, no segments). From 30 % life down to 0 a soft red glow grows
  around it (a canvas shadow, so it works in Safari too): the halo gets wider (blur 8 → 38 px), stronger (up to
  five passes) and pulses faster. The halo is cast by the bar's own outline, which the bar then covers, so only
  the blur shows: no hard red edge, and the frame stays gold.

- **Top left:** level name (e.g. *The Forsaken Crypt*, *The Ossuary*, … eight names that cycle with a Roman
  numeral after depth 8), the depth number, and gold.
- **Top centre:** name, level and health bar of the hovered or targeted monster (gold name for champions,
  green for bosses).
- **Top right:** minimap.
- **Bottom left:** the **attack globe** (always shown), and above it a message log (6 lines, each fading after
  6 s). The globe is a dark steel disc with a gold rim and an "ATTACK" label, showing the equipped weapon (or
  the potion being used). The icon is as big as the globe's inside (`#atk` `clientWidth`), so only the round
  edge crops it, not the icon's square. On touch screens holding it is the attack modifier (see Controls); a
  mouse press on it does nothing.
- **Touch mode** (`body.touch`): every `pointerdown` records its pointer type; a **touch** press turns touch
  mode on and a **mouse** press turns it off (pen leaves it as it is), so a touch-screen laptop switches as
  you switch between finger and touchpad (it changes how hover tooltips and the action box behave).
- **Bottom right:** the **life orb**. A click or tap on it drinks
  a health potion (the same as `Q`, queued; "No health potions left." when there are none).
- **Burn badge:** while the hero burns, a small flame badge on the life orb's top-left edge shows the seconds of
  burning left, or "in fire" (see [Fire bombs](#fire-bombs)).
- **Bottom centre:** quick-key hotbar and XP bar, between the two globes (see *Fitting* below). The last
  square of the hotbar, set 4 px apart from the keys, is the **Equipment** button (`#menuBtn`, title
  "Equipment (I)"): a 3 × 3 grid of rounded squares drawn in muted gold (`#8c7650`), turning gold on hover. It
  opens and closes the equipment overlay and acts on a touch at once, like the keys (see *HUD taps*). It
  stays when only keys 1–5 are shown.
- Taking damage flashes a red vignette whose strength depends on how big the hit was.
- Descending fades in from black.
- **Phones** (narrow portrait screens: width under 700 px and taller than wide; `fitUI()` on load, on resize
  and when the overlay opens sets `body.narrow`):
  - the attack globe and the life orb move to the **top left** at 76 px (no labels), the orb right of the
    globe (96 px from the left); the level name, depth and gold go below them (94 px from the top) in smaller
    type, and the target bar moves down to 160 px;
  - the minimap shrinks to 120 × 71 px (top right);
  - the message log spans the width above the hotbar
    (112 px from the bottom);
  - the hotbar shows only quick keys **1–5**, bigger (64 px, 58 px icons); keys 6–0 can still be bound and
    used from the equipment overlay or the keyboard;
  - the equipment overlay switches to a 504 px wide layout: paper doll and attributes side by side, the
    inventory below them, quick keys in 2 rows of 5, and no key hint in the header.
- **Fitting** (`fitUI`, on every resize and when the HUD switches between touch and mouse): the hotbar (with
  the XP bar) stays centred when it fits between the attack globe and the life orb (and their labels), 8 px
  from each. Otherwise it is centred in the gap between them and scaled
  down (never up) to fit it. If even that would be under 70 % size, it shows only quick keys 1–5
  (`body.fewkeys`, as in the narrow layout) so the keys stay big enough to tap. The open equipment overlay is
  scaled to fit the width and height minus 12 px (never scaled up; centred).
- **Short landscape screens** (height ≤ 500 px, e.g. a phone turned sideways): the attack globe and the life
  orb shrink to 88 px (labels 10 px), leaving room for the hotbar.

## Music

Six AI-made tracks in `assets/music/` (Google `lyria-3.5`, $0.08 each). The four dungeon tracks are gothic, all
in D minor so they blend when crossfaded:

| Mood | Instrumental (normal) | Choir version (Pit Demon levels) |
|---|---|---|
| Exploration | `explore-instrumental.mp3` (1:24): slow; organ drone, distant low strings, chime bells, a lonely cello, no drums | `explore.mp3` (1:40): the same bed with a hushed Gregorian-style choir: *Descendimus in tenebras, / nox aeterna, lux perdita, / requiem in silentio, / custodes mortuorum vigilant.* |
| Combat | `combat-instrumental.mp3` (1:06): 130 bpm; taiko and war drums, staccato low strings, brass stabs, organ, low horns | `combat.mp3` (1:04): the same with a full choir: *Dies irae, sanguis et ferrum, / mors venit, pugna, pugna! / Gladius in tenebris, / non timebimus mortem.* |

The two **surface** tracks are in the same spirit but cheerful, in D major, with no voices (checked with a
transcription, which came back empty; $0.01):

| Track | Sound |
|---|---|
| `surface-1.mp3` (1:35) | gentle and hopeful: a soft church organ pad, harp and lute arpeggios, pizzicato and warm strings, a wooden flute's folk tune, chime bells, airy reverb |
| `surface-2.mp3` (1:35) | medieval folk at ~90 bpm: lute and harp, a recorder tune, warm cello, soft organ underneath, glockenspiel, a gentle hand drum |

`updateMusic(dt)` runs every frame (from `frame`, outside the game steps) and picks a **mood** (`musicMood`):

- **none** on the title screen and once the hero has died: the music fades out over 1.5 s;
- **boss** while the hero stands in the boss room (`roomAt` of the hero's tile is `G.map.bossRoom`) of a level
  whose boss is a **Pit Demon** and that boss is alive: the choir combat track (`combat.mp3`);
- **combat** from the moment 4 or more living monsters are pursuing the hero (`state === 'chase'`,
  `COMBAT_MIN`) for as long as at least one still pursues; fewer than 4 pursuers never start it. When the last
  pursuers stop because they **lost interest**, it goes on for 6 s more (`COMBAT_HOLD`), so a fight doesn't flick
  between the moods (a pursuer in that time keeps it going); when they stop because they were **killed** (every
  monster that pursued in the previous frame is dead, `MUSIC.chasers`), it ends at once, with the usual 2 s
  crossfade;
- **surface** on the surface (`G.map.surface`): the two surface tracks take turns, `surface-1` on odd plays and
  `surface-2` on even ones (if `surface-2` isn't decoded yet, `surface-1` plays). There are no monsters there,
  so no combat;
- **exploration** otherwise.

**Plays and the choir.** Every start of a track is a *play*, counted per mood and per level (`MUSIC.plays`;
loop repeats count, the boss mood doesn't). The instrumental version plays, except on a **Pit Demon boss level**
(`demonLevel`: `G.map.boss.type === 'demon'`, dead or alive), where the 2nd, 5th and 9th play of each mood
(`CHOIR_PLAYS`) is the choir version. Levels without a Pit Demon boss never use the choir tracks.

**Looping and switching.** When a track is decoded (`musicLoad`), the end of its sound is found: the last 50 ms
block whose level is above ~ -50 dB (RMS 0.003), since the files end in a few seconds' fade-out and silence.
3 s before that point (`MUSIC_XF`) the next play of the same mood starts (0.4 s fade-in) while the old one fades
out over 3 s, so the file's own fade-out overlaps the next start. A change of mood crossfades over 2 s
(`MUSIC_SWITCH`), and so does a **new level** (`G.map` changed): it resets the play counts and restarts the
music with play 1 of the level. The first track of a game fades in over 1.5 s. A track that isn't decoded yet
is tried again the next frame (a choir play falls back to the instrumental one, and still counts).

**Mixing and memory.** Each play is a buffer source with its own gain into a music bus (`MUSIC.bus`), which goes
straight to the output (not through the effects' compressor or reverb). The bus gain is
`0.5 × (v / 100)²` of the **Music** slider, or 0 while sound is off (`N`). A decoded track takes ~35 MB per
100 s, so only the two instrumental tracks are loaded when audio starts, and the choir tracks are loaded on
entering a Pit Demon level and dropped again on a level without one. Likewise the two surface tracks are loaded
only on the surface and dropped on going down.

## Sound

Sounds are synthesised with WebAudio (foley-style), except the ghoul's voice, which is a set of short AI-voiced
clips. Audio starts on the first click (browser autoplay rules); `N` toggles it (music too).

- **Volume.** The **Effects** slider in the equipment overlay sets the master gain: `0.9 × (v / 100)²` (squared so
  the slider feels even to the ear); at 0 no effect is made at all. Releasing the slider plays a coin clink at
  the new level. Both volumes are shared by all heroes, in `localStorage` `dc01-volume` (`VOL`, default
  `{ music: 60, fx: 100 }`, wrapped in `try`).

- **Mixing.** Every sound goes to a master gain through a compressor (so stacked sounds don't clip), with a send
  to a short dungeon reverb (a 1.3 s impulse of decaying, darkening noise, 22 % wet). Sounds with a position
  (monsters, their hits, wraith bolts) get quieter with distance from the hero and are silent beyond 14 tiles
  (`SFX_RANGE`). Rattles, moans, grunts and pick-ups are throttled so they don't pile up.
- **Building blocks** (`sfx`): band-passed noise with a frequency sweep (whooshes), sine drops with low noise
  (thuds), very short high-Q noise bursts (bone and wood knocks), and a hinge
  creak (a jittered, accelerating train of tiny impulses through two narrow resonances).
- **Weapons.** A sword swing is a rising-and-falling whoosh with a thin edge hiss; an axe swing is a lower,
  heavier whoosh. A bow shot is the release, not a musical note: the string slapping to rest (a dull ~140 Hz thwap, a wooden knock and a 0.09 s damped low thrum) and then the arrow's quick falling *fwip*.
- **Hits** depend on the target: bone (skeleton: a thud and knocks), flesh (ghoul, demon) and hide (spider):
  thuds; spirit (wraith): a hollow swish. A broken urn is a crack and scattered shards; the hero being hit is
  a dull thud.
- **Monsters** (`monsterVoice`): a skeleton rattles its bones when it starts chasing, when it attacks, every
  1–3 s while chasing (softer), and falls apart in a clatter when killed. A ghoul moans when it starts chasing
  and every 5–11 s while chasing, grunts when hit, and gives a long, lower moan when killed. Other monsters
  use a generic death sound.
- **World.** A door: the latch, a long hinge creak and the door settling. A chest: the hasp, a shorter, higher
  creak and the lid falling back; a sealed guardian's chest rattles. Picking things up is a faint rustle; gold
  a few faint coin clinks. Potions are gulps, stairs footsteps going down, plus tones for level-ups.
- **Lakes.** Two sounds, each in several versions still being chosen (`SOUND_LOOK`: `drip` 1–4, `splash` 1–3,
  default 1; the sandbox's lake scenario switches them for the page's session). Like other positioned sounds they
  fade with distance and are silent beyond 14 tiles; the reverb is the cave's echo.
  - **Drip** (`drip`, a drop falling into a lake):
    1. *Plink*: a tiny high-passed noise tick (the splash, 0.03 s), the bubble's rising sine plink (900–1500 Hz up
       to 1.9× in 0.14 s, peak 0.3) with a soft octave above, and 0.28 s later the rebound droplet's smaller,
       higher plink (1500–2300 Hz, peak 0.13), matching the second ripple.
    2. *Hollow*: a lower, rounder bubble (480–720 Hz up to 1.6× in 0.26 s, peak 0.34) with a faint fifth, a soft
       low-passed tick, and a lower rebound (800–1100 Hz).
    3. *Glassy*: very high and short (2600–3600 Hz up to 1.35× in 0.05 s, peak 0.2), a faint second tick 0.21 s later.
    4. *Echo*: the plink (peak 0.28), then two discrete, duller cave echoes (triangle waves) 0.19 and 0.39 s later at
       40 % and 18 %.
  - **Bomb splash** (`plunge`, a fire bomb sinking into a lake; much louder and lower than a drip):
    1. *Plunge*: a deep thump (110 → 42 Hz), a dark low-passed rush of water (1800 → 350 Hz, 0.45 s) with a little
       brightness, then five big bubbles (220–380 Hz) from 0.3 s.
    2. *Heavy*: a bright spray sweeping down (4200 → 700 Hz, 0.5 s), a hissing tail of falling droplets (high-passed,
       0.7 s, with seven tiny high plinks), and a low thud.
    3. *Gurgle*: a smaller splash and thump, then a long gurgle: twelve bubbles getting lower and quieter over about
       a second, as it sinks.

  AI sound generation was tried for these: Google's music model (Lyria) returned music (a drone and a beat) rather
  than sound effects, so it isn't used.
- **Fire bombs.**
  - A throw is a soft rising whoosh.
  - The impact is clay breaking (a thud and shards, like an urn), then the oil catching: a deep rushing whoomp.
  - A burning fire crackles: tiny dry pops every 0.06–0.22 s at its position.
  - It also roars: a looping low-passed noise per fire (`updateFireSound`), with its gain following the fire's
    strength and its distance from the hero. It is silent when sound is off or the game isn't running, and stops
    when the fire goes out or the level changes.
- **Ghoul clips** (`assets/sfx/moan1–5.mp3`, `grunt1–2.mp3`): Google `gemini-3.8-flash-lite-tts` (fractions of
  a cent) with wordless text and a style prompt, e.g. "Uuuuurrrrhhhhhh... hhhuuuurrrrgh." in the voice Algenib,
  styled "a rotting undead ghoul: a long, low, wet guttural moan, raspy and breathy, no words, slow" (raw takes in
  `tools/raw/sfx`). `tools/cut_sfx.py` splits each take at its quiet gaps into clips, fades and normalises them
  and saves 64 kbit/s MP3s. The game plays a random clip at 0.82–1× speed (0.7× for the death moan).

## Assets

The art was generated through the `ai-media-generation` skill in Martin's notes repo: monsters, items, props
and textures with OpenAI `gpt-image-2` (medium quality, about $0.70), and the hero walk cycle with Google
`gemini-3.1-flash-image` (see [Walk cycles](#walk-cycles-hero-skeleton-ghoul)). Total spend so far is about
$3.93 ($0.39 for the surface, $0.22 for the keepers and their stall, $0.08 for the fire bomb designs, $0.07 for the door leaves, $0.07 for the arch-door sheet, about $0.01 for the ghoul voice, $0.26 for the dirt texture, the searched bones and a first door attempt, $0.14 for the newer item icons, $0.07 for the boss-room furnishings, and before that about $0.70 for the original sheets, $0.83 for the hero walk cycle and $0.88 for the skeleton and ghoul
walk cycles, plus small tests; since then $1.58 for the four keepers' walk cycles and about $3.45 for the cast's, OpenAI, see Walk cycles).

- **Background.** `gpt-image-2` can't make transparent backgrounds (and a Gemini test returned an opaque JPEG
  too). Every sprite is therefore generated on flat magenta `#FF00FF` and keyed out by `tools/process_art.py`.
- **Prompt template for characters** (1024 × 1536), with `<subject>` replaced per character:

  > Game sprite sheet, gothic dark fantasy style, isometric 3/4 top-down view. A single `<subject>`, small,
  > full body, walking animation. Strict grid layout: 8 rows and 4 columns, equal-size cells, character
  > centered in each cell, same size and same design in every cell, no text, no labels, no grid lines, no
  > shadows on the ground. Each ROW is one facing direction, top to bottom: facing down toward viewer (south),
  > down-left (southwest), left (west), up-left (northwest), away from viewer (north), up-right (northeast),
  > right (east), down-right (southeast). Each COLUMN is a successive walk-cycle frame. Painterly gothic
  > game-art, muted desaturated colors, strong rim light. Background: perfectly flat solid pure magenta
  > #FF00FF everywhere, no gradient.

- **Subjects:** (there was also a hero knight sheet, "in dark steel plate armor with a tattered crimson cape";
  it, and the skeleton and ghoul sheets, now serve only as design references for their walk cycles)
  - undead skeleton warrior with a rusty sword and a broken round shield, glowing blue eye sockets
  - hunched pale grey ghoul with long claws and torn rags, feral
  - giant black cave spider with eight hairy legs and red eyes, legs moving in a scuttling cycle
  - floating hooded wraith in tattered black robes with ghostly green glow and skeletal hands
  - horned red-black demon brute with bat wings folded and a cleaver, muscular
- **Item icons** (1536 × 1024): a 6 × 4 grid listing the 24 icons in the order of the `META.items` keys
  (weapons, bows, helms, armor, gloves, boots, rings, amulets, potion), on magenta. These are the first 4 rows of
  `items.webp` (6 × 7 cells of 96 px).
- **Fire bombs** (row 8 of `items.webp`, `firebomb1`–`firebomb6`; `tools/raw/firebombs.png`, OpenAI `gpt-image-2`
  medium 1536 × 1024, ~$0.08): a 3 × 2 sheet on magenta of six designs of a hand-thrown fire bomb, "a small
  ceramic container filled with lamp oil, meant to shatter on impact … All unlit: no fire, no flames, no glow".
  Each design is described in [Fire bombs](#fire-bombs). Added by `add_items.py` like the newer icons.
- **Newer item icons** (rows 5–7 of `items.webp`, 18 icons; built by `tools/add_items.py`, ~$0.14):
  - `tools/raw/items2.png`: Google `gemini-3.1-flash-image` `edit` (1K, 3:2) with the old atlas on magenta as a
    style reference, asking for a 6 × 3 sheet of broadsword, bastard sword, knight's greatsword, bearded axe, great
    axe, hunting bow, composite bow, war bow, iron helm, visored helm, studded leather, chain mail, full plate,
    plated gauntlets, heavy gauntlets, greaves, heavy sabatons and a quiver, "in exactly the same art style …
    no glow, no magical effects". It kept the reference's 6 × 4 layout, copied several old icons and painted the
    top rows on dark purple, so `add_items.py` takes only 13 cells (the swords, axes, hunting bow, both helms,
    studded leather, both gauntlets, chain mail and the quiver) and keys each cell against its own border colour
    (flood fill from the border, enclosed background too, plus the magenta key and despill).
  - `tools/raw/items3.png`: OpenAI `gpt-image-2` (medium, 1536 × 1024), a 3 × 2 sheet on magenta for the rest:
    war bow, composite bow, full plate, iron greaves, heavy sabatons (and a belt pouch, unused).
  - The **quiver** icon (`quiver`) isn't used yet; it is meant for limited ammo (todo #15).
- **Dirt and searched bones** (built by `tools/add_props.py`, ~$0.14 for the two used images, ~$0.26 with the
  rejected dirt and the replaced arch-door sheet):
  - `tools/raw/dirt_b.png`: Google `gemini-3.1-flash-image` `edit` (1K, 1:1) with `wall.jpg` and `floor.jpg` as
    style references: "a NEW seamless tileable square texture of dark cave earth: rough packed brown soil with
    embedded stones and pebbles, a few thin roots, crumbly clumps … even flat lighting". It wasn't quite
    seamless, so the script blends it with a half-offset copy of itself. (The other candidate, finer soil from
    OpenAI `gpt-image-2`, was rejected.)
  - `tools/raw/bones_searched.png`: Google `gemini-3.1-flash-image` `edit` (1K, 4:3) of the original bone pile on
    magenta: "the same bones after someone has searched through them … scattered and spread out flat over a
    wider area, a lower and sparser pile". Keyed with `add_items.py`'s `key_cell`, keeping every loose bone,
    scaled to 200 px wide.
  - `tools/raw/doors.png` (~$0.07): Google `gemini-3.1-flash-image` `edit` (1K, 3:2) of a door leaf cut from an
    earlier arch-and-leaf sheet (itself an edit of the original door): "TWO new door leaves … a plain RECTANGLE with
    a flat top (no arch, no stone frame, no threshold, no wall), proportioned 3 wide by 4 tall, thick vertical oak
    planks with iron straps and studs. LEFT: two horizontal iron strap hinges and a ring handle. RIGHT: … an
    iron-banded cross brace and a small barred viewing grate". Each is cropped inside its edge to a fully opaque
    192 × 256 rectangle.
- **Props** (1536 × 1024): a 4 × 2 grid (closed chest, open chest with glowing gold, arched gothic door in a
  stone frame, descending stairway seen from above, lit brazier, skull-and-bone pile, cracked funeral urn,
  gold coin pile), on magenta.
- **The surface** (`tools/add_surface.py`, ~$0.39 with a rejected grass):
  - `tools/raw/grass_a.png`: Google `gemini-3.1-flash-image` `edit` (1K, 1:1) with `floor.jpg` as a style
    reference: "lush dark green grass seen from above, short dense blades with small clumps, a few tiny clover leaves".
    A second grass made the same way copied the floor's flagstones and was dropped.
  - `tools/raw/grass_b.png`: OpenAI `gpt-image-2` (medium, 1024²), no reference: "patchy olive and yellow-green
    meadow grass with short tufts and a few small bare brown earth spots". Both are made seamless as `dirt.jpg` is
    (a half-offset copy blended in over a soft cross).
  - `tools/raw/trees.png` (OpenAI, 1536 × 1024): a 4 × 1 sheet of an oak, a fir, a dead tree and a birch on magenta,
    "each crown clearly above a visible bare trunk section". Cut by columns (the crowns reach past their cells).
  - `tools/raw/bushes.png` (OpenAI, 1536 × 1024): 4 × 2, four bushes and four ground details.
  - `tools/raw/crypt.png` (OpenAI, 1024²): "an old weathered stone CRYPT / mausoleum … on its LEFT visible wall … a
    large arched ENTRANCE … steps leading DOWN into complete darkness".
- **Keepers of the Crypt** (`tools/raw/keepers.png`, OpenAI `gpt-image-2` medium 1536 × 1024, ~$0.08): a 4 × 1
  sheet on magenta of four "ordinary living HUMAN merchant[s] who [have] set up shop deep in a dungeon … Friendly,
  weathered and human, not creepy, not undead, faces clearly visible", standing, facing down-left. A first sheet of
  hooded, skeletal and monk-like keepers (~$0.08) was rejected as too creepy.
- **The keeper's stall** (`tools/raw/keeper_decor.png`, Google `gemini-3.1-flash-image` `edit`, 1K, 3:2, ~$0.07,
  with the props on magenta as a style reference): a 4 × 2 sheet "in exactly the same art style, camera angle …" of a
  trestle table with wares, a weapon rack, an open chest of trinkets, a shelf of potions, crates and sacks, a barrel of
  swords, a lantern on a post and a round red rug. `tools/add_market.py` keys both sheets (`add_items.py`'s
  `key_cell`), scales each figure (keepers 220–230 px tall), and packs them into new rows of `props.webp`. The rug
  spreads past its grid cell into the lantern's, so it is cut from its own columns (x 848–1264, in the gap
  between the two) instead of its cell.
- **Boss-room furnishings** (`decor.png`, Google `gemini-3.1-flash-image` `edit`, 1K, aspect 3:2, ~$0.07):
  the props sheet as a style reference, asking for a new sheet "in exactly the same art style, camera angle,
  lighting, painterly detail and scale": a 4 × 2 grid of a black stone and bone throne with a spiked back, a
  blood-stained altar with a skull and black candles, a wrought-iron candelabrum with lit candles, a heap of
  skulls, a tattered dark green banner with a skull on an iron pole, a broken gothic pillar with rubble, a
  closed stone sarcophagus, and a green summoning circle. The circle isn't used (its six-pointed star read
  like a religious symbol); the game draws its own.
- **Textures** (1024²): "seamless tileable … dark gothic dungeon floor of worn irregular grey flagstones" and
  "… dungeon wall of large rough grey stone blocks with mortar, moss and grime".

**`tools/process_art.py`** (`python process_art.py <raw_dir> <out_dir>`, needs Pillow + NumPy):

- **Soft chroma key:** alpha comes from the "magentaness" `min(r, b) − g`. Edge pixels are un-mixed from the
  key colour, and remaining magenta spill is removed.
- **Fragment cleanup (icons, props):** stray islands from neighbouring cells are dropped. Islands that are
  small, or that touch the cell border, are removed.
- **Monster sheets (spider, wraith, demon):** the AI let figures cross the 4 × 8 grid lines (heads sliced into
  the cell above, legs into the cell below), so frames are *not* cut by the grid. Each figure is a whole
  connected component of the keyed sheet (`components()` from `walk_cycle.py`, specks under 2 % dropped),
  assigned to the cell that holds its centroid; a component wider or taller than 1.4 cells (two touching
  figures) is split along the grid lines. Only the base rows S, SW, W, NW, N are used, and SE, E, NE are their
  horizontal mirrors, because several of the AI's right-facing rows faced the wrong way (for example the
  skeleton's E row faced down-right). One scale per monster makes the 90th-percentile figure height 124 px.
  Each frame goes into a 152 px tall frame with the head-and-shoulders (top 45 %) alpha centroid centred and
  the lowest pixel at `footY + 4` (`footY` = 128); the frame width is the narrowest that fits every frame.
  Saved as WebP.
- **Icons and props:** icons are fitted into 96 px cells; props are scaled to 45 % and packed into a strip.
  If `decor.png` exists, its first 7 cells are found as whole components (`figures()`, so rubble and flames stay
  with their prop), scaled to the same pixel scale (45 % × 1536 / 1264) and appended to the strip.
- **Textures** are resized to 512 px JPEGs.
- **`meta.json`** gets the frame sizes and atlas coordinates. When assets are regenerated, copy its contents
  into the `META` constant in `index.html`.
- `process_art.py` keeps every existing `meta.json` character entry with 8 frames (built by `walk_cycle.py`)
  and skips those characters, so it never overwrites a walk-cycle sheet.

### Walk cycles (hero, skeleton, ghoul)

A single AI image can't be trusted to invent a walk cycle: asked for a whole 8 × 4 direction grid, the model
draws one pose 32 times. So these characters are generated **one direction per image, painted over a pose
guide**. `tools/walk_cycle.py` takes the character as its first argument, and `CHARS` holds each one's gait
and frame settings. The hero is described first; the [skeleton and ghoul](#skeleton-and-ghoul) differences
follow.

- **Pose model.** `tools/walk_cycle.py` has a small 3D stick figure (1.75 m: hips at 0.95 m, 0.46 m thigh and
  shin, 0.17 m foot, arms 0.30 + 0.28 m). Over 8 phases the hip swings ±24° (cosine), the knee bends up to
  52° during swing, and the arms swing ±20° opposite to the same-side leg, with the elbow bending from 18° (arm
  back) to 32° (arm forward) and a fist blob at each hand. The upper body isn't rigid: the pelvis turns ±6° with
  the forward leg, the shoulders counter-rotate ±8°, the upper body shifts 3.5 cm sideways over the stance leg
  (the hips half as much), it leans 4° forward, and the head follows the shoulder motion at 60 %. The figure
  is lowered so its lowest point touches the ground, which gives the natural body bob. It is rotated to the ground facing angle
  (k × 45°) and projected with a 30° camera elevation (the 2:1 dimetric view), and parts are drawn far to near.
  Left limbs are blue and right limbs orange; a red dot marks the face.
- **Placeholders.** A base direction without an AI image falls back to these stick figures, rendered at game
  scale (~118 px tall, ground point at `footY`), so it still animates correctly in the game.
- **Guide** (`python walk_cycle.py guide <CHAR> <DIR> <out.png> --magenta --mannequin`): the 8 poses for one direction
  in a 4 × 2 grid (1200 × 880) on magenta, as a grey mannequin with thicker limbs (dark grey = left, light
  grey = right). Coloured limbs once leaked into the armour, so these sheets used the grey guide.
  `--limbs` instead of `--mannequin` draws one colour per limb (blue left leg, orange right leg, teal left arm,
  yellow right arm, grey torso). In a test on 2026-11-16 (a ranger, NW, `gpt-image-2.6-flare` and
  `gemini-nano-banana-2.1`), with the prompt saying the colours are only a guide and must not appear, nothing
  leaked and the legs followed the guide at least as well as with the grey one. See the `sprite-animation` skill.
  The test's scripts became the skill's tools (`.claude/skills/sprite-animation/tools/`).
- **Generation** (`google_media.py edit`, `gemini-3.1-flash-image`, 1K, aspect 4:3, ~$0.07 per direction). The
  inputs are the guide (as the image being edited), a clean crop of the knight from the original sheet in the
  same view (the original NW row actually faced NE, so that crop is mirrored), and a frame of the finished SW
  knight as the close-up design reference. The prompt names the view (S: front view walking toward the
  bottom; W: strict side profile facing left; NW: three-quarter back view walking to the top-left, face not
  visible; N: back view) and spells out the design (rounded dome great helm with a visor slit, nearly black
  steel with a reddish-brown sheen, red-brown straps, chainmail skirt, dark-red cape draped over both
  shoulders); without the explicit design, the S view drifted to a flat-topped helm and light grey plate. The prompt asks to paint over every mannequin with the knight, keeping each one's exact
  position, size and pose (dark grey = left, light grey = right), to copy only the *design* of the reference
  and not its pose, and to keep the flat magenta background. It also spells out the arms (frame 1 right arm
  forward and left arm back, frame 5 the reverse, frames 3 and 7 arms close to the body, fists at clearly
  different positions) and the torso (shoulders twist against the hips, slight forward lean and shift over the
  supporting leg); without that the model kept the reference's hanging arms and a stiff torso. Giving the
  knight as the main image and the guide only as a reference produced eight nearly identical poses.
- **Cleanup.** The model can leave flat grey mannequin pieces behind (found as large flat, unsaturated
  regions, values 150–240). A second edit pass on the result removes them ("remove the leftover flat grey
  shapes … change nothing else"). Where that also removed a limb, the missing part is copied from the
  neighbouring frame with the same pose (SW frame 2 got its forward right arm from frame 1, aligned on the
  helmet, filling only empty background pixels). `tools/raw/hero_walk_SW.png` is the cleaned result.
- **Build** (`python walk_cycle.py build <CHAR> tools/raw assets`):
  - Each figure is found as a whole connected component of the chroma-keyed image. Components are labelled on
    a 3× downsampled mask, and specks under 2 % of the largest are dropped. Each component is assigned to the
    4 × 2 cell that holds its centroid, so a grid line never cuts a figure (the original sheet had heads sliced
    off into the cell above).
  - One scale per direction: the median ratio of the pose model's bounding-box height to the AI figure's height.
  - Each frame is placed in an `fw × fh` frame (hero 144 × 152). Horizontally, the head-and-shoulders (top 45 %) alpha centroid is
    centred. Vertically, the figure's lowest pixel goes where the pose model's lowest foot is for that frame.
  - Base directions are S, SW, W, NW and N. SE, E and NE are horizontal mirrors of SW, W and NW. Mirroring
    swaps the legs, which in a walk cycle is just a half-stride phase shift.
  - Writes `assets/<char>.webp` and its entry in `assets/meta.json` (hero:
    `{"fw":144,"fh":152,"frames":8,"idle":3,"footY":128,"fpt":5}`), which must be copied into `META` in
    `index.html`.
- **Status:** all five base directions (and so all eight) of the hero use AI art. Every raw image was checked
  for leftover flat-grey guide pieces (none ≥ 150 px remain).

#### Keepers of the Crypt

The four keepers (Aldric, Borin, Mirela, Old Tobias) walk with the same pipeline, `CHARS` `keeper1`–`keeper4`:

| | keeper1 Aldric | keeper2 Borin | keeper3 Mirela | keeper4 Old Tobias |
|---|---|---|---|---|
| frame `fw × fh`, `footY` | 160 × 152, 128 | 168 × 152, 128 | 168 × 160, 136 | 160 × 152, 128 |
| forward lean, knee bend | 3, 0 | 2, 0 | 2, 0 | 10, 8 (stooped) |
| hip swing | 20 | 20 | 17 (long dress) | 15 (short steps) |
| arm swing (left, right) | 8, 16 | 16, 16 | 16, 3 | 10, 3 |
| arm forward offset | 10, 0 | 0, 0 | 0, 12 | 4, 6 |
| base elbow bend | 55, 18 (the pouch) | 20, 20 | 18, 85 (the basket) | 25, 40 (hand on the satchel) |
| `fpt` | 5 | 5 | 5 | 5.5 |

- **Generation:** Google's prepaid credit had run out, so these were made with **OpenAI** `gpt-image-2` `edit`
  (medium, 1536 × 1024, ~$0.075 per direction), with the same three inputs as the monsters: the mannequin guide
  (first, "keep its 4 × 2 layout and its magenta background"), the keeper cut from `tools/raw/keepers.png` (its
  front view, as the design reference) and, for every direction after SW, the first frame of the finished SW sheet.
  It followed the guides as well as Gemini did. The prompt (built per keeper and view) has the same parts as
  the monsters': paint over every mannequin keeping each pose, dark grey = left / light grey = right, the view
  sentence, an explicit design paragraph and what each hand holds, the per-frame legs and arms, "long clothes
  (cloak, coat, dress, apron) swing with the legs", no grey left, flat magenta.
  - Aldric: grey-streaked dark hair and short beard, green scarf, long dark-green hooded cloak with a thick fur
    collar, brown leather jerkin, belt pouches; a coin pouch in the left hand, a small lit lantern on the left hip.
  - Borin: short, stout, bald, a bushy black moustache, cream shirt with rolled sleeves, heavy leather apron; hammer
    and tongs on the left hip, big fists.
  - Mirela: dark curly hair under a deep-blue hooded cloak with gold trim (hood up), long blue dress; a wicker
    basket of potion bottles on the bent right forearm.
  - Old Tobias: stooped, wild white hair, white beard, round spectacles, long brown leather coat, dark scarf; a big
    satchel of scrolls at the right hip on a strap across the chest, the right hand on it.
- **Fixes:** Mirela's NW view first showed her basket in some frames and not in others (it would flicker); it was
  made again with "the basket … must look the SAME in all 8 frames: from this back-left view it is mostly hidden
  behind her body, with only its rim and a few bottle tops peeking out". Her side view reached above the default
  frame, so her frame is 160 tall (ground point 136). Old Tobias's satchel shows on his left side in the back
  views (the model's choice); it stays the same within each direction.
- **Raw images used:** `tools/raw/keeper<N>_walk_<DIR>.png`. In the mirrored rows (SE, E, NE) what a keeper holds
  changes hands.
- **Known flaw (keepers and the cast, except the hunter):** in the side and three-quarter views (SW, W, NW, and
  so SE, E, NE) frames 4–7 were painted like 0–3, so the same leg always leads and the walk glides instead of
  striding; the front and back views alternate only roughly. The hunter has been redone (see The cast); the
  others still have it.
- **Cost:** 21 images, about $1.58.

#### The cast (villagers and nobles)

Eight more walking characters, so far only for the sandbox's character viewer: a **hunter**, a **huntress**, a
**village girl** and a **village boy**, a **duke**, a modest **princess**, a **female blacksmith** (`smithess`) and a
**sorcerer**. Their sheets are not loaded at start-up (`CAST_SRC`, `loadCast`); `CAST_NAMES` names them and
`CAST_SCALE` draws the children smaller (girl 0.7, boy 0.74) and the huntress and princess a little smaller (0.97,
0.95).

- **Designs:** two 4 × 1 front-view sheets on magenta (`tools/raw/cast_design1.png`, `cast_design2.png`), OpenAI
  `gpt-image-2` `edit` with `tools/raw/keepers.png` as the style reference ("EXACTLY the same art style, lighting,
  rendering, camera angle, scale and framing"), ~$0.075 each; each figure was cut out by the columns of
  non-magenta pixels.
- **Walk cycles:** as for the keepers (OpenAI `edit`, the guide, the design crop, the first SW frame), with these
  `CHARS` and what each holds:

| | frame `fw × fh`, `footY` | lean, hip swing | arm swing (left, right) | holds |
|---|---|---|---|---|
| hunter | 176 × 152, 128 | 4, 23 | 6, 18 | a longbow upright in the left hand, a quiver on the back |
| huntress | 176 × 152, 128 | 3, 22 | 6, 18 | the same |
| girl | 144 × 152, 128 | 2, 24 | 18, 10 | wildflowers in the right hand (child proportions) |
| boy | 144 × 152, 128 | 3, 26 | 20, 12 | a wooden toy sword in the right hand (child proportions) |
| duke | 176 × 152, 128 | 0, 19 | 4, 14 | the left hand on his rapier's hilt (elbow 60) |
| princess | 160 × 152, 128 | 1, 16 | 10, 10 | nothing (a long dress, short steps) |
| smithess | 168 × 152, 128 | 3, 21 | 16, 10 | a smith's hammer hanging from the right hand |
| sorcerer | 176 × 176, 152 | 5, 16 | 12, 4 | a staff taller than him in the right hand (elbow 70); a taller frame for it; `fpt` 5.5 |

- **Fixes:** one request failed and was sent again; the female blacksmith's S and N views first lost the hammer and
  were made again with "in ALL 8 frames her RIGHT hand … grips the wooden handle of a heavy iron smith's hammer …
  clearly visible in every frame".
- **Cost:** 2 design sheets and 43 walk images, about $3.45 (OpenAI).
- **The hunter, redone** (Google `gemini-3.1-flash-image` `edit`, 1K, 4:3, about $0.90 for 13 images), because his
  OpenAI sheet had the stride flaw above. The inputs were the guide, `ref_hunter` (the design crop) and the first
  OpenAI SW frame; the prompt (built per view) names the legs **near** and **far** in the side views and spells out
  every frame, with "5: the FAR leg far forward … the NEAR leg far BACK … the OPPOSITE of frame 1, NOT a copy of
  it" and "frames 5–8 must look clearly different from frames 1–4: the legs have swapped places".
  - **W** and **NW** came out right at once (W: in a profile the halves share a silhouette, so it was checked by
    which boot overlaps the other; NW: `stride_check.py`). W kept flat grey guide hands in two frames, removed with
    a second edit ("repaint every flat light grey hand as … a dark brown leather glove … change nothing else").
  - **SW** took five tries. The first was right by `stride_check` except frame 0, and a patch (frame 1 in its
    place) still looked odd in the game: the lower-left boot led in almost every frame, frames 0 and 1 stalled, and
    the head jumped. A try given a W frame as the look reference mixed profile figures in; two given the front-view
    frame came out facing the viewer. The one used gave a three-quarter frame of the first try as the look
    reference, described the legs by picture cues ("1: the NEAR (left) leg steps forward: its boot is planted
    directly BELOW the other boot in the image … 5: the FAR (right) leg steps forward: its boot is planted far to
    the lower LEFT … the boots are WIDE apart left-right, the widest stance of all 8 frames … NOT a copy") and added
    "BODY ANGLE: a three-quarter view exactly like the third reference image: his chest, hips and face are turned
    about 45 degrees to the LEFT … NOT facing the viewer straight on, and NOT in full profile". Its frame 6 is
    painted a little taller, so the head rises about 9 px more on that step.
  - **S** (front view): two tries kept both feet at nearly the same height, with the same foot slightly lower in
    almost every frame, despite describing the feet by image side ("the foot on the RIGHT side of the image … is
    clearly LOWER"). The S row was put together from the two tries' frames by `stride_check`'s *low* measure: the
    four frames whose right-side foot is lower for frames 0–2 and 7, the four whose left-side foot is lower for
    3–6 (all from the second try but frame 7, from the first; the second try's frame 0, which lost the bow, unused).
  - **N** (back view): the second try (the feet described by image side) alternates; the first did not.
  - `tools/stride_check.py` passes all five rows; the old OpenAI SW, W and NW fail it.
  - The look is Gemini's: a little cleaner and more saturated than the other OpenAI-made characters.

#### Skeleton and ghoul

Same pipeline, with these `CHARS` settings (angles in degrees; arm values are left, right):

| | hero | skeleton | ghoul |
|---|---|---|---|
| frame `fw × fh`, `footY` | 144 × 152, 128 | 176 × 152, 128 | 160 × 162, 138 |
| forward lean (rotation of the upper body about the hip axis) | 4 | 4 | 25 |
| constant knee bend (half taken up at the hip, feet kept flat) | 0 | 0 | 24 |
| hip swing amplitude | 24 | 22 | 19 |
| arm swing amplitude | 20, 20 | 5, 12 | 14, 14 |
| constant forward offset of the upper arm | 0, 0 | 12, 4 | 8, 8 |
| base elbow bend (+14 when the arm is fully forward) | 18, 18 | 75, 28 | 14, 14 |
| `fpt` (frames per tile) | 5 | 5 | 5.5 |

The skeleton's left forearm is held bent in front (the shield) and barely swings, and the sword arm has a
short swing. The ghoul is hunched with bent knees, a shorter stride, and arms dangling in front.

- **Generation:** the same edit call with three inputs: the mannequin guide, a crop of the monster from its
  original sheet in the same view (cut with the component method above), and, for every direction after SW, a
  frame of the finished SW sheet as the close-up design reference. The prompt follows the hero's (paint over
  every mannequin, keep each pose, dark grey = left and light grey = right, the same per-frame leg
  description, copy only the design), with a per-monster design and motion text:
  - skeleton: aged brownish-bronze bones, glowing pale-blue eye sockets, rusted bronze shoulder and chest
    pieces, tattered loincloth; a rusty sword in the right hand (light grey arm) and a round wooden shield
    with an iron rim on the bent left forearm (dark grey arm), which barely moves.
  - ghoul: emaciated, pale grey-brown skin over ribs and sinews, long matted white-grey hair, gaping mouth,
    long black claws, ragged loincloth, bare feet; strongly hunched, knees always bent, arms dangling loosely
    in front.
  - views: S "front view, walks straight toward the viewer"; SW "three-quarter view, walks toward the viewer
    and to the left"; W "strict side profile, walks to the left, we see only its left side"; NW "three-quarter
    back view, walks away and to the left, face hidden"; N "back view, face not visible".
- **Fixes:** S (both monsters) left flat grey mannequin legs behind several figures; the cleanup pass removed
  them, repainting each as the monster's leg. Skeleton W twice came out with a second shield at its back; a
  cleanup pass removed it (the second row lost its shoulder armour). Ghoul N stays upright from behind even
  when the hunch is spelled out; it is used as is, and the ghoul's taller frame keeps it from being clipped.
- **Raw images used:** `tools/raw/skeleton_walk_<DIR>.png` and `tools/raw/ghoul_walk_<DIR>.png`. In the
  mirrored rows (SE, E, NE) the skeleton holds its sword in the left hand.
