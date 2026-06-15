# Worm (version with leaderboards, mobile-optimized, two-player)

Worm is a simple game where the user directs a worm on a two-dimensional board. The board contains food and poison. If the worm goes across a food cell, it eats the food and grows by one segment. If the worm goes over a poison cell it dies and the game is over. If the worm hits the edge of the board, it dies as well.

The game can be played solo or as a two-player match between two browsers connected peer-to-peer (see "Two-Player Multiplayer").

## Gameplay details

- The game is played on a board consisting of 80 by 40 cells.
- The player is directing a worm, the worm can move in the 4 cardinal directions.
- The player can use the keys 'A', 'S', 'D' and 'W' (or arrow keys) to change the direction that the worm is moving in.
- The worm moves at a speed equal to its length in cells per second; as the worm grows, it moves faster.
- The worm consists of a head and additional segments, each segment follows the path of the previous segment. The first segment follows the path of the head.
- The worm head is visually distinct in orange and has two green eyes that face the direction of movement.
- On the board, there are cells with food and cells that are poison:
  - The board starts with 30 cells that are poison and 2 cells that are food in random positions.
  - When the worm's head goes onto a food cell, the worm eats it and another food appears in a new random position on the board.
- When the worm eats food, it grows by one segment. The next time the worm moves, a new segment is added in the previous position of the last segment.
- When the worm eats poison, it dies and the game is over.

## Game Start

- The start panel (titled "Worm") is a card menu and is the hub the player returns to after every game. The **main screen** has two cards: **"Start Single Player Game"** and **"Start Multi Player Game"**.
- Clicking **Start Single Player Game** begins a solo game. No name is requested up front; the player is only prompted for a name if they achieve a leaderboard-worthy score (see "Scoring and Leaderboard").
- Clicking **Start Multi Player Game** opens the multiplayer screen (see "Two-Player Multiplayer").
- Prior to the start of the game, the player is shown the board with the worm, food and poison.
- The worm is placed in the middle of the board.
- The initial length of the worm is 3 segments.
- The worm is stationary until the player hits one of the direction keys or taps the screen, which starts the game.
- The worm starts moving based on the input direction and continues to move with the speed mentioned above.

## Name validation

The leaderboard name is validated in the browser when the player clicks **Publish Score** (see "Scoring and Leaderboard"). A name is rejected if it is any of:

- empty, or longer than **18 characters**,
- anything other than **letters (A–Z, a–z), spaces, and dashes**,
- or contains a **bad word** (profanity, slur, or sensitive term).

If validation fails, a dialog explains the three rules ("at most 18 characters", "letters, spaces and dashes only", "respectful") and the score is not published (the publish prompt stays open).

The same limits are also enforced **at the database** (see "Data constraints").

### Bad-word lists

The check uses **two** bad-word lists embedded in `index.html`: one matched as a substring anywhere in the name, the other matched only as a whole word (to avoid flagging innocent names). The words are stored lightly obfuscated with a reversible Caesar +3 cipher rather than in clear text.

By design, the specific words are **not** documented here — this is the one place the repository's "describe everything in the README" rule intentionally does not apply.

## Data constraints

The `mw3_high_score` table enforces the name rules at the database level, as a backstop to the browser validation:

- `name` length is **1..18** characters.
- `name` matches `^[A-Za-z *-]+$` — letters, spaces, and dashes, **plus `*`**. The `*` is allowed only so the table owner can manually redact a published name directly in the database; the client never submits `*`.

These are `CHECK` constraints added by a migration under `supabase/migrations/`.

## Game End

- See gameplay details for conditions of ending the game.
- When the player dies, the game stops, the worm stops moving, and the text **"Game Over!"** is displayed across the board (in a two-player game the result is "You win!" / "You lose!" / "Draw!" instead).
- After a **1.2-second** pause, the game proceeds automatically:
  - if the player's score qualifies for the leaderboard, the **"Well done!"** leaderboard-entry dialog is shown (see "Scoring and Leaderboard");
  - otherwise the player is taken **directly back to the start panel**.
- After the leaderboard dialog is dismissed (by publishing or skipping), the player is likewise returned to the start panel. There is no separate "restart" button — the start panel is the single hub for beginning the next game.

## Scoring and Leaderboard

- The score of the current player is equal to the current length of the worm minus the initial length of the worm. Hence, the score starts at 0 and grows by one every time the worm eats food.
- The current score is displayed in the top-right corner of the game canvas as `Score: 12` — just the number, with no player name. (In a two-player game the corners instead show `You: 12` and `Opponent: 7`, also without names.)
- A leaderboard button in the bottom-right corner of the canvas opens a modal listing the **top 20 scores** (highest first). Each entry shows the player name, the score, and the date/time the score was achieved.
- The leaderboard is **shared across all players**: scores are stored in a public Supabase table (hosted Postgres) accessed over its REST API, so every browser sees the same global board rather than a per-device list. The modal is refreshed from the server both on page load and each time it is opened.

### Publishing a score

- When a game ends, the leaderboard is refreshed and the local player's score is checked. It **qualifies** if the board holds fewer than 20 entries, or the score is at least as high as the current lowest top-20 score (and is greater than 0).
- If the score qualifies, a **"Well done!"** overlay appears with a name field and two buttons: **Publish Score** and **Skip**. The field is pre-filled with the player's saved name and is **not** auto-focused (so steering keys still being pressed don't type into it).
- **Publish Score** validates the name (see "Name validation"); on success it inserts the score row, saves the name to `localStorage` so it is pre-filled next time, and refreshes the board. **Skip** dismisses the overlay without publishing. Either button then returns the player to the start panel.
- Each published score is its own row, so the same player can appear more than once on the board.
- Scores do not expire. The table is kept in sync with what the board displays: after each new score is submitted, every row outside the top 20 is deleted, so the table holds only the 20 scores shown in the leaderboard. Ties in score are ranked by most-recently-inserted, and the same ordering is used for both the displayed board and the prune so the rows kept are exactly the rows shown.
- Leaderboard network calls are best-effort: if Supabase is unreachable, errors are logged to the console and solo play continues normally.

## Two-Player Multiplayer

Two players can play together on a single shared board, with their browsers connected directly peer-to-peer.

### The multiplayer screen

Clicking **Start Multi Player Game** on the start panel opens a screen with four cards:

- **Back** — returns to the main start screen (cancelling any in-progress random search).
- **Join Random Game** — random matchmaking (see below). While searching, this card reads **"Cancel Search"**.
- **Enter Game Number to Join** — reveals a 4-digit input and a **Join** button to join a friend's game by their number.
- **Your Game Number: &lt;number&gt;** — shows this browser's own 4-digit game number. Clicking it displays the hint *"Share this number with a friend, the game will start automatically when your friend enters this number."* The host does not press anything to start; the game begins for both as soon as the friend joins the number.

### Matchmaking by code

- To host a game, a player shares their own game number (shown on the "Your Game Number" card); the friend opens **Enter Game Number to Join**, types it, and clicks **Join**.
- The player who is connected to becomes the **host**; the player who joins becomes the **joiner**. The match is one-on-one — additional connection attempts to a player already in a game are refused.
- Codes are random 4-digit numbers. If a generated code happens to already be in use, a new one is generated automatically.

### Random matchmaking

- The **Join Random Game** card pairs the player with anyone else who is currently searching, without exchanging a number.
- Matchmaking uses a **single well-known rendezvous peer ID** (a fixed lobby ID, namespaced so it cannot collide with the 4-digit game codes). The first searcher to find the lobby empty **claims** the lobby ID and waits; the next searcher **finds** the waiter there.
- When a searcher reaches a waiter, the waiter sends back its own 4-digit game code over the lobby connection, and the searcher then joins that code through the normal code-based flow. The waiter becomes the host, the searcher becomes the joiner.
- The lobby ID is only used to introduce the two players; the actual game runs over each player's persistent game peer. As soon as a match forms, the host **releases the lobby ID** so the next pair of searchers can use it.
- While searching, the card changes to **"Cancel Search"**. Because the lobby is a single slot, only one pair can be forming a match at a time; this is suitable for a small number of concurrent players (e.g. a class), not for large-scale matchmaking.

### Networking

- Connections use **WebRTC data channels** established via **PeerJS**. PeerJS is loaded from a CDN and its public broker is used only at connection setup; once connected, game traffic flows directly between the two browsers.
- The player's 4-digit code is used as their PeerJS peer ID, so joining is simply a connection to that ID. Each player keeps this game peer (and its signaling link) alive for the whole session, which is what makes reconnection possible.
- Internet access is required to load PeerJS and complete the handshake. If PeerJS cannot be reached, the multiplayer controls report that multiplayer is unavailable and solo play still works.
- When a connection opens, a diagnostic line is written to the browser **console** reporting the selected ICE candidate pair: whether the link is **direct peer-to-peer** (candidate types `host`/`srflx`/`prflx`) or **relayed through a TURN server** (`relay`), along with the candidate addresses and round-trip time. This is purely informational and does not affect gameplay.

### Host-authoritative model

- The **host runs the single authoritative simulation**: it owns the board, food, poison, both worms, and all collision logic.
- The host broadcasts the full game state (both worms, food, poison, and game phase) to the joiner after every change. The joiner renders the received state.
- The **joiner sends only its direction inputs** to the host, which applies them to the joiner's worm (subject to the same perpendicular-only rule as solo play). This keeps the two browsers in agreement without any shared clock.

### Two-worm gameplay

- Both worms share the same board, food, and poison. There are 2 food and 30 poison cells, the same as solo play.
- The **host's worm** keeps the original colors (orange head, green body). The **joiner's worm** is visually distinct with a blue head and cyan body.
- The worms start on opposite sides of the board and are stationary until their controller provides a direction. **Both worms move at the same speed, set by whichever worm is currently longer** (unlike solo play, where speed tracks the single worm's own length). As either worm grows, both speed up together.
- To keep a hesitant player from stalling the match, if one worm has still not started moving by the time the other worm eats its first food, the idle worm **automatically starts moving in the direction its head is already facing**.
- At the start of a two-player game, a translucent **"This is you!"** callout appears next to the local player's worm for 1.2 seconds and then disappears.
- A worm dies if its head hits a wall, a poison cell, its own body, **or the other worm's body**.
- As soon as one worm dies, the round ends. The surviving player sees "You win!", the player whose worm died sees "You lose!" (a "Draw!" if both die together). The dead worm's head is drawn greyed out.
- Each player's current score and their opponent's is shown on the canvas as `You: N` and `Opponent: N` (no player names).
- Each browser handles its own player's score with the same end-of-game flow as solo play: the result is shown for 1.2 s, then the leaderboard-entry dialog (if the score qualifies) or a return to the start panel (see "Scoring and Leaderboard").

### Restarting, reconnecting and disconnects

- When a multiplayer round ends, each player follows the same end-of-game flow as solo play and is returned to the **start panel** (after the result pause and any leaderboard-entry dialog). This ends the session and closes the peer-to-peer connection; to play again the players start a fresh game from the start panel. There is no in-place rematch.
- If the WebRTC connection drops **mid-round** (while still playing), the game attempts to **reconnect** rather than ending immediately, using the still-alive game peers:
  - The simulation pauses and both players see a "Reconnecting…" / "Opponent disconnected — waiting to reconnect…" message.
  - The **joiner** re-initiates the connection to the host's game code (a few timed attempts); the **host** waits for the joiner to return. On success, the host resumes the paused simulation and resyncs the state, and play continues.
  - If reconnection does not succeed within the retry window, the remaining player is returned to the start panel and can start a new game.
- Reconnection only applies to drops during active play; a connection closing once the round is already over is expected (both players are returning to the start panel) and does not trigger a reconnect.

## Mobile Screen Scaling

- The game canvas is scaled dynamically to fill as much of the device viewport as possible.
- The cell size is calculated as the largest integer that allows all 80×40 cells to fit within the screen width and height simultaneously.
- On resize or device orientation change, the canvas is recomputed and redrawn automatically.
- The scoreboard and leaderboard button are overlaid on top of the canvas so no screen space is wasted on UI chrome outside the game area.
- The viewport meta tag sets `maximum-scale=1.0` and `user-scalable=no` to prevent accidental pinch-zoom during gameplay.

## Touch Controls

- The game canvas is divided into four directional zones by its two diagonals (top-left to bottom-right, and top-right to bottom-left).
- Tapping in the **top** triangular zone (above both diagonals) moves the worm up.
- Tapping in the **bottom** triangular zone (below both diagonals) moves the worm down.
- Tapping in the **left** triangular zone (between the diagonals, on the left side) moves the worm left.
- Tapping in the **right** triangular zone (between the diagonals, on the right side) moves the worm right.
- The same direction constraint as keyboard controls applies: only perpendicular direction changes are allowed (the worm cannot reverse into itself).
- A brief hint about touch controls is shown on the start and game-over overlay screen.

## Backend with Supabase

The shared leaderboard is stored in a hosted **Supabase** project (named "coding") and accessed directly from the browser over its REST (PostgREST) Data API.

- **Dashboard:** <https://supabase.com/dashboard/project/qifgxysuhskscrjjwzfm>
- **Administering Supabase:** log in to the dashboard with **Martin's GitHub account**.
- **Data API base URL:** `https://qifgxysuhskscrjjwzfm.supabase.co/rest/v1/`
- **Publishable (anon) key:** `sb_publishable_dJ7DGbkXPYOiD4YipTXEog_vx_FhOot` — embedded in `index.html`. Publishable keys are designed to ship in client code; access is governed by row-level security, not by hiding the key.

### Table: `mw3_high_score`

- Table names are prefixed with the per-project slug `mw3` (for `martin/worm/03`) so multiple projects in this repository can share one database.
- Columns: `id`, `name`, `score`, and `timestamp` (a `timestamptz` defaulting to `now()`, shown in the leaderboard as the date/time the score was achieved).
- **Row-level security** is enabled with permissive policies granting the anonymous role read / insert / delete, so the table is effectively world read/write (the game is unauthenticated). The `name` column is additionally guarded by length/character `CHECK` constraints (see "Data constraints").
- The client reads the board with `order=score.desc,id.desc&limit=20`, `POST`s new scores, and after each insert prunes the table by fetching the top-20 ids and issuing `DELETE` with `id=not.in.(<those ids>)` (a no-op until the table holds at least 20 rows).

### Migrations

- The table and its policies/constraints are created by SQL migrations under `supabase/migrations/` at the repository root. Supabase's **GitHub integration** applies them automatically when changes are merged to `main`.

## Implementation details

- The game is implemented in JavaScript as a single HTML5 file index.html.
- PeerJS is included via a CDN `<script>` tag for the WebRTC peer-to-peer connection used by multiplayer.
- Game state is held in a `players` array so the same rendering and simulation code serves both solo (one worm) and two-player (two worms) games.
- Random matchmaking uses a transient second PeerJS peer that claims a fixed lobby ID only while waiting; it is destroyed once a match forms, leaving the game running on the persistent per-player game peers.
- The shared leaderboard is backed by Supabase — see "Backend with Supabase".
