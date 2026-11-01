"""The restyle's artwork keeps every picture's size, and a bar piece keeps Ford's outline.

The pieces are made here (no Ford file): a slanted piece with a soft shadow and a bevel.

Run: python3 -m unittest discover tests
"""
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import restyle_art as art  # noqa: E402
import restyle_frame  # noqa: E402


def piece():
    """A slanted bar piece like Ford's: transparent outside, a soft shadow, a lighter bevel."""
    image = Image.new("RGBA", (60, 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.polygon([(0, 29), (20, 4), (59, 4), (59, 29)], fill=(0, 0, 0, 120))  # the shadow
    d.polygon([(2, 29), (21, 6), (59, 6), (59, 29)], fill=(30, 30, 30, 255))
    d.line([(21, 6), (59, 6)], fill=(90, 90, 90, 255))  # the bevel
    return image


class Art(unittest.TestCase):
    def test_strips_keep_their_size_and_mark_the_selected_area(self):
        for state, area in (("AVAILABLE", None), ("PRESSED", None), ("SELECTED", 1), ("PRESSEDSELECTED", 4)):
            image = art.strip(2, 42, state, area)
            self.assertEqual(image.size, (2, 42))
            self.assertEqual(image.getpixel((0, 41))[3], 255)
        self.assertEqual(art.strip(2, 42, "SELECTED", 3).getpixel((0, 0))[:3], art.ACCENTS[3])
        self.assertEqual(art.strip(4, 32, "AVAILABLE").getpixel((0, 0))[:3], art.BUTTON)
        self.assertNotEqual(art.strip(2, 42, "SELECTED", 2).getpixel((0, 20))[:3], art.BUTTON)

    def test_a_flattened_piece_keeps_fords_outline_to_the_pixel(self):
        ford = piece()
        for pressed in (False, True):
            ours = art.flatten(ford, pressed, ("home", 40, 18, 14))
            self.assertEqual(ours.size, ford.size)
            self.assertEqual(list(ours.getchannel("A").getdata()), list(ford.getchannel("A").getdata()))
        inside = art.flatten(ford, False).getpixel((50, 25))
        self.assertEqual(inside[:3], art.BAR)
        self.assertEqual(art.flatten(ford, True).getpixel((50, 25))[:3], art.BAR_PRESSED)
        self.assertEqual(art.flatten(ford, False).getpixel((59, 29))[:3], art.BAR)  # no edge where pieces meet

    def test_bars_lights_icons_and_dividers_keep_their_size(self):
        self.assertEqual(art.bar((334, 48), 1, False).getpixel((10, 47))[:3], art.ACCENTS[1])
        self.assertEqual(art.bar((334, 48), 3, True).getpixel((10, 0))[:3], art.ACCENTS[3])
        self.assertEqual(art.bar((334, 48), 3, True).getpixel((10, 20))[:3], art.BAR)
        lit, dark = art.light((30, 24), (9, 9, 20, 14), 1.0), art.light((30, 24), (9, 9, 20, 14), 0.0)
        self.assertEqual(lit.size, (30, 24))
        self.assertGreater(sum(lit.getpixel((15, 11))[:3]), sum(dark.getpixel((15, 11))[:3]))
        self.assertEqual(lit.getpixel((0, 0))[3], 0)
        self.assertEqual(art.socket((25, 20), (8, 7, 17, 12)).size, (25, 20))
        self.assertEqual(art.icon((38, 33), "home", art.TEXT, 28).size, (38, 33))
        self.assertEqual(art.signal((21, 18), 2, 17).size, (21, 18))
        line = Image.new("RGBA", (2, 49), (56, 56, 56, 200))
        self.assertEqual(art.recolour(line, art.EDGE).getpixel((1, 5)), (*art.EDGE, 200))

    def test_strip_names_are_read_as_the_button_class_builds_them(self):
        self.assertEqual(restyle_frame.parse_strip("PRESSEDSELECTED45_2"), ("PRESSEDSELECTED", 45, 2))
        self.assertEqual(restyle_frame.parse_strip("AVAILABLE30"), ("AVAILABLE", 30, None))
        self.assertEqual(restyle_frame.parse_strip("SELECTED120_4"), ("SELECTED", 120, 4))


if __name__ == "__main__":
    unittest.main()
