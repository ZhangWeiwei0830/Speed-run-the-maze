import pygame
import sys
from PIL import Image
from pathlib import Path
import colorsys
import random

# ------------ 基础设置 ------------
WIDTH, HEIGHT = 800, 480
FPS = 60
TIMER_SECONDS = 3 * 60  # 3 分钟

BG_PATH = "maze/assets/background_maze.png"
BLUE_PATH = "maze/assets/blue_player.png"
RED_PATH = "maze/assets/red_player.png"

# 你图上的起点
BLUE_START = (200, 200)  # New position for blue player
RED_START = (700, 300)  # New position for red player

# 终点/旗子区域（终点区域）
END_ZONE = pygame.Rect(745, 160, 50, 80)
# 兼容老代码变量名（可选）
FLAG_RECT = END_ZONE

PLAYER_SIZE = 32
PLAYER_SPEED = 2.4

IMG = "maze/assets/background_maze.png"
OUT = "maze/level_maze.txt"
TILE = 32               # 800x480 -> 25x15


def is_hay_wall(rgb):
    """判断这个像素是不是黄色草垛"""
    r, g, b, *_ = rgb  # 忽略多余的通道，例如 Alpha
    # 主体是金黄
    if r > 150 and g > 110 and b < 90:
        return True
    # 阴影偏棕
    if r > 120 and g > 90 and b < 75:
        return True
    return False


def build_wall_mask(bg_surf):
    """把整张背景图扫一遍，生成一个 True/False 的墙体表"""
    w, h = bg_surf.get_size()
    px = pygame.PixelArray(bg_surf)
    wall_mask = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            color = bg_surf.unmap_rgb(px[x, y])
            if is_hay_wall(color):
                wall_mask[y][x] = True
    del px
    return wall_mask


def rect_hits_wall(rect, mask):
    """玩家的矩形跟草垛有没有撞上"""
    # iterate only over the intersection between rect and the mask bounds
    mw, mh = mask.get_size()
    x0 = max(0, rect.left)
    y0 = max(0, rect.top)
    x1 = min(mw, rect.right)
    y1 = min(mh, rect.bottom)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if mask.get_at((x, y)):
                return True
    return False


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pixel Maze Duel")
    clock = pygame.time.Clock()

    # keep keyboard focus so get_pressed() works after clicks
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(True)

    # 背景: removed external image, use a plain solid color so only characters remain
    bg = pygame.Surface((WIDTH, HEIGHT))
    bg.fill((30, 120, 30))  # plain "grass" color

    # 玩家贴图
    blue_img = pygame.transform.smoothscale(
        pygame.image.load(BLUE_PATH).convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE)
    )
    red_img = pygame.transform.smoothscale(
        pygame.image.load(RED_PATH).convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE)
    )

    # No hay_wall asset — use an empty mask so no wall collisions occur
    hay_wall_mask = pygame.mask.Mask((WIDTH, HEIGHT))  # all False (no collisions)

    # Colors
    OBSTACLE_COLOR = (120, 80, 40)   # brown block color
    END_ZONE_COLOR = (255, 204, 0)   # gold for the end/flag
    END_ZONE_BORDER = (200, 140, 0)

    # --- Maze generator: perfect maze (recursive backtracker) with 40x40 cells ---
    def generate_obstacles(cell=40, passage_expand=0):
        """Produce a perfect maze where each tile is `cell`×`cell` pixels.
        We use an expanded visual grid where odd indices are passage centers and
        carving moves by 2 tiles so walls remain aligned to the `cell` grid.
        `passage_expand` = number of dilation iterations to widen passages (0 = 1-cell wide).
        Returns list of pygame.Rect wall blocks (cell-aligned).
        """
        visual_cols = WIDTH // cell
        visual_rows = HEIGHT // cell

        # ensure at least a 3x3 visual grid
        visual_cols = max(3, visual_cols)
        visual_rows = max(3, visual_rows)

        # map pixel pos to visual tile coords
        def pos_to_tile(pos):
            x, y = pos
            tx = min(visual_cols - 1, max(0, x // cell))
            ty = min(visual_rows - 1, max(0, y // cell))
            return tx, ty

        start_tile = pos_to_tile(BLUE_START)
        end_tile = pos_to_tile(END_ZONE.center)

        # visual grid: True = wall, False = passage
        grid = [[True for _ in range(visual_rows)] for _ in range(visual_cols)]

        # convert to "carvable" coordinates where passages are at odd indices:
        def to_carve(tile):
            tx, ty = tile
            # clamp and map to odd coordinate (1,3,5,...)
            cx = min(visual_cols - 1, max(1, tx | 1))
            cy = min(visual_rows - 1, max(1, ty | 1))
            return cx, cy

        sx, sy = to_carve(start_tile)
        ex, ey = to_carve(end_tile)

        # carve with recursive backtracker stepping by 2 tiles
        dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        stack = [(sx, sy)]
        grid[sx][sy] = False
        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy in dirs:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < visual_cols and 0 <= ny < visual_rows and grid[nx][ny]:
                    neighbors.append((nx, ny))
            if neighbors:
                nx, ny = random.choice(neighbors)
                # remove wall between
                wx, wy = (cx + nx) // 2, (cy + ny) // 2
                grid[wx][wy] = False
                grid[nx][ny] = False
                stack.append((nx, ny))
            else:
                stack.pop()

        # ensure end is passage
        grid[ex][ey] = False

        # optionally expand passages by converting adjacent wall tiles into passages
        for _ in range(max(0, passage_expand)):
            new_grid = [row[:] for row in grid]
            for tx in range(visual_cols):
                for ty in range(visual_rows):
                    if grid[tx][ty]:
                        # if any 4-neighbor is passage, convert this wall to passage
                        neighbors = [(tx+1,ty),(tx-1,ty),(tx,ty+1),(tx,ty-1)]
                        if any(0 <= nx < visual_cols and 0 <= ny < visual_rows and not grid[nx][ny] for nx,ny in neighbors):
                            new_grid[tx][ty] = False
            grid = new_grid

        # convert True tiles to obstacle rects
        obs = []
        for tx in range(visual_cols):
            for ty in range(visual_rows):
                if grid[tx][ty]:
                    obs.append(pygame.Rect(tx * cell, ty * cell, cell, cell))

        # remove any obstacles overlapping start/red or end
        start_rect = pygame.Rect(BLUE_START[0], BLUE_START[1], PLAYER_SIZE, PLAYER_SIZE)
        red_rect = pygame.Rect(RED_START[0], RED_START[1], PLAYER_SIZE, PLAYER_SIZE)
        safe_obs = [r for r in obs if not r.colliderect(start_rect)
                    and not r.colliderect(red_rect)
                    and not r.colliderect(END_ZONE)]
        return safe_obs

    # initial maze: 40×40 tiles, 1-cell-wide passages (passage_expand=0)
    OBSTACLES = generate_obstacles(cell=40, passage_expand=0)

    # ✅ 盖掉背景里"画死的那两个大人"
    # 这两个矩形是我根据你截图估的，如果没盖干净，你就改这两个 rect 的位置 / 尺寸
    cover_blue = pygame.Rect(40, 40, 130, 140)   # 盖左上大蓝
    cover_red = pygame.Rect(40, 320, 130, 140)   # 盖左下大红

    # 我们用一块"草地色"去盖（取背景的(200,200)那块草地色）
    grass_color = bg.get_at((200, 200))

    # 玩家当前位置（浮点数）
    blue_x, blue_y = BLUE_START
    red_x, red_y = RED_START

    start_ticks = pygame.time.get_ticks()
    font = pygame.font.SysFont("arial", 28, True)
    small_font = pygame.font.SysFont("arial", 20, True)

    winner = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ---------- 处理事件 ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    blue_x, blue_y = BLUE_START
                    red_x, red_y = RED_START
                    start_ticks = pygame.time.get_ticks()
                    winner = None
                    # regenerate a fresh random maze on restart
                    OBSTACLES = generate_obstacles(cell=40, passage_expand=0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # re-grab input if user clicked away and came back
                pygame.event.set_grab(True)

        keys = pygame.key.get_pressed()

        if winner is None:
            # ---------- 蓝玩家移动 (WASD) ----------
            old_bx, old_by = blue_x, blue_y
            if keys[pygame.K_w]:
                blue_y -= PLAYER_SPEED
            if keys[pygame.K_s]:
                blue_y += PLAYER_SPEED
            if keys[pygame.K_a]:
                blue_x -= PLAYER_SPEED
            if keys[pygame.K_d]:
                blue_x += PLAYER_SPEED

            blue_rect = pygame.Rect(int(blue_x), int(blue_y), PLAYER_SIZE, PLAYER_SIZE)
            blue_rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
            # keep float position synced with the potentially clamped rect
            blue_x, blue_y = float(blue_rect.left), float(blue_rect.top)
            # obstacle collision (rect-based)
            if blue_rect.collidelist(OBSTACLES) != -1:
                blue_x, blue_y = old_bx, old_by
                blue_rect.topleft = (int(blue_x), int(blue_y))

            # remove noisy per-frame prints (use logging only on collisions or state change)
            if rect_hits_wall(blue_rect, hay_wall_mask):
                print(f"[DEBUG] Blue collided at ({blue_x},{blue_y})")

            # ---------- 红玩家移动 (方向键) ----------
            old_rx, old_ry = red_x, red_y
            if keys[pygame.K_UP]:
                red_y -= PLAYER_SPEED
            if keys[pygame.K_DOWN]:
                red_y += PLAYER_SPEED
            if keys[pygame.K_LEFT]:
                red_x -= PLAYER_SPEED
            if keys[pygame.K_RIGHT]:
                red_x += PLAYER_SPEED

            red_rect = pygame.Rect(int(red_x), int(red_y), PLAYER_SIZE, PLAYER_SIZE)
            red_rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
            # keep float position synced with the potentially clamped rect
            red_x, red_y = float(red_rect.left), float(red_rect.top)
            # obstacle collision (rect-based)
            if red_rect.collidelist(OBSTACLES) != -1:
                red_x, red_y = old_rx, old_ry
                red_rect.topleft = (int(red_x), int(red_y))

            if rect_hits_wall(red_rect, hay_wall_mask):
                print(f"[DEBUG] Red collided at ({red_x},{red_y})")

            # ---------- 判胜 ----------
            if blue_rect.colliderect(END_ZONE):
                winner = "A (Blue)"
            elif red_rect.colliderect(END_ZONE):
                winner = "B (Red)"

            # ---------- 判时间 ----------
            elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
            remaining = max(0, TIMER_SECONDS - elapsed)
            if remaining == 0 and winner is None:
                # 时间到了没人到旗子，就比谁近
                fx, fy = FLAG_RECT.center
                bx, by = blue_rect.center
                rx, ry = red_rect.center
                b_dist = abs(bx - fx) + abs(by - fy)
                r_dist = abs(rx - fx) + abs(ry - fy)
                if b_dist < r_dist:
                    winner = "A (Blue)"
                elif r_dist < b_dist:
                    winner = "B (Red)"
                else:
                    winner = "Draw"

        # ---------- 绘制 ----------
        screen.blit(bg, (0, 0))

        # 盖掉背景里画死的那俩人
        pygame.draw.rect(screen, grass_color, cover_blue)
        pygame.draw.rect(screen, grass_color, cover_red)

        # Draw obstacles (blocks)
        for r in OBSTACLES:
            pygame.draw.rect(screen, OBSTACLE_COLOR, r)
            pygame.draw.rect(screen, (0,0,0), r, 2)

        # Draw end zone / flag
        pygame.draw.rect(screen, END_ZONE_COLOR, END_ZONE)
        pygame.draw.rect(screen, END_ZONE_BORDER, END_ZONE, 3)

        # 计时器
        elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
        remaining = max(0, TIMER_SECONDS - elapsed)
        m, s = divmod(remaining, 60)
        pygame.draw.rect(screen, (0, 0, 0), (120, 0, 560, 48))
        timer_surf = font.render(f"{m}:{s:02d}", True, (255, 204, 0))
        screen.blit(timer_surf, (WIDTH // 2 - timer_surf.get_width() // 2, 8))

        # 玩家（只画一次）
        screen.blit(blue_img, (int(blue_x), int(blue_y)))
        screen.blit(red_img, (int(red_x), int(red_y)))

        # 底部文字
        info = small_font.render("Blue: WASD   Red: Arrows   R: restart   ESC: quit", True, (255, 255, 255))
        screen.blit(info, (10, HEIGHT - 26))

        if winner:
            w_surf = font.render(f"Winner: {winner}", True, (255, 204, 0))
            screen.blit(w_surf, (WIDTH // 2 - w_surf.get_width() // 2, HEIGHT - 60))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def is_hay(rgb):
    r,g,b = rgb
    h,s,v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    # 宽松一点的黄/棕范围：适配高光/阴影
    if 0.08 <= h <= 0.18 and s >= 0.25 and v >= 0.25:
        return True
    # 再补一个“偏棕”兜底（阴影比较暗）
    if r > 120 and g > 90 and b < 90:
        return True
    return False

def build_level():
    p = Path(IMG)
    if not p.exists():
        raise SystemExit(f"not found: {p}")
    im = Image.open(p).convert("RGB")
    if im.size != (WIDTH, HEIGHT):
        print(f"[warn] image size {im.size}, expect {(WIDTH,HEIGHT)}")

    cols = WIDTH // TILE
    rows = HEIGHT // TILE
    pixels = im.load()

    lines = []
    for row in range(rows):
        y = row*TILE + TILE//2
        y = min(HEIGHT-1, y)
        chars = []
        for col in range(cols):
            x = col*TILE + TILE//2
            x = min(WIDTH-1, x)
            rgb = pixels[x,y]
            chars.append('x' if is_hay(rgb) else ' ')
        lines.append(''.join(chars))

    Path(OUT).write_text('\n'.join(lines), encoding="utf-8")
    print(f"[ok] wrote {OUT}  ({cols}x{rows})")
    # 预览前5行
    for ln in lines[:5]:
        print(ln)

# Note: we removed the bottom "if __name__ == '__main__': main()" so the game main() remains the entrypoint.
# To generate the level file manually, call build_level() from a separate script or an interactive session.

if __name__ == "__main__":
    main()

