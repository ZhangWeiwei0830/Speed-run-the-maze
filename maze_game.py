import pygame
import sys
from PIL import Image
from pathlib import Path
import colorsys

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

# 你图上右边红旗的位置（可以微调）
FLAG_RECT = pygame.Rect(745, 160, 50, 80)

PLAYER_SIZE = 48
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
    # Ensure coordinates are within bounds
    if not (0 <= rect.left < mask.get_size()[0] and 0 <= rect.top < mask.get_size()[1]):
        return False

    for y in range(max(0, rect.top), min(mask.get_size()[1], rect.bottom)):
        for x in range(max(0, rect.left), min(mask.get_size()[0], rect.right)):
            if mask.get_at((x, y)):
                return True
    return False


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pixel Maze Duel")
    clock = pygame.time.Clock()

    # 背景
    bg = pygame.image.load(BG_PATH).convert()

    # 玩家贴图
    blue_img = pygame.transform.smoothscale(
        pygame.image.load(BLUE_PATH).convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE)
    )
    red_img = pygame.transform.smoothscale(
        pygame.image.load(RED_PATH).convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE)
    )

    # 从背景生成墙体遮罩
    wall_mask = build_wall_mask(bg)

    # Re-identify black lines in hay_wall.png as collision areas
    hay_wall_img = pygame.image.load("maze/assets/hay_wall.png").convert()
    HAY_RGB = (0, 0, 0)  # Black color for collision
    HAY_TOL = (30, 30, 30)  # Tolerance for black detection
    hay_wall_mask = pygame.mask.from_threshold(hay_wall_img, HAY_RGB, HAY_TOL)

    # Debugging wall_mask generation
    wall_pixel_count = sum(sum(row) for row in wall_mask)
    print(f"[DEBUG] Wall mask pixel count: {wall_pixel_count}")

    # Visualize wall_mask for debugging
    debug_surf = pygame.Surface((WIDTH, HEIGHT))
    debug_surf.set_colorkey((0, 0, 0))
    for y, row in enumerate(wall_mask):
        for x, is_wall in enumerate(row):
            if is_wall:
                debug_surf.set_at((x, y), (255, 0, 0))
    screen.blit(debug_surf, (0, 0))

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
            if rect_hits_wall(blue_rect, hay_wall_mask):
                # 撞墙回退
                blue_x, blue_y = old_bx, old_by
                blue_rect.topleft = (int(blue_x), int(blue_y))

            # Debugging blue player movement
            print(f"[DEBUG] Blue position: ({blue_x}, {blue_y})")
            print(f"[DEBUG] Blue collision: {rect_hits_wall(blue_rect, hay_wall_mask)}")

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
            if rect_hits_wall(red_rect, hay_wall_mask):
                # 撞墙回退
                red_x, red_y = old_rx, old_ry
                red_rect.topleft = (int(red_x), int(red_y))

            # Debugging red player movement
            print(f"[DEBUG] Red position: ({red_x}, {red_y})")
            print(f"[DEBUG] Red collision: {rect_hits_wall(red_rect, hay_wall_mask)}")

            # ---------- 判胜 ----------
            if blue_rect.colliderect(FLAG_RECT):
                winner = "A (Blue)"
            elif red_rect.colliderect(FLAG_RECT):
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

        # Commented out visualization of hay_wall_mask to resolve green screen issue
        # hay_debug_surf = pygame.Surface((WIDTH, HEIGHT))
        # hay_debug_surf.set_colorkey((0, 0, 0))
        # for y in range(hay_wall_mask.get_size()[1]):
        #     for x in range(hay_wall_mask.get_size()[0]):
        #         if hay_wall_mask.get_at((x, y)):
        #             hay_debug_surf.set_at((x, y), (0, 255, 0))  # Green for hay wall
        # screen.blit(hay_debug_surf, (0, 0))

        # Debugging collision mask visualization
        # collision_debug_surf = pygame.Surface((WIDTH, HEIGHT))
        # collision_debug_surf.set_colorkey((0, 0, 0))
        # for y in range(hay_wall_mask.get_size()[1]):
        #     for x in range(hay_wall_mask.get_size()[0]):
        #         if hay_wall_mask.get_at((x, y)):
        #             collision_debug_surf.set_at((x, y), (255, 0, 0))  # Red for collision areas
        # screen.blit(collision_debug_surf, (0, 0))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()


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

def main():
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

if __name__ == "__main__":
    main()

