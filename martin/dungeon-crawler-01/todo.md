# Dungeon Crawler 01 — Ideas / TODO

Ideas for future work, numbered so they can be referred to by number. When an idea is implemented, describe it
in `README.md` and remove it from this list (keep the numbers of the remaining ideas unchanged).

1. **Item action buttons in mouse mode.** The action buttons that touch mode shows in the equipment overlay
   after an item is tapped (Equip, Drop, Unequip, Drink, Clear key, Quick key 1–0) don't appear when the mouse
   hovers an item. They are a good idea everywhere, so update mouse mode:
   - the buttons are always present;
   - a single click on an item opens the same overlay as in touch mode;
   - a double click on an item equips it right away.

2. **More potions:** life regeneration over a period of time, iron-skin (armor) potion, speed potion.

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

8. **Overhaul the equip and attack system.**
   - The player can equip other things than weapons: instant-use items such as potions or scrolls. An equipped
     instant item is used automatically (no "attack" click needed), and afterwards the previously equipped
     weapon is equipped again. For example, a health potion has to be equipped to be used, but it is then drunk
     at once and the weapon comes back.
   - This makes it possible to sequence attacks and item uses. Each one has a cost in time.
   - **Item uses are queued.** If the player has quick keys for items and presses 3, 4, 5, 6 in quick
     succession, and all are potions / scrolls used automatically, they are queued, and each use takes its set
     time.
   - **Point-to-attack clicks are not queued** this way. If the player clicks a monster 4 times in 2 s but one
     attack takes 1 s, this must not build a 4 s queue. Instead, a click attack is queued for the next moment
     the hero is free, and any further click attack replaces the one already waiting in the queue.
   - **Walking is independent of the queue.** The hero can keep walking while items are being equipped and used.
   - **Avoiding a long queue** that leaves the player watching while monsters attack:
     - when a queued use comes up and would be pointless (e.g. a health potion at full life, or a scroll whose
       effect is already active), it is skipped and takes no time;
     - item uses are short, so even a well-filled queue drains quickly.
   - The queue has no length cap, isn't cleared by player input, and isn't shown on screen.

9. **Health potions in the inventory grid.** Stop treating the health potion as a special item with its own
   counter: it goes in the regular inventory grid, but stays stackable — one stack takes a single cell and
   records a count.
