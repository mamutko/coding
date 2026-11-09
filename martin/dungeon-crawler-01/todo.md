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
