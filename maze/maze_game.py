import pygame, sys
from pathlib import Path

# ---------- CONFIG ----------
ASSETS = Path("maze/assets")
BG_FILE   = ASSETS / "background_maze.png"    # 你的像素迷宫背景
BLUE_FILE = ASSETS / "blue_player.png"
RED_FILE  = ASSETS / "red_player.png"

# 把这两个尺寸改成你的背景真实像素
WIN_W, WIN_H = 800, 480        # 若你用 840x480，请改成 840, 480

# 角色基准尺寸 & 放大倍率
SPRITE_BASE = 32
SPRITE_SCALE = 2               # 放大一倍 => 2
SPEED = 3                      # 每帧像素速度

# 起点（可按需微调）
BLUE_START = (90,  86)        # 蓝：WASD
RED_START  = (70, 360)        # 红：方向键

# 草垛（黄色）阈值——适配你的贴图
HAY_RGB   = (226, 171, 66, 255)    # 近似 #E2AB42
HAY_TOL   = (60,  60,  60, 120)    # 容差，必要时放大/缩小

# ---------- HELPERS ----------
def load_png(path: Path) -> pygame.Surface:
    img = pygame.image.load(str(path)).convert_alpha()
    return img

def scale_sprite(surf: pygame.Surface, scale: int) -> pygame.Surface:
    size = SPRITE_BASE * scale
    # 用 nearest 保留像素风
    return pygame.transform.scale(surf, (size, size))

def move_with_collision(rect: pygame.Rect, dx: int, dy: int,
                        hit_mask: pygame.mask.Mask,
                        wall_mask: pygame.mask.Mask):
    # x 轴尝试
    if dx:
        oldx = rect.x
        rect.x += dx
        # Debug collision detection
        collision = wall_mask.overlap(hit_mask, (rect.x, rect.y))
        print(f"Collision detected: {collision} at position: ({rect.x}, {rect.y})")
        if collision:
            rect.x = oldx
    # y 轴尝试
    if dy:
        oldy = rect.y
        rect.y += dy
        # Debug collision detection
        collision = wall_mask.overlap(hit_mask, (rect.x, rect.y))
        print(f"Collision detected: {collision} at position: ({rect.x}, {rect.y})")
        if collision:
            rect.y = oldy

# ---------- MAIN ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H), 0, 32)  # 不要 SCALED/RESIZABLE
    pygame.display.set_caption("Pixel Maze Duel")
    clock = pygame.time.Clock()

    # 背景：必须与窗口尺寸一致
    bg = load_png(BG_FILE)
    if bg.get_width() != WIN_W or bg.get_height() != WIN_H:
        raise SystemExit(f"Background size mismatch. Expected {WIN_W}x{WIN_H}, "
                         f"got {bg.get_width()}x{bg.get_height()}.")

    # 仅从“黄色草垛”提取墙 mask（不会把整张当墙）
    wall_mask = pygame.mask.from_threshold(bg, HAY_RGB, HAY_TOL)
    # Debug wall_mask generation
    print(f"Wall mask pixel count: {wall_mask.count()}")
    if wall_mask.count() < 1000:
        print("[WARN] wall_mask has very few pixels—adjust HAY_RGB/HAY_TOL.")

    # 角色：加载 → 放大一次 → 建 mask
    blue_img_raw = load_png(BLUE_FILE)
    red_img_raw  = load_png(RED_FILE)
    blue_img = scale_sprite(blue_img_raw, SPRITE_SCALE)
    red_img  = scale_sprite(red_img_raw,  SPRITE_SCALE)
    blue_mask = pygame.mask.from_surface(blue_img)
    red_mask  = pygame.mask.from_surface(red_img)

    # 起点
    blue_rect = blue_img.get_rect(topleft=BLUE_START)
    red_rect  = red_img.get_rect(topleft=RED_START)

    # 简单 UI 字体（可无视）
    font = pygame.font.SysFont("Arial", 24, bold=True)

    running = True
    while running:
        dt = clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                if e.key == pygame.K_r:
                    blue_rect.topleft = BLUE_START
                    red_rect.topleft  = RED_START

        pygame.event.pump()
        keys = pygame.key.get_pressed()

        # 蓝玩家：WASD
        blue_dx = (keys[pygame.K_d] - keys[pygame.K_a]) * SPEED
        blue_dy = (keys[pygame.K_s] - keys[pygame.K_w]) * SPEED
        move_with_collision(blue_rect, blue_dx, blue_dy, blue_mask, wall_mask)

        # 红玩家：方向键
        red_dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * SPEED
        red_dy = (keys[pygame.K_DOWN]  - keys[pygame.K_UP])   * SPEED
        move_with_collision(red_rect, red_dx, red_dy, red_mask, wall_mask)

        # Debug player movement
        print(f"Blue dx: {blue_dx}, dy: {blue_dy}, position: {blue_rect.topleft}")
        print(f"Red dx: {red_dx}, dy: {red_dy}, position: {red_rect.topleft}")

        # 绘制
        screen.blit(bg, (0, 0))
        screen.blit(blue_img, blue_rect)
        screen.blit(red_img,  red_rect)

        # 底部提示
        txt = font.render("Blue: WASD   Red: Arrows   R: restart   ESC: quit",
                          True, (255,255,255))
        screen.blit(txt, (14, WIN_H-30))

        # Visualize wall_mask for debugging
        wall_surface = pygame.Surface((WIN_W, WIN_H))
        wall_surface.set_colorkey((0, 0, 0))
        wall_surface.fill((0, 0, 0))
        for y in range(WIN_H):
            for x in range(WIN_W):
                if wall_mask.get_at((x, y)):
                    wall_surface.set_at((x, y), (255, 255, 255))
        screen.blit(wall_surface, (0, 0))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
