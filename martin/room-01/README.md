# room-01

A browser-based first-person 3D room exploration game built as a single `index.html` file using [Three.js](https://threejs.org/) (loaded via CDN importmap).

## Requirements

- The player is placed inside an enclosed room and sees a first-person 3D view.
- Movement via **W / A / S / D** keys.
- Camera look controlled by the mouse.
- On load, the game shows a **"Start Game"** overlay button. Clicking it locks the mouse pointer (pointer lock API), hides the cursor, and hands mouse control to the camera.
- **ESC** releases the pointer lock and returns to the overlay.
- The room is furnished with simple furniture.

## Design

### Technology

- **Three.js r0.160** via CDN `importmap` — no build step required.
- **PointerLockControls** from Three.js addons for mouse-look.
- Single `index.html`, no external assets.

### Room

- Dimensions: 12 × 5 × 12 (width × height × depth).
- Materials: warm wood-tone floor, off-white walls, light ceiling.
- Fog applied to match the scene background color for depth.

### Lighting

- Ambient light (cool blue-gray, low intensity) for base fill.
- Ceiling point light (warm white) with shadow casting — the main light source.
- Floor lamp point light (warm amber) in the back-right corner for accent lighting.

### Furniture

| Item | Position | Notes |
|---|---|---|
| Dining table | Center-back | 4 legs, dark wood |
| 4 Chairs | Around dining table | Seat + backrest + 4 legs each |
| Bookshelf | Left wall | 3 rows of books in varied colors and sizes |
| Sofa | Right wall | Seat, backrest, two armrests, two seat cushions |
| Coffee table | In front of sofa | 4 legs, matching wood tone |
| Floor lamp | Back-right corner | Pole + cone shade with emissive glow |
| Ceiling fixture | Center ceiling | Decorative box |
| 3 Paintings | Back wall | Framed colored panels at eye level |

### Controls

| Input | Action |
|---|---|
| Click "Start Game" | Locks pointer, hides cursor, starts mouse-look |
| W / A / S / D | Move forward / left / backward / right |
| Mouse | Look around (yaw + pitch) |
| ESC | Releases pointer lock, shows overlay |

A crosshair is displayed while the pointer is locked.

### Collision

Player position is clamped to the room bounds (wall margin 0.4 units). Eye height is fixed at 1.7 units.

## Implementation

- All geometry is built from `THREE.BoxGeometry` and `THREE.PlaneGeometry` primitives.
- The `cube(w, h, d, color, cx, cy, cz)` helper creates a box centered at the given world position.
- Furniture groups (chairs) use `THREE.Group` for easy rotation around a local origin.
- The render loop uses `renderer.setAnimationLoop` with a delta-time cap of 50 ms to handle tab-switching lag gracefully.
- Movement direction is derived each frame from `camera.getWorldDirection()` projected onto the XZ plane, so strafing and forward motion always match where the player is looking.
