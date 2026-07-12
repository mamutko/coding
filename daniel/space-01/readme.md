# Space Game

A spaceship sits at the bottom of the screen. It can move left and right, and shoot down alien invaders that descend from the top.

## Controls

- `A` / `D` (or Left / Right arrow keys) — move the ship left/right.
- `Space` — fire a projectile upward from the ship.

## Gameplay

- Aliens spawn periodically at the top of the screen and descend toward the bottom, at a randomized speed.
- Aliens periodically fire projectiles downward at random intervals.
- If a player projectile hits an alien, the alien is destroyed and the player earns 10 points.
- If an alien reaches the bottom of the screen without being destroyed, it disappears and the player loses 5 points.
- If an alien projectile hits the player's ship, the game ends and "GAME OVER!" is displayed over the board.
- A "Restart" button appears on game over; clicking it saves the current score to the leaderboard (using the entered player name, or "Anonymous" if left blank) and starts a new game.

## Score and leaderboard

- The current score is shown in the top-right of the screen.
- A player name field lets the player enter a name before finishing a game.
- The leaderboard shows the top 5 scores, in-memory only (not persisted between page loads).

## Implementation details

- The game is implemented in JavaScript as a single self-contained HTML5 file, `index.html`, using the canvas API.
