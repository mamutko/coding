# Dungeon Crawler 01 — Versions

What each version of the game added, newest first. The version is `VERSION` in `index.html`, shown at the
bottom right of the title screen. The game's full state at any version is in git history (see
[Going back to a version](#going-back-to-a-version)). Kept by the `version-tracking` skill
(`.claude/skills/version-tracking/SKILL.md`).

Small changes that build on the one before are merged into one entry (e.g. *v38–v40*) with a single feature
list. The **Commit** line names the commit of the entry's last version; the newest entry gets its commit when
the next version is recorded.

## v43 — the game so far (v1–v43, 2026-11-05 to 2026-11-11)

Commit: *(the next version records it; until then, the latest commit that set `VERSION = 43`)*

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
