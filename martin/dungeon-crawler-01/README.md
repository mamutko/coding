# Dungeon Crawler 01 — "Crypt of Endless Night"

An isometric, gothic dungeon crawler in a single `index.html` (vanilla JavaScript, HTML5 canvas, no build step).
A lone knight descends an endless crypt, fighting monsters that grow stronger on every level, collecting
and equipping gear, and levelling up. All art is AI-generated (see [Assets](#assets)).

## Files

| Path | Purpose |
|---|---|
| `index.html` | The whole game: markup, CSS, and JavaScript. Asset metadata (`META`) is inlined so the page also works from `file://`. |
| `assets/hero.webp`, `skeleton.webp`, `ghoul.webp`, `spider.webp`, `wraith.webp`, `demon.webp` | 8-direction × 4-frame walk sprite sheets (transparent). |
| `assets/items.webp` | 6 × 4 atlas of 96 px item icons. |
| `assets/props.webp` | Horizontal strip of props (chest, open chest, door, stairs, brazier, bones, urn, gold). |
| `assets/floor.jpg`, `assets/wall.jpg` | 512 px seamless floor and wall textures. |
| `assets/meta.json` | Frame sizes and atlas coordinates written by the processing script (copied into `META` in `index.html`). |
| `tools/process_art.py` | Turns the raw AI images into the files above (chroma-key, slicing, packing). |

## Controls

| Input | Action |
|---|---|
| Left click on floor | Walk there (A* pathfinding). Holding the button keeps walking toward the cursor. |
| Left click on chest / door / urn / bones / gold / item / stairs | Walk to it and act on it: open, break, search, pick up, or descend. |
| Right click | Attack with the equipped weapon (see [Combat](#combat)). Hold to keep attacking. |
| `I`, `C` or `Tab` | Toggle the equipment overlay (`Esc` closes it). |
| `1`–`9`, `0` | Quick keys: equip the bound weapon or drink a potion. |
| `Q` | Drink a health potion. |
| `M` | Toggle the minimap. |
| `N` | Toggle sound. |
| Mouse wheel | Zoom (0.6×–1.5×). |

The title screen lists the controls and has an **Enter the Crypt** button (enabled once all images have loaded).
The first level is rendered behind the title screen.

## Rendering

- **Isometric projection.** Tiles are 96 × 48 px diamonds. A world point `(x, y)` (in tile units) maps to screen
  `((x − y)·48, (x + y)·24)`. The camera follows the hero smoothly (25 % lerp per frame) and keeps them centred,
  with the view aimed 46 px above the feet. It snaps when the hero teleports (new level). The canvas renders at
  device-pixel ratio (max 2).
- **Floor.** Every visible floor and doorway tile is added to one path in iso-transformed space
  (`transform(48, 24, −48, 24)`). It is filled with the floor texture pattern, which spans 3 tiles, and faint
  seams are stroked.
- **Walls** are 72 px tall blocks. Only the two faces facing the viewer (+y and +x) are drawn, and only where the
  neighbour isn't also a wall. Faces are affine-mapped slices of the wall texture, picked per tile so the
  pattern varies. The left face is shaded 42 %, the right 18 %, and the top is a dark cap. Walls within about
  4 tiles *in front of* the hero are drawn at 30 % opacity so the hero is never hidden.
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
  orange glow (`lighter`). Item labels, monster health bars and floating damage numbers are drawn after the
  lighting so they stay readable.
- **Characters.** Each sheet has 8 rows, one per direction, in the order S, SW, W, NW, N, NE, E, SE, and
  4 walk frames per row. The facing row comes from the movement or attack direction projected to screen space
  and rounded to 45° sectors. Frames advance with distance moved; frame 0 is idle. Characters have a shadow
  ellipse and are anchored bottom-centre at their feet. The wraith hovers and bobs. Attacks show a short
  lunge toward the facing direction. A hit flashes the sprite white (`filter: brightness`), and champions get
  a red glow (`drop-shadow`). Dead monsters sink and fade over about 1 s.
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
- **Stairs down** are placed in the centre of the room farthest from the start room (by BFS walking distance).
  The hero starts in the centre of the first room, which never has monsters or chests.
- **Props per room:**
  - brazier: 75 % chance, always in the start room; blocking
  - chest: 38 % chance; blocking
  - urns: 0–2; blocking
  - bones: 0–2
  - gold pile: 20 % chance, worth 3–12 × d
- Blocking props are only placed on a room's edge, against solid wall, and never next to a doorway or
  corridor mouth, so they can't cut off a path.
- **Monsters per room:** `min(7, 1 + ⌊area/22⌋ + ⌊d/3⌋ + (40 % chance of +1))`. The type is drawn by weight
  from the types unlocked at that depth.

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
- **Regeneration:** `0.6 % of max life per second + item regen`, always active. Life is shown in the red
  orb at the bottom left.
- **Critical chance:** `5 % + 0.2 %·DEX + item crit`. Criticals deal ×1.75.
- **Experience:** level `L` needs `round(60 · L^1.7)` XP. On a level-up, STR, DEX and VIT each gain +2 and
  the hero fully heals. XP comes from:

  | Source | XP |
  |---|---|
  | Killing a monster | the monster's XP value |
  | Opening a chest | 6·d |
  | Breaking an urn | 2·d |
  | Searching bones | d |
  | Opening a door | d |
  | Picking up an item | 2·d |
  | Picking up a potion | 1 + d |
  | Descending stairs | 10 × the new depth |
- **Health potion:** restores 45 % of max life, with a 0.8 s cooldown. It can't be drunk at full life.
- **Death** shows the "You Have Fallen" screen with depth, level, kills and gold. **Rise Again** starts a new
  game. Progress is not saved between sessions.

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
hit regardless of angle.

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

- Monsters wake when the hero is within 8.5 tiles with line of sight, or when they or a monster within
  6 tiles is hit.
- They chase directly when the way is clear and otherwise follow A\* paths, re-planned every 0.5–0.9 s.
  They push apart from each other and from the hero, and give up beyond 20 tiles.
- Idle monsters wander slowly.
- A monster not damaged for 4 s regenerates 1 % of its max life per second.
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
| Life | × 1.17^(d−1) |
| Damage | × 1.13^(d−1) |
| Armor | + 3·(d−1) |
| Speed | × min(1.35, 1 + 0.015·(d−1)) |
| XP | × 1.17^(d−1) |
| Monster level | = d (used by armor mitigation) |

**Champions.** From depth 2, 10 % of monsters are champions: a name prefix (Dread, Blighted, …), ×2.5 life,
×1.5 damage, ×3 XP, 15 % larger, red glow, gold health bar.

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

**Scaling.** Weapon damage and armor scale by `1 + 0.14·(ilvl − 1)`; built-in bonuses scale by
`1 + 0.1·(ilvl − 1)`.

**Rarity.**

| Rarity | Base chance | Affixes | Name |
|---|---|---|---|
| Common (white) | the rest | 0 | base name |
| Magic (blue) | 30 % + boost | 1–2 | "Prefix Base of Suffix", e.g. *Mighty Longsword of the Fox* |
| Rare (gold) | 7 % + half the boost | 3–4 | random name, e.g. *Gravefang, Longsword* |

Chests, champions and some drops add a rarity boost.

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

| Source | Drops |
|---|---|
| Monster | 13 % item, 9 % potion, 30 % gold (2–8 × d) |
| Champion | a guaranteed item of ilvl d+1 with a large rarity boost, plus a 50 % chance of a second |
| Chest | 1–3 items (boost 0.15, 30 % chance of ilvl+1), gold (10–30 × d), 30 % potion |
| Urn | 35 % gold, 12 % potion, 8 % item |
| Bones | 20 % gold, 10 % item |

Dropped things land on nearby free tiles. Floor items bob, glow in their rarity colour, and show a name
label when within 7.5 tiles. Gold is counted at the top left. Potions go to a potion counter, not the
inventory.

## Equipment overlay

Opened with `I` / `C` / `Tab` or the **Equipment (I)** button. It is a partly transparent dark panel
(`rgba(16, 11, 14, 0.78)`); **the game keeps running underneath** and can still be played around it.

- **Paper doll:** eight slots around an animated portrait of the hero slowly turning through all eight
  directions. Click an equipped item to move it back to the pack.
- **Inventory:** 6 × 5 grid (30 items).
  - Click to equip. The previously equipped item swaps into the same cell. Rings fill an empty ring slot
    first, otherwise they replace ring 1.
  - Right-click to drop the item on the floor; this also clears its quick key.
  - A potion cell shows the potion count; click it to drink.
- **Tooltips:** name in rarity colour, type, item level, damage and attacks per second or armor, and every
  bonus. For pack items it also compares with the equipped item in that slot: base DPS difference for
  weapons, armor difference otherwise.
- **Attributes:** level, XP, STR / DEX / VIT, life (live), regen, armor, damage range, attack speed, crit,
  move speed, kills, gold.
- **Quick keys:** hover a weapon (in the pack or the weapon slot) or the potion, then press `1`–`9` / `0` to
  bind it to that key. A weapon can only be on one key, and key tags show on bound items. Right-click a key to
  clear it.
- Outside the overlay (or while hovering nothing in it), a quick key equips its weapon from the pack, or
  drinks a potion. The bottom hotbar shows the bound icons, highlights the equipped weapon, and can also be
  clicked.

## HUD

- **Top left:** level name (e.g. *The Forsaken Crypt*, *The Ossuary*, … eight names that cycle with a Roman
  numeral after depth 8), the depth number, and gold.
- **Top centre:** name, level and health bar of the hovered or targeted monster (gold name for champions).
- **Top right:** minimap.
- **Bottom left:** the life orb, and above it a message log (6 lines, each fading after 6 s).
- **Bottom centre:** quick-key hotbar and XP bar.
- **Bottom right:** Equipment button.
- Taking damage flashes a red vignette whose strength depends on how big the hit was.
- Descending fades in from black.

## Sound

A tiny WebAudio synth (no audio files): filtered-noise swings, hits and doors, plus tones for the bow, bolts,
pickups, gold, potions, level-ups, death and stairs. Audio starts on the first click (browser autoplay rules).
`N` toggles it.

## Assets

All art was generated with OpenAI `gpt-image-2` (medium quality) through the `ai-media-generation` skill in
Martin's notes repo, for about **$0.70** total.

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

- **Subjects:**
  - hero knight in dark steel plate armor with a tattered crimson cape
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
- **Textures** (1024²): "seamless tileable … dark gothic dungeon floor of worn irregular grey flagstones" and
  "… dungeon wall of large rough grey stone blocks with mortar, moss and grime".

**`tools/process_art.py`** (`python process_art.py <raw_dir> <out_dir>`, needs Pillow + NumPy):

- **Soft chroma key:** alpha comes from the "magentaness" `min(r, b) − g`. Edge pixels are un-mixed from the
  key colour, and remaining magenta spill is removed.
- **Fragment cleanup:** stray islands from neighbouring cells are dropped. Islands that are small, or that
  touch the cell border (items and props), are removed.
- **Character sheets:** each is cut into its 4 × 8 grid. Every frame is cropped with one shared,
  horizontally-centred bounding box so the feet stay planted, scaled to 128 px tall, and saved as WebP.
- **Icons and props:** icons are fitted into 96 px cells; props are scaled to 45 % and packed into a strip.
- **Textures** are resized to 512 px JPEGs.
- **`meta.json`** gets the frame sizes and atlas coordinates. When assets are regenerated, copy its contents
  into the `META` constant in `index.html`.
