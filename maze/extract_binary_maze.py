from PIL import Image

def is_hay(pixel):
    r, g, b, a = pixel
    # Transparent = walkable
    if a < 50:
        return False
    # Adjusted thresholds for yellow haystack detection
    return (r > 140 and g > 110 and b < 90)

def main():
    img = Image.open("maze/assets/Golden_haystacks_maze.png").convert("RGBA")
    w, h = img.size
    pixels = img.load()

    maze = []
    for y in range(h):
        row = ""
        for x in range(w):
            if is_hay(pixels[x, y]):
                row += "X"
            else:
                row += " "
        maze.append(row)

    with open("maze/level_binary_maze.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(maze))

    print("✅ Maze extraction complete!")
    print(f"Saved to: maze/level_binary_maze.txt")
    print(f"Size: {w} × {h}")

if __name__ == "__main__":
    main()