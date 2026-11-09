# Dungeon Crawler 01 — Ideas / TODO

Ideas for future work, numbered so they can be referred to by number. When an idea is implemented, describe it
in `README.md` and remove it from this list (keep the numbers of the remaining ideas unchanged).

2. **More potions:** life regeneration over a period of time, speed potion. (The iron skin potion is done.)

3. **Scrolls** — support for using scrolls. Kinds:
   - defensive magic — increase armor; bounce enemies off after they hit the hero;
   - conjuring — conjure a monster that fights alongside the hero;
   - offensive magic — freeze blast (freezes monsters within a radius for 4 s), fire blast (deals damage to
     monsters within a radius).

4. **Incendiaries** — the ability to throw explosive projectiles.

5. **Weapon enchantments** other than stat improvements:
   - freeze the monster on a critical hit;
   - knock the monster back on a critical hit;
   - cleaving — every monster hit takes 100 % damage.

6. **Item valuation** — items have a value.

7. **Keepers of the Crypt** — merchants where the hero can buy and sell items and services.

10. **Multiplayer** — several players exploring the crypt together online. See the `multiplayer-game` skill for
    the generic mechanics (PeerJS handshake, WebRTC data channels, host-authoritative simulation).

11. **Stairs up** — going back up the stairs to earlier (shallower) levels, i.e. lower depth numbers. Open
    question: levels are currently generated fresh and never kept, so going up either regenerates the level or
    requires remembering visited levels (layout, what was looted and killed).

12. **Better wall visuals** — improve how the dungeon walls look.

13. **Animated doors** — doors visibly swing open (and shut, see 14) instead of switching state instantly.

14. **Closing doors** — the hero can close an open door again.

15. **Limited ammo** — bows need arrows; each shot uses one. Arrows are a stackable pack item (like potions).
    - **Different kinds of arrows**, e.g. explosive and freeze arrows.
    - **Quiver slot** (preferred): a new paper-doll slot holds the arrow stack the bow shoots, so the player
      equips a bow + arrows combination by filling both slots. (Alternatives considered: an arrow quick key that
      makes a stack the active ammo — could still be added on top, as a queued action like a weapon swap; or
      always shooting the best / first arrow stack in the pack.)
    - **Special quivers** — unique items that go in the quiver slot instead of an arrow stack, e.g. a *magic
      quiver of limitless arrows* that never runs out.

16. **Item quality and wear.**
    - **Quality** — a roll on an item's base stats (weapon damage, armor, built-in jewelry bonus), e.g. ±15 %, so
      two common items of the same type and item level can differ. Shown in the name (*Crude*, *Fine*,
      *Superior*, …) and/or only in the numbers.
    - **Wear** — items wear out with use (weapons when hitting, armor when hit) and lose effectiveness as they do.
    - **Fixing** — some of it can be fixed: repairing wear (and perhaps improving quality) at a shop (see 7) or
      with a hero skill.
