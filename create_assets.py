# create_assets.py
# Generate an approximate maze background and two placeholder player sprites
import pygame
from pathlib import Path

pygame.init()
ASSETS = Path("assets")
ASSETS.mkdir(exist_ok=True)
W, H = 800, 480
bg = pygame.Surface((W,H))
# ground
bg.fill((80,120,60))

# helper to draw thick "hay" walls as rounded rectangles
def draw_hay_rect(surf, rect):
    color = (200,150,60)
    shadow = (140,100,30)
    pygame.draw.rect(surf, shadow, (rect[0]+3, rect[1]+3, rect[2], rect[3]))
    pygame.draw.rect(surf, color, rect)

# draw a stylized maze roughly matching the sample layout
th = 36
pad = 12
# vertical walls columns
cols = [0+pad, 260, 520, 760-th]
for x in cols:
    for y in range(pad, H-th, th*2):
        draw_hay_rect(bg, (x, y, th, th))

# draw some continuous wall strips to form corridors (approx)
blocks = [
    (0+pad, 0+pad, 300, th),
    (0+pad, 0+pad, th, 200),
    (0+pad, 200, 200, th),
    (200, 200, th, 120),
    (200, 320, 340, th),
    (520, 0+pad, th, 260),
    (520, 260, 220, th),
    (700, 120, th, 120),
]
for b in blocks:
    draw_hay_rect(bg, b)

# add a right-side red flag
flag_x = W - 60
flag_y = H//3
pygame.draw.rect(bg, (180,30,30), (flag_x+18, flag_y+6, 8, 28))
pygame.draw.polygon(bg, (200,40,40), [(flag_x+26, flag_y+6), (flag_x+46, flag_y+16), (flag_x+26, flag_y+26)])

# add some darker detailing
for i in range(200):
    import random
    x = random.randrange(0, W)
    y = random.randrange(0, H)
    pygame.draw.circle(bg, (50,90,40), (x,y), 1)

# save
pygame.image.save(bg, str(ASSETS / 'background_maze.png'))

# blue player sprite
ps = pygame.Surface((32,32), pygame.SRCALPHA)
ps.fill((0,0,0,0))
pygame.draw.circle(ps, (60,140,220), (16,12), 10)
pygame.draw.rect(ps, (20,60,140), (8,18,16,10))
pygame.image.save(ps, str(ASSETS / 'blue_player.png'))

# red player sprite
pr = pygame.Surface((32,32), pygame.SRCALPHA)
pr.fill((0,0,0,0))
pygame.draw.circle(pr, (220,70,90), (16,12), 10)
pygame.draw.rect(pr, (140,30,60), (8,18,16,10))
pygame.image.save(pr, str(ASSETS / 'red_player.png'))

print('Generated assets/background_maze.png, blue_player.png, red_player.png')
