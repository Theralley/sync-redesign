"""build_corners edits only the placements and text fields its table names, reads them back,
changes PhoneSmartCorner's two layout numbers in place and nothing else, and makes the idle
state for the preview without touching the build.

Made here (no Ford file): XML trees shaped like FFDec's (a main timeline and sprites with named
placements, text fields with bounds and colours) and a class whose Push holds the pattern of
UpdateIconLayout. The real round trip through FFDec in Docker is the build's own.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_corners as build  # noqa: E402
import swf_bitmaps  # noqa: E402
import swf_place  # noqa: E402
import xmlswf as X  # noqa: E402
from test_xmlswf import actions, flash, matrix, place2  # noqa: E402


def xml(places, texts=(), shapes=()):
    """FFDec-like XML: `places` = (container, depth, name, characterId, matrix attrs); a sprite
    container is made when first named; `texts` = (id, bounds, colour, html); `shapes` = (id, bounds)."""
    root = ET.Element("swf")
    tags = ET.SubElement(root, "tags")
    ET.SubElement(ET.SubElement(tags, "item", type="SetBackgroundColorTag"), "backgroundColor", red="0", green="0", blue="0")
    for ident, (x0, x1, y0, y1) in shapes:
        element = ET.SubElement(tags, "item", type="DefineShapeTag", shapeId=str(ident))
        ET.SubElement(element, "shapeBounds", Xmin=str(x0), Xmax=str(x1), Ymin=str(y0), Ymax=str(y1))
        fills = ET.SubElement(ET.SubElement(ET.SubElement(element, "shapes"), "fillStyles"), "fillStyles")
        ET.SubElement(ET.SubElement(fills, "item", type="FILLSTYLE", fillStyleType="0"), "color", red="37", green="37", blue="37")
    for ident, (x0, x1, y0, y1), colour, html in texts:
        element = ET.SubElement(tags, "item", type="DefineEditTextTag", characterID=str(ident), fontHeight="760", align="2",
                                initialText=html)
        ET.SubElement(element, "bounds", Xmin=str(x0), Xmax=str(x1), Ymin=str(y0), Ymax=str(y1))
        ET.SubElement(element, "textColor", red=str(colour[0]), green=str(colour[1]), blue=str(colour[2]), alpha="255")
    sprites = {}
    for container, depth, name, char, m in places:
        if container == "main":
            box = tags
        else:
            if container not in sprites:
                sprites[container] = ET.SubElement(ET.SubElement(tags, "item", type="DefineSpriteTag", spriteId=str(container)), "subTags")
            box = sprites[container]
        attrs = {"type": "PlaceObject2Tag", "depth": str(depth), "characterId": str(char)}
        if name:
            attrs["name"] = name
        place = ET.SubElement(box, "item", **attrs)
        ET.SubElement(place, "matrix", {"hasScale": "false", "hasRotate": "false", "translateX": "0", "translateY": "0", **m})
    return root


SPEC = {"places": [("main", 11, "icons", {"y": 8}), (101, 1, "bgButton", {"scale": (1.5, 1.1)}), (101, 8, "LEDOne", {"x": 222, "y": 22}),
                   (90, 5, "DayNight", {"scale": build.ZERO})],
        "texts": {67: {"fontHeight": 400, "Xmax": 1160, "Ymax": 560, "align": 1, "color": (150, 156, 168)},
                  12: {"fontHeight": 600, "size": 30, "Ymax": 740}}}
PLACES = [("main", 11, "icons", 87, {"translateX": "1580", "translateY": "850"}),
          ("main", 12, "other", 88, {"translateX": "10", "translateY": "10"}),
          (101, 1, "bgButton", 90, {"hasScale": "true", "scaleX": "1.3333435", "scaleY": "1.25", "nScaleBits": "18"}),
          (101, 7, "txtButton", 91, {"translateX": "340", "translateY": "240"}),
          (101, 8, "LEDOne", 100, {"translateX": "4200", "translateY": "480"}),
          (90, 5, "DayNight", 89, {})]
TEXTS = [(67, (-40, 2460, -40, 926), (255, 255, 255), '<p align="center"></p>'),
         (12, (-40, 6760, -40, 646), (255, 255, 255), '<p align="center"><font face="F" size="26" color="#ffffff">Street</font></p>')]


class Edits(unittest.TestCase):
    def test_applies_the_table_and_reads_it_back(self):
        root = xml(PLACES, TEXTS)
        build.apply(root, SPEC)
        build.read_back(root, SPEC)
        icons = X.placement(X.container(root, "main"), depth=11)
        self.assertEqual(X.matrix_values(icons)[:3], ("1580", "160", "false"))  # x kept, y 8 px
        self.assertEqual(X.matrix_values(X.placement(X.container(root, 101), depth=1))[2:5], ("true", "1.5", "1.1"))
        self.assertEqual(X.matrix_values(X.placement(X.container(root, 90), depth=5))[3:5], ("0.0", "0.0"))
        self.assertEqual(X.matrix_values(X.placement(X.container(root, 101), depth=7))[:2], ("340", "240"))  # untouched
        temp = X.define(root, "DefineEditTextTag", 67)
        self.assertEqual((temp.get("fontHeight"), temp.get("align"), temp.find("bounds").get("Xmax"), temp.find("bounds").get("Ymax")),
                         ("400", "1", "1160", "560"))
        self.assertEqual(temp.find("textColor").get("green"), "156")
        self.assertEqual(temp.get("initialText"), '<p align="right"></p>')
        self.assertIn('size="30"', X.define(root, "DefineEditTextTag", 12).get("initialText"))

    def test_refuses_another_name_at_the_depth_and_a_value_that_did_not_read_back(self):
        swapped = [("main", 11, "icon", 87, {}) if p[1] == 11 and p[0] == "main" else p for p in PLACES]
        with self.assertRaises(SystemExit):
            build.apply(xml(swapped, TEXTS), SPEC)
        root = xml(PLACES, TEXTS)
        build.apply(root, SPEC)
        X.placement(X.container(root, 101), depth=8).find("matrix").set("translateX", "4400")
        with self.assertRaises(SystemExit):
            build.read_back(root, SPEC)
        root = xml(PLACES, TEXTS)
        build.apply(root, SPEC)
        X.define(root, "DefineEditTextTag", 67).find("textColor").set("red", "151")
        with self.assertRaises(SystemExit):
            build.read_back(root, SPEC)

    def test_wanted_and_allowed_follow_the_table(self):
        defines, main_places, sprite_places = build.wanted(SPEC)
        self.assertEqual(defines, {(37, 67), (37, 12)})
        self.assertEqual(main_places, {(11, "icons")})
        self.assertEqual(sprite_places, {101: {(1, "bgButton"), (8, "LEDOne")}, 90: {(5, "DayNight")}})
        self.assertIn(("sprite101", "PlaceObject2", 8, "LEDOne"), build.allowed_keys(SPEC))
        self.assertIn(("DefineEditText", 12), build.allowed_keys(SPEC))
        self.assertNotIn(("main", "PlaceObject2", 12, "other"), build.allowed_keys(SPEC))

    def test_the_table_names_the_four_files_and_only_matrix_or_text_changes(self):
        self.assertEqual(set(build.EDITS), set(build.FILES))
        for name, spec in build.EDITS.items():
            for container, depth, placed, change in spec["places"]:
                self.assertTrue(container == "main" or isinstance(container, int), (name, container))
                self.assertTrue(set(change) <= {"x", "y", "scale"}, (name, placed))
            for ident, change in spec["texts"].items():
                self.assertTrue(set(change) <= {"fontHeight", "Xmax", "Ymax", "align", "color", "size"}, (name, ident))
        self.assertEqual(build.ICON_LAYOUT, {"int": (200, 385), "double": (0.5, 1.0)})


def assignment(first=200, second=0.5, op=0x0B):
    """`this.pThis.icons._x = first - total * second` as the compiler lays it out: a member lookup,
    one Push of _x, the int, the register and the double, Multiply, Subtract, SetMember."""
    push = lambda *items: b"\x96" + struct.pack("<H", sum(len(p) for p in items)) + b"".join(items)  # noqa: E731
    return (push(b"\x08\x00") + b"\x4e" + push(b"\x08\x01") + b"\x4e"
            + push(b"\x08\x02", b"\x07" + struct.pack("<i", first), b"\x04\x04", b"\x06" + X.as2_double_bytes(second))
            + b"\x0c" + bytes([op]) + b"\x4f")


def phone_class(first=200, second=0.5, op=0x0B, twice=False, outside=False, method="UpdateIconLayout"):
    """The class's init code: a constant pool, `method = function() { assignment }` (an anonymous
    DefineFunction2 whose body follows inline), with the assignment also twice or outside the method."""
    pool = ["pThis", "icons", "_x", method]
    names = b"".join(n.encode() + b"\0" for n in pool)
    body = assignment(first, second, op) * (2 if twice else 1)
    function = b"\x8e" + struct.pack("<H", 1 + 2 + 1 + 2 + 2) + b"\0" + struct.pack("<HBHH", 0, 0, 0, len(body))
    code = b"\x88" + struct.pack("<HH", len(names) + 2, len(pool)) + names
    if outside:
        code += assignment(first, second, op)
    return code + b"\x96\x02\x00\x08\x03" + function + body + b"\x4f" + b"\x00"


class PhoneCode(unittest.TestCase):
    def test_patches_the_two_numbers_in_place_reads_them_back_and_changes_nothing_else(self):
        ford = swf_bitmaps.unpack(flash(code=phone_class(), class_name=build.PHONE_CLASS.encode()))[1]
        ours = build.patch_phone_code(ford)
        self.assertEqual(len(ours), len(ford))
        (io, _, iv), (do, _, dv) = build.icon_slots(ours)
        self.assertEqual((iv, dv), (385, 1.0))
        slots = [(io, "int"), (do, "double")]
        self.assertEqual(X.check_class(ford, ours, build.PHONE_CLASS, slots), 67)
        self.assertEqual(sum(a != b for a, b in zip(ford, ours)), sum(a != b for a, b in zip(
            struct.pack("<i", 200) + X.as2_double_bytes(0.5), struct.pack("<i", 385) + X.as2_double_bytes(1.0))))

    def test_refuses_other_numbers_another_operation_another_method_or_a_pattern_found_twice(self):
        for why, code in (("201", phone_class(first=201)), ("0.25", phone_class(second=0.25)),
                          ("Add instead of Subtract", phone_class(op=0x0A)), ("twice in the method", phone_class(twice=True)),
                          ("outside the method only", phone_class(method="Other")),
                          ("another method's name", phone_class(method="UpdateIconLayouts"))):
            with self.subTest(why=why), self.assertRaises(SystemExit):
                build.patch_phone_code(swf_bitmaps.unpack(flash(code=code, class_name=build.PHONE_CLASS.encode()))[1])
        inside_and_outside = swf_bitmaps.unpack(flash(code=phone_class(outside=True), class_name=build.PHONE_CLASS.encode()))[1]
        (io, _, _), _ = build.icon_slots(inside_and_outside)  # the copy outside the method is not the one
        start, end = X.method_range(X.class_pushes(inside_and_outside, build.PHONE_CLASS), build.METHOD)
        self.assertTrue(start <= io < end)

    def test_text_fields_may_change_only_in_the_fields_their_table_entry_names(self):
        self.assertEqual(build.text_allowed(SPEC), {67: {"fontHeight", "bounds", "layout", "initialText", "textColor"},
                                                    12: {"fontHeight", "initialText", "bounds"}})


class Length(unittest.TestCase):
    def test_grow_widens_the_street_placement_keeps_its_translation_and_leaves_the_rest(self):
        street = place2(15, 12, matrix(640, 1800, bits=12))
        body = swf_bitmaps.unpack(flash(street + place2(16, 36, matrix(3200, -20000))))[1]
        grown = build.grow("NavSmartCorner", body)
        self.assertGreater(len(grown), len(body))
        self.assertEqual(swf_place.read(grown, None, 15, 12), (640, 1800))
        self.assertEqual(swf_place.read(grown, None, 16, 36), (3200, -20000))
        keys_before, keys_after = X.flat_keys(body), X.flat_keys(grown)
        self.assertEqual([k for k, _ in keys_before], [k for k, _ in keys_after])
        self.assertEqual([k for (k, x), (_, y) in zip(keys_before, keys_after) if x != y], [("main", "PlaceObject2", 15, "")])
        self.assertTrue(X.same_but(26, dict(keys_before)[("main", "PlaceObject2", 15, "")], dict(keys_after)[("main", "PlaceObject2", 15, "")], ("matrix",)))
        self.assertEqual(build.grow("MediaSmartCorner", body), body)
        self.assertEqual(build.GROW["NavSmartCorner"], (None, 15, 12))
        self.assertIn(("main", 15, "currentStreetTxt"), [e[:3] for e in build.EDITS["NavSmartCorner"]["places"]])


class Idle(unittest.TestCase):
    def test_drops_hidden_placements_sets_sample_text_and_the_background(self):
        root = xml(PLACES, TEXTS)
        build.idle(root, {"drop": {"main": ["other"], 101: ["txtButton"]}, "move": {101: {"LEDOne": (66, 0)}},
                         "text": {67: "22.0°", 12: "Storgatan"}}, (255, 255, 255))
        self.assertEqual([p.get("name") for p in X.container(root, 101)], ["bgButton", "LEDOne"])
        self.assertEqual([p.get("name") for p in X.container(root, "main") if p.get("type") == "PlaceObject2Tag"], ["icons"])
        self.assertEqual(X.matrix_values(X.placement(X.container(root, 101), name="LEDOne"))[:2], ("1320", "0"))
        self.assertEqual(X.define(root, "DefineEditTextTag", 67).get("initialText"), '<p align="center">22.0°</p>')
        self.assertEqual(X.define(root, "DefineEditTextTag", 12).get("initialText"),
                         '<p align="center"><font face="F" size="26" color="#ffffff">Storgatan</font></p>')
        background = next(t for t in root.find("tags") if t.get("type") == "SetBackgroundColorTag").find("backgroundColor")
        self.assertEqual(background.get("red"), "255")

    def test_runtime_look_recolours_the_sizer_and_lays_the_phone_icons_out_as_the_patched_code_does(self):
        places = [("main", 11, "icons", 87, {"translateX": "1580", "translateY": "160"}),
                  (87, 13, "battery", 85, {"translateX": "2900", "translateY": "320"}),
                  (87, 25, "radiosignals", 86, {"translateX": "4000", "translateY": "200"}),
                  (85, 1, "iconBatteryLife4", 81, {}), (86, 1, "iconRadioSignal4", 38, {}), (81, 1, "", 80, {}), (38, 1, "", 37, {})]
        root = xml(places, shapes=[(80, (0, 600, 0, 400)), (37, (0, 800, 0, 500)), (5, (0, 3120, 0, 800))])
        build.runtime_look(root, "PhoneSmartCorner", (13, 14, 18))
        self.assertEqual(build.sprite_width(root, 85), 30)
        self.assertEqual(X.matrix_values(X.placement(X.container(root, 87), name="battery"))[:2], ("0", "320"))
        self.assertEqual(X.matrix_values(X.placement(X.container(root, 87), name="radiosignals"))[:2], (str(37 * 20), "200"))
        total = 30 + 7 + 40 + 7
        self.assertEqual(X.matrix_values(X.placement(X.container(root, "main"), name="icons"))[:2], (str((385 - total) * 20), "160"))
        colour = X.define(root, "DefineShapeTag", 5).find("shapes").find("fillStyles").find("fillStyles")[0].find("color")
        self.assertEqual([colour.get(k) for k in ("red", "green", "blue")], ["13", "14", "18"])

    def test_variants_name_the_chip_colours_and_the_temperature_sample(self):
        self.assertEqual(build.VARIANTS[""][0], (13, 14, 18))
        self.assertEqual(build.VARIANTS["22"][0], (22, 24, 30))
        self.assertEqual(build.VARIANTS["temps"][1], {"ClimateSmartCorner": {67: "22.0°", 68: "22.0°"}})
        self.assertEqual(build.IDLE["ClimateSmartCorner"]["text"], {})


if __name__ == "__main__":
    unittest.main()
