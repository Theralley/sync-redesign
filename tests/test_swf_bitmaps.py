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
        with self.assertRaisesRegex(swf_bitmaps.SwfError, "no lossless picture 8"):
            swf_bitmaps.replace(flash(), {8: Image.new("RGBA", (4, 3))})
        with self.assertRaises(swf_bitmaps.SwfError):
            swf_bitmaps.unpack(b"ZWS\x0a....")


if __name__ == "__main__":
    unittest.main()
