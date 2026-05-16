# Worm

Worm is a simple game where the user directs a worm on a two-dimensional board. The board contains food and poison. If the worm goes across a food cell, it eats the food and grows by one segment. If the worm goes over a poison cell it dies and the game is over. If the worm hits the edge of the board, it dies as well.

## AI Instructions

This `readme.md` files describes this project. It should be kept up to date with all the features of the project. Whenever the user prompts the AI to do updates to the code, this file should be updated as well. Do so by adding the description of the newly implemented feature into the relevant section, or if there is no relevant section, create a new section. The user might mark some features or descriptions in this file as "TODO". That means, the feature is still not implemented in code. If the user asks the AI to implement the feature, the "TODO" label should be removed and the description of the feature updated if necessary. If the feature was implemented only partially, a description of the parts that were not implemented should be retained with a "TODO" label.

## Gameplay details

- The game is played on a board consisting of 80 by 40 cells.
- The player is directing a worm, the worm can move in the 4 cardinal directions.
- The player can use the keys 'A', 'S', 'D' and 'W' to change the direction that the worm is moving in.
- The worm moves at a speed equal to its length in cells per second; as the worm grows, it moves faster.
- The worm consists of a head and additional segments, each segment follows the path of the previous segment. The first segment follows the path of the head.
- The worm head is visually distinct in orange and has two green eyes that face the direction of movement.
- On the board, there are cells with food and cells that are poison:
  - The board starts with 30 cells that are food or poison in random positions.
  - The board starts with two cells that are food in random positions.
  - When the worm's head goes onto a food cell, the worm eats it and another food appears in a new random position on the board.
- When the worm eats food, it grows by one segment. The next time the worm moves, a new segment is added in the previous position of the last segment.
- When the worm eats poison, it dies and the game is over.

## Game Start

- At the beginning of the game, the player enters their name in a start panel titled "Worm" and clicks "Start Game". If the player is restarting, the player can update their name using the game over panel.
- Prior to the start of the game, the player is shown the board with the worm, food and poison.
- The worm is placed in the middle of the board.
- The initial length of the worm is 3 segments.
- The worm is stationary until the player hits one of the direction keys, which starts the game.
- The worm starts moving based on the key that the player hit and continues to move with the speed mentioned above.

## Game End

- See gameplay details for conditions of ending the game.
- Once one of these conditions is met. The game stops, the worm stops moving, and the text "Game Over!" is displayed across the board.
- Below the "Game Over!" text is an input field pre-populated with the current player's name. The user can edit the name to start a new game as a different player.
- Below the name input is a button with the label "Restart Game". If the user clicks the button a new game is started.

## Scoring and Leaderboard

- The score of the current player is equal to the current length of the worm minus the initial length of the worm. Hence, the score starts at 0 and grows by one every time the worm eats food.
- The current score is displayed above the top right corner of the board in the format `PlayerName, current score: 12`, aligned to the right edge of the board.
- `PlayerName` is the current player's name as entered at the beginning of the game.
- To the right of the board, a leaderboard lists the top 10 players and their top scores.
- The leaderboard data persists in the browser using local storage.

## Implementation details

- The game is to be implemented in JavaScript as a single HTML5 file index.html.