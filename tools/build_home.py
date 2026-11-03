"""Build the Home screen as an aligned 2x2 grid of cards with our headings (phase R7 v2).

Usage: python3 tools/build_home.py CAR_APPS_FOLDER OUT_FOLDER [--preview DIR [--photo FILE] [--outlines]]

Takes **your car's own** Sync/Apps folder (from the drive log, in ~/.s2am) and writes, at their
Apps-relative paths under OUT_FOLDER: Home/Home.swf, and through build_corners.py the four
quadrant files Phone/PhoneSmartCorner.swf, Nav/NavSmartCorner.swf, Media/MediaSmartCorner.swf,
Climate/ClimateSmartCorner.swf. Home.swf is a start-up file and only a frame: it shows the
wallpaper under a half-transparent black filter and two gradient divider lines, loads the four
quadrant files and moves them into place. This makes it the grid of version 2; nothing is
recompiled, no tag is added or removed:

- through FFDec's XML form (the pinned copy, in Docker, no network): the vertical divider
  (shape 54) becomes the four card bodies, rounded rectangles of CARD on the grid x 8-396 and
  404-792, y 56-236 and 244-424 (8 px margins and gaps); the horizontal divider (shape 56)
  becomes the four headings, a 16 px area icon and the area's name ("Telefon", "Navigation",
  "Media", "Klimat") in the area colour, 18 px, as plain vector art set in DM Sans (fonts/, OFL)
  through glyphs.py: no font tag, no device font; their two placements inside mcSmartCorners
  are moved so the shapes draw in screen coordinates and lose Ford's "screen" blend mode; the
  sprite's own placement loses its 0.9989 y-scale; and the filter (shape 52) becomes opaque
  black, so the wallpaper never shows;
- in place, same length, in the class Home: the eight numbers of SC_TOP_LEFT, SC_TOP_RIGHT,
  SC_BTM_RIGHT and SC_BTM_LEFT, where Home moves the four quadrant files (OURS). Seven are
  integers; one (SC_BTM_LEFT's x, 0) the compiler stored as a double, which ActionScript 2
  writes with the two 32-bit halves of the number swapped.

FFDec's round trip is not byte for byte (it re-encodes a gradient shape it was not asked to
touch), so only the tags named above are taken from its output; every other tag is the car's
own. The result is checked tag by tag against the car's file: only the three shapes, the sprite
(and inside it only the two divider placements), its placement on the main timeline and the
class Home may differ, the class only in the eight numbers; and every shape, matrix, colour and
number must read back as written. A file that is not the Home screen this was made for (other
dividers, another filter, other corner numbers) is refused, and so is any output as long as
the car's file: s2am refuses such a start-up file, and the car's import checks a copy by its
size alone.

--preview DIR renders the result with FFDec: Home with the four quadrant files in an idle state
(a connected phone, FM with six presets, no route, two seat heaters) composed where Home moves
them, the frame's bars plain black, in three pictures (the run-time chip colour, lighter chips,
sample temperatures), beside a photo if one is given with --photo FILE, and prints the measured
screen positions. The theme draws no button outline in the car (frame v2 sets the theme's
LINE_ALPHA to 0), so the pictures show none; --outlines adds a diagnostic overlay, labelled as
such, of where SyncThemeButtonArt.DrawIt would draw one, each checked against its fill. Ford's
artwork: keep OUT_FOLDER and DIR private.
"""
from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

import build_corners
import glyphs
import swf_bitmaps
import xmlswf as X

HOME = "Home/Home.swf"
CLASS = "__Packages.Home"
BACKGROUND = (0, 0, 0)  # the gaps between the cards: Ford's filter, now opaque
CARD = (10, 11, 14)
ACCENT = {"phone": (214, 160, 72), "nav": (72, 190, 150), "media": (220, 76, 84), "climate": (64, 150, 255)}
NAME = {"phone": "Telefon", "nav": "Navigation", "media": "Media", "climate": "Klimat"}
RADIUS = 12
# The grid (screen px): columns x 8-396 and 404-792, rows y 56-236 and 244-424; (x, y, w, h)
CARDS = {"phone": (8, 56, 388, 180), "nav": (404, 56, 388, 180),
         "media": (8, 244, 388, 180), "climate": (404, 244, 388, 180)}
HEADING_SIZE, HEADING_TOP, HEADING_X, ICON = 18, 12, 16, 16  # px: type size, offsets from the card's corner, icon box
# Where Home moves each quadrant file (SC_* in the class Home): Ford's and ours, screen px. Ours
# are chosen so each quadrant's content sits centred in its card below the heading (build_corners
# lays the content out for exactly these origins) and each quadrant's full-size invisible touch
# button stays at or below y=48, under the frame's title bar: the phone's button starts at +9,+9
# (44+9=53), nav's at +0 (48), media's at +0 (236; it reaches under the bottom bar as Ford's did),
# climate's at +9,+0 (236).
FORD = {"phone": (10, 40), "nav": (400, 40), "climate": (400, 235), "media": (0, 245)}
OURS = {"phone": (2, 44), "nav": (398, 48), "climate": (400, 236), "media": (2, 236)}
SLOT = {"SC_TOP_LEFT": "phone", "SC_TOP_RIGHT": "nav", "SC_BTM_RIGHT": "climate", "SC_BTM_LEFT": "media"}
BODIES, HEADINGS, FILTER, SMART = 54, 56, 52, 63  # the three shapes, and the sprite mcSmartCorners
DIVIDERS = {1: 55, 3: 57}  # the two placements inside it: depth -> the clip holding shape 54 / 56
SMART_PLACED = (402, 240)  # px: where the main timeline puts mcSmartCorners
SMART_AT = (400, 240)  # px: where it sits at run time (Home.init forces _x = 400)
LABELS = (59, 60, 61, 62)  # its design-time labels, hidden at run time; blanked for the preview only
ALLOWED = {("DefineShape", BODIES), ("DefineShape", HEADINGS), ("DefineShape3", FILTER), ("DoInitAction", 67),
           ("main", "PlaceObject2", 6, "mcSmartCorners"), (f"sprite{SMART}", "PlaceObject3", 1, ""),
           (f"sprite{SMART}", "PlaceObject3", 3, "")}


# ------------------------------------------------------------------ the art
def icon_paths(name: str, x: float, y: float) -> list[tuple]:
    """A 16 px area icon with its box at (x, y): simple filled geometry, holes in CARD."""
    a, c = ACCENT[name], CARD
    if name == "phone":  # a phone: a rounded ring with a short bar at the bottom
        return [(a, X.rounded_rect(x + 3.5, y + 0.5, 9, 15, 2.5)), (c, X.rounded_rect(x + 5, y + 2, 6, 10.5, 1.2)),
                (c, X.rounded_rect(x + 6.5, y + 13.1, 3, 1.2, 0.5))]
    if name == "nav":  # a navigation arrow
        return [(a, X.polygon([(x + 8, y + 0.5), (x + 15, y + 15), (x + 8, y + 11.6), (x + 1, y + 15)]))]
    if name == "media":  # a note: head, stem, flag
        return [(a, X.circle(x + 5.2, y + 12.2, 3.6)), (a, X.polygon([(x + 7.3, y + 1), (x + 9, y + 1), (x + 9, y + 12), (x + 7.3, y + 12)])),
                (a, X.polygon([(x + 7.3, y + 1), (x + 14.5, y + 3.4), (x + 14.5, y + 7.2), (x + 9, y + 5.2)]))]
    if name == "climate":  # a thermometer
        return [(a, X.rounded_rect(x + 4.5, y + 0.5, 7, 11.5, 3.5)), (c, X.rounded_rect(x + 6.2, y + 2.2, 3.6, 8.3, 1.8)),
                (a, X.circle(x + 8, y + 12.3, 3.6)), (a, X.polygon([(x + 7.2, y + 5.5), (x + 8.8, y + 5.5), (x + 8.8, y + 11), (x + 7.2, y + 11)]))]
    raise ValueError(name)


def body_paths() -> list[tuple]:
    return [(CARD, X.rounded_rect(x, y, w, h, RADIUS)) for x, y, w, h in CARDS.values()]


def heading_paths(face: glyphs.Face) -> list[tuple]:
    """Icon and name for each card at the card's top-left; the icon box is centred on the type's
    cap height so icon and letters sit on one visual line."""
    out = []
    cap = face.cap_height * HEADING_SIZE
    for name, (x, y, _, _) in CARDS.items():
        baseline = y + HEADING_TOP + cap + 1  # 1 px of air above the cap height
        icon_top = baseline - cap / 2 - ICON / 2 - 0.5
        out += icon_paths(name, x + HEADING_X, icon_top)
        for contour in face.edges(NAME[name], x + HEADING_X + ICON + 8, baseline, HEADING_SIZE):
            out.append((ACCENT[name], contour))
    return out


# ------------------------------------------------------------------ the XML edits
def filter_colour(root: ET.Element) -> ET.Element:
    return X.define(root, "DefineShape3Tag", FILTER).find("shapes").find("fillStyles").find("fillStyles")[0].find("color")


def check_ford(root: ET.Element) -> None:
    """The file is the Home screen this was made for: Ford's two dividers (0.75 x 348 and 800 x
    0.75 px), its 50 % black filter, and mcSmartCorners with its two dividers, placed once."""
    s = X.define(root, "DefineShapeTag", BODIES).find("shapeBounds")
    c = X.define(root, "DefineShapeTag", HEADINGS).find("shapeBounds")
    if (s.get("Xmax"), s.get("Ymax")) != ("15", "6968") or (c.get("Xmax"), c.get("Ymax")) != ("15999", "15"):
        raise SystemExit("the divider shapes are not Ford's: this is not the Home screen this tool was made for")
    colour = filter_colour(root)
    if tuple(colour.get(k) for k in ("red", "green", "blue", "alpha")) != ("0", "0", "0", "127"):
        raise SystemExit("the screen filter is not Ford's 50 % black: this is not the Home screen this tool was made for")
    smart = X.container(root, SMART)
    for depth, character in DIVIDERS.items():
        if X.matrix_values(X.placement(smart, depth=depth, character=character))[5] == "true":
            raise SystemExit("a divider placement is rotated or skewed: this is not the Home screen this tool was made for")
    main = X.placement(X.container(root, "main"), name="mcSmartCorners", character=SMART)
    if X.matrix_values(main)[:2] != tuple(str(v * X.TWIP) for v in SMART_PLACED) or X.matrix_values(main)[5] == "true":
        raise SystemExit("mcSmartCorners is not where Ford put it: this is not the Home screen this tool was made for")


def edit_xml(root: ET.Element, face: glyphs.Face, preview: bool) -> None:
    X.shape_xml(X.define(root, "DefineShapeTag", BODIES), body_paths())
    X.shape_xml(X.define(root, "DefineShapeTag", HEADINGS), heading_paths(face))
    smart = X.container(root, SMART)
    for depth in DIVIDERS:
        place = X.placement(smart, depth=depth)
        X.set_matrix(place, -SMART_AT[0], -SMART_AT[1], keep_scale=False)
        place.set("blendMode", "1")  # normal; Ford's "screen" blend would let the wallpaper through
        place.set("placeFlagHasBlendMode", "false")
    X.set_matrix(X.placement(X.container(root, "main"), name="mcSmartCorners"), *SMART_PLACED, keep_scale=False)
    colour = filter_colour(root)
    for key, value in zip(("red", "green", "blue", "alpha"), (*BACKGROUND, 255)):
        colour.set(key, str(value))
    if preview:  # Home hides the four design-time labels at run time, and forces mcSmartCorners._x = 400;
        for ident in LABELS:  # FFDec runs no code, so the picture gets both here
            X.define(root, "DefineEditTextTag", ident).set("initialText", "")
        X.set_matrix(X.placement(X.container(root, "main"), name="mcSmartCorners"), *SMART_AT, keep_scale=False)


def check_xml(root: ET.Element, face: glyphs.Face, preview: bool) -> None:
    """Our shapes, matrices and colour read back from the result's XML."""
    for ident, paths in ((BODIES, body_paths()), (HEADINGS, heading_paths(face))):
        tag = X.define(root, "DefineShapeTag", ident)
        want = ET.fromstring(ET.tostring(tag))
        X.shape_xml(want, paths)
        if X.read_shape(tag) != X.read_shape(want):
            raise SystemExit(f"shape {ident} did not read back as written")
    smart = X.container(root, SMART)
    for depth in DIVIDERS:
        place = X.placement(smart, depth=depth)
        values = X.matrix_values(place)
        if values[:3] != (str(-SMART_AT[0] * X.TWIP), str(-SMART_AT[1] * X.TWIP), "false") or values[5] != "false" \
                or place.get("placeFlagHasBlendMode") == "true":
            raise SystemExit(f"the placement at depth {depth} in mcSmartCorners did not read back as written")
    at = SMART_AT if preview else SMART_PLACED
    values = X.matrix_values(X.placement(X.container(root, "main"), name="mcSmartCorners"))
    if values[:3] != (str(at[0] * X.TWIP), str(at[1] * X.TWIP), "false") or values[5] != "false":
        raise SystemExit("mcSmartCorners' placement did not read back as written")
    if tuple(int(filter_colour(root).get(k)) for k in ("red", "green", "blue", "alpha")) != (*BACKGROUND, 255):
        raise SystemExit("the filter colour did not read back as written")


# ------------------------------------------------------------------ the eight numbers
def corner_slots(body: bytes) -> dict[str, tuple[tuple[int, str, object], tuple[int, str, object]]]:
    """For each slot, the (y push, x push) of its [x, y] literal as (offset in body, kind, value).
    Only the pattern Ford's compiler left is accepted: the name, y, x and the count 2 pushed
    with nothing in between, then InitArray and SetMember at once; anything else is refused."""
    rows = X.class_pushes(body, CLASS)
    found = {}
    for i, (_, kind, value) in enumerate(rows):
        if kind == "const" and value in SLOT and i + 5 < len(rows):
            y, x, count, init, member = rows[i + 1:i + 6]
            if y[1] in ("int", "double") and x[1] in ("int", "double") and count[1:] == ("int", 2) \
                    and init[1:] == ("op", X.INIT_ARRAY) and member[1:] == ("op", X.SET_MEMBER):
                if SLOT[value] in found:
                    raise SystemExit(f"{value} is set twice in {CLASS}: not the Home screen this tool was made for")
                found[SLOT[value]] = (y, x)
    if set(found) != set(SLOT.values()):
        raise SystemExit(f"{CLASS} does not set all of {sorted(SLOT)} as Ford's compiler did: "
                         "not the Home screen this tool was made for")
    return found


def patch_corners(body: bytes) -> bytes:
    """The eight corner numbers, changed in place (same length, same kinds) and read back."""
    out = bytearray(body)
    for name, ((yoff, ykind, yval), (xoff, xkind, xval)) in corner_slots(body).items():
        if xval != FORD[name][0] or yval != FORD[name][1]:  # exactly: 0.75 is not Ford's 0
            raise SystemExit(f"{name} is at {xval},{yval}, not Ford's {FORD[name]}: not the Home screen this tool was made for")
        for off, kind, value in ((xoff, xkind, OURS[name][0]), (yoff, ykind, OURS[name][1])):
            if kind == "int":
                struct.pack_into("<i", out, off, value)
            else:
                out[off:off + 8] = X.as2_double_bytes(float(value))
    result = bytes(out)
    back = {n: (s[1][2], s[0][2]) for n, s in corner_slots(result).items()}
    if any(back[n] != OURS[n] for n in OURS) or set(back) != set(OURS):
        raise SystemExit(f"the corner numbers did not read back as written: {back}")
    return result


# ------------------------------------------------------------------ build and check
def build(original: bytes, face: glyphs.Face, work: Path, preview: bool = False) -> bytes:
    """The car's Home.swf as the grid. A preview build (labels blanked, the sprite at its run-time
    x) is a picture only and skips the tag check, which it could not pass."""
    if original[:3] != b"FWS" or struct.unpack_from("<I", original, 4)[0] != len(original):
        raise SystemExit("not an uncompressed Flash file of the length its header says: "
                         "this is not the Home screen this tool was made for")
    tree = X.swf2xml(work, original)
    check_ford(tree.getroot())
    edit_xml(tree.getroot(), face, preview)
    rebuilt = X.xml2swf(work, tree)
    head, body = swf_bitmaps.unpack(original)
    body = X.splice(body, swf_bitmaps.unpack(rebuilt)[1],
                    defines={(X.SHAPE, BODIES), (X.SHAPE, HEADINGS), (X.SHAPE3, FILTER)}
                    | ({(X.EDIT_TEXT, i) for i in LABELS} if preview else set()),
                    main_places={(6, "mcSmartCorners")}, sprite_places={SMART: {(d, "") for d in DIVIDERS}})
    result = swf_bitmaps.pack(head, patch_corners(body))
    check_xml(X.swf2xml(work, result, "check").getroot(), face, preview)
    if not preview:
        check(original, result)
    return result


def check(original: bytes, result: bytes) -> list[tuple]:
    """Tag by tag: only the three shapes, the sprite (inside it the two divider placements, in
    matrix and blend mode only), its own placement (matrix only) and the class Home differ, the
    class only in its eight numbers; and the result is not as long as the car's file. Returns
    the changed keys (eight, the sprite's own included)."""
    X.check_length(original, result, HOME)
    changed = X.check(original, result, ALLOWED, place_allowed=("matrix", "blend"))
    body = swf_bitmaps.unpack(result)[1]
    found = corner_slots(body)
    if any(found[n][1][2] != OURS[n][0] or found[n][0][2] != OURS[n][1] for n in OURS):
        raise SystemExit("the corner numbers in the result are not ours")
    slots = [(off, kind) for pair in found.values() for off, kind, _ in pair]
    X.check_class(swf_bitmaps.unpack(original)[1], body, CLASS, slots)
    if len(changed) != 8:
        raise SystemExit(f"expected 8 changed tags, got {changed}")
    return changed


# ------------------------------------------------------------------ the preview
PICTURES = {"": "home.png", "22": "home-chips22.png", "temps": "home-temps.png"}
OUTLINE = (255, 64, 160)  # the --outlines diagnostic overlay: a colour nothing in the picture has
# content blocks measured per quadrant: label -> quadrant-local box (x0, y0, x1, y1[, x split])
BLOCKS = {
    "phone": {"icons": (0, 0, 400, 48), "text": (0, 60, 400, 112), "chip": (0, 112, 400, 175)},
    "nav": {"street": (0, 60, 400, 150)},
    "media": {"source icon": (90, 10, 150, 48), "name": (40, 42, 360, 91), "presets": (0, 91, 400, 190)},
    "climate": {"seats": (0, 44, 400, 195, 198)},
}
VARIANT_BLOCKS = {"temps": {"climate": {"temps": (150, 8, 400, 44, 313)}}}
QUADRANT = {"phone": "PhoneSmartCorner", "nav": "NavSmartCorner", "media": "MediaSmartCorner", "climate": "ClimateSmartCorner"}


def with_alpha(on_black: Image.Image, on_white: Image.Image) -> Image.Image:
    """A render's exact alpha from two renders: alpha = 255 - (white - black); the colour from
    the black one, divided by the alpha."""
    alpha = ImageChops.invert(ImageChops.difference(on_white, on_black).convert("L"))
    image = on_black.convert("RGBA")
    px, al = image.load(), alpha.load()
    for y in range(image.height):
        for x in range(image.width):
            a = al[x, y]
            r, g, b, _ = px[x, y]
            px[x, y] = (min(255, r * 255 // a), min(255, g * 255 // a), min(255, b * 255 // a), a) if a else (0, 0, 0, 0)
    return image


def runs(values: list[bool]) -> list[tuple[int, int]]:
    out, start = [], None
    for i, v in enumerate(values + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    return out


def measure_home(home: Image.Image) -> list[str]:
    px = home.load()
    is_card = lambda p: max(abs(a - b) for a, b in zip(p[:3], CARD)) <= 1  # noqa: E731
    lines = []
    for y, label in ((146, "top row"), (334, "bottom row")):
        lines.append(f"cards, {label} (y={y}): x runs {runs([is_card(px[x, y]) for x in range(800)])}")
    for x, label in ((200, "left column"), (600, "right column")):
        lines.append(f"cards, {label} (x={x}): y runs {runs([is_card(px[x, y]) for y in range(480)])}")
    for name, (cx, cy, cw, ch) in CARDS.items():
        band = home.crop((cx, cy + 6, cx + cw, cy + 40)).convert("RGB")
        mask = ImageChops.difference(band, Image.new("RGB", band.size, ACCENT[name])).convert("L").point(lambda v: 255 if v < 90 else 0)
        box = mask.getbbox()
        lines.append(f"heading {name!r}: screen x {box[0] + cx}-{box[2] + cx}, y {box[1] + cy + 6}-{box[3] + cy + 6}")
    return lines


def outlines(image: Image.Image, chip: tuple[int, int, int]) -> list[str]:
    """The --outlines diagnostic: where SyncThemeButtonArt.DrawIt would draw each theme button's
    1 px outline (the button's base box at its DayNight clip's origin, Ford's placement = the
    fill's origin, corners r=3 where the shape type rounds them), drawn in the overlay colour
    and measured against the fill. The car draws none while the theme's line alpha is 0."""
    draw = ImageDraw.Draw(image)
    lines = []
    px = image.load()
    for key, name in QUADRANT.items():
        ox, oy = OURS[key]
        for x, y, w, h, corners in build_corners.chip_boxes(name):
            x0, y0, x1, y1 = round(ox + x), round(oy + y), round(ox + x + w) - 1, round(oy + y + h) - 1
            fill = [(i, j) for j in range(y0 - 3, y1 + 4) for i in range(x0 - 3, x1 + 4)
                    if max(abs(a - b) for a, b in zip(px[i, j][:3], chip)) <= 2]
            box = (min(i for i, _ in fill), min(j for _, j in fill), max(i for i, _ in fill), max(j for _, j in fill)) if fill else None
            draw.rounded_rectangle((x0, y0, x1, y1), radius=3, outline=(*OUTLINE, 255), width=1, corners=tuple(bool(c) for c in corners))
            lines.append(f"{key} outline x {x0}-{x1 + 1} y {y0}-{y1 + 1}: fill measured {box and (box[0], box[2] + 1, box[1], box[3] + 1)}"
                         f" -> {'on the fill' if box == (x0, y0, x1, y1) else 'OFF THE FILL'}")
    return lines


def measure_corner(key: str, corner: Image.Image, blocks: dict | None = None, note: str = "") -> list[str]:
    ox, oy = OURS[key]
    alpha = corner.getchannel("A")
    lines = []
    for label, spec in (blocks or BLOCKS[key]).items():
        x0, y0, x1, y1 = spec[:4]
        parts = [(x0, x1)] if len(spec) == 4 else [(x0, spec[4]), (spec[4], x1)]
        for i, (px0, px1) in enumerate(parts):
            side = f" {('left', 'right')[i]}" if len(parts) > 1 else ""
            box = alpha.crop((px0, y0, px1, y1)).point(lambda v: 255 if v > 40 else 0).getbbox()
            if box is None:
                lines.append(f"{key} {label}{note}{side}: nothing drawn")
                continue
            sx0, sy0, sx1, sy1 = box[0] + px0 + ox, box[1] + y0 + oy, box[2] + px0 + ox, box[3] + y0 + oy
            lines.append(f"{key} {label}{note}{side}: screen x {sx0}-{sx1} (centre {(sx0 + sx1) / 2:.1f}), "
                         f"y {sy0}-{sy1} (centre {(sy0 + sy1) / 2:.1f})")
    return lines


def preview(home_preview: bytes, corners: dict[str, bytes], folder: Path, work: Path, photo: Path | None,
            overlay: bool = False) -> list[str]:
    """Home-preview with the quadrant files' idle variants composed where Home moves them."""
    folder.mkdir(parents=True, exist_ok=True)
    swfs = {"home": home_preview}
    for key, name in QUADRANT.items():
        for variant, data in build_corners.idle_variants(name, corners[name], work / name).items():
            swfs[f"{key}{variant}"] = data
    shots = {name: Image.open(path).convert("RGB") for name, path in X.render(work / "render", swfs).items()}
    report = measure_home(shots["home"])
    pictures = {}
    for variant, filename in PICTURES.items():
        image = shots["home"].convert("RGBA")
        for key in QUADRANT:
            v = variant if f"{key}{variant}-black" in shots else ""
            corner = with_alpha(shots[f"{key}{v}-black"], shots[f"{key}{v}-white"])
            image.alpha_composite(corner, OURS[key])
            if variant == "":
                corner.save(folder / f"quadrant-{key}-idle.png")
                report += measure_corner(key, corner)
            elif key in VARIANT_BLOCKS.get(variant, {}):
                report += measure_corner(key, corner, VARIANT_BLOCKS[variant][key], f" ({variant} variant)")
        if overlay:
            drawn = outlines(image, build_corners.VARIANTS[variant][0])
            if variant == "":
                report += drawn
        draw = ImageDraw.Draw(image)
        for top, bottom in ((0, 48), (432, 480)):
            draw.rectangle((0, top, 799, bottom - 1), fill=(0, 0, 0, 255))
        note = {"": "chips (13,14,18); temperature fields empty as in the car", "22": "chips (22,24,30)",
                "temps": "chips (13,14,18); sample temperatures shown"}[variant]
        draw.text((8, 18), "frame: title bar (AppConsole, not Home.swf)" + ("   DIAGNOSTIC OVERLAY: where DrawIt would draw a button outline (the car draws none, line alpha 0)" if overlay else ""),
                  fill=(*OUTLINE, 255) if overlay else (60, 60, 60, 255))
        draw.text((8, 452), "frame: bottom bar (AppConsole, not Home.swf)   " + note, fill=(60, 60, 60, 255))
        pictures[variant] = image.convert("RGB")
        pictures[variant].save(folder / filename)
    shots["home"].save(folder / "home-cards-only.png")
    if photo:
        shot = Image.open(photo).convert("RGB")
        shot = shot.resize((800, round(shot.height * 800 / shot.width)), Image.LANCZOS)
        sheet = Image.new("RGB", (1620, max(480, shot.height) + 24), (255, 255, 255))
        sheet.paste(shot, (0, 24))
        sheet.paste(pictures[""], (820, 24))
        d = ImageDraw.Draw(sheet)
        d.text((4, 6), "in the car (photo)", fill="black")
        d.text((824, 6), "built: Home.swf + the four quadrant files, FFDec renders, idle state", fill="black")
        sheet.save(folder / "home-vs-car.png")
    (folder / "measurements.txt").write_text("\n".join(report) + "\n")
    return report


# ------------------------------------------------------------------ the command line
def options(argv: list[str]) -> tuple[Path, Path, Path | None, Path | None, bool]:
    folder = photo = None
    args, i = [], 0
    overlay = "--outlines" in argv
    argv = [a for a in argv if a != "--outlines"]
    while i < len(argv):
        if argv[i] in ("--preview", "--photo"):
            if i + 1 == len(argv) or argv[i + 1].startswith("--"):
                raise SystemExit(__doc__)
            if argv[i] == "--preview":
                folder = Path(argv[i + 1])
            else:
                photo = Path(argv[i + 1])
            i += 2
            continue
        if argv[i].startswith("--"):
            raise SystemExit(__doc__)
        args.append(argv[i])
        i += 1
    if len(args) != 2 or (overlay and folder is None):
        raise SystemExit(__doc__)
    return Path(args[0]), Path(args[1]), folder, photo, overlay


def main(argv: list[str]) -> None:
    source, target, folder, photo, overlay = options(argv)
    original = (source / HOME).read_bytes()
    face = glyphs.Face()
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        result = build(original, face, work / "home")
        (target / HOME).parent.mkdir(parents=True, exist_ok=True)
        (target / HOME).write_bytes(result)
        print(f"{target / HOME}: the grid; 8 of {len(swf_bitmaps.tags(swf_bitmaps.unpack(original)[1])) - 1} top-level tags' "
              f"content changed (three shapes, mcSmartCorners and its placement, the class Home's eight numbers); "
              f"everything else byte for byte; sha256 {hashlib.sha256(result).hexdigest()}, {len(result)} bytes")
        corners = build_corners.build_all(source, target, work / "corners")
        if folder:
            home_preview = build(original, face, work / "home-preview", preview=True)
            print("\n".join(preview(home_preview, corners, folder, work / "preview", photo, overlay)))
            print(f"previews in {folder}")


if __name__ == "__main__":
    main(sys.argv[1:])
