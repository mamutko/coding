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

- At the beginning of the game, the player enters their name in a start panel titled "Worm" and clicks "Start Game" to begin a solo game. If the player is restarting, the player can update their name using the game over panel.
- The same start panel also contains the multiplayer controls described in "Two-Player Multiplayer".
- Prior to the start of the game, the player is shown the board with the worm, food and poison.
- The worm is placed in the middle of the board.
- The initial length of the worm is 3 segments.
- The worm is stationary until the player hits one of the direction keys or taps the screen, which starts the game.
- The worm starts moving based on the input direction and continues to move with the speed mentioned above.

## Game End

- See gameplay details for conditions of ending the game.
- Once one of these conditions is met. The game stops, the worm stops moving, and the text "Game Over!" is displayed across the board.
- Below the "Game Over!" text is an input field pre-populated with the current player's name. The user can edit the name to start a new game as a different player.
- Below the name input is a button with the label "Restart Game". If the user clicks the button a new game is started.

## Scoring and Leaderboard

- The score of the current player is equal to the current length of the worm minus the initial length of the worm. Hence, the score starts at 0 and grows by one every time the worm eats food.
- The current score is displayed in the top-right corner of the game canvas in the format `PlayerName, current score: 12`.
- `PlayerName` is the current player's name as entered at the beginning of the game.
- A leaderboard button in the bottom-right corner of the canvas opens a modal listing the top 10 players and their top scores.
- The leaderboard data persists in the browser using local storage.

## Two-Player Multiplayer

Two players can play together on a single shared board, with their browsers connected directly peer-to-peer.

### Matchmaking by code

- The start panel shows the player **their own 4-digit code** and an input field for **entering a friend's code**.
- To host a game, a player shares their code; the friend types it into the "Join a friend" field and clicks "Join Game".
- The player who is connected to becomes the **host**; the player who joins becomes the **joiner**. The match is one-on-one — additional connection attempts to a player already in a game are refused.
- Codes are random 4-digit numbers. If a generated code happens to already be in use, a new one is generated automatically.

### Networking

- Connections use **WebRTC data channels** established via **PeerJS**. PeerJS is loaded from a CDN and its public broker is used only at connection setup; once connected, game traffic flows directly between the two browsers.
- The player's 4-digit code is used as their PeerJS peer ID, so joining is simply a connection to that ID.
- Internet access is required to load PeerJS and complete the handshake. If PeerJS cannot be reached, the multiplayer controls report that multiplayer is unavailable and solo play still works.

### Host-authoritative model

- The **host runs the single authoritative simulation**: it owns the board, food, poison, both worms, and all collision logic.
- The host broadcasts the full game state (both worms, food, poison, and game phase) to the joiner after every change. The joiner renders the received state.
- The **joiner sends only its direction inputs** to the host, which applies them to the joiner's worm (subject to the same perpendicular-only rule as solo play). This keeps the two browsers in agreement without any shared clock.

### Two-worm gameplay

- Both worms share the same board, food, and poison. There are 2 food and 30 poison cells, the same as solo play.
- The **host's worm** keeps the original colors (orange head, green body). The **joiner's worm** is visually distinct with a blue head and cyan body.
- The worms start on opposite sides of the board, are stationary until their controller provides a direction, and each moves at a speed equal to its own length in cells per second.
- A worm dies if its head hits a wall, a poison cell, its own body, **or the other worm's body**.
- As soon as one worm dies, the round ends. The surviving player sees "You win!", the player whose worm died sees "You lose!". The dead worm's head is drawn greyed out.
- Each player's current score (and their opponent's) is shown on the canvas; the local player's score is labeled "(you)".
- Each browser records its own player's best score to its local leaderboard, exactly as in solo play.

### Restarting and disconnects

- After a multiplayer round ends, the **host** can click "Restart Game" to deal a new board and broadcast it. The **joiner's** "Restart Game" button sends a restart request to the host, which starts the new round for both players; while waiting, the joiner sees "Waiting for host…".
- If the connection is lost, the remaining player is returned to the start panel with an "Opponent left" message and can start a new solo game or rematch.

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

## Implementation details

- The game is implemented in JavaScript as a single HTML5 file index.html.
- PeerJS is included via a CDN `<script>` tag for the WebRTC peer-to-peer connection used by multiplayer.
- Game state is held in a `players` array so the same rendering and simulation code serves both solo (one worm) and two-player (two worms) games.
