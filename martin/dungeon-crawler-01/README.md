# Dungeon Crawler 01 — "Crypt of Endless Night"

An isometric, gothic dungeon crawler in a single `index.html` (vanilla JavaScript, HTML5 canvas, no build step).
A lone knight descends an endless crypt, fighting monsters that grow stronger on every level, collecting
and equipping gear, and levelling up. All art is AI-generated (see [Assets](#assets)).

## Files

| Path | Purpose |
|---|---|
| `index.html` | The whole game: markup, CSS, and JavaScript. Asset metadata (`META`) is inlined so the page also works from `file://`. |
| `assets/hero.webp`, `skeleton.webp`, `ghoul.webp` | 8-direction × 8-frame walk cycles (transparent). |
| `assets/spider.webp`, `wraith.webp`, `demon.webp` | 8-direction × 4-frame monster sprite sheets (transparent). |
| `assets/items.webp` | 6 × 7 atlas of 96 px item icons (`ATLAS_W` × `ATLAS_H`; rows 1–4 from `process_art.py`, rows 5–7 from `add_items.py`). |
| `assets/props.webp` | Props: row 1 has the chest, open chest, door, stairs, brazier, bones, urn and gold, and the boss-room furnishings (throne, altar, candelabrum, skull pile, banner, pillar, sarcophagus), from `process_art.py`; row 2 has the searched bones (`bonesused`) and the door leaves (`doorA`, `doorB`), from `add_props.py`. |
| `assets/floor.jpg`, `assets/wall.jpg` | 512 px seamless floor and wall textures. |
| `assets/dirt.jpg` | 512 px seamless dirt texture for wall tops and wall faces toward solid ground (from `add_props.py`). |
| `assets/meta.json` | Frame sizes and atlas coordinates written by the processing script (copied into `META` in `index.html`). |
| `tools/process_art.py` | Turns the raw AI images for the 4-frame monsters, items, props and textures into the files above (chroma-key, slicing, packing). Imports `walk_cycle.py`. |
| `tools/walk_cycle.py` | Walk-cycle pipeline (hero, skeleton, ghoul): renders the 3D stick-figure pose guides and placeholders, and builds the 8-frame sheets. |
| `tools/add_items.py`, `tools/raw/items2.png`, `items3.png` | Appends the icons of the newer item types (and a quiver) to `assets/items.webp` from the two raw sheets, and updates `assets/meta.json` and the inline `META`. See [Assets](#assets). |
| `tools/add_props.py`, `tools/raw/bones_searched.png`, `doors.png`, `dirt_b.png` | Adds row 2 of `assets/props.webp` (searched bones, door leaves) and makes `assets/dirt.jpg` seamless; updates `assets/meta.json` and the inline `META`. |
| `tools/cut_sfx.py`, `tools/raw/sfx/` | Cuts the AI-voiced ghoul takes into the clips in `assets/sfx/`. |
| `assets/sfx/` | Ghoul moans and grunts (MP3). |
| `tools/raw/<char>_walk_<DIR>.png` | The raw AI walk-cycle images (`hero`, `skeleton`, `ghoul` × `S`, `SW`, `W`, `NW`, `N`) the 8-frame sheets are built from. |
| `catalog.html` | Monster and item catalog (bestiary, armory, potions, affixes, rarity, and what first appears at each depth), with sprites from `assets/`. **Generated** by `tools/catalog/build.js`: see [Catalog](#catalog). |
| `tools/catalog/` | `build.js` (reads the game's data in a headless browser and writes `catalog.html`) and `template.html` (the catalog page, edit this one). |
| `tools/simulation/` | Balance simulation: `simulate.js` runs simulated heroes through the real game and reports how hero and monsters compare per depth. How to use it: [`tools/simulation/README.md`](tools/simulation/README.md); dated results with conclusions: `results-YYYY-MM-DD.md`. |
| `todo.md` | Numbered list of ideas for future work (not yet implemented). |
| `backup/index.NN.html` | Old snapshots of `index.html`, numbered `01`, `02`, … in the order they were made; not used by the game and not described by this README. `index.01.html` is an early version of the game. |

## Version

`VERSION` (an integer near the top of the script) is shown muted at the bottom right of the title screen as `v<N>`.
**Increment it before every push**, so a player can tell whether the page they have open is up to date.

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
| Double click / double tap on an item on the floor | Walk to it, pick it up and equip it at once; what it replaces goes into the pack slot it took. Needs a free pack slot, unless the item's equipment slot is empty (then it goes straight on). Potions are just picked up. |
| Right click, or `Shift` + left click, or a tap while a finger rests on the attack button (touch) | Attack with the equipped weapon (see [Combat](#combat)). Hold to keep attacking. |
| `I`, `C` or `Tab` | Toggle the equipment overlay (`Esc` closes it). |
| `1`–`9`, `0` | Quick keys: equip the bound weapon or use the bound potion (both are queued; see [Actions](#actions)). |
| `Q`, or a click / tap on the life orb | Drink a health potion (queued like a quick key). |
| `M` | Toggle the minimap. |
| `N` | Toggle sound. |
| `Ctrl` + `D` | Toggle the debug overlay (see [Debug overlay](#debug-overlay)). |
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

The title screen lists the controls and is also the hero picker (see [Saving](#saving)). A level-1 level is
rendered behind it. The start button is enabled once all images have loaded.

## Saving

Progress is saved in the browser's `localStorage` under one key, `crypt-of-endless-night.save`:
`{ v: 1, last: <id of the hero played last>, heroes: { <id>: entry } }`, where an entry is
`{ id, name, depth, lvl, saved: <timestamp>, hero: { name, lvl, xp, base, equip, inv, gold, hotkeys, kills, hp } }`.
Items are plain data, so the hero's equipment, pack (potion stacks included) and quick keys are stored as they are.
**Older saves** kept health potions as a counter (`hero.potions`) and a `{ type: 'potion' }` quick key; on loading,
the counter becomes a health potion stack in the first free pack cell (if the pack is full, the stack is dropped
on the floor at the start of the level), with an id after the highest saved one, and the key becomes a
`{ type: 'use', pot: 'health' }` key. Items from before regeneration was removed lose their life regen bonus,
and an old *Bone Talisman* gets the current crit bonus instead (`3 × (1 + 0.1·(item level − 1))`, rounded; items from before fixed item stats carry an `ilvl`).
The iron skin effect is not saved. Every read and write
is wrapped in `try`; if storage is unavailable the game still plays, logs that progress could not be saved,
and the picker shows no saved heroes.

- **When it saves:** when a hero is created (at depth 1), and automatically on arrival at each new depth
  (after the descend XP; the log says "Progress saved."). Nothing else is saved: not the level layout, and
  nothing gained or lost partway through a level.
- **Hero picker** (the title screen): one button per saved hero, most recently saved first, showing name,
  level and depth, plus **New Hero**. The selected button has a gold border; the hero played last (or the
  newest) is selected at start. Clicking a selected hero (or the button below) starts it.
  - **Resuming** generates a *new* layout for the saved depth and restores the saved hero with the life it had
    when saved (capped at max life; saves made before life was saved start at full life). Item
    ids continue after the highest saved one, so new drops never clash with owned items.
  - **New Hero** shows a name field (up to 20 characters, spaces collapsed; empty names are refused with a red
    border), and the button becomes **Begin** (Enter also works). The new hero starts at level 1 on depth 1
    with the starting kit, and is saved at once.
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
  device-pixel ratio (max 2).
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
  redrawn 4× per second. Walls are tan, doors brown, floor dark, the stairs gold, and the hero red.

## Main loop

A `requestAnimationFrame` loop runs update → render → HUD every frame, with `dt` capped at 50 ms. The next
frame is scheduled *before* the work. Update and render run inside a `try/catch`: if something goes wrong, the
canvas state is reset, the first error is logged to the console, and the game keeps running instead of
freezing.

## Dungeon generation

Each depth `d` gets a freshly generated level.

- Map size `min(44 + 2d, 80)` square. Up to `min(9 + ⌊d/2⌋, 18)` rectangular rooms of 5–10 × 5–10 tiles,
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
- **Big rooms.** Right after the start room, the generator places this depth's big rooms, each 11–14 tiles a
  side (about 2.8× the area of a normal 5–10 room): first the boss room (if the depth has one), then the big
  room (if it has one). They get the first 300 placement tries; one that doesn't fit falls back to an existing
  room (see below).
- **Boss room** at depth 3 (`BOSS_ROOM_FROM`) and from depth 6 (`BOSS_FROM`) on (`bossRoomAt`); depths 1–2 and
  4–5 have none, and no boss. If the big boss room doesn't fit, the room with the largest
  `area × (BFS distance from the start + 10)` other than the start, stairs and big rooms is used instead. The
  stairs never go in it. **At depth 3 it stands empty**, a premonition of what is to come: only the rune circle,
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
  grey) on its edge, and a larger pack of easier monsters: `5–7 + ⌊(d − 3)/2⌋`, never champions, of the types
  unlocked at depth `d − 4` or earlier, skeletons always allowed and weighted ×3 (depth 3: skeletons only;
  depth 5: skeletons, ghouls, spiders; depth 7: also wraiths).
- **The lone demon** (depth 4, `DEMON_ROOM_AT`): one random normal room (not the start room) holds a single
  Pit Demon (normal tier, never a champion) and nothing else, a foretaste before demons appear from depth 5.
- **Green banners.** Every room joined to the boss room by a corridor (also at depth 3, where it stands empty)
  gets a banner (the normal banner sprite: dark green with a skull) on its edge, as close as possible to the mouth
  of that corridor: the room's last tile on the carved corridor's way toward the boss room (corridors are
  recorded with their tiles; with several corridors to the boss room, the first counts). The spot follows the
  usual edge rule (solid wall behind it, no doorway next to it), so it never blocks the corridor.
- **Green brazier.** When there is a boss room, with 50 % chance one room joined to the boss room by a corridor gets an extra brazier
  with green flames, a hint of what lies next door.
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
  circle's bounding box are on walkable tiles: floor or open door, with no blocking prop. Movement resolves
  the x and y axes separately, so entities slide along walls.
- **A\*** runs on the 8-connected tile grid with a binary heap and octile heuristic. Diagonal steps are not
  allowed past corners. A "near" mode stops on any free tile adjacent to the goal; it is used for walking up
  to blocking props, doors and monsters.
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
  the hero's armor for 30 s. Using one takes 0.4 s of the hero's action time (see [Actions](#actions)).
- **Death** returns to the title screen with the fallen hero selected; the hero resumes from its last save
  (see [Saving](#saving)).

## Combat

**Damage dealt by the hero:**

`weapon roll (min–max) × (1 + 0.02·STR) × (1 + damage% / 100)`

Bows use DEX instead of STR. One roll is made per target hit.

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

**Ranged (bows).** A right click fires an arrow at the hovered monster, or toward the cursor. Arrows travel
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
| Skeleton Warrior | 26 | 3–6 | 5 | 2.5 | 1.2 s | 16 | 1 |
| Ghoul | 20 | 2–5 | 2 | 3.3 | 0.9 s | 13 | 1 |
| Cave Spider | 15 | 2–4 | 1 | 3.9 | 0.8 s | 11 | 1 |
| Wraith (ranged) | 22 | 4–7 | 3 | 2.3 | 1.9 s | 22 | 3 |
| Pit Demon | 75 | 8–13 | 12 | 2.1 | 1.5 s | 60 | 5 (one lone demon at depth 4) |

Spawn weights are 3 : 3 : 2 : 2 : 1 in table order. Every monster's speed is the table value × 0.85 (`MON_SPEED`):
2.1 / 2.8 / 3.3 / 2.0 / 1.8 tiles/s at depth 1, so the hero (4.2) can outrun them all. Life and damage in the table are base values: at depth 1 a
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
| Occurs | always | 10 % of monsters of a type at least 4 depths past its first depth (`canChamp`; none at depths 1–4; never in the big room, the lone demon or as escorts) | one per level from depth 6, in the boss room |
| Name | type name | prefix + type, e.g. *Dread Ghoul* | *&lt;name&gt;, &lt;type&gt; Tyrant*, e.g. *Morgrath, Ghoul Tyrant* |
| Life / damage / XP | ×1 | ×2.5 / ×1.5 / ×3 | ×8 / ×1.8 / ×8 |
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
(`lvl`). The loot depth is the current depth, + 1 for champions' and the boss's loot and 30 % of chest items. Every
type has its own icon.

| Item | Type | Stats | Unlocks at |
|---|---|---|---|
| Short Sword | sword | 4–8, 0.55 s | 1 |
| Longsword | sword | 7–14, 0.65 s | 2 |
| Broadsword | sword | 13–22, 0.7 s | 4 |
| Blackened Greatsword | sword | 20–34, 0.85 s | 6 |
| Bastard Sword | sword | 24–40, 0.8 s | 8 |
| Knight's Greatsword | sword | 32–52, 0.85 s | 11 |
| Hand Axe | axe | 5–10, 0.7 s | 1 |
| Bearded Axe | axe | 10–18, 0.8 s | 3 |
| Battle Axe | axe | 17–29, 0.9 s | 5 |
| Executioner's Axe | axe | 26–46, 1.05 s | 7 |
| Great Axe | axe | 34–58, 1.05 s | 10 |
| Short Bow | bow | 3–7, 0.6 s | 1 |
| Hunting Bow | bow | 5–10, 0.65 s | 2 |
| Yew Longbow | bow | 9–16, 0.75 s | 4 |
| Bone Bow | bow | 14–25, 0.9 s | 6 |
| Composite Bow | bow | 18–31, 0.85 s | 8 |
| War Bow | bow | 25–42, 0.9 s | 11 |
| Leather Cap | helm | armor 3 | 1 |
| Iron Helm | helm | armor 7 | 3 |
| Horned Great Helm | helm | armor 13 | 6 |
| Visored Helm | helm | armor 19 | 9 |
| Leather Tunic | armor | armor 6 | 1 |
| Studded Leather | armor | armor 11 | 3 |
| Chain Mail | armor | armor 18 | 5 |
| Plate Cuirass | armor | armor 28 | 8 |
| Full Plate | armor | armor 36 | 11 |
| Leather Gloves | gloves | armor 2 | 1 |
| Iron Gauntlets | gloves | armor 6 | 3 |
| Plated Gauntlets | gloves | armor 10 | 7 |
| Heavy Gauntlets | gloves | armor 13 | 10 |
| Leather Boots | boots | armor 2, +5 % move speed | 1 |
| Plated Boots | boots | armor 6 | 3 |
| Iron Greaves | boots | armor 10 | 7 |
| Heavy Greaves | boots | armor 13 | 10 |
| Silver Ring, Ruby Ring, Grave Ring | ring | none | 1 |
| Sapphire Amulet, Blood Amulet, Bone Talisman | amulet | none | 1 |

**Choosing a drop** (`genItem`): the rarity is rolled first (see below). Then a **group** is drawn evenly from
sword, axe, bow, helm, armor, gloves, boots, ring and amulet, and then a type of that group unlocked at the loot
depth, older types less likely (weight × 0.5 for every 4 depths since the type unlocked; e.g. at loot depth 6 a
sword is a Blackened Greatsword 38 % of the time, a Short Sword 16 %).

**Rings and amulets** have no stats of their own: they only drop as **magic or rare** items (a common roll never
picks them), and all their worth is in their affixes, whose ranges are doubled on them (`JEWEL_MULT`). With the
rarity gates below they appear from depth 3 at the earliest (amulets from depth 5, `AMULET_FROM`; rings from 3,
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

**Rarity gates by depth.** No magic items before depth 3 (`MAGIC_FROM`) and no rares before depth 6 (`RARE_FROM`);
a roll above what the depth allows is lowered to the best allowed rarity. Some sources count as deeper for these
gates (and for the ring and amulet gates): **champions** + 1, **chests in the big room** + 1, the **boss** and the
**guardian's chest** + 2. So a champion can drop magic items from depth 2 and rares from depth 5.

**Affixes** are the bonuses of magic and rare items: **prefixes** go before the type's name, **suffixes** after it.
Each kind has 3 tiers with fixed ranges and their own names. A tier can roll once the loot depth reaches 1, 5 or 9
(`AFFIX_FROM`); among the unlocked tiers, higher ones are likelier (weights 1 : 2 : 4). A kind appears at most once
per item. On rings and amulets every range is doubled.

| Stat | Tier 1 (from 1) | Tier 2 (from 5) | Tier 3 (from 9) |
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
chests 27 %, urns 10.8 %. The guardian's chest's guaranteed item is not thinned.

| Source | Drops (item chances before `LOOT`) |
|---|---|
| Monster | 13 % item, 6.75 % × 1.2 potion, 30 % gold (2–8 × d) |
| Champion | an item of loot depth d+1 (boost 0.35), plus a 50 % chance of a second (boost 0.2); rarity gates at d+1 |
| Boss | an item of loot depth d+1 (boost 0.35, rarity gates at d+2), gold (20–40 × d), plus the normal potion / gold rolls of a monster |
| Chest | 1–3 items (boost 0.15, 30 % chance of loot depth d+1; in the big room rarity gates at d+1), gold (10–30 × d), 22.5 % × 1.2 potion |
| Guardian's chest | **always** one item of loot depth d+1 that is rare (30 %) or else magic (rarity gates at d+2), gold (30–60 × d), plus everything a normal chest drops |
| Urn | 35 % gold, 9 % × 1.2 potion, 8 % item |
| Bones | 20 % gold, 10 % item |

**Guardian's chest.** It glows green and is labelled *Guardian's Chest* on hover. While the boss lives it is
sealed: clicking it only logs "The chest is sealed while its guardian lives." When the boss dies, the log says
"<boss> is destroyed. The guardian's chest unseals."

Dropped things land on nearby free tiles. Floor items bob, glow in their rarity colour (potions in their
potion colour), and show a name label when within 7.5 tiles. Gold is counted at the top left.

## Equipment overlay

Opened with `I` / `C` / `Tab` or the **Equipment (I)** button, closed with the same keys, `Esc`, the button,
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
- **Attributes:** level, XP, STR / DEX / VIT, life (live), armor, damage range, attack speed, crit,
  move speed, kills, gold.
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
game paused or running; the browser's bookmark shortcut is suppressed). Its switches are remembered in
`localStorage` (`dc01-debug`, wrapped in `try`):

- **Pursuit indicator** — a red dot (5 px, black outline) above every monster that is pursuing the hero
  (`state === 'chase'`).

## HUD

- **Top left:** level name (e.g. *The Forsaken Crypt*, *The Ossuary*, … eight names that cycle with a Roman
  numeral after depth 8), the depth number, and gold.
- **Top centre:** name, level and health bar of the hovered or targeted monster (gold name for champions,
  green for bosses).
- **Top right:** minimap.
- **Bottom left:** the life orb, and above it a message log (6 lines, each fading after 6 s).
- **Touch mode** (`body.touch`): every `pointerdown` records its pointer type; a **touch** press turns touch
  mode on and a **mouse** press turns it off (pen leaves it as it is), so a touch-screen laptop switches as
  you switch between finger and touchpad. In touch mode an **attack button** appears in the life orb's place:
  round and the orb's size, a dark steel disc with a gold rim showing the equipped weapon's icon (or the
  potion being used) (80 px; 52 px
  on phones) and an "ATTACK" label below. Holding it is the attack modifier (see Controls). The life orb slides
  right next to it (to 156 px from the left), so the finger on the button never covers it.
- **Life orb:** a click or tap on it drinks a health potion (the same as `Q`, queued; "No health potions
  left." when there are none).
- **Bottom centre:** quick-key hotbar and XP bar.
- **Bottom right:** Equipment button.
- Taking damage flashes a red vignette whose strength depends on how big the hit was.
- Descending fades in from black.
- **Phones** (narrow portrait screens: width under 700 px and taller than wide; `fitUI()` on load, on resize
  and when the overlay opens sets `body.narrow`):
  - the life orb moves to the **top left** at 76 px (no "LIFE" label), with the level name, depth and gold to
    its right in smaller type; in touch mode the attack button (76 px) takes the top-left corner, the orb sits
    right of it (96 px from the left), the level name, depth and gold move below them (94 px from the top),
    and the target bar moves down to 160 px;
  - the minimap shrinks to 120 × 71 px (top right), with the Equipment button below it;
  - the target bar moves down to 120 px from the top; the message log spans the width above the hotbar
    (112 px from the bottom);
  - the hotbar shows only quick keys **1–5**, bigger (64 px, 58 px icons); keys 6–0 can still be bound and
    used from the equipment overlay or the keyboard;
  - the equipment overlay switches to a 504 px wide layout: paper doll and attributes side by side, the
    inventory below them, quick keys in 2 rows of 5, and no key hint in the header.
- **Fitting:** on any screen, the hotbar (with the XP bar) is scaled down to fit the width minus 16 px, and
  the open equipment overlay to fit the width and height minus 12 px (never scaled up; centred).

## Sound

Sounds are synthesised with WebAudio (foley-style), except the ghoul's voice, which is a set of short AI-voiced
clips. Audio starts on the first click (browser autoplay rules); `N` toggles it.

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
- **Ghoul clips** (`assets/sfx/moan1–5.mp3`, `grunt1–2.mp3`): Google `gemini-3.8-flash-lite-tts` (fractions of
  a cent) with wordless text and a style prompt, e.g. "Uuuuurrrrhhhhhh... hhhuuuurrrrgh." in the voice Algenib,
  styled "a rotting undead ghoul: a long, low, wet guttural moan, raspy and breathy, no words, slow" (raw takes in
  `tools/raw/sfx`). `tools/cut_sfx.py` splits each take at its quiet gaps into clips, fades and normalises them
  and saves 64 kbit/s MP3s. The game plays a random clip at 0.82–1× speed (0.7× for the death moan).

## Assets

The art was generated through the `ai-media-generation` skill in Martin's notes repo: monsters, items, props
and textures with OpenAI `gpt-image-2` (medium quality, about $0.70), and the hero walk cycle with Google
`gemini-3.1-flash-image` (see [Walk cycles](#walk-cycles-hero-skeleton-ghoul)). Total spend so far is about
$3.24 ($0.07 for the door leaves, $0.07 for the arch-door sheet, about $0.01 for the ghoul voice, $0.26 for the dirt texture, the searched bones and a first door attempt, $0.14 for the newer item icons, $0.07 for the boss-room furnishings, and before that about $0.70 for the original sheets, $0.83 for the hero walk cycle and $0.88 for the skeleton and ghoul
walk cycles, plus small tests).

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
  grey = right). Coloured limbs leaked into the armour, so the guide is grey.
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
