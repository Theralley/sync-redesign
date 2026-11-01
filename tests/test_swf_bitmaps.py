"""swf_bitmaps replaces only the named pictures, at their size, and keeps every other tag.

The Flash file is made here (no Ford file): a stage, one action tag and two pictures.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
import zlib
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import swf_bitmaps  # noqa: E402


def tag(code, contents):
    return struct.pack("<HI", (code << 6) | 0x3F, len(contents)) + contents


def picture(code, ident, size, colour):
    return tag(code, swf_bitmaps.encode(code, ident, Image.new("RGBA", size, colour)))


def flash(compressed=True):
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)  # a 10-bit stage rectangle: 6 bytes
    body = (stage + tag(12, b"\x96\x05\x00\x00code\x00\x00") + picture(36, 7, (4, 3), (255, 0, 0, 128))
            + picture(20, 9, (2, 2), (0, 0, 255, 255)) + struct.pack("<H", 1 << 6) + struct.pack("<H", 0))
    head = b"CWS\x0a" if compressed else b"FWS\x0a"
    return head + struct.pack("<I", 8 + len(body)) + (zlib.compress(body) if compressed else body)


class Bitmaps(unittest.TestCase):
    def test_lists_the_pictures(self):
        found = swf_bitmaps.pictures(swf_bitmaps.unpack(flash())[1])
        self.assertEqual(found, {7: (36, 5, 4, 3), 9: (20, 5, 2, 2)})

    def test_replaces_only_the_named_picture(self):
        for compressed in (True, False):
            old = flash(compressed)
            new = swf_bitmaps.replace(old, {7: Image.new("RGBA", (4, 3), (0, 200, 0, 255))})
            self.assertEqual(new[:4], old[:4])
            self.assertEqual(struct.unpack_from("<I", new, 4)[0], 8 + len(swf_bitmaps.unpack(new)[1]))
            before, after = swf_bitmaps.tags(swf_bitmaps.unpack(old)[1]), swf_bitmaps.tags(swf_bitmaps.unpack(new)[1])
            changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
            self.assertEqual(changed, [2])  # the stage, the action and picture 9 are untouched
            self.assertEqual(swf_bitmaps.decode(36, after[2][2]).getpixel((0, 0)), (0, 200, 0, 255))

    def test_refuses_another_size_or_an_unknown_picture(self):
        with self.assertRaisesRegex(swf_bitmaps.SwfError, "4x3"):
            swf_bitmaps.replace(flash(), {7: Image.new("RGBA", (5, 3))})
        with self.assertRaisesRegex(swf_bitmaps.SwfError, "no picture 8"):
            swf_bitmaps.replace(flash(), {8: Image.new("RGBA", (4, 3))})
        with self.assertRaises(swf_bitmaps.SwfError):
            swf_bitmaps.unpack(b"ZWS\x0a....")


def jpeg_flash():
    """A stage and one JPEG3 picture (id 5, 6x4), half of it transparent."""
    image = Image.new("RGBA", (6, 4), (200, 40, 40, 255))
    for x in range(3):
        for y in range(4):
            image.putpixel((x, y), (0, 0, 0, 0))
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)
    body = stage + tag(35, swf_bitmaps.encode(35, 5, image)) + struct.pack("<H", 1 << 6) + struct.pack("<H", 0)
    return b"FWS\x0a" + struct.pack("<I", 8 + len(body)) + body


class Jpeg3(unittest.TestCase):
    def test_a_jpeg3_stays_a_jpeg3_with_its_alpha(self):
        old = jpeg_flash()
        self.assertEqual(swf_bitmaps.pictures(swf_bitmaps.unpack(old)[1]), {5: (35, 0, 6, 4)})
        new_image = Image.new("RGBA", (6, 4), (30, 34, 42, 255))
        new_image.putpixel((0, 0), (0, 0, 0, 0))
        new = swf_bitmaps.replace(old, {5: new_image})
        after = swf_bitmaps.tags(swf_bitmaps.unpack(new)[1])
        self.assertEqual([code for code, _, _ in after], [-1, 35, 1, 0])
        back = swf_bitmaps.decode(35, after[1][2])
        self.assertEqual(back.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(back.getpixel((5, 3))[3], 255)
        self.assertLessEqual(max(abs(a - b) for a, b in zip(back.getpixel((5, 3))[:3], (30, 34, 42))), 4)

    def test_a_wrong_colour_under_partial_alpha_is_caught(self):
        red, blue = Image.new("RGBA", (8, 8), (255, 0, 0, 254)), Image.new("RGBA", (8, 8), (0, 0, 255, 254))
        contents = swf_bitmaps.encode(35, 5, red)
        with self.assertRaisesRegex(swf_bitmaps.SwfError, "colour"):
            swf_bitmaps.check_jpeg(5, swf_bitmaps.decode(35, contents), blue)

    def test_a_wrong_length_in_the_header_is_caught(self):
        old = jpeg_flash()
        new = bytearray(swf_bitmaps.replace(old, {5: Image.new("RGBA", (6, 4), (1, 2, 3, 255))}))
        new[4:8] = (1).to_bytes(4, "little")
        with self.assertRaisesRegex(swf_bitmaps.SwfError, "length"):
            swf_bitmaps.check(old, bytes(new), {5: Image.new("RGBA", (6, 4), (1, 2, 3, 255))})

    def test_the_colour_is_premultiplied_as_fords_are(self):
        contents = swf_bitmaps.encode(35, 5, Image.new("RGBA", (8, 8), (240, 240, 240, 64)))
        end = struct.unpack_from("<I", contents, 2)[0]
        colour = Image.open(__import__("io").BytesIO(contents[6:6 + end])).convert("RGB")
        self.assertTrue(all(max(px) <= 64 + 4 for px in colour.getdata()))


if __name__ == "__main__":
    unittest.main()
