# Dungeon Crawler 01 — Versions

What each version of the game added, newest first. The version is `VERSION` in `index.html`, shown at the
bottom right of the title screen. The game's full state at any version is in git history (see
[Going back to a version](#going-back-to-a-version)). Kept by the `version-tracking` skill
(`.claude/skills/version-tracking/SKILL.md`).

Small changes that build on the one before are merged into one entry (e.g. *v38–v40*) with a single feature
list. The **Commit** line names the commit of the entry's last version; the newest entry gets its commit when
the next version is recorded.

## v62–v63 — debug overlay and scenarios from the title screen (2026-11-15)

Commit: *(the next version records it; until then, the latest commit that set `VERSION = 63`)*

- The version number on the title screen is larger; double-click it (long-press on a phone) to open the debug
  overlay, which now shows above the title screen (`Ctrl` + `D` works there too).
- A **Scenarios** button at the title screen's bottom left opens the sandbox's scenario picker.
- The scenario picker shows its loading progress, and why the scenarios stay off if the game fails to start.

## v61 — surface music (2026-11-15)

Commit: 47830bd

- The surface has its own music: two cheerful folk-style instrumental tracks in the dungeon music's spirit
  (organ, harp, lute, flute, strings), taking turns. Going down switches to the dungeon music.
- The sandbox's surface scenario shows the track playing and has **Next loop**.

## v60 — the surface, depth 0 (2026-11-15)

Commit: d8e5526

- New heroes start on the surface: an endless moonlit grassland with woods and glades, bushes, flowers, rocks and
  mushrooms, made as you walk (32-tile "super tiles", always the same for a place).
- Trees are drawn in two parts: walk under a crown and its leaves cover you, turning see-through.
- The crypt: a 5 × 5-tile stone mausoleum a few steps away; click its dark doorway to go down to depth 1.
- The sandbox has a "The surface" scenario; unused AI images now live in `assets/unused/`.

## v57–v59 — Keepers of the Crypt: the market (2026-11-15)

Commit: ea9c02d

- On every third depth a Keeper of the Crypt, one of four human merchants (Aldric, Borin, Mirela, Old Tobias), keeps
  a furnished stall in a quiet room: rug, table of wares, weapon rack, shelf, chest of trinkets, crates, barrel,
  lanterns.
- Click the keeper to trade:
  - two wishes, each giving a magic (sometimes rare) item for something it wants;
  - gear of depth + 3 for gold, sometimes magic or rare;
  - selling pack items for a quarter of their value;
  - healing to full for gold.
- Items have a value (the price), from their type's depth, rarity and affix tier.
- Sandbox: a "Keeper of the Crypt" scenario with keeper look buttons.
- Avoid going back to v57 or v58: hovering a door froze the screen (a red flash that never cleared, life and damage
  numbers stuck), and the keeper's rug was cut off on one side. Both are fixed in v59.

## v54–v56 — fire keeps burning (2026-11-14)

Commit: 2995d78

- Anyone who leaves a fire keeps burning for 10 s at 5 damage per second (50 in all); touching a fire again
  restarts it, and nothing stacks.
- A monster catches fire (burns on after leaving) only after 1.5 s in a fire without a break; the hero at once.
- Burning creatures show flames on their body, shrinking as the burn runs out; the hero gets a flame badge with a
  countdown on the life orb.

## v53 — deeper loot from champions, bosses and their chests (2026-11-14)

Commit: f7234b3

- Champions and chests in the big room drop items allowed at depth + 2 (were + 1), bosses at depth + 3, and
  everything in the guardian's chest at depth + 4: item types, affix tiers, rarity, rings and amulets.
- Eases the v52 spike: about twice as many deaths as v51 at depths 3–13 instead of three times.

## v52 — item progression spread over more depths (2026-11-14)

Commit: 1ab9b3f

- Better item types unlock later: the best of each slot at depth 14–15 (was 10–11), the second tier at depth 4
  (was 3).
- Magic items and rings from depth 4 (was 3), amulets from 6 (was 5), rares from 8 (was 6).
- Affix tiers 2 and 3 from depth 7 and 12 (were 5 and 9).
- Older types still fade out as before (half as likely every 4 depths).
- Harder: the balance simulation shows about three times as many deaths at depths 3–13
  (`tools/simulation/results-2026-11-14.md`).

## v51 — later wraiths and boss room, bigger big rooms (2026-11-14)

Commit: 6e364c4

- A single wraith in one room at depth 3; wraiths appear from depth 4 (was 3), champions from depth 8.
- The empty boss room moved from depth 3 to depth 5 (bosses still from depth 6).
- Big rooms have twice the area (16–20 tiles a side, was 11–14) and 50 % more monsters.

## v50 — faster skeletons and Pit Demons, stronger charge (2026-11-14)

Commit: f41c0e7

- Skeletons run 2.3 tiles/s at depth 1 (was 2.1), Pit Demons 1.9 (was 1.8); both still grow 1.5 % per depth.
- A charge is 1.6× speed (was 1.5×).

## v47–v49 — gentle limits on kiting (2026-11-14)

Commit: 05cd592

- Bows have a short draw before each arrow: the hero stands still 0.15 s (Short Bow) to 0.24 s (War Bow); the
  rate of fire is unchanged, and the arrow is aimed when it is loosed.
- Spiders and Pit Demons hit by an arrow from more than 2.5 tiles away charge at 1.5× speed for 2 s (at most every
  5 s), trailing dust.
- Sandbox: a "Kiting with a bow" scenario with a common Hunting Bow, in the level's big room grown to 3× its area,
  with sleeping spiders and Pit Demons.

## v46 — tougher, richer champions and bosses (2026-11-14)

Commit: 32411bf

- Champions hit twice as hard as a normal monster (was ×1.5) and give ×4 XP (was ×3).
- Bosses hit three times as hard (was ×1.8) and give ×12 XP (was ×8).

## v45 — melee and chase fixes next to the target (2026-11-14)

Commit: 13628f4

- Fix: a melee attack on a monster one tile away diagonally but out of reach (typically a wraith keeping its
  distance) did nothing; the hero now steps in and strikes.
- Fix: a monster on the other side of an outside wall corner from the hero no longer stands stuck; it walks
  around the corner and attacks.

## v44 — fire bombs (2026-11-13)

Commit: 4c5ab9b

- Fire bombs: clay pots of lamp oil, equipped as a weapon and thrown with a right click, up to 7 tiles; they land on
  the aimed spot (or break against a wall on the way).
- Where one breaks, the ground burns for 12 s in a 1.5-tile circle: 10 damage per second to anyone in it,
  monsters and the hero alike.
- They stack like potions; picked-up bombs join the stack; a quick key for them survives running out; after the
  last throw the hero is bare-handed until another weapon is equipped.
- Drops from depth 2 (chests, urns, monsters).
- The bomb's look: design 1 of six AI-made designs (a brown clay pot with a rag stopper); the other five kept in
  the item atlas for stronger bombs later.
- Three looks for the fire to choose from (Blaze, Ember bed, Oil pool), with light, smoke, sparks and a fading
  scorch mark; throw, shatter, crackle and roar sounds.
- Sandbox: three fire bomb scenarios (pack fight, the last two, practice yard) with a fire status bar and fire
  look buttons; the catalog lists fire bombs with the potions.

## v43 — the game so far (v1–v43, 2026-11-05 to 2026-11-11)

Tags: Playable / Good Experience

Commit: 7fe788b

**The crypt**
- Isometric, gothic dungeon crawler in one `index.html` (vanilla JavaScript, canvas, no build step); all art,
  voices and music AI-generated.
- Endless descent: every depth is a freshly generated level that grows with depth (map size, room count), with
  rooms joined by corridors (65 % of them wide), doors that swing open into the corridor, and stairs down in the
  room farthest from the start.
- Props: chests, urns to break, bones to search, gold, braziers; full-height walls with a dirt texture on top;
  props near the south and east walls kept in view.
- Big rooms on every second depth from 3; a lone Pit Demon at depth 4.
- Boss room from depth 3 (empty at 3, a boss from 6): entered only through doors, furnished by depth (throne,
  altar, candelabra, skull piles, banners, pillars, sarcophagi), a rune circle, four or more braziers, a guardian's
  chest sealed while the boss lives; green banners and sometimes a green brazier in the rooms next to it.
- Lighting with soft light holes around the hero and braziers, fog of war, and a minimap (`M`).

**Monsters**
- Skeleton warriors, ghouls, cave spiders, wraiths (ranged) and Pit Demons, stronger at every depth
  (+12 % per depth), with champions (gold) and named bosses.
- 8-frame walk cycles for the hero, skeleton and ghoul, built from 3D stick-figure pose guides; 4-frame sheets for
  the other monsters; soft grounded shadows.
- Awareness by type: who notices the hero, who wakes whom, chance-based noticing for ghouls, wraiths and demons; a
  hit always starts pursuit; monsters lose interest when stuck for 3 s or out of sight for 8 s, and take
  detours when stalled.
- New types are limited per room for four depths after they appear, and can be champions only after that.

**Hero and combat**
- STR / DEX / VIT, levels, crits, armor mitigation both ways; no life regeneration.
- Melee with reach and arc per weapon type (swords, axes with a wide cleave, bare hands), 25 % cleave damage to
  everything else in the swing; bows that shoot arrows stopped by walls and closed doors.
- One action timeline and an action queue for attacks, weapon swaps (0.2 s), equips and potions (0.4 s), with
  pointless uses skipped.
- Potions: health (44 % of max life) and iron skin (armor ×3 + 60 for 20 s), stackable in the pack.
- Death: the scene runs on for 4 s while the hero fades; then back to the title screen, resuming from the last save.

**Items**
- Eight slots: weapon, helm, armor, gloves, boots, two rings and an amulet.
- Fixed stats per item type, with type ladders that unlock by depth and their own icons.
- Rarity: common, magic (from depth 3) and rare (from depth 6); rings and amulets magic or rare only; three affix
  tiers by depth.
- Loot from monsters, champions, bosses, chests, urns and bones; floor items bob and glow in their rarity colour,
  with outlined labels and a highlight that grows with the affix tier.
- Double click / tap a floor item to pick it up and equip it at once.

**Screens and HUD**
- Title screen as hero picker: new heroes named in place, a cogwheel per hero to rename, erase or export it,
  import of an exported hero (versioned JSON file), scrolling list, the version number.
- Saves in `localStorage`: on creating a hero and on arriving at each new depth.
- Equipment overlay (`I` / `C` / `Tab`, or the grid square at the end of the quick-key bar): paper doll with an
  animated walking portrait, 6 × 5 pack, tooltips, attributes with their sources (character / items / magic /
  temporary), quick-key assignment, music and effects volume sliders.
- HUD: attack globe, life orb (bottom right; a click drinks a potion), quick-key hotbar with XP bar, message log,
  hovered monster's name and life, a life bar over the hero's head after hits with a red glow at low life, a red
  vignette on hits.
- Debug overlay (`Ctrl` + `D`, or hold the minimap and the life orb together on touch): version, fps, render
  scale, an Auto resolution switch, the music state.

**Touch, phones and performance**
- Touch mode: attack button, a modifier for right clicks, tap to inspect, pinch zoom, multi-touch HUD keys that
  act on touchstart, holding the attack button auto-attacks.
- Phone portrait and short landscape layouts that fit the hotbar and buttons without overlap.
- Home-screen app (web app manifest, iOS meta tags, icons) that opens without browser bars; full screen with `F5`
  or a title-screen button where the browser supports it.
- Game time follows real time on slow devices; automatic render scale that steps down under 25 fps; sprite
  effects without canvas filters (iOS / Safari).

**Sound and music**
- Foley-style WebAudio synthesis with reverb: swings and hits by material, doors, chests, urns, potions, stairs,
  level-ups, a bow that sounds like a bow; skeleton rattles; AI-voiced ghoul moans and grunts.
- Music (Google Lyria, D minor): instrumental exploration and combat loops with crossfades; combat starts when four
  or more monsters pursue, lasts while any still pursues, ends at once when the last pursuer is killed and 6 s
  after they lose interest.
- On Pit Demon levels: Latin choir versions on the 2nd, 5th and 9th play of a track, and the choir combat track in
  the boss room.
- Volume sliders for music and effects; `N` mutes both.

**Tools and testing**
- Generated catalog (`catalog.html`) of monsters, items, affixes and rarity per depth.
- Balance simulation (`tools/simulation/`) with dated results.
- Art pipeline scripts (`tools/`) for sprites, walk cycles, items, props, icons and ghoul clips.
- Sandbox (`sandbox.js`, `?sandbox`, and a Claude artifact): Pack fight and Pit Demon level scenarios with a
  never-saved test hero and a music status bar; `versions.md` (this file).

## Going back to a version

Every pushed version is a commit, and its message names the version (`v<N>`). From the repo root:

```bash
git log --oneline -- martin/dungeon-crawler-01            # find the version's commit (its message says v<N>)
git log --oneline -S "const VERSION = 38;" -- martin/dungeon-crawler-01/index.html   # or by the VERSION line
git show <commit>:martin/dungeon-crawler-01/index.html > /tmp/index-v38.html          # look at one file
git checkout <commit> -- martin/dungeon-crawler-01         # bring the whole folder back to that version
```

Before v36 the commit messages carry the version in brackets at the end, e.g. *… (v21)*; v1 is 87ae48b, the first
commit with a version number. Bringing a folder back is a normal change: commit it as a new version (or
`git checkout main -- martin/dungeon-crawler-01` to undo it).
