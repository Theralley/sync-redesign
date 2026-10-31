"""The icon family draws every icon, and the fan stays mirror-symmetric.

A hooked cross and a three-legged triskele turn only one way: their mirror image differs. A fan
whose picture equals its mirror image can therefore never read as one. The first fan (four
hooked blades) failed exactly this.

Run: python3 -m unittest discover tests
"""
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import icons  # noqa: E402


def mask(name, size=96):
    image = Image.new("L", (size * 2, size * 2), 0)
    icons.draw(ImageDraw.Draw(image), name, size, size, size, 255)
    return image


class Icons(unittest.TestCase):
    def test_every_icon_draws(self):
        for name in icons.NAMES:
            self.assertGreater(sum(mask(name).histogram()[1:]), 0, name)

    def test_fan_equals_its_mirror_image(self):
        fan = mask("fan")
        for mirror in (Image.Transpose.FLIP_LEFT_RIGHT, Image.Transpose.FLIP_TOP_BOTTOM):
            difference = ImageChops.difference(fan, fan.transpose(mirror))
            changed = sum(difference.point(lambda v: 255 if v > 128 else 0).histogram()[255:])
            drawn = sum(fan.point(lambda v: 255 if v > 128 else 0).histogram()[255:])
            # thick lines rasterize a pixel apart at some edges (about 5%); the hooked fan: 54%
            self.assertLess(changed, drawn * 0.10, mirror)

    def test_unknown_icon_is_refused(self):
        with self.assertRaises(ValueError):
            mask("nothing")


if __name__ == "__main__":
    unittest.main()
