"""Build the call history screen with our icons (plan phase R3a: pictures only, no code).

Usage: python3 tools/build_phone_history.py CAR_PHONEHISTORY_SWF OUT_SWF [PREVIEW_FOLDER]

Takes **your car's own** Phone\\PhoneHistory\\PhoneHistory.swf (from the drive log, in ~/.s2am)
and replaces eight of its pictures with icons from icons.py, at exactly their sizes: the
outgoing, incoming and missed call marks, the green dial handset, the scroll arrows and the two
small arrows. The screen's code, texts and layout stay byte for byte (swf_bitmaps.py checks
every tag). A file with other pictures than expected is refused: it is not the screen this
was made for. PREVIEW_FOLDER gets the eight new pictures, enlarged, to look at.
"""
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import icons
import swf_bitmaps

WHITE, GREEN = (245, 246, 248), (72, 190, 110)
# Ford's picture id -> (its width, height), our icon, the icon's size and line in pixels, colour
PICTURES = {
    30: ((30, 25), "chevron_up", 22, 2.5, WHITE),
    37: ((30, 25), "chevron_down", 22, 2.5, WHITE),
    44: ((30, 30), "call_out", 28, 2.5, WHITE),
    47: ((30, 30), "call_missed", 28, 2.5, WHITE),
    50: ((30, 30), "call_in", 28, 2.5, WHITE),
    56: ((6, 12), "chevron_right", 12, 1.6, WHITE),
    73: ((21, 28), "handset", 26, 2.5, GREEN),
    78: ((12, 18), "chevron_right", 18, 2.2, WHITE),
}
SCALE = 8  # drawn this much larger, then reduced, for smooth edges


def picture(name: str, size: tuple[int, int], icon: int, weight: float, colour) -> Image.Image:
    """The icon, centred in a transparent picture of exactly `size`."""
    side = max(size) * SCALE
    mask = Image.new("L", (side, side), 0)
    icons.draw(ImageDraw.Draw(mask), name, side / 2, side / 2, icon * SCALE, 255, round(weight * SCALE))
    mask = mask.resize((max(size), max(size)), Image.LANCZOS)
    left, top = (max(size) - size[0]) // 2, (max(size) - size[1]) // 2
    mask = mask.crop((left, top, left + size[0], top + size[1]))
    return Image.merge("RGBA", (*(Image.new("L", size, c) for c in colour), mask))


def main(source: str, target: str, preview=None) -> None:
    data = Path(source).read_bytes()
    found = swf_bitmaps.pictures(swf_bitmaps.unpack(data)[1])
    for ident, (size, *_) in PICTURES.items():
        if ident not in found or found[ident][2:] != size:
            raise SystemExit(f"picture {ident} is not the {size[0]}x{size[1]} picture expected: "
                             "this is not the call history screen this tool was made for")
    new = {ident: picture(name, size, icon, weight, colour)
           for ident, (size, name, icon, weight, colour) in PICTURES.items()}
    result = swf_bitmaps.replace(data, new)
    Path(target).write_bytes(result)
    if preview:
        folder = Path(preview)
        folder.mkdir(parents=True, exist_ok=True)
        for ident, image in new.items():
            backed = Image.new("RGBA", image.size, (30, 33, 40, 255))
            backed.alpha_composite(image)
            backed.resize((image.width * 6, image.height * 6), Image.NEAREST).save(folder / f"{ident}.png")
    print(f"{target}: {len(new)} pictures replaced, everything else byte for byte; "
          f"sha256 {hashlib.sha256(result).hexdigest()[:16]}, {len(result)} bytes")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
