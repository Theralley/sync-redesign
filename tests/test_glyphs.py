"""glyphs turns DM Sans (fonts/, OFL) into closed, clockwise shape edges with the holes intact.

Run: python3 -m unittest discover tests
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glyphs  # noqa: E402
from test_xmlswf import closes  # noqa: E402


class Fonts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.face = glyphs.Face()

    def test_the_font_is_dm_sans_under_the_ofl_and_the_licence_is_beside_it(self):
        self.assertEqual(self.face.family, "DM Sans 9pt")
        self.assertIn("SIL Open Font License", self.face.font["name"].getDebugName(13))
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", (glyphs.FONT.parent / "OFL.txt").read_text())

    def test_every_contour_closes_and_the_outer_ones_run_one_way(self):
        signs = set()
        for text in ("Telefon", "Navigation", "Media", "Klimat"):
            contours = self.face.edges(text, 24, 80, 18)
            self.assertTrue(contours)
            for contour in contours:
                self.assertEqual(closes(contour)[0], (0, 0))
                self.assertEqual(contour[0][0], "move")
                self.assertEqual(sum(1 for e in contour if e[0] == "move"), 1)
            signs.add(closes(max(contours, key=lambda c: abs(closes(c)[1])))[1] > 0)
        self.assertEqual(len(signs), 1)
        self.assertTrue(all(e[0] in ("move", "line", "curve") for c in self.face.edges("Klimat", 0, 0, 18) for e in c))

    def test_holes_are_separate_contours_of_the_opposite_direction(self):
        o, l = self.face.edges("o", 0, 20, 18), self.face.edges("l", 0, 20, 18)
        self.assertEqual((len(o), len(l)), (2, 1))
        outer, hole = sorted((closes(c)[1] for c in o), key=abs, reverse=True)
        self.assertLess(outer * hole, 0)
        self.assertEqual(closes(l[0])[1] > 0, outer > 0)

    def test_widths_grow_with_size_and_text_starts_at_x(self):
        self.assertAlmostEqual(self.face.width("Media", 36), 2 * self.face.width("Media", 18))
        self.assertGreater(self.face.width("Navigation", 18), self.face.width("Media", 18))
        contours = self.face.edges("H", 100, 50, 18)
        xs = [edge[1] for edge in contours[0] if edge[0] == "move"]
        self.assertGreaterEqual(min(xs), 100 * 20)
        ys = []
        x = y = 0
        for edge in contours[0]:
            if edge[0] == "move":
                x, y = edge[1], edge[2]
            elif edge[0] == "line":
                x, y = x + edge[1], y + edge[2]
            else:
                x, y = x + edge[1] + edge[3], y + edge[2] + edge[4]
            ys.append(y)
        self.assertEqual(max(ys), 50 * 20)  # H stands on the baseline
        self.assertAlmostEqual((50 - min(ys) / 20) / 18, self.face.cap_height, places=1)


if __name__ == "__main__":
    unittest.main()
