Two-player Maze Game (800×480)

Place your assets in the `assets/` folder (create if missing):

- `assets/background_maze.png`  <-- REQUIRED, size 800×480. Green = walkable, yellow hay = walls, red flag = goal.
- (optional) `assets/blue_player.png`
- (optional) `assets/red_player.png`

Controls:
- Player A (Blue): W S A D
- Player B (Red) : Arrow keys
- R to restart, ESC to quit

Run:

```bash
pip install pygame
python maze_game.py
```

Notes:
- Collision is detected by sampling background pixel colors (yellow = wall). If wall/flag colors don't match, ask me to switch to HSV detection or provide a small sample pixel color to tune thresholds.
- You can adjust `SPEED`, `SAMPLE_STEP`, or starting positions in the top of `maze_game.py`.
