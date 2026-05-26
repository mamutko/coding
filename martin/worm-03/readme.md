# Worm (mobile-optimized version)

Worm is a simple game where the user directs a worm on a two-dimensional board. The board contains food and poison. If the worm goes across a food cell, it eats the food and grows by one segment. If the worm goes over a poison cell it dies and the game is over. If the worm hits the edge of the board, it dies as well.

This version is derived from worm-02 and is optimized for play on a cellphone.

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

- At the beginning of the game, the player enters their name in a start panel titled "Worm" and clicks "Start Game". If the player is restarting, the player can update their name using the game over panel.
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
