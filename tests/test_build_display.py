"""build_display lowers the Auto dim offset's floor in place, and only in Ford's Display screen.

The class is made here (no Ford file): an export of __Packages.Display and its init code, a
constant pool and one push like {max: 14, MAX_LEVEL: 5, MIN_LEVEL: -5} compiles to, in an
uncompressed file, as Ford stores its screens.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build_display  # noqa: E402
import build_phone_history  # noqa: E402
import swf_bitmaps  # noqa: E402


def tag(code, contents):
    return struct.pack("<HI", (code << 6) | 0x3F, len(contents)) + contents


def screen(floor=-5, top=5, brightness=14):
    pool = b"max\0MAX_LEVEL\0MIN_LEVEL\0"
    push = b"".join(bytes([8, k, 7]) + struct.pack("<i", v) for k, v in enumerate((brightness, top, floor)))
    actions = (b"\x88" + struct.pack("<HH", len(pool) + 2, 3) + pool
               + b"\x96" + struct.pack("<H", len(push)) + push + b"\x00")
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)
    export = struct.pack("<HH", 1, 77) + b"__Packages.Display\0"
    body = stage + tag(56, export) + tag(59, struct.pack("<H", 77) + actions) + struct.pack("<H", 0)
    return b"FWS\x0a" + struct.pack("<I", 8 + len(body)) + body


def values(data):
    body = swf_bitmaps.unpack(data)[1]
    actions = swf_bitmaps.tags(body)[build_phone_history.class_actions(body, build_display.CLASS)][2][2:]
    return {n: v for n, v, _ in build_phone_history.numbers(actions)}


class Display(unittest.TestCase):
    def test_lowers_only_the_floor_in_place(self):
        old = screen()
        new = build_display.change(old, -10)
        self.assertEqual(values(new), {"max": 14, "MAX_LEVEL": 5, "MIN_LEVEL": -10})
        self.assertEqual(len(new), len(old))
        self.assertEqual(sum(a != b for a, b in zip(old, new)), 1)  # -5 -> -10: one byte

    def test_refuses_a_screen_that_is_not_fords(self):
        for wrong in (screen(floor=-10), screen(top=6), screen(brightness=15)):
            with self.subTest(wrong=values(wrong)), self.assertRaises(SystemExit):
                build_display.change(wrong, -10)


if __name__ == "__main__":
    unittest.main()
