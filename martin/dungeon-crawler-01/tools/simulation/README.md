# Balance simulation

`simulate.js` estimates how hard each depth is. Simulated heroes clear depths 1 to N of the real game and
equip the best gear they find. The script prints a Markdown report comparing the hero with the monsters at
each depth. Use it to check a balance change: run it before and after, and compare.

## Running it

```
node tools/simulation/simulate.js [--runs 200] [--depths 6] [--travel 40] [--pot 0.35] [--melee 5] [--json out.json]
```

Run it from the game folder or from anywhere else; it finds `index.html` itself. It needs Node.js and
Playwright with Chromium (`npm i playwright` and `npx playwright install chromium`; both are pre-installed in
Claude's cloud sessions). 200 runs of 6 depths take a few seconds.

| Option | Default | Meaning |
|---|---|---|
| `--runs` | 200 | Number of simulated heroes (each starts fresh at depth 1). |
| `--depths` | 6 | How many depths each hero clears. |
| `--travel` | 40 | Seconds of walking between two rooms, during which the hero regenerates life (no effect while the game's regeneration is 0). |
| `--pot` | 0.35 | The hero drinks a health potion when life falls below this share of max life. |
| `--melee` | 5 | At most this many monsters attack in melee at once (ranged wraiths always attack). |
| `--json` | — | Also write the raw per-run, per-depth data to this file. |

The report goes to stdout. To keep a result, save it as a dated file in this folder (e.g.
`results-2026-11-09.md`, with the time added when there are several on one day) together with the conclusions
drawn from it.

## How it works

The script serves the game folder on a local port and opens `index.html` in headless Chromium. Everything
except the fights runs the game's own code:

- levels from `buildLevel`, so the same rooms, monster counts, champions with escorts, boss rooms, chests,
  urns and bones as in play;
- monster stats from `makeMonster`, item rolls from `genItem`, hero stats from `recalc`, the armor formula
  from `armorReduce`;
- XP and level-ups from `gainXp`; kills, loot drops and potion drops from `killMonster` and `act`.

Each simulated hero starts as a new hero (Rusty Short Sword, Short Bow, 3 health potions) and clears every
depth completely:

1. **Rooms in order, boss room last.** All monsters in a room fight at once, because a hit wakes the whole
   room in the game too.
2. **Fight model** (time step 0.05 s):
   - The hero attacks every `cd` seconds of the equipped weapon and always hits. It rolls damage and crits
     like `heroAttack` and focuses the weakest monster. Melee swings also cleave one other monster with a
     sword, or two with an axe, for 25 % (`CLEAVE`). With a bow, monsters arrive 1.5 s later (free shots).
   - Each monster hits every `cd` seconds of its type, after a random first delay. Its damage is reduced by
     the hero's armor exactly as in `damageHero`. Only `--melee` melee monsters attack at once.
   - The hero regenerates `regen` life per second, drinks a health potion below `--pot` of max life (0.4 s,
     heals `HEAL` of max life), and drinks an iron skin potion at the start of a fight with a boss, a champion, or 6 or more
     monsters.
   - **Death:** counted, then the hero continues at full life (the real game would send it back to the start
     of the depth). The death numbers are therefore "how often it would have died", not a run ending.
3. **After each room:** the hero opens the room's chests, urns and bones, picks up all gold, potions and
   items (with the game's pick-up XP), equips the best gear, and walks `--travel` seconds to the next room.
4. **Best gear:** for each slot, every owned item is tried, and the one with the highest
   *DPS × effective life* is kept. DPS is against a normal skeleton of the current depth; effective life
   is max life ÷ (1 − armor reduction). Axes get ×1.25, swords ×1.12 and bows ×1.15 for cleave and free
   shots. Items that aren't equipped are discarded, so the pack never fills up.

**Limits.** The model is harsher than real play: there is no retreating, fighting in doorways, kiting with
the bow, waiting to regenerate, or pulling monsters one at a time. So the absolute death rates are
pessimistic. Compare depths with each other, and compare runs before and after a change.

## The report

- **Hero vs. normal monsters:** the hero's medians on arrival at each depth (level, life, armor and its
  damage cut against monsters of that depth, DPS against a normal skeleton after its armor). Then the
  skeleton's and Pit Demon's life / average hit / armor, and how long each side takes to kill the other
  one on one.
- **Whole level:** means per depth: monsters and champions on the level, room pack sizes, damage taken in
  multiples of the hero's max life, potions found and drunk, the share of runs with at least one death, and
  deaths per run.
- **Share of damage taken, by source:** which monsters cause the damage (champions and the boss are counted
  separately from their type).
- **Deaths per run, by room kind:** where the deaths happen: a normal room, a room with a champion (and its
  escorts), the big room (found by its grey banners) or the boss room.

## Results

- [results-2026-11-09-1650.md](results-2026-11-09-1650.md): second pass (XP per level −40 %, health potion 44 %,
  iron skin × 2 + 20 for 30 s). Deaths at depths 2–4 roughly halved; depths 5–6 (Pit Demons, boss) and champion
  rooms are what's left.
- [results-2026-11-09-1630.md](results-2026-11-09-1630.md): after the first balance pass (no regeneration,
  fewer monsters per room, wraiths from depth 3, Pit Demons from 5, bosses from 6, big rooms). Damage per level
  roughly halved; champion rooms are now the main killer, and with no regeneration healing is short.
- [results-2026-11-09.md](results-2026-11-09.md): baseline before any balance change. The difficulty comes from
  numbers, champion packs, the Pit Demon at depth 3, and healing that doesn't keep up; one on one, the hero
  stays ahead.
