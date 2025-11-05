from PIL import Image
from pathlib import Path
import colorsys

IMG = "maze/assets/background_maze.png"
OUT = "maze/level_maze.txt"
TILE = 32               # 800x480 -> 25x15
WIDTH, HEIGHT = 800, 480

def is_hay(rgb):
    r,g,b = rgb
    h,s,v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    # 宽松一点的黄/棕范围：适配高光/阴影
    if 0.08 <= h <= 0.18 and s >= 0.25 and v >= 0.25:
        return True
    # 再补一个"偏棕"兜底（阴影比较暗）
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
