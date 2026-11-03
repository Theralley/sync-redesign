"""Build frame v2: SYNC's bars and corners flat, black and on one grid (the sixth visit).

Usage: python3 tools/build_frame.py CAR_APPS_FOLDER OUT_FOLDER [--preview DIR]

CAR_APPS_FOLDER is the drive log's copy of \\8inchSkins\\Ford\\Sync\\Apps (in ~/.s2am), read only.
Every frame-side file of the visit is written under OUT_FOLDER at its Apps-relative path:
AppConsole/AppConsole.swf and AppConsole/MenuConsoleObject.swf, Phone/PhoneConsoleObject.swf,
Nav/NavConsoleObject.swf, Media/MediaConsoleObject.swf and Media/Media.swf,
Climate/ClimateConsoleObject.swf, Menu/Menu.swf and Info/Info.swf (build_menus.py), and, when
the log's Themes folder sits beside Apps, Themes/ (make_theme.py --borderless --palette v2
--no-glow: the outline round every button in the strips' own colour, black area glows).

What changes, all in place, nothing recompiled (the Ford code that decides each point is named
by class and line in the comments; it stays Ford's):

AppConsole.swf (a start-up file). First restyle_frame's artwork in the "v2" palette: the 76
button strips in "chips22" (available (22,24,30), pressed (34,37,45), the selected mixes on that
base, so a button shows on a Home card), icons, lights, dividers, the hidden launch variants
black. Then the frame's own pictures (restyle_art): the four corner tabs 232/236/240/245 black
with no line; the clock's piece 249 black to the bar's edge; the launch pieces Info 260/271,
Home 309/311, Settings 252/254 transparent above the bar, black in it, our icon grey when
available and white when selected, centred in its cell (Info 280-360, Home 364-436, Settings
440-520, y 456.5), the selected one with a 3 px line along the bar's top edge the cell's width
(Info/Settings system grey, Home white); Ford's Info icon overlays 268/265 transparent (the icon
lives in the pieces now, the only way its colour can follow frame 1/2) and the alert overlay 262
(ACUpstream.SetAlertPendingIndicator) our icon in the phone accent. Three placements move
(swf_place): iconHome 362 -> 364 (centre 400), the alert overlay onto the piece's icon, and the
1 px separator Ford hid under its slanted pieces off the screen. There is no pressed picture:
the launch buttons are PlainButtons with an available and a selected frame only.

The console objects (start-up files too): placements only. The clock field centred on 400; the
phone, street and climate texts moved so phone (x 16) / clock / street (right edge 784) share
one baseline (the car's device font puts it 0.714 em below the field's top) and "Klimat" shares
the media text's; the heading letter and needle of the nav console off the stage; the media
source icons to x 16 with the texts after them. And so that Home shows only the clock and the
three launch buttons (its cards carry the four names):
- P1: the phone console's home-only clip (its one text is the word "Telefon",
  PhoneConsoleObject.OnAppConsoleStateChanged) off the stage; calls, status and timer are the
  tab view's and untouched;
- N3: in NavConsoleObject.SetConsoleView the Home branch's `compSystemStatus._visible = true`
  becomes false (one byte in the class; swf_actions finds it by the instructions round it);
- C1: the climate console's home-only clip (the word "Klimat") off the stage;
- M1: MediaConsoleStrings' Entertainment label (shown in the media corner on Home only) blanked:
  its resource key altered by one character so the lookup misses, its default "" (13 bytes
  shorter), both in the class's constant pool, in MediaConsoleObject.swf and in Media.swf, which
  carries an identical copy of the class (`if (!_global.MediaConsoleStrings)`: whichever loads
  first wins).

Every output must differ in length from the car's file: s2am refuses a start-up file as long as
Ford's, because on the car a copy is checked by its size alone and a failed copy must not pass
as a success. Where nothing else changes a file's length (the clock, phone and nav consoles)
one moved placement's matrix is re-encoded one field wider with the same values (GROW); the
build refuses to write a result as long as its source.

Checks, every file: it must be the one this tool was made for (picture sizes, Ford's placement
values, the strings and the push it expects); the result is compared tag by tag with the car's
file and only the named tags may differ; every picture (swf_bitmaps), every placement
(swf_place) and every patched byte is read back. --preview DIR gets Ford's frame and menu
pictures beside ours (Ford's artwork: keep DIR private). Keep OUT_FOLDER private too.
"""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

from PIL import Image

import build_menus
import make_theme
import restyle_art as art
import restyle_frame
import swf_actions
import swf_bitmaps
import swf_place
from build_phone_history import class_actions

PALETTE = "v2"
OFF_STAGE = -2000  # twips: a clip parked above the screen (y -100)
FILES = {"AppConsole": "AppConsole/AppConsole.swf", "MenuConsoleObject": "AppConsole/MenuConsoleObject.swf",
         "PhoneConsoleObject": "Phone/PhoneConsoleObject.swf", "NavConsoleObject": "Nav/NavConsoleObject.swf",
         "MediaConsoleObject": "Media/MediaConsoleObject.swf", "ClimateConsoleObject": "Climate/ClimateConsoleObject.swf",
         "Media": "Media/Media.swf"}

# The frame's pictures in AppConsole: id -> size
TABS = {232: (334, 48), 236: (334, 48), 240: (334, 48), 245: (334, 48)}
CLOCK_PIECE = (249, (252, 59))
# Launch pieces: (available id, selected id, size, cell (x0, x1) inside the piece, icon (name, centre x, size), line colour name)
LAUNCH = {"info": (260, 271, (90, 59), (8, 88), ("info", 47.5, 26), "ACCENT0"),
          "home": (309, 311, (72, 59), (0, 72), ("home", 36, 28), "TEXT"),
          "settings": (252, 254, (90, 59), (6, 86), ("settings", 46, 26), "ACCENT0")}
INFO_OVERLAYS = {268: (19, 33), 265: (19, 33)}  # iconInfoDefault / iconInfoSelected: transparent
INFO_ALERT = (262, (21, 35))  # iconInfoHighlighted: our icon, centred, in the phone accent

# Placements moved: file -> [(sprite or None for the main timeline, depth, character, Ford's (x, y), ours), twips]
MEDIA_ICON_DX, MEDIA_TEXT_DX = -4090, 1100  # source icons to x 16, the texts after them (x 72)
MEDIA_ICONS = [(30, 35, (4440, 60)), (34, 41, (4440, 21)), (36, 44, (4440, 20)), (38, 47, (4420, 20)),
               (40, 50, (4400, 40)), (32, 38, (4500, 0)), (20, 25, (4423, -30)), (28, 32, (4456, 25)),
               (50, 65, (4400, 41)), (42, 53, (4440, 0)), (44, 56, (4439, 40)), (46, 59, (4440, 42)),
               (48, 62, (4440, 40)), (4, 9, (4440, 40))]  # AM/FM, CD, USB, SD, line-in, Sirius, DAB, BT, note, listening x4, HD
MEDIA_TEXTS = [(69, 115, (340, 300)), (70, 116, (340, 300)), (55, 70, (300, 260)), (52, 68, (240, -1700)),
               (60, 77, (239, 20)), (57, 73, (300, 1074))]  # txtInfoField(_2Icon), compSource(_2Icon), track progress, compInfo
MOVES = {
    "AppConsole": [(366, 15, 322, (7240, 140), (7280, 140)),  # iconHome 362 -> 364
                   (273, 2, 264, (1020, 300), (740, 360)),  # iconInfoHighlighted (51,15) -> (37,18), on the piece's icon
                   (366, 3, 259, (8655, 359), (8655, 9700))],  # lineVerticalSeparator off the screen
    "MenuConsoleObject": [(None, 1, 2, (-833, 100), (-933, 100))],  # the clock field: centre 405 -> 400
    "PhoneConsoleObject": [(56, 1, 2, (300, 120), (320, 280)), (56, 23, 55, (300, 120), (320, 280)),  # label, info field
                           (56, 22, 54, (-1467, 120), (-1467, 280)), (56, 2, 53, (5701, 76), (5701, 236)),  # timer, icons
                           (None, 25, 58, (260, 80), (280, OFF_STAGE))],  # P1: compPhoneConsoleHomeView
    "NavConsoleObject": [(None, 1, 14, (748, -20), (828, 120)), (None, 9, 19, (260, -69), (340, 71)),  # street, status
                         (None, 12, 24, (1040, 20), (1040, OFF_STAGE)), (None, 22, 48, (1102, 0), (1102, OFF_STAGE))],  # compass
    "MediaConsoleObject": [(117, d, c, xy, (xy[0] + MEDIA_ICON_DX, xy[1])) for d, c, xy in MEDIA_ICONS]
                          + [(117, d, c, xy, (xy[0] + MEDIA_TEXT_DX, xy[1])) for d, c, xy in MEDIA_TEXTS],
    "ClimateConsoleObject": [(None, 1, 3, (-80, -40), (-100, OFF_STAGE)),  # C1: compClimateTabViewHome ("Klimat")
                             (None, 3, 49, (-200, 0), (-200, 28))],  # temperatures, seats: the media text's baseline
    "Media": [],
}
# N3: the class, the branch's opener and the member whose `_visible = true` turns false
NAV_CLASS, NAV_BRANCH = "__Packages.NavConsoleObject", ("isOnHomeScreen", "compSystemStatus", "_visible")
# M1: the class and its two constant-pool strings, same lengths
STRINGS_CLASS = "__Packages.MediaConsoleStrings"
STRINGS = {b"Resource.Media.ConsoleObject.146\0": b"Resource.Media.ConsoleObject.x46\0",
           b"Entertainment\0": b"\0"}  # the default becomes "", 13 bytes shorter: the class tag and the file change length
# Placements re-encoded one field wider (same values) in the files that would otherwise keep
# Ford's length: s2am refuses a start-up file as long as Ford's, because the car checks a copy by
# its size alone
GROW = {("MenuConsoleObject", None, 1, 2), ("PhoneConsoleObject", None, 25, 58), ("NavConsoleObject", None, 1, 14)}
PATCHED_CLASS = {"NavConsoleObject": NAV_CLASS, "MediaConsoleObject": STRINGS_CLASS, "Media": STRINGS_CLASS}


def frame_pictures(data: bytes) -> dict[int, Image.Image]:
    """Every picture restyle_frame replaces, in the v2 palette, then the frame's own."""
    art.use(PALETTE)
    new = restyle_frame.artwork(data, straight=True)
    for ident, size in TABS.items():
        new[ident] = art.tab(size)
    new[CLOCK_PIECE[0]] = art.clock_piece(CLOCK_PIECE[1])
    for available, selected, size, cell, icon, line in LAUNCH.values():
        new[available] = art.launch(size, cell, icon, False, restyle_frame.colour(line))
        new[selected] = art.launch(size, cell, icon, True, restyle_frame.colour(line))
    for ident, size in INFO_OVERLAYS.items():
        new[ident] = Image.new("RGBA", size, (0, 0, 0, 0))
    ident, size = INFO_ALERT
    new[ident] = art.icon(size, "info", art.ACCENTS[1], LAUNCH["info"][4][2], centre=(size[0] / 2, size[1] / 2))
    found = swf_bitmaps.pictures(swf_bitmaps.unpack(data)[1])
    for ident, image in new.items():
        if ident not in found or tuple(found[ident][2:]) != image.size:
            raise SystemExit(f"picture {ident} is not {image.size[0]}x{image.size[1]}: not the frame this tool was made for")
    return new


def move_all(body: bytes, moves: list, name: str = "") -> bytes:
    """Every placement from Ford's values to ours; refused when one is not at Ford's."""
    for sprite, depth, character, ford, ours in moves:
        if swf_place.read(body, sprite, depth, character) != ford:
            raise SystemExit(f"placement {sprite}/{depth}/{character} is not Ford's: not the file this tool was made for")
        body = swf_place.move(body, sprite, depth, character, ford, ours, grow=(name, sprite, depth, character) in GROW)
    for sprite, depth, character, _, ours in moves:
        if swf_place.read(body, sprite, depth, character) != ours:
            raise SystemExit("a placement did not read back as written")
    return body


def patch_class(body: bytes, name: str, change) -> bytes:
    """The class's code through `change(code) -> code`; the tag's length field follows."""
    found = swf_bitmaps.tags(body)
    index = class_actions(body, name)
    code, header, contents = found[index]
    contents = contents[:2] + change(contents[2:])
    found[index] = (code, swf_place.tag_header(code, len(contents)), contents)
    return b"".join(h + c for _, h, c in found)


def nav_home_branch(code: bytes) -> bytes:
    """N3: the Home branch's `compSystemStatus._visible = true` -> false, read back."""
    at = swf_actions.branch_boolean(code, *NAV_BRANCH)
    patched = swf_actions.set_boolean(code, at, False)
    _, strings = swf_actions.pool(patched)
    push = next(d for o, op, d in swf_actions.actions(patched) if op == swf_actions.PUSH and o + 3 + len(d) - 1 == at)
    if swf_actions.push_items(push, strings) != [NAV_BRANCH[2], False]:
        raise SystemExit("the push did not read back as false")
    return patched


def media_strings(code: bytes) -> bytes:
    """M1: the Entertainment label's key and default, same lengths, read back."""
    return swf_actions.replace_strings(code, STRINGS)


def check(old: bytes, new: bytes, pictures: set[int], sprites: set[int], main_places: bool, classes: set[int]) -> list[int]:
    """Tag by tag: only the named pictures, sprites, main-timeline placements and class tags
    may differ. Returns the indices that do."""
    (head, before), (head2, after) = swf_bitmaps.unpack(old), swf_bitmaps.unpack(new)
    a, b = swf_bitmaps.tags(before), swf_bitmaps.tags(after)
    if head != head2 or [t[0] for t in a] != [t[0] for t in b]:
        raise SystemExit("the header or the list of tags changed")
    allowed = set(classes)
    for i, (code, _, c) in enumerate(a):
        if code in (20, 35, 36) and swf_bitmaps.picture_info(code, c)[0] in pictures:
            allowed.add(i)
        elif code == swf_place.SPRITE and struct.unpack_from("<H", c)[0] in sprites:
            allowed.add(i)
        elif code == swf_place.PLACE2 and main_places:
            allowed.add(i)
    changed = {i for i, (x, y) in enumerate(zip(a, b)) if x[1:] != y[1:]}
    if changed - allowed:
        raise SystemExit(f"tags changed that should not have: {sorted(changed - allowed)}")
    return sorted(changed)


def build_one(name: str, data: bytes) -> tuple[bytes, dict[int, Image.Image], list[int]]:
    """(the built file, the new pictures if any, the indices of the tags that differ)."""
    pictures: dict[int, Image.Image] = {}
    if name == "AppConsole":
        pictures = frame_pictures(data)
        data_in = swf_bitmaps.replace(data, pictures)
    else:
        data_in = data
    head, body = swf_bitmaps.unpack(data_in)
    body = move_all(body, MOVES[name], name)
    classes = set()
    if name == "NavConsoleObject":
        body = patch_class(body, NAV_CLASS, nav_home_branch)
    if name in ("MediaConsoleObject", "Media"):
        body = patch_class(body, STRINGS_CLASS, media_strings)
    if name in PATCHED_CLASS:
        classes = {class_actions(body, PATCHED_CLASS[name])}
    result = swf_bitmaps.pack(head, body)
    sprites = {m[0] for m in MOVES[name] if m[0] is not None}
    changed = check(data, result, set(pictures), sprites, any(m[0] is None for m in MOVES[name]), classes)
    if len(result) == len(data):
        raise SystemExit(f"{name}: the result is as long as the car's file; s2am would refuse it (nothing written)")
    return result, pictures, changed


def main(argv: list[str]) -> None:
    folder = Path(argv[argv.index("--preview") + 1]) if "--preview" in argv else None
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--preview")]
    if len(args) != 2 or any(a.startswith("--") and a != "--preview" for a in argv):
        raise SystemExit(__doc__)
    apps, out = Path(args[0]), Path(args[1])
    for name, relative in FILES.items():
        data = (apps / relative).read_bytes()
        result, pictures, changed = build_one(name, data)
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result)
        if folder and pictures:
            restyle_frame.preview(data, pictures, folder)
        print(f"{target}: {len(pictures)} pictures, {len(MOVES[name])} placements"
              + (", 1 class" if name in PATCHED_CLASS else "") + f"; {len(changed)} tags differ from the car's "
              f"file, everything else byte for byte; sha256 {hashlib.sha256(result).hexdigest()[:16]}, {len(result)} bytes")
    build_menus.main([str(apps), str(out)] + (["--preview", str(folder)] if folder else []))
    themes = apps.parent / "Themes"
    if themes.is_dir():
        make_theme.main(str(themes), str(out / "Themes"), borderless=True, palette=PALETTE, glow=False)
    else:
        print(f"no Themes folder beside {apps}: run tools/make_theme.py CAR_THEMES OUT --borderless --palette {PALETTE} --no-glow")


if __name__ == "__main__":
    main(sys.argv[1:])
