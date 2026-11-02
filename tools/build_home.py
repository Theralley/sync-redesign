"""Build the Home screen as four cards with accent stripes (plan phase R7).

Usage: python3 tools/build_home.py CAR_HOME_SWF OUT_SWF [--preview FOLDER]

Takes **your car's own** Home\\Home.swf (from the drive log, in ~/.s2am). Home.swf is a start-up
file, and only a frame: the four quadrants (phone, navigation, media, climate) are separate
files that Home loads and moves into place once all four have arrived. What Home draws itself
is a half-transparent black filter over the wallpaper and two gradient divider lines. This
turns that into the cards of the sketch; nothing is recompiled:

- through FFDec's XML form of the file (the pinned copy, in Docker, no network): the two
  divider shapes (54 and 56) are redrawn as four accent stripes and four rounded card bodies
  over them; their two placements inside mcSmartCorners (sprite 63) are moved so the shapes
  draw in screen coordinates, and no longer in Ford's "screen" blend mode; the sprite's own
  placement loses its 0.9989 y-scale; and the filter (shape 52) becomes opaque black, so the
  gaps between the cards do not depend on the wallpaper the owner picked;
- in place, same length, in the class Home: the eight numbers of SC_TOP_LEFT, SC_TOP_RIGHT,
  SC_BTM_RIGHT and SC_BTM_LEFT, where Home moves the four quadrant files, so each lands inside
  its card. Seven are integers; one (SC_BTM_LEFT's x, 0) the compiler stored as a double, which
  ActionScript 2 writes with the two 32-bit halves of the number swapped.

FFDec's round trip is not byte for byte (it re-encodes a gradient shape it was not asked to
touch), so only the tags named above are taken from its output; every other tag is the car's
own. The result is checked tag by tag against the car's file: only the three shapes, the sprite
(and inside it only the two divider placements), its placement on the main timeline and the
class Home may differ, the class only in the eight numbers; and every shape, matrix, colour and
number must read back as written. A file that is not the Home screen this was made for (other
dividers, another filter, other corner numbers) is refused.

--preview FOLDER renders Ford's Home and ours with FFDec, side by side, and, when the four
quadrant files lie beside Home.swf as in the drive log (Apps/Phone/PhoneSmartCorner.swf and so
on), puts them on both pictures in an idle state. Ford's artwork: keep FOLDER private.

The cards take the deep palette's bar colour on black, the stripes the four area colours
(restyle_art.ACCENTS). They are fitted to what the quadrant files draw today, so nothing inside
those files has to move yet, and each quadrant's full-size invisible touch button stays at or
below y=48, under the frame's title bar, as Ford had it.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

import restyle_art as art
import swf_bitmaps
from build_apps_menu import run_ffdec, tags as every_tag
from build_phone_history import class_actions

CLASS = "__Packages.Home"
BACKGROUND = art.PALETTES["deep"]["BACKGROUND"]  # the gaps between the cards: Ford's filter, now opaque
CARD = art.PALETTES["deep"]["BAR"]
ACCENT = {"phone": art.ACCENTS[1], "nav": art.ACCENTS[2], "media": art.ACCENTS[3], "climate": art.ACCENTS[4]}
RADIUS, STRIPE = 10, 6  # px: the cards' corners, and how much of each stripe shows at the card's left
# Screen pixels. The cards (x, y, width, height), each sized to what its quadrant file draws in its
# idle state (phone y 49..165, nav 30..170, media 28..165, climate 34..160 of their 400x240).
CARDS = {"phone": (10, 56, 385, 158), "media": (10, 224, 385, 200),
         "nav": (405, 56, 385, 174), "climate": (405, 240, 385, 184)}
# Where Home moves each quadrant file: (Ford's, ours), by the constant in the class Home
CORNERS = {"SC_TOP_LEFT": ("phone", (10, 40), (3, 39)), "SC_TOP_RIGHT": ("nav", (400, 40), (398, 48)),
           "SC_BTM_RIGHT": ("climate", (400, 235), (398, 242)), "SC_BTM_LEFT": ("media", (0, 245), (2, 232))}
FILTER, STRIPES, BODIES, SMART = 52, 54, 56, 63  # the three shapes, and the sprite mcSmartCorners
DIVIDERS = (55, 57)  # the two placements inside it: the clips that hold shapes 54 and 56
SMART_PLACED = (8040, 4800)  # twips: where the main timeline puts mcSmartCorners (Home.init forces _x = 400)
SMART_AT = (400, 240)  # px: where it sits at run time, so the shapes inside are drawn from minus this
LABELS = (59, 60, 61, 62)  # its design-time labels, hidden at run time; blanked for the preview only
PLACE2, PLACE3, SHAPE, SHAPE3, SPRITE, EDIT_TEXT = 26, 70, 2, 32, 39, 37  # tag codes
TWIP = 20


# ------------------------------------------------------------------ the shapes, in FFDec's XML form
def bits(*values: int) -> int:
    """The signed bit count FFDec's XML wants for these values."""
    return max(2, max(abs(v) for v in values).bit_length() + 1)


def rounded_rect(x: int, y: int, w: int, h: int, r: int) -> list[tuple]:
    """Edge records in twips of a rounded rectangle, clockwise on screen from (x + r, y)."""
    x, y, w, h, r = x * TWIP, y * TWIP, w * TWIP, h * TWIP, r * TWIP
    return [("move", x + r, y),
            ("line", w - 2 * r, 0), ("curve", r, 0, 0, r),
            ("line", 0, h - 2 * r), ("curve", 0, r, -r, 0),
            ("line", -(w - 2 * r), 0), ("curve", -r, 0, 0, -r),
            ("line", 0, -(h - 2 * r)), ("curve", 0, -r, r, 0)]


def card_paths() -> tuple[list, list]:
    """The stripes (drawn first) and the card bodies over them, each (colour, edges)."""
    stripes, bodies = [], []
    for name, (x, y, w, h) in CARDS.items():
        stripes.append((ACCENT[name], rounded_rect(x, y, 2 * RADIUS + STRIPE, h, RADIUS)))
        bodies.append((CARD, rounded_rect(x + STRIPE, y, w - STRIPE, h, RADIUS)))
    return stripes, bodies


def shape_xml(tag: ElementTree.Element, paths: list[tuple[tuple[int, int, int], list[tuple]]]) -> None:
    """Rewrite a DefineShape's styles, records and bounds: one solid colour fill per path."""
    shapes = tag.find("shapes")
    fills = shapes.find("fillStyles").find("fillStyles")
    for child in list(fills):
        fills.remove(child)
    for colour, _ in paths:
        item = ElementTree.SubElement(fills, "item", {"type": "FILLSTYLE", "fillStyleType": "0"})
        ElementTree.SubElement(item, "color", {"type": "RGB", "red": str(colour[0]), "green": str(colour[1]),
                                               "blue": str(colour[2])})
    shapes.set("numFillBits", str(len(paths).bit_length()))
    shapes.set("numLineBits", "0")
    lines = shapes.find("lineStyles").find("lineStyles")
    for child in list(lines):
        lines.remove(child)
    records = shapes.find("shapeRecords")
    for child in list(records):
        records.remove(child)
    xs, ys = [], []
    for index, (_, edges) in enumerate(paths, start=1):
        px = py = 0
        for edge in edges:
            if edge[0] == "move":
                px, py = edge[1], edge[2]
                ElementTree.SubElement(records, "item", {
                    "type": "StyleChangeRecord", "stateMoveTo": "true", "moveBits": str(bits(px, py)),
                    "moveDeltaX": str(px), "moveDeltaY": str(py), "stateFillStyle0": "false",
                    "stateFillStyle1": "true", "fillStyle1": str(index), "stateLineStyle": "false",
                    "stateNewStyles": "false"})
            elif edge[0] == "line":
                dx, dy = edge[1], edge[2]
                attrs = {"type": "StraightEdgeRecord", "numBits": str(bits(dx, dy)),
                         "generalLineFlag": str(bool(dx and dy)).lower()}
                if dx and dy:
                    attrs.update(deltaX=str(dx), deltaY=str(dy))
                elif dx:
                    attrs.update(vertLineFlag="false", deltaX=str(dx))
                else:
                    attrs.update(vertLineFlag="true", deltaY=str(dy))
                ElementTree.SubElement(records, "item", attrs)
                px, py = px + dx, py + dy
            else:
                cx, cy, ax, ay = edge[1:]
                ElementTree.SubElement(records, "item", {
                    "type": "CurvedEdgeRecord", "numBits": str(bits(cx, cy, ax, ay)), "controlDeltaX": str(cx),
                    "controlDeltaY": str(cy), "anchorDeltaX": str(ax), "anchorDeltaY": str(ay)})
                px, py = px + cx + ax, py + cy + ay
            xs.append(px)
            ys.append(py)
    ElementTree.SubElement(records, "item", {"type": "EndShapeRecord", "endOfShape": "0"})
    bounds = tag.find("shapeBounds")
    for key, value in (("Xmin", min(xs)), ("Xmax", max(xs)), ("Ymin", min(ys)), ("Ymax", max(ys))):
        bounds.set(key, str(value))
    bounds.set("nbits", str(bits(min(xs), max(xs), min(ys), max(ys))))


STATE = ("stateMoveTo", "stateFillStyle0", "stateFillStyle1", "stateLineStyle", "stateNewStyles",
         "fillStyle0", "fillStyle1", "lineStyle", "moveDeltaX", "moveDeltaY")


def read_shape(tag: ElementTree.Element) -> list[tuple]:
    """Everything that decides what a shape is, as plain tuples: its bounds, bit counts, fills, line
    styles and every record with all its flags, to compare what was read back with what was written."""
    shapes = tag.find("shapes")
    bounds = tag.find("shapeBounds")
    out = [("bounds", *(bounds.get(k) for k in ("Xmin", "Xmax", "Ymin", "Ymax", "nbits"))),
           ("bits", shapes.get("numFillBits"), shapes.get("numLineBits")),
           ("lines", len(shapes.find("lineStyles").find("lineStyles")))]
    for fill in shapes.find("fillStyles").find("fillStyles"):
        colour = fill.find("color")
        out.append(("fill", fill.get("fillStyleType"), None if colour is None else
                    tuple(colour.get(k) for k in ("red", "green", "blue", "alpha"))))
    for record in shapes.find("shapeRecords"):
        kind = record.get("type")
        if kind == "StyleChangeRecord":
            out.append(("change", *(record.get(k) for k in STATE)))
        elif kind == "StraightEdgeRecord":
            out.append(("line", record.get("deltaX", "0"), record.get("deltaY", "0"),
                        record.get("generalLineFlag"), record.get("vertLineFlag")))
        elif kind == "CurvedEdgeRecord":
            out.append(("curve", record.get("controlDeltaX"), record.get("controlDeltaY"),
                        record.get("anchorDeltaX"), record.get("anchorDeltaY")))
        else:
            out.append((kind,))
    return out


# ------------------------------------------------------------------ finding things in FFDec's XML
def find(root: ElementTree.Element, kind: str, ident: int) -> ElementTree.Element | None:
    """The Define tag of one XML type (DefineShapeTag, DefineSpriteTag, ...) with this character id."""
    attr = {"DefineShapeTag": "shapeId", "DefineShape3Tag": "shapeId", "DefineSpriteTag": "spriteId",
            "DefineEditTextTag": "characterID"}[kind]
    return next((tag for tag in root.find("tags") if tag.get("type") == kind and tag.get(attr) == str(ident)), None)


def define(root: ElementTree.Element, kind: str, ident: int) -> ElementTree.Element:
    """The same, for Home.swf: a missing tag means another file."""
    tag = find(root, kind, ident)
    if tag is None:
        raise SystemExit(f"no {kind} {ident}: this is not the Home screen this tool was made for")
    return tag


def container(root: ElementTree.Element, which: str) -> ElementTree.Element | None:
    """The placements of the main timeline ("main") or of a sprite, by its id; None without that sprite."""
    if which == "main":
        return root.find("tags")
    sprite = find(root, "DefineSpriteTag", int(which))
    return None if sprite is None else sprite.find("subTags")


def placements(items: ElementTree.Element, character: int) -> list[ElementTree.Element]:
    """Every PlaceObject2 or PlaceObject3 in items that places this character."""
    return [item for item in items if item.get("type") in ("PlaceObject2Tag", "PlaceObject3Tag")
            and item.get("characterId") == str(character)]


def set_translate(place: ElementTree.Element, x: int, y: int) -> None:
    """A placement's matrix: a plain move by (x, y) twips, no scale, no rotation."""
    matrix = place.find("matrix")
    for key in ("scaleX", "scaleY", "rotateSkew0", "rotateSkew1", "nScaleBits", "nRotateBits"):
        matrix.attrib.pop(key, None)
    matrix.set("hasScale", "false")
    matrix.set("hasRotate", "false")
    matrix.set("nTranslateBits", str(bits(x, y)))
    matrix.set("translateX", str(x))
    matrix.set("translateY", str(y))


def filter_colour(root: ElementTree.Element) -> ElementTree.Element:
    return define(root, "DefineShape3Tag", FILTER).find("shapes").find("fillStyles").find("fillStyles")[0].find("color")


def smart(root: ElementTree.Element) -> ElementTree.Element:
    """The placements inside mcSmartCorners."""
    return define(root, "DefineSpriteTag", SMART).find("subTags")


def check_ford(root: ElementTree.Element) -> None:
    """The file is the Home screen this was made for: Ford's two dividers (0.75 x 348 and 800 x 0.75
    px), its 50 % black filter, and mcSmartCorners placed once where Ford put it."""
    stripes = define(root, "DefineShapeTag", STRIPES).find("shapeBounds")
    bodies = define(root, "DefineShapeTag", BODIES).find("shapeBounds")
    if (stripes.get("Xmax"), stripes.get("Ymax")) != ("15", "6968") or (bodies.get("Xmax"), bodies.get("Ymax")) != ("15999", "15"):
        raise SystemExit("the divider shapes are not Ford's: this is not the Home screen this tool was made for")
    colour = filter_colour(root)
    if (colour.get("red"), colour.get("green"), colour.get("blue"), colour.get("alpha")) != ("0", "0", "0", "127"):
        raise SystemExit("the screen filter is not Ford's 50 % black: this is not the Home screen this tool was made for")
    if any(len(placements(smart(root), character)) != 1 for character in DIVIDERS):
        raise SystemExit("the dividers are not placed once each in mcSmartCorners: not the Home screen this tool was made for")
    placed_smart = placements(container(root, "main"), SMART)
    matrix = placed_smart[0].find("matrix") if len(placed_smart) == 1 else None
    if matrix is None or placed_smart[0].get("name") != "mcSmartCorners" \
            or (matrix.get("translateX"), matrix.get("translateY")) != tuple(str(v) for v in SMART_PLACED):
        raise SystemExit("mcSmartCorners is not placed once where Ford put it: not the Home screen this tool was made for")


def edit_xml(root: ElementTree.Element, preview: bool) -> None:
    """The cards, in FFDec's XML form of the file."""
    stripes, bodies = card_paths()
    shape_xml(define(root, "DefineShapeTag", STRIPES), stripes)
    shape_xml(define(root, "DefineShapeTag", BODIES), bodies)
    for character in DIVIDERS:
        place = placements(smart(root), character)[0]
        set_translate(place, -SMART_AT[0] * TWIP, -SMART_AT[1] * TWIP)
        place.set("blendMode", "1")  # normal; Ford's "screen" blend (4) would let the wallpaper through
        place.set("placeFlagHasBlendMode", "false")
    set_translate(placements(container(root, "main"), SMART)[0], *SMART_PLACED)
    colour = filter_colour(root)
    for key, value in zip(("red", "green", "blue", "alpha"), (*BACKGROUND, 255)):
        colour.set(key, str(value))
    if preview:  # Home hides the four design-time labels at run time; FFDec would draw them
        for ident in LABELS:
            define(root, "DefineEditTextTag", ident).set("initialText", "")


def check_xml(root: ElementTree.Element) -> None:
    """Every shape, matrix and colour read back from the result's XML as written."""
    stripes, bodies = card_paths()
    for ident, paths in ((STRIPES, stripes), (BODIES, bodies)):
        tag = define(root, "DefineShapeTag", ident)
        want = ElementTree.fromstring(ElementTree.tostring(tag))
        shape_xml(want, paths)
        if read_shape(tag) != read_shape(want):
            raise SystemExit(f"shape {ident} did not read back as written")
    expected = [(smart(root), c, (-SMART_AT[0] * TWIP, -SMART_AT[1] * TWIP)) for c in DIVIDERS]
    expected.append((container(root, "main"), SMART, SMART_PLACED))
    for items, character, (x, y) in expected:
        place = placements(items, character)[0]
        matrix = place.find("matrix")
        got = (matrix.get("translateX"), matrix.get("translateY"), matrix.get("hasScale"), matrix.get("hasRotate"),
               matrix.get("scaleX"), matrix.get("scaleY"), matrix.get("rotateSkew0"), matrix.get("rotateSkew1"))
        if got != (str(x), str(y), "false", "false", None, None, None, None) \
                or (character in DIVIDERS and place.get("placeFlagHasBlendMode") == "true"):
            raise SystemExit(f"the placement of {character} did not read back as written")
    colour = filter_colour(root)
    if tuple(colour.get(k) for k in ("red", "green", "blue", "alpha")) != tuple(str(v) for v in (*BACKGROUND, 255)):
        raise SystemExit("the filter colour did not read back as written")


# ------------------------------------------------------------------ the eight numbers in the class Home
def as2_double(raw: bytes) -> float:
    """A double as ActionScript 2 pushes it: the two 32-bit halves of the little-endian IEEE number swapped."""
    return struct.unpack("<d", raw[4:8] + raw[0:4])[0]


def as2_double_bytes(value: float) -> bytes:
    raw = struct.pack("<d", value)
    return raw[4:8] + raw[0:4]


PUSH, CONSTANT_POOL, INIT_ARRAY, SET_MEMBER = 0x96, 0x88, 0x42, 0x4F  # ActionScript 2 opcodes


def actions_in(actions: bytes) -> list[tuple[int, list[tuple[int, str, object]]]]:
    """(opcode, pushed items) for every action in a class's init code: a Push's items as (offset,
    kind, value) with constant pool names resolved, an empty list for any other action.
    build_phone_history.numbers reads one integer after a name, as {rowHeight: 50} compiles;
    SC_TOP_LEFT = [10, 40] compiles to one Push of the name, 40, 10 and the count 2, then
    InitArray and SetMember, and one of Home's eight numbers is a double, so this lists all."""
    pool, out, p = [], [], 0
    while p < len(actions) and actions[p]:
        op = actions[p]
        p += 1
        if op < 0x80:
            out.append((op, []))
            continue
        length = struct.unpack_from("<H", actions, p)[0]
        start, p = p + 2, p + 2 + length
        data, items = actions[start:p], []
        if op == CONSTANT_POOL:
            pool, q = [], 2
            for _ in range(struct.unpack_from("<H", data)[0]):
                end = data.index(b"\0", q)
                pool.append(data[q:end].decode("latin1"))
                q = end + 1
        elif op == PUSH:
            q = 0
            while q < len(data):
                kind, q = data[q], q + 1
                size = {0: None, 1: 4, 2: 0, 3: 0, 4: 1, 5: 1, 6: 8, 7: 4, 8: 1, 9: 2}[kind]
                if kind == 0:
                    size = data.index(b"\0", q) - q + 1
                if kind == 6:
                    items.append((start + q, "double", as2_double(data[q:q + 8])))
                elif kind == 7:
                    items.append((start + q, "int", struct.unpack_from("<i", data, q)[0]))
                elif kind in (8, 9):
                    items.append((start + q, "name", pool[data[q] if kind == 8 else struct.unpack_from("<H", data, q)[0]]))
                else:
                    items.append((start + q, "other", None))
                q += size
        out.append((op, items))
    return out


def corner_slots(actions: bytes) -> dict[str, tuple[tuple[int, str, float], tuple[int, str, float]]]:
    """For each SC_* constant, its y and its x as (offset in actions, "int" or "double", value).
    Only the pattern Ford's compiler left is accepted: one Push ending in the name, y, x and the
    count 2, followed at once by InitArray and SetMember; anything else in between is refused."""
    rows = actions_in(actions)
    found = {}
    for i, (op, items) in enumerate(rows):
        if op != PUSH or len(items) < 4 or items[-4][1] != "name" or items[-4][2] not in CORNERS:
            continue
        name, y, x, count = items[-4:]
        if (y[1] in ("int", "double") and x[1] in ("int", "double") and count[1:] == ("int", 2)
                and [row[0] for row in rows[i + 1:i + 3]] == [INIT_ARRAY, SET_MEMBER]):
            if name[2] in found:
                raise SystemExit(f"{name[2]} is set twice in {CLASS}: not the Home screen this tool was made for")
            found[name[2]] = (y, x)
    if set(found) != set(CORNERS):
        raise SystemExit(f"{CLASS} does not set all of {sorted(CORNERS)} as Ford's compiler did: "
                         "not the Home screen this tool was made for")
    return found


def change_code(body: bytes) -> bytes:
    """The eight corner numbers in the class Home, changed in place (same length, same kinds)."""
    found = swf_bitmaps.tags(body)
    index = class_actions(body, CLASS)
    code, header, contents = found[index]
    actions = bytearray(contents[2:])
    for name, ((yoff, ykind, yval), (xoff, xkind, xval)) in corner_slots(bytes(actions)).items():
        _, ford, ours = CORNERS[name]
        if (xval, yval) != ford:
            raise SystemExit(f"{name} is {(xval, yval)}, not Ford's {ford}: not the Home screen this tool was made for")
        for offset, kind, value in ((xoff, xkind, ours[0]), (yoff, ykind, ours[1])):
            if kind == "int":
                struct.pack_into("<i", actions, offset, value)
            else:
                actions[offset:offset + 8] = as2_double_bytes(float(value))
    back = {name: (x[2], y[2]) for name, (y, x) in corner_slots(bytes(actions)).items()}
    if back != {name: ours for name, (_, _, ours) in CORNERS.items()}:
        raise SystemExit("the corner numbers did not read back as written")
    found[index] = (code, header, contents[:2] + bytes(actions))
    return b"".join(h + c for _, h, c in found)


# ------------------------------------------------------------------ the tags
def character(contents: bytes) -> int:
    """The id a Define tag declares."""
    return struct.unpack_from("<H", contents)[0]


def placed(code: int, contents: bytes) -> int | None:
    """The character a PlaceObject2 or PlaceObject3 places; None when it only moves one."""
    if not contents[0] & 0x02:
        return None
    p = 3 if code == PLACE2 else 4  # the flags (one byte, two in PlaceObject3), then the depth
    if code == PLACE3 and contents[1] & 0x18:  # a class name comes first
        p = contents.index(b"\0", p) + 1
    return struct.unpack_from("<H", contents, p)[0]


class Bits:
    """A reader of the bit-packed fields in a placement: its matrix and colour transform."""

    def __init__(self, data: bytes, pos: int) -> None:
        self.data, self.pos, self.bit = data, pos, 0

    def read(self, count: int) -> int:
        value = 0
        for _ in range(count):
            value = value << 1 | (self.data[self.pos] >> (7 - self.bit)) & 1
            self.bit += 1
            if self.bit == 8:
                self.bit, self.pos = 0, self.pos + 1
        return value

    def end(self) -> int:
        """The next byte boundary."""
        return self.pos + (1 if self.bit else 0)


def matrix_end(data: bytes, pos: int) -> int:
    """Where a MATRIX starting at pos ends: scale and rotation each a flag, then a bit count and
    two values when set; then the translation's bit count and two values."""
    bits = Bits(data, pos)
    for _ in range(2):
        if bits.read(1):
            count = bits.read(5)
            bits.read(count), bits.read(count)
    count = bits.read(5)
    bits.read(count), bits.read(count)
    return bits.end()


def cxform_end(data: bytes, pos: int) -> int:
    """Where a colour transform with alpha starting at pos ends."""
    bits = Bits(data, pos)
    add, mult, count = bits.read(1), bits.read(1), bits.read(4)
    for _ in range(4 * (add + mult)):
        bits.read(count)
    return bits.end()


def place_fields(code: int, contents: bytes) -> dict[str, object]:
    """A PlaceObject2 or PlaceObject3 split into its fields by name, so each can be compared on
    its own: flags, depth, class name, character, matrix, colour transform, ratio, name, clip
    depth, blend mode, bitmap cache, visibility, background and clip actions (None when absent).
    A filter list cannot be walked here; Ford's Home has none, so one is refused."""
    flags = contents[0] | (contents[1] << 8 if code == PLACE3 else 0)
    p = 1 if code == PLACE2 else 2  # after the flags: one byte, two in PlaceObject3
    fields = {"flags": flags, "depth": contents[p:p + 2]}
    p += 2
    if flags & 0x0800 or (flags & 0x1000 and flags & 0x02):
        end = contents.index(b"\0", p) + 1
        fields["class"], p = contents[p:end], end
    for name, present, size in (("character", flags & 0x02, 2), ("matrix", flags & 0x04, matrix_end),
                                ("cxform", flags & 0x08, cxform_end), ("ratio", flags & 0x10, 2),
                                ("name", flags & 0x20, 0), ("clip_depth", flags & 0x40, 2)):
        if present:
            end = (contents.index(b"\0", p) + 1 if name == "name" else
                   size(contents, p) if callable(size) else p + size)
            fields[name], p = contents[p:end], end
    if flags & 0x0100:
        raise SystemExit("a placement with filters: not the Home screen this tool was made for")
    for name, present, size in (("blend", flags & 0x0200, 1), ("cache", flags & 0x0400, 1),
                                ("visible", flags & 0x2000, 1), ("background", flags & 0x4000, 4)):
        if present:
            fields[name], p = contents[p:p + size], p + size
    if flags & 0x80:
        fields["clip_actions"] = contents[p:]
        p = len(contents)
    if p != len(contents):
        raise SystemExit("a placement with trailing bytes: not the Home screen this tool was made for")
    return fields


def same_but(code: int, x: bytes, y: bytes, allowed: tuple[str, ...]) -> bool:
    """Two placements equal in every field but the allowed ones (and, when the blend mode may
    change, in its flag)."""
    a, b = place_fields(code, x), place_fields(code, y)
    for fields in (a, b):
        for name in allowed:
            fields.pop(name, None)
        if "blend" in allowed:
            fields["flags"] &= ~0x0200
    return a == b


def sprite_tags(contents: bytes) -> list[tuple[int, bytes, bytes]]:
    """The tags inside a DefineSprite. swf_bitmaps.tags wants a frame header first; a sprite has
    none, so it gets a blank one (five zero bytes: an empty rectangle, rate and count)."""
    return swf_bitmaps.tags(bytes(5) + contents[4:])[1:]


def wanted(code: int, contents: bytes, preview: bool) -> bool:
    """A tag this tool changes: the three shapes, the sprite, its placement; for the preview the labels."""
    if code in (SHAPE, SHAPE3, SPRITE):
        return character(contents) in (FILTER, STRIPES, BODIES, SMART)
    if code == PLACE2:
        return placed(code, contents) == SMART
    return preview and code == EDIT_TEXT and character(contents) in LABELS


def splice(original: bytes, rebuilt: bytes, preview: bool) -> bytes:
    """The car's body with only the tags this tool changes taken from FFDec's rebuilt body."""
    a, b = swf_bitmaps.tags(original), swf_bitmaps.tags(rebuilt)
    if [t[0] for t in a] != [t[0] for t in b]:
        raise SystemExit("FFDec changed the list of tags")
    return b"".join(h2 + c2 if code != -1 and wanted(code, c, preview) else h + c
                    for (code, h, c), (_, h2, c2) in zip(a, b))


def check(old: bytes, new: bytes) -> int:
    """Tag by tag: only the three shapes, the sprite (inside it only the two divider placements),
    its placement on the main timeline and the class Home differ, the class only in its eight
    numbers. Returns how many tags changed, sprites' tags counted one by one."""
    (head, before), (head2, after) = swf_bitmaps.unpack(old), swf_bitmaps.unpack(new)
    for data, body in ((old, before), (new, after)):
        if struct.unpack_from("<I", data, 4)[0] != 8 + len(body):
            raise SystemExit("the file's length in its header is wrong")
    a, b = swf_bitmaps.tags(before), swf_bitmaps.tags(after)
    if head != head2 or a[0] != b[0] or [t[0] for t in a] != [t[0] for t in b]:
        raise SystemExit("the header or the list of tags changed")
    index = class_actions(before, CLASS)
    allowed = {i for i, (code, _, c) in enumerate(a) if code != -1 and wanted(code, c, False)} | {index}
    changed = {i for i, (x, y) in enumerate(zip(a, b)) if x[1:] != y[1:]}
    if changed - allowed:
        raise SystemExit(f"tags changed that should not have: {sorted(changed - allowed)}")
    main = next(i for i, (code, _, c) in enumerate(a) if code == PLACE2 and placed(code, c) == SMART)
    if main in changed and not same_but(PLACE2, a[main][2], b[main][2], ("matrix",)):
        raise SystemExit("mcSmartCorners' placement changed in more than its matrix")
    sprite = next(i for i, (code, _, c) in enumerate(a) if code == SPRITE and character(c) == SMART)
    inside, inside2 = sprite_tags(a[sprite][2]), sprite_tags(b[sprite][2])
    if a[sprite][2][:4] != b[sprite][2][:4] or [t[0] for t in inside] != [t[0] for t in inside2]:
        raise SystemExit("mcSmartCorners' header or its list of tags changed")
    for (code, h, c), (_, h2, c2) in zip(inside, inside2):
        if (h, c) == (h2, c2):
            continue
        if not (code == PLACE3 and placed(code, c) in DIVIDERS and same_but(code, c, c2, ("matrix", "blend"))):
            raise SystemExit("more than the two divider placements' matrix and blend mode changed inside mcSmartCorners")
    x, y = a[index][2], b[index][2]
    numbers = set()
    for offset, kind, _ in (slot for pair in corner_slots(y[2:]).values() for slot in pair):
        numbers |= set(range(offset + 2, offset + 2 + (4 if kind == "int" else 8)))
    if len(x) != len(y) or any(p != q and i not in numbers for i, (p, q) in enumerate(zip(x, y))):
        raise SystemExit("the class Home changed outside the eight corner numbers")
    return sum(p != q for p, q in zip(every_tag(old), every_tag(new)))


def build(data: bytes, preview: bool = False) -> bytes:
    """The car's Home.swf with the cards: the numbers first (no Docker needed to refuse a wrong
    file), then the shapes through FFDec, spliced and read back. check() comes after, in main: a
    preview build (labels blanked) could not pass it."""
    if data[:3] != b"FWS" or struct.unpack_from("<I", data, 4)[0] != len(data):
        raise SystemExit("not an uncompressed Flash file of the length its header says: "
                         "this is not the Home screen this tool was made for")
    head, body = swf_bitmaps.unpack(data)
    body = change_code(body)
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        (work / "in.swf").write_bytes(data)
        run_ffdec(work, "-swf2xml", "/work/in.swf", "/work/in.xml")
        tree = ElementTree.parse(work / "in.xml")
        check_ford(tree.getroot())
        edit_xml(tree.getroot(), preview)
        tree.write(work / "out.xml", encoding="utf-8", xml_declaration=True)
        run_ffdec(work, "-xml2swf", "/work/out.xml", "/work/out.swf")
        rebuilt = swf_bitmaps.unpack((work / "out.swf").read_bytes())[1]
        result = swf_bitmaps.pack(head, splice(body, rebuilt, preview))
        (work / "check.swf").write_bytes(result)
        run_ffdec(work, "-swf2xml", "/work/check.swf", "/work/check.xml")
        check_xml(ElementTree.parse(work / "check.xml").getroot())
    return result


# ------------------------------------------------------------------ the preview
QUADRANTS = {"phone": "Phone/PhoneSmartCorner.swf", "nav": "Nav/NavSmartCorner.swf",
             "media": "Media/MediaSmartCorner.swf", "climate": "Climate/ClimateSmartCorner.swf"}
# Each quadrant file in an idle state (a connected phone, FM with presets, no route, two seat
# heaters), through FFDec's XML form: placements dropped by instance name (in the main timeline
# or a sprite, by id), one moved as the code moves it, sample texts set by field id.
IDLE = {
    "phone": {
        "drop": {"main": ["mcActiveCallPanel", "phoneCallFrame", "progressIconInst", "compButtonAddPhone"],
                 "87": ["iconEA", "iconE911", "iconRoaming", "iconMessage"],
                 "85": ["iconBatteryLife0", "iconBatteryLife1", "iconBatteryLife2", "iconBatteryLife3", "iconBatteryLife5"],
                 "86": ["iconRadioSignal0", "iconRadioSignal1", "iconRadioSignal2", "iconRadioSignal3", "iconRadioSignal5"]},
        "text": {"103": "Telefon ansluten", "91": "Stör inte"},
    },
    "nav": {
        "drop": {"main": ["compButtonWhereAmI", "compButtonDestination", "compETA", "compButtonCancelRoute",
                          "activeIconInst", "milesToGoTxt", "maneuverStreetTxt"]},
        "text": {"12": "Storgatan"},
    },
    "media": {
        "drop": {"main": ["racActivationBTIcon", "compButtonPower", "dabIcon", "mcHDRadioScreen", "mcSatRadioScreen",
                          "satIcon", "mcCDScreen", "mcDeviceMetaScreen", "mcDeviceNoMetaScreen", "iconTA"],
                 "20": ["txtLabel", "txtLabel2"]},
        "text": {"17": "P1", "48": "P2", "62": "P3", "66": "P4", "55": "MIX", "72": "ROCK", "76": "P3"},
    },
    "climate": {
        "drop": {"main": ["compPower", "compDriverTemp", "compPassengerTemp", "txtLeftTempCentered", "txtRightTempCentered"],
                 "61": ["compCooledSeatsDriver", "compHeatedSteeringWheel"], "64": ["compCooledSeatsPassenger"],
                 "30": ["bgButtonPanelSOLO", "LEDTwoHeatedSeatsDriver"], "62": ["bgButtonPanelSOLO", "LEDTwoHeatedSeatsPassenger"]},
        "move": {"61": {"compHeatedSeatsDriver": (1320, 0)}},  # as UpdateCornerView does: _x = 66
        "text": {"67": "22.0°", "68": "22.0°"},
    },
}
FRAME = (20, 22, 26)  # the frame's bars, which are not Home's, drawn flat on the preview


def idle(root: ElementTree.Element, spec: dict, background: tuple[int, int, int]) -> None:
    """One quadrant file's XML in its idle state, on a black or white background. What a file does
    not have (another car's quadrant files) is left alone: the preview is a picture, not a check."""
    for which, names in spec.get("drop", {}).items():
        box = container(root, which)
        for item in list(box) if box is not None else []:
            if item.get("type") in ("PlaceObject2Tag", "PlaceObject3Tag") and item.get("name") in names:
                box.remove(item)
    for which, moves in spec.get("move", {}).items():
        for item in container(root, which) if container(root, which) is not None else []:
            if item.get("name") in moves:
                matrix = item.find("matrix")
                matrix.set("translateX", str(moves[item.get("name")][0]))
                matrix.set("translateY", str(moves[item.get("name")][1]))
                matrix.set("nTranslateBits", "16")
    for ident, text in spec.get("text", {}).items():
        field = find(root, "DefineEditTextTag", int(ident))
        if field is None:
            continue
        html = field.get("initialText") or '<p align="center"></p>'
        if "<font" in html:  # the first font run gets the text; one paragraph only
            html = re.sub(r"(<font[^>]*>).*?(</font>)", lambda m: m.group(1) + text + m.group(2), html, count=1, flags=re.S)
            html = re.sub(r"</p><p.*$", "</p>", html, flags=re.S)
        else:
            html = re.sub(r"(<p[^>]*>).*?(</p>)", lambda m: m.group(1) + text + m.group(2), html, count=1, flags=re.S)
        field.set("initialText", html)
    for tag in root.find("tags"):
        if tag.get("type") == "SetBackgroundColorTag":
            for key, value in zip(("red", "green", "blue"), background):
                tag.find("backgroundColor").set(key, str(value))


def render(work: Path, swfs: dict[str, bytes]) -> dict[str, Image.Image]:
    """The first frame of each file, rendered by FFDec in one run."""
    (work / "in").mkdir(parents=True)
    for name, data in swfs.items():
        (work / "in" / f"{name}.swf").write_bytes(data)
    run_ffdec(work, "-select", "1", "-export", "frame", "/work/out", "/work/in")
    return {name: Image.open(work / "out" / f"{name}.swf" / "1.png").convert("RGB") for name in swfs}


def with_alpha(on_black: Image.Image, on_white: Image.Image) -> Image.Image:
    """A render's exact alpha from two renders: alpha = 255 - (white - black); the colour from the
    black one, divided by the alpha."""
    alpha = ImageChops.invert(ImageChops.difference(on_white, on_black).convert("L"))
    image = on_black.convert("RGBA")
    pixels, levels = image.load(), alpha.load()
    for y in range(image.height):
        for x in range(image.width):
            a = levels[x, y]
            r, g, b, _ = pixels[x, y]
            pixels[x, y] = (min(255, r * 255 // a), min(255, g * 255 // a), min(255, b * 255 // a), a) if a else (0, 0, 0, 0)
    return image


def quadrants(work: Path, files: dict[str, Path]) -> dict[str, Image.Image]:
    """The four quadrant files in their idle state, with alpha."""
    work.mkdir(parents=True)
    variants = {}
    for name, file in files.items():
        (work / "in.swf").write_bytes(file.read_bytes())
        run_ffdec(work, "-swf2xml", "/work/in.swf", "/work/in.xml")
        for suffix, background in (("black", (0, 0, 0)), ("white", (255, 255, 255))):
            tree = ElementTree.parse(work / "in.xml")
            idle(tree.getroot(), IDLE[name], background)
            tree.write(work / f"{name}-{suffix}.xml", encoding="utf-8", xml_declaration=True)
            run_ffdec(work, "-xml2swf", f"/work/{name}-{suffix}.xml", f"/work/{name}-{suffix}.swf")
            variants[f"{name}-{suffix}"] = (work / f"{name}-{suffix}.swf").read_bytes()
    shots = render(work / "render", variants)
    return {name: with_alpha(shots[f"{name}-black"], shots[f"{name}-white"]) for name in files}


def compose(base: Image.Image, corners: dict[str, Image.Image], which: int, note: str) -> Image.Image:
    """Home's frame with the quadrants where Home moves them (which: 0 Ford's places, 1 ours), and
    the frame's bars, which are not Home.swf's, flat."""
    image = base.convert("RGBA")
    for name, ford, ours in CORNERS.values():
        if name in corners:
            image.alpha_composite(corners[name], (ford, ours)[which])
    draw = ImageDraw.Draw(image)
    for top, bottom in ((0, 48), (432, 480)):
        draw.rectangle((0, top, 799, bottom - 1), fill=(*FRAME, 255))
    draw.text((8, 16), "the frame's title bar (not in Home.swf)", fill=(120, 120, 120, 255))
    draw.text((8, 450), "the frame's bottom bar (not in Home.swf)   " + note, fill=(120, 120, 120, 255))
    return image.convert("RGB")


def preview(source: Path, ours: bytes, folder: Path) -> None:
    """Ford's Home and ours, rendered by FFDec, side by side; with the quadrant files when they
    lie beside Home.swf as in the drive log."""
    folder.mkdir(parents=True, exist_ok=True)
    files = {name: source.parent.parent / path for name, path in QUADRANTS.items()}
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        (work / "in.swf").write_bytes(source.read_bytes())
        run_ffdec(work, "-swf2xml", "/work/in.swf", "/work/in.xml")
        tree = ElementTree.parse(work / "in.xml")
        for ident in LABELS:
            define(tree.getroot(), "DefineEditTextTag", ident).set("initialText", "")
        for sprite in ("28", "27"):  # the Loader and View components draw a grey box at design time
            box = container(tree.getroot(), sprite)
            for item in list(box) if box is not None else []:
                if item.get("name") == "boundingBox_mc":
                    box.remove(item)
        tree.write(work / "ford.xml", encoding="utf-8", xml_declaration=True)
        run_ffdec(work, "-xml2swf", "/work/ford.xml", "/work/ford.swf")
        shots = render(work / "home", {"ford": (work / "ford.swf").read_bytes(), "ours": ours})
        corners = quadrants(work / "quadrants", files) if all(f.is_file() for f in files.values()) else {}
    note = "" if corners else "(quadrant files not found beside Home.swf)"
    ford = compose(shots["ford"], corners, 0, "wallpaper not rendered " + note)
    cards = compose(shots["ours"], corners, 1, note)
    ford.save(folder / "home-ford.png")
    cards.save(folder / "home-ours.png")
    shots["ours"].save(folder / "home-ours-cards-only.png")
    sheet = Image.new("RGB", (800 * 2 + 20, 480 + 24), (255, 255, 255))
    sheet.paste(ford, (0, 24))
    sheet.paste(cards, (820, 24))
    draw = ImageDraw.Draw(sheet)
    draw.text((4, 6), "Ford's Home.swf with the quadrant files (idle)", fill="black")
    draw.text((824, 6), "ours, the same quadrant files moved into the cards", fill="black")
    sheet.save(folder / "home-ford-vs-ours.png")
    for name, image in corners.items():
        image.save(folder / f"quadrant-{name}-idle.png")


# ------------------------------------------------------------------ the command line
def options(argv: list[str]) -> tuple[str, str, Path | None]:
    """The command line: (source, target, preview folder). An option without its value, an
    unknown option or a missing file name stops with the usage."""
    folder, args, i = None, [], 0
    while i < len(argv):
        if argv[i] == "--preview":
            if i + 1 == len(argv) or argv[i + 1].startswith("--"):
                raise SystemExit(__doc__)
            folder, i = Path(argv[i + 1]), i + 2
            continue
        if argv[i].startswith("--"):
            raise SystemExit(__doc__)
        args.append(argv[i])
        i += 1
    if len(args) != 2:
        raise SystemExit(__doc__)
    return args[0], args[1], folder


def main(argv: list[str]) -> None:
    source, target, folder = options(argv)
    data = Path(source).read_bytes()
    result = build(data)
    changed = check(data, result)
    Path(target).write_bytes(result)
    print(f"{target}: four cards; {changed} of {len(every_tag(data))} tags changed (the three shapes, the two "
          f"divider placements, mcSmartCorners' own, the class Home's eight numbers); everything else byte for "
          f"byte; sha256 {hashlib.sha256(result).hexdigest()}, {len(result)} bytes")
    if folder:
        preview(Path(source), build(data, preview=True), folder)
        print(f"previews in {folder}")


if __name__ == "__main__":
    main(sys.argv[1:])
