"""Text as Flash shape edges, from a font we may use: no font tag, no device font, no Ford font.

DM Sans (fonts/DMSans[opsz,wght].ttf, SIL Open Font License 1.1, see fonts/OFL.txt) is read with
fontTools, instanced at one weight and optical size, and each glyph's TrueType outline (lines and
quadratic curves, exactly what a DefineShape holds) becomes edge records in twips, every path
with the same fill style on its right. Each glyph's contours are reversed (fontTools'
ReverseContourPen), so once y points down a glyph's outer contour and its holes keep opposite
directions and the player cuts the holes out; FFDec's renders confirmed it. No kerning: the
headings are short and the glyphs' advance widths are enough.
"""
from __future__ import annotations

from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONT = Path(__file__).resolve().parent.parent / "fonts" / "DMSans[opsz,wght].ttf"
TWIP = 20


class EdgePen(BasePen):
    """Collects contours as absolute points in font units: ("move", x, y), ("line", x, y),
    ("quad", cx, cy, x, y)."""

    def __init__(self, glyphset) -> None:
        super().__init__(glyphset)
        self.contours: list[list[tuple]] = []

    def _moveTo(self, p):
        self.contours.append([("move", *p)])

    def _lineTo(self, p):
        self.contours[-1].append(("line", *p))

    def _qCurveToOne(self, c, p):
        self.contours[-1].append(("quad", *c, *p))

    def _curveToOne(self, c1, c2, p):
        raise ValueError("a cubic curve: not a TrueType outline")

    def _closePath(self):
        pass

    def _endPath(self):
        pass


class Face:
    """One instance of the font: weight 560 and optical size 14 suit 16-18 px headings."""

    def __init__(self, weight: float = 560, optical: float = 14, path: Path = FONT) -> None:
        font = TTFont(path)
        self.font = instantiateVariableFont(font, {"wght": weight, "opsz": optical}, inplace=False)
        self.upm = self.font["head"].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.family = self.font["name"].getDebugName(1)
        self.cap_height = self.font["OS/2"].sCapHeight / self.upm

    def glyph(self, char: str) -> tuple[list[list[tuple]], float]:
        """The reversed contours of one character, and its advance width, in font units."""
        name = self.cmap[ord(char)]
        pen = EdgePen(self.glyphs)
        self.glyphs[name].draw(ReverseContourPen(pen))
        return pen.contours, self.glyphs[name].width

    def width(self, text: str, size: float) -> float:
        """The advance of `text` at `size` px."""
        return sum(self.glyph(ch)[1] for ch in text) * size / self.upm

    def edges(self, text: str, x: float, baseline: float, size: float) -> list[list[tuple]]:
        """Edge records (twips, relative, as xmlswf.shape_xml wants them) of `text` at `size` px
        with its left at x px and its baseline at `baseline` px; one closed list per contour."""
        scale = size / self.upm
        out = []
        pen_x = x
        for ch in text:
            contours, advance = self.glyph(ch)
            for contour in contours:
                pts = []
                for seg in contour:
                    if seg[0] == "quad":
                        pts.append(("quad", (pen_x + seg[1] * scale) * TWIP, (baseline - seg[2] * scale) * TWIP,
                                    (pen_x + seg[3] * scale) * TWIP, (baseline - seg[4] * scale) * TWIP))
                    else:
                        pts.append((seg[0], (pen_x + seg[1] * scale) * TWIP, (baseline - seg[2] * scale) * TWIP))
                edges = []
                px = py = 0
                start = (0, 0)
                for seg in pts:
                    if seg[0] == "move":
                        px, py = int(round(seg[1])), int(round(seg[2]))
                        start = (px, py)
                        edges.append(("move", px, py))
                    elif seg[0] == "line":
                        nx, ny = int(round(seg[1])), int(round(seg[2]))
                        edges.append(("line", nx - px, ny - py))
                        px, py = nx, ny
                    else:
                        cx, cy = int(round(seg[1])), int(round(seg[2]))
                        ax, ay = int(round(seg[3])), int(round(seg[4]))
                        edges.append(("curve", cx - px, cy - py, ax - cx, ay - cy))
                        px, py = ax, ay
                if (px, py) != start:
                    edges.append(("line", start[0] - px, start[1] - py))
                out.append(edges)
            pen_x += advance * scale
        return out
