#!/usr/bin/env python3
"""
render_and_report.py
Load maze/assets background and sprites, run HSV detection to compute
walls, flag, blue/red starts (selecting blue candidate #2), render a single
frame (background + sprites + HUD) and save it as maze_run_screenshot.png.
Print a console summary as requested.
"""
import pygame, sys, os
from pathlib import Path
import colorsys

# config
WIDTH, HEIGHT = 800, 480
ASSETS = Path('maze') / 'assets'
BG = ASSETS / 'background_maze.png'
BLUE = ASSETS / 'blue_player.png'
RED = ASSETS / 'red_player.png'
SCREENSHOT = 'maze_run_screenshot.png'
SELECT_BLUE_CLUSTER = 2
# manual start positions to match maze_game.py (user-requested)
BLUE_START_POS = (55, 48)
RED_START_POS  = (60, 340)

if not BG.exists():
    print('Missing background:', BG)
    sys.exit(1)

# helpers

def rgb_to_hsv(r,g,b):
    h,s,v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
    return h,s,v

def is_yellow_hsv(r,g,b):
    h,s,v = rgb_to_hsv(r,g,b)
    return (0.10 <= h <= 0.20) and (s > 0.35) and (v > 0.25)

def is_red_hsv(r,g,b):
    h,s,v = rgb_to_hsv(r,g,b)
    return ((h <= 0.06 or h >= 0.94) and s > 0.4 and v > 0.2)

def is_blue_hsv(r,g,b):
    h,s,v = rgb_to_hsv(r,g,b)
    return (0.45 <= h <= 0.78) and (s > 0.12) and (v > 0.10)

def is_blue_relaxed(r,g,b):
    h,s,v = rgb_to_hsv(r,g,b)
    return (0.40 <= h <= 0.80) and (s > 0.08) and (v > 0.06)

# load background
pygame.init()
# initialize a display so surfaces can be converted; this will open a window briefly
screen = pygame.display.set_mode((WIDTH, HEIGHT))
bg = pygame.image.load(str(BG)).convert()

# scan
walls = [[False]*WIDTH for _ in range(HEIGHT)]
flag_points = []
blue_points = []
red_points = []

for y in range(HEIGHT):
    for x in range(WIDTH):
        col = bg.get_at((x,y))
        r,g,b = col.r, col.g, col.b
        if is_yellow_hsv(r,g,b):
            walls[y][x] = True
        if is_red_hsv(r,g,b):
            flag_points.append((x,y))
            red_points.append((x,y))
        if is_blue_hsv(r,g,b):
            blue_points.append((x,y))

# flag rect
if flag_points:
    xs = [p[0] for p in flag_points]; ys = [p[1] for p in flag_points]
    flag_rect = (min(xs), min(ys), max(xs)-min(xs)+1, max(ys)-min(ys)+1)
else:
    flag_rect = None

# bboxes

def bbox_from_points(points):
    if not points: return None
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs)-min(xs)+1, max(ys)-min(ys)+1)

blue_bbox = bbox_from_points(blue_points)
red_bbox = bbox_from_points(red_points)

# if blue missing, try relaxed components
import collections
if blue_bbox is None:
    relaxed_mask = [[False]*WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            col = bg.get_at((x,y))
            if is_blue_relaxed(col.r, col.g, col.b):
                relaxed_mask[y][x] = True
    seen = [[False]*WIDTH for _ in range(HEIGHT)]
    comps = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if relaxed_mask[y][x] and not seen[y][x]:
                dq = collections.deque()
                dq.append((x,y))
                seen[y][x] = True
                size = 0; sx=0; sy=0
                while dq:
                    cx,cy = dq.popleft()
                    size += 1; sx += cx; sy += cy
                    for nx,ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
                        if 0<=nx<WIDTH and 0<=ny<HEIGHT and not seen[ny][nx] and relaxed_mask[ny][nx]:
                            seen[ny][nx] = True; dq.append((nx,ny))
                comps.append((size,sx,sy))
    if comps:
        comps.sort(reverse=True, key=lambda c:c[0])
        size,sx,sy = comps[0]
        cx = sx//size; cy = sy//size
        blue_bbox = (max(0,cx-8), max(0,cy-8), 16,16)
    else:
        # heuristic clusters
        candidates = []
        for y in range(HEIGHT):
            for x in range(WIDTH):
                col = bg.get_at((x,y))
                h,s,v = rgb_to_hsv(col.r,col.g,col.b)
                hue_score = 1.0 - min(abs(h-0.6),1.0)
                score = hue_score*(s+v)
                candidates.append((score,x,y))
        candidates.sort(reverse=True,key=lambda c:c[0])
        top = candidates[:300]
        clusters = []
        for score,x,y in top:
            placed=False
            for i,(cnt,sx,sy) in enumerate(clusters):
                cx = sx//cnt; cy = sy//cnt
                if abs(x-cx)<=12 and abs(y-cy)<=12:
                    clusters[i] = (cnt+1,sx+x,sy+y); placed=True; break
            if not placed:
                clusters.append((1,x,y))
            if len(clusters)>=6: break
        clusters.sort(reverse=True,key=lambda c:c[0])
        top3 = []
        for i,(cnt,sx,sy) in enumerate(clusters[:3]):
            cx = sx//cnt; cy = sy//cnt; top3.append((cnt,cx,cy))
        if len(top3)>=SELECT_BLUE_CLUSTER:
            _,cx,cy = top3[SELECT_BLUE_CLUSTER-1]
            blue_bbox = (max(0,cx-8), max(0,cy-8),16,16)
        else:
            print('Blue detection failed; top3 candidates:', top3)
            sys.exit(1)

# red bbox presence check
if red_bbox is None:
    # compute top3 red clusters
    candidates=[]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            col = bg.get_at((x,y))
            h,s,v = rgb_to_hsv(col.r,col.g,col.b)
            hue_dist = min(abs(h-0.0), abs(h-1.0))
            score = (1.0-hue_dist)*(s+v)
            candidates.append((score,x,y))
    candidates.sort(reverse=True,key=lambda c:c[0])
    top = candidates[:400]
    clusters=[]
    for score,x,y in top:
        placed=False
        for i,(cnt,sx,sy) in enumerate(clusters):
            cx = sx//cnt; cy = sy//cnt
            if abs(x-cx)<=12 and abs(y-cy)<=12:
                clusters[i]=(cnt+1,sx+x,sy+y); placed=True; break
        if not placed:
            clusters.append((1,x,y))
        if len(clusters)>=6: break
    clusters.sort(reverse=True,key=lambda c:c[0])
    top3=[]
    for i,(cnt,sx,sy) in enumerate(clusters[:3]):
        cx=sx//cnt; cy=sy//cnt; top3.append((cnt,cx,cy))
    print('Red detection failed; top3 candidates:', top3)
    sys.exit(1)

# compute centers and sprite top-lefts
def center_from_bbox_tuple(b):
    x,y,w,h = b
    return (x + w//2, y + h//2)

# Use manual start positions instead of detected centers
bx, by = BLUE_START_POS
rx, ry = RED_START_POS

# clamp just in case
bx = max(0, min(bx, WIDTH-32)); by = max(0, min(by, HEIGHT-32))
rx = max(0, min(rx, WIDTH-32)); ry = max(0, min(ry, HEIGHT-32))

# load sprites, fail if missing
if not BLUE.exists() or not RED.exists():
    print('Missing sprites in', ASSETS)
    for fn in sorted(os.listdir(ASSETS)):
        p=ASSETS/fn; print(fn, p.stat().st_size)
    sys.exit(1)

# load and center into 32x32 with target 28
def load_centered_sprite(path):
    raw = pygame.image.load(str(path)).convert_alpha()
    w,h = raw.get_size()
    target=28
    scale = min(max(1, target/w), max(1, target/h))
    nw,nh = max(1,int(w*scale)), max(1,int(h*scale))
    small = pygame.transform.scale(raw, (nw,nh))
    canvas = pygame.Surface((32,32), pygame.SRCALPHA)
    canvas.blit(small, ((32-nw)//2, (32-nh)//2))
    return canvas

blue_sprite = load_centered_sprite(BLUE)
red_sprite = load_centered_sprite(RED)

# Render one frame
surf = pygame.Surface((WIDTH,HEIGHT))
surf.blit(bg, (0,0))
surf.blit(blue_sprite, (bx,by))
surf.blit(red_sprite, (rx,ry))

# draw HUD timer at 3:00
font = pygame.font.SysFont(None,22); bigfont = pygame.font.SysFont(None,36)
hud_w,hud_h = 220,34
hud = pygame.Surface((hud_w,hud_h), pygame.SRCALPHA); hud.fill((20,20,20,160))
txt = bigfont.render('3:00', True, (255,220,60)); hud.blit(txt, (hud_w//2-txt.get_width()//2, hud_h//2-txt.get_height()//2))
surf.blit(hud, (WIDTH//2 - hud_w//2, 6))

# save screenshot
pygame.image.save(surf, SCREENSHOT)

# count wall pixels
wall_count = sum(1 for y in range(HEIGHT) for x in range(WIDTH) if walls[y][x])

# print summary
print('Using background:', str(BG))
print('Blue start:', (bx,by))
print('Red start:', (rx,ry))
print('Flag rect:', flag_rect)
print('Wall pixels detected:', wall_count)
print('Saved screenshot to', SCREENSHOT)

pygame.quit()
sys.exit(0)
