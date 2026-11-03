"""build_frame draws the v2 frame at Ford's sizes, moves placements in place and patches two
classes by one byte and two strings, refusing files that are not the ones it was made for.

Everything is made here (no Ford file): a class with the instructions round the patch sites,
small files with the placements the tool expects, in uncompressed form as Ford stores them.

Run: python3 -m unittest discover tests
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # test_swf_place's file makers
import build_frame  # noqa: E402
import restyle_art as art  # noqa: E402
import swf_actions  # noqa: E402
import swf_bitmaps  # noqa: E402
import swf_place  # noqa: E402
from build_phone_history import class_actions  # noqa: E402
from test_swf_place import place, tag  # noqa: E402

STAGE = bytes([0x50, 0, 0, 0, 0, 0]) + struct.pack("<HH", 15 << 8, 1)


def push(*items):
    data = b""
    for item in items:
        if isinstance(item, bool):
            data += bytes([5, int(item)])
        elif isinstance(item, tuple):
            data += bytes([4, item[1]])
        else:
            data += bytes([8, item])
    return b"\x96" + struct.pack("<H", len(data)) + data


def constant_pool(strings):
    raw = b"".join(s.encode() + b"\0" for s in strings)
    return b"\x88" + struct.pack("<H", len(raw) + 2) + struct.pack("<H", len(strings)) + raw


def nav_code(groups=1, openers=1, after=0):
    """isOnHomeScreen ... Not If, then (in the If's fall-through) pThis._visible = true and
    `groups` times compSystemStatus._visible = true; `after` more of those in the else arm."""
    pool = ["isOnHomeScreen", "compSystemStatus", "_visible", "pThis"]
    group = push(1) + b"\x4e" + push(2, True) + b"\x4f"
    fall = push(3) + b"\x4e" + push(2, True) + b"\x4f" + group * groups
    code = constant_pool(pool)
    for _ in range(openers):
        code += push(("r", 1), 0) + b"\x4e\x12" + b"\x9d\x02\x00" + struct.pack("<h", len(fall))
    code += fall + group * after + b"\x00"
    return code


def flash(name, ident, code, places=b""):
    export = struct.pack("<HH", 1, ident) + name.encode() + b"\0"
    body = STAGE + tag(56, export) + tag(59, struct.pack("<H", ident) + code) + places + struct.pack("<H", 1 << 6) + struct.pack("<H", 0)
    return b"FWS\x0a" + struct.pack("<I", 8 + len(body)) + body


def strings_code():
    return constant_pool(["ENTERTAINMENT_LABEL", "Resource.Media.ConsoleObject.146", "Entertainment", "GetDMString"]) \
        + push(0, 2) + b"\x4f" + push(1, 3) + b"\x00"


class FrameArt(unittest.TestCase):
    def setUp(self):
        art.use("v2")

    def tearDown(self):
        art.use("night")

    def test_launch_pieces_are_clear_above_the_bar_black_in_it_and_lined_only_when_selected(self):
        available, selected, size, cell, icon, line = build_frame.LAUNCH["info"]
        off = art.launch(size, cell, icon, False, art.ACCENTS[0])
        on = art.launch(size, cell, icon, True, art.ACCENTS[0])
        self.assertEqual((off.size, on.size), (size, size))
        self.assertEqual([off.getpixel((2, y))[3] for y in (0, 10, 11, 58)], [0, 0, 255, 255])
        self.assertEqual(off.getpixel((2, 30)), (0, 0, 0, 255))
        self.assertEqual(off.getpixel((cell[0], 11)), (0, 0, 0, 255))
        self.assertEqual([on.getpixel((x, 12))[:3] for x in (cell[0] - 1, cell[0], cell[1] - 1, cell[1])],
                         [(0, 0, 0), art.ACCENTS[0], art.ACCENTS[0], (0, 0, 0)])
        self.assertEqual(on.getpixel((cell[0], 14))[:3], (0, 0, 0))
        centre = (round(icon[1]), round(art.LAUNCH_ICON_Y))
        self.assertEqual(off.getpixel(centre)[:3], art.QUIET)
        self.assertEqual(on.getpixel(centre)[:3], art.TEXT)
        home = art.launch(*build_frame.LAUNCH["home"][2:5], True, art.TEXT)
        self.assertEqual(home.getpixel((0, 11))[:3], art.TEXT)

    def test_tabs_and_the_clock_piece_are_black_with_no_line(self):
        self.assertEqual(set(art.tab((334, 48)).getdata()), {(0, 0, 0, 255)})
        clock = art.clock_piece((252, 59))
        self.assertEqual([clock.getpixel((5, y)) for y in (0, 47, 48, 58)],
                         [(0, 0, 0, 255), (0, 0, 0, 255), (0, 0, 0, 0), (0, 0, 0, 0)])


class Patches(unittest.TestCase):
    def test_the_home_branchs_boolean_is_found_by_its_neighbours_and_turned_off(self):
        code = nav_code()
        at = swf_actions.branch_boolean(code, *build_frame.NAV_BRANCH)
        new = build_frame.nav_home_branch(code)
        self.assertEqual(len(new), len(code))
        self.assertEqual([i for i, (a, b) in enumerate(zip(code, new)) if a != b], [at])
        pushes = [swf_actions.push_items(d, swf_actions.pool(new)[1]) for _, op, d in swf_actions.actions(new) if op == swf_actions.PUSH]
        self.assertEqual(pushes[-1], ["_visible", False])
        self.assertEqual(pushes[-3], ["_visible", True])  # pThis._visible stays

    def test_refuses_a_class_with_two_sites_or_two_branches_or_none(self):
        for code in (nav_code(groups=2), nav_code(openers=2), nav_code(groups=0), constant_pool(["x"]) + b"\x00"):
            with self.subTest(), self.assertRaises(SystemExit):
                build_frame.nav_home_branch(code)

    def test_only_the_ifs_fall_through_is_searched_not_the_else_arm(self):
        with self.assertRaises(SystemExit):  # the only site sits after the If's target
            build_frame.nav_home_branch(nav_code(groups=0, after=1))
        code = nav_code(groups=1, after=1)  # one in the branch, one after it: the first is patched
        new = build_frame.nav_home_branch(code)
        self.assertEqual(sum(a != b for a, b in zip(code, new)), 1)
        self.assertLess([i for i, (a, b) in enumerate(zip(code, new)) if a != b][0], len(code) - len(push(1) + b"\x4e" + push(2, True) + b"\x4f") - 1)

    def test_a_branch_into_the_pool_forbids_a_change_of_length(self):
        code = strings_code()
        back = code[:-1] + b"\x99\x02\x00" + struct.pack("<h", -(len(code) - 1 + 5 - 10)) + b"\x00"  # a Jump to byte 10, inside the pool
        with self.assertRaises(SystemExit):
            swf_actions.replace_strings(back, {b"Entertainment\0": b"\0"})
        same = swf_actions.replace_strings(back, {b"Entertainment\0": b"Entertainmenu\0"})  # same length: allowed
        self.assertEqual(len(same), len(back))
        pool_end = 3 + struct.unpack_from("<H", code, 1)[0]
        to_end = code[:-1] + b"\x99\x02\x00" + struct.pack("<h", -(len(code) - 1 + 5 - pool_end)) + b"\x00"  # to the first action after the pool
        self.assertEqual(len(swf_actions.replace_strings(to_end, {b"Entertainment\0": b"\0"})), len(to_end) - 13)
        spanning = code[:-1] + b"\x94\x02\x00\x00\x00" + b"\x00"  # a With block after the pool: fine
        self.assertEqual(len(swf_actions.replace_strings(spanning, {b"Entertainment\0": b"\0"})), len(spanning) - 13)

    def test_the_two_strings_change_in_the_pool_and_nowhere_else(self):
        code = strings_code()
        new = build_frame.media_strings(code)
        self.assertEqual(len(new), len(code) - 13)  # "Entertainment" -> ""
        strings = swf_actions.pool(new)[1]
        self.assertEqual(strings, ["ENTERTAINMENT_LABEL", "Resource.Media.ConsoleObject.x46", "", "GetDMString"])
        self.assertEqual(new[-10:], code[-10:])  # the pushes keep their pool indices
        tail = push(0, 2) + b"\x4f" + push(1, 3) + b"\x00"  # the code after the pool
        self.assertEqual(struct.unpack_from("<H", new, 1)[0], len(new) - 3 - len(tail))  # the pool record's length follows
        with self.assertRaises(SystemExit):
            build_frame.media_strings(constant_pool(["Entertainment", "Entertainment"]) + b"\x00")
        with self.assertRaises(ValueError):
            swf_actions.replace_strings(code, {b"Entertainment\0": b"Fun"})
        with self.assertRaises(SystemExit):  # another length is allowed only with the pool first
            swf_actions.replace_strings(b"\x12" + code, {b"Entertainment\0": b"\0"})
        same = swf_actions.replace_strings(b"\x12" + code, {b"Entertainment\0": b"Entertainmenu\0"})
        self.assertEqual(len(same), len(code) + 1)


class Files(unittest.TestCase):
    def nav(self, street=(748, -20)):
        places = (place(1, 14, *street, 11) + place(9, 19, 260, -69, 11) + place(12, 24, 1040, 20, 12)
                  + place(22, 48, 1102, 0, 12))
        return flash(build_frame.NAV_CLASS, 7, nav_code(), places)

    def test_builds_the_nav_console_placements_and_class_and_checks_every_tag(self):
        old = self.nav()
        new, pictures, changed = build_frame.build_one("NavConsoleObject", old)
        self.assertEqual(pictures, {})
        body = swf_bitmaps.unpack(new)[1]
        for sprite, depth, character, _, ours in build_frame.MOVES["NavConsoleObject"]:
            self.assertEqual(swf_place.read(body, sprite, depth, character), ours)
        code = swf_bitmaps.tags(body)[class_actions(body, build_frame.NAV_CLASS)][2][2:]
        pushes = [swf_actions.push_items(d, swf_actions.pool(code)[1]) for _, op, d in swf_actions.actions(code) if op == swf_actions.PUSH]
        self.assertEqual(pushes[-1], ["_visible", False])
        self.assertEqual(len(changed), 5)  # the class and the four placements
        self.assertGreater(len(new), len(old))  # the street's matrix one field wider: never Ford's length

    def test_refuses_to_write_a_result_as_long_as_the_cars_file(self):
        grown = build_frame.GROW
        try:
            build_frame.GROW = set()
            with self.assertRaisesRegex(SystemExit, "as long as"):
                build_frame.build_one("NavConsoleObject", self.nav())
        finally:
            build_frame.GROW = grown

    def test_refuses_a_console_whose_placement_is_not_fords(self):
        with self.assertRaises(SystemExit):
            build_frame.build_one("NavConsoleObject", self.nav(street=(750, -20)))

    def test_patches_the_media_apps_copy_of_the_strings_and_nothing_else(self):
        old = flash(build_frame.STRINGS_CLASS, 9, strings_code())
        new, _, changed = build_frame.build_one("Media", old)
        self.assertEqual(changed, [2])
        self.assertEqual(len(new), len(old) - 13)
        body = swf_bitmaps.unpack(new)[1]
        code = swf_bitmaps.tags(body)[class_actions(body, build_frame.STRINGS_CLASS)][2][2:]
        self.assertIn("", swf_actions.pool(code)[1])

    def test_refuses_a_frame_without_the_strips(self):
        with self.assertRaises(SystemExit):
            build_frame.build_one("AppConsole", flash("__Packages.Nothing", 3, constant_pool(["x"]) + b"\x00"))

    def test_only_allowed_tags_may_differ(self):
        old = self.nav()
        new = old.replace(b"NavConsoleObject\0", b"NavConsoleObjecT\0")  # the export tag altered
        with self.assertRaises(SystemExit):
            build_frame.check(old, new, set(), set(), True, set())


if __name__ == "__main__":
    unittest.main()
