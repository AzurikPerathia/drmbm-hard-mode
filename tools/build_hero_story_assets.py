"""Build the story-route selector and prototype Dark Story Cream assets.

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
DIALOGUE_SIZE = (80, 112)
BACKGROUND = (0, 0, 73)


FONT_5X7 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
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
    width = sum(image.width for image in images)
    height = max(image.height for image in images)
    sample = Image.new("RGB", (width, height), BACKGROUND)
    cursor = 0
    for index, image in enumerate(images):
        if image.mode == "RGBA":
            sample.paste(image.convert("RGB"), (cursor, 0), image.getchannel("A"))
        else:
            sample.paste(image, (cursor, 0))
        cursor += image.width
    quantized = sample.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
    raw = quantized.getpalette()[: 12 * 3]

    colors = [BACKGROUND]
    for offset in range(0, len(raw), 3):
        color = tuple(raw[offset : offset + 3])
        snapped = tuple(genesis_channel(component) * 255 // 14 for component in color)
        if snapped not in colors:
            colors.append(snapped)
        if len(colors) == 13:
            break
    # Palette entries 14 and 15 are deliberately unused.  The original game
    # writes its white-flash effect into entry 14; keeping it out of Cream's
    # visible art prevents the face/ear texture corruption seen during flashes.
    while len(colors) < 13:
        colors.append(colors[-1])
    # Entry 13 is a stable opaque blue for Dark Story's STAGE lettering.
    colors.append((0, 68, 238))
    colors.extend((BACKGROUND, BACKGROUND))
    return colors


def remap(image: Image.Image, palette: list[tuple[int, int, int]]) -> Image.Image:
    rgba = image.convert("RGBA")
    indexed = Image.new("P", image.size)
    flat = [component for color in palette for component in color]
    indexed.putpalette(flat + [0] * (768 - len(flat)))
    source = rgba.load()
    target = indexed.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = source[x, y]
            if alpha < 128:
                target[x, y] = 0
                continue
            target[x, y] = min(
                range(14),
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


def replace_tile_regions(
    base: Image.Image,
    variant: Image.Image,
    regions: tuple[tuple[int, int, int, int], ...],
) -> Image.Image:
    """Copy tile-aligned regions while leaving the rest bit-identical."""

    output = base.copy()
    for left, top, right, bottom in regions:
        box = (left * 8, top * 8, right * 8, bottom * 8)
        output.paste(variant.crop(box), box)
    return output


def build_tile_pool(images: list[Image.Image]) -> tuple[bytes, list[list[int]]]:
    """Deduplicate portrait tiles and return one arbitrary tilemap per frame."""

    pool: list[bytes] = []
    lookup: dict[bytes, int] = {}
    maps: list[list[int]] = []

    def flipped(tile: bytes, horizontal: bool, vertical: bool) -> bytes:
        rows: list[list[int]] = []
        for y in range(8):
            row: list[int] = []
            for byte in tile[y * 4 : y * 4 + 4]:
                row.extend((byte >> 4, byte & 15))
            rows.append(row)
        if horizontal:
            rows = [list(reversed(row)) for row in rows]
        if vertical:
            rows.reverse()
        output = bytearray()
        for row in rows:
            for x in range(0, 8, 2):
                output.append((row[x] << 4) | row[x + 1])
        return bytes(output)

    for image in images:
        mapping: list[int] = []
        for tile_y in range(image.height // 8):
            for tile_x in range(image.width // 8):
                tile = tile_bytes(image, tile_x, tile_y)
                tile_id = lookup.get(tile)
                if tile_id is None:
                    tile_id = len(pool)
                    pool.append(tile)
                    lookup.setdefault(tile, tile_id)
                    lookup.setdefault(flipped(tile, True, False), tile_id | 0x0800)
                    lookup.setdefault(flipped(tile, False, True), tile_id | 0x1000)
                    lookup.setdefault(flipped(tile, True, True), tile_id | 0x1800)
                mapping.append(tile_id)
        maps.append(mapping)
    return b"".join(pool), maps


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


def prepare_dialogue(path: Path) -> Image.Image:
    """Normalize generated full-body art to a stable 10x14-tile sprite canvas."""

    source = Image.open(path).convert("RGBA")
    normalized = Image.new("RGBA", (1200, 1320), (0, 0, 0, 0))
    if source.width > 1200 or source.height > 1320:
        source.thumbnail((1200, 1320), Image.Resampling.LANCZOS)
    normalized.alpha_composite(source, ((1200 - source.width) // 2, 0))
    scaled = normalized.resize((80, 88), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", DIALOGUE_SIZE, (0, 0, 0, 0))
    canvas.alpha_composite(scaled, (0, 24))
    return canvas


def sprite_piece_art(
    image: Image.Image, pieces: tuple[tuple[int, int, int, int], ...]
) -> tuple[bytes, list[int]]:
    """Write column-major sprite pieces and return their starting tile IDs."""

    output = bytearray()
    starts: list[int] = []
    for start_x, start_y, width, height in pieces:
        starts.append(len(output) // 32)
        for x in range(width):
            for y in range(height):
                output.extend(tile_bytes(image, start_x + x, start_y + y))
    return bytes(output), starts


def write_palette(palette: list[tuple[int, int, int]], filename: str) -> None:
    output = bytearray()
    for red, green, blue in palette:
        r = genesis_channel(red)
        g = genesis_channel(green)
        b = genesis_channel(blue)
        output.extend(((b << 8) | (g << 4) | r).to_bytes(2, "big"))
    (PAL_DIR / filename).write_bytes(output)


def write_portrait_assets() -> None:
    neutral = prepare_portrait(SOURCE_DIR / "cream-neutral.png", remove_white=True)
    generated = {
        "Blink": prepare_portrait(SOURCE_DIR / "cream-blink.png"),
        "Ears": prepare_portrait(SOURCE_DIR / "cream-ears.png"),
        "Happy": prepare_portrait(SOURCE_DIR / "cream-happy.png", remove_white=True),
        "Upset": prepare_portrait(SOURCE_DIR / "cream-upset.png", remove_white=True),
        "Stress": prepare_portrait(SOURCE_DIR / "cream-stress.png"),
        "Defeated": prepare_portrait(SOURCE_DIR / "cream-defeated-v2.png", remove_white=True),
    }
    images = [
        neutral,
        replace_tile_regions(neutral, generated["Blink"], ((2, 2, 8, 6),)),
        replace_tile_regions(neutral, generated["Ears"], ((0, 0, 10, 2), (0, 2, 2, 7), (8, 2, 10, 7))),
        replace_tile_regions(neutral, generated["Happy"], ((2, 2, 8, 6),)),
        replace_tile_regions(neutral, generated["Upset"], ((2, 2, 8, 6),)),
        replace_tile_regions(neutral, generated["Stress"], ((2, 2, 8, 6),)),
        replace_tile_regions(neutral, generated["Defeated"], ((2, 2, 8, 6),)),
    ]
    palette = build_shared_palette(images)
    indexed = [remap(image, palette) for image in images]

    art, maps = build_tile_pool(indexed)
    if len(art) > 0x2000:
        raise RuntimeError(f"Cream portrait exceeds reserved VRAM: {len(art)} bytes")
    (ART_DIR / "Portrait - Cream.unc").write_bytes(art)
    write_palette(palette, "Portrait - Cream.pal")

    names = ("Neutral", "Blink", "Ears", "Happy", "Upset", "Stress", "Defeated")
    for name, tilemap in zip(names, maps):
        mapping = b"".join(tile.to_bytes(2, "big") for tile in tilemap)
        (MAP_DIR / f"Portrait - Cream ({name}).map").write_bytes(mapping)

    preview = Image.new("RGB", (80 * len(indexed), 56))
    for frame, image in enumerate(indexed):
        preview.paste(image.convert("RGB"), (frame * 80, 0))
    preview.resize((320 * len(indexed), 224), Image.Resampling.NEAREST).save(SOURCE_DIR / "cream-preview.png")

    print(f"Cream portrait: {len(art) // 32} unique tiles across {len(indexed)} frames")


def write_dialogue_assets() -> None:
    closed = prepare_dialogue(SOURCE_DIR / "cream-dialogue-closed.png")
    generated_open = prepare_dialogue(SOURCE_DIR / "cream-dialogue-open.png")
    opened = replace_tile_regions(closed, generated_open, ((4, 7, 6, 9),))
    palette = build_shared_palette([closed, opened])
    closed_indexed = remap(closed, palette)
    open_indexed = remap(opened, palette)

    pieces = (
        (0, 0, 4, 4), (4, 0, 4, 4), (8, 0, 2, 4),
        (0, 4, 4, 4), (4, 4, 4, 4), (8, 4, 2, 4),
        (0, 8, 4, 4), (4, 8, 4, 4), (8, 8, 2, 4),
        (0, 12, 4, 2), (4, 12, 4, 2), (8, 12, 2, 2),
    )
    art, starts = sprite_piece_art(closed_indexed, pieces)
    mouth_piece = ((4, 7, 2, 2),)
    mouth_art, mouth_starts = sprite_piece_art(open_indexed, mouth_piece)
    mouth_start = len(art) // 32 + mouth_starts[0]
    art += mouth_art
    if len(art) > 0x2000:
        raise RuntimeError(f"Cream dialogue sprite exceeds reserved VRAM: {len(art)} bytes")
    (ART_DIR / "Cutscene - Cream.unc").write_bytes(art)
    write_palette(palette, "Cutscene - Cream.pal")

    def mapping_words(include_mouth: bool) -> list[tuple[int, int, int, int]]:
        words: list[tuple[int, int, int, int]] = []
        talking_bob = -1 if include_mouth else 0
        for (tile_x, tile_y, width, height), start in zip(pieces, starts):
            size = (((height - 1) << 2) | (width - 1)) << 8
            words.append((tile_y * 8 - 16 + talking_bob, size | 2, 0xE400 + start, 8 + tile_x * 8))
        if include_mouth:
            words.append((39, 0x502, 0xE400 + mouth_start, 40))
        return words

    for suffix, include_mouth in (("Closed", False), ("Open", True)):
        output = bytearray()
        words = mapping_words(include_mouth)
        output.extend(len(words).to_bytes(2, "big"))
        for piece in words:
            for value in piece:
                output.extend((value & 0xFFFF).to_bytes(2, "big"))
        (MAP_DIR / f"Cutscene - Cream ({suffix}).map").write_bytes(output)

    preview = Image.new("RGBA", (160, 112), (0, 0, 0, 0))
    preview.alpha_composite(closed, (0, 0))
    preview.alpha_composite(opened, (80, 0))
    preview.resize((640, 448), Image.Resampling.NEAREST).save(SOURCE_DIR / "cream-dialogue-preview.png")
    print(f"Cream dialogue: {len(art) // 32} tiles including mouth overlay")


def label_tile(char: str, background: int = 12, shadow: int = 11, foreground: int = 14) -> Image.Image:
    image = Image.new("P", (8, 8), color=background)
    pixels = image.load()
    glyph = FONT_5X7[char]
    for y, row in enumerate(glyph):
        for x, bit in enumerate(row):
            if bit == "1" and x + 2 < 8 and y + 1 < 8:
                pixels[x + 2, y + 1] = shadow
    for y, row in enumerate(glyph):
        for x, bit in enumerate(row):
            if bit == "1":
                pixels[x + 1, y] = foreground
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


def write_stage_label_assets() -> None:
    # Palette entry 0 remains transparent: only the STAGE letters turn blue.
    stage_top: list[Image.Image] = []
    stage_bottom: list[Image.Image] = []
    for char in "STAGE":
        full = Image.new("P", (8, 16), color=0)
        glyph = FONT_5X7[char]
        pixels = full.load()
        for y, row in enumerate(glyph):
            for x, bit in enumerate(row):
                if bit == "1":
                    pixels[x + 1, y + 4] = 13
                    if x + 2 < 8 and y + 5 < 16:
                        pixels[x + 2, y + 5] = 12
        stage_top.append(full.crop((0, 0, 8, 8)))
        stage_bottom.append(full.crop((0, 8, 8, 16)))

    cream = [label_tile(char, background=1, shadow=1, foreground=12) for char in "CREAM"]
    art = b"".join(image_to_tiles(tile) for tile in stage_top + stage_bottom + cream)
    (ART_DIR / "Dark Story Stage Labels.unc").write_bytes(art)


if __name__ == "__main__":
    write_portrait_assets()
    write_dialogue_assets()
    write_menu_assets()
    write_stage_label_assets()
    print("Built Cream animations and story-route interface assets.")
