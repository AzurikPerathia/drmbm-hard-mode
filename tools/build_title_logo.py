#!/usr/bin/env python3
"""Convert the custom logo into a full-screen, four-palette Mega Drive title."""

from pathlib import Path
import colorsys
import struct

from PIL import Image, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "resources/source/title/Mean Bean Machine - New Story.png"
ART = ROOT / "resources/art/art_nem/uncompressed/Title.unc"
MAP = ROOT / "resources/mappings/background/map_eni/uncompressed/Title - Logo.map"
PREVIEW = ROOT / "resources/source/title/Mean Bean Machine - New Story - Mega Drive preview.png"
PALETTES = [
    ROOT / "resources/palettes/line/new/Title - Colors 1.pal",
    ROOT / "resources/palettes/line/new/Title - Colors 2.pal",
    ROOT / "resources/palettes/line/new/Title - Colors 3.pal",
    ROOT / "resources/palettes/line/new/Title - Colors 4 (Show Robotnik Face).pal",
]

WIDTH = 320
HEIGHT = 224
MAX_LOGO_WIDTH = 304
MAX_LOGO_HEIGHT = 190
FONT_TILE = 1280


def md_channel(value):
    return max(0, min(7, round(value / 33))) * 33


def md_word(rgb):
    r, g, b = (max(0, min(7, round(c / 33))) * 2 for c in rgb)
    return (b << 8) | (g << 4) | r


def colour_distance(a, b):
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return 2 * dr * dr + 4 * dg * dg + db * db


def prepare_canvas():
    source = Image.open(SOURCE).convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox:
        source = source.crop(bbox)
    scale = min(MAX_LOGO_WIDTH / source.width, MAX_LOGO_HEIGHT / source.height)
    size = (round(source.width * scale), round(source.height * scale))
    source = source.resize(size, Image.Resampling.LANCZOS)
    source = ImageEnhance.Contrast(source).enhance(1.10)
    source = ImageEnhance.Color(source).enhance(1.12)
    source = source.filter(ImageFilter.UnsharpMask(radius=0.65, percent=125, threshold=2))
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    canvas.alpha_composite(source, ((WIDTH - size[0]) // 2, (HEIGHT - size[1]) // 2))
    return canvas


def split_tiles(image):
    tiles = []
    data = list(image.getdata())
    for tile_y in range(HEIGHT // 8):
        for tile_x in range(WIDTH // 8):
            pixels = []
            for y in range(8):
                offset = (tile_y * 8 + y) * WIDTH + tile_x * 8
                pixels.extend(data[offset:offset + 8])
            tiles.append(pixels)
    return tiles


def tile_signature(tile):
    bins = [0.0] * 7  # red, yellow, green, cyan, blue, purple, neutral
    opaque = 0
    brightness = 0.0
    for r, g, b, a in tile:
        if a < 64:
            continue
        opaque += 1
        brightness += (r + g + b) / 765
        h, s, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < 0.18:
            bins[6] += 1
        else:
            bins[min(5, int((h * 6 + 0.5) % 6))] += 1
    if not opaque:
        return (0.0,) * 9
    return tuple(v / opaque for v in bins) + (opaque / 64, brightness / opaque)


def sq_distance(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def initial_groups(tiles):
    features = [tile_signature(tile) for tile in tiles]
    nonblank = [i for i, f in enumerate(features) if f[7] > 0]
    seeds = [nonblank[0]]
    while len(seeds) < 4:
        seeds.append(max(nonblank, key=lambda i: min(sq_distance(features[i], features[s]) for s in seeds)))
    centres = [features[i] for i in seeds]
    groups = [0] * len(tiles)
    for _ in range(12):
        groups = [min(range(4), key=lambda g: sq_distance(f, centres[g])) for f in features]
        for g in range(4):
            members = [features[i] for i in nonblank if groups[i] == g]
            if members:
                centres[g] = tuple(sum(v) / len(members) for v in zip(*members))
    return groups


def quantize_group(tiles, groups, group):
    pixels = [p[:3] for i, tile in enumerate(tiles) if groups[i] == group for p in tile if p[3] >= 64]
    if not pixels:
        return [(0, 0, 0)] * 16
    sample = Image.new("RGB", (len(pixels), 1))
    sample.putdata(pixels)
    reduced = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT)
    raw = reduced.getpalette()[:45]
    colours = [(md_channel(raw[i]), md_channel(raw[i + 1]), md_channel(raw[i + 2])) for i in range(0, len(raw), 3)]
    result = [(0, 0, 0)]
    for colour in colours:
        if colour not in result[1:]:
            result.append(colour)
    while len(result) < 16:
        result.append(result[-1])
    return result[:16]


def reconstruction_error(tile, palette):
    error = 0
    for r, g, b, a in tile:
        if a >= 64:
            error += min(colour_distance((r, g, b), colour) for colour in palette[1:])
    return error


def optimise_palettes(tiles):
    groups = initial_groups(tiles)
    palettes = None
    for _ in range(8):
        palettes = [quantize_group(tiles, groups, g) for g in range(4)]
        new_groups = []
        for tile in tiles:
            if not any(p[3] >= 64 for p in tile):
                new_groups.append(0)
            else:
                new_groups.append(min(range(4), key=lambda g: reconstruction_error(tile, palettes[g])))
        if new_groups == groups:
            break
        groups = new_groups
    return groups, palettes


def encode_tile(tile, palette):
    indices = []
    reconstructed = []
    for r, g, b, a in tile:
        if a < 64:
            index = 0
        else:
            index = min(range(1, 16), key=lambda i: colour_distance((r, g, b), palette[i]))
        indices.append(index)
        reconstructed.append(palette[index] + ((0 if index == 0 else 255),))
    encoded = bytearray()
    for row in range(8):
        start = row * 8
        for col in range(0, 8, 2):
            encoded.append((indices[start + col] << 4) | indices[start + col + 1])
    return bytes(encoded), reconstructed


def build_assets():
    canvas = prepare_canvas()
    tiles = split_tiles(canvas)
    groups, palettes = optimise_palettes(tiles)

    blank = bytes(32)
    tile_ids = {blank: 0}
    art_tiles = [blank]
    map_words = []
    preview_tiles = []
    for tile, group in zip(tiles, groups):
        encoded, reconstructed = encode_tile(tile, palettes[group])
        if encoded not in tile_ids:
            tile_ids[encoded] = len(art_tiles)
            art_tiles.append(encoded)
        map_words.append(tile_ids[encoded] | (group << 13))
        preview_tiles.append(reconstructed)

    if len(art_tiles) >= FONT_TILE:
        raise RuntimeError(f"Title uses {len(art_tiles)} tiles; maximum is {FONT_TILE - 1}")

    ART.write_bytes(b"".join(art_tiles))
    MAP.write_bytes(b"".join(struct.pack(">H", word) for word in map_words))
    for path, palette in zip(PALETTES, palettes):
        path.write_bytes(b"".join(struct.pack(">H", md_word(c)) for c in palette))

    preview = Image.new("RGBA", (WIDTH, HEIGHT))
    output = [(0, 0, 0, 0)] * (WIDTH * HEIGHT)
    for i, tile in enumerate(preview_tiles):
        tile_x = (i % (WIDTH // 8)) * 8
        tile_y = (i // (WIDTH // 8)) * 8
        for y in range(8):
            for x in range(8):
                output[(tile_y + y) * WIDTH + tile_x + x] = tile[y * 8 + x]
    preview.putdata(output)
    preview.resize((WIDTH * 3, HEIGHT * 3), Image.Resampling.NEAREST).save(PREVIEW)
    print(f"Full title: {len(art_tiles)} unique tiles, four palettes, native {WIDTH}x{HEIGHT}")


if __name__ == "__main__":
    build_assets()
