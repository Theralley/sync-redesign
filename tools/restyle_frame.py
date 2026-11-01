"""Restyle SYNC's frame: every button, the bars round the screen and their icons (plan phase R4).

Usage: python3 tools/restyle_frame.py CAR_APPCONSOLE_SWF OUT_SWF [--radius N] [--preview FOLDER]

Takes **your car's own** Apps\\AppConsole\\AppConsole.swf (from the drive log, in ~/.s2am). It
holds the art for the whole frame, and for every button on every screen: SYNC's button class
(SyncThemeButtonArt) tiles one of 76 strips across each button, chosen by the button's height
(30 to 120 px), its state and, when selected, its area. This replaces 135 of the file's 137
pictures with flat ones from restyle_art.py, at exactly their sizes:

- the 76 button strips: flat; a selected button tinted in its area's colour, a line on top;
- the four corner bars (status bar and area bar): flat, the area's line kept;
- the bar pieces between them (the clock, Info, Home, Settings): Ford's outline, flat inside,
  our icons; their pressed states a little lighter;
- the bar icons, the signal strength, the indicator lights and the dividers.

Left as they are: a JPEG with shared tables (id 93) and the CD picture. No code changes,
unless --radius N: the buttons' corner radius
(Ford's 3), changed in place in SyncThemeButtonArt as R3b changed the call list's numbers. SYNC
draws it before scaling each button, so on wide buttons a larger radius turns oval.

The file is SYNC's frame and loads at start-up. The result is checked tag by tag against the
car's file: only the named pictures (and, with --radius, that one class) may differ. A file
that is not the frame this was made for (other pictures or sizes) is refused. --preview FOLDER
gets Ford's pictures and ours side by side (Ford's artwork: keep it private).
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import restyle_art as art
import swf_bitmaps
from build_phone_history import class_actions, numbers

STATES = ("AVAILABLE", "PRESSED", "SELECTED", "PRESSEDSELECTED")
HEIGHTS = (30, 40, 45, 50, 60, 100, 120)  # SyncThemeButtonArt.availableBitmapFillHeights
BUTTON_CLASS = "__Packages.SyncThemeButtonArt"
FORD_RADIUS = 3

# The bars round the screen: id -> (size, area, line at the top)
BARS = {232: ((334, 48), 1, False), 236: ((334, 48), 2, False), 240: ((334, 48), 3, True), 245: ((334, 48), 4, True)}
# The bar pieces: id -> (size, pressed, our icon (name, centre x, centre y, size) where Ford's was)
PIECES = {
    249: ((252, 59), False, None),  # the clock's piece, at the top
    288: ((252, 59), False, None), 291: ((252, 59), True, None),
    296: ((126, 59), False, None), 298: ((126, 59), True, None),
    302: ((126, 59), False, None), 304: ((126, 59), True, None),
    346: ((68, 59), False, None), 348: ((68, 59), True, None),
    352: ((67, 59), False, None), 354: ((67, 59), True, None),
    328: ((90, 59), False, None), 330: ((90, 59), True, None),
    334: ((59, 59), False, None), 336: ((59, 59), True, None),
    340: ((58, 59), False, None), 343: ((58, 59), True, None),
    252: ((90, 59), False, ("settings", 31, 32.5, 26)), 254: ((90, 59), True, ("settings", 31, 32.5, 26)),
    260: ((90, 59), False, ("info", 61, 32.5, 26)), 271: ((90, 59), True, ("info", 61, 32.5, 26)),
    309: ((72, 59), False, ("home", 36, 32.5, 28)), 311: ((72, 59), True, ("home", 36, 32.5, 28)),
    323: ((72, 59), False, ("road", 36, 32, 26)), 325: ((72, 59), True, ("road", 36, 32, 26)),
}
# Icons alone: id -> (size, icon, colour, icon size)
ICONS = {
    103: ((23, 28), "person_voice", art.TEXT, 21), 127: ((23, 28), "person_voice", art.DIM, 21),
    121: ((50, 50), "back", art.TEXT, 34), 150: ((28, 20), "backspace", art.TEXT, 19),
    262: ((21, 35), "info", art.ACCENTS[1], 24), 265: ((19, 33), "info", art.TEXT, 24),
    268: ((19, 33), "info", art.QUIET, 24),
    287: ((38, 33), "home", art.QUIET, 28), 290: ((38, 33), "home", art.TEXT, 28),
    317: ((36, 33), "settings", art.TEXT, 27), 319: ((36, 33), "settings", art.QUIET, 27),
    339: ((50, 50), "road", art.QUIET, 30), 342: ((50, 50), "road", art.TEXT, 30),
}
SIGNAL = {275: 3, 278: 2, 281: 1, 284: 0}  # 21x18, Ford's four signal strengths
# Indicator lights: id -> (size, the pill (x0, y0, x1, y1), level); None for a dark socket
LIGHTS = {
    161: ((28, 20), (8, 7, 19, 12), 0.0), 179: ((28, 20), (8, 7, 19, 12), 0.0),
    163: ((25, 20), (8, 7, 17, 12), None), 181: ((25, 20), (8, 7, 17, 12), None),
    183: ((30, 24), (9, 9, 20, 14), 0.35), 185: ((30, 24), (9, 9, 20, 14), 0.7),
    165: ((30, 24), (9, 9, 20, 14), 1.0), 187: ((30, 24), (9, 9, 20, 14), 1.0),
    203: ((24, 36), (9, 7, 14, 28), 0.0), 205: ((26, 50), (10, 14, 15, 35), 1.0),
}
DIVIDERS = {156: (2, 49), 174: (2, 49), 295: (2, 53)}


def strip_names(body: bytes) -> dict[int, str]:
    """Picture id -> its exported name, for the button strips (AVAILABLE30 ... SELECTED120_4)."""
    names = {}
    for code, _, contents in swf_bitmaps.tags(body):
        if code == 56:  # ExportAssets
            q = 2
            for _ in range(struct.unpack_from("<H", contents)[0]):
                ident, end = struct.unpack_from("<H", contents, q)[0], contents.index(b"\0", q + 2)
                name = contents[q + 2:end].decode("latin1")
                if name.rstrip("_01234").rstrip("0123456789") in STATES:
                    names[ident] = name
                q = end + 1
    return names


def parse_strip(name: str) -> tuple[str, int, int | None]:
    """'PRESSEDSELECTED45_2' -> ('PRESSEDSELECTED', 45, 2); 'AVAILABLE30' -> ('AVAILABLE', 30, None)."""
    base, _, area = name.partition("_")
    state = base.rstrip("0123456789")
    return state, int(base[len(state):]), int(area) if area else None


def artwork(data: bytes) -> dict[int, Image.Image]:
    """Our pictures for the frame, by id, after checking it is the frame this was made for."""
    head, body = swf_bitmaps.unpack(data)
    found = swf_bitmaps.pictures(body)
    names = strip_names(body)
    if len(names) != 76 or sorted({parse_strip(n)[1] for n in names.values()}) != list(HEIGHTS):
        raise SystemExit("not the 76 button strips expected: this is not the frame this tool was made for")
    new = {}
    for ident, name in names.items():
        state, height, area = parse_strip(name)
        _, _, width, tall = found[ident]
        if tall != height + 2 or (area is None) != (state in ("AVAILABLE", "PRESSED")):
            raise SystemExit(f"strip {name} is {width}x{tall}: not the frame this tool was made for")
        new[ident] = art.strip(width, tall, state, area)
    expected = {i: v[0] for i, v in {**BARS, **PIECES, **ICONS, **LIGHTS}.items()}
    expected |= {i: (21, 18) for i in SIGNAL} | DIVIDERS
    for ident, size in expected.items():
        if ident not in found or tuple(found[ident][2:]) != size:
            raise SystemExit(f"picture {ident} is not the {size[0]}x{size[1]} picture expected: "
                             "this is not the frame this tool was made for")
    pictures = {code_id: swf_bitmaps.decode(found[code_id][0], contents)
                for code, _, contents in swf_bitmaps.tags(body) if code in (20, 35, 36)
                for code_id in [swf_bitmaps.picture_info(code, contents)[0]] if code_id in PIECES or code_id in DIVIDERS}
    for ident, (size, area, top) in BARS.items():
        new[ident] = art.bar(size, area, top)
    for ident, (size, pressed, icon) in PIECES.items():
        new[ident] = art.flatten(pictures[ident], pressed, icon)
    for ident, (size, name, colour, icon_size) in ICONS.items():
        new[ident] = art.icon(size, name, colour, icon_size)
    for ident, level in SIGNAL.items():
        new[ident] = art.signal((21, 18), level, 17)
    for ident, (size, box, level) in LIGHTS.items():
        new[ident] = art.socket(size, box) if level is None else art.light(size, box, level)
    for ident in DIVIDERS:
        new[ident] = art.recolour(pictures[ident], art.EDGE)
    return new


def change_radius(body: bytes, radius: int) -> bytes:
    """SyncThemeButtonArt.CORNER_RADIUS, changed in place (same length)."""
    found = swf_bitmaps.tags(body)
    index = class_actions(body, BUTTON_CLASS)
    code, header, contents = found[index]
    actions = bytearray(contents[2:])
    hits = [(v, o) for n, v, o in numbers(bytes(actions)) if n == "CORNER_RADIUS"]
    if len(hits) != 1 or hits[0][0] != FORD_RADIUS:
        raise SystemExit(f"CORNER_RADIUS is not {FORD_RADIUS} once: not the frame this was made for")
    struct.pack_into("<i", actions, hits[0][1], radius)
    if [v for n, v, _ in numbers(bytes(actions)) if n == "CORNER_RADIUS"] != [radius]:
        raise SystemExit("CORNER_RADIUS did not read back as written")
    found[index] = (code, header, contents[:2] + bytes(actions))
    return b"".join(h + c for _, h, c in found)


def check(old: bytes, new: bytes, pictures: set[int], radius: bool) -> None:
    """Tag by tag: only the named pictures, and with --radius the button class, differ."""
    (head, before), (head2, after) = swf_bitmaps.unpack(old), swf_bitmaps.unpack(new)
    a, b = swf_bitmaps.tags(before), swf_bitmaps.tags(after)
    if head != head2 or [t[0] for t in a] != [t[0] for t in b]:
        raise SystemExit("the header or the list of tags changed")
    allowed = {i for i, (code, _, c) in enumerate(a)
               if code in (20, 35, 36) and swf_bitmaps.picture_info(code, c)[0] in pictures}
    if radius:
        allowed.add(class_actions(before, BUTTON_CLASS))
    changed = {i for i, (x, y) in enumerate(zip(a, b)) if x[1:] != y[1:]}
    if changed - allowed:
        raise SystemExit(f"tags changed that should not have: {sorted(changed - allowed)}")


def preview(data: bytes, new: dict[int, Image.Image], folder: Path) -> None:
    """Ford's pictures (left) and ours (right), enlarged two times, on the screen's black."""
    body = swf_bitmaps.unpack(data)[1]
    ford = {swf_bitmaps.picture_info(code, c)[0]: swf_bitmaps.decode(code, c)
            for code, _, c in swf_bitmaps.tags(body) if code in (20, 35, 36)
            and swf_bitmaps.picture_info(code, c)[0] in new and swf_bitmaps.picture_info(code, c)[1] in (0, 5)}
    order = sorted(new, key=lambda i: (new[i].width < 10, i))
    rows = [order[k:k + 4] for k in range(0, len(order), 4)]
    scale, gap = 2, 8
    widest = max(image.width for image in new.values())  # the bars, 334 px
    height = sum(max(new[i].height for i in row) * scale + gap for row in rows)
    sheet = Image.new("RGB", (2 * (4 * (widest * scale + gap)) + 40, height + gap), (0, 0, 0))
    y = gap
    for row in rows:
        for side, source in enumerate((ford, new)):
            x = side * (4 * (widest * scale + gap) + 40)
            for ident in row:
                image = source[ident].convert("RGBA")
                if image.width < 10:  # strips: shown as a button 120 px wide
                    image = Image.new("RGBA", (120, image.height)).resize((120, image.height))
                    tile = source[ident].convert("RGBA")
                    for k in range(0, 120, tile.width):
                        image.paste(tile, (k, 0))
                big = image.resize((image.width * scale, image.height * scale), Image.NEAREST)
                back = Image.new("RGBA", big.size, (0, 0, 0, 255))
                back.alpha_composite(big)
                sheet.paste(back.convert("RGB"), (x, y))
                x += big.width + gap
        y += max(new[i].height for i in row) * scale + gap
    ImageDraw.Draw(sheet).line((sheet.width // 2, 0, sheet.width // 2, sheet.height), fill=(80, 80, 80))
    folder.mkdir(parents=True, exist_ok=True)
    sheet.save(folder / "frame-ford-vs-ours.png")
    for ident, image in new.items():
        image.save(folder / f"{ident}.png")


def main(argv: list[str]) -> None:
    radius = int(argv[argv.index("--radius") + 1]) if "--radius" in argv else None
    folder = Path(argv[argv.index("--preview") + 1]) if "--preview" in argv else None
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--radius",
                                                                                                    "--preview"))]
    if len(args) != 2 or (radius is not None and not 1 <= radius <= 12):
        raise SystemExit(__doc__)
    source, target = args
    data = Path(source).read_bytes()
    new = artwork(data)
    result = swf_bitmaps.replace(data, new)
    if radius is not None:
        head, body = swf_bitmaps.unpack(result)
        result = swf_bitmaps.pack(head, change_radius(body, radius))
    check(data, result, set(new), radius is not None)
    Path(target).write_bytes(result)
    if folder:
        preview(data, new, folder)
    print(f"{target}: {len(new)} pictures restyled" + (f", corner radius {radius}" if radius else "")
          + f"; everything else byte for byte; sha256 {hashlib.sha256(result).hexdigest()[:16]}, {len(result)} bytes")


if __name__ == "__main__":
    main(sys.argv[1:])
