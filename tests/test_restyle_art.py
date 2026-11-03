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

    def test_the_deep_palette_draws_near_black_and_the_theme_outline_follows_it(self):
        import make_theme
        xml = (b'<AppTypes>\n<AppType btnColor="0x777777" dialogColor="0x777777" dayColor="0x666666" nightColor="0x393939" />\n'
               + b''.join(b'<AppType btnColor="0x111111" dialogColor="0x111111" dayColor="0x666666" nightColor="0x393939" />\n'
                          for _ in range(4)))
        try:
            art.use("deep")
            self.assertEqual(art.strip(4, 32, "AVAILABLE").getpixel((0, 0))[:3], (13, 14, 18))
            self.assertEqual(restyle_frame.colour("DIM"), art.PALETTES["deep"]["DIM"])
            self.assertEqual(restyle_frame.colour("ACCENT1"), art.ACCENTS[1])
            self.assertIn(b'dayColor="0x0D0E12" nightColor="0x0D0E12"', make_theme.theme_xml(xml, True, "deep"))
        finally:
            art.use("night")
        self.assertEqual(art.strip(4, 32, "AVAILABLE").getpixel((0, 0))[:3], (38, 42, 51))
        self.assertIn(b'dayColor="0x262A33" nightColor="0x262A33"', make_theme.theme_xml(xml, True))

    def test_the_v2_palette_has_black_bars_lighter_strips_and_the_outline_to_match(self):
        import make_theme
        xml = (b'<AppTypes>\n<AppType btnColor="0x777777" dialogColor="0x777777" dayColor="0x666666" nightColor="0x393939" />\n'
               + b''.join(b'<AppType btnColor="0x111111" dialogColor="0x111111" dayColor="0x666666" nightColor="0x393939" />\n'
                          for _ in range(4)))
        try:
            art.use("v2")
            self.assertEqual(art.strip(4, 32, "AVAILABLE").getpixel((0, 0))[:3], (22, 24, 30))
            self.assertEqual(art.strip(4, 32, "PRESSED").getpixel((0, 0))[:3], (34, 37, 45))
            self.assertEqual(art.strip(4, 42, "SELECTED", 0).getpixel((0, 20))[:3], art.mix((22, 24, 30), art.ACCENTS[0], art.TINT))
            self.assertEqual((art.BAR, art.BAR_PRESSED, art.CARD), ((0, 0, 0), (0, 0, 0), (10, 11, 14)))
            self.assertEqual(art.straight((90, 59), True, (11, 59), line=True).getpixel((5, 30))[:3], (0, 0, 0))
            self.assertIn(b'dayColor="0x16181E" nightColor="0x16181E"', make_theme.theme_xml(xml, True, "v2"))
        finally:
            art.use("night")
        self.assertEqual(art.PALETTES["deep"]["BUTTON"], (13, 14, 18))  # deep is not changed by v2
        self.assertTrue(all("CARD" in p and "CARD_PRESSED" in p for p in art.PALETTES.values()))

    def test_a_straight_piece_is_flat_inside_the_bar_and_clear_outside(self):
        bottom = art.straight((90, 59), False, (restyle_frame.OVERHANG, 59), ("home", 45, 32.5, 26))
        self.assertEqual(bottom.size, (90, 59))
        self.assertEqual([bottom.getpixel((5, y))[3] for y in (0, 10, 11, 58)], [0, 0, 255, 255])
        self.assertEqual(bottom.getpixel((5, 30)), (*art.BAR, 255))
        selected = art.straight((90, 59), True, (11, 59), line=True)
        self.assertEqual([selected.getpixel((5, y))[:3] for y in (11, 13, 14)],
                         [art.ACCENTS[0], art.ACCENTS[0], art.BAR_PRESSED])
        top = art.straight((252, 59), False, (0, 48))
        self.assertEqual([top.getpixel((5, y))[3] for y in (0, 47, 48, 58)], [255, 255, 0, 0])

    def test_the_frame_is_laid_out_where_sync_puts_it(self):
        new = {ident: Image.new("RGBA", (1, 1)) for ident, _ in restyle_frame.LAYOUT}
        for ident, size in ((232, (334, 48)), (240, (334, 48)), (249, (252, 59)), (311, (72, 59))):
            new[ident] = Image.new("RGBA", size, (200, 0, 0, 255))
        screen = restyle_frame.mock(new)
        self.assertEqual(screen.size, (800, 480))
        self.assertEqual(screen.getpixel((0, 0)), (200, 0, 0))      # the top-left bar, at x=-2
        self.assertEqual(screen.getpixel((0, 431)), (0, 0, 0))      # the bottom bar starts at 432
        self.assertEqual(screen.getpixel((0, 432)), (200, 0, 0))
        self.assertEqual(screen.getpixel((362, 421)), (200, 0, 0))  # Home's piece at (362, 421)

    def test_the_command_lines_refuse_a_missing_value_and_carry_the_flags(self):
        self.assertEqual(restyle_frame.options(["a.swf", "b.swf", "--palette", "deep", "--straight"]),
                         ("a.swf", "b.swf", "deep", True, None, None))
        for wrong in (["a.swf", "b.swf", "--preview", "--straight"], ["a.swf", "b.swf", "--palette"],
                      ["a.swf", "b.swf", "--palette", "pink"], ["a.swf", "b.swf", "--bent"], ["a.swf"]):
            with self.subTest(wrong=wrong), self.assertRaises(SystemExit):
                restyle_frame.options(wrong)

    def test_without_glow_the_gradients_are_black_and_keep_their_size(self):
        import struct
        import make_theme
        header = (b"BM" + struct.pack("<IHHI", 70 + 800 * 240 * 2, 0, 0, 70)
                  + struct.pack("<IiiHHIIiiII", 56, 800, 240, 1, 16, 3, 800 * 240 * 2, 2835, 2835, 0, 0)
                  + struct.pack("<IIII", 0xF800, 0x7E0, 0x1F, 0))
        original = header + struct.pack("<H", 0x1234) * (800 * 240)
        black = make_theme.gradient(original, (214, 160, 72), glow=False)
        self.assertEqual((len(black), black[:70], set(black[70:])), (len(original), header, {0}))
        self.assertNotEqual(set(make_theme.gradient(original, (214, 160, 72))[70:]), {0})
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            car, out = Path(temp) / "car", Path(temp) / "out"
            car.mkdir()
            (car / "Theme.XML").write_bytes(
                b'<AppType btnColor="0x777777" dialogColor="0x777777" dayColor="0x666666" nightColor="0x393939" />\n' * 5)
            for name, _ in make_theme.NIGHT:
                (car / name).write_bytes(original)
            make_theme.main(str(car), str(out), True, "deep", glow=False)
            for name, _ in make_theme.NIGHT:
                self.assertEqual(set((out / name).read_bytes()[70:]), {0})
            self.assertIn(b'dayColor="0x0D0E12"', (out / "Theme.XML").read_bytes())

    def test_strip_names_are_read_as_the_button_class_builds_them(self):
        self.assertEqual(restyle_frame.parse_strip("PRESSEDSELECTED45_2"), ("PRESSEDSELECTED", 45, 2))
        self.assertEqual(restyle_frame.parse_strip("AVAILABLE30"), ("AVAILABLE", 30, None))
        self.assertEqual(restyle_frame.parse_strip("SELECTED120_4"), ("SELECTED", 120, 4))


if __name__ == "__main__":
    unittest.main()
