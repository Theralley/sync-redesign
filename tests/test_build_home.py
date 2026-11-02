"""build_home changes the eight corner numbers in place, in Ford's class only, lets only the
intended tags differ, and reads its shapes and placements back whole.

Made here (no Ford file): a small but valid Flash file: a class Home whose init code sets the four
SC_* arrays exactly as Ford's compiler did (one Push of the name, y, x and the count 2, then
InitArray and SetMember; one number a double), the three shapes (real bounds, no edges),
mcSmartCorners with its two divider placements (bit-packed matrices, a blend mode) and a label,
its named placement on the main timeline, and one shape more. The XML side is tested on an XML
tree shaped like FFDec's; the real round trip through FFDec in Docker is the build's own.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build_home as build  # noqa: E402
import swf_bitmaps  # noqa: E402
from build_phone_history import class_actions  # noqa: E402

# a float marks the number the compiler stored as a double: SC_BTM_LEFT's x
FORD = {"SC_TOP_LEFT": (10, 40), "SC_TOP_RIGHT": (400, 40), "SC_BTM_RIGHT": (400, 235), "SC_BTM_LEFT": (0.0, 245)}
OURS = {"SC_TOP_LEFT": (3, 39), "SC_TOP_RIGHT": (398, 48), "SC_BTM_RIGHT": (398, 242), "SC_BTM_LEFT": (2.0, 232)}
NAME = b"mcSmartCorners"


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


def matrix(tx=0, ty=0, scale=None, rotate=None):
    """A MATRIX: scale and rotation (16.16 fixed point) when given, then the translation in twips."""
    fields = []
    for pair in (scale, rotate):
        fields += [(0, 1)] if pair is None else [(1, 1), (20, 5), (pair[0], 20), (pair[1], 20)]
    fields += [(16, 5), (tx, 16), (ty, 16)]
    return bitfield(fields)


def shape(ident, code=2, bounds=(0, 0, 0, 0)):
    """A DefineShape or DefineShape3: its bounds, no fills, no lines, no edges."""
    return tag(code, struct.pack("<H", ident) + rect(*bounds) + b"\x00\x00\x00\x00")


def edit_text(ident):
    return tag(37, struct.pack("<H", ident) + rect() + b"\x00\x00" + b"\0")


def place2(depth, char, m=matrix(), name=None):
    flags = 0x06 | (0x20 if name else 0)
    return tag(26, bytes([flags]) + struct.pack("<HH", depth, char) + m + (name + b"\0" if name else b""))


def place3(depth, char, m=matrix(), blend=4, name=None):
    flags = (0x06 | (0x20 if name else 0), 0x02 if blend is not None else 0)
    return tag(70, bytes(flags) + struct.pack("<HH", depth, char) + m + (name + b"\0" if name else b"")
               + (bytes([blend]) if blend is not None else b""))


def sprite(frames=1, dividers=(matrix(-6, -3484), matrix(-8000, -8)), blend=4, label=place2(5, 59, matrix(30, 40))):
    return tag(39, struct.pack("<HH", 63, frames) + place3(1, 55, dividers[0], blend) + place3(3, 57, dividers[1], blend)
               + label + tag(1, b"") + tag(0, b""))


def push(value):
    """One pushed number: an int, or a double in ActionScript 2's word order."""
    if isinstance(value, float):
        return b"\x06" + build.as2_double_bytes(value)
    return b"\x07" + struct.pack("<i", value)


def home(corners=FORD, names=tuple(FORD), member=b"\x4f", between=b""):
    """The class Home's init code: a constant pool, then NAME = [x, y] for each name, as Ford's
    compiler pushed it: one Push of a register, the name, y, x and 2; InitArray; SetMember."""
    pool = b"".join(n.encode() + b"\0" for n in FORD)
    actions = b"\x88" + struct.pack("<HH", len(pool) + 2, len(FORD)) + pool
    for name in names:
        x, y = corners[name]
        items = b"\x04\x02" + bytes([8, list(FORD).index(name)]) + push(y) + push(x)
        if between:  # the count pushed on its own, with an action in between
            actions += b"\x96" + struct.pack("<H", len(items)) + items + between + b"\x96\x05\x00" + push(2)
        else:
            actions += b"\x96" + struct.pack("<H", len(items) + 5) + items + push(2)
        actions += b"\x42" + member
    return actions + b"\x00"


def flash(actions=None, filter_=shape(52, 32, (0, 16000, 0, 9600)), stripes=shape(54, bounds=(0, 15, 0, 6968)),
          bodies=shape(56, bounds=(0, 15999, 0, 15)), extra=shape(7, bounds=(0, 100, 0, 100)), sprite_tag=sprite(),
          smart=place2(6, 63, matrix(8040, 4800, scale=(65536, 65461)), NAME), version=b"\x0a", length=None):
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)
    export = struct.pack("<HH", 1, 67) + b"__Packages.Home\0"
    body = (stage + filter_ + stripes + bodies + extra + edit_text(59) + sprite_tag + smart + tag(56, export)
            + tag(59, struct.pack("<H", 67) + (home() if actions is None else actions)) + tag(1, b"") + tag(0, b""))
    return b"FWS" + version + struct.pack("<I", 8 + len(body) if length is None else length) + body


def corners(actions):
    return {name: (x[2], y[2]) for name, (y, x) in build.corner_slots(actions).items()}


def ours():
    """What the build makes of flash(): the class patched for real, the shapes, placements and
    the sprite as the XML edit leaves them (new bounds, moved dividers in normal blend, no scale)."""
    body = build.change_code(swf_bitmaps.unpack(flash())[1])
    patched = swf_bitmaps.tags(body)[class_actions(body, build.CLASS)][2][2:]
    moved = matrix(-8000, -4800)
    return flash(patched, filter_=shape(52, 32, (0, 16000, 0, 9600 + 1)), stripes=shape(54, bounds=(200, 15800, 1120, 8480)),
                 bodies=shape(56, bounds=(320, 15800, 1120, 8480)), sprite_tag=sprite(dividers=(moved, moved), blend=None),
                 smart=place2(6, 63, matrix(8040, 4800), NAME))


# ---------------------------------------------------------------- FFDec's XML, in small
def skeleton(ident):
    return ElementTree.fromstring(
        f'<item type="DefineShapeTag" shapeId="{ident}"><shapeBounds Xmin="0" Xmax="15" Ymin="0" Ymax="6968" nbits="14"/>'
        '<shapes numFillBits="1" numLineBits="0"><fillStyles><fillStyles><item type="FILLSTYLE" fillStyleType="16"/>'
        '</fillStyles></fillStyles><lineStyles><lineStyles/></lineStyles>'
        '<shapeRecords><item type="EndShapeRecord"/></shapeRecords></shapes></item>')


def xml_home():
    """The result's XML as FFDec would give it back: the three shapes, the sprite's two divider
    placements and mcSmartCorners' own, all as the build writes them."""
    root = ElementTree.Element("swf")
    tags = ElementTree.SubElement(root, "tags")
    filter_ = ElementTree.fromstring(
        '<item type="DefineShape3Tag" shapeId="52"><shapes><fillStyles><fillStyles><item type="FILLSTYLE" fillStyleType="0">'
        '<color type="RGBA" red="0" green="0" blue="0" alpha="255"/></item></fillStyles></fillStyles></shapes></item>')
    tags.append(filter_)
    for ident, paths in zip((54, 56), build.card_paths()):
        element = skeleton(ident)
        build.shape_xml(element, paths)
        tags.append(element)
    sub = ElementTree.SubElement(ElementTree.SubElement(tags, "item", type="DefineSpriteTag", spriteId="63"), "subTags")
    for character in (55, 57):
        place = ElementTree.SubElement(sub, "item", type="PlaceObject3Tag", characterId=str(character), placeFlagHasBlendMode="false")
        ElementTree.SubElement(place, "matrix", hasScale="false", hasRotate="false", translateX="-8000", translateY="-4800")
    main = ElementTree.SubElement(tags, "item", type="PlaceObject2Tag", characterId="63", name="mcSmartCorners")
    ElementTree.SubElement(main, "matrix", hasScale="false", hasRotate="false", translateX="8040", translateY="4800")
    return root


class Doubles(unittest.TestCase):
    def test_a_double_is_written_and_read_with_its_halves_swapped(self):
        for value in (0.0, 2.0, 245.0, -1.5, 0.1):
            self.assertEqual(build.as2_double(build.as2_double_bytes(value)), value)
        self.assertEqual(build.as2_double_bytes(2.0), bytes.fromhex("0000004000000000"))  # the high word first
        self.assertNotEqual(build.as2_double(struct.pack("<d", 2.0)), 2.0)  # the plain order reads wrong


class Numbers(unittest.TestCase):
    def test_reads_each_corner_and_its_kind(self):
        slots = build.corner_slots(home())
        self.assertEqual(corners(home()), FORD)
        self.assertEqual([slots[n][1][1] for n in ("SC_TOP_LEFT", "SC_BTM_LEFT")], ["int", "double"])  # the x values

    def test_changes_the_eight_numbers_in_place_and_nothing_else(self):
        old = swf_bitmaps.unpack(flash())[1]
        new = build.change_code(old)
        self.assertEqual(len(new), len(old))
        before, after = swf_bitmaps.tags(old), swf_bitmaps.tags(new)
        self.assertEqual([i for i, (x, y) in enumerate(zip(before, after)) if x != y], [class_actions(old, build.CLASS)])
        self.assertEqual(corners(after[class_actions(new, build.CLASS)][2][2:]), OURS)
        self.assertEqual(after[class_actions(new, build.CLASS)][2], struct.pack("<H", 67) + home(OURS))

    def test_refuses_a_class_that_is_not_fords(self):
        moved = dict(FORD, SC_TOP_LEFT=(11, 40))
        for wrong in (home(moved), home(names=list(FORD)[:3]), home(names=list(FORD) + ["SC_TOP_LEFT"])):
            with self.subTest(wrong=wrong), self.assertRaises(SystemExit):
                build.change_code(swf_bitmaps.unpack(flash(wrong))[1])

    def test_refuses_an_initialiser_that_is_not_the_compilers_pattern(self):
        swapped = home(between=b"\x4d")  # Push name, y, x; StackSwap; Push 2; InitArray; SetMember
        no_member = home(member=b"\x17")  # InitArray; Pop
        for wrong in (swapped, no_member):
            with self.subTest(wrong=wrong), self.assertRaises(SystemExit):
                build.corner_slots(wrong)


class Tags(unittest.TestCase):
    def test_passes_a_real_round_trip_where_only_the_intended_tags_differ(self):
        old, new = flash(), ours()
        # the three shapes, the sprite, its two divider placements, its own placement and the class
        self.assertEqual(build.check(old, new), 8)
        self.assertEqual(build.check(old, old), 0)
        body = swf_bitmaps.unpack(new)[1]
        self.assertEqual(corners(swf_bitmaps.tags(body)[class_actions(body, build.CLASS)][2][2:]), OURS)

    def test_rejects_a_change_outside_the_intended_tags(self):
        moved = matrix(-8000, -4800)
        for why, wrong in (("another shape", dict(extra=shape(7, bounds=(0, 101, 0, 100)))),
                           ("the label inside the sprite", dict(sprite_tag=sprite(label=place2(5, 59, matrix(31, 40))))),
                           ("the sprite's frame count", dict(sprite_tag=sprite(frames=0))),
                           ("a divider's depth", dict(sprite_tag=sprite(dividers=(moved, moved), blend=None).replace(
                               struct.pack("<HH", 1, 55), struct.pack("<HH", 2, 55)))),
                           ("a divider named", dict(sprite_tag=tag(39, struct.pack("<HH", 63, 1) + place3(1, 55, moved, None, b"x")
                                                                   + place3(3, 57, moved, None) + place2(5, 59, matrix(30, 40))
                                                                   + tag(1, b"") + tag(0, b"")))),
                           ("mcSmartCorners' depth", dict(smart=place2(7, 63, matrix(8040, 4800), NAME))),
                           ("mcSmartCorners' name", dict(smart=place2(6, 63, matrix(8040, 4800), b"mcSmartCorner2"))),
                           ("the class, same length", dict(actions=home(OURS, member=b"\x17"))),
                           ("the class, longer", dict(actions=home(OURS) + b"\x00")),
                           ("the version", dict(version=b"\x0b")),
                           ("the declared length", dict(length=8))):
            with self.subTest(why=why), self.assertRaises(SystemExit):
                build.check(flash(), flash(**wrong))
        with self.assertRaises(SystemExit):  # the input's declared length, too
            build.check(flash(length=8), flash())

    def test_splits_a_placement_into_its_fields(self):
        fields = build.place_fields(70, place3(1, 55, matrix(-6, -3484), 4, b"x")[6:])
        self.assertEqual(fields, {"flags": 0x0226, "depth": struct.pack("<H", 1), "character": struct.pack("<H", 55),
                                  "matrix": matrix(-6, -3484), "name": b"x\0", "blend": b"\x04"})
        self.assertEqual(build.place_fields(26, place2(6, 63, matrix(8040, 4800, scale=(65536, 65461)), NAME)[6:])["matrix"],
                         matrix(8040, 4800, scale=(65536, 65461)))
        self.assertEqual(build.placed(26, place2(6, 63, name=b"x")[6:]), 63)
        self.assertEqual(build.placed(70, place3(1, 55)[6:]), 55)
        self.assertIsNone(build.placed(26, bytes([0x01]) + struct.pack("<H", 6)))  # a move only
        named = bytes([0x06, 0x08]) + struct.pack("<H", 1) + b"Cls\0" + struct.pack("<H", 55)  # a class name first
        self.assertEqual(build.placed(70, named), 55)
        self.assertEqual([code for code, _, _ in build.sprite_tags(sprite()[6:])], [70, 70, 26, 1, 0])


class Cards(unittest.TestCase):
    def test_every_card_path_closes_and_starts_where_its_card_is(self):
        stripes, bodies = build.card_paths()
        for _, edges in stripes + bodies:
            x = y = 0
            for edge in edges:
                if edge[0] == "move":
                    start = x, y = edge[1], edge[2]
                elif edge[0] == "line":
                    x, y = x + edge[1], y + edge[2]
                else:
                    x, y = x + edge[1] + edge[3], y + edge[2] + edge[4]
            self.assertEqual((x, y), start)
        for (name, (cx, cy, _, _)), (accent, stripe), (card, body) in zip(build.CARDS.items(), stripes, bodies):
            self.assertEqual((accent, card), (build.ACCENT[name], build.CARD))
            self.assertEqual(stripe[0][1:], ((cx + build.RADIUS) * 20, cy * 20))
            self.assertEqual(body[0][1:], ((cx + build.STRIPE + build.RADIUS) * 20, cy * 20))
        self.assertEqual(build.BACKGROUND, (0, 0, 0))

    def test_shape_xml_writes_the_fills_the_records_the_bounds_and_no_lines(self):
        element = skeleton(56)
        element.find("shapes").find("lineStyles").find("lineStyles").append(ElementTree.Element("item"))
        build.shape_xml(element, build.card_paths()[1])
        read = build.read_shape(element)
        self.assertEqual(read[:3], [("bounds", "320", "15800", "1120", "8480", "15"), ("bits", "3", "0"), ("lines", 0)])
        self.assertEqual(len(read), 3 + 4 + 4 * 9 + 1)  # four fills, nine records per card, the end
        self.assertEqual(read[3], ("fill", "0", (*(str(v) for v in build.CARD), None)))
        self.assertEqual(read[7][:3], ("change", "true", "false"))  # a move, fill style 1 set
        self.assertEqual(read[7][9:], ("520", "1120"))  # the first card body starts at x + stripe + radius

    def test_check_xml_reads_back_shapes_and_placements_whole(self):
        build.check_xml(xml_home())
        tags = xml_home().find("tags")
        shape54 = next(t for t in tags if t.get("shapeId") == "54" and t.get("type") == "DefineShapeTag")
        divider = next(t for t in tags if t.get("spriteId") == "63").find("subTags")[0]
        for why, spoil in (("zeroed bounds", lambda: [shape54.find("shapeBounds").set(k, "0") for k in ("Xmin", "Xmax", "Ymin", "Ymax")]),
                           ("a line style", lambda: shape54.find("shapes").find("lineStyles").find("lineStyles").append(ElementTree.Element("item"))),
                           ("a record's fill flag", lambda: shape54.find("shapes").find("shapeRecords")[0].set("stateFillStyle0", "true")),
                           ("a rotated divider", lambda: divider.find("matrix").set("hasRotate", "true")),
                           ("a scaled divider", lambda: divider.find("matrix").set("scaleX", "1.0")),
                           ("a blended divider", lambda: divider.set("placeFlagHasBlendMode", "true"))):
            root = xml_home()
            tags = root.find("tags")
            shape54 = next(t for t in tags if t.get("shapeId") == "54" and t.get("type") == "DefineShapeTag")
            divider = next(t for t in tags if t.get("spriteId") == "63").find("subTags")[0]
            spoil()
            with self.subTest(why=why), self.assertRaises(SystemExit):
                build.check_xml(root)

    def test_the_command_line_refuses_a_missing_value_or_file(self):
        self.assertEqual(build.options(["a.swf", "b.swf", "--preview", "p"]), ("a.swf", "b.swf", Path("p")))
        for wrong in (["a.swf", "b.swf", "--preview"], ["a.swf", "b.swf", "--layout", "x"], ["a.swf"]):
            with self.subTest(wrong=wrong), self.assertRaises(SystemExit):
                build.options(wrong)


if __name__ == "__main__":
    unittest.main()
