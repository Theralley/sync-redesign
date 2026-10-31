"""Draw the sketches of a complete SYNC 2 redesign, one per screen (our own drawings).

Usage: python3 tools/mockup_redesign.py docs/mockups [--lang sv|en]
Writes redesign-<screen>.png (800x480, SYNC 2's screen), a day and a night Home, and
redesign-overview.png. Swedish is the default language. Needs Pillow.

Rules the sketches follow (docs/UX-REVIEW.md): one main value per card that reads in under a
second; text contrast at least 7:1 (main) and 4.5:1 (secondary); touch targets at least 80 px
high (about 18 mm, enough with gloves); sentence case, no capitals for labels; one icon family
(icons.py). Climate keeps every control where Ford put it.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import icons

W, H = 800, 480
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
TOP, BOTTOM = 44, 64
TARGET = 80  # smallest touch target, px

DAY = {"bg": (14, 16, 20), "panel": (30, 33, 40), "panel2": (44, 48, 58), "text": (245, 246, 248),
       "dim": (170, 176, 188), "bar": (8, 9, 12), "on": (255, 196, 64),
       "area": {"phone": (226, 170, 80), "nav": (80, 200, 160), "media": (230, 86, 94),
                "climate": (80, 160, 255), "home": (170, 170, 180)}}
NIGHT = {**DAY, "text": (214, 217, 224), "dim": (150, 156, 168), "on": (214, 160, 52),
         "area": {k: tuple(round(c * 0.78) for c in v) for k, v in DAY["area"].items()}}

WORDS = {
    "sv": {"phone": "Telefon", "nav": "Karta", "home": "Hem", "media": "Media", "climate": "Klimat",
           "playing": "Spelas nu", "route": "Vägbeskrivning", "home_dest": "Hem", "eta": "24 min, framme 12:07",
           "recent": "Senaste samtal", "keypad": "Knappsats", "contacts": "Kontakter", "favourites": "Favoriter",
           "messages": "Meddelanden", "voice": "Säg \"Ring ...\"", "yesterday": "igår", "mon": "mån",
           "turn": "Sväng höger mot E18", "in": "Om 400 m", "distance": "24 min, 18 km", "arrive": "framme 12:07",
           "sources": "Källa", "presets": "Förval", "save": "Spara", "outside": "6° ute", "auto": "Auto",
           "driver": "Förare", "passenger": "Passagerare", "min_temp": "Min temp", "dual": "Dual",
           "max": "Max", "rear": "Bakruta", "ac": "A/C", "max_ac": "Max A/C", "recirc": "Återluft",
           "fan": "Fläkt", "work": "Jobbet", "garage": "Verkstan", "off": "Av", "decimal": ","},
    "en": {"phone": "Phone", "nav": "Map", "home": "Home", "media": "Media", "climate": "Climate",
           "playing": "Now playing", "route": "Route", "home_dest": "Home", "eta": "24 min, arrive 12:07",
           "recent": "Recent calls", "keypad": "Keypad", "contacts": "Contacts", "favourites": "Favourites",
           "messages": "Messages", "voice": "Say \"Call ...\"", "yesterday": "yesterday", "mon": "Mon",
           "turn": "Turn right onto E18", "in": "In 400 m", "distance": "24 min, 18 km", "arrive": "arrive 12:07",
           "sources": "Source", "presets": "Presets", "save": "Save", "outside": "6° outside", "auto": "Auto",
           "driver": "Driver", "passenger": "Passenger", "min_temp": "Min temp", "dual": "Dual",
           "max": "Max", "rear": "Rear", "ac": "A/C", "max_ac": "Max A/C", "recirc": "Recirc",
           "fan": "Fan", "work": "Work", "garage": "Garage", "off": "Off", "decimal": "."},
}


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


class Screen:
    def __init__(self, theme, words, dual=False):
        self.t, self.w = theme, words
        self.dual = dual  # Ford's Climate.DUALBUTTONSTATE: the passenger has a temperature of their own
        self.temps = (19.0, 21.5)  # Climate.TEMPDRIVERSET, Climate.TEMPCODRIVERSET
        self.image = Image.new("RGB", (W, H), theme["bg"])
        self.d = ImageDraw.Draw(self.image)

    def deg(self, value):
        """A temperature the way the language writes it: 19,0° in Swedish, 19.0° in English."""
        return f"{value:.1f}°".replace(".", self.w["decimal"])

    def text(self, xy, value, size, bold=False, color=None, anchor="la"):
        self.d.text(xy, value, font=font(size, bold), fill=color or self.t["text"], anchor=anchor)

    def card(self, box, accent=None, fill=None):
        self.d.rounded_rectangle(box, radius=12, fill=fill or self.t["panel"])
        if accent:
            self.d.rounded_rectangle((box[0], box[1], box[0] + 6, box[3]), radius=3, fill=accent)

    def button(self, box, label=None, icon=None, accent=None, on=None, size=18):
        """A control: icon above a label (or either alone); `on` draws its state light."""
        self.d.rounded_rectangle(box, radius=10, fill=self.t["panel2"])
        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        if icon and label:
            icons.draw(self.d, icon, cx, cy - 11, 30, accent or self.t["text"])
            self.text((cx, box[3] - 14), label, 14, True, anchor="mm")
        elif icon:
            icons.draw(self.d, icon, cx, cy, min(40, box[3] - box[1] - 24), accent or self.t["text"])
        elif label:
            self.text((cx, cy), label, size, True, anchor="mm")
        if on is not None:  # a lamp in the top right corner, lit when the function is on
            colour = self.t["on"] if on else self.t["bg"]
            self.d.rounded_rectangle((box[2] - 18, box[1] + 8, box[2] - 8, box[1] + 12), radius=2, fill=colour)

    def frame(self, area, title):
        t, d = self.t, self.d
        d.rectangle((0, 0, W, TOP), fill=t["bar"])
        self.text((16, TOP // 2), title, 20, True, anchor="lm")
        self.text((W // 2, TOP // 2), "12:23", 22, True, anchor="mm")
        self.text((W - 16, TOP // 2), f"{self.w['outside']}   iPhone", 16, color=t["dim"], anchor="rm")
        d.rectangle((0, H - BOTTOM, W, H), fill=t["bar"])
        items = ["phone", "nav", "home", "media", "climate"]
        width = W // len(items)
        for i, key in enumerate(items):
            x, active = i * width, key == area
            if active:
                d.rectangle((x, H - BOTTOM, x + width, H), fill=t["panel"])
            d.rectangle((x + 24, H - BOTTOM, x + width - 24, H - BOTTOM + 3), fill=t["area"][key])
            icon = {"nav": "map", "home": "home"}.get(key, key)
            colour = t["text"] if active else t["dim"]
            icons.draw(d, icon, x + width // 2, H - BOTTOM + 24, 24, colour)
            if key == "climate":  # the set temperature in place of the word, both with Dual on
                cx = x + width // 2
                if self.dual:
                    self.text((cx - 8, H - 14), self.deg(self.temps[0]), 15, True, t["text"], "rm")
                    d.line((cx, H - 22, cx, H - 7), fill=t["dim"], width=1)
                    self.text((cx + 8, H - 14), self.deg(self.temps[1]), 15, True, t["text"], "lm")
                else:
                    self.text((cx, H - 14), self.deg(self.temps[0]), 15, True, t["text"], "mm")
            else:
                self.text((x + width // 2, H - 14), self.w[key], 14, active, colour, "mm")

    def symbol(self, box, kind):
        """Media keys, drawn (the fonts lack them)."""
        self.d.rounded_rectangle(box, radius=10, fill=self.t["panel2"])
        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        r, c = 13, self.t["text"]
        if kind == "play":
            self.d.polygon([(cx - r * 0.7, cy - r), (cx - r * 0.7, cy + r), (cx + r, cy)], fill=c)
        else:
            sign = -1 if kind == "prev" else 1
            for k in (0, 1):
                x = cx + sign * (k * r - r * 0.5)
                self.d.polygon([(x - sign * r * 0.5, cy - r * 0.8), (x - sign * r * 0.5, cy + r * 0.8),
                                (x + sign * r * 0.5, cy)], fill=c)


def home(s):
    w, a = s.w, s.t["area"]
    s.frame("home", w["home"])
    y0, y1 = TOP + 12, H - BOTTOM - 12
    s.card((12, y0, 396, y1), a["media"])
    s.text((36, y0 + 18), f"{w['playing']}: NRJ", 16, color=s.t["dim"])
    s.text((36, y0 + 46), "Money For Nothing", 30, True)
    s.text((36, y0 + 88), "Dire Straits", 20, color=s.t["dim"])
    for i, kind in enumerate(("prev", "play", "next")):
        s.symbol((36 + i * 118, y1 - 100, 142 + i * 118, y1 - 20), kind)
    s.card((408, y0, 788, y0 + 164), a["nav"])
    s.text((432, y0 + 18), w["route"], 16, color=s.t["dim"])
    s.text((432, y0 + 46), w["home_dest"], 30, True)
    s.text((432, y0 + 92), w["eta"], 20, color=s.t["dim"])
    s.card((408, y0 + 176, 592, y1), a["phone"])
    s.text((430, y0 + 194), w["phone"], 16, color=s.t["dim"])
    s.text((430, y0 + 222), "iPhone", 24, True)
    s.card((604, y0 + 176, 788, y1), a["climate"])
    s.text((626, y0 + 194), w["climate"], 16, color=s.t["dim"])
    s.text((626, y0 + 220), s.deg(s.temps[0]), 34, True)
    s.text((626, y0 + 262), w["auto"], 16, color=s.t["dim"])


def media(s):
    w, a = s.w, s.t["area"]
    s.frame("media", w["media"])
    y0, y1 = TOP + 12, H - BOTTOM - 12
    s.card((12, y0, 248, y1))
    for i, (label, on) in enumerate((("FM", True), ("DAB", False), ("USB", False), ("Bluetooth", False))):
        y = y0 + 12 + i * 84
        s.d.rounded_rectangle((24, y, 236, y + 76), radius=10, fill=s.t["panel2"] if on else s.t["panel"])
        if on:
            s.d.rectangle((24, y + 18, 28, y + 58), fill=a["media"])
        s.text((44, y + 38), label, 22, on, s.t["text"] if on else s.t["dim"], "lm")
    s.card((260, y0, 788, y0 + 172), a["media"])
    s.text((286, y0 + 18), "FM 104,7", 16, color=s.t["dim"])
    s.text((286, y0 + 46), "NRJ", 34, True)
    s.text((286, y0 + 96), "Money For Nothing, Dire Straits", 20, color=s.t["dim"])
    for i, kind in enumerate(("prev", "play", "next")):
        s.symbol((260 + i * 132, y0 + 184, 384 + i * 132, y0 + 264), kind)
    s.button((260 + 3 * 132, y0 + 184, 788, y0 + 264), w["save"])
    for i, label in enumerate(("NRJ", "P3", "Mix", "Rock")):
        s.button((260 + i * 132, y0 + 276, 384 + i * 132, y1), label, size=17)


def phone(s):
    w, a = s.w, s.t["area"]
    s.frame("phone", w["phone"])
    y0, y1 = TOP + 12, H - BOTTOM - 12
    s.card((12, y0, 396, y1), a["phone"])
    s.text((36, y0 + 16), w["recent"], 16, color=s.t["dim"])
    for i, (name, when) in enumerate((("Anna", "11:02"), (w["work"], "10:41"), ("Erik", w["yesterday"]),
                                      (w["garage"], w["mon"]))):
        y = y0 + 44 + i * 80
        if i:
            s.d.line((36, y, 376, y), fill=s.t["panel2"], width=1)
        s.text((36, y + 40), name, 24, True, anchor="lm")
        s.text((376, y + 40), when, 18, color=s.t["dim"], anchor="rm")
    for i, (label, icon) in enumerate(((w["keypad"], "apps"), (w["contacts"], "phone"),
                                       (w["favourites"], "home"), (w["messages"], "media"))):
        r, c = divmod(i, 2)
        s.button((408 + c * 196, y0 + r * 112, 592 + c * 196, y0 + 100 + r * 112), label)
    s.button((408, y0 + 224, 788, y1), w["voice"], size=20)


def climate(s):
    """Ford's climate layout, control for control, in the new style: nothing moves."""
    w, a = s.w, s.t["area"]
    s.frame("climate", w["climate"])
    blue, red = a["climate"], a["media"]
    y = TOP + 12
    for x0, side in ((12, w["driver"]), (548, w["passenger"])):  # temperatures, top left and right
        s.card((x0, y, x0 + 240, y + 84))
        s.button((x0 + 8, y + 8, x0 + 64, y + 76), "–", size=30)
        s.text((x0 + 120, y + 34), s.deg(s.temps[0] if side == w["driver"] or not s.dual else s.temps[1]), 30, True,
               anchor="mm")
        s.text((x0 + 120, y + 66), side, 13, color=s.t["dim"], anchor="mm")
        s.button((x0 + 176, y + 8, x0 + 232, y + 76), "+", size=30)
    s.button((352, y, 448, y + 84), w["auto"], "power", on=True)  # power, top centre
    y = TOP + 108
    s.button((12, y, 128, y + 136), w["off"], "seat", red, on=False)  # driver seat heat
    s.button((136, y, 252, y + 136), w["min_temp"], "min_temp", on=False)
    for i, icon in enumerate(("air_screen", "air_face", "air_feet")):  # air distribution, three stacked
        s.button((264, y + i * 46, 396, y + 42 + i * 46), None, icon, on=icon == "air_feet")
    s.button((404, y, 536, y + 42), "+", size=26)  # fan
    s.d.rounded_rectangle((404, y + 46, 536, y + 88), radius=10, fill=s.t["panel2"])
    icons.draw(s.d, "fan", 434, y + 67, 26, s.t["text"])
    for k in range(7):
        s.d.rectangle((456 + k * 10, y + 76 - k * 3, 462 + k * 10, y + 80), fill=blue if k < 3 else s.t["panel"])
    s.button((404, y + 92, 536, y + 134), "–", size=26)
    s.button((548, y, 664, y + 136), w["dual"], "dual", on=False)
    s.button((672, y, 788, y + 136), w["off"], "seat", red, on=False)  # passenger seat heat
    y = H - BOTTOM - 12 - TARGET  # the bottom row, in Ford's order
    row = [("defrost", None), ("defrost_max", w["max"]), ("rear", w["rear"]), (None, w["auto"]),
           ("ac", w["ac"]), ("ac_max", w["max_ac"]), ("recirc", w["recirc"])]
    width = (W - 24 - 6 * 6) // 7
    for i, (icon, label) in enumerate(row):
        x = 12 + i * (width + 6)
        s.button((x, y, x + width, y + TARGET), label, icon, None, on=label in (w["auto"], w["ac"]),
                 size=20 if icon is None else 18)


def nav(s):
    w, a = s.w, s.t["area"]
    s.frame("nav", w["nav"])
    y0, y1 = TOP, H - BOTTOM
    s.d.rectangle((0, y0, W, y1), fill=(28, 34, 30))  # stands in for Ford's own map, which stays
    for x in range(0, W, 60):
        s.d.line((x, y0, x + 140, y1), fill=(40, 48, 42), width=2)
    s.d.line((0, 330, W, 250), fill=(80, 96, 84), width=10)
    s.text((W // 2, (y0 + y1) // 2 + 30), "Fords karta (oförändrad)" if w is WORDS["sv"] else "Ford's map (unchanged)",
           16, color=(120, 140, 125), anchor="mm")
    s.card((12, y0 + 12, 340, y0 + 112), a["nav"])
    s.text((36, y0 + 26), w["in"], 18, color=s.t["dim"])
    s.text((36, y0 + 56), w["turn"], 24, True)
    s.card((W - 232, y1 - 92, W - 12, y1 - 12))
    s.text((W - 212, y1 - 72), w["distance"], 20, True)
    s.text((W - 212, y1 - 42), w["arrive"], 18, color=s.t["dim"])
    s.button((W - 92, y0 + 12, W - 12, y0 + 92), "+", size=30)
    s.button((W - 92, y0 + 100, W - 12, y0 + 180), "–", size=30)


def speed_box(s, x, y, limit, speed):
    """The speed box on the map: the speed limit as a Swedish sign (yellow, red ring) from Ford's
    map data, and the GPS speed beside it. Over the limit (+3 km/h) a quiet amber mark shows: the
    card's edge and a short line under the number. The number keeps its colour; nothing blinks."""
    over = speed > limit + 3
    amber = (255, 176, 32)
    s.card((x, y, x + 236, y + 104), amber if over else None)
    r, cx, cy = 40, x + 58, y + 52
    s.d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 204, 0))
    s.d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(208, 32, 44), width=9)
    s.text((cx, cy + 1), str(limit), 30, True, (0, 0, 0), "mm")
    s.text((x + 168, y + 42), str(speed), 44, True, anchor="mm")
    if over:
        s.d.rounded_rectangle((x + 146, y + 68, x + 190, y + 72), radius=2, fill=amber)
    s.text((x + 168, y + 88), "km/h (GPS)", 14, color=s.t["dim"], anchor="mm")


def nav_speed(s, speed=68):
    nav(s)
    speed_box(s, 12, H - BOTTOM - 116, 70, speed)


SCREENS = {"home": home, "media": media, "phone": phone, "climate": climate, "nav": nav}


def main(out, lang):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    pictures = []
    for name, draw_screen in SCREENS.items():
        screen = Screen(DAY, WORDS[lang], dual=name == "media")
        draw_screen(screen)
        screen.image.save(out / f"redesign-{name}.png")
        pictures.append((name, screen.image))
    for name, speed in (("nav-speed", 68), ("nav-speed-over", 82)):
        screen = Screen(DAY, WORDS[lang])
        nav_speed(screen, speed)
        screen.image.save(out / f"redesign-{name}.png")
    night = Screen(NIGHT, WORDS[lang])
    home(night)
    night.image.save(out / "redesign-home-night.png")
    pictures.append(("home, night", night.image))
    sheet = Image.new("RGB", (W + 30, 3 * (H // 2 + 30)), (255, 255, 255))
    for i, (name, image) in enumerate(pictures):
        x, y = (i % 2) * (W // 2 + 10), (i // 2) * (H // 2 + 30)
        sheet.paste(image.resize((W // 2, H // 2), Image.LANCZOS), (x, y + 22))
        ImageDraw.Draw(sheet).text((x + 4, y + 4), name, font=font(16, True), fill=(0, 0, 0))
    sheet.save(out / "redesign-overview.png")
    print(f"{len(pictures)} sketches ({lang}) in {out}")


if __name__ == "__main__":
    lang = sys.argv[3] if len(sys.argv) == 4 and sys.argv[2] == "--lang" else "sv"
    if len(sys.argv) not in (2, 4) or lang not in WORDS:
        raise SystemExit(__doc__)
    main(sys.argv[1], lang)
