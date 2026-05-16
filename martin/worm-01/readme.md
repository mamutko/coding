# Worm

Worm is a simple game where the user directs a worm on a two-dimensional board. The board contains food and poison. If the worm goes across a food cell, it eats the food and grows by one segment. If the worm goes over a poison cell it dies and the game is over. If the worm hits the edge of the board, it dies as well.

## Gameplay details

- The game is played on a board consisting of 80 by 40 cells.
- The player is directing a worm, the worm can move in the 4 cardinal directions.
- The player can use the keys 'A', 'S', 'D' and 'W' to change the direction that the worm is moving in.
- The worm moves at a constant speed of 4 cells per second.
- The worm consist of a head and additional segments, each segment follows the path of the previous segment. The first segment follows the path of the head.
- On the board, there are cells with food and cells that are poison:
  - The board starts with 30 cells that are food or poison in random positions.
  - The board starts with two cells that are food in random positions.
  - When the worm's head goes onto a food cell, the worm eats it and another food appears in a new random position on the board.
- When the worm eats food, it grows by one segment. The next time the worm moves, a new segment is added in the previous position of the last segment.
- When the worm eats poison, it dies and the game is over.

## Game Start

- Prior to the start of the game, the player is shown the board with the worm, food and poison.
- The worm is placed in the middle of the board.
- The initial length of the worm is 3 segments.
- The worm is stationary until the player hits one of the direction keys, which starts the game.
- The worm starts moving based on the key that the player hit and continues to move with the speed mentioned above.

## Game End

- See gameplay details for conditions of ending the game.
- Once one of these conditions is met. The game stops, the worm stops moving, and the text "Game Over!" is displayed across the board.
- Below the "Game Over!" text is a button with the label "Restart Game". If the user clicks the button a new game is started.

## Implementation details

- The game is to be implemented in JavaScript as a single HTML5 file index.html.