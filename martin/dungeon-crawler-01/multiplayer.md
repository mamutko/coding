# Multiplayer: the Rift — specification

Status: **planned, not implemented.** This is the design for the game's online co-op mode. It is kept apart from
`README.md` (which describes what is built) because of its size; when a phase is built, the parts it implements
move into `README.md` (or stay here and `README.md` links to them) and are marked done in [Phases](#phases).

## Summary

- North of the crypt stands a **portal** into **the Rift**: a large underground realm, one level, no depths.
- In front of the portal lies the **dial**, a ground decal. The items lying on it pick **which** Rift the portal
  opens: their hash, prefixed with the game version, is the **realm id**. Only players with the same realm id meet.
- A realm exists only while a player is in it, and its state lives only in the players' browsers. Browsers find
  each other through **Supabase Realtime** (presence + signaling) and then talk directly over **WebRTC** data channels.
- The first player in builds the layout and spawns monsters and chests for **their** deepest depth reached. Each
  player who joins receives the layout and adds monsters and chests for **their** depth.
- **Every object has an owner** (the player who brought it in). The owner simulates it and decides about it;
  everyone else sends the owner requests (a hit, a pickup) and predicts the object from its latest state and intent.
- **Co-op only**, but the protocol treats heroes as targets like monsters, so PvP can be switched on later.
- To get from the crypt back to the surface, there is the **Scroll of Surface Escape** (Garrick gives one, the
  keepers sell them).

## 1. Scroll of Surface Escape

A use item (an entry in `POTIONS`, like the Scroll of Frost), stacking in the pack and usable from a quick key.

| State | Name | Read where | Effect |
|---|---|---|---|
| fresh | **Scroll of Surface Escape** | in the crypt (depth ≥ 1) | takes the hero to the surface, in front of the crypt door; the scroll becomes a Scroll of Return |
| spent once | **Scroll of Return — Depth N** | on the surface | takes the hero to depth N, built new (levels are never kept); the scroll is used up |

- **Reading takes 4 s.** While reading, the hero cannot move, attack or use anything (other queued actions wait
  until it is over). The incantation appears over the hero's head word by word, one phrase per second, and in the
  log as it finishes:

  > *Per umbras noctis aeternae — aperi mihi viam ad lucem — et redde me superis — ex tenebris in diem.*
  > ("Through the shadows of the endless night — open for me the way to the light — and return me to those above —
  > out of darkness into day.")

  A Scroll of Return reads the reverse: *E luce in tenebras — redi me ad profundum — ubi mortui vigilant — ad
  gradum N.* ("From light into darkness — take me back to the deep — where the dead keep watch — to step N.")
  While reading, a column of pale light grows around the hero (Surface Escape) or a dark swirl sinks into the
  ground (Return); monsters keep attacking.
- **Not interruptible** (for now): damage does not stop it. Only the hero's death does.
- **Dying while reading:** the dying timer (`DYING_T`) keeps running during the read. If the hero is at or below
  0 life when the 4 s are up, the hero **dies at once, with no save** (the normal death: back to the title screen,
  resuming from the last save).
- **Saving:** the hero is saved right after arriving on the surface (escape) and on arrival at depth N (return,
  the usual arrival save). A save on the surface stores `depth: 0`, so the hero resumes on the surface.
- **A Scroll of Return keeps its depth** in the item (`{ pot: 'return', depth: N }`); returns to different depths
  are separate stacks. Reading one in the crypt does nothing ("You are already below."). A Surface Escape read on
  the surface does nothing ("You are already under the open sky.").
- **Does not work in the Rift** ("The Rift does not let go so easily. Find the portal."); the Rift is left only
  through its portal ([§3](#3-the-rift)).
- **Where it comes from:**
  - **Garrick** gives one in his first conversation (a new node with a voiced line, then `give('escape', 1)`), and
    another later if the hero has none (repeatable, at most one in the pack from him).
  - **Every keeper** stocks Scrolls of Surface Escape, always, at a fixed price (suggested 60 gold), beside the
    random stock.
- Icon: a scroll with a pale sky-blue seal (a new cell in the items sheet; Scroll of Return: the same scroll, seal
  turned dark violet, drawn with a filter).

## 2. The portal and the dial on the surface

### Placement

- A second landmark beside the crypt: `SURF.portal`, about 50 tiles **north** of the crypt (screen up = −x −y), at
  world tile ≈ (−22, −23), in another super tile. Generalise the crypt's special case into `SURF.landmarks` (crypt,
  portal): each keeps a clearing free of trees (the portal's: radius 7, wider on its south side where the dial is),
  a minimap mark, and a hover label.
- **Orientation: the arch runs W–E** (constant x + y, flat across the screen), facing south toward the crypt.
  (For the record: constant x + y is W–E; NW–SE is constant y, like the crypt's door wall; NE–SW is constant x.)
  Because every point of a W–E arch has the same depth key x + y, it sorts as one sprite: the hero can walk in
  front of and behind it without slicing it into strips. It is 4 tiles wide.
- **Entering:** walking into the arch's opening (the strip of 2 tiles in the middle of its face) with the dial set
  as wanted. The game first asks Supabase how many players are in that realm and shows: *"Step into the Rift of
  Ashen Hollow? 2 adventurers are inside."* (or *"The Rift lies empty. You will be the first."*), Enter / Stay.

### Art

One image (Gemini, in the style of the crypt building), cut into two parts as with the big trees:

- **Ground decal (the dial):** a round stone dais, about 5 tiles across, in front of the arch, with a ring of
  carved runes and an inner circle where items are laid. Drawn flat under everything.
- **Standing part:** a tall stone arch of broken, rune-cut stones, a swirling violet-blue light filling the
  opening; sorted on its base line (x + y of its foot). The swirl gets a slow shimmer in code (a second copy drawn
  with `lighter`, rotating), a light added to the surface's light, and a soft hum near it (`sfx`).
- The **Rift's end of the portal** is the same arch, drawn over a dungeon floor (the dais without the dial runes).

### The dial: choosing a realm

- The hero drops items on the dial's inner circle like on any floor (drag out of the pack, or Drop in the overlay).
  Items lying there are the **dial items**; picking one up removes it.
- **Realm key** = the multiset of the dial items' **base types and stack counts**, sorted (e.g.
  `longsword×1, potion:health×3, rubyring×1`), so the order of laying them down does not matter. Only the base and
  count, not the random affixes or rarity, so two friends can set the same dial with items they can both find.
  (Option for later: including rarity or the exact item makes a dial "private" — a realm only that item's owner
  can open.)
- **Realm id** = `v<VERSION>-<hash>`, hash = the first 10 characters of SHA-256 (base32) of the realm key
  (`crypto.subtle`). An empty dial is a valid key: the **open Rift**, where strangers meet. Because the version is
  part of the id, players on different versions never meet (and never need to agree on a protocol).
- **The realm's name:** two words picked from the hash out of fixed lists (e.g. *Ashen Hollow*, *Weeping Deep*),
  shown on the dial's hover label, in the entry prompt and on the Rift's HUD, so friends can check they dialled the
  same realm. The portal's light takes a hue from the hash as well.
- **Saved:** the dial items are saved with the hero (`hero.dial`, a new `SAVED_FIELDS` entry; the items as data,
  like the pack), and lie on the dial again when the hero returns to the surface. They are the hero's items: a
  hero with items on the dial does not carry them (they are not in the pack and do not count for anything).
- Only the dial keeps items on the surface between visits; other items dropped on the surface are not saved
  (as now).

## 3. The Rift

- **One level, no depths, no stairs.** Built by `buildLevel` in a realm mode: about 110 × 110 tiles, 30–40 rooms,
  the usual corridors and doors, no lake, no dragon, no boss room (for now).
- **The portal's other end** stands in the start room. Every player arrives there (spread around it) and **leaves
  only through it**: walking into it takes the hero to the surface in front of the portal.
- **Saving:** the hero is saved **on entering** (before the transfer, on the surface) and **on leaving** (after
  arriving on the surface). There are **no saves inside the Rift**. Closing the tab inside the Rift resumes the
  hero on the surface by the portal with what it had when it entered.
- **Death in the Rift** is a normal death: the hero is gone from the realm (the others see the body sink and fade)
  and the title screen comes back; the hero resumes from its last save — the one made on entering, on the surface.
  Everything won in the Rift since entering is lost.
- **Monster and chest depth per player:** `hero.maxDepth` (the deepest depth reached; a new saved field, set on
  arrival at a depth and from `depth` for older saves). A player's monsters are made with `makeMonster(type, x, y,
  maxDepth)` and their chests and drops roll with `maxDepth`'s loot rules.
- **How much each player brings:** what one crypt level at their depth would hold (its monster count and chests,
  champions included), spread over the rooms nobody has claimed yet, farthest from the start room first. The
  first player also places the static furnishings (props, doors, urns).
- **Keeping the realm alive:** a player's monsters slowly come back (one every ~20 s, up to their starting number)
  in rooms where no hero has been within 15 tiles for 60 s.
- Nameplates show a monster's level in the Rift (monsters of different players' depths mix), coloured by how far it
  is above or below the viewing hero's depth.

## 4. Network: finding each other

### Supabase Realtime (signaling and presence)

No database table. The existing Supabase project (the one `worm-03` uses), its publishable key, and
`supabase-js@2` from a CDN.

- One channel per realm: `rift:<realmId>`.
  - **Presence** of each player: `{ peer, name, lvl, depth: maxDepth, look, since }` (`peer`: a random id made per
    visit; `since`: when it joined).
  - **Broadcast** for WebRTC signaling: `{ to, from, kind: 'offer' | 'answer' | 'ice', data }`; everyone ignores
    messages not addressed to them.
- **The realm exists while the channel's presence is not empty.** The entry prompt subscribes, reads presence,
  and unsubscribes if the player stays outside.
- **Joining:** subscribe, track own presence, wait up to 1.5 s for the presence sync.
  - Nobody else there: **found** the realm (build the layout, spawn own monsters and chests).
  - Others there: open a connection to **each** of them (the joiner always makes the offers), then ask the
    **elder** (the player present longest, the smallest `since`; ties by `peer`) for the snapshot.
  - **Founding race:** two players found at the same moment. Each sees the other's presence arrive with its
    `since`. The later founder throws its realm away and joins the earlier one; the "Entering the Rift…" screen is
    still up, so it is not seen.
- **Capacity:** 6 players per realm (a full mesh is 15 connections). A 7th sees "The Rift is full."
- The Supabase connection stays open while in the realm (presence must say the realm exists, and later joiners
  need to reach everyone).
- **Supabase or WebRTC unreachable:** the portal says "The Rift is silent" and the player can still enter alone
  — the realm is built and played without networking (the same code path as a founder with nobody joining).

### WebRTC (the game traffic)

- One `RTCPeerConnection` per pair, with two data channels:
  - **`ev`**: reliable, ordered. Events: join, leave, spawn, hit, death, pickup, chest, snapshot.
  - **`st`**: unreliable, unordered (`ordered: false, maxRetransmits: 0`). State snapshots.
- ICE: public STUN (`stun:stun.l.google.com:19302`). A TURN relay is added later (phase 6): a Supabase edge
  function hands out short-lived Cloudflare TURN credentials, so no token is in the page. Until then about 10–20 %
  of pairs (mostly mobile networks) may fail to connect; the joiner then sees "Could not reach <name>" and enters
  without that player.
- **Clock:** each pair exchanges pings every 2 s; each side keeps the round-trip time and the offset to the other's
  `G.time`, smoothed. Every state message carries the sender's time.
- **Heartbeat:** a state message at least once a second. No message from a peer for 3 s: it is **gone** (as if it
  left, [§7](#7-leaving-hidden-tabs-and-hand-over)).
- **Messages** are JSON with short keys (switch to binary later if needed).

### Snapshot for a joiner

Sent by the elder over `ev`, in pieces of at most 16 KB:

- The **map**: size, the tile grid run-length encoded (≈ 3–5 KB), the static objects (doors open or shut, props,
  urns broken or not), the start room and the portal.
- Every **live object** (monsters, chests, ground items, fires) with its `owner` and current state.
- Every player's **hero** state.

The map is sent, not a seed: `buildLevel` draws from `Math.random`, and a seed would make any change in the
generation code a silent desync.

## 5. Ownership

**Rule: each browser decides about what it owns; everyone else sends it requests.**

| Object | Owner | Others send |
|---|---|---|
| A hero (position, life, gear, death) | its player | `hit` |
| Monsters, chests, ground items, gold a player spawned or dropped | that player | `hit`, `freeze`, `pickup`, `open` |
| A player's arrows, bombs, fires | that player | — |
| Static objects (doors, urns) | the founder, then the elder | `use` |

- **Ids** are `slot × 2²⁰ + n`, where `slot` (1–6) is the player's seat in the realm, given by the elder in the
  snapshot reply; `n` is the player's own counter. Items picked up get a new local id in the picker's pack.
- **Hits are one message for every target:** `hit { target: { kind: 'mon' | 'hero', id }, dmg, crit, src, from }`.
  - **A hero hits a monster:** the attacker's browser rolls the hit and damage with its own stats (as now) and sends
    `hit` to the owner. The owner applies it (armour, frozen bonus, etc.) and its next state message carries the new
    life. The attacker shows the number at once (prediction); the owner's life value wins. In close calls the
    attacker's view decides whether it hit (good for co-op).
  - **A monster hits a hero:** the owner runs the monster's AI. Target choice picks among **all** heroes (nearest
    visible, as now, plus a little stickiness to its current target). When the swing lands, the owner sends `hit` to
    the target hero's player, whose browser applies armour and damage, so its life, potions and dying window stay
    exact on its own screen. Monster projectiles are spawned as events; each player checks only whether they hit
    their **own** hero.
  - **PvP later:** a hero's `hit` on another hero is the same message. Every hero has a `team`; with co-op all
    heroes share a team, and hits on a team-mate are not sent (no friendly fire). PvP = one team per player plus a
    realm flag. Fire and bombs already damage "everything in the area"; they will check `team` the same way.
- **Kills and XP:** the owner decides the death (`died { id, by }`) and rolls the loot. Each hero who damaged it in
  the last 30 s gets experience × its share of the damage done, at least 25 % (so helping always pays).
- **Loot is shared and the owner rolls it:** drops lie on the ground for everyone, owned by the monster's or chest's
  owner.
  - **Pickup:** the picker sends `pickup { id }`; the owner grants the **first** request (`granted { id, to }` to
    everyone; the item is removed and the winner adds it to its pack) and refuses later ones. While waiting
    (≈ one round trip), the item shows as "reaching" for the picker. If the picker's pack is full when the grant
    arrives, it drops the item again (as its own drop).
  - **Chests:** `open { id }` to the owner; the owner opens it (first request wins), rolls the contents with its
    depth, and drops them as its ground items.
  - **Gold** is picked up the same way.
- **Static objects:** opening a door or breaking an urn is `use { id }` to the owner of statics, who broadcasts the
  new state; the requester opens it locally at once (a door has no contest).

## 6. Keeping updates cheap and smooth

### Heroes

15 state messages a second: `{ id, x, y, dir, anim, busy, hp, maxHp, dying, t }` plus events for swings, shots,
potion drinks and gear changes (weapon, look). Other heroes are drawn **100 ms in the past**, interpolated between
the two states around that time (extrapolated for at most 250 ms if messages are late).

### Monsters: intent, not a stream of positions

A monster's state message:

```
{ id, x, y, hp, st: 'idle' | 'chase' | 'windup' | 'frozen', path: [[x, y], …] | null, target: heroId | null,
  speed, windup, t }
```

- Receivers **predict**: walk the monster along `path` at `speed` (or toward `target`'s latest known position when
  chasing), using the sender's `t` and the clock offset.
- Corrections: an error under 2 tiles is blended out over 150 ms; more snaps.
- **Windups and attacks** go on `ev` at once, so the target sees the swing coming and plays it in time.

### Priority queue

Each owner keeps, for each peer, when each owned object was last sent to it. On every tick (15 Hz) for each peer:

```
priority = (now − lastSentTo[peer][obj]) × weight(distance from obj to that peer's hero)
weight = 1 on screen (< 14 tiles), 0.3 nearby (< 30 tiles), 0.05 far away
```

The top K (≈ 25 a tick) are sent. Changing intent (a new path, a new target, a state change) puts an object at the
top. Far monsters end up at about 1 update a second, objects on screen at the full rate. With 6 players and a few
hundred monsters this stays near 2–3 KB/s per pair.

### Other objects

Ground items and chests change only by events (spawn, granted, opened). Fires and bombs are events (spawn with
their parameters; everyone runs the same visual effect; only the owner applies damage).

## 7. Leaving, hidden tabs and hand-over

- **Leaving** (through the portal, death, or closing the tab: a `leave` event if possible, else the 3 s silence):
  - Monsters the leaver owned that are **fighting** someone pass to the hero they are fighting (its player becomes
    the owner and takes over the AI from the last state).
  - Its other monsters fade out ("The Rift reclaims its own.").
  - Its ground items and chests pass to the **elder**.
  - Its fires and projectiles end.
- **Hidden tabs:** a hidden tab gets no `requestAnimationFrame`, so it cannot simulate. When a player's tab becomes
  hidden (`visibilitychange`) it hands **all** its objects over at once (fighting monsters to their targets, the
  rest to the elder), and its hero becomes an **away** ghost: drawn faded, not targeted, not hittable. Back within
  60 s, it takes over nothing (objects stay where they went) and plays on; after 60 s it is treated as having left
  (its own screen, when shown again, says "The Rift let you go." and puts the hero on the surface; it is saved
  there, with what it had when it went away).
- **The elder leaves:** the next oldest becomes the elder (everyone computes the same answer from presence).
- **The last player leaves:** the realm is gone. The next player to dial that realm id founds a new one.

## 8. Changes to the existing code

- **Several heroes.** The game assumes one hero (`G.hero`) in the monster AI (target choice, notice, chase, hits),
  fire and bomb damage, door opening and the camera. Introduce `G.heroes` (the local hero first, then others as
  remote heroes); monster AI picks its target among them. This is the largest change and comes before any
  networking (phase 2), so the solo Rift already runs on it.
- **Owned and remote objects:** each monster, chest and ground item gets `owner`. `updateMonster` runs the AI only
  for owned monsters; remote ones run the prediction ([§6](#6-keeping-updates-cheap-and-smooth)).
- **New files** next to `index.html`: `net.js` (Supabase presence and signaling, the WebRTC mesh, clock, priority
  queue) and `realm.js` (the Rift: realm mode of `buildLevel`, spawning per player, snapshot, ownership, hand-over).
- **Saving:** new `SAVED_FIELDS` `dial` and `maxDepth`; saves on surface escape, on entering and on leaving the Rift;
  no saves inside it.
- **Sandbox:** scenarios for the scroll (a hero at depth 6 with a Surface Escape; a Scroll of Return on the
  surface), the dial (items next to it), the solo Rift, and the Rift with a **bot player** (a second browser page
  driving a hero by script) for local testing.
- **Risk to check early (before phase 4):** the artifact viewer's content policy may block the Supabase websocket
  or WebRTC. If so, the multiplayer parts are tested locally (two Playwright browsers against the real Supabase
  project) and on GitHub Pages only; the solo Rift still works in the sandbox.

## Phases

Each phase is one version (or a few), playable at the end.

| # | Phase | Contents | Status |
|---|---|---|---|
| 1 | Surface Escape | the scroll and its return, the 4 s incantation, dying while reading, Garrick's gift, keepers' stock, save after escape, `maxDepth` | planned |
| 2 | Portal and solo Rift | portal and dial art, placement, dial items saved and hashed into a realm id and name, the Rift's map and its portal, spawning for `maxDepth`, saves on entering and leaving, `G.heroes` refactor | planned |
| 3 | Seeing each other | Supabase presence and signaling, WebRTC mesh, snapshot (map + heroes), other heroes walking and animating, clock and heartbeat; no combat | planned |
| 4 | Fighting together | spawning for each joiner, ownership, monster state with intent and prediction, the priority queue, hits both ways, deaths and shared XP | planned |
| 5 | Loot | ground items, gold and chests decided by their owner, pickup and open requests | planned |
| 6 | Robustness | hand-over on leaving, hidden tabs and away ghosts, founding race, capacity, TURN relay | planned |
