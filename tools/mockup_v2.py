"""Draw the aim right now: version 2's Home screen (our own drawing, no Ford picture).

Usage: python3 tools/mockup_v2.py OUT.png [--scale N]

Version 2 rebuilds the frame and Home on one 8 px grid (docs/BILTEST.md, the sixth and seventh
visits): four equal cards, x 8-396 and 404-792, y 56-236 and 244-424, each with a heading in its
area's colour; black bars, on Home only the clock on top and Info, Home and Settings below, a
line over the selected one; flat buttons a step lighter than the cards, no outlines. The numbers
and colours are the ones the build tools use (restyle_art's "v2" palette); the texts are samples.
In the car Ford's own font draws the cards' contents; here everything is DM Sans (fonts/).
Default scale 2 (1600x960), so the picture stays sharp on a high-density screen.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import icons
import restyle_art as art

FONT = Path(__file__).resolve().parent.parent / "fonts" / "DMSans[opsz,wght].ttf"
art.use("v2")
BACKGROUND, CARD, BUTTON = art.BACKGROUND, art.CARD, art.BUTTON
SELECTED = art.mix(BUTTON, (236, 238, 242), 0.22)  # the selected preset
TEXT, QUIET = art.TEXT, art.QUIET
PHONE, NAV, MEDIA, CLIMATE = (art.ACCENTS[i] for i in (1, 2, 3, 4))
HEAT = (232, 92, 52)  # a lit seat-heat step
CARDS = {"phone": (8, 56, 396, 236), "nav": (404, 56, 792, 236),
         "media": (8, 244, 396, 424), "climate": (404, 244, 792, 424)}
HEADINGS = {"phone": ("Telefon", PHONE, "phone"), "nav": ("Navigation", NAV, "map"),
            "media": ("Media", MEDIA, "media"), "climate": ("Klimat", CLIMATE, "climate")}


class Canvas:
    """800x480 coordinates, drawn `scale` times larger."""

    def __init__(self, scale: int):
        self.k = scale
        self.image = Image.new("RGB", (800 * scale, 480 * scale), BACKGROUND)
        self.d = ImageDraw.Draw(self.image)

    def font(self, size: float, weight: int = 450):
        font = ImageFont.truetype(str(FONT), round(size * self.k))
        font.set_variation_by_axes([min(40, max(9, size)), weight])
        return font

    def box(self, xy, fill, radius=0):
        x0, y0, x1, y1 = (v * self.k for v in xy)
        self.d.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=radius * self.k, fill=fill)

    def text(self, xy, value, size, color=TEXT, anchor="ls", weight=450):
        self.d.text((xy[0] * self.k, xy[1] * self.k), value, font=self.font(size, weight), fill=color, anchor=anchor)

    def icon(self, name, cx, cy, size, color, weight=None):
        icons.paste(self.image, name, cx * self.k, cy * self.k, size * self.k, color,
                    (weight or max(2, size / 12)) * self.k)


def draw(scale: int = 2) -> Image.Image:
    c = Canvas(scale)
    # top bar: on Home only the clock and the outside temperature, centred
    c.text((400, 36), "12:53   7°", 30, anchor="ms", weight=400)
    # the four cards and their headings (icon, then the name, baseline 27 below the card's top)
    for key, (x0, y0, x1, y1) in CARDS.items():
        c.box((x0, y0, x1, y1), CARD, radius=12)
        name, colour, icon = HEADINGS[key]
        c.icon(icon, x0 + 24, y0 + 21, 16, colour, 1.8)
        c.text((x0 + 40, y0 + 27), name, 18, colour, weight=560)
    # phone: battery and signal at the right of the heading line; the status and one chip
    c.box((345, 70, 365, 80), QUIET, radius=2)
    c.box((347, 72, 363, 78), CARD, radius=1)
    c.box((348, 73, 360, 77), QUIET)
    c.box((365, 73, 367, 77), QUIET)
    for bar in range(4):  # signal: four bars, rising
        c.box((372 + bar * 3, 78 - bar * 3, 374 + bar * 3, 81), QUIET)
    c.text((202, 141), "Telefon ansluten", 26, anchor="ms")
    c.box((92, 162, 312, 206), BUTTON, radius=3)
    c.text((109, 191), "Stör inte", 20, anchor="ls")
    c.box((292, 174, 295, 194), QUIET)
    # navigation: the street, centred
    c.text((600, 171), "Storgatan", 30, anchor="ms")
    # media: the station, centred, and six flat presets, 8 px apart, 16 px inside the card
    c.text((202, 316), "P4", 40, anchor="ms", weight=500)
    presets = ("P1", "P2", "P3", "P4", "MIX", "ROCK")
    for i, label in enumerate(presets):
        x, y = 24 + (i % 3) * 122, 328 + (i // 3) * 48
        c.box((x, y, x + 112, y + 40), SELECTED if label == "P4" else BUTTON, radius=3)
        c.text((x + 56, y + 27), label, 18, anchor="ms")
    # climate: the set temperatures small at the right of the heading line, the seats centred
    c.text((776, 271), "20.5°   19.5°", 18, QUIET, anchor="rs")
    for i, x in enumerate((486, 627)):
        c.box((x, 310, x + 84, 386), BUTTON, radius=3)
        c.icon("seat", x + 42, 340, 34, TEXT, 2.4)
        for step in range(3):
            lit = i == 0
            c.box((x + 22 + step * 14, 370, x + 34 + step * 14, 375), HEAT if lit else art.DIM, radius=2)
    # bottom bar: Info, Home (selected: white, a line over its cell), Settings
    c.box((364, 432, 436, 435), TEXT)
    c.icon("info", 320, 456.5, 26, QUIET, 2.5)
    c.icon("home", 400, 456.5, 28, TEXT, 2.5)
    c.icon("settings", 480, 456.5, 26, QUIET, 2.5)
    return c.image


def main(argv: list[str]) -> None:
    scale = int(argv[argv.index("--scale") + 1]) if "--scale" in argv else 2
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--scale")]
    if len(args) != 1 or not 1 <= scale <= 4:
        raise SystemExit(__doc__)
    draw(scale).save(args[0])
    print(f"{args[0]}: version 2's Home, {800 * scale}x{480 * scale} (our own drawing)")


if __name__ == "__main__":
    main(sys.argv[1:])
