from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "resources/source/cream/forest/cream-forest-board-master.png"
ART_RAW = ROOT / "resources/art/art_nem/uncompressed/Board - Cream Forest.unc"
ART_NEM = ROOT / "resources/art/art_nem/compressed/Board - Cream Forest.nem"
UI_RAW = ROOT / "resources/art/art_nem/uncompressed/Board - Cream Forest UI.unc"
UI_NEM = ROOT / "resources/art/art_nem/compressed/Board - Cream Forest UI.nem"
MAP_RAW = ROOT / "resources/mappings/background/map_eni/uncompressed/Board - Cream Forest.map"
PREVIEW = ROOT / "resources/source/cream/forest/cream-forest-board-megadrive-preview.png"
REDUCED = ROOT / "resources/source/cream/forest/cream-forest-board-reduced.png"
NEMESIS = ROOT / "tools/windows/clownnemesis.exe"

PALETTE_FILES = [
    ROOT / "resources/palettes/line/new/Stage - Red and Yellow.pal",
    ROOT / "resources/palettes/line/new/Stage - Blue and Purple.pal",
    ROOT / "resources/palettes/line/original/Board - Grass.pal",
]

TILE_BASE = 0x000  # VRAM $0000, replacing the unused native stone-board art
TILE_COUNT = 116
SCREEN_W = 320
SCREEN_H = 224


def load_palette(path: Path) -> np.ndarray:
    raw = path.read_bytes()
    colours = []
    for offset in range(0, 32, 2):
        word = int.from_bytes(raw[offset : offset + 2], "big")
        red = (word & 0x000E) * 255 // 14
        green = ((word >> 4) & 0x000E) * 255 // 14
        blue = ((word >> 8) & 0x000E) * 255 // 14
        colours.append((red, green, blue))
    return np.asarray(colours, dtype=np.float32)


def prepare_source() -> np.ndarray:
    image = Image.open(SOURCE).convert("RGB")
    target_ratio = SCREEN_W / SCREEN_H
    source_ratio = image.width / image.height
    if source_ratio > target_ratio:
        crop_w = round(image.height * target_ratio)
        left = (image.width - crop_w) // 2
        image = image.crop((left, 0, left + crop_w, image.height))
    else:
        crop_h = round(image.width / target_ratio)
        top = (image.height - crop_h) // 2
        image = image.crop((0, top, image.width, top + crop_h))

    image = image.resize((160, 112), Image.Resampling.LANCZOS)
    image = image.resize((SCREEN_W, SCREEN_H), Image.Resampling.NEAREST)
    screen = np.asarray(image, dtype=np.float32)

    # The master illustration contains opaque flat-green playfields, so merely
    # brightening them cannot reveal any scenery. Reuse the central forest path
    # beneath both panels before applying the dark gameplay veil; the left copy
    # is mirrored to avoid an obvious duplicated strip.
    # Match the engine's exact 6 x 12 visible grids: 96 x 192 pixels, starting
    # at x=16/x=208 and y=16. This keeps every bean immediately inside the
    # frame instead of leaving decorative dead space around the playfields.
    panel_source = Image.fromarray(screen.astype(np.uint8), "RGB").crop((112, 16, 208, 208))
    panel_source = panel_source.resize((96, 192), Image.Resampling.NEAREST)
    panel_scene = np.asarray(panel_source, dtype=np.float32)
    screen[16:208, 16:112] = panel_scene[:, ::-1]
    screen[16:208, 208:304] = panel_scene

    # Keep the two playfields dark enough for the beans to remain readable,
    # but render the surrounding forest as a bright daytime clearing.  The
    # field veil reaches the top edge so falling/preview beans never appear
    # outside it, and remains translucent enough to show the forest beneath.
    # Shadow/highlight stays enabled for correct chain effects, so the forest
    # source is deliberately lifted before quantisation to remain daytime-bright.
    lit_screen = np.clip(screen * 1.55 + 18.0, 0, 255)
    playfield_mask = np.zeros((SCREEN_H, SCREEN_W), dtype=bool)
    playfield_mask[16:208, 16:112] = True
    playfield_mask[16:208, 208:304] = True
    lit_screen[playfield_mask] = np.clip(lit_screen[playfield_mask] * 0.68, 0, 255)

    # Crisp two-pixel black frames make both playfields readable against the
    # detailed forest without consuming extra VRAM tiles or covering the beans.
    for left, right in ((16, 111), (208, 303)):
        lit_screen[14:210, left - 2 : left] = 0
        lit_screen[14:210, right + 1 : right + 3] = 0
        lit_screen[14:16, left - 2 : right + 3] = 0
        lit_screen[208:210, left - 2 : right + 3] = 0
    image = Image.fromarray(lit_screen.astype(np.uint8), "RGB")
    image.save(REDUCED)
    return lit_screen


def make_source_tiles(screen: np.ndarray) -> np.ndarray:
    return np.stack(
        [
            screen[y : y + 8, x : x + 8].reshape(-1, 3)
            for y in range(0, SCREEN_H, 8)
            for x in range(0, SCREEN_W, 8)
        ]
    )


def cluster_tiles(tiles: np.ndarray) -> np.ndarray:
    vectors = tiles.reshape(len(tiles), -1)
    rng = np.random.default_rng(0xC0EA)
    centers = [vectors[rng.integers(len(vectors))]]
    nearest = np.sum((vectors - centers[0]) ** 2, axis=1)
    for _ in range(1, TILE_COUNT):
        total = float(nearest.sum())
        if total == 0:
            centers.append(vectors[len(centers) % len(vectors)])
        else:
            choice = rng.choice(len(vectors), p=nearest / total)
            centers.append(vectors[choice])
        distance = np.sum((vectors - centers[-1]) ** 2, axis=1)
        nearest = np.minimum(nearest, distance)

    centers = np.asarray(centers, dtype=np.float32)
    for _ in range(8):
        distance = np.sum((vectors[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        labels = np.argmin(distance, axis=1)
        for index in range(TILE_COUNT):
            members = vectors[labels == index]
            if len(members):
                centers[index] = members.mean(axis=0)
    return centers.reshape(TILE_COUNT, 64, 3)


def quantize_prototypes(centers: np.ndarray, palettes: np.ndarray):
    prototype_indices = []
    prototype_rgb = []
    prototype_palettes = []
    for center in centers:
        best_error = None
        best_indices = None
        best_rgb = None
        best_palette = 0
        for palette_id, palette in enumerate(palettes):
            distance = np.sum((center[:, None, :] - palette[None, 1:, :]) ** 2, axis=2)
            indices = np.argmin(distance, axis=1) + 1
            rgb = palette[indices]
            error = float(np.sum((center - rgb) ** 2))
            if best_error is None or error < best_error:
                best_error = error
                best_indices = indices.astype(np.uint8)
                best_rgb = rgb
                best_palette = palette_id
        prototype_indices.append(best_indices.reshape(8, 8))
        prototype_rgb.append(best_rgb.reshape(8, 8, 3))
        prototype_palettes.append(best_palette)
    return (
        np.asarray(prototype_indices, dtype=np.uint8),
        np.asarray(prototype_rgb, dtype=np.float32),
        np.asarray(prototype_palettes, dtype=np.uint16),
    )


def assign_tiles(tiles: np.ndarray, prototype_rgb: np.ndarray):
    variants = np.stack(
        [
            prototype_rgb,
            prototype_rgb[:, :, ::-1, :],
            prototype_rgb[:, ::-1, :, :],
            prototype_rgb[:, ::-1, ::-1, :],
        ],
        axis=1,
    )
    assignments = []
    for tile in tiles.reshape(-1, 8, 8, 3):
        error = np.sum((variants - tile[None, None, :, :, :]) ** 2, axis=(2, 3, 4))
        prototype, flip = np.unravel_index(np.argmin(error), error.shape)
        assignments.append((int(prototype), int(flip)))
    return assignments


def encode_art(patterns: np.ndarray) -> bytes:
    output = bytearray()
    for pattern in patterns:
        for row in pattern:
            for x in range(0, 8, 2):
                output.append((int(row[x]) << 4) | int(row[x + 1]))
    return bytes(output)


def build_ui_art() -> bytes:
    battle_font = (ROOT / "resources/art/art_sor/uncompressed/Font - Battle.unc").read_bytes()
    # STAGE followed by the stage-one digit, two 8x8 tiles per glyph.
    tile_ids = [0xA4, 0xA5, 0xA6, 0xA7, 0x80, 0x81, 0x8C, 0x8D, 0x88, 0x89, 0x6E, 0x6F]
    output = bytearray()
    for position, tile_id in enumerate(tile_ids):
        tile = battle_font[tile_id * 32 : (tile_id + 1) * 32]
        blue = position < 10
        for packed in tile:
            pixels = (packed >> 4, packed & 0xF)
            converted = []
            for pixel in pixels:
                if pixel == 0:
                    converted.append(0)
                elif pixel == 1:
                    converted.append(2 if blue else 9)
                else:
                    converted.append(4 if blue else 11)
            output.append((converted[0] << 4) | converted[1])
    return bytes(output)


def encode_map(assignments, palette_ids: np.ndarray) -> bytes:
    output = bytearray()
    rows = [assignments[y * 40 : (y + 1) * 40] for y in range(28)]
    # The VDP plane is 32 tiles tall while the visible image is 28. Mirror the
    # first four rows into the hidden tail so small negative landing scrolls
    # wrap into matching treetops instead of exposing the old grey ground.
    rows.extend(rows[0:4])
    for row in rows:
        for prototype, flip in row:
            hflip = 0x0800 if flip in (1, 3) else 0
            vflip = 0x1000 if flip in (2, 3) else 0
            word = 0x8000 | (int(palette_ids[prototype]) << 13) | vflip | hflip | TILE_BASE | prototype
            output.extend(word.to_bytes(2, "big"))
    return bytes(output)


def render_preview(patterns, palettes, palette_ids, assignments):
    canvas = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)
    for position, (prototype, flip) in enumerate(assignments):
        tile = palettes[palette_ids[prototype]][patterns[prototype]].astype(np.uint8)
        if flip in (1, 3):
            tile = tile[:, ::-1]
        if flip in (2, 3):
            tile = tile[::-1]
        y, x = divmod(position, 40)
        canvas[y * 8 : y * 8 + 8, x * 8 : x * 8 + 8] = tile
    Image.fromarray(canvas, "RGB").save(PREVIEW)


def main() -> None:
    screen = prepare_source()
    tiles = make_source_tiles(screen)
    palettes = np.stack([load_palette(path) for path in PALETTE_FILES])
    centers = cluster_tiles(tiles)
    patterns, prototype_rgb, palette_ids = quantize_prototypes(centers, palettes)
    assignments = assign_tiles(tiles, prototype_rgb)
    ART_RAW.write_bytes(encode_art(patterns))
    UI_RAW.write_bytes(build_ui_art())
    MAP_RAW.write_bytes(encode_map(assignments, palette_ids))
    render_preview(patterns, palettes, palette_ids, assignments)
    subprocess.run([str(NEMESIS), "-c", str(ART_RAW), str(ART_NEM)], check=True)
    subprocess.run([str(NEMESIS), "-c", str(UI_RAW), str(UI_NEM)], check=True)
    print(f"Forest art: {ART_RAW.stat().st_size} bytes / {TILE_COUNT} tiles")
    print(f"Forest UI: {UI_RAW.stat().st_size} bytes / 12 tiles")
    print(f"Forest map: {MAP_RAW.stat().st_size} bytes / 40x32 cells")
    print(f"Preview: {PREVIEW}")


if __name__ == "__main__":
    main()
