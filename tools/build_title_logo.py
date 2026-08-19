#!/usr/bin/env python3
"""Build a separate New Story logo without replacing the original title art."""

from pathlib import Path
import struct

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "resources/source/title/Mean Bean Machine - New Story.png"
ART = ROOT / "resources/art/art_nem/uncompressed/Title - New Story Logo.unc"
MAP = ROOT / "resources/mappings/background/map_eni/uncompressed/Title - New Story Logo.map"
PREVIEW = ROOT / "resources/source/title/Mean Bean Machine - New Story - Mega Drive preview.png"
PALETTE_PATHS = [
    ROOT / "resources/palettes/line/new/Title - Colors 1.pal",
    ROOT / "resources/palettes/line/new/Title - Colors 2.pal",
    ROOT / "resources/palettes/line/new/Title - Colors 3.pal",
]

WIDTH = 192
HEIGHT = 160
LOGO_WIDTH = 152
LOGO_HEIGHT = 88
FIRST_TILE = 0x4B8       # VRAM $9700, immediately after the original title art.
MAX_TILES = 0x5C0 - FIRST_TILE  # Stop before the h-scroll table at VRAM $B800.


def decode_palette(path):
    data = path.read_bytes()
    colours = []
    for offset in range(0, 32, 2):
        word = struct.unpack(">H", data[offset:offset + 2])[0]
        colours.append(
            (((word & 0xE) >> 1) * 33, (((word >> 4) & 0xE) >> 1) * 33, (((word >> 8) & 0xE) >> 1) * 33)
        )
    return colours


def distance(a, b):
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return 2 * dr * dr + 4 * dg * dg + db * db


def prepare_image():
    source = Image.open(SOURCE).convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox:
        source = source.crop(bbox)
    scale = min(LOGO_WIDTH / source.width, LOGO_HEIGHT / source.height)
    size = (round(source.width * scale), round(source.height * scale))
    source = source.resize(size, Image.Resampling.LANCZOS)
    source = ImageEnhance.Contrast(source).enhance(1.12)
    source = ImageEnhance.Color(source).enhance(1.12)
    source = source.filter(ImageFilter.UnsharpMask(radius=0.65, percent=125, threshold=2))
    canvas = Image.new("RGBA", (WIDTH, HEIGHT))
    canvas.alpha_composite(source, ((WIDTH - size[0]) // 2, 2))

    font = ImageFont.load_default()
    draw = ImageDraw.Draw(canvas)
    white = (231, 231, 231, 255)

    def centred(text, y):
        box = draw.textbbox((0, 0), text, font=font)
        x = (WIDTH - (box[2] - box[0])) // 2
        draw.text((x, y), text, font=font, fill=white)
        draw.text((x + 1, y), text, font=font, fill=white)

    # A doubled nearest-neighbour line makes the main prompt unmistakable.
    prompt = Image.new("RGBA", (96, 12))
    prompt_draw = ImageDraw.Draw(prompt)
    prompt_box = prompt_draw.textbbox((0, 0), "PRESS START", font=font)
    prompt_x = (96 - (prompt_box[2] - prompt_box[0])) // 2
    prompt_draw.text((prompt_x, 0), "PRESS START", font=font, fill=white)
    prompt = prompt.resize((192, 24), Image.Resampling.NEAREST)
    # One extra output pixel gives a medium weight: thicker than the first
    # version, but much lighter than doubling a source pixel before scaling.
    prompt_bold = Image.new("RGBA", prompt.size)
    prompt_bold.alpha_composite(prompt)
    prompt_bold.alpha_composite(prompt, (1, 0))
    prompt = prompt_bold
    canvas.alpha_composite(prompt, (0, 111))
    centred("AZURIK PERATHIA - 2026", 137)
    centred("VERSION 0.2", 149)
    return canvas


def encode_tile(pixels, palette):
    indices = []
    rebuilt = []
    error = 0
    for r, g, b, a in pixels:
        if a < 64:
            index = 0
        else:
            index = min(range(1, 16), key=lambda i: distance((r, g, b), palette[i]))
            error += distance((r, g, b), palette[index])
        indices.append(index)
        rebuilt.append(palette[index] + ((0 if index == 0 else 255),))
    encoded = bytearray()
    for row in range(8):
        for col in range(0, 8, 2):
            pos = row * 8 + col
            encoded.append((indices[pos] << 4) | indices[pos + 1])
    return bytes(encoded), rebuilt, error


def build_assets():
    image = prepare_image()
    source_pixels = list(image.getdata())
    palettes = [decode_palette(path) for path in PALETTE_PATHS]
    unique = {bytes(32): 0}
    art_tiles = [bytes(32)]
    words = []
    preview_tiles = []

    for tile_y in range(HEIGHT // 8):
        for tile_x in range(WIDTH // 8):
            tile = []
            for y in range(8):
                start = (tile_y * 8 + y) * WIDTH + tile_x * 8
                tile.extend(source_pixels[start:start + 8])
            candidates = [encode_tile(tile, palette) for palette in palettes]
            group = min(range(len(candidates)), key=lambda i: candidates[i][2])
            encoded, rebuilt, _ = candidates[group]
            if encoded not in unique:
                unique[encoded] = len(art_tiles)
                art_tiles.append(encoded)
            words.append(0x8000 | FIRST_TILE + unique[encoded] | (group << 13))
            preview_tiles.append(rebuilt)

    if len(art_tiles) > MAX_TILES:
        raise RuntimeError(f"Logo requires {len(art_tiles)} tiles; available VRAM allows {MAX_TILES}")

    ART.parent.mkdir(parents=True, exist_ok=True)
    MAP.parent.mkdir(parents=True, exist_ok=True)
    ART.write_bytes(b"".join(art_tiles))
    MAP.write_bytes(b"".join(struct.pack(">H", word) for word in words))

    preview = Image.new("RGBA", (WIDTH, HEIGHT))
    output = [(0, 0, 0, 0)] * (WIDTH * HEIGHT)
    for i, tile in enumerate(preview_tiles):
        tile_x = (i % (WIDTH // 8)) * 8
        tile_y = (i // (WIDTH // 8)) * 8
        for y in range(8):
            for x in range(8):
                output[(tile_y + y) * WIDTH + tile_x + x] = tile[y * 8 + x]
    preview.putdata(output)
    preview.resize((WIDTH * 4, HEIGHT * 4), Image.Resampling.NEAREST).save(PREVIEW)
    print(f"Separate title logo: {len(art_tiles)} tiles of {MAX_TILES} available")


if __name__ == "__main__":
    build_assets()
