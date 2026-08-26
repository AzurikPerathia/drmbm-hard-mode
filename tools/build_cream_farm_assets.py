"""Build the v0.3 Cream farm backgrounds for Mega Drive story screens.

The generated master is converted twice:

* a one-palette 320x224 version for Cream's dialogue scene;
* the same palette for the opponent announcement, leaving the other palette
  lines available for the two character portraits and stage label.

Both variants share the same composition and use native 4bpp tiles/maps.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "resources/source/cream/farm"
ART_DIR = ROOT / "resources/art/art_nem/uncompressed"
MAP_DIR = ROOT / "resources/mappings/background/map_eni/uncompressed"
PAL_DIR = ROOT / "resources/palettes/line/new"
ENIGMA = ROOT / "tools/windows/enicmp.exe"

MASTER_PATH = SOURCE_DIR / "cream-farm-master.png"
SCREEN_SIZE = (320, 224)
TILE_SIZE = 8
MAX_TILES = 0x6000 // 32  # VRAM $2000-$7FFF; Cream starts at $8000.
ANNOUNCEMENT_X_OFFSET_TILES = 15  # The native screen scrolls Plane B by -120 px.


def genesis_channel(value: int) -> int:
    """Snap an 8-bit channel to the Mega Drive's eight useful intensities."""

    return max(0, min(14, round(value / 255 * 7) * 2))


def snap_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(genesis_channel(component) * 255 // 14 for component in color)


def prepare_master() -> Image.Image:
    source = Image.open(MASTER_PATH).convert("RGB")
    target_ratio = SCREEN_SIZE[0] / SCREEN_SIZE[1]
    source_ratio = source.width / source.height
    if source_ratio < target_ratio:
        crop_height = round(source.width / target_ratio)
        top = max(0, (source.height - crop_height) // 2 - 8)
        source = source.crop((0, top, source.width, top + crop_height))
    elif source_ratio > target_ratio:
        crop_width = round(source.height * target_ratio)
        left = (source.width - crop_width) // 2
        source = source.crop((left, 0, left + crop_width, source.height))

    # Work at quarter resolution before the final nearest-neighbour enlargement.
    # This removes high-frequency AI detail and produces stable 4x4 pixel
    # clusters that survive palette reduction and Nemesis compression cleanly.
    source = source.resize((80, 56), Image.Resampling.LANCZOS)
    return source.resize(SCREEN_SIZE, Image.Resampling.NEAREST)


def quantized_palette(sample: Image.Image, colors: int = 15) -> list[tuple[int, int, int]]:
    quantized = sample.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    raw = quantized.getpalette()[: colors * 3]
    palette: list[tuple[int, int, int]] = [(0, 0, 0)]  # Entry zero remains unused.
    for offset in range(0, len(raw), 3):
        color = snap_color(tuple(raw[offset : offset + 3]))
        if color not in palette:
            palette.append(color)
    while len(palette) < 16:
        palette.append(palette[-1])
    return palette[:16]


def tile_rgb(image: Image.Image, tile_x: int, tile_y: int) -> list[tuple[int, int, int]]:
    pixels = image.load()
    return [
        pixels[tile_x * TILE_SIZE + x, tile_y * TILE_SIZE + y]
        for y in range(TILE_SIZE)
        for x in range(TILE_SIZE)
    ]


def remap_tile(
    colors: list[tuple[int, int, int]],
    palettes: list[list[tuple[int, int, int]]],
) -> tuple[int, bytes]:
    best_error: int | None = None
    best_palette = 0
    best_indices: bytes | None = None
    for palette_id, palette in enumerate(palettes):
        indices = bytearray()
        error = 0
        for color in colors:
            index = min(
                range(1, 16),
                key=lambda candidate: sum(
                    (color[channel] - palette[candidate][channel]) ** 2
                    for channel in range(3)
                ),
            )
            indices.append(index)
            error += sum(
                (color[channel] - palette[index][channel]) ** 2
                for channel in range(3)
            )
        if best_error is None or error < best_error:
            best_error = error
            best_palette = palette_id
            best_indices = bytes(indices)
    assert best_indices is not None
    return best_palette, best_indices


def flip_indices(indices: bytes, horizontal: bool, vertical: bool) -> bytes:
    rows = [list(indices[y * 8 : y * 8 + 8]) for y in range(8)]
    if horizontal:
        rows = [list(reversed(row)) for row in rows]
    if vertical:
        rows.reverse()
    return bytes(pixel for row in rows for pixel in row)


def pack_tile(indices: bytes) -> bytes:
    output = bytearray()
    for offset in range(0, 64, 2):
        output.append((indices[offset] << 4) | indices[offset + 1])
    return bytes(output)


@dataclass
class NativeBackground:
    art: bytes
    mapping: list[int]
    palettes: list[list[tuple[int, int, int]]]
    width_tiles: int
    height_tiles: int


def convert_background(image: Image.Image, palettes: list[list[tuple[int, int, int]]]) -> NativeBackground:
    tile_pool: list[bytes] = []
    lookup: dict[bytes, int] = {}
    mapping: list[int] = []
    width_tiles = image.width // TILE_SIZE
    height_tiles = image.height // TILE_SIZE

    for tile_y in range(height_tiles):
        for tile_x in range(width_tiles):
            palette_id, indices = remap_tile(tile_rgb(image, tile_x, tile_y), palettes)
            tile_word = lookup.get(indices)
            if tile_word is None:
                tile_id = len(tile_pool)
                tile_pool.append(indices)
                # Do not encode horizontal/vertical attributes in custom Enigma
                # streams.  The game's older decoder corrupts maps whose header
                # advertises those optional attribute bits.
                lookup.setdefault(indices, tile_id)
                tile_word = tile_id
            mapping.append(tile_word | (palette_id << 13))

    if len(tile_pool) > MAX_TILES:
        raise RuntimeError(
            f"Cream farm needs {len(tile_pool)} tiles, exceeding the {MAX_TILES}-tile VRAM window"
        )
    return NativeBackground(
        art=b"".join(pack_tile(tile) for tile in tile_pool),
        mapping=mapping,
        palettes=palettes,
        width_tiles=width_tiles,
        height_tiles=height_tiles,
    )


def write_palette(palette: list[tuple[int, int, int]], filename: str) -> None:
    output = bytearray()
    for red, green, blue in palette:
        value = (genesis_channel(blue) << 8) | (genesis_channel(green) << 4) | genesis_channel(red)
        output.extend(value.to_bytes(2, "big"))
    (PAL_DIR / filename).write_bytes(output)


def write_map(words: list[int], filename: str) -> None:
    source = MAP_DIR / filename
    source.write_bytes(
        b"".join((word & 0xFFFF).to_bytes(2, "big") for word in words)
    )
    if ENIGMA.exists():
        compressed = Path(str(source).replace("uncompressed", "compressed")).with_suffix(".eni")
        compressed.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(ENIGMA), str(source), str(compressed)], check=True)


def render_preview(background: NativeBackground, output_path: Path) -> None:
    tiles = [background.art[offset : offset + 32] for offset in range(0, len(background.art), 32)]
    output = Image.new("RGB", (background.width_tiles * 8, background.height_tiles * 8))
    pixels = output.load()
    for map_index, word in enumerate(background.mapping):
        tile_id = word & 0x7FF
        palette = background.palettes[(word >> 13) & 3]
        tile = tiles[tile_id]
        horizontal = bool(word & 0x0800)
        vertical = bool(word & 0x1000)
        tile_x = map_index % background.width_tiles
        tile_y = map_index // background.width_tiles
        unpacked = [nibble for value in tile for nibble in (value >> 4, value & 15)]
        for y in range(8):
            for x in range(8):
                source_x = 7 - x if horizontal else x
                source_y = 7 - y if vertical else y
                pixels[tile_x * 8 + x, tile_y * 8 + y] = palette[unpacked[source_y * 8 + source_x]]
    output.save(output_path)


def announcement_plane_map(viewport_map: list[int]) -> list[int]:
    output: list[int] = []
    for tile_y in range(32):
        source_y = tile_y % 28
        for tile_x in range(64):
            source_x = (tile_x - ANNOUNCEMENT_X_OFFSET_TILES) % 40
            # Palette selection is supplied through EniDec's base tile word,
            # keeping the compressed map itself free of optional attributes.
            output.append(viewport_map[source_y * 40 + source_x])
    return output


def sunset_palette(palette: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    output = [(0, 0, 0)]
    for red, green, blue in palette[1:]:
        output.append(
            snap_color(
                (
                    min(255, round(red * 0.78 + 46)),
                    min(255, round(green * 0.58 + 20)),
                    min(255, round(blue * 0.48 + 42)),
                )
            )
        )
    return output


def build_opponent_screen_art(
    image: Image.Image, palette: list[tuple[int, int, int]]
) -> tuple[bytes, Image.Image]:
    """Replace the native 13x6 wall block without enlarging its RAM map."""

    patch = image.crop((0, 0, 320, 168)).resize((104, 48), Image.Resampling.NEAREST)
    art = bytearray()
    preview = Image.new("RGB", patch.size)
    preview_pixels = preview.load()
    for tile_y in range(6):
        for tile_x in range(13):
            _, indices = remap_tile(tile_rgb(patch, tile_x, tile_y), [palette])
            art.extend(pack_tile(indices))
            for y in range(8):
                for x in range(8):
                    preview_pixels[tile_x * 8 + x, tile_y * 8 + y] = palette[indices[y * 8 + x]]

    native = (ART_DIR / "Next Opponent.unc").read_bytes()
    if len(native) < 78 * 32:
        raise RuntimeError("Native opponent-screen art is incomplete")
    return bytes(art) + native[78 * 32 :], preview


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    image = prepare_master()
    image.save(SOURCE_DIR / "cream-farm-cropped.png")

    shared_palette = quantized_palette(image, colors=12)
    dialogue = convert_background(image, [shared_palette])
    (ART_DIR / "Cutscene - Cream Farm.unc").write_bytes(dialogue.art)
    write_map(dialogue.mapping, "Cutscene - Cream Farm.map")
    write_palette(shared_palette, "Cutscene - Cream Farm.pal")
    write_palette(sunset_palette(shared_palette), "Cutscene - Cream Farm (Sunset).pal")
    render_preview(dialogue, SOURCE_DIR / "cream-farm-dialogue-preview.png")

    announcement_art, announcement_patch = build_opponent_screen_art(image, shared_palette)
    (ART_DIR / "Next Opponent - Cream Farm.unc").write_bytes(announcement_art)
    write_palette(shared_palette, "Next Opponent - Cream Farm.pal")
    announcement_preview = Image.new("RGB", SCREEN_SIZE)
    for y in range(0, SCREEN_SIZE[1], announcement_patch.height):
        for x in range(0, SCREEN_SIZE[0], announcement_patch.width):
            announcement_preview.paste(announcement_patch, (x, y))
    announcement_preview.save(SOURCE_DIR / "cream-farm-announcement-preview.png")

    print(
        "Cream farm built: "
        f"dialogue={len(dialogue.art) // 32} tiles, "
        f"announcement={len(announcement_art) // 32} native-screen tiles"
    )


if __name__ == "__main__":
    main()
