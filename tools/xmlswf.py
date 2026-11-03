"""Flash files through FFDec's XML form: find, edit, splice back into the car's bytes, check.

Shared by build_home.py and build_corners.py. A tool edits FFDec's swf2xml of the car's file,
has FFDec write it back, then takes from that output only the tags it meant to change (whole
Define tags by id, placements by depth and name, inside a sprite only the named placements) and
keeps every other byte the car's: FFDec's round trip is not byte for byte for every tag. The
result is compared tag by tag with the car's file (sprites expanded, placements split into
their fields) and every value is read back from a second swf2xml.

Also here: solid-colour shape records in FFDec's form (rounded rectangles, polygons, circles),
the reader for an AS2 class's Push items (to change a number in place), and the FFDec runner
(the pinned 26.3.0, checksum-verified, in Docker without network, as build_apps_menu runs it).
"""
from __future__ import annotations

import math
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import swf_bitmaps
from build_apps_menu import run_ffdec

TWIP = 20
PLACE2, PLACE3, SPRITE, EDIT_TEXT, SHAPE, SHAPE3, EXPORT, INIT_ACTION = 26, 70, 39, 37, 2, 32, 56, 59
INIT_ARRAY, SET_MEMBER = 0x42, 0x4F  # ActionScript 2 opcodes
NAMES = {0: "End", 1: "ShowFrame", 2: "DefineShape", 9: "SetBackgroundColor", 10: "DefineFont", 11: "DefineText",
         12: "DoAction", 13: "DefineFontInfo", 20: "DefineBitsLossless", 21: "DefineBitsJPEG2", 22: "DefineShape2",
         26: "PlaceObject2", 28: "RemoveObject2", 32: "DefineShape3", 33: "DefineText2", 34: "DefineButton2",
         35: "DefineBitsJPEG3", 36: "DefineBitsLossless2", 37: "DefineEditText", 39: "DefineSprite", 43: "FrameLabel",
         48: "DefineFont2", 56: "ExportAssets", 57: "ImportAssets", 59: "DoInitAction", 69: "FileAttributes",
         70: "PlaceObject3", 71: "ImportAssets2", 73: "DefineFontAlignZones", 74: "CSMTextSettings", 75: "DefineFont3",
         77: "Metadata", 83: "DefineShape4", 88: "DefineFontName"}
DEFINES = (2, 22, 32, 83, 20, 36, 21, 35, 37, 39, 34, 10, 48, 75, 11, 33, 59, 73, 88)  # tags that start with a character id


# ------------------------------------------------------------------ FFDec
def swf2xml(work: Path, data: bytes, stem: str = "in") -> ET.ElementTree:
    work.mkdir(parents=True, exist_ok=True)
    (work / f"{stem}.swf").write_bytes(data)
    run_ffdec(work, "-swf2xml", f"/work/{stem}.swf", f"/work/{stem}.xml")
    return ET.parse(work / f"{stem}.xml")


def xml2swf(work: Path, tree: ET.ElementTree, stem: str = "out") -> bytes:
    tree.write(work / f"{stem}.xml", encoding="utf-8", xml_declaration=True)
    run_ffdec(work, "-xml2swf", f"/work/{stem}.xml", f"/work/{stem}.swf")
    return (work / f"{stem}.swf").read_bytes()


def render(work: Path, swfs: dict[str, bytes]) -> dict[str, Path]:
    """The first frame of each file as a PNG, rendered by FFDec in one run: name -> path."""
    (work / "in").mkdir(parents=True, exist_ok=True)
    for name, data in swfs.items():
        (work / "in" / f"{name}.swf").write_bytes(data)
    run_ffdec(work, "-select", "1", "-export", "frame", "/work/out", "/work/in")
    return {name: work / "out" / f"{name}.swf" / "1.png" for name in swfs}


# ------------------------------------------------------------------ finding things in the XML
ID_ATTR = {"DefineShapeTag": "shapeId", "DefineShape3Tag": "shapeId", "DefineShape4Tag": "shapeId",
           "DefineSpriteTag": "spriteId", "DefineEditTextTag": "characterID"}


def define(root: ET.Element, kind: str, ident: int | str) -> ET.Element:
    """The Define tag of one XML type with this character id; a missing one means another file."""
    for tag in root.find("tags"):
        if tag.get("type") == kind and tag.get(ID_ATTR[kind]) == str(ident):
            return tag
    raise SystemExit(f"no {kind} {ident}: not the file this tool was made for")


def container(root: ET.Element, which: str | int) -> ET.Element:
    """The placements of the main timeline ("main") or of a sprite by id."""
    if which == "main":
        return root.find("tags")
    return define(root, "DefineSpriteTag", which).find("subTags")


def placement(items: ET.Element, name: str | None = None, depth: int | None = None,
              character: int | None = None) -> ET.Element:
    """Exactly one PlaceObject2/3 by name, depth and/or character."""
    hits = [p for p in items if p.get("type") in ("PlaceObject2Tag", "PlaceObject3Tag")
            and (name is None or p.get("name") == name)
            and (depth is None or p.get("depth") == str(depth))
            and (character is None or p.get("characterId") == str(character))]
    if len(hits) != 1:
        raise SystemExit(f"placement name={name} depth={depth} character={character}: {len(hits)} hits, not 1: "
                         "not the file this tool was made for")
    return hits[0]


def bits(*values: int) -> int:
    """The signed bit count FFDec's XML wants for these values."""
    return max(2, max(abs(int(v)) for v in values).bit_length() + 1)


def matrix_values(place: ET.Element) -> tuple:
    m = place.find("matrix")
    return (m.get("translateX"), m.get("translateY"), m.get("hasScale"), m.get("scaleX"), m.get("scaleY"),
            m.get("hasRotate"), m.get("rotateSkew0"), m.get("rotateSkew1"))


def set_matrix(place: ET.Element, x_px: float | None = None, y_px: float | None = None,
               scale: tuple[float, float] | None = None, keep_scale: bool = True) -> None:
    """A placement's translation in pixels (stored in twips), and a plain scale when given; with
    keep_scale=False any scale is dropped. Rotation is never added."""
    m = place.find("matrix")
    if m is None:
        m = ET.SubElement(place, "matrix", {"type": "MATRIX"})
        place.set("placeFlagHasMatrix", "true")
    tx = int(round(float(x_px) * TWIP)) if x_px is not None else int(m.get("translateX", "0"))
    ty = int(round(float(y_px) * TWIP)) if y_px is not None else int(m.get("translateY", "0"))
    m.set("translateX", str(tx))
    m.set("translateY", str(ty))
    m.set("nTranslateBits", str(bits(tx, ty)))
    if scale is not None:
        m.set("hasScale", "true")
        m.set("scaleX", repr(float(scale[0])))
        m.set("scaleY", repr(float(scale[1])))
        m.set("nScaleBits", "20")
    elif not keep_scale:  # a plain move: no scale, no rotation or skew either
        for key in ("scaleX", "scaleY", "nScaleBits", "rotateSkew0", "rotateSkew1", "nRotateBits"):
            m.attrib.pop(key, None)
        m.set("hasScale", "false")
        m.set("hasRotate", "false")
    if m.get("hasRotate") is None:
        m.set("hasRotate", "false")


# ------------------------------------------------------------------ shapes
def rounded_rect(x: float, y: float, w: float, h: float, r: float) -> list[tuple]:
    """Edge records in twips of a rounded rectangle, clockwise on screen from (x + r, y)."""
    x, y, w, h, r = (int(round(v * TWIP)) for v in (x, y, w, h, r))
    return [("move", x + r, y),
            ("line", w - 2 * r, 0), ("curve", r, 0, 0, r),
            ("line", 0, h - 2 * r), ("curve", 0, r, -r, 0),
            ("line", -(w - 2 * r), 0), ("curve", -r, 0, 0, -r),
            ("line", 0, -(h - 2 * r)), ("curve", 0, -r, r, 0)]


def polygon(points: list[tuple[float, float]]) -> list[tuple]:
    """Edge records of a closed polygon (pixels in, twips out), in the order given."""
    pts = [(int(round(x * TWIP)), int(round(y * TWIP))) for x, y in points]
    out = [("move", *pts[0])]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (x1 - x0, y1 - y0) != (0, 0):
            out.append(("line", x1 - x0, y1 - y0))
    return out


def circle(cx: float, cy: float, r: float, segments: int = 8) -> list[tuple]:
    """Edge records of a circle from quadratic curves, clockwise on screen from (cx + r, cy)."""
    step = 2 * math.pi / segments
    k = r / math.cos(step / 2)
    sx, sy = int(round((cx + r) * TWIP)), int(round(cy * TWIP))
    out = [("move", sx, sy)]
    px, py = sx, sy
    for i in range(segments):
        am, a1 = (i + 0.5) * step, (i + 1) * step
        c = (int(round((cx + k * math.cos(am)) * TWIP)), int(round((cy + k * math.sin(am)) * TWIP)))
        a = (int(round((cx + r * math.cos(a1)) * TWIP)), int(round((cy + r * math.sin(a1)) * TWIP)))
        out.append(("curve", c[0] - px, c[1] - py, a[0] - c[0], a[1] - c[1]))
        px, py = a
    return out


def shape_xml(tag: ET.Element, paths: list[tuple[tuple[int, int, int], list[tuple]]]) -> None:
    """Rewrite a DefineShape's styles, records and bounds: solid RGB fills, one fill style per
    distinct colour, every path filled on its right (fillStyle1), no line styles."""
    colours = []
    for colour, _ in paths:
        if colour not in colours:
            colours.append(colour)
    shapes = tag.find("shapes")
    fills = shapes.find("fillStyles").find("fillStyles")
    for child in list(fills):
        fills.remove(child)
    for colour in colours:
        item = ET.SubElement(fills, "item", {"type": "FILLSTYLE", "fillStyleType": "0"})
        ET.SubElement(item, "color", {"type": "RGB", "red": str(colour[0]), "green": str(colour[1]), "blue": str(colour[2])})
    shapes.set("numFillBits", str(len(colours).bit_length()))
    shapes.set("numLineBits", "0")
    lines = shapes.find("lineStyles").find("lineStyles")
    for child in list(lines):
        lines.remove(child)
    records = shapes.find("shapeRecords")
    for child in list(records):
        records.remove(child)
    xs, ys = [], []
    for colour, edges in paths:
        index = colours.index(colour) + 1
        px = py = 0
        for edge in edges:
            if edge[0] == "move":
                px, py = edge[1], edge[2]
                ET.SubElement(records, "item", {
                    "type": "StyleChangeRecord", "stateMoveTo": "true", "moveBits": str(bits(px, py)),
                    "moveDeltaX": str(px), "moveDeltaY": str(py), "stateFillStyle0": "false",
                    "stateFillStyle1": "true", "fillStyle1": str(index), "stateLineStyle": "false",
                    "stateNewStyles": "false"})
            elif edge[0] == "line":
                dx, dy = edge[1], edge[2]
                if dx == 0 and dy == 0:
                    continue
                attrs = {"type": "StraightEdgeRecord", "numBits": str(bits(dx, dy)),
                         "generalLineFlag": str(bool(dx and dy)).lower()}
                if dx and dy:
                    attrs.update(deltaX=str(dx), deltaY=str(dy))
                elif dx:
                    attrs.update(vertLineFlag="false", deltaX=str(dx))
                else:
                    attrs.update(vertLineFlag="true", deltaY=str(dy))
                ET.SubElement(records, "item", attrs)
                px, py = px + dx, py + dy
            else:
                cx, cy, ax, ay = edge[1:]
                if (cx, cy, ax, ay) == (0, 0, 0, 0):
                    continue
                ET.SubElement(records, "item", {
                    "type": "CurvedEdgeRecord", "numBits": str(bits(cx, cy, ax, ay)), "controlDeltaX": str(cx),
                    "controlDeltaY": str(cy), "anchorDeltaX": str(ax), "anchorDeltaY": str(ay)})
                px, py = px + cx + ax, py + cy + ay
            xs.append(px)
            ys.append(py)
    ET.SubElement(records, "item", {"type": "EndShapeRecord", "endOfShape": "0"})
    bounds = tag.find("shapeBounds")
    for key, value in (("Xmin", min(xs)), ("Xmax", max(xs)), ("Ymin", min(ys)), ("Ymax", max(ys))):
        bounds.set(key, str(value))
    bounds.set("nbits", str(bits(min(xs), max(xs), min(ys), max(ys))))


STATE = ("stateMoveTo", "stateFillStyle0", "stateFillStyle1", "stateLineStyle", "stateNewStyles",
         "fillStyle0", "fillStyle1", "lineStyle", "moveDeltaX", "moveDeltaY")


def read_shape(tag: ET.Element) -> list[tuple]:
    """Everything that decides what a shape is, as plain tuples, for the read-back check."""
    shapes = tag.find("shapes")
    bounds = tag.find("shapeBounds")
    out = [("bounds", *(bounds.get(k) for k in ("Xmin", "Xmax", "Ymin", "Ymax"))),
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
            out.append(("line", record.get("deltaX", "0"), record.get("deltaY", "0")))
        elif kind == "CurvedEdgeRecord":
            out.append(("curve", record.get("controlDeltaX"), record.get("controlDeltaY"),
                        record.get("anchorDeltaX"), record.get("anchorDeltaY")))
        else:
            out.append((kind,))
    return out


# ------------------------------------------------------------------ the bytes: tags and classes
def tags(body: bytes) -> list[tuple[int, int, int, bytes]]:
    """Top-level tags of a body (after the 8-byte file header) as (code, tag start, contents
    start, contents); swf_bitmaps.tags does the walking."""
    out, p = [], 0
    for code, header, contents in swf_bitmaps.tags(body):
        if code != -1:
            out.append((code, p, p + len(header), contents))
        p += len(header) + len(contents)
    return out


def sprite_inner(contents: bytes) -> list[tuple[int, int, int, bytes]]:
    """The tags inside a DefineSprite's contents (after its id and frame count), with offsets
    into those contents; swf_bitmaps.tags wants a frame header, so it gets a blank one."""
    return [(code, s - 1, c - 1, inner) for code, s, c, inner in tags(bytes(5) + contents[4:])]


def char_id(code: int, contents: bytes) -> int | None:
    return struct.unpack_from("<H", contents)[0] if code in DEFINES else None


def exports(body: bytes) -> dict[str, int]:
    out = {}
    for code, _, _, c in tags(body):
        if code == EXPORT:
            q = 2
            for _ in range(struct.unpack_from("<H", c)[0]):
                ident, end = struct.unpack_from("<H", c, q)[0], c.index(b"\0", q + 2)
                out[c[q + 2:end].decode("latin1")] = ident
                q = end + 1
    return out


def class_tag(body: bytes, name: str) -> tuple[int, int, bytes]:
    """(tag index, contents offset in body, contents) of the DoInitAction holding an exported class."""
    ident = exports(body).get(name)
    for i, (code, _, cstart, c) in enumerate(tags(body)):
        if code == INIT_ACTION and struct.unpack_from("<H", c)[0] == ident:
            return i, cstart, c
    raise SystemExit(f"no class {name}: not the file this tool was made for")


def as2_double(raw: bytes) -> float:
    """A double as ActionScript 2 pushes it: the two 32-bit halves of the IEEE number swapped."""
    return struct.unpack("<d", raw[4:8] + raw[0:4])[0]


def as2_double_bytes(value: float) -> bytes:
    raw = struct.pack("<d", value)
    return raw[4:8] + raw[0:4]


def pushes(actions: bytes) -> list[tuple[int, str, object]]:
    """(offset of the value inside `actions`, kind, value) for every Push item, constant pool
    names resolved ("const"); ("op", opcode) for every other action, so a pattern can require
    what comes between and after the pushes; ("func", (name, body start, body end)) for a
    function definition, so a pattern can be required to lie inside one method (a class method
    is an anonymous function assigned to a member: its name is the constant pushed before it)."""
    pool, p, rows = [], 0, []
    while p < len(actions) and actions[p]:
        op = actions[p]
        p += 1
        if op < 0x80:
            rows.append((p - 1, "op", op))
            continue
        length = struct.unpack_from("<H", actions, p)[0]
        start = p + 2
        p = start + length
        data = actions[start:p]
        if op == 0x88:  # ConstantPool
            pool, q = [], 2
            for _ in range(struct.unpack_from("<H", data)[0]):
                e = data.index(b"\0", q)
                pool.append(data[q:e].decode("latin1"))
                q = e + 1
            continue
        if op in (0x9B, 0x8E):  # DefineFunction / DefineFunction2: the body's actions follow inline
            e = data.index(b"\0")
            fname = data[:e].decode("latin1")
            q = e + 1
            params = struct.unpack_from("<H", data, q)[0]
            q += 2 if op == 0x9B else 5  # DefineFunction2: register count and flags too
            for _ in range(params):
                if op == 0x8E:
                    q += 1
                q = data.index(b"\0", q) + 1
            size = struct.unpack_from("<H", data, q)[0]
            rows.append((start - 3, "func", (fname, p, p + size)))
            continue
        if op != 0x96:  # not a Push
            rows.append((start - 3, "op", op))
            continue
        q = 0
        while q < len(data):
            kind = data[q]
            q += 1
            if kind == 0:
                e = data.index(b"\0", q)
                rows.append((start + q, "str", data[q:e].decode("latin1")))
                q = e + 1
            elif kind == 1:
                rows.append((start + q, "float", struct.unpack_from("<f", data, q)[0]))
                q += 4
            elif kind in (2, 3):
                rows.append((start + q, "null" if kind == 2 else "undefined", None))
            elif kind == 4:
                rows.append((start + q, "reg", data[q]))
                q += 1
            elif kind == 5:
                rows.append((start + q, "bool", data[q]))
                q += 1
            elif kind == 6:
                rows.append((start + q, "double", as2_double(data[q:q + 8])))
                q += 8
            elif kind == 7:
                rows.append((start + q, "int", struct.unpack_from("<i", data, q)[0]))
                q += 4
            elif kind == 8:
                rows.append((start + q, "const", pool[data[q]]))
                q += 1
            elif kind == 9:
                rows.append((start + q, "const", pool[struct.unpack_from("<H", data, q)[0]]))
                q += 2
            else:
                raise SystemExit(f"unknown push type {kind}: not the file this tool was made for")
    return rows


def class_pushes(body: bytes, name: str) -> list[tuple[int, str, object]]:
    """A class's pushes (and other actions) with offsets into the whole body."""
    _, cstart, contents = class_tag(body, name)
    base = cstart + 2
    return [(off + base, kind, (value[0], value[1] + base, value[2] + base) if kind == "func" else value)
            for off, kind, value in pushes(contents[2:])]


def method_range(rows: list[tuple[int, str, object]], method: str) -> tuple[int, int]:
    """The body offsets of the one method with this name: the anonymous function defined right
    after the constant `method` is pushed."""
    found = [value[1:] for (_, kind, value), before in zip(rows[1:], rows) if kind == "func" and before[1:] == ("const", method)]
    if len(found) != 1:
        raise SystemExit(f"method {method} defined {len(found)} times, not once: not the file this tool was made for")
    return found[0]


def check_class(ford_body: bytes, our_body: bytes, name: str, slots: list[tuple[int, str]]) -> int:
    """The class named differs from Ford's only inside these (body offset, kind) number slots;
    same length. Returns the class sprite's id."""
    _, _, a = class_tag(ford_body, name)
    _, cs, b = class_tag(our_body, name)
    if len(a) != len(b):
        raise SystemExit(f"the class {name} changed its length")
    mask = bytearray(len(a))
    for off, kind in slots:
        for j in range(off - cs, off - cs + (4 if kind == "int" else 8)):
            mask[j] = 1
    if any(x != y and not m for x, y, m in zip(a, b, mask)):
        raise SystemExit(f"the class {name} changed outside the intended numbers")
    return struct.unpack_from("<H", a)[0]


# ------------------------------------------------------------------ placements, bit for bit
class Bits:
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
        return self.pos + (1 if self.bit else 0)


def matrix_end(data: bytes, pos: int) -> int:
    b = Bits(data, pos)
    for _ in range(2):
        if b.read(1):
            n = b.read(5)
            b.read(n), b.read(n)
    n = b.read(5)
    b.read(n), b.read(n)
    return b.end()


def cxform_end(data: bytes, pos: int) -> int:
    b = Bits(data, pos)
    add, mult, n = b.read(1), b.read(1), b.read(4)
    for _ in range(4 * (add + mult)):
        b.read(n)
    return b.end()


def place_fields(code: int, contents: bytes) -> dict[str, object]:
    """A PlaceObject2/3 split into its fields: flags, depth, class, character, matrix, cxform,
    ratio, name, clip_depth, blend, cache, visible, background, clip_actions (absent ones left
    out). A filter list cannot be walked here and is refused."""
    flags = contents[0] | (contents[1] << 8 if code == PLACE3 else 0)
    p = 1 if code == PLACE2 else 2
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
        raise SystemExit("a placement with filters: not the file this tool was made for")
    for name, present, size in (("blend", flags & 0x0200, 1), ("cache", flags & 0x0400, 1),
                                ("visible", flags & 0x2000, 1), ("background", flags & 0x4000, 4)):
        if present:
            fields[name], p = contents[p:p + size], p + size
    if flags & 0x80:
        fields["clip_actions"] = contents[p:]
        p = len(contents)
    if p != len(contents):
        raise SystemExit("a placement with trailing bytes: not the file this tool was made for")
    return fields


TEXT_FLAGS = ("HasText", "WordWrap", "Multiline", "Password", "ReadOnly", "HasTextColor", "HasMaxLength", "HasFont",
              "HasFontClass", "AutoSize", "HasLayout", "NoSelect", "Border", "WasStatic", "HTML", "UseOutlines")


def rect_end(data: bytes, pos: int) -> int:
    b = Bits(data, pos)
    n = b.read(5)
    for _ in range(4):
        b.read(n)
    return b.end()


def text_fields(contents: bytes) -> dict[str, object]:
    """A DefineEditText split into its fields: id, bounds (raw), flags, fontId, fontClass,
    fontHeight, textColor, maxLength, layout (raw), variableName, initialText (absent ones left out)."""
    fields = {"id": contents[:2]}
    p = rect_end(contents, 2)
    fields["bounds"] = contents[2:p]
    flags = {name: (contents[p + i // 8] >> (7 - i % 8)) & 1 for i, name in enumerate(TEXT_FLAGS)}
    fields["flags"] = contents[p:p + 2]
    p += 2
    if flags["HasFont"]:
        fields["fontId"], p = contents[p:p + 2], p + 2
    if flags["HasFontClass"]:
        end = contents.index(b"\0", p) + 1
        fields["fontClass"], p = contents[p:end], end
    if flags["HasFont"]:
        fields["fontHeight"], p = contents[p:p + 2], p + 2
    if flags["HasTextColor"]:
        fields["textColor"], p = contents[p:p + 4], p + 4
    if flags["HasMaxLength"]:
        fields["maxLength"], p = contents[p:p + 2], p + 2
    if flags["HasLayout"]:
        fields["layout"], p = contents[p:p + 9], p + 9
    end = contents.index(b"\0", p) + 1
    fields["variableName"], p = contents[p:end], end
    if flags["HasText"]:
        end = contents.index(b"\0", p) + 1
        fields["initialText"], p = contents[p:end], end
    if p != len(contents):
        raise SystemExit("a text field with trailing bytes: not the file this tool was made for")
    return fields


def place_key(code: int, contents: bytes) -> tuple[int, str]:
    """(depth, name) of a placement; "" without a name."""
    f = place_fields(code, contents)
    return (struct.unpack("<H", f["depth"])[0], f.get("name", b"").rstrip(b"\0").decode("latin1"))


def same_but(code: int, x: bytes, y: bytes, allowed: tuple[str, ...]) -> bool:
    """Two placements equal in every field but the allowed ones (a matrix or blend mode may
    also appear or disappear, so their flags are ignored too)."""
    a, b = place_fields(code, x), place_fields(code, y)
    for fields in (a, b):
        for name in allowed:
            fields.pop(name, None)
        if "blend" in allowed:
            fields["flags"] &= ~0x0200
        if "matrix" in allowed:
            fields["flags"] &= ~0x04
    return a == b


# ------------------------------------------------------------------ splicing and checking
def splice(original: bytes, rebuilt: bytes, defines: set[tuple[int, int]],
           main_places: set[tuple[int, str]], sprite_places: dict[int, set[tuple[int, str]]]) -> bytes:
    """The car's body with only these taken from FFDec's rebuilt body: whole Define tags by
    (code, id); main-timeline placements by (depth, name); inside a sprite by id, only the
    placements named by (depth, name), the sprite's other tags the car's own."""
    a, b = swf_bitmaps.tags(original), swf_bitmaps.tags(rebuilt)
    if [t[0] for t in a] != [t[0] for t in b]:
        raise SystemExit("FFDec changed the list of tags")
    parts = []
    for (code, h, c), (_, h2, c2) in zip(a, b):
        ident = char_id(code, c) if code != -1 else None
        if (code, ident) in defines:
            parts.append(h2 + c2)
        elif code in (PLACE2, PLACE3) and place_key(code, c) in main_places:
            parts.append(h2 + c2)
        elif code == SPRITE and ident in sprite_places:
            inner, inner2 = sprite_inner(c), sprite_inner(c2)
            if [t[0] for t in inner] != [t[0] for t in inner2]:
                raise SystemExit(f"FFDec changed the list of tags inside sprite {ident}")
            body = [c[:4]]
            for (k, s, e, ic), (_, s2, e2, ic2) in zip(inner, inner2):
                take = k in (PLACE2, PLACE3) and place_key(k, ic) in sprite_places[ident]
                body.append(c2[s2:e2 + len(ic2)] if take else c[s:e + len(ic)])
            new = b"".join(body)
            parts.append(struct.pack("<HI", (SPRITE << 6) | 0x3F, len(new)) + new)
        else:
            parts.append(h + c)
    return b"".join(parts)


def flat_keys(body: bytes) -> list[tuple[tuple, bytes]]:
    """(key, contents) for every tag, sprites expanded: a Define tag by kind and id, a placement
    by its container, kind, depth and name, anything else by kind and position."""
    out = []
    for i, (code, _, _, c) in enumerate(tags(body)):
        ident = char_id(code, c)
        kind = NAMES.get(code, str(code))
        if code in (PLACE2, PLACE3):
            out.append((("main", kind, *place_key(code, c)), c))
        else:
            out.append(((kind, ident if ident is not None else i), c))
        if code == SPRITE:
            for j, (k, _, _, ic) in enumerate(sprite_inner(c)):
                ikind = NAMES.get(k, str(k))
                key = (f"sprite{ident}", ikind, *place_key(k, ic)) if k in (PLACE2, PLACE3) else (f"sprite{ident}", ikind, j)
                out.append((key, ic))
    return out


def check_length(ford: bytes, ours: bytes, name: str = "the result") -> None:
    """A result must not be as long as the car's file: s2am refuses a start-up file of Ford's
    length, and the car's own import checks a copy by its size alone (MortScript has no hash),
    so a copy that failed on a locked file would pass for a success."""
    if len(ours) == len(ford):
        raise SystemExit(f"{name} is as long as the car's file ({len(ford)} bytes): the car could not tell a failed copy")


def check(ford: bytes, ours: bytes, allowed: set[tuple], place_allowed: tuple[str, ...] = ("matrix",),
          text_allowed: dict[int, set[str]] | None = None) -> list[tuple]:
    """Header, frame header, declared length and the list of tags unchanged; every changed tag
    is in `allowed` (keys as flat_keys makes them; a sprite's own key is implied by a changed
    child, but its id and frame count must stay); every changed placement differs only in the
    allowed fields; every changed text field only in the fields `text_allowed` names for its id.
    Returns the changed keys."""
    (ha, ba), (hb, bb) = swf_bitmaps.unpack(ford), swf_bitmaps.unpack(ours)
    fa, fb = swf_bitmaps.tags(ba), swf_bitmaps.tags(bb)
    if ha != hb or fa[0] != fb[0]:
        raise SystemExit("the header changed")
    for data, body in ((ford, ba), (ours, bb)):
        if struct.unpack_from("<I", data, 4)[0] != 8 + len(body):
            raise SystemExit("the file's length in its header is wrong")
    ka, kb = flat_keys(ba), flat_keys(bb)
    if [k for k, _ in ka] != [k for k, _ in kb]:
        raise SystemExit("the list of tags changed")
    changed = [(k, x, y) for (k, x), (_, y) in zip(ka, kb) if x != y]
    implied = {("DefineSprite", int(k[0][6:])) for k, _, _ in changed if k[0].startswith("sprite")}
    bad = [k for k, _, _ in changed if k not in allowed and k not in implied]
    if bad:
        raise SystemExit(f"tags changed that should not have: {bad}")
    for k, x, y in changed:
        if len(k) == 4 and k[1].startswith("PlaceObject"):
            code = PLACE2 if k[1] == "PlaceObject2" else PLACE3
            if not same_but(code, x, y, place_allowed):
                raise SystemExit(f"placement {k} changed in more than {place_allowed}")
        elif k[0] == "DefineSprite" and x[:4] != y[:4]:
            raise SystemExit(f"sprite {k[1]} changed its id or frame count")
        elif k[0] == "DefineEditText":
            a, b = text_fields(x), text_fields(y)
            wrong = [f for f in set(a) | set(b) if a.get(f) != b.get(f) and f not in (text_allowed or {}).get(k[1], set())]
            if wrong:
                raise SystemExit(f"text field {k[1]} changed in {sorted(wrong)}, which was not intended")
    return [k for k, _, _ in changed]
