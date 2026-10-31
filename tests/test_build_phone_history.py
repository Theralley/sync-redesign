"""build_phone_history changes the two list numbers in place, and only when they are Ford's.

The class is made here (no Ford file): an export of __Packages.PhoneHistory and its init code,
a constant pool and one push like {rowHeight: 50, visibleRowCount: 5} compiles to. The row's
layout goes through FFDec in Docker and is checked by the build itself, not here.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import build_phone_history as build  # noqa: E402
import swf_bitmaps  # noqa: E402


def tag(code, contents):
    return struct.pack("<HI", (code << 6) | 0x3F, len(contents)) + contents


def body(row_height=50, rows=5):
    pool = b"rowHeight\0visibleRowCount\0"
    actions = (b"\x88" + struct.pack("<HH", len(pool) + 2, 2) + pool
               + b"\x96" + struct.pack("<H", 14) + b"\x08\x00\x07" + struct.pack("<i", row_height)
               + b"\x08\x01\x07" + struct.pack("<i", rows) + b"\x00")
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)
    export = struct.pack("<HH", 1, 91) + b"__Packages.PhoneHistory\0"
    return stage + tag(56, export) + tag(59, struct.pack("<H", 91) + actions) + struct.pack("<H", 0)


class Numbers(unittest.TestCase):
    def test_reads_the_numbers_after_their_names(self):
        actions = swf_bitmaps.tags(body())[build.class_actions(body(), build.CLASS)][2][2:]
        self.assertEqual([(n, v) for n, v, _ in build.numbers(actions)], [("rowHeight", 50), ("visibleRowCount", 5)])

    def test_changes_them_in_place_and_nothing_else(self):
        old, new = body(), build.change_code(body())
        self.assertEqual(len(new), len(old))
        actions = swf_bitmaps.tags(new)[build.class_actions(new, build.CLASS)][2][2:]
        self.assertEqual([(n, v) for n, v, _ in build.numbers(actions)], [("rowHeight", 76), ("visibleRowCount", 3)])
        self.assertEqual(sum(a != b for a, b in zip(old, new)), 2)  # one byte each: 50 -> 76, 5 -> 3

    def test_refuses_a_class_that_is_not_fords(self):
        with self.assertRaises(SystemExit):
            build.change_code(body(row_height=60))


if __name__ == "__main__":
    unittest.main()
