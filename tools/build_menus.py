"""Flatten the glossy side menus of Settings (Menu.swf) and Info (Info.swf) (frame v2).

Usage: python3 tools/build_menus.py CAR_APPS_FOLDER OUT_FOLDER [--preview DIR]

Takes **your car's own** Menu\\Menu.swf and Info\\Info.swf (from the drive log, in ~/.s2am) and
writes Menu/Menu.swf and Info/Info.swf under OUT_FOLDER. build_frame.py runs this as one of its
steps; alone it does the menus only.

The column buttons in both files are the apps' own 150x50 glass pictures (a highlight row on
top, a gradient below), stretched by a clipped bitmap fill and the skin's scale to exactly
150x50 on the screen, drawn above the button class's strip; behind the column lies a 153x306
panel picture. Each is replaced at its size (restyle_art.menu_card, restyle_art.panel):
available a flat card with a 2 px gap on top, pressed a step lighter, Info's selected pictures
the card with a 3 px line down the left edge in the system colour, the panel the background.
Menu.swf has no selected picture: its SELECTED frame removes the glass and SYNC tiles the
shared SELECTED strip from AppConsole instead. Icons, labels and the outline SYNC draws round
every button are untouched (make_theme.py --borderless --palette v2 gives the outline the
strip's colour).

The result is checked tag by tag against the car's file: only the named pictures differ, each
read back at its size (swf_bitmaps). A file that is not the menu this was made for (other
pictures or sizes) is refused. --preview DIR gets Ford's pictures and ours side by side (Ford's
artwork: keep DIR private).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from PIL import Image

import restyle_art as art
import swf_bitmaps

GLASS, PANEL = (150, 50), (153, 306)
# file -> (Apps-relative path, {picture id: state})
MENUS = {
    "Menu": ("Menu/Menu.swf", {11: "available", 35: "available", 24: "available",
                               13: "pressed", 37: "pressed", 26: "pressed", 4: "panel"}),
    "Info": ("Info/Info.swf", {6: "available", 19: "available", 47: "available",
                               8: "pressed", 21: "pressed", 49: "pressed",
                               10: "selected", 23: "selected", 51: "selected", 1: "panel"}),
}


def artwork(data: bytes, wanted: dict[int, str]) -> dict[int, Image.Image]:
    """Our pictures by id, after checking this is the menu they were made for."""
    found = swf_bitmaps.pictures(swf_bitmaps.unpack(data)[1])
    new = {}
    for ident, state in wanted.items():
        size = PANEL if state == "panel" else GLASS
        if ident not in found or tuple(found[ident][2:]) != size:
            raise SystemExit(f"picture {ident} is not the {size[0]}x{size[1]} picture expected: "
                             "this is not the menu this tool was made for")
        new[ident] = art.panel(size) if state == "panel" else art.menu_card(size, state, found[ident][0] == swf_bitmaps.LOSSLESS2)
    return new


def check(old: bytes, new: bytes, pictures: set[int]) -> None:
    """Tag by tag: only the named pictures differ."""
    (head, before), (head2, after) = swf_bitmaps.unpack(old), swf_bitmaps.unpack(new)
    a, b = swf_bitmaps.tags(before), swf_bitmaps.tags(after)
    if head != head2 or [t[0] for t in a] != [t[0] for t in b]:
        raise SystemExit("the header or the list of tags changed")
    allowed = {i for i, (code, _, c) in enumerate(a)
               if code in (20, 36) and swf_bitmaps.picture_info(code, c)[0] in pictures}
    changed = {i for i, (x, y) in enumerate(zip(a, b)) if x[1:] != y[1:]}
    if changed - allowed:
        raise SystemExit(f"tags changed that should not have: {sorted(changed - allowed)}")


def build(data: bytes, name: str) -> tuple[bytes, dict[int, Image.Image]]:
    """(the flattened file, our pictures) for Menu or Info."""
    new = artwork(data, MENUS[name][1])
    result = swf_bitmaps.replace(data, new)
    check(data, result, set(new))
    if len(result) == len(data):
        raise SystemExit(f"{name}: the result is as long as the car's file; s2am would refuse it (nothing written)")
    return result, new


def preview(data: bytes, new: dict[int, Image.Image], folder: Path, name: str) -> None:
    """Ford's pictures (left) and ours (right), two times, on the background."""
    body = swf_bitmaps.unpack(data)[1]
    ford = {swf_bitmaps.picture_info(code, c)[0]: swf_bitmaps.decode(code, c)
            for code, _, c in swf_bitmaps.tags(body) if code in (20, 36) and swf_bitmaps.picture_info(code, c)[0] in new}
    order = sorted(new, key=lambda i: (new[i].height, i))
    scale, gap = 2, 8
    column = max(image.width for image in new.values()) * scale + gap
    height = sum(new[i].height * scale + gap for i in order) + gap
    sheet = Image.new("RGBA", (2 * column + 40, height), (*art.BACKGROUND, 255))
    y = gap
    for ident in order:
        for side, source in enumerate((ford, new)):
            big = source[ident].convert("RGBA").resize((new[ident].width * scale, new[ident].height * scale), Image.NEAREST)
            sheet.alpha_composite(big, (side * (column + 40), y))
        y += new[ident].height * scale + gap
    folder.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(folder / f"{name}-ford-vs-ours.png")


def main(argv: list[str]) -> None:
    folder = Path(argv[argv.index("--preview") + 1]) if "--preview" in argv else None
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--preview")]
    if len(args) != 2 or any(a.startswith("--") and a != "--preview" for a in argv):
        raise SystemExit(__doc__)
    apps, out = Path(args[0]), Path(args[1])
    art.use("v2")
    for name, (relative, _) in MENUS.items():
        data = (apps / relative).read_bytes()
        result, new = build(data, name)
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result)
        if folder:
            preview(data, new, folder, name)
        print(f"{target}: {len(new)} pictures flat; everything else byte for byte; "
              f"sha256 {hashlib.sha256(result).hexdigest()[:16]}, {len(result)} bytes")


if __name__ == "__main__":
    main(sys.argv[1:])
