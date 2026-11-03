"""swf_place moves one placement's translation in place and leaves every other byte alone.

The Flash file is made here (no Ford file): a stage, a sprite with two placements (one of them
scaled and named) and one placement on the main timeline.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import swf_bitmaps  # noqa: E402
import swf_place  # noqa: E402


def tag(code, contents):
    return struct.pack("<HI", (code << 6) | 0x3F, len(contents)) + contents


def packed(bits):
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def sb(value, n):
    return format(value & ((1 << n) - 1), f"0{n}b")


def matrix(x, y, n, scale=None):
    bits = "0" if scale is None else "1" + format(18, "05b") + sb(scale[0], 18) + sb(scale[1], 18)
    return packed(bits + "0" + format(n, "05b") + sb(x, n) + sb(y, n))


def place(depth, character, x, y, n, scale=None, name=None):
    flags = 0x06 | (0x20 if name else 0)
    return tag(26, bytes([flags]) + struct.pack("<HH", depth, character) + matrix(x, y, n, scale)
               + (name.encode() + b"\0" if name else b""))


def body():
    sprite = (struct.pack("<HH", 5, 1) + place(1, 20, 300, 120, 10) + place(3, 21, -40, 160, 9, (65536, 65800), "txt")
              + struct.pack("<H", 1 << 6) + struct.pack("<H", 0))
    stage = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)
    return stage + tag(39, sprite) + place(25, 58, 260, 80, 10) + struct.pack("<H", 1 << 6) + struct.pack("<H", 0)


class Place(unittest.TestCase):
    def test_reads_the_translation_of_a_sprites_and_the_main_timelines_placements(self):
        self.assertEqual(swf_place.read(body(), 5, 1, 20), (300, 120))
        self.assertEqual(swf_place.read(body(), 5, 3, 21), (-40, 160))
        self.assertEqual(swf_place.read(body(), None, 25, 58), (260, 80))
        with self.assertRaises(SystemExit):
            swf_place.read(body(), 5, 2, 20)

    def test_moves_in_place_when_the_width_allows_and_changes_nothing_else(self):
        old = body()
        new = swf_place.move(old, 5, 1, 20, (300, 120), (320, 280))
        self.assertEqual(len(new), len(old))
        self.assertEqual(swf_place.read(new, 5, 1, 20), (320, 280))
        self.assertEqual(swf_place.read(new, 5, 3, 21), (-40, 160))
        before, after = swf_bitmaps.tags(old), swf_bitmaps.tags(new)
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b], [1])  # the sprite only
        self.assertEqual(sum(a != b for a, b in zip(old, new)), 2)

    def test_widens_the_matrix_when_the_value_needs_more_bits_and_keeps_the_rest_of_the_tag(self):
        old = body()
        new = swf_place.move(old, 5, 3, 21, (-40, 160), (72, -2000))  # 9 bits cannot hold -2000
        self.assertEqual(swf_place.read(new, 5, 3, 21), (72, -2000))
        self.assertEqual(swf_place.read(new, 5, 1, 20), (300, 120))
        contents = swf_bitmaps.tags(new)[1][2]
        i, start, end = swf_place.find(new, 5, 3, 21)
        placed = contents[start:end]
        self.assertEqual(swf_place.matrix_fields(placed)[2], 12)
        self.assertTrue(placed.endswith(b"txt\0"))
        self.assertEqual(struct.unpack_from("<HH", contents)[0], 5)  # the sprite's header still names it
        self.assertEqual([t[0] for t in swf_bitmaps.tags(new)], [t[0] for t in swf_bitmaps.tags(old)])
        back = swf_place.move(new, 5, 3, 21, (72, -2000), (-40, 160))
        self.assertEqual(swf_place.read(back, 5, 3, 21), (-40, 160))

    def test_moves_a_main_timeline_placement_and_refuses_values_that_are_not_the_expected_ones(self):
        new = swf_place.move(body(), None, 25, 58, (260, 80), (280, -2000))
        self.assertEqual(swf_place.read(new, None, 25, 58), (280, -2000))
        self.assertEqual(swf_bitmaps.tags(new)[2][0], 26)
        with self.assertRaises(SystemExit):
            swf_place.move(body(), None, 25, 58, (261, 80), (280, 0))
        with self.assertRaises(SystemExit):
            swf_place.move(body(), 5, 7, 20, (300, 120), (320, 280))

    def test_grow_makes_the_tag_longer_with_the_same_values(self):
        old = body()
        new = swf_place.move(old, None, 25, 58, (260, 80), (280, 240), grow=True)
        self.assertGreater(len(new), len(old))
        self.assertEqual(swf_place.read(new, None, 25, 58), (280, 240))
        self.assertGreater(swf_place.matrix_fields(swf_bitmaps.tags(new)[2][2])[2], 10)
        self.assertEqual(swf_bitmaps.tags(new)[1], swf_bitmaps.tags(old)[1])  # the sprite untouched

    def test_a_translation_of_sixteen_bits_or_more_is_encoded_and_read_back(self):
        new = swf_place.move(body(), 5, 1, 20, (300, 120), (3200, -20000))  # 16 bits: the width field is unsigned
        self.assertEqual(swf_place.read(new, 5, 1, 20), (3200, -20000))
        i, start, end = swf_place.find(new, 5, 1, 20)
        self.assertEqual(swf_place.matrix_fields(swf_bitmaps.tags(new)[i][2][start:end])[2], 16)
        grown = swf_place.move(new, 5, 1, 20, (3200, -20000), (3200, -20000), grow=True)
        self.assertEqual(swf_place.read(grown, 5, 1, 20), (3200, -20000))
        self.assertGreater(len(grown), len(new))
        wide = swf_place.move(body(), None, 25, 58, (260, 80), (-600000, 600000))  # 21 bits
        self.assertEqual(swf_place.read(wide, None, 25, 58), (-600000, 600000))

    def test_refuses_a_sprite_whose_record_runs_past_it_or_lacks_its_end_tag(self):
        data = body()
        sprite_at = len(bytes(6) + struct.pack("<HH", 0, 0)) + 6  # the sprite's contents start after the stage and its long header
        contents = swf_bitmaps.tags(data)[1][2]
        last = swf_place.inner_tags(contents)[-2]  # the ShowFrame before End
        bad = bytearray(data)
        bad[sprite_at + last[1]:sprite_at + last[1] + 2] = struct.pack("<H", (1 << 6) | 0x3F)  # long form, no length follows
        with self.assertRaises(SystemExit):
            swf_place.read(bytes(bad), 5, 1, 20)
        too_long = bytearray(data)
        header = sprite_at + swf_place.inner_tags(contents)[0][1]
        struct.pack_into("<I", too_long, header + 2, len(contents))  # the first record claims the whole sprite
        with self.assertRaises(SystemExit):
            swf_place.read(bytes(too_long), 5, 1, 20)
        no_end = data.replace(tag(39, contents), tag(39, contents[:-2]))  # the sprite's End tag cut off
        with self.assertRaises(SystemExit):
            swf_place.read(no_end, 5, 1, 20)

    def test_signed_widths(self):
        self.assertEqual([swf_place.signed_bits(v) for v in (0, 1, -1, 255, 256, -256, -257, 7240)], [1, 2, 1, 9, 10, 9, 10, 14])


if __name__ == "__main__":
    unittest.main()
