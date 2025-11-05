import argparse
from pathlib import Path
from typing import Tuple
from PIL import Image
import colorsys

# 800x480，按像素风常用32像素一格 => 25列x15行
DEFAULT_TILE = 32
WIDTH, HEIGHT = 800, 480

def rgb_to_hsv(rgb: Tuple[int,int,int]):
    r,g,b = rgb
    return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)  # h∈[0,1]

def is_hay_wall(rgb: Tuple[int,int,int]) -> bool:
    """判断是否为黄色草垛像素（兼容高光/阴影）"""
    r,g,b = rgb
    h,s,v = rgb_to_hsv(rgb)
    # 主体黄：h≈0.10~0.16, s较高, v中等
    if 0.10 <= h <= 0.16 and s >= 0.35 and v >= 0.35:
        return True
    # 阴影棕：r高、b低
    if r > 130 and g > 95 and b < 90:
        return True
    return False

def cell_is_wall(img: Image.Image, x0: int, y0: int, tile: int) -> bool:
    """统计一个网格内草垛像素占比，超过阈值则此格为墙"""
    w, h = img.size
    x1 = min(x0 + tile, w)
    y1 = min(y0 + tile, h)
    pixels = img.crop((x0, y0, x1, y1)).convert("RGB").load()
    cnt_wall, cnt = 0, 0
    for y in range(y1 - y0):
        for x in range(x1 - x0):
            if is_hay_wall(pixels[x, y]):
                cnt_wall += 1
            cnt += 1
    return (cnt_wall / max(1, cnt)) >= 0.35  # 35% 以上判为墙

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="maze/assets/background_maze.png")
    ap.add_argument("--out", default="maze/level_maze.txt")
    ap.add_argument("--tile", type=int, default=DEFAULT_TILE)
    args = ap.parse_args()

    p_img = Path(args.image)
    if not p_img.exists():
        raise SystemExit(f"Image not found: {p_img}")

    img = Image.open(p_img).convert("RGB")
    if img.size != (WIDTH, HEIGHT):
        print(f"[warn] image is {img.size}, expected {(WIDTH, HEIGHT)}")

    cols = WIDTH // args.tile
    rows = HEIGHT // args.tile

    lines = []
    for r in range(rows):
        y0 = r * args.tile
        row_chars = []
        for c in range(cols):
            x0 = c * args.tile
            row_chars.append('x' if cell_is_wall(img, x0, y0, args.tile) else ' ')
        lines.append(''.join(row_chars))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text('\n'.join(lines), encoding="utf-8")

    print(f"[ok] wrote ASCII maze to: {out_path}")
    print(f"[info] size: {cols} cols x {rows} rows, tile={args.tile}px")
    print("Preview (top 5 rows):")
    for ln in lines[:5]:
        print(ln)

if __name__ == "__main__":
    main()
