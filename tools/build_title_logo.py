#!/usr/bin/env python3
"""Convert the custom title logo to the game's native Mega Drive assets."""

from pathlib import Path
import struct

from PIL import Image, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "resources/source/title/Mean Bean Machine - New Story.png"
ART = ROOT / "resources/art/art_nem/uncompressed/Title.unc"
MAP = ROOT / "resources/mappings/background/map_eni/uncompressed/Title - Logo.map"
PALETTE = ROOT / "resources/palettes/line/new/Title - Colors 1.pal"
PREVIEW = ROOT / "resources/source/title/Mean Bean Machine - New Story - Mega Drive preview.png"

WIDTH = 192
HEIGHT = 64
ORIGINAL_ART_SIZE = 38656  # 1208 tiles; everything after tile 147 is preserved.
FIRST_EXTRA_TILE = 1208
FONT_TILE = 1280


def md_channel(value: int) -> int:
    return max(0, min(7, round(value / 33))) * 33


def md_word(rgb):
    r, g, b = (max(0, min(7, round(c / 33))) * 2 for c in rgb)
    return (b << 8) | (g << 4) | r


def colour_distance(a, b):
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return 2 * dr * dr + 4 * dg * dg + db * db


def build_palette(image):
    opaque = [p[:3] for p in image.getdata() if p[3] >= 96 and max(p[:3]) >= 18]
    sample = Image.new("RGB", (len(opaque), 1))
    sample.putdata(opaque)
    reduced = sample.quantize(colors=14, method=Image.Quantize.MEDIANCUT)
    raw = reduced.getpalette()[: 14 * 3]
    colours = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]
    colours = [(md_channel(r), md_channel(g), md_channel(b)) for r, g, b in colours]

    result = [(0, 0, 0), (0, 0, 0)]
    for colour in colours:
        if colour not in result:
            result.append(colour)
    while len(result) < 16:
        result.append(result[-1])
    return result[:16]


def prepare_image():
    source = Image.open(SOURCE).convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox:
        source = source.crop(bbox)
    source = source.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    source = ImageEnhance.Contrast(source).enhance(1.12)
    source = ImageEnhance.Color(source).enhance(1.15)
    return source.filter(ImageFilter.UnsharpMask(radius=0.7, percent=135, threshold=2))


def index_image(image, palette):
    indexed = []
    for r, g, b, a in image.getdata():
        if a < 72:
            indexed.append(0)
            continue
        best = min(range(1, 16), key=lambda i: colour_distance((r, g, b), palette[i]))
        indexed.append(best)
    return indexed


def encode_tile(indices):
    data = bytearray()
    for row in range(8):
        start = row * 8
        for col in range(0, 8, 2):
            data.append((indices[start + col] << 4) | indices[start + col + 1])
    return bytes(data)


def build_assets():
    image = prepare_image()
    palette = build_palette(image)
    pixels = index_image(image, palette)

    tiles = []
    for tile_y in range(HEIGHT // 8):
        for tile_x in range(WIDTH // 8):
            values = []
            for y in range(8):
                offset = (tile_y * 8 + y) * WIDTH + tile_x * 8
                values.extend(pixels[offset:offset + 8])
            tiles.append(encode_tile(values))

    blank = bytes(32)
    tile_ids = {blank: 0}
    unique_tiles = []
    map_ids = []
    for tile in tiles:
        if tile not in tile_ids:
            ordinal = len(unique_tiles)
            tile_id = ordinal + 1 if ordinal < 147 else FIRST_EXTRA_TILE + ordinal - 147
            if tile_id >= FONT_TILE:
                raise RuntimeError("The converted logo exceeds the free title-screen VRAM.")
            tile_ids[tile] = tile_id
            unique_tiles.append(tile)
        map_ids.append(tile_ids[tile])

    art = bytearray(ART.read_bytes()[:ORIGINAL_ART_SIZE])
    if len(art) != ORIGINAL_ART_SIZE:
        raise RuntimeError("Unexpected original Title.unc size")
    for ordinal, tile in enumerate(unique_tiles):
        tile_id = ordinal + 1 if ordinal < 147 else FIRST_EXTRA_TILE + ordinal - 147
        needed = (tile_id + 1) * 32
        if len(art) < needed:
            art.extend(bytes(needed - len(art)))
        art[tile_id * 32:(tile_id + 1) * 32] = tile
    ART.write_bytes(art)

    MAP.write_bytes(b"".join(struct.pack(">H", tile_id) for tile_id in map_ids))
    PALETTE.write_bytes(b"".join(struct.pack(">H", md_word(c)) for c in palette))

    preview = Image.new("RGBA", (WIDTH, HEIGHT))
    preview.putdata([palette[i] + ((0 if i == 0 else 255),) for i in pixels])
    preview.resize((WIDTH * 4, HEIGHT * 4), Image.Resampling.NEAREST).save(PREVIEW)
    print(f"Title logo: {len(unique_tiles)} unique tiles, {len(art) // 32} total art tiles")


if __name__ == "__main__":
    build_assets()
