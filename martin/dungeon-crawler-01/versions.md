# Dungeon Crawler 01 — Versions

What each version of the game added, newest first. The version is `VERSION` in `index.html`, shown at the
bottom right of the title screen. The game's full state at any version is in git history (see
[Going back to a version](#going-back-to-a-version)). Kept by the `version-tracking` skill
(`.claude/skills/version-tracking/SKILL.md`).

Small changes that build on the one before are merged into one entry (e.g. *v38–v40*) with a single feature
list. The **Commit** line names the commit of the entry's last version; the newest entry gets its commit when
the next version is recorded.

## v157 — polearms: reach, not sweep; the catalog lists every weapon kind (2026-11-27)

Commit: *(the next version records it; until then, the latest commit that set `VERSION = 157`)*

- Glaive and Halberd: a longer reach (2.5 tiles, was 2.3) and a narrow arc, a little narrower than a sword's (was a
  half circle). Their strength is striking from further away.
- The catalog (catalog.html) now has flails and polearms, and shows each weapon kind's arc, the share of the blow
  the other monsters in it take, and a flail's knockback.

## v155–v156 — the Rift's horde topped up to two players' worth; a satchel on the surface; the armoury (2026-11-27)

Commit: 0b66ec9

- The Rift's big room and lake are filled up to two players' worth of monsters whenever someone comes in, counting
  what's still there: a real horde from the start, but no longer growing past that with every player who joins.
- On the surface, 40 tiles west of the portal, lies a satchel. Open it like a chest: a rusty short sword and a pair
  of leather gloves. (v156: it is full again on every visit, like everything on the surface but the dial.)
- v156: a sandbox scenario, *The armoury*: every weapon and armor type on the floor of a hall, packs of monsters to
  the north and single foes to the south, ever stronger.

## v154 — flails and polearms, for fighting crowds; axes and bows rebalanced (2026-11-27)

Commit: f450b40

- Flails spin all the way round, hitting every monster in reach with the full blow and knocking them back; they hit
  weaker and slower to make up for it. Flail from depth 3, Morning Star from depth 10.
- Polearms sweep a half circle at a long reach (the front rank and the one behind), every monster with the full blow.
  Glaive from depth 6, Halberd from depth 13.
- Axes do a little less damage (about 8 %) but cleave harder: 40 % to the other monsters in the arc (was 25 %).
- Bows and crossbows do about 10 % less damage. (Items already found keep their numbers.)

## v153 — the bigger side wins a merge; the monster load kept even (2026-11-27)

Commit: 341f1c3

- When players who were split apart meet again, conflicts (monsters both sides ran, loot, doors) go to the side with
  more players; equal sides to whoever entered the Rift first.
- The monsters are kept spread evenly over the players: a few idle ones at a time pass from the busiest player to
  the least busy, out of sight.

## v152 — monsters open doors (2026-11-27)

Commit: 93570ec

- Skeletons, Pit Demons and ghouls chasing you open closed doors in their way, after a moment's fumbling.
  Wandering skeletons sometimes open a door they come to. Spiders and wraiths are still held back by a closed door.

## v151 — doors close; doors have owners; the world kept in step through other players (2026-11-27)

Commit: a88de08

- Click an open door to close it again (not while anyone stands in the doorway). Most monsters can't open doors
  (v152: skeletons, Pit Demons and ghouls can). Experience only for the first opening.
- In the Rift every door has an owner, like chests and loot, who has the last word on whether it is open.
- The repair of lost messages now passes on everything a player knows, so the word gets through even when the
  owner can't reach you directly.

## v150 — doors, chests and loot kept in step (2026-11-27)

Commit: e6d41ea

- If messages are lost (a break, a reconnection), the games now repair their view of the world: open doors, opened
  chests, urns and bones, items and gold dropped or picked up. Any two connected players agree within about 10 s.
- Trying to open something another player already opened now shows it opened at once.

## v149 — monsters never fade; split realms merge again (2026-11-27)

Commit: 493c198

- When a player leaves the Rift, their monsters stay: the ones fighting someone go to that hero's player, the rest are
  spread evenly over the players still there. Bosses stay too, so their chests stay sealed.
- Players separated by a long network break find each other again and merge: a monster both ended up running stays
  with the player who was in the Rift first, and nothing killed meanwhile comes back.

## v147–v148 — player against player: a sword on the dial draws blades (2026-11-26)

Commit: fa8ec0d

- A sword (any) on the portal's dial makes the realm one where heroes can hurt each other: with swings, arrows and
  fire bombs (v148: fire bombs everywhere). The portal warns before you enter, and the log on arriving.
- Attack the spot where the other hero stands (right click, or Shift + click). Their armor counts, the number shows
  over them for everyone, and a death says who struck the blow.
- v148: other heroes can be clicked as targets where blades are drawn (right click: walk in and strike, or shoot),
  and a fire is a fire: any fire bomb burns any hero in every realm, the one way to hurt someone where blades aren't drawn.

## v141–v146 — the whole fight seen by everyone, reconnecting instead of splitting, multiplayer debug (2026-11-25)

Commit: 1b1290a

- In the Rift, every player sees the others' sword swings, arrows, monster blows and wraith bolts, and every damage
  number: on monsters, whoever struck them, and over heroes that are hurt.
- A player who goes quiet for 3 s is now "lost", not gone: the game reconnects and catches up on the monsters,
  instead of carrying on as two separate games. Only after 30 s lost (or 10 s after closing the tab) has that player left.
- The debug overlay (Ctrl+D) lists each player in the Rift: ping, monsters and objects it runs, messages, failed
  sends, late heartbeats, losses and reconnects; and a green dot flashes on each monster or object a message just
  came about, in the scene and on the minimap (v142: bigger in the scene, and on the minimap too). v143: a blue dot
  on each monster your game runs; both colours half see-through.
- v143: a monster waking its neighbours now wakes other players' monsters too (it only woke your own).
- v144: swings, arrows, monster blows, bolts and damage numbers go on a channel of their own that never waits for a
  lost message, and only to players within 20 tiles of them. The debug overlay shows messages and kB a second.
- v145: monster updates adapt to each player's connection: re-sent every 66 ms when it's good, slowing to 600 ms when
  messages pile up, the ping rises or heartbeats come late; the debug overlay shows the pace, green to red.
- v146: a monster more than 20 tiles from a player's hero no longer jumps the queue when its plan changes; its new
  plan reaches that player with its regular update (about every 1.2 s beyond 30 tiles).

## v140 — the Rift's new layout: boss room, big room, lake by the east corner, rooms shared by thirds (2026-11-25)

Commit: df6518a

- The portal and start room are back on the north side: in the middle of the Rift's north-west edge.
- The lake lies beyond the other rooms' north-east edge, by their east corner, with nothing behind it.
- A boss room near the south corner: everyone who comes in adds a boss one depth above their own, each with its own
  guardian's chest, sealed until that boss dies.
- A big room (twice a crypt big room) in the middle: everyone who comes in adds a horde to it, and wraiths to the lake.
- The first player fills ⅓ of the ordinary rooms, each who joins ⅓ of those left (was one crypt level's worth each).

## v139 — monsters spread evenly through the Rift, a quiet zone, the lake far away (2026-11-25)

Commit: 0c60439

- Each player's monsters and treasure are spread evenly over the Rift from near the portal to far (they were put
  in the farthest rooms, which left the rooms near the portal empty).
- The two rooms nearest the portal are a quiet zone, with one skeleton for a warm-up.
- The Rift's start room and portal are in the map's south corner, as far from the lake (north corner) as it gets.
- Fixed: since v132, arriving on a new level kept the hero's last click target, attack target and swing.

## v138 — a lake in the Rift (2026-11-25)

Commit: 4b85d57

- The Rift always has a lake room in its north corner (water, reflections, wraiths, the chest of scrolls of frost);
  its start room and portal lie just south-west of it, and the portal is mirrored in the water.
- Players joining get the lake too; a scroll of frost read there makes the same ice for everyone, and each game
  drowns only its own hero and monsters when it melts.

## v137 — handover, hidden tabs and shared fire bombs in the Rift (2026-11-25)

Commit: 3c0ccf6

- A player leaving hands its monsters over: one fighting someone passes to that player, the rest fade away (the
  player in the Rift longest decides, for everyone).
- A hidden tab hands its monsters over at once and its hero is "away" (faded, left alone); back within 60 s it plays
  on, else it leaves the Rift (saved before the portal).
- Fire bombs are seen by all; only the thrower's fire burns (monsters through their owners), and a companion's fire
  does not hurt your hero.

## v136 — shared loot in the Rift (2026-11-25)

Commit: a4ed4a0

- Everything that drops in the Rift (from monsters, chests, urns, bones, or a player's pack) is seen by everyone and
  belongs to whoever dropped it; the chests, urns, bones and gold of each player's rooms likewise. A player joining
  brings chests and gold for its rooms too.
- Picking up or opening another player's things asks that player's game: the first to ask gets it; it vanishes for
  the others. The one who opens a chest gains its experience; its owner rolls what is inside.
- Doors open for everyone. A player leaving leaves its loot to the player in the Rift longest.

## v135 — fighting together in the Rift (2026-11-25)

Commit: 191e68b

- Every monster belongs to the player who brought it; a player joining a Rift brings its own share (monsters of its
  own deepest depth) into rooms no one has claimed.
- Everyone sees every monster: its owner runs it and sends its state and intent (most often for those near each
  player); the others predict it smoothly between states.
- Monsters go for any hero in the Rift; blows on another player's hero are taken by that player's game. Hits on
  another player's monster go to its owner, who decides its death and shares its experience by damage done (at
  least 25 % each). Frost freezes them for everyone; bolts are seen by all.
- A player leaving takes its monsters with it. Loot is not shared yet.

## v134 — the portal 10 tiles farther north, the dial 2 tiles farther out (2026-11-25)

Commit: 013fdbd

- The Rift's portal stands at (−29, −29), about 60 tiles north of the crypt; its dial at (−23, −23), about 8.5
  tiles in front of the arch (2 tiles more), with grass between the steps and the dial.

## v133 — players in the same Rift see each other (2026-11-25)

Commit: 9ef3503

- The portal's question says who is in the realm (Supabase Realtime presence).
- Entering a realm others are in joins them: a WebRTC connection to each, the Rift's map from the eldest, and the
  other heroes walking about, with their names and life bars, smoothly interpolated. Two players entering at once
  end up in the same Rift. Leaving, dying or closing the page tells the others.
- Not shared yet: monsters, chests, loot, fighting (next phases).

## v132 — the Rift's portal, its dial and the Rift played alone (2026-11-25)

Commit: 1e87dcf

- A stone **portal** with a swirling vortex stands about 50 tiles north of the crypt (new AI art in three layers:
  the arch, depth-sorted; its platform and a rune **dial** on the ground).
- Items laid on the dial choose the **realm** (id and a two-word name from their hash: ordinary items give a shared
  realm, a magic or rare one a private one); they stay on the dial between visits (saved).
- Walking into the arch asks, then enters **the Rift**: a 110-tile, 34-room dungeon with no stairs, its monsters and
  loot of the deepest depth reached, in the rooms farthest from the way in; the portal's other end stands in its
  start room. Saved on entering and on leaving, never inside; death there loses what was won inside.
- Sandbox: *The portal and the dial*.

## v131 — the realm key includes affixes (2026-11-25)

Commit: 74268b5

- `multiplayer.md`: the dial's realm key is built from the whole items (affixes, rarity, rolled names), so a magic
  or rare item on the dial opens a private realm; friends share a realm with ordinary items. No game changes.

## v130 — scrolls of surface escape and return (2026-11-25)

Commit: 463484c

- **Scroll of Surface Escape:** read in the crypt (4 s, standing still, voiced Latin incantation, its words over the
  hero's head, a column of light) to go up to the surface; it becomes a **Scroll of Return** to that depth, which,
  read on the surface, takes the hero back down to a new level of it and is used up. Dying when the words end
  kills the hero at once, with no save. The hero is saved on arrival either way.
- Garrick gives one in the first meeting, and another on request when the hero has none; every keeper sells them
  (60 gold, never sold out).
- The deepest depth reached is saved (`maxDepth`, for the planned Rift).
- Sandbox: *Surface escape* and *Scroll of return* scenarios.

## v129 — multiplayer specification (2026-11-25)

Commit: cb74983

- `multiplayer.md`: the planned online co-op mode (the Rift beyond a portal north of the crypt, realms chosen by
  items laid on a dial, Supabase + WebRTC, ownership of monsters and loot) and the Scroll of Surface Escape. No
  game changes.

## v127–v128 — item comparison as a table (2026-11-24)

Commit: e59e34d

- The item comparison is a table, labels on the left: damage as "+6–8", attacks per second as a change in
  percent, no computed values (the base DPS row is gone).

## v126 — the dying message names no time (2026-11-24)

Commit: 3553794

- When the hero drops to 0 life the log says "You are dying! Heal yourself, quickly!" instead of naming the seconds
  left.

## v125 — fuller item comparison (2026-11-24)

Commit: 670b47f

- A pack weapon is compared with the last equipped weapon of its class (melee or ranged), not just the equipped one.
- The comparison lists every difference, bonuses from affixes included, as + / −, with the other item's name in
  plain text; for all gear, and in the action box below the buttons.

## v123–v124 — the voice-over skill; a shorter walk-away distance (2026-11-24)

2bf2194

- The clip making moved into the repo's new voice-over skill (`make_voices.py`); `tools/story/voice.js` collects
  the lines and calls it, and can now also check new clips' words by transcribing them (`--verify`).
- Characters count the hero as walking away 1.2 tiles beyond the closest point of the conversation (was 2), so
  stepping away ends a talk sooner; the panel dims at 0.6 tiles.
- Fix: a character that walks up to the hero (`walkUp`) did so for the whole conversation, following the hero, so
  walking away never worked; it now walks up once and stays where it arrives.

## v121–v122 — dying instead of dying at once, slower potions and swaps (2026-11-24)

Commit: 2d3d509

- At 0 life or below the hero is **dying**, not dead: 2 s to heal back above 0 (a potion), or the hero dies.
  While dying: a throbbing crimson vignette, a heartbeat, the hero glowing red, a draining red ring round the hero's
  feet and a pulsing life orb showing the negative life.
- Drinking a potion takes 0.6 s (was 0.4 s), and it works half way through, at 0.3 s (was at once).
- Equipping or unequipping a weapon takes 0.5 s (was 0.2 s).

## v120 — Garrick the Hunter at the crypt, and voice-over (2026-11-24)

Commit: 8da2c2e

- The game's story has its first character: **Garrick the Hunter**, on the lawn by the crypt's door. He calls out
  as the hero comes near and walks over, gives vague warnings about what lies below, and, asked for help, one
  health potion (only once). He calls the hero "traveller".
- **Voice-over:** lines are spoken aloud, the hero's choices too (in the male or female hero voice, by the look).
  `tools/story/voice.js` makes the clips with OpenAI speech (about $0.001 a line) and keeps them in step with the
  dialogue. Garrick and the hero's side are voiced; the choices wait until a line has been spoken.
- Characters can talk on the surface.

## v118–v119 — story descriptions in free writing; characters that hail, walk up, wander and face you (2026-11-24)

Commit: 9d6366f

- A story is now two files: `story/<name>.md`, a free description at any level of detail (exact lines, a sentence
  for a scene, or its logic in technical terms), and `story/<name>.js`, the dialogue the game plays, written from
  the description with judgement and kept in step with it. The Markdown compiler is gone.
- The dialogue files are readable by hand: items `{ say, text }`, `{ choose }`, `{ do }`, `{ go }`, with conditions
  and effects as short JavaScript strings that the game turns into functions when it loads.
- `tools/story/check.js` checks the dialogue files (speakers, jump targets, unreached nodes, JavaScript).
- The demo's description is rewritten at mixed levels of detail.
- A click on a character walks the hero all the way up to it; while they talk, the hero and the character turn to
  face each other.
- New character settings, which a conversation can override: `hail` (the distance it calls out from; 0 waits for a
  click, replacing `starts`) and `walkUp` (it comes over as it hails); and `wander` (a story NPC strolls about).
  `talk` is gone. In the demo, Tobias hails and walks over, Vesper wanders.
- Walking away is measured from the closest the hero has been during the conversation, and `leave` defaults to 2
  tiles (was 6). The panel fades out quickly (0.15 s, was 0.45).

## v116–v117 — tree variants, groves, and shadows for the small things (2026-11-23)

Commit: 62a6700

- Two more variants of each tree kind (15 trees): a low-forked and a tall oak, a leaning and a twin-trunked pine, a
  twin and a young birch, a golden and a half-bare red maple, a broken snag and a leaning dead oak.
- The forest grows in groves: one kind tends to dominate an area (a pine wood, a maple grove, a stand of dead trees),
  mixing at the edges, and woods and meadows are larger, with gradual edges.
- Bushes, flowers, rocks, mushrooms and grass tufts cast soft, short shadows to the lower right that hug their bases
  (with a faint contact shade), so they sit on the ground.

## v114–v115 — five big trees replace the surface's trees (2026-11-23)

Commit: 7d99831

- The surface's forest is made of big trees in five kinds: oak, Scots pine, silver birch, autumn maple and a dead
  tree, all AI-painted to the oak's brief (wide sparse crowns, partly exposed roots sinking into the ground, a soft
  moonlight shadow) and cut into the same three layers. The four small trees are retired.
- Trees stand farther apart (each keeps the 7 × 7 tiles around it), so the crowns don't close into a canopy.
- The trees' cast shadows are softer.
- The birch's roots join its trunk without a visible cut (their fade starts at the trunk's base).
- The sandbox's Big trees scenario shows one of each kind around the hero.

## v110–v113 — big oaks in three layers (sandbox) (2026-11-23)

Commit: 66b9716

- A big oak for the surface, AI-painted with a wide, sparse crown and a partly exposed root system, cut into three
  layers: the roots lie on the ground (sinking into it toward their tips: brown near the trunk, then only faint
  bumps in the grass, never beyond the painted roots; the shading eases in across the transition), the trunk is depth-sorted with
  the hero, and the crown is always on top and never fades (the hero shows through its gaps).
- For now only in the sandbox's new **Big trees** scenario (three oaks around the hero, and half the forest's trees
  big oaks); the game's surface is unchanged.
- Each big oak casts a soft shadow toward the lower right, baked into its ground layer: the art is lit from the
  upper left, taken as the moon's direction. Big oaks are never mirrored, so their light stays consistent.

## v109 — the hero in front of the crypt, items in front of walls (2026-11-23)

Commit: a609b50

- The crypt on the surface is depth-sorted by the middle of its square footprint instead of its front corner, so the
  hero (or anything else) standing along its front walls is drawn in front of it, no longer half covered.
- Items on the floor are depth-sorted with walls, props and characters: a wall, chest or monster behind an item no
  longer cuts its icon off (its floor glow stays flat on the floor).

## v108 — the Heavy Crossbow reloads in 1.2 s (2026-11-23)

Commit: be62413

- The Heavy Crossbow reloads in 1.2 s instead of 0.95 s: the same damage per second as the War Bow (about 37), with
  bigger, slower shots, a choice rather than a strict upgrade. (Made alongside the dragon, where it was numbered
  v101: 45eb234.)

## v102–v107 — the dragon on real legs, turning in 32 directions (2026-11-23)

Commit: 4177fdb

- The dragon's body is a still painted sprite in **32 directions** (17 painted, 15 mirrored; was 8 with a walk cycle), with its lower legs
  cut off; the torso lies along the heading snapped to those directions, so the neck and tail always join it where
  the painting has them.
- **Four IK legs** of painted bones and feet: each foot stays planted on the floor and steps (diagonal pairs taking
  turns) when it falls behind, so the dragon no longer slides over its feet.
- **One shade:** every body view, leg bone and foot is brought to the same colour when the atlas is built, so the
  dragon no longer changes shade as it turns; the neck and tail keep their mirrored scale texture (it makes each node
  look rounded) and get a sheen like the painted leg bones': the lit scales glint, the far side falls into shadow;
  two beads per node gap instead of one, each with a bone spike, for a ribbed neck and tail (drawing only); each
  bead tucks under its neighbour toward the body, so none shows its whole rim where the neck or tail curls.
- A smaller dragon atlas (444 KB, was 883 KB).

## v101 — a guardian's chests scenario (2026-11-22)

Commit: f88a1b9

- A sandbox scenario, **Guardian's chests**: the dragon's lair at depth 13 emptied of everything but six unsealed
  guardian's chests; open them, then play on through the rest of the level.

## v100 — a lake every 4 depths (2026-11-22)

Commit: f5decf4

- The underground lake room, with its wraiths and its chest of 4 scrolls of frost, comes back every 4 depths: depth
  8, 12, 16, 20, … (before only depth 8).

## v99 — frost scrolls in the dragon's chest (2026-11-22)

Commit: cce1a33

- The guardian's chest in a dragon's lair also holds 3–5 scrolls of frost.

## v98 — the dragon in the game (2026-11-22)

Commit: 87470f4 (made on a branch alongside the crossbows, where it was numbered v96)

- The dragon is the boss of depth 13 and every 8th depth after it (21, 29, …): there the boss room is its lair, 20–23
  tiles a side, with pillars, braziers, the guardian's chest and its gold hoard, and the dragon asleep on it.
- Slain, it spills its hoard: 6 rare and magic items from 4 depths deeper, 5 big piles of gold, 4 potions and 3 fire
  bombs, besides the guardian's chest.
- The sandbox's dragon's lair scenario now starts in the game's own lair at depth 13.

## v97 — the dragon, in the sandbox (2026-11-22)

Commit: d747a1a (numbered v95 on its branch)

- A dragon boss made of parts: Nythrakar, the Crypt Wyrm, painted in the game's style (a walking body with its legs,
  a head with an opening jaw, a curving neck and tail with bone spikes and a spiked club, wings that fold and beat),
  each part sorted on its own against walls, pillars and the hero.
- It sleeps on a gold hoard until you come near, wakes with a roar, follows you, and bites, breathes fire (you go on
  burning), sweeps its tail at you behind it and beats its wings to throw you back. Swords, arrows, fire bombs and the
  scroll of frost work on whichever part they reach; the head takes ×1.5. The view draws back during the fight. Slain,
  it sinks from the tail to the head and unseals the guardian's chest.
- Only in the sandbox for now: the new **The dragon's lair** scenario (depth 10).

## v95–v96 — crossbows (2026-11-22)

Commit: 9268974

- Two crossbows, the strongest ranged weapons. They shoot like bows (DEX, same arrows and reach) and drop with the
  bows, each with its own painted icon:
  - the **Heavy Crossbow** (34–56 damage, 0.95 s, from depth 15), ahead of the War Bow;
  - the **Gilded Arbalest** (62–104 damage, a long 1.4 s reload, from depth 18), the best of all.
- A **Crossbows** sandbox scenario: depth 18, all three top ranged weapons on quick keys to compare, sleeping
  monsters, and a bar with each weapon's damage, reload, last shot and a tally of shots.

## v94 — dialogue with characters (2026-11-21)

Commit: c1cb7a7

- A dialogue system: conversations written in Markdown (`story/*.md`), compiled and checked by
  `tools/story/build.js` into `story/story.js`. Lines, choices, conditions and effects in JavaScript, a property bag
  on the hero and one per character, consequences in the game (gold, items, a keeper's discount, a monster that
  attacks or lets you pass).
- The game keeps running while characters talk, in a light panel above the quick bar. Characters can start talking
  by themselves when you come near, or wait for a click; walking away gets a reaction, and coming back picks the
  conversation up where it stopped. Monsters can talk too.
- The game's own story is not written yet, so the game plays as before. A demo story (Old Tobias, Vesper the
  Sorcerer, a champion skeleton) is in the sandbox's new **Dialogue** scenario.

## v93 — the attack button shows the action in progress (2026-11-20)

Commit: 1ecb10e

- While the hero is busy, a glowing arc runs round the attack button's rim in the action's colour, and behind the
  icon an animation shows what it is: a crescent slash (melee), a tightening ring (bow), the potion welling up, frost
  motes and runes (scroll), a soft pulse (a throw or a weapon swap).

## v91–v92 — a Voices slider, the Huntress's voice, a cast sound, a wider frost blast (2026-11-20)

Commit: d6b1ec4

- The Huntress reads incantations in a female voice (Google, Leda, the male voice's engine and prompt).
- A **Voices** volume slider in the equipment screen (default 75 %), for the hero's spoken incantations.
- A rising **cast sound** under a scroll's reading, building to the blast: **Gathering frost** (picked from three;
  Rising hum and Crystal riser stay in the sandbox's frost scenario).
- The scroll of frost reaches 1 tile farther: monsters freeze within 5 tiles, water within 11.

## v90 — the hero's own voice for incantations (2026-11-20)

Commit: 76929f5

- Each hero look has a voice for incantations (`HERO_VOICE`): the male looks keep the incantation in use (Google
  `gemini-3.8-flash-tts`, Algenib; now `assets/sfx/incantm1.mp3`, its prompt recorded in the README and in each
  male hero's `character.json`); the Huntress gets a female voice once one is picked (until then the male one).

## v88–v89 — the frost blast shows its reach (2026-11-20)

Commit: 16e87cd

- The scroll of frost's blast has a visible wave: a glowing ring running out from the hero that stops at the
  4-tile freeze radius, with ice shards flung to the same edge, and a ring of rime on the stones there that fades
  out within 0.8 s.
- Frozen monsters stay frozen 1 s longer (6 s; a champion 4 s, a guardian 3 s).

## v87 — scrolls, and the scroll of frost (2026-11-19)

Commit: e282dcc

- **Scrolls**: use items like potions (they stack, bind to quick keys, show as equipped while used) that are read
  aloud; the spell goes off when the reading ends. Found only in a new chest on the lake room's shore (4 scrolls).
- **The scroll of frost**: a 1.6 s Latin incantation ("Gelu, cuncta liga!", an AI voice), then a frost blast
  around the hero. Monsters within 4 tiles freeze solid (5 s; less for stronger ones, champions, guardians), and
  the lake within 10 tiles freezes for 18 s: walkable, scarred with frost on the side of the blast, cracking for
  its last 5 s (from under whoever stands on it), then thawing; anyone still on it drowns. Drops tick on the ice,
  fire bombs shatter and burn on it. New sounds, a sandbox scenario, and the frost scroll icon.

## v86 — the woodsman and scout looks (2026-11-19)

Commit: 1d86a1e

- Two more hero looks, **Woodsman** (`assets/hero4.webp`: short beard, brown hooded half-cloak, olive jerkin) and
  **Scout** (`assets/hero5.webp`: young, black hair, leather vest over a rust-red tunic, green cowl), painted with
  the `sprite-animation` skill (12 frames, all 8 directions). Six looks now, two per row in the cogwheel box.

## v85 — the huntress look (2026-11-19)

Commit: 1058842

- A fourth hero look, **Huntress** (`assets/hero3.webp`): a ranger with a chestnut braid and a moss-green
  half-cloak, painted with the `sprite-animation` skill (12 frames, all 8 directions). Picked like the others, in
  the hero's cogwheel box on the title screen or in the debug overlay.

## v84 — boss levels no longer crawl without the GPU (2026-11-19)

Commit: ae17ba3

- The boss room's **rune circle** is drawn once into an offscreen image (per room and screen scale) and pasted
  each frame, only while on screen. Drawn live every frame (a blur filter and a 26 px shadow), it cost ~800 ms a
  frame whenever the browser was drawing without the GPU: 1 fps on every boss level (seen at depth 11), until
  the browser was restarted. Measured without the GPU: ~880 ms → ~22 ms a frame; it looks the same.

## v83 — a frame-rate readout that sees slow frames (2026-11-19)

Commit: 7a46936

- The debug overlay's frame rate now counts every frame, however slow. Before, frames over 0.25 s were skipped,
  so at 1-2 fps it kept showing its last good value (e.g. 22 fps) and the automatic render scale never stepped in.
- It also shows the slowest frame of the last 2 s and the time per frame of the update steps and of render + HUD,
  to tell slow drawing from slow game logic.

## v81–v82 — the stocky knight drawn a little smaller (2026-11-19)

Commit: 7c9cf1c

- The **stocky knight** look is drawn at 0.96 of its sheet (`CAST_SCALE.hero2`; v81 had 0.93). Its mocap guide was normalised
  to full height, so his short legs had made his torso, head and shoulders larger than the original knight's;
  now he is a little shorter than the knight, as designed. The walk still advances by the scaled stride, so the
  feet stay planted.

## v80 — hero looks: the stocky knight and the mannequin (2026-11-18)

Commit: e0777d7

- Each hero has a **look**, picked in its settings on the title screen (the cogwheel: Knight, Stocky knight,
  Mannequin) or in the debug overlay, and saved with the hero (and in exported heroes).
- **Stocky knight** (`assets/hero2.webp`): the new hero painted with the `sprite-animation` skill, 12 frames per
  direction, all 8 directions painted. Every frame is lined up with its mocap guide frame (the AI drifts figures
  by up to ~8 game px), and the frames advance 8.54 per tile walked, the mocap's own stride, so the foot on the
  ground stays put.
- **Mannequin** (`assets/mannequin.webp`): the skill's standard grey pose guide itself, walking (fpt 8.02).
- The equipment screen's turning portrait shows the hero's look.
- The two new sheets load only when a hero uses them.

## v73–v79 — the Keepers of the Crypt walk; character viewer and a new cast (2026-11-16)

Commit: 9235266

- The four Keepers of the Crypt have full 8-direction walk cycles (AI-painted, OpenAI).
- A keeper always faces the hero. The first time the hero enters its room it walks up to the hero, once, and
  stops a step away; after that it stays put and only turns. It never follows the hero or leaves its room.
- The sandbox's market scenario starts a few steps away, so the keeper walks up.
- Sandbox **Character viewer**: walk around an empty room as any character with a sprite sheet (the hero,
  the monsters, the keepers and the new cast), picked from a grouped list, at a chosen walking speed (down to 0.05×, to see every frame); on phones
  its bar sits at the top.
- A new cast of walking characters, so far only in the viewer: a hunter, a huntress, a village girl and boy, a
  duke, a princess, a female blacksmith and a sorcerer (8 directions × 8 frames each).
- The hunter walks with a real stride now (repainted with Google's model): before, the same leg led in both
  halves of the stride in the side views, so he glided (his SW / SE walk was redone once more in v79).

## v66–v72 — the underground lake (2026-11-15)

Commit: bb18528

- Depth 8 has a huge **lake room** (28–30 tiles a side) in a corner of a larger map: most of it is a still, dark
  underground lake whose far shores lie out of sight and out of reach. The dry shore along its near walls has
  braziers, bones and sometimes a chest; broken pillars stand in the water.
- A group of 8–10 **wraiths** hovers over the water. Wraiths are the only monsters that can cross water; loot
  from one slain over the lake washes ashore. A fire bomb that lands in the water sinks with a splash, but one that hits a pillar standing in the water breaks against it; a fire on the shore spreads its burning oil over the water.
- **Lakes** are drawn as mirror-like water 8 px below the floor, with rounded shores, rock banks on the far
  shores, reflections of walls, props, monsters, lights, projectiles (arrows, wraith bolts, fire bombs in flight) and fire (bomb fires and burning monsters), and drops falling from the ceiling that leave ripples
  (rings plus a refraction that bends the reflections, and a clearly audible drip: a splash tick, a plink and the rebound's smaller plink). Under 28 fps (with Auto resolution on)
  the refraction switches off for the session.
- Sandbox scenario **The underground lake** (with 15 fire bombs), with pickers to compare four drip sounds and
  three bomb-splash sounds (a bomb sinking has its own, heavier sound).
- The fire bombs' fire always looks like **Blaze**; the other looks stay only as a switch in the sandbox's fire
  scenarios (no longer remembered).

## v62–v65 — debug overlay and scenarios from the title screen (2026-11-15)

Commit: 3a4d2dd

- The version number on the title screen is larger; double-click it (long-press on a phone) to open the debug
  overlay, which now shows above the title screen (`Ctrl` + `D` works there too).
- A **Scenarios** button at the title screen's bottom left opens the sandbox's scenario picker.
- The scenario picker shows its loading progress, and why the scenarios stay off if the game fails to start.
- An image that fails to load is tried again (up to 4 times) instead of stopping the game from starting.
- The sandbox artifact embeds its images in the page, so it starts in the claude.ai phone app too; if an image
  still fails, the picker shows what the server answered.

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
  props near the south-west and south-east walls kept in view.
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
