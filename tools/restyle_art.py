"""The restyle's artwork (plan phase R4): Ford's pictures redrawn flat, in the Night palette.

Ford's look is pictures, not code: the gloss on every button is a strip that SYNC tiles across
it, the bars round the screen are pictures, and so are the icons and indicator lights. Each is
redrawn here at exactly its size, so nothing on the screen moves:

- button strips: one flat colour per state; a selected button is tinted with its area's colour
  and carries a line of it along the top;
- bar pieces: Ford's outline kept to the pixel (so the pieces still fit together), the carbon
  texture and the shine replaced by one flat colour and a quiet edge, Ford's icon by ours;
- indicator lights: a flat pill, lit or not, without the glow;
- icons: ours (icons.py), the same line weight everywhere.

Only our own drawings come from here; Ford's pictures are read from the car's file and used
for their outline and sizes alone. The last functions are frame v2's (build_frame.py,
build_menus.py): black tabs and launch pieces with a line for the selected one, the side menus'
flat cards.
"""
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import icons

BACKGROUND, BAR, BUTTON = (14, 16, 20), (23, 26, 32), (38, 42, 51)
BAR_PRESSED, BUTTON_PRESSED = (44, 49, 59), (59, 65, 77)
EDGE = (52, 57, 68)  # a quiet edge on the bar pieces
TEXT, QUIET, DIM = (236, 238, 242), (150, 156, 168), (74, 80, 92)
# The car's screen shows dark greys far lighter than their numbers: photographed in daylight on
# 2026-11-02, black came out about 42 of 255, the "night" bars (23,26,32) about 150 and its
# buttons (38,42,51) about 210, as light as Ford's own grey frame. "deep" sits near black.
# "v2" (the sixth visit, DESIGN-V2): the bars black with no line, the Home cards CARD, and the
# button strips a step lighter ("chips22") so a button shows on a card.
CARD, CARD_PRESSED = (10, 11, 14), (17, 19, 23)
PALETTES = {
    "night": dict(BACKGROUND=BACKGROUND, BAR=BAR, BUTTON=BUTTON, BAR_PRESSED=BAR_PRESSED,
                  BUTTON_PRESSED=BUTTON_PRESSED, EDGE=EDGE, DIM=DIM, CARD=BAR, CARD_PRESSED=BAR_PRESSED),
    "deep": dict(BACKGROUND=(0, 0, 0), BAR=(6, 7, 9), BUTTON=(13, 14, 18), BAR_PRESSED=(17, 19, 23),
                 BUTTON_PRESSED=(26, 29, 35), EDGE=(18, 20, 25), DIM=(34, 37, 44), CARD=CARD, CARD_PRESSED=CARD_PRESSED),
    "v2": dict(BACKGROUND=(0, 0, 0), BAR=(0, 0, 0), BUTTON=(22, 24, 30), BAR_PRESSED=(0, 0, 0),
               BUTTON_PRESSED=(34, 37, 45), EDGE=(18, 20, 25), DIM=(34, 37, 44), CARD=CARD, CARD_PRESSED=CARD_PRESSED),
}
# SYNC's area types (Theme.XML's AppTypes): 0 system, 1 phone, 2 navigation, 3 media, 4 climate
ACCENTS = {0: (150, 150, 160), 1: (214, 160, 72), 2: (72, 190, 150), 3: (220, 76, 84), 4: (64, 150, 255)}
LINE = 3  # px: the area colour's line on a selected button and on the bars
TINT, TINT_PRESSED = 0.42, 0.58  # how much of the area colour a selected button takes
WEIGHT = 2.5  # px: the stroke of every bar icon


def use(palette: str) -> None:
    """Draw everything after this in one of PALETTES."""
    globals().update(PALETTES[palette])


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def strip(width: int, height: int, state: str, area: int | None = None) -> Image.Image:
    """A button strip, as SYNC tiles it across a button: AVAILABLE, PRESSED, SELECTED or
    PRESSEDSELECTED, the last two in an area's colour."""
    if state in ("AVAILABLE", "PRESSED"):
        return Image.new("RGBA", (width, height), (*(BUTTON if state == "AVAILABLE" else BUTTON_PRESSED), 255))
    accent = ACCENTS[area]
    image = Image.new("RGBA", (width, height), (*mix(BUTTON, accent, TINT if state == "SELECTED" else TINT_PRESSED), 255))
    ImageDraw.Draw(image).rectangle((0, 0, width - 1, LINE - 1), fill=(*accent, 255))
    return image


def flatten(original: Image.Image, pressed: bool, icon: tuple | None = None) -> Image.Image:
    """A bar piece: Ford's outline (its alpha) kept exactly; inside it one flat colour, a 1.5 px
    quiet edge where Ford had its bevel, and the soft shadow outside left as it is. icon is
    (name, centre x, centre y, size) for ours, drawn where Ford's was."""
    alpha = original.convert("RGBA").getchannel("A")
    solid = alpha.point(lambda v: 255 if v == 255 else 0)
    # the edge runs along transparent pixels only: the picture's own border is where pieces meet
    padded = Image.new("L", (solid.width + 6, solid.height + 6), 255)
    padded.paste(solid, (3, 3))
    inner = padded.filter(ImageFilter.MinFilter(3)).crop((3, 3, 3 + solid.width, 3 + solid.height))
    edge = ImageChops.subtract(solid, inner)
    image = Image.new("RGBA", original.size, (0, 0, 0, 0))
    shadow = ImageChops.subtract(alpha, solid)  # Ford's soft shadow: black, its own alpha
    image.paste((0, 0, 0, 255), (0, 0), shadow)
    image.putalpha(ImageChops.add(shadow, solid))
    image.paste((*(BAR_PRESSED if pressed else BAR), 255), (0, 0), inner)
    image.paste((*EDGE, 255), (0, 0), edge)
    if icon:
        name, x, y, size = icon
        layer = Image.new("RGBA", original.size, (0, 0, 0, 0))
        icons.paste(layer, name, x, y, size, (*(TEXT if pressed else QUIET), 255), WEIGHT)
        image.alpha_composite(Image.composite(layer, Image.new("RGBA", original.size), solid))
    return image


def straight(size: tuple[int, int], pressed: bool, band: tuple[int, int], icon: tuple | None = None,
             line: bool = False) -> Image.Image:
    """A bar piece without Ford's slant: flat in rows band[0] to band[1] - 1 (where the bars run),
    transparent above and below, so the bar is one straight band. A line in the system's colour
    along the band's top marks the selected piece (line=True)."""
    top, bottom = band
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.rectangle((0, top, size[0] - 1, bottom - 1), fill=(*(BAR_PRESSED if pressed else BAR), 255))
    if line:
        d.rectangle((0, top, size[0] - 1, top + LINE - 1), fill=(*ACCENTS[0], 255))
    if icon:
        name, x, y, icon_size = icon
        icons.paste(image, name, x, y, icon_size, (*(TEXT if pressed else QUIET), 255), WEIGHT)
    return image


def bar(size: tuple[int, int], area: int, line_at_top: bool) -> Image.Image:
    """One of the four corner bars: flat, with its area's line where Ford's was."""
    width, height = size
    image = Image.new("RGBA", size, (*BAR, 255))
    top = 0 if line_at_top else height - LINE
    ImageDraw.Draw(image).rectangle((0, top, width - 1, top + LINE - 1), fill=(*ACCENTS[area], 255))
    return image


def light(size: tuple[int, int], box: tuple[int, int, int, int], level: float, colour=ACCENTS[1]) -> Image.Image:
    """An indicator light: a flat pill in box (x0, y0, x1, y1, inclusive), lit to level (0 = off,
    a dark pill; 1 = fully lit), drawn four times larger for smooth edges."""
    k = 4
    big = Image.new("RGBA", (size[0] * k, size[1] * k), (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    r = min(x1 - x0 + 1, y1 - y0 + 1) * k / 2
    shape = (x0 * k, y0 * k, (x1 + 1) * k - 1, (y1 + 1) * k - 1)
    ImageDraw.Draw(big).rounded_rectangle(shape, radius=r, fill=(*DIM, 255))
    if level > 0:
        lit = Image.new("RGBA", big.size, (0, 0, 0, 0))
        ImageDraw.Draw(lit).rounded_rectangle(shape, radius=r, fill=(*colour, round(255 * level)))
        big.alpha_composite(lit)
    return big.resize(size, Image.LANCZOS)


def socket(size: tuple[int, int], box: tuple[int, int, int, int]) -> Image.Image:
    """The dark pill behind a light."""
    k = 4
    big = Image.new("RGBA", (size[0] * k, size[1] * k), (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(big).rounded_rectangle((x0 * k, y0 * k, (x1 + 1) * k - 1, (y1 + 1) * k - 1),
                                          radius=min(x1 - x0 + 1, y1 - y0 + 1) * k / 2, fill=(*BACKGROUND, 255))
    return big.resize(size, Image.LANCZOS)


def icon(size: tuple[int, int], name: str, colour, icon_size: float, centre=None, weight=WEIGHT) -> Image.Image:
    """One of our icons alone on a transparent picture of exactly size."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    x, y = centre or (size[0] / 2, size[1] / 2)
    icons.paste(image, name, x, y, icon_size, (*colour, 255) if len(colour) == 3 else colour, weight)
    return image


def signal(size: tuple[int, int], level: int, icon_size: float) -> Image.Image:
    """Signal strength: all three arcs dim, the first `level` of them lit."""
    image = icon(size, "wifi3", DIM, icon_size)
    image.alpha_composite(icon(size, f"wifi{level}", TEXT, icon_size))
    return image


def recolour(original: Image.Image, colour) -> Image.Image:
    """Ford's shape (its alpha) in one flat colour: thin lines and dividers."""
    image = Image.new("RGBA", original.size, (*colour, 255))
    image.putalpha(original.convert("RGBA").getchannel("A"))
    return image


# Frame v2 (build_frame.py): the launch pieces hang 11 rows above the bar; the bar is rows 11-58
LAUNCH_BAND = (11, 59)
LAUNCH_ICON_Y = 35.5  # the icons' centre inside a piece: screen y 456.5
MENU_GAP = 2  # rows between the side menus' cards


def tab(size: tuple[int, int]) -> Image.Image:
    """A corner tab of frame v2: the bar's colour, no line."""
    return Image.new("RGBA", size, (*BAR, 255))


def clock_piece(size: tuple[int, int], bar_height: int = 48) -> Image.Image:
    """The clock's piece: the bar's colour down to the bar's edge, transparent below."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((0, 0, size[0] - 1, bar_height - 1), fill=(*BAR, 255))
    return image


def launch(size: tuple[int, int], cell: tuple[int, int], icon: tuple, selected: bool, line) -> Image.Image:
    """A launch piece (Info, Home, Settings): transparent above the bar, the bar's colour in its
    band, our icon (name, centre x, size) grey when available and white when selected, and for
    the selected piece a LINE px line in `line` along the bar's top edge across cell (x0, x1)."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    top, bottom = LAUNCH_BAND
    d.rectangle((0, top, size[0] - 1, bottom - 1), fill=(*BAR, 255))
    if selected:
        d.rectangle((cell[0], top, cell[1] - 1, top + LINE - 1), fill=(*line, 255))
    name, cx, icon_size = icon
    icons.paste(image, name, cx, LAUNCH_ICON_Y, icon_size, (*(TEXT if selected else QUIET), 255), WEIGHT)
    return image


def menu_card(size: tuple[int, int], state: str, alpha: bool) -> Image.Image:
    """One of the side menus' 150x50 button pictures, flat: MENU_GAP rows of gap (transparent, or
    the background where the picture has no alpha channel), then the card; "pressed" in
    CARD_PRESSED; "selected" with a LINE px line down the left edge in the system colour."""
    image = Image.new("RGBA", size, (0, 0, 0, 0) if alpha else (*BACKGROUND, 255))
    d = ImageDraw.Draw(image)
    d.rectangle((0, MENU_GAP, size[0] - 1, size[1] - 1), fill=(*(CARD_PRESSED if state == "pressed" else CARD), 255))
    if state == "selected":
        d.rectangle((0, MENU_GAP, LINE - 1, size[1] - 1), fill=(*ACCENTS[0], 255))
    return image


def panel(size: tuple[int, int]) -> Image.Image:
    """The side menus' panel picture: the background, so the cards stand on it as on Home."""
    return Image.new("RGBA", size, (*BACKGROUND, 255))
