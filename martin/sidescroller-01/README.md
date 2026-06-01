# Sidescroller 01

A 2D side-scrolling platformer game built as a single HTML5 Canvas file.

## Requirements

- Character is always positioned at 1/5 of the screen width from the left edge
- Moving right causes screen content to scroll left (camera follows character rightward)
- Moving left causes screen content to scroll right (camera follows character leftward)
- Character can jump
- World contains platforms at varying heights with gaps between them
- Falling off the bottom of the screen ends the game

## Controls

| Key | Action |
|-----|--------|
| Arrow Right / D | Move right |
| Arrow Left / A | Move left |
| Arrow Up / W / Space | Jump |
| R | Restart (after game over) |

## Design

### Camera System

The character is always rendered at a fixed horizontal screen position — exactly `canvas.width / 5` pixels from the left. The camera offset is:

```
cameraX = player.worldX - canvas.width / 5
```

All world objects are drawn at `screenX = worldX - cameraX`, producing the illusion of scrolling. The world has the same height as the screen; only horizontal scrolling occurs.

### Physics

| Parameter | Value |
|-----------|-------|
| Gravity | 0.55 px/frame² |
| Jump velocity | −13 px/frame |
| Terminal velocity | 22 px/frame |
| Horizontal speed | 4 px/frame |

### Platform Generation

Platforms are generated procedurally as the player advances to the right:

- Gap between platforms: 80–180 px (always jumpable at the given horizontal speed)
- Height variation: ±80 px from the previous platform (capped to screen bounds)
- Platform width: 90–270 px
- New platforms are pre-generated 2.5 screen-widths ahead of the camera
- Platforms more than half a screen-width behind the camera are pruned to save memory

### Collision Detection

One-directional (landing on top only). Each frame the player's previous-frame bottom position is compared to the platform top:

```
prevBottom = (player.y + PLAYER_H) - player.vy
if prevBottom ≤ platform.y + 2 AND currentBottom ≥ platform.y → land
```

The player is snapped to the platform surface and vertical velocity is zeroed.

### Scoring

Score equals the maximum `worldX` position reached during the run, shown as "Distance" in the HUD.

### Game Over

Triggered when `player.y > canvas.height + 60` (character has fallen fully off the bottom of the screen). A "GAME OVER" overlay is displayed with the final distance. Press R to restart.

## Implementation

Single-file HTML5 application (`index.html`). Uses `requestAnimationFrame` for the game loop. No external dependencies.

### Visual Features

- Sky gradient background (dark blue–green)
- Parallax stars (scroll at 0.2× camera speed)
- Parallax background hills (scroll at 0.4× camera speed)
- Red danger glow at the screen bottom to signal the fall zone
- Green platforms with grass highlight, body shading, and drop shadow
- Animated character with:
  - Walking leg-bob cycle (alternating legs, arms counterswing)
  - Jump pose (legs tucked when airborne)
  - Facing direction (eye and hair sideburn flip)
  - Drop shadow ellipse
- HUD showing current distance (top-left) and controls hint (bottom)
- Game Over overlay with glowing title and final distance
