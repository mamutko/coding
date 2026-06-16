---
name: multiplayer-game
description: How to build a browser-to-browser real-time multiplayer game using PeerJS for the handshake/matchmaking and WebRTC data channels for in-game traffic, with a host-authoritative simulation. Use when adding online multiplayer, peer-to-peer connectivity, matchmaking by code or random pairing, or reconnection to a single-file HTML game. Worked example: martin/worm-03.
---

# Multiplayer game (PeerJS + WebRTC)

This skill describes the pattern used by `martin/worm-03` for two-player,
peer-to-peer online play with no game server: **PeerJS** handles connection
setup (signaling), **WebRTC data channels** carry the actual game traffic
directly between browsers, and one player runs the **authoritative
simulation**.

## Architecture at a glance

- **PeerJS** (`https://unpkg.com/peerjs@1.5.4/dist/peerjs.min.js` from a CDN)
  wraps WebRTC. Its public broker is used **only at connection setup** to
  exchange signaling; once the data channel opens, game traffic flows directly
  peer-to-peer (or via a TURN relay if direct fails).
- Each player creates a `Peer` with a **short, human-shareable ID** (worm-03
  uses a random 4-digit number). Joining is just connecting to that ID.
- The connector becomes the **host**, the one who connects becomes the
  **joiner**. The host owns the simulation; the joiner sends inputs and renders
  the state it receives.
- Internet is required to load PeerJS and complete the handshake. If PeerJS is
  unreachable, degrade gracefully (disable multiplayer, keep solo play working).

## Setting up the peer

```js
let peer, conn, myCode;

function createPeer() {
  if (typeof Peer === 'undefined') { /* CDN failed → mark multiplayer unavailable */ return; }
  myCode = String(Math.floor(1000 + Math.random() * 9000)); // 4-digit ID
  peer = new Peer(myCode, { debug: 0 });

  peer.on('open', (id) => { myCode = id; /* show "Your game number: id" */ });

  peer.on('connection', (c) => {          // someone joined us → we are the host
    if (conn && conn.open) {               // already in a match: refuse extras
      c.on('open', () => c.close());
      return;
    }
    setupHostConnection(c);
  });

  peer.on('error', (err) => {
    if (err.type === 'unavailable-id') { peer.destroy(); createPeer(); }      // code collided → pick another
    else if (err.type === 'peer-unavailable') { /* no game for that code */ }
    // ... other errors
  });
}
```

Keep this game peer **alive for the whole session** — it is what makes
reconnection possible.

## Joining by code

```js
function joinByCode(code) {
  const c = peer.connect(code, { reliable: true }); // reliable, ordered data channel
  setupJoinerConnection(c);
}
```

The two roles wire up symmetric handlers:

```js
function setupHostConnection(c) {
  conn = c;
  c.on('open',  () => { logConnectionDetails(c); startHostGame(); });
  c.on('data',  (msg) => { if (msg.t === 'input') applyInput(1, msg.dir); });
  c.on('close', onConnClose);
  c.on('error', () => {});
}

function setupJoinerConnection(c) {
  conn = c;
  c.on('open',  () => { c.send({ t: 'hello', name: playerName }); });
  c.on('data',  (msg) => { if (msg.t === 'state') applyRemoteState(msg); });
  c.on('close', onConnClose);
  c.on('error', () => {});
}
```

## Host-authoritative model

Keeping one side authoritative avoids needing a shared clock or conflict
resolution:

- The **host runs the single simulation**: board, items, all players, and
  collision logic.
- After every change the host **broadcasts the full game state** to the joiner,
  which simply renders what it receives.
- The **joiner sends only its inputs** (e.g. direction changes) to the host,
  which applies them subject to the same rules as a local player.

Use a small tagged-message protocol (`{ t: 'input', ... }`, `{ t: 'state', ... }`,
`{ t: 'hello', ... }`) so both sides can branch on `msg.t`.

## Matchmaking

**By code (play with a friend):** the host shares its 4-digit number; the
friend types it and connects. The game starts automatically for both when the
connection opens — no "start" button.

**Random pairing (single rendezvous slot):** use one **well-known lobby peer
ID** (a fixed string, namespaced so it can't collide with game codes), e.g.
`'worm03-random-lobby-v1-566231993'`:

1. A searcher first **probes** the lobby by connecting to the lobby ID.
2. If nobody answers (timeout/error), the searcher **claims** the lobby by
   creating a transient second `Peer(LOBBY_ID)` and waits.
3. The next searcher connects, the waiter **sends back its own game code** over
   the lobby connection, and the searcher joins that code through the normal
   code flow.
4. As soon as the match forms, the waiter **releases the lobby ID** (destroys
   the transient lobby peer) so the next pair can use it.

This single-slot scheme suits a small group (e.g. a class), not large-scale
matchmaking. Handle the `unavailable-id` race (two searchers claim at once → the
loser re-probes).

## Reconnection

Because each player keeps its game peer alive, a mid-game drop can be healed
instead of ending the match:

- On an unexpected `close` **while still playing**, pause the simulation and
  show a "Reconnecting…" message instead of ending.
- The **joiner** re-initiates `peer.connect(hostCode)` a few timed times; the
  **host** waits for the joiner to return, then resumes and resyncs state.
- Give up after a retry budget (e.g. 5 attempts) and return to the menu.
- A `close` once the round is already **over** is expected — don't reconnect
  then. Track an `intentionalLeave` / `sessionActive` flag to distinguish
  deliberate exits from drops.

## Diagnosing the connection (optional)

To see whether a link is direct or relayed, read the underlying
`RTCPeerConnection` stats after it opens and log the selected candidate pair:

```js
const pc = conn.peerConnection;                 // PeerJS exposes the RTCPeerConnection
pc.getStats().then((report) => {
  report.forEach((s) => {
    if (s.type === 'candidate-pair' && s.state === 'succeeded' && s.nominated) {
      // local/remote candidateType 'host'/'srflx'/'prflx' = direct, 'relay' = TURN
    }
  });
});
```

`host`/`srflx`/`prflx` candidate types mean a **direct** peer-to-peer link;
`relay` means traffic goes through a **TURN** server. This is informational only.

## Checklist for a new multiplayer game

- [ ] Add the PeerJS CDN `<script>` tag.
- [ ] Create a persistent game peer with a short shareable ID; handle `unavailable-id`.
- [ ] Implement code-based join (host = connectee, joiner = connector).
- [ ] Decide the authoritative side; define a tagged message protocol (state vs input).
- [ ] (Optional) Add single-slot random matchmaking via a namespaced lobby ID.
- [ ] Handle reconnection vs. expected close.
- [ ] Degrade gracefully when PeerJS can't be reached.
- [ ] Document the design in the project README (link back to this skill for the generic mechanics).
