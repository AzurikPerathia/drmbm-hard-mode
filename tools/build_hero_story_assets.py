"""Build the prototype Hero Story portrait and menu assets.

The source PNG files live in resources/source/cream.  The generated files use
the native 4bpp tile and 16-bit tilemap formats consumed by the disassembly.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "resources/source/cream"
ART_DIR = ROOT / "resources/art/art_nem/uncompressed"
MAP_DIR = ROOT / "resources/mappings/background/map_eni/uncompressed"
PAL_DIR = ROOT / "resources/palettes/line/new"

PORTRAIT_SIZE = (80, 56)
BACKGROUND = (0, 0, 73)


FONT_5X7 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    " ": ("00000",) * 7,
}


def remove_connected_white(image: Image.Image) -> Image.Image:
    """Make only the white area connected to the image border transparent."""

    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    queue: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in seen:
            continue
        seen.add((x, y))
        red, green, blue, alpha = pixels[x, y]
        if alpha == 0 or min(red, green, blue) >= 220:
            pixels[x, y] = (red, green, blue, 0)
            if x:
                queue.append((x - 1, y))
            if x + 1 < width:
                queue.append((x + 1, y))
            if y:
                queue.append((x, y - 1))
            if y + 1 < height:
                queue.append((x, y + 1))
    return rgba


def prepare_portrait(path: Path, remove_white: bool = False) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    if remove_white:
        image = remove_connected_white(image)

    # Keep Cream's face and hands centered in the board's wide 10x7-tile box.
    side = min(image.size)
    left = (image.width - side) // 2
    image = image.crop((left, 0, left + side, side))
    image = image.resize((80, 80), Image.Resampling.LANCZOS)
    image = image.crop((0, 6, 80, 62))

    backdrop = Image.new("RGBA", PORTRAIT_SIZE, (*BACKGROUND, 255))
    backdrop.alpha_composite(image)
    return backdrop.convert("RGB")


def genesis_channel(value: int) -> int:
    return max(0, min(14, round(value / 255 * 7) * 2))


def build_shared_palette(images: list[Image.Image]) -> list[tuple[int, int, int]]:
    sample = Image.new("RGB", (80 * len(images), 56))
    for index, image in enumerate(images):
        sample.paste(image, (index * 80, 0))
    quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT)
    raw = quantized.getpalette()[: 15 * 3]

    colors = [BACKGROUND]
    for offset in range(0, len(raw), 3):
        color = tuple(raw[offset : offset + 3])
        snapped = tuple(genesis_channel(component) * 255 // 14 for component in color)
        if snapped not in colors:
            colors.append(snapped)
        if len(colors) == 16:
            break
    while len(colors) < 16:
        colors.append(colors[-1])
    return colors


def remap(image: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    indexed = Image.new("P", image.size)
    flat = [component for color in palette for component in color]
    indexed.putpalette(flat + [0] * (768 - len(flat)))
    source = image.load()
    target = indexed.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue = source[x, y]
            target[x, y] = min(
                range(16),
                key=lambda index: sum(
                    (component - palette[index][channel]) ** 2
                    for channel, component in enumerate((red, green, blue))
                ),
            )
    return indexed


def image_to_tiles(image: Image.Image) -> bytes:
    pixels = image.load()
    output = bytearray()
    for tile_y in range(0, image.height, 8):
        for tile_x in range(0, image.width, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    output.append((pixels[tile_x + x, tile_y + y] << 4) | pixels[tile_x + x + 1, tile_y + y])
    return bytes(output)


def tile_bytes(image: Image.Image, tile_x: int, tile_y: int) -> bytes:
    pixels = image.load()
    output = bytearray()
    for y in range(8):
        for x in range(0, 8, 2):
            left = pixels[tile_x * 8 + x, tile_y * 8 + y]
            right = pixels[tile_x * 8 + x + 1, tile_y * 8 + y]
            output.append((left << 4) | right)
    return bytes(output)


def image_to_sprite_art(image: Image.Image) -> bytes:
    """Arrange tiles in the Mega Drive's column-major multi-sprite order."""

    pieces = ((0, 0, 4, 4), (4, 0, 4, 4), (8, 0, 2, 4),
              (0, 4, 4, 3), (4, 4, 4, 3), (8, 4, 2, 3))
    output = bytearray()
    for start_x, start_y, width, height in pieces:
        for x in range(width):
            for y in range(height):
                output.extend(tile_bytes(image, start_x + x, start_y + y))
    return bytes(output)


def write_palette(palette: list[tuple[int, int, int]]) -> None:
    output = bytearray()
    for red, green, blue in palette:
        r = genesis_channel(red)
        g = genesis_channel(green)
        b = genesis_channel(blue)
        output.extend(((b << 8) | (g << 4) | r).to_bytes(2, "big"))
    (PAL_DIR / "Portrait - Cream.pal").write_bytes(output)


def write_portrait_assets() -> None:
    images = [
        prepare_portrait(SOURCE_DIR / "cream-neutral.png", remove_white=True),
        prepare_portrait(SOURCE_DIR / "cream-happy.png", remove_white=True),
        prepare_portrait(SOURCE_DIR / "cream-upset.png", remove_white=True),
    ]
    palette = build_shared_palette(images)
    indexed = [remap(image, palette) for image in images]

    art = b"".join(image_to_tiles(image) for image in indexed)
    (ART_DIR / "Portrait - Cream.unc").write_bytes(art)
    (ART_DIR / "Cutscene - Cream.unc").write_bytes(image_to_sprite_art(indexed[0]))
    write_palette(palette)

    names = ("Neutral", "Happy", "Upset")
    for frame, name in enumerate(names):
        base = frame * 70
        mapping = b"".join((base + tile).to_bytes(2, "big") for tile in range(70))
        (MAP_DIR / f"Portrait - Cream ({name}).map").write_bytes(mapping)

    preview = Image.new("RGB", (240, 56))
    for frame, image in enumerate(indexed):
        preview.paste(image.convert("RGB"), (frame * 80, 0))
    preview.resize((960, 224), Image.Resampling.NEAREST).save(SOURCE_DIR / "cream-preview.png")


def label_tile(char: str) -> Image.Image:
    image = Image.new("P", (8, 8), color=12)
    pixels = image.load()
    glyph = FONT_5X7[char]
    for y, row in enumerate(glyph):
        for x, bit in enumerate(row):
            if bit == "1" and x + 2 < 8 and y + 1 < 8:
                pixels[x + 2, y + 1] = 11
    for y, row in enumerate(glyph):
        for x, bit in enumerate(row):
            if bit == "1":
                pixels[x + 1, y] = 14
    return image


def write_menu_assets() -> None:
    dark_tiles = [Image.new("P", (8, 8), color=12) for _ in range(10)]
    dark_tiles += [label_tile(char) for char in "DARK STORY"]
    dark_tiles += [Image.new("P", (8, 8), color=12) for _ in range(10)]

    hero_tiles = [Image.new("P", (8, 8), color=12) for _ in range(16)]
    hero_tiles += [Image.new("P", (8, 8), color=12) for _ in range(1)]
    hero_tiles += [label_tile(char) for char in "HERO STORY"]
    hero_tiles += [Image.new("P", (8, 8), color=12) for _ in range(5)]
    hero_tiles += [Image.new("P", (8, 8), color=12) for _ in range(16)]

    tiles = dark_tiles + hero_tiles
    art = b"".join(image_to_tiles(tile) for tile in tiles)
    (ART_DIR / "Hero Story Menu Labels.unc").write_bytes(art)

    dark_map = b"".join(tile.to_bytes(2, "big") for tile in range(30))
    hero_map = b"".join(tile.to_bytes(2, "big") for tile in range(30, 78))
    (MAP_DIR / "Hero Story Menu - Dark.map").write_bytes(dark_map)
    (MAP_DIR / "Hero Story Menu - Hero.map").write_bytes(hero_map)


if __name__ == "__main__":
    write_portrait_assets()
    write_menu_assets()
    print("Built Cream portrait and Hero Story menu assets.")
