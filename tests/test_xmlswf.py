"""xmlswf writes shapes FFDec can read back, splits placements into their fields, splices only
the intended tags from a rebuilt file into the original, and lets only allowed tags differ.

Made here (no Ford file): small but valid Flash files (bit-packed rectangles and matrices,
PlaceObject2/3 with names and blend modes, a sprite, a class with a constant pool and pushes)
and XML elements shaped like FFDec's. The other Home tests import these builders. The real
round trip through FFDec in Docker is the build's own.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import swf_bitmaps  # noqa: E402
import xmlswf as X  # noqa: E402


# ---------------------------------------------------------------- the pieces of a Flash file
def tag(code, contents):
    return struct.pack("<HI", (code << 6) | 0x3F, len(contents)) + contents


def bitfield(fields):
    """(value, bit count) pairs packed most significant bit first, padded to whole bytes."""
    text = "".join(format(value & ((1 << count) - 1), f"0{count}b") for value, count in fields if count)
    text += "0" * (-len(text) % 8)
    return int(text, 2).to_bytes(len(text) // 8, "big") if text else b""


def rect(xmin=0, xmax=0, ymin=0, ymax=0):
    count = max(abs(v) for v in (xmin, xmax, ymin, ymax)).bit_length() + 1 if any((xmin, xmax, ymin, ymax)) else 0
    return bitfield([(count, 5), (xmin, count), (xmax, count), (ymin, count), (ymax, count)])


def matrix(tx=0, ty=0, scale=None, rotate=None, bits=16):
    """A MATRIX: scale and rotation (16.16 fixed point) when given, then the translation in
    twips, `bits` wide."""
    fields = []
    for pair in (scale, rotate):
        fields += [(0, 1)] if pair is None else [(1, 1), (20, 5), (pair[0], 20), (pair[1], 20)]
    fields += [(bits, 5), (tx, bits), (ty, bits)]
    return bitfield(fields)


def shape(ident, code=2, bounds=(0, 0, 0, 0)):
    """A DefineShape or DefineShape3: its bounds, no fills, no lines, no edges."""
    return tag(code, struct.pack("<H", ident) + rect(*bounds) + b"\x00\x00\x00\x00")


def edit_text(ident, extra=b"", font=(5, 400), colour=(255, 255, 255, 255), text=b"", variable=b"", align=2):
    """A DefineEditText with a font, a colour, a layout, a variable name and an initial text."""
    flags = bytes([0x80 | 0x04 | 0x01, 0x20 | 0x02])  # HasText, HasTextColor, HasFont; HasLayout, HTML
    return tag(37, struct.pack("<H", ident) + rect() + flags + struct.pack("<HH", *font) + bytes(colour)
               + bytes([align]) + struct.pack("<HHHh", 0, 0, 0, 40) + variable + b"\0" + text + b"\0" + extra)


def place2(depth, char, m=matrix(), name=None):
    flags = 0x06 | (0x20 if name else 0)
    return tag(26, bytes([flags]) + struct.pack("<HH", depth, char) + m + (name + b"\0" if name else b""))


def place3(depth, char, m=matrix(), blend=4, name=None):
    flags = (0x06 | (0x20 if name else 0), 0x02 if blend is not None else 0)
    return tag(70, bytes(flags) + struct.pack("<HH", depth, char) + m + (name + b"\0" if name else b"")
               + (bytes([blend]) if blend is not None else b""))


def sprite(ident=63, frames=1, inner=None):
    inner = (place3(1, 55, matrix(-6, -3484)) + place3(3, 57, matrix(-8000, -8)) + place2(5, 59, matrix(30, 40), b"label")
             if inner is None else inner)
    return tag(39, struct.pack("<HH", ident, frames) + inner + tag(1, b"") + tag(0, b""))


def push(value):
    """One pushed item: an int, a double in ActionScript 2's word order, a register, or a
    constant pool index."""
    if isinstance(value, float):
        return b"\x06" + X.as2_double_bytes(value)
    if isinstance(value, tuple):  # ("reg", n) or ("const", n)
        return (b"\x04" if value[0] == "reg" else b"\x08") + bytes([value[1]])
    return b"\x07" + struct.pack("<i", value)


def actions(pool, *pushes, tail=b""):
    """A ConstantPool, one Push of all the items given, then `tail` actions and End."""
    names = b"".join(n.encode() + b"\0" for n in pool)
    items = b"".join(push(v) for v in pushes)
    return (b"\x88" + struct.pack("<HH", len(names) + 2, len(pool)) + names
            + b"\x96" + struct.pack("<H", len(items)) + items + tail + b"\x00")


def flash(tags_between=b"", class_id=67, class_name=b"__Packages.Demo", code=None, version=b"\x0a", length=None):
    """A file: stage, the tags given, an export of one class, its DoInitAction, a frame, End."""
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)
    export = struct.pack("<HH", 1, class_id) + class_name + b"\0"
    code = actions(["a", "b"], ("const", 0), 5, 0.5) if code is None else code
    body = stage + tags_between + tag(56, export) + tag(59, struct.pack("<H", class_id) + code) + tag(1, b"") + tag(0, b"")
    return b"FWS" + version + struct.pack("<I", 8 + len(body) if length is None else length) + body


def skeleton(ident):
    """A DefineShapeTag in FFDec's XML form with one gradient fill and no records."""
    return ET.fromstring(
        f'<item type="DefineShapeTag" shapeId="{ident}"><shapeBounds Xmin="0" Xmax="15" Ymin="0" Ymax="6968" nbits="14"/>'
        '<shapes numFillBits="1" numLineBits="0"><fillStyles><fillStyles><item type="FILLSTYLE" fillStyleType="16"/>'
        '</fillStyles></fillStyles><lineStyles><lineStyles><item type="LINESTYLE"/></lineStyles></lineStyles>'
        '<shapeRecords><item type="EndShapeRecord"/></shapeRecords></shapes></item>')


def closes(edges):
    """Where a path ends relative to where it started, and its signed area (y down: clockwise > 0)."""
    x = y = 0
    area = 0
    for edge in edges:
        if edge[0] == "move":
            start = x, y = edge[1], edge[2]
            continue
        nx, ny = (x + edge[1], y + edge[2]) if edge[0] == "line" else (x + edge[1] + edge[3], y + edge[2] + edge[4])
        area += x * ny - nx * y
        x, y = nx, ny
    return (x - start[0], y - start[1]), area / 2


class Shapes(unittest.TestCase):
    def test_rectangles_polygons_and_circles_close_and_run_clockwise(self):
        for edges in (X.rounded_rect(8, 56, 388, 180, 12), X.polygon([(0, 0), (10, 0), (10, 10), (0, 10)]), X.circle(5, 5, 3)):
            gap, area = closes(edges)
            self.assertEqual(gap, (0, 0))
            self.assertGreater(area, 0)
        self.assertEqual(X.rounded_rect(8, 56, 388, 180, 12)[0], ("move", (8 + 12) * 20, 56 * 20))
        self.assertEqual(len(X.circle(0, 0, 1, 8)), 9)

    def test_shape_xml_writes_one_fill_per_colour_the_records_the_bounds_and_no_lines(self):
        element = skeleton(54)
        red, blue = (200, 0, 0), (0, 0, 200)
        X.shape_xml(element, [(red, X.rounded_rect(10, 10, 100, 50, 5)), (blue, X.polygon([(0, 0), (4, 0), (4, 4)])),
                              (red, X.polygon([(1, 1), (2, 1), (2, 2)]))])
        shapes = element.find("shapes")
        fills = shapes.find("fillStyles").find("fillStyles")
        self.assertEqual([(f.get("fillStyleType"), f.find("color").get("red")) for f in fills], [("0", "200"), ("0", "0")])
        self.assertEqual((shapes.get("numFillBits"), shapes.get("numLineBits")), ("2", "0"))
        self.assertEqual(len(shapes.find("lineStyles").find("lineStyles")), 0)
        records = shapes.find("shapeRecords")
        self.assertEqual([r.get("fillStyle1") for r in records if r.get("type") == "StyleChangeRecord"], ["1", "2", "1"])
        self.assertEqual(records[-1].get("type"), "EndShapeRecord")
        self.assertEqual([records[1].get("generalLineFlag"), records[1].get("vertLineFlag")], ["false", "false"])
        bounds = element.find("shapeBounds")
        self.assertEqual([bounds.get(k) for k in ("Xmin", "Xmax", "Ymin", "Ymax")], ["0", "2200", "0", "1200"])
        self.assertEqual(X.read_shape(element)[3:5], [("fill", "0", ("200", "0", "0", None)), ("fill", "0", ("0", "0", "200", None))])

    def test_read_shape_tells_a_moved_record_from_the_written_one(self):
        a, b = skeleton(1), skeleton(1)
        X.shape_xml(a, [((1, 2, 3), X.polygon([(0, 0), (4, 0), (4, 4)]))])
        X.shape_xml(b, [((1, 2, 3), X.polygon([(0, 0), (4, 0), (4, 5)]))])
        self.assertNotEqual(X.read_shape(a), X.read_shape(b))
        self.assertEqual(X.read_shape(a), X.read_shape(a))


class Matrices(unittest.TestCase):
    def test_set_matrix_writes_twips_and_a_scale_or_drops_it(self):
        place = ET.fromstring('<item type="PlaceObject2Tag"><matrix hasScale="true" scaleX="0.9" scaleY="0.9" nScaleBits="18" '
                              'hasRotate="false" translateX="100" translateY="200"/></item>')
        X.set_matrix(place, 4.25, None)
        self.assertEqual(X.matrix_values(place)[:4], ("85", "200", "true", "0.9"))
        X.set_matrix(place, None, -1000, scale=(1.25, 0.0))
        self.assertEqual(X.matrix_values(place)[:5], ("85", "-20000", "true", "1.25", "0.0"))
        place.find("matrix").set("hasRotate", "true")
        place.find("matrix").set("rotateSkew0", "0.1")
        X.set_matrix(place, 402, 240, keep_scale=False)
        self.assertEqual(X.matrix_values(place), ("8040", "4800", "false", None, None, "false", None, None))
        bare = ET.fromstring('<item type="PlaceObject2Tag"/>')
        X.set_matrix(bare, 1, 2)
        self.assertEqual((bare.get("placeFlagHasMatrix"), X.matrix_values(bare)[:3]), ("true", ("20", "40", None)))


class Placements(unittest.TestCase):
    def test_splits_a_placement_into_its_fields(self):
        fields = X.place_fields(70, place3(1, 55, matrix(-6, -3484), 4, b"x")[6:])
        self.assertEqual(fields, {"flags": 0x0226, "depth": struct.pack("<H", 1), "character": struct.pack("<H", 55),
                                  "matrix": matrix(-6, -3484), "name": b"x\0", "blend": b"\x04"})
        self.assertEqual(X.place_fields(26, place2(6, 63, matrix(8040, 4800, scale=(65536, 65461)), b"n")[6:])["matrix"],
                         matrix(8040, 4800, scale=(65536, 65461)))
        self.assertEqual(X.place_key(26, place2(6, 63, name=b"mcSmartCorners")[6:]), (6, "mcSmartCorners"))
        self.assertEqual(X.place_key(70, place3(3, 57)[6:]), (3, ""))
        with self.assertRaises(SystemExit):  # a filter list, or bytes after the fields
            X.place_fields(70, bytes([0x06, 0x01]) + struct.pack("<HH", 1, 2) + matrix() + b"\x00")
        with self.assertRaises(SystemExit):
            X.place_fields(26, place2(1, 2)[6:] + b"\x00")

    def test_same_but_allows_only_the_named_fields(self):
        a = place3(1, 55, matrix(-6, -3484), 4)[6:]
        moved = place3(1, 55, matrix(-8000, -4800), None)[6:]
        renamed = place3(1, 55, matrix(-6, -3484), 4, b"x")[6:]
        self.assertTrue(X.same_but(70, a, moved, ("matrix", "blend")))
        self.assertFalse(X.same_but(70, a, moved, ("matrix",)))
        self.assertFalse(X.same_but(70, a, renamed, ("matrix", "blend")))


class Classes(unittest.TestCase):
    def test_a_double_is_written_and_read_with_its_halves_swapped(self):
        for value in (0.0, 2.0, 245.0, -1.5, 0.1):
            self.assertEqual(X.as2_double(X.as2_double_bytes(value)), value)
        self.assertEqual(X.as2_double_bytes(2.0), bytes.fromhex("0000004000000000"))
        self.assertNotEqual(X.as2_double(struct.pack("<d", 2.0)), 2.0)

    def test_lists_pushes_with_their_kinds_and_offsets_into_the_body(self):
        code = actions(["icons", "_x"], ("const", 0), ("const", 1), 200, ("reg", 4), 0.5, tail=b"\x42")
        data = flash(code=code)
        body = swf_bitmaps.unpack(data)[1]
        rows = X.class_pushes(body, "__Packages.Demo")
        self.assertEqual([r[1:] for r in rows], [("const", "icons"), ("const", "_x"), ("int", 200), ("reg", 4), ("double", 0.5),
                                                 ("op", X.INIT_ARRAY)])
        self.assertEqual(body[rows[-1][0]], X.INIT_ARRAY)
        off = rows[2][0]
        self.assertEqual(struct.unpack_from("<i", body, off)[0], 200)
        self.assertEqual(X.as2_double(body[rows[4][0]:rows[4][0] + 8]), 0.5)
        self.assertEqual(X.class_tag(body, "__Packages.Demo")[0], len(swf_bitmaps.tags(body)) - 4)
        with self.assertRaises(SystemExit):
            X.class_tag(body, "__Packages.Other")

    def test_check_class_allows_only_the_named_slots(self):
        code = actions(["icons", "_x"], ("const", 0), ("const", 1), 200, ("reg", 4), 0.5)
        ford = swf_bitmaps.unpack(flash(code=code))[1]
        rows = X.class_pushes(ford, "__Packages.Demo")
        ours = bytearray(ford)
        struct.pack_into("<i", ours, rows[2][0], 385)
        ours[rows[4][0]:rows[4][0] + 8] = X.as2_double_bytes(1.0)
        slots = [(rows[2][0], "int"), (rows[4][0], "double")]
        self.assertEqual(X.check_class(ford, bytes(ours), "__Packages.Demo", slots), 67)
        with self.assertRaises(SystemExit):
            X.check_class(ford, bytes(ours), "__Packages.Demo", slots[:1])
        with self.assertRaises(SystemExit):
            X.check_class(ford, swf_bitmaps.unpack(flash(code=code + b"\x00"))[1], "__Packages.Demo", slots)


class Splicing(unittest.TestCase):
    def between(self, **kw):
        values = dict(a=shape(7, bounds=(0, 100, 0, 100)), b=shape(8, bounds=(0, 50, 0, 50)), text=edit_text(12),
                      spr=sprite(), main=place2(6, 63, matrix(8040, 4800), b"mcSmartCorners"), other=place2(9, 8, matrix(1, 1), b"o"))
        values.update(kw)
        return b"".join(values.values())

    def test_takes_only_the_wanted_defines_main_placements_and_sprite_placements(self):
        original = swf_bitmaps.unpack(flash(self.between()))[1]
        rebuilt_sprite = sprite(inner=place3(1, 55, matrix(-8000, -4800), None) + place3(3, 57, matrix(-8000, -4800), None)
                                + place2(5, 59, matrix(31, 41), b"label"))
        rebuilt = swf_bitmaps.unpack(flash(self.between(
            a=shape(7, bounds=(0, 101, 0, 100)), b=shape(8, bounds=(0, 51, 0, 50)), text=edit_text(12, b"x"), spr=rebuilt_sprite,
            main=place2(6, 63, matrix(8000, 4800), b"mcSmartCorners"), other=place2(9, 8, matrix(2, 2), b"o"))))[1]
        spliced = X.splice(original, rebuilt, defines={(2, 7), (37, 12)}, main_places={(6, "mcSmartCorners")},
                           sprite_places={63: {(1, "")}})
        keys = dict(X.flat_keys(spliced))
        want = dict(X.flat_keys(rebuilt))
        keep = dict(X.flat_keys(original))
        for key in (("DefineShape", 7), ("DefineEditText", 12), ("main", "PlaceObject2", 6, "mcSmartCorners"), ("sprite63", "PlaceObject3", 1, "")):
            self.assertEqual(keys[key], want[key], key)
        for key in (("DefineShape", 8), ("main", "PlaceObject2", 9, "o"), ("sprite63", "PlaceObject3", 3, ""), ("sprite63", "PlaceObject2", 5, "label")):
            self.assertEqual(keys[key], keep[key], key)
        with self.assertRaises(SystemExit):  # another list of tags
            X.splice(original, swf_bitmaps.unpack(flash(self.between(other=b"")))[1], set(), set(), {})

    def test_check_passes_allowed_changes_and_rejects_the_rest(self):
        old = flash(self.between())
        moved = flash(self.between(main=place2(6, 63, matrix(8000, 4800), b"mcSmartCorners")))
        allowed = {("main", "PlaceObject2", 6, "mcSmartCorners")}
        self.assertEqual(X.check(old, moved, allowed), [("main", "PlaceObject2", 6, "mcSmartCorners")])
        self.assertEqual(X.check(old, old, set()), [])
        inner = flash(self.between(spr=sprite(inner=place3(1, 55, matrix(-8000, -4800), None) + place3(3, 57, matrix(-8000, -8))
                                                    + place2(5, 59, matrix(30, 40), b"label"))))
        self.assertEqual(X.check(old, inner, {("sprite63", "PlaceObject3", 1, "")}, ("matrix", "blend")),
                         [("DefineSprite", 63), ("sprite63", "PlaceObject3", 1, "")])
        for why, wrong, allowed_keys, fields in (
                ("a tag not allowed", self.between(a=shape(7, bounds=(0, 101, 0, 100))), set(), ("matrix",)),
                ("a blend mode when only the matrix may change", self.between(spr=sprite(inner=place3(1, 55, matrix(-6, -3484), None)
                 + place3(3, 57, matrix(-8000, -8)) + place2(5, 59, matrix(30, 40), b"label"))), {("sprite63", "PlaceObject3", 1, "")}, ("matrix",)),
                ("a renamed placement", self.between(main=place2(6, 63, matrix(8040, 4800), b"mcSmartCorner2")), allowed, ("matrix",)),
                ("a tag more", self.between(other=place2(9, 8, matrix(1, 1), b"o") + place2(10, 8)), allowed, ("matrix",))):
            with self.subTest(why=why), self.assertRaises(SystemExit):
                X.check(old, flash(wrong), allowed_keys, fields)
        with self.assertRaises(SystemExit):
            X.check(old, flash(self.between(), version=b"\x0b"), set())
        with self.assertRaises(SystemExit):
            X.check(old, flash(self.between(), length=8), set())

    def test_check_length_refuses_a_result_as_long_as_the_original(self):
        old = flash(self.between())
        with self.assertRaisesRegex(SystemExit, "as long as the car's file"):
            X.check_length(old, flash(self.between(main=place2(6, 63, matrix(8000, 4800), b"mcSmartCorners"))), "Nav")
        X.check_length(old, old + b"\x00")
        X.check_length(old, old[:-1])

    def test_check_lets_a_text_field_change_only_in_its_allowed_fields(self):
        old = flash(self.between())
        bigger = flash(self.between(text=edit_text(12, font=(5, 600), text=b"<p>x</p>")))
        self.assertEqual(X.check(old, bigger, {("DefineEditText", 12)}, text_allowed={12: {"fontHeight", "initialText"}}),
                         [("DefineEditText", 12)])
        for why, wrong, allowed in (("the font id", edit_text(12, font=(6, 600)), {"fontHeight"}),
                                    ("the colour", edit_text(12, colour=(1, 2, 3, 255)), {"fontHeight"}),
                                    ("the variable name", edit_text(12, variable=b"v", font=(5, 600)), {"fontHeight"}),
                                    ("nothing allowed", edit_text(12, font=(5, 600)), set())):
            with self.subTest(why=why), self.assertRaisesRegex(SystemExit, "text field 12 changed in"):
                X.check(old, flash(self.between(text=wrong)), {("DefineEditText", 12)}, text_allowed={12: allowed})
        fields = X.text_fields(edit_text(12, variable=b"v", text=b"t")[6:])
        self.assertEqual((fields["fontId"], fields["fontHeight"], fields["variableName"], fields["initialText"], fields["layout"][0]),
                         (struct.pack("<H", 5), struct.pack("<H", 400), b"v\0", b"t\0", 2))
        with self.assertRaises(SystemExit):
            X.text_fields(edit_text(12)[6:] + b"\0")

    def test_check_keeps_a_changed_sprites_id_and_frame_count(self):
        old = flash(self.between())
        inner = place3(1, 55, matrix(-8000, -4800), None) + place3(3, 57, matrix(-8000, -8)) + place2(5, 59, matrix(30, 40), b"label")
        allowed = {("sprite63", "PlaceObject3", 1, "")}
        X.check(old, flash(self.between(spr=sprite(inner=inner))), allowed, ("matrix", "blend"))
        with self.assertRaisesRegex(SystemExit, "frame count"):
            X.check(old, flash(self.between(spr=sprite(frames=99, inner=inner))), allowed, ("matrix", "blend"))
        with self.assertRaisesRegex(SystemExit, "the list of tags changed"):
            X.check(old, flash(self.between(spr=sprite(ident=64, inner=inner))), allowed, ("matrix", "blend"))

    def test_pushes_scope_a_method_and_list_a_function_body(self):
        body = b"\x96\x02\x00\x08\x00" + b"\x0b"
        function = b"\x8e" + struct.pack("<H", 8) + b"\0" + struct.pack("<HBHH", 0, 0, 0, len(body))
        pool = b"m\0n\0"
        code = (b"\x88" + struct.pack("<HH", len(pool) + 2, 2) + pool + b"\x96\x02\x00\x08\x01" + b"\x96\x02\x00\x08\x00"
                + function + body + b"\x4f\x00")
        rows = X.pushes(code)
        self.assertEqual([r[1:] for r in rows][:3], [("const", "n"), ("const", "m"), ("func", ("", rows[2][2][1], rows[2][2][2]))])
        self.assertEqual([r[1:] for r in rows][3:], [("const", "m"), ("op", 0x0B), ("op", 0x4F)])
        start, end = X.method_range(rows, "m")
        self.assertTrue(start <= rows[3][0] < end)
        with self.assertRaises(SystemExit):
            X.method_range(rows, "n")

    def test_sprite_inner_offsets_point_at_the_inner_tags(self):
        contents = sprite()[6:]
        for code, start, cstart, inner in X.sprite_inner(contents):
            self.assertEqual(contents[cstart:cstart + len(inner)], inner)
            self.assertEqual(struct.unpack_from("<H", contents, start)[0] >> 6, code)
        self.assertEqual([t[0] for t in X.sprite_inner(contents)], [70, 70, 26, 1, 0])


if __name__ == "__main__":
    unittest.main()
