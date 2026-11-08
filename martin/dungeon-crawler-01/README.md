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
| `assets/items.webp` | 6 × 4 atlas of 96 px item icons. |
| `assets/props.webp` | Horizontal strip of props (chest, open chest, door, stairs, brazier, bones, urn, gold) and boss-room furnishings (throne, altar, candelabrum, skull pile, banner, pillar, sarcophagus). |
| `assets/floor.jpg`, `assets/wall.jpg` | 512 px seamless floor and wall textures. |
| `assets/meta.json` | Frame sizes and atlas coordinates written by the processing script (copied into `META` in `index.html`). |
| `tools/process_art.py` | Turns the raw AI images for the 4-frame monsters, items, props and textures into the files above (chroma-key, slicing, packing). Imports `walk_cycle.py`. |
| `tools/walk_cycle.py` | Walk-cycle pipeline (hero, skeleton, ghoul): renders the 3D stick-figure pose guides and placeholders, and builds the 8-frame sheets. |
| `tools/raw/<char>_walk_<DIR>.png` | The raw AI walk-cycle images (`hero`, `skeleton`, `ghoul` × `S`, `SW`, `W`, `NW`, `N`) the 8-frame sheets are built from. |

## Controls

| Input | Action |
|---|---|
| Left click on floor | Walk there (A* pathfinding). Holding the button keeps walking toward the cursor. |
| Left click on chest / door / urn / bones / gold / item / stairs | Walk to it and act on it: open, break, search, pick up, or descend. |
| Right click, or `Shift` + left click, or a tap while a finger rests on the attack button (touch) | Attack with the equipped weapon (see [Combat](#combat)). Hold to keep attacking. |
| `I`, `C` or `Tab` | Toggle the equipment overlay (`Esc` closes it). |
| `1`–`9`, `0` | Quick keys: equip the bound weapon or drink a potion. |
| `Q`, or a click / tap on the life orb | Drink a health potion. |
| `M` | Toggle the minimap. |
| `N` | Toggle sound. |
| Mouse wheel | Zoom (0.6×–1.5×). |

**Touchpads and touch screens.** A *modifier* turns any left click or tap into a right click, everywhere a
right click does something: attacking in the game view, dropping a pack item and clearing a quick key. The
modifier is the `Shift` key, or, on a touch screen, a finger resting on the **attack button** (its rim glows
gold while it is held). The game view and the button use pointer events (mouse, touchpad, touch and pen alike) with
`touch-action: none`, so a finger held on the screen keeps walking or attacking and dragging doesn't scroll
or zoom the page.

- Each press remembers its `pointerId` (and, for a mouse, which button), so with several fingers down,
  lifting one never ends another's press: lifting the attack-button finger doesn't stop a walk or an attack already
  under way, and a press that started as a right click stays one until it is released.
- A second mouse button pressed or released while another is held arrives as a `pointermove` with
  `e.button` set (a "chorded" press), so the game treats those as presses and releases too. Holding left to
  walk and then holding right attacks, as before.

The title screen lists the controls and is also the hero picker (see [Saving](#saving)). A level-1 level is
rendered behind it. The start button is enabled once all images have loaded.

## Saving

Progress is saved in the browser's `localStorage` under one key, `crypt-of-endless-night.save`:
`{ v: 1, last: <id of the hero played last>, heroes: { <id>: entry } }`, where an entry is
`{ id, name, depth, lvl, saved: <timestamp>, hero: { name, lvl, xp, base, equip, inv, potions, gold, hotkeys, kills, hp } }`.
Items are plain data, so the hero's equipment, pack and quick keys are stored as they are. Every read and write
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
- **Death:** after a short pause the title screen returns with the fallen hero selected and a message
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
- **Walls** are 72 px tall blocks (`WALLH`), except **front (south) walls**: any wall or door tile with walkable
  floor (floor or an open door) behind it, at `x − 1`, `y − 1` or the diagonal `(x − 1, y − 1)`, is drawn as a
  **low lip** 22 px tall (`LIPH`, under half a tile's height), so it marks the wall but never hides the floor or
  anyone on it. Back walls stay full height; nothing is ever drawn transparent. Only the two faces facing the
  viewer (+y and +x) are drawn, and only where the neighbour on that side isn't a wall at least as tall (so a
  tall wall shows its face above a lower lip next to it). Faces are affine-mapped slices of the wall texture,
  picked per tile so the pattern varies; a lip uses the bottom 22/72 of the texture (or of the door sprite) at
  the same scale rather than squashing it. The left face is shaded 42 %, the right 18 %, and the top is a dark
  cap (slightly lighter on a lip, with a brighter edge line).
- **Doors** are wall blocks whose passage-facing face shows the door sprite. A door between walls on x±1 shows it
  on the +y face; one between walls on y±1 shows it on the +x face. Opened doors become plain floor.
- **Depth sorting.** Walls, props, monsters, the hero and projectiles are sorted by `x + y`. A wall or prop on
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
  **mounds** (skull pile, bones) 0.2w above, 0.58w × 0.28w; **posts** (brazier, candelabrum, banner, pillar,
  urn) 0.08w above, 0.46w × 0.21w. Stairs and gold have none. A prop with `flip` (a throne on the right back
  wall) is drawn mirrored.
- **Green brazier** (see Dungeon generation): drawn with `hue-rotate(80deg) saturate(1.4)`, with green embers.
- **Rune circle** in the boss room: drawn on the floor, centred on the room, radius 0.24 × the room's shorter
  side. Static (no animation): a very faint green radial glow out to 1.45 × the radius, then two thin
  concentric rings, 24 rune ticks between them (every third one longer) and three arcs inside, in a muted green
  (40 % opacity), heavily blurred (`blur(3px)` plus a 26 px green shadow blur), all additive (`lighter`).
- **Effects.** Melee swings draw a sweeping crescent arc in the attack direction. Arrows are drawn as shafts with
  a tip, and wraith bolts as glowing green orbs. Hits spray blood-coloured sparks (green for wraiths), urns
  burst into shards, and level-ups emit an expanding golden ring.
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
- Each room is joined to the nearest earlier room by an L-shaped, 1-wide corridor, so the whole level is
  connected. `2 + ⌊d/4⌋` extra random corridors add loops.
- Every void tile next to floor (8-neighbourhood) becomes a wall.
- **Doors.** A corridor tile in a room's surrounding ring, with void on both sides along the ring, is a door
  candidate. Each candidate becomes a closed door with 55 % probability.
- **Stairs down** are placed in the centre of the room farthest from the start room (by BFS walking distance),
  never the boss room.
  The hero starts in the centre of the first room, which never has monsters or chests.
- **Props per room:**
  - brazier: 75 % chance, always in the start room; blocking
  - chest: 38 % chance; blocking
  - urns: 0–2; blocking
  - bones: 0–2
  - gold pile: 20 % chance, worth 3–12 × d × `LOOT`
- **Boss room** (from depth 3, `BOSS_ROOM_FROM`; depths 1 and 2 have none, and no boss). From depth 3 the
  second room placed is the boss room, 11–14 tiles a side (about 2.8× the area of a normal
  5–10 room; it gets the first 300 placement tries, and if it doesn't fit, the room with the largest
  `area × (BFS distance from the start + 10)` other than the start and stairs rooms is used instead). The stairs
  never go in it. **At depth 3 it stands empty**, a premonition of what is to come: only the rune circle, the
  braziers and the furnishings, with no boss, guards, champion or guardian's chest. From depth 4
  (`BOSS_FROM`) it holds:
  - the boss on the centre tile, standing on the **rune circle** (see Rendering);
  - at least 4 ordinary braziers and a **guardian's chest**, on the edge (blocking);
  - furnishings (non-interactive), each type only from its unlock depth (`DECOR_FROM`): 3 skull piles on
    inner tiles (not blocking) and 2 banners from depth 3, 2 candelabra from depth 4, 2 broken pillars from
    depth 5, a sarcophagus from depth 6, an altar from depth 7, and a throne from depth 8, all on the edge
    (blocking). The throne's sprite faces down-right (+x), so it always goes against a back wall, facing into
    the room: on the left back wall (`x = r.x`) as drawn, or on the right back wall (`y = r.y`) mirrored, never
    in a corner or next to a doorway;
  - 1–2 ordinary monsters and a 50 % chance of an extra champion (without escorts);
  - no chests, urns, bones or gold piles.
  The boss's type is drawn by weight from the types unlocked at depth `d + 1`, so it can be a type not yet
  seen at this depth (from depth 4 every type is already unlocked, so this only matters if bosses start earlier).
- **Green brazier.** When there is a boss room, with 50 % chance one room joined to the boss room by a corridor gets an extra brazier
  with green flames, a hint of what lies next door. Corridors are recorded as room pairs when carved.
- Blocking props are only placed on a room's edge, against solid wall, and never next to a doorway or
  corridor mouth, so they can't cut off a path.
- **Monsters per room** (not the start or boss room): `min(7, 1 + ⌊area/22⌋ + ⌊d/3⌋ + (40 % chance of +1))`.
  The type is drawn by weight from the types unlocked at that depth. A **champion** also brings 2–3 escorts of
  its own type (never champions themselves) on free floor tiles within 2 tiles of it.

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

- Starts with: STR 10, DEX 10, VIT 10, a *Rusty Short Sword* (equipped), a *Short Bow* in the pack, and
  3 health potions. Quick keys start as 1 = sword, 2 = bow, 3 = potion.
- **Maximum life:** `40 + 4·VIT + 6·level + life bonuses`.
- **Regeneration:** `0.2 % of max life per second + item regen`, always active. Life is shown in the red
  orb at the bottom left.
- **Critical chance:** `5 % + 0.2 %·DEX + item crit`. Criticals deal ×1.75.
- **Experience:** level `L` needs `round(120 · L^1.7)` XP (120, 390, 1851 … for levels 1, 2, 5). On a level-up, STR, DEX and VIT each gain +2 and
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
- **Health potion:** restores 35 % of max life, with a 0.8 s cooldown (minimum time between two potions). There is no limit on how many the hero carries. It can't be drunk at full life.
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

**Attack speed.** Each weapon has a cooldown (attacks per second = 1 / cooldown). Swapping weapons adds a
0.2 s delay before the next attack.

**Monsters:**

- Monsters wake when the hero is within 8.5 tiles with line of sight, or when they are hit. A monster that
  wakes also wakes idle monsters within 6 tiles of it; one that is **hit** also wakes every monster in the same
  room.
- They chase directly when the way is clear and otherwise follow A\* paths, re-planned every 0.5–0.9 s.
  They push apart from each other and from the hero, and give up beyond 20 tiles.
- **Losing interest.** A chasing monster goes back to wandering when:
  - it is **stuck** for 3 s (`STUCK_GIVEUP`): it is trying to move toward the hero (not in reach, not winding
    up, not standing to shoot) but stays within 0.5 tiles (`STUCK_MOVE`) of one spot, e.g. a pack plugging a
    corridor mouth. Plugging is intended; giving up thins the plug out. A monster that gave up this way is
    **calm**: it ignores the hero and isn't woken by other monsters for at least 6 s (`CALM_MIN`) and until it is
    unstuck (it has walked 1 tile, `UNSTUCK`, of its own random walk; pushes don't count). A hit on a calm
    monster doesn't wake it at once: it marks it **provoked**, and it re-engages the moment it is unstuck;
  - it has **not seen** the hero for 15 s (`LOST_SIGHT`). It isn't calm afterwards, so it wakes again normally.
- Idle monsters wander slowly.
- A monster not damaged for 4 s regenerates 1.5 % of its max life per second.
- **Melee monsters** wind up for 0.32 s (a visible shake). The blow lands only if the hero is still in reach.
- **Wraiths** keep 3+ tiles away. They cast a 0.45 s green bolt at 7 tiles/s with a 6.5-tile range; walls
  block it.

| Monster | Life | Damage | Armor | Speed | Attack every | XP | From depth |
|---|---|---|---|---|---|---|---|
| Skeleton Warrior | 26 | 3–6 | 5 | 2.5 | 1.2 s | 16 | 1 |
| Ghoul | 20 | 2–5 | 2 | 3.3 | 0.9 s | 13 | 1 |
| Cave Spider | 15 | 2–4 | 1 | 3.9 | 0.8 s | 11 | 1 |
| Wraith (ranged) | 22 | 4–7 | 3 | 2.3 | 1.9 s | 22 | 2 |
| Pit Demon | 75 | 8–13 | 12 | 2.1 | 1.5 s | 60 | 3 |

Spawn weights are 3 : 3 : 2 : 2 : 1 in table order.

**Scaling with depth `d`** (the dungeon is endless):

| Stat | Scaling |
|---|---|
| Life | × 1.22^(d−1) |
| Damage | × 1.22^(d−1) |
| Armor | + 3·(d−1) |
| Speed | × min(1.35, 1 + 0.015·(d−1)) |
| XP | × 1.17^(d−1) |
| Monster level | = d (used by armor mitigation) |

**Monster tiers** (`TIER` in the code):

| | Normal | Champion | Boss |
|---|---|---|---|
| Occurs | always | 10 % of monsters from depth 2 (none at depth 1) | one per level from depth 4, in the boss room |
| Name | type name | prefix + type, e.g. *Dread Ghoul* | *&lt;name&gt;, &lt;type&gt; Tyrant*, e.g. *Morgrath, Ghoul Tyrant* |
| Life / damage / XP | ×1 | ×2.5 / ×1.5 / ×3 | ×6 / ×1.8 / ×8 |
| Armor | — | — | + 4·d |
| Size | ×1 | ×1.15 (radius too) | ×1.35 drawn; radius ×1.15, at most 0.48 so it fits corridors |
| Look | — | red glow, gold health bar and target name | green glow, green health bar and target name |
| Loot | see Loot sources | see Loot sources | see Loot sources |

Boss names are drawn from Morgrath, Vexhollow, Ulthane, Skarn, Belmorah, Grisvald, Nythra, Corvane, Drokkar
and Ashmire.

## Items

**Slots:** weapon, helm, armor (chest), gloves, boots, two rings and an amulet. Only one weapon can be
equipped at a time.

**Base items.** They unlock at an item level, which normally equals the depth:

| Item | Slot / type | Base stats | Unlocks at |
|---|---|---|---|
| Short Sword | sword | 4–8, 0.55 s | 1 |
| Longsword | sword | 6–12, 0.65 s | 2 |
| Blackened Greatsword | sword | 11–19, 0.85 s | 4 |
| Hand Axe | axe | 5–10, 0.7 s | 1 |
| Battle Axe | axe | 9–16, 0.85 s | 3 |
| Executioner's Axe | axe | 14–26, 1.05 s | 5 |
| Short Bow | bow | 3–7, 0.6 s | 1 |
| Yew Longbow | bow | 6–12, 0.75 s | 3 |
| Bone Bow | bow | 10–18, 0.9 s | 5 |
| Leather Cap | helm | armor 3 | 1 |
| Horned Great Helm | helm | armor 8 | 3 |
| Leather Tunic | armor | armor 6 | 1 |
| Plate Cuirass | armor | armor 15 | 4 |
| Leather Gloves | gloves | armor 2 | 1 |
| Iron Gauntlets | gloves | armor 5 | 2 |
| Leather Boots | boots | armor 2, +5 % move speed | 1 |
| Plated Boots | boots | armor 5 | 2 |
| Silver Ring | ring | +2 VIT | 1 |
| Ruby Ring | ring | +3 STR | 3 |
| Grave Ring | ring | +8 % damage | 5 |
| Sapphire Amulet | amulet | +3 DEX | 1 |
| Blood Amulet | amulet | +15 life | 3 |
| Bone Talisman | amulet | +1 life regen/s | 5 |

**Slot gates by depth.** On top of the item-level unlocks, no rings drop before depth 3 (`RING_FROM`) and no
amulets before depth 5 (`AMULET_FROM`); the base is then drawn from the other slots. Like the rarity gates,
boss-room loot (the boss, its guards and the guardian's chest) uses depth + 2, so the boss room (which has
loot from depth 4) can drop amulets from depth 4 rather than 5.

**Scaling.** Weapon damage and armor scale by `1 + 0.14·(ilvl − 1)`; built-in bonuses scale by
`1 + 0.1·(ilvl − 1)`.

**Rarity.**

| Rarity | Base chance | Affixes | Name |
|---|---|---|---|
| Common (white) | the rest | 0 | base name |
| Magic (blue) | (30 % + boost) × `MAGIC_ODDS` (0.25) | 1–2 | "Prefix Base of Suffix", e.g. *Mighty Longsword of the Fox* |
| Rare (gold) | (7 % + half the boost) × `RARE_ODDS` (0.1) | 3–4 | random name, e.g. *Gravefang, Longsword* |

So a plain drop is 0.7 % rare and 7.5 % magic. Chests, champions and bosses add a rarity boost (with a 0.35
boost: 2.45 % rare, 16.25 % magic). An item with a forced rarity (the starting kit, the guardian's chest) skips
the roll.

**Rarity gates by depth.** No magic items before depth 2 (`MAGIC_FROM`) and no rares before depth 4
(`RARE_FROM`); a roll above what the depth allows is lowered to the best allowed rarity (rare → magic at
depths 2–3, anything → common at depth 1). Loot from the **boss room** (the boss, its guards and the
guardian's chest) uses the rules of depth + 2; since the boss room only has loot from depth 4, where every
rarity is already allowed, the rarity gates never limit it.

**Affixes** (value ranges grow with item level `l`):

| Stat | Prefix / suffix | Range |
|---|---|---|
| +STR | Mighty / of the Bear | 1 – 2+l |
| +DEX | Nimble / of the Fox | 1 – 2+l |
| +VIT | Stalwart / of the Ox | 1 – 2+l |
| +Life | Hale / of Life | 5 – 8+4l |
| +Life regen/s | Mending / of Renewal | 0.3 – 0.6+0.2l |
| +Armor | Warded / of Iron | 2 – 3+2l (not on weapons) |
| +Crit % | Keen / of Precision | 1 – min(3+0.5l, 12) |
| +Damage % | Cruel / of Slaughter | 5 – 10+3l |
| +Move speed % | Swift / of Haste | 3 – min(6+l, 15) (boots only) |

**Loot sources:**

`LOOT` (0.8) thins all loot by 20 %: each random item drop below happens only with probability `LOOT`
(`lootItem()`), and every gold amount is multiplied by `LOOT` (`dropGold()`, at least 1). Potions are not
affected. The guardian's chest's guaranteed item is not thinned.

| Source | Drops (item chances before `LOOT`) |
|---|---|
| Monster | 13 % item, 6.75 % potion, 30 % gold (2–8 × d) |
| Champion | an item of ilvl d+1 (boost 0.35), plus a 50 % chance of a second (boost 0.2) |
| Boss | an item of ilvl d+1 (boost 0.35), gold (20–40 × d), plus the normal 6.75 % potion / 30 % gold rolls |
| Chest | 1–3 items (boost 0.15, 30 % chance of ilvl+1), gold (10–30 × d), 22.5 % potion |
| Guardian's chest | **always** one item of ilvl d+1 that is rare (30 %) or else magic, gold (30–60 × d), plus everything a normal chest drops |
| Urn | 35 % gold, 9 % potion, 8 % item |
| Bones | 20 % gold, 10 % item |

**Guardian's chest.** It glows green and is labelled *Guardian's Chest* on hover. While the boss lives it is
sealed: clicking it only logs "The chest is sealed while its guardian lives." When the boss dies, the log says
"<boss> is destroyed. The guardian's chest unseals."

Dropped things land on nearby free tiles. Floor items bob, glow in their rarity colour, and show a name
label when within 7.5 tiles. Gold is counted at the top left. Potions go to a potion counter, not the
inventory.

## Equipment overlay

Opened with `I` / `C` / `Tab` or the **Equipment (I)** button, closed with the same keys, `Esc`, the button,
or the **✕** in its header (for touch screens). It is a partly transparent dark panel
(`rgba(16, 11, 14, 0.78)`); **the game keeps running underneath** and can still be played around it.
If it doesn't fit the screen it is scaled down to fit (see HUD, Phones).

- **Paper doll:** eight slots around an animated portrait of the hero walking (12 frames/s) and slowly
  turning through all eight directions, drawn 128 px tall with the frame's aspect ratio kept. Click an equipped item to move it back to the pack.
- **Inventory:** 6 × 5 grid (30 items).
  - Click to equip. The previously equipped item swaps into the same cell. Rings fill an empty ring slot
    first, otherwise they replace ring 1.
  - Right-click (or `Shift` + click) to drop the item on the floor; this also clears its quick key.
  - A potion cell shows the potion count; click it to drink.
- **Tooltips:** name in rarity colour, type, item level, damage and attacks per second or armor, and every
  bonus. For pack items it also compares with the equipped item in that slot: base DPS difference for
  weapons, armor difference otherwise.
- **Attributes:** level, XP, STR / DEX / VIT, life (live), regen, armor, damage range, attack speed, crit,
  move speed, kills, gold.
- **Quick keys:** hover a weapon (in the pack or the weapon slot) or the potion, then press `1`–`9` / `0` to
  bind it to that key. A weapon can only be on one key, and key tags show on bound items. Right-click (or `Shift` +
  click) a key to clear it.
- Outside the overlay (or while hovering nothing in it), a quick key equips its weapon from the pack, or
  drinks a potion. The bottom hotbar shows the bound icons, highlights the equipped weapon, and can also be
  clicked.
- **Tap to inspect (touch):** the last pointer type is tracked on every `pointerdown`. In the overlay, a touch
  tap on an equipped item, a pack item, the potion or a quick key (captured before the element's own click)
  opens its tooltip instead of acting, placed centred on the element, below it if it fits, otherwise above
  it, without the mouse hints. It adds buttons for the actions: **Equip** and **Drop** (pack item),
  **Unequip** (equipped item), **Drink** (potion), **Clear key** (bound quick key), always **Close**, and
  for weapons and the potion a **Quick key: 1–0** row to bind it. A button acts and closes the tooltip; a
  tap anywhere outside it also closes it. Hover handlers ignore touch input (emulated mouse events would
  otherwise show, move or hide the tooltip). Mouse and pen work as before; the HUD hotbar still acts on tap.

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
  round and the orb's size, a dark steel disc with a gold rim showing the equipped weapon's icon (80 px; 52 px
  on phones) and an "ATTACK" label below. Holding it is the attack modifier (see Controls). The life orb slides
  right next to it (to 156 px from the left), so the finger on the button never covers it.
- **Life orb:** a click or tap on it drinks a health potion (the same as `Q`; "No potions left." when there
  are none).
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

A tiny WebAudio synth (no audio files): filtered-noise swings, hits and doors, plus tones for the bow, bolts,
pickups, gold, potions, level-ups, death and stairs. Audio starts on the first click (browser autoplay rules).
`N` toggles it.

## Assets

The art was generated through the `ai-media-generation` skill in Martin's notes repo: monsters, items, props
and textures with OpenAI `gpt-image-2` (medium quality, about $0.70), and the hero walk cycle with Google
`gemini-3.1-flash-image` (see [Walk cycles](#walk-cycles-hero-skeleton-ghoul)). Total spend so far is about
$2.69 ($0.07 for the boss-room furnishings, and before that about $0.70 for the original sheets, $0.83 for the hero walk cycle and $0.88 for the skeleton and ghoul
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
  (weapons, bows, helms, armor, gloves, boots, rings, amulets, potion), on magenta.
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
