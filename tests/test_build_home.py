"""build_home changes the eight corner numbers in place, in Ford's class only, lets only the
intended tags differ, draws the grid and the headings as closed shapes, and reads its XML back.

Made here (no Ford file): a small but valid Flash file: a class Home whose init code sets the four
SC_* arrays exactly as Ford's compiler did (one Push of the name, y, x and the count 2, then
InitArray and SetMember; one number a double), the three shapes (real bounds, no edges),
mcSmartCorners with its two divider placements (bit-packed matrices, a blend mode) and a label,
its named placement on the main timeline, and one shape more; and an XML tree shaped like
FFDec's. The real round trip through FFDec in Docker is the build's own.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_home as build  # noqa: E402
import glyphs  # noqa: E402
import swf_bitmaps  # noqa: E402
import xmlswf as X  # noqa: E402
from test_xmlswf import closes, edit_text, matrix, place2, place3, push, shape, skeleton, tag  # noqa: E402

# a float marks the number the compiler stored as a double: SC_BTM_LEFT's x
FORD = {"SC_TOP_LEFT": (10, 40), "SC_TOP_RIGHT": (400, 40), "SC_BTM_RIGHT": (400, 235), "SC_BTM_LEFT": (0.0, 245)}
OURS = {"SC_TOP_LEFT": (2, 44), "SC_TOP_RIGHT": (398, 48), "SC_BTM_RIGHT": (400, 236), "SC_BTM_LEFT": (2.0, 236)}
NAME = b"mcSmartCorners"


def sprite(frames=1, dividers=(matrix(-6, -3484), matrix(-8000, -8)), blend=4, label=place2(5, 59, matrix(30, 40))):
    return tag(39, struct.pack("<HH", 63, frames) + place3(1, 55, dividers[0], blend) + place3(3, 57, dividers[1], blend)
               + label + tag(1, b"") + tag(0, b""))


def home(corners=FORD, names=tuple(FORD), member=b"\x4f", between=b""):
    """The class Home's init code: a constant pool, then NAME = [x, y] for each name, as Ford's
    compiler pushed it: one Push of a register, the name, y, x and 2; InitArray; SetMember."""
    pool = b"".join(n.encode() + b"\0" for n in FORD)
    code = b"\x88" + struct.pack("<HH", len(pool) + 2, len(FORD)) + pool
    for name in names:
        x, y = corners[name]
        items = b"\x04\x02" + bytes([8, list(FORD).index(name)]) + push(y) + push(x)
        if between:  # the count pushed on its own, with an action in between
            code += b"\x96" + struct.pack("<H", len(items)) + items + between + b"\x96\x05\x00" + push(2)
        else:
            code += b"\x96" + struct.pack("<H", len(items) + 5) + items + push(2)
        code += b"\x42" + member
    return code + b"\x00"


def flash(code=None, filter_=shape(52, 32, (0, 16000, 0, 9600)), bodies=shape(54, bounds=(0, 15, 0, 6968)),
          headings=shape(56, bounds=(0, 15999, 0, 15)), extra=shape(7, bounds=(0, 100, 0, 100)), sprite_tag=sprite(),
          smart=place2(6, 63, matrix(8040, 4800, scale=(65536, 65461)), NAME), version=b"\x0a", length=None):
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)
    export = struct.pack("<HH", 1, 67) + b"__Packages.Home\0"
    body = (stage + filter_ + bodies + headings + extra + edit_text(59) + sprite_tag + smart + tag(56, export)
            + tag(59, struct.pack("<H", 67) + (home() if code is None else code)) + tag(1, b"") + tag(0, b""))
    return b"FWS" + version + struct.pack("<I", 8 + len(body) if length is None else length) + body


def corners(body):
    return {name: (x[2], y[2]) for name, (y, x) in build.corner_slots(body).items()}


def by_slot(values):
    return {build.SLOT[k]: v for k, v in values.items()}


MOVED = matrix(-8000, -4800)


def patched_class():
    body = build.patch_corners(swf_bitmaps.unpack(flash())[1])
    return swf_bitmaps.tags(body)[X.class_tag(body, build.CLASS)[0] + 1][2][2:]


def ours(**overrides):
    """What the build makes of flash(): the class patched for real, the shapes, placements and
    the sprite as the XML edit leaves them (new bounds, moved dividers in normal blend, no scale);
    `overrides` replace single parts, for a result that is wrong in exactly one way."""
    parts = dict(code=patched_class(), filter_=shape(52, 32, (0, 16000, 0, 9600 + 1)), bodies=shape(54, bounds=(160, 15840, 1120, 8480)),
                 headings=shape(56, bounds=(480, 10700, 1340, 5700)), sprite_tag=sprite(dividers=(MOVED, MOVED), blend=None),
                 smart=place2(6, 63, matrix(8040, 4800), NAME))
    parts.update(overrides)
    return flash(**parts)


def xml_home():
    """Ford's Home as FFDec's XML, in small: the three shapes, the sprite with its dividers and
    a label, mcSmartCorners' own placement, the four labels."""
    root = ET.Element("swf")
    tags = ET.SubElement(root, "tags")
    tags.append(ET.fromstring(
        '<item type="DefineShape3Tag" shapeId="52"><shapes><fillStyles><fillStyles><item type="FILLSTYLE" fillStyleType="0">'
        '<color type="RGBA" red="0" green="0" blue="0" alpha="127"/></item></fillStyles></fillStyles></shapes></item>'))
    tags.append(skeleton(54))
    headings = skeleton(56)
    headings.find("shapeBounds").set("Xmax", "15999")
    headings.find("shapeBounds").set("Ymax", "15")
    tags.append(headings)
    for ident in build.LABELS:
        ET.SubElement(tags, "item", type="DefineEditTextTag", characterID=str(ident), initialText="{Corner}")
    sub = ET.SubElement(ET.SubElement(tags, "item", type="DefineSpriteTag", spriteId="63"), "subTags")
    for depth, character, (x, y) in ((1, 55, (-6, -3483)), (3, 57, (-7998, -100))):
        place = ET.SubElement(sub, "item", type="PlaceObject3Tag", depth=str(depth), characterId=str(character),
                              placeFlagHasBlendMode="true", blendMode="4")
        ET.SubElement(place, "matrix", hasScale="false", hasRotate="false", translateX=str(x), translateY=str(y))
    label = ET.SubElement(sub, "item", type="PlaceObject2Tag", depth="5", characterId="59", name="mcLabelClimateCorner")
    ET.SubElement(label, "matrix", hasScale="false", hasRotate="false", translateX="240", translateY="1442")
    main = ET.SubElement(tags, "item", type="PlaceObject2Tag", depth="6", characterId="63", name=NAME.decode())
    ET.SubElement(main, "matrix", hasScale="true", scaleY="0.9988556", nScaleBits="18", hasRotate="false", translateX="8040", translateY="4800")
    return root


class Face:
    """One face for all tests: instancing the font takes a moment."""
    _face = None

    @classmethod
    def get(cls):
        if cls._face is None:
            cls._face = glyphs.Face()
        return cls._face


class Numbers(unittest.TestCase):
    def test_reads_each_corner_and_its_kind(self):
        body = swf_bitmaps.unpack(flash())[1]
        slots = build.corner_slots(body)
        self.assertEqual(corners(body), by_slot(FORD))
        self.assertEqual([slots[n][1][1] for n in ("phone", "media")], ["int", "double"])  # the x values

    def test_changes_the_eight_numbers_in_place_and_nothing_else(self):
        old = swf_bitmaps.unpack(flash())[1]
        new = build.patch_corners(old)
        self.assertEqual(len(new), len(old))
        before, after = swf_bitmaps.tags(old), swf_bitmaps.tags(new)
        index = X.class_tag(old, build.CLASS)[0] + 1  # swf_bitmaps.tags counts the frame header first
        self.assertEqual([i for i, (x, y) in enumerate(zip(before, after)) if x != y], [index])
        self.assertEqual(corners(new), by_slot(OURS))
        self.assertEqual(after[index][2], struct.pack("<H", 67) + home(OURS))
        self.assertEqual(build.OURS, {k: (int(x), int(y)) for k, (x, y) in by_slot(OURS).items()})

    def test_refuses_a_class_that_is_not_fords(self):
        moved = dict(FORD, SC_TOP_LEFT=(11, 40))
        nearly = dict(FORD, SC_BTM_LEFT=(0.75, 245))  # a double that int() would take for Ford's 0
        for wrong in (home(moved), home(nearly), home(names=list(FORD)[:3]), home(names=list(FORD) + ["SC_TOP_LEFT"])):
            with self.subTest(wrong=wrong), self.assertRaises(SystemExit):
                build.patch_corners(swf_bitmaps.unpack(flash(wrong))[1])

    def test_refuses_an_initialiser_that_is_not_the_compilers_pattern(self):
        swapped = home(between=b"\x4d")  # Push name, y, x; StackSwap; Push 2; InitArray; SetMember
        no_member = home(member=b"\x17")  # InitArray; Pop
        for wrong in (swapped, no_member):
            with self.subTest(wrong=wrong), self.assertRaises(SystemExit):
                build.corner_slots(swf_bitmaps.unpack(flash(wrong))[1])


class Tags(unittest.TestCase):
    def test_passes_a_real_round_trip_where_only_the_intended_tags_differ(self):
        old, new = flash(), ours()
        # the three shapes, the sprite, its two divider placements, its own placement and the class
        self.assertEqual(len(build.check(old, new)), 8)
        self.assertEqual(corners(swf_bitmaps.unpack(new)[1]), by_slot(OURS))

    def test_rejects_a_change_outside_the_intended_tags_for_the_reason_it_names(self):
        """Each case is the passing result wrong in exactly one way, so the named safeguard, not an
        earlier one, is what rejects it."""
        for why, wrong, reason in (
                ("another shape", dict(extra=shape(7, bounds=(0, 101, 0, 100))), "tags changed that should not have"),
                ("the label inside the sprite", dict(sprite_tag=sprite(dividers=(MOVED, MOVED), blend=None, label=place2(5, 59, matrix(31, 40)))),
                 "tags changed that should not have"),
                ("the sprite's frame count", dict(sprite_tag=sprite(frames=0, dividers=(MOVED, MOVED), blend=None)), "frame count"),
                ("a divider's depth", dict(sprite_tag=sprite(dividers=(MOVED, MOVED), blend=None).replace(
                    struct.pack("<HH", 1, 55), struct.pack("<HH", 2, 55))), "the list of tags changed"),
                ("a divider renamed", dict(sprite_tag=tag(39, struct.pack("<HH", 63, 1) + place3(1, 55, MOVED, None, b"x")
                                                           + place3(3, 57, MOVED, None) + place2(5, 59, matrix(30, 40)) + tag(1, b"") + tag(0, b""))),
                 "the list of tags changed"),
                ("mcSmartCorners' depth", dict(smart=place2(7, 63, matrix(8040, 4800), NAME)), "the list of tags changed"),
                ("mcSmartCorners' name", dict(smart=place2(6, 63, matrix(8040, 4800), b"mcSmartCorner2")), "the list of tags changed"),
                ("mcSmartCorners' character", dict(smart=place2(6, 64, matrix(8040, 4800), NAME)), "changed in more than"),
                ("the class, Pop for SetMember", dict(code=home(OURS, member=b"\x17")), "as Ford's compiler did"),
                ("the class, a register elsewhere", dict(code=patched_class().replace(b"\x04\x02", b"\x04\x03")), "outside the intended numbers"),
                ("the class, longer", dict(code=home(OURS) + b"\x00"), "changed its length"),
                ("the class unpatched", dict(code=home()), "not ours"),
                ("the version", dict(version=b"\x0b"), "the header changed"),
                ("the declared length", dict(length=8), "length in its header")):
            with self.subTest(why=why), self.assertRaisesRegex(SystemExit, reason):
                build.check(flash(), ours(**wrong))
        with self.assertRaisesRegex(SystemExit, "length in its header"):  # the input's declared length, too
            build.check(flash(length=8), ours())

    def test_rejects_a_result_as_long_as_the_cars_file(self):
        with self.assertRaisesRegex(SystemExit, "as long as the car's file"):
            build.check(flash(), flash(code=patched_class()))


class Art(unittest.TestCase):
    def test_every_body_and_heading_path_closes_and_the_bodies_sit_on_the_grid(self):
        bodies = build.body_paths()
        self.assertEqual([c for c, _ in bodies], [build.CARD] * 4)
        for (name, (cx, cy, cw, ch)), (_, edges) in zip(build.CARDS.items(), bodies):
            self.assertEqual(closes(edges)[0], (0, 0))
            self.assertEqual(edges[0][1:], ((cx + build.RADIUS) * 20, cy * 20))
            self.assertEqual((cw, ch), (388, 180))
        self.assertEqual((build.CARDS["phone"][:2], build.CARDS["climate"][:2]), ((8, 56), (404, 244)))  # 8 px margins
        self.assertEqual(build.CARDS["nav"][0] - build.CARDS["phone"][0] - 388, 8)  # and 8 px gaps
        self.assertEqual(build.CARDS["media"][1] - build.CARDS["phone"][1] - 180, 8)
        self.assertEqual((800 - build.CARDS["nav"][0] - 388, 432 - build.CARDS["media"][1] - 180), (8, 8))
        paths = build.heading_paths(Face.get())
        self.assertGreater(len(paths), 40)
        for colour, edges in paths:
            self.assertIn(colour, (*build.ACCENT.values(), build.CARD))
            self.assertEqual(closes(edges)[0], (0, 0))
        for name, (cx, cy, _, _) in build.CARDS.items():  # each heading starts in its card's top-left
            xs = [e[1] for c, edges in paths if c == build.ACCENT[name] for e in edges if e[0] == "move"]
            ys = [e[2] for c, edges in paths if c == build.ACCENT[name] for e in edges if e[0] == "move"]
            self.assertGreaterEqual(min(xs), (cx + build.HEADING_X) * 20)
            self.assertGreaterEqual(min(ys), (cy + build.HEADING_TOP - 2) * 20)
            self.assertLess(max(ys), (cy + 40) * 20)

    def test_the_corner_origins_keep_the_touch_buttons_under_the_title_bar(self):
        self.assertGreaterEqual(build.OURS["phone"][1] + 9, 48)
        self.assertGreaterEqual(build.OURS["nav"][1], 48)
        for name in ("media", "climate"):
            self.assertGreaterEqual(build.OURS[name][1], build.CARDS[name][1] - 8)


class Xml(unittest.TestCase):
    def test_edits_fords_xml_and_reads_it_back_for_the_build_and_the_preview(self):
        for preview in (False, True):
            root = xml_home()
            build.check_ford(root)
            build.edit_xml(root, Face.get(), preview)
            build.check_xml(root, Face.get(), preview)
            smart = X.container(root, 63)
            for depth in (1, 3):
                place = X.placement(smart, depth=depth)
                self.assertEqual((place.get("placeFlagHasBlendMode"), place.get("blendMode")), ("false", "1"))
            main = X.placement(X.container(root, "main"), name=NAME.decode())
            self.assertEqual(X.matrix_values(main)[:3], (("8000" if preview else "8040"), "4800", "false"))
            self.assertEqual(X.read_shape(X.define(root, "DefineShapeTag", 54))[3], ("fill", "0", ("10", "11", "14", None)))
            self.assertEqual(build.filter_colour(root).get("alpha"), "255")
            self.assertEqual(X.define(root, "DefineEditTextTag", 59).get("initialText"), "" if preview else "{Corner}")

    def test_refuses_a_file_that_is_not_fords_home(self):
        for why, spoil in (("filter", lambda r: build.filter_colour(r).set("alpha", "255")),
                           ("divider bounds", lambda r: X.define(r, "DefineShapeTag", 54).find("shapeBounds").set("Ymax", "6969")),
                           ("sprite placement", lambda r: X.placement(X.container(r, "main"), name=NAME.decode()).find("matrix").set("translateX", "8000")),
                           ("a rotated divider", lambda r: X.placement(X.container(r, 63), depth=1).find("matrix").set("hasRotate", "true")),
                           ("a skewed sprite", lambda r: X.placement(X.container(r, "main"), name=NAME.decode()).find("matrix").set("hasRotate", "true")),
                           ("a divider missing", lambda r: X.container(r, 63).remove(X.placement(X.container(r, 63), depth=3)))):
            root = xml_home()
            spoil(root)
            with self.subTest(why=why), self.assertRaises(SystemExit):
                build.check_ford(root)
        root = xml_home()
        build.check_ford(root)
        build.edit_xml(root, Face.get(), False)
        X.placement(X.container(root, 63), depth=1).find("matrix").set("translateY", "-4801")
        with self.assertRaises(SystemExit):
            build.check_xml(root, Face.get(), False)


if __name__ == "__main__":
    unittest.main()
