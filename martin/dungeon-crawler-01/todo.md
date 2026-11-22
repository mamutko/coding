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

10. **Multiplayer** — several players exploring the crypt together online. See the `multiplayer-game` skill for
    the generic mechanics (PeerJS handshake, WebRTC data channels, host-authoritative simulation).

11. **Stairs up** — going back up the stairs to earlier (shallower) levels, i.e. lower depth numbers. Open
    question: levels are currently generated fresh and never kept, so going up either regenerates the level or
    requires remembering visited levels (layout, what was looted and killed).

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
    - **Quality** — a roll on an item's base stats (weapon damage, armor), e.g. ±15 %, so
      two common items of the same type can differ. Shown in the name (*Crude*, *Fine*,
      *Superior*, …) and/or only in the numbers.
    - **Wear** — items wear out with use (weapons when hitting, armor when hit) and lose effectiveness as they do.
    - **Fixing** — some of it can be fixed: repairing wear (and perhaps improving quality) from a Keeper of the Crypt (the market, see README) or
      with a hero skill.

17. **Dragon** — a big dragon boss with a large, articulated body (planned, not started).
    - **Where:** the boss of depth 13 and every 8th depth after it (v96; first sandbox only, v95).
    - **Why one big sprite doesn't fit the engine:**
      - *Depth sorting* — every drawable has one sort key (`x + y`) and is drawn whole. A dragon 6–8 tiles long
        would be drawn entirely in front of or behind the hero, walls and pillars, so the wrong part covers them.
      - *Sheet size* — a tile is 96 px wide, so a 7-tile dragon is ~700 px across. 8 directions × 8 frames of
        800×600 is ~245 MB of decoded image memory; phones can't take it.
      - *Stiffness* — a whole-body sprite turns in 45° steps and plays one loop: no curling neck or swinging tail.
      - *Art consistency* — the image-model pipeline already drifts between directions on a hero-sized figure;
        64 consistent frames of a big detailed body would be very hard.
      - *Collision and pathing* — monsters are one circle (radius capped at 0.48) moving on the tile grid; a
        dragon can't fit through corridors.
    - **Recommended: a body made of parts, each sorted separately.** Every piece is its own drawable with its
      own sort key, which fixes the sorting (the tail sorts at the tail, the head at the head) and gives the
      articulation for free.

      | Part | How it's drawn | Art |
      |---|---|---|
      | Torso | Pre-rendered sprite, 8 directions, 2–3 breathing frames | ~300 px frames, ~15 MB |
      | Head | Pre-rendered sprite, 8 (ideally 16) directions × jaw closed / open / roaring | small |
      | Neck and tail (8–12 segments) | One top-down scale texture per segment size, rotated and squashed onto the floor plane at runtime | 3–4 small images |
      | Wings | Painted flat, projected onto a tilted plane, flapped by animating the plane's angle (+ 2–3 folding frames) | 2–3 images, mirrored |
      | Legs | 4 short limb sprites; feet stay planted and step when they fall behind (simple two-bone IK) | 1–2 images |

      - *Spine* — the head steers; neck, torso and tail segments follow the head's past path at fixed spacing,
        like a snake.
      - *Height* — each segment can be lifted off the floor (the floating wraiths' offset), so the neck can rear up.
      - *Runtime rotation* normally looks wrong in an isometric view, but works for the neck and tail because
        they're painted from above and projected onto the floor.
      - *Cost* — ~400–600 lines for a new multi-part entity type (update, draw, hit-testing); ~20–30 MB of art
        instead of 245.
    - **Other options considered:**
      - *Scaled-up single sprite* (like the Pit Demon, but huge) — cheapest; works only if the dragon stays
        rooted in the middle of a big room and just turns to face the hero (sorting mostly avoided by keeping it
        away from walls). Still stiff, and the sheet is large even with 4 frames.
      - *3D model rendered to sprites* (offline into sheets, or live in WebGL with a camera matching the isometric
        view) — smoothest via skeletal animation, but doesn't match the painted look; repainting frames with AI
        brings back the drift. Live 3D also needs its own answer for overlap with walls.
    - **Gameplay and integration:**
      - *Lair* — a big boss room (~20×20 or more) with a gold-hoard decal, a few pillars (good for testing
        sorting), possibly lava or a lake. The dragon never leaves it.
      - *Collision* — a circle per segment; clicks and attacks hit any segment, all sharing one health pool.
        The head could be a weak point (×1.5 damage).
      - *Attacks* — fire breath in a cone (reusing the fire bomb / burning system); a tail sweep punishing
        standing behind it; a bite in front; a wing buffet that knocks the hero back; later perhaps a takeoff
        phase (only a shadow on the ground, then a slam on landing).
      - *Camera* — zooms out to ~0.7 during the fight so the whole body fits on screen.
      - *Existing systems* — the per-segment freeze tint already works with `tinted()` (boss freezes last 0.4×);
        lake reflections, burning and the green boss glow work too. Bake the glow in rather than a CSS filter per
        segment: per-draw filters caused 1 fps on boss levels in v84, and a dragon has ~20 pieces.
      - *Death* — segments collapse one after another from the tail up, then the guardian's chest unseals.
      - *Sound and music* — roar, breath and wing-flap sounds; the choir boss track.
    - **Steps:**
      1. Standalone prototype (like `ice-prototype.html`) with placeholder shapes: spine following, leg stepping,
         wing flap, per-segment sorting next to a hero and pillars, camera zoom. Tune proportions and movement
         before any paid art.
      2. Concept art: a few reference paintings to pick from (~$0.04–0.19 each); then the parts painted from the
         chosen one, using the sprite-animation skill's per-direction workflow for the head and torso.
      3. Engine: the multi-part entity type (drawing, sort keys, hit areas, collision, shadow); then lair
         generation, AI and attacks, and a sandbox scenario starting in the lair.
      4. Polish: sounds, death sequence, balance, README and versions.
    - **Decided:** a body of **articulated parts** (the recommended option below); it
      **stays on the ground** (no flying, takeoff or landing).
    - **Step 1 is done:** `dragon-prototype.html` (see the README's file list), with placeholder shapes.
    - **Step 2 is done:** the crypt dragon (concept 2) painted in the game's style (`art/characters/dragon/`): the
      body with its legs as a walking sprite (the trunk alone looked like a grub, so the legs are painted, not IK),
      the head (mouth closed and open), the wing, a bone spike, the tail club, and the body's scales for the neck and
      tail; in the prototype as *Look: Painted*.
    - **Step 3 is done (v95):** the dragon in the game (`index.html`, README "The dragon") and the sandbox's
      **The dragon's lair** scenario. Left for step 4 (polish): real sounds (roar, breath, wings) instead of the
      synthesised ones, an ice tint while frozen and flames on it while burning, balance, and the dragon in the
      catalog (`tools/catalog`) and the balance simulation (`tools/simulation`).
