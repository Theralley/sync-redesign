"""Make the "Night" colour theme (plan phase R1) from the car's own theme files.

Usage: python3 tools/make_theme.py CAR_THEMES_FOLDER OUTFOLDER
CAR_THEMES_FOLDER is the drive log's copy of \\8inchSkins\\Ford\\Sync\\Themes (in ~/.s2am).

Writes Theme.XML and yellow/green/red/blue.bmp for `s2am job theme --from OUTFOLDER`:
- Theme.XML: the car's own file with only the four areas' button and dialog colours changed.
- The gradients: a thinner, calmer glow in the new accent colours, drawn into exactly the
  original format (the car's own 70-byte header, 800x240, 16-bit RGB565, bottom-up), so
  every file keeps its size.
Ford's files never go into this repository: the output is built from your car's copy.
"""
import re
import struct
import sys
from pathlib import Path

# area -> (gradient file, accent colour); TopLeft phone, TopRight navigation, BottomLeft media,
# BottomRight climate, the order of the AppType lines after System in Theme.XML
NIGHT = [("yellow.bmp", (214, 160, 72)), ("green.bmp", (72, 190, 150)), ("red.bmp", (220, 76, 84)),
         ("blue.bmp", (64, 150, 255))]
GLOW = (0.42, 150)  # brightness at the edge, and how many pixels the glow reaches
ACTIVE = re.compile(rb"^([ \t]*<AppType )btnColor=\"0x[0-9a-fA-F]{6}\" dialogColor=\"0x[0-9a-fA-F]{6}\"",
                    re.MULTILINE)


def hex_color(rgb, scale=1.0):
    return "0x%02X%02X%02X" % tuple(min(255, round(c * scale)) for c in rgb)


def theme_xml(original: bytes) -> bytes:
    lines = ACTIVE.findall(original)
    if len(lines) != 5:
        raise SystemExit(f"expected 5 AppType lines (System and four areas), found {len(lines)}")
    count = [0]

    def recolour(match):
        count[0] += 1
        if count[0] == 1:  # System stays as it is
            return match.group(0)
        accent = NIGHT[count[0] - 2][1]
        return match.group(1) + f'btnColor="{hex_color(accent)}" dialogColor="{hex_color(accent, 0.72)}"'.encode()
    return ACTIVE.sub(recolour, original)


def gradient(original: bytes, accent) -> bytes:
    offset, header, width, height, _planes, bits, compression = struct.unpack_from("<IIiiHHI", original, 10)
    masks = struct.unpack_from("<III", original, 54)
    if (offset, header, width, height, bits, compression, masks) != (70, 56, 800, 240, 16, 3, (0xF800, 0x7E0, 0x1F)):
        raise SystemExit("the car's gradient is not the 800x240 RGB565 BMP this tool knows")

    def brightness(row):  # rows are stored bottom-up
        pixel = struct.unpack_from("<H", original, offset + row * width * 2 + width)[0]
        return (pixel >> 11) + ((pixel >> 5) & 63) // 2 + (pixel & 31)
    glow_at_top = brightness(height - 1) > brightness(0)
    edge, reach = GLOW
    pixels = bytearray()
    for row in range(height):  # bottom-up
        distance = (height - 1 - row) if glow_at_top else row  # from the bright edge
        level = edge * max(0.0, 1 - distance / reach) ** 2
        r, g, b = (round(c * level) for c in accent)
        value = (r >> 3) << 11 | (g >> 2) << 5 | (b >> 3)
        pixels += struct.pack("<H", value) * width
    built = original[:offset] + bytes(pixels) + original[offset + len(pixels):]
    if len(built) != len(original):
        raise SystemExit("size changed; nothing written")
    return built


def main(car: str, out: str) -> None:
    car_folder, out_folder = Path(car), Path(out)
    out_folder.mkdir(parents=True, exist_ok=True)
    (out_folder / "Theme.XML").write_bytes(theme_xml((car_folder / "Theme.XML").read_bytes()))
    for name, accent in NIGHT:
        (out_folder / name).write_bytes(gradient((car_folder / name).read_bytes(), accent))
    print(f"Night theme in {out_folder}: Theme.XML and {len(NIGHT)} gradients, sizes unchanged")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
