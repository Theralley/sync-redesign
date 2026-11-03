"""build_menus flattens the side menus' glass pictures at their sizes and nothing else.

The Flash file is made here (no Ford file): the pictures of Menu.swf's buttons and panel, with
and without an alpha channel, beside an unrelated picture and an action tag.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build_menus  # noqa: E402
import restyle_art as art  # noqa: E402
import swf_bitmaps  # noqa: E402


def tag(code, contents):
    return struct.pack("<HI", (code << 6) | 0x3F, len(contents)) + contents


def picture(code, ident, size):
    return tag(code, swf_bitmaps.encode(code, ident, Image.new("RGBA", size, (90, 90, 90, 255))))


def menu(panel=(153, 306)):
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)
    body = stage + tag(12, b"\x96\x05\x00\x00code\x00\x00") + picture(36, 4, panel)
    for ident in (11, 13, 24, 26):
        body += picture(36, ident, (150, 50))
    for ident in (35, 37):
        body += picture(20, ident, (150, 50))
    body += picture(36, 16, (30, 30)) + struct.pack("<H", 1 << 6) + struct.pack("<H", 0)
    return b"FWS\x0a" + struct.pack("<I", 8 + len(body)) + body


class Menus(unittest.TestCase):
    def setUp(self):
        art.use("v2")

    def tearDown(self):
        art.use("night")

    def test_replaces_the_glass_and_the_panel_and_keeps_the_icon_and_the_code(self):
        old = menu()
        new, pictures = build_menus.build(old, "Menu")
        self.assertEqual(set(pictures), {4, 11, 13, 24, 26, 35, 37})
        before, after = swf_bitmaps.tags(swf_bitmaps.unpack(old)[1]), swf_bitmaps.tags(swf_bitmaps.unpack(new)[1])
        changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual(changed, [2, 3, 4, 5, 6, 7, 8])  # not the stage, the code or picture 16
        found = swf_bitmaps.pictures(swf_bitmaps.unpack(new)[1])
        self.assertEqual(found[4][2:], (153, 306))
        self.assertEqual(swf_bitmaps.decode(36, after[2][2]).getpixel((76, 150)), (*art.BACKGROUND, 255))

    def test_cards_have_a_gap_on_top_a_flat_body_and_a_line_only_when_selected(self):
        card = art.menu_card((150, 50), "available", True)
        self.assertEqual([card.getpixel((75, y)) for y in (0, 1, 2, 49)],
                         [(0, 0, 0, 0), (0, 0, 0, 0), (*art.CARD, 255), (*art.CARD, 255)])
        opaque = art.menu_card((150, 50), "pressed", False)
        self.assertEqual([opaque.getpixel((75, y)) for y in (0, 2)], [(*art.BACKGROUND, 255), (*art.CARD_PRESSED, 255)])
        selected = art.menu_card((150, 50), "selected", True)
        self.assertEqual([selected.getpixel((x, 20))[:3] for x in (0, 2, 3)], [art.ACCENTS[0], art.ACCENTS[0], art.CARD])
        self.assertEqual(selected.getpixel((0, 1))[3], 0)

    def test_refuses_a_file_that_is_not_the_menu(self):
        with self.assertRaises(SystemExit):
            build_menus.build(menu(panel=(153, 300)), "Menu")
        with self.assertRaises(SystemExit):
            build_menus.build(menu(), "Info")


if __name__ == "__main__":
    unittest.main()
