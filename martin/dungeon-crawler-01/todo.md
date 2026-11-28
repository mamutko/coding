# Dungeon Crawler 01 — Ideas / TODO

Ideas for future work, numbered so they can be referred to by number. When an idea is implemented, describe it
in `README.md` and remove it from this list (keep the numbers of the remaining ideas unchanged).

2. **More potions:** life regeneration over a period of time, speed potion. (The iron skin potion is done.)

3. **More scrolls** (scrolls themselves are done: frost, surface escape, return; see README, Scrolls). Kinds still
   to add:
   - defensive magic — increase armor; bounce enemies off after they hit the hero;
   - conjuring — conjure a monster that fights alongside the hero;
   - offensive magic — fire blast (deals damage to monsters within a radius).

5. **Weapon enchantments** — now part of #18 (special affixes): freezing and knockback as affixes. (100 % cleave
   with knockback is the flails', v154.)

10. **Multiplayer** — the Rift is built (phases 1–6 of `multiplayer.md`; see README, The Rift). Left:
    - **Keeping the realm alive** — a player's monsters slowly come back (one every ~20 s, up to their starting
      number) in rooms no hero has been near for 60 s (`multiplayer.md`, §3).
    - **TURN relay** (on hold) — without it ~10–20 % of player pairs (mostly on mobile networks) can't connect.

11. **Stairs up** — going back up the stairs to earlier (shallower) levels, i.e. lower depth numbers. Open
    question: levels are currently generated fresh and never kept, so going up either regenerates the level or
    requires remembering visited levels (layout, what was looted and killed).

13. **Animated doors** — doors visibly swing open and shut (closing is done, v151) instead of switching state instantly.

15. **Limited ammo** — bows need arrows; each shot uses one. Arrows are a stackable pack item (like potions).
    - **Different kinds of arrows**, e.g. explosive and freeze arrows.
    - **Quiver slot** (preferred): a new paper-doll slot holds the arrow stack the bow shoots, so the player
      equips a bow + arrows combination by filling both slots. (Alternatives considered: an arrow quick key that
      makes a stack the active ammo — could still be added on top, as a queued action like a weapon swap; or
      always shooting the best / first arrow stack in the pack.)
    - **Special quivers** — unique items that go in the quiver slot instead of an arrow stack, e.g. a *magic
      quiver of limitless arrows* that never runs out.

16. **Item quality and wear.**
    - **Quality** — a roll on an item's base stats (weapon damage, armor), e.g. ±15 %, so
      two common items of the same type can differ. Shown in the name (*Crude*, *Fine*,
      *Superior*, …) and/or only in the numbers.
    - **Wear** — items wear out with use (weapons when hitting, armor when hit) and lose effectiveness as they do.
    - **Fixing** — some of it can be fixed: repairing wear (and perhaps improving quality) from a Keeper of the Crypt (the market, see README) or
      with a hero skill.

17. **Dragon polish** — the dragon is done (v97–v103; README, The dragon). Left: real sounds (roar, breath, wings)
    instead of the synthesised ones, an ice tint while frozen and flames on it while burning, balance, and the dragon
    in the catalog (`tools/catalog`) and the balance simulation (`tools/simulation`).

18. **Special affixes and forging** (suggested 2026-11-28; builds on #5).
    - **Special affixes** — change how a fight goes rather than adding a number. At most one per item, only on
      magic and rare items, from about depth 6, rarer than stat affixes:

      | Affix | Effect | Rolls on |
      |---|---|---|
      | *of Thunder* | knockback 0.3–0.6 tiles (flails have it built in: the item's `knock`) | melee weapons |
      | *Vampiric* | heals 3–8 % of the damage dealt (healing is scarce since regeneration went) | weapons, rings |
      | *Searing* | 15–30 % chance to set the target burning (the fire bombs' burning) | weapons |
      | *Frostbitten* | 10–25 % chance to freeze the target briefly (the scroll of frost's freeze) | weapons, amulets |
      | *Piercing* | arrows pass through 1–2 monsters | bows |
      | *Thorned* | melee attackers take 10–30 % of their blow back | body armor, helms |
      | *of the Lantern* | a larger light radius | helms, amulets |
      | *Swift* | 5–12 % faster attacks | gloves, weapons |
      | *of Fortune* | more gold and better odds of magic items | rings, amulets |

    - **Resources** — two counters on the hero, like gold (saved; shown in the equipment screen and on the
      title screen's hero card):
      - *Arcane dust* — from **salvaging** unwanted items: a little from a magic item, more from a rare, more from
        deeper items. The everyday forging currency, and a use for junk loot.
      - *Soul shards* — from **champions and bosses** (several from the dragon); needed only for special affixes,
        so the best forging is tied to the hardest fights.
    - **The forge** (costs scale with the item's depth):
      - *Imbue* — a common item becomes magic with one random affix of the depth's tier (dust).
      - *Enhance* — a magic item gains an affix and becomes rare, up to 4 (dust).
      - *Reforge* — re-roll the values of one chosen affix (dust).
      - *Engrave* — add a special affix, chosen from **three offered at random** (dust + soul shards).
    - **The smith** — the cast's unused *smithess* sprite at an anvil, on the surface near the crypt's door (a
      reason to come back up, with the scrolls of escape and return), or in the keepers' rooms.
    - **Order:** 1. special affixes as drops (start with knockback, life steal, burning, freezing, piercing; test
      in the armoury scenario); 2. salvage, arcane dust, soul shards; 3. the smith and the forge.
    - **Open questions:** which special affixes to start with; where the smith stands (surface or keepers' rooms);
      salvage only at the smith, or anywhere from the pack.
