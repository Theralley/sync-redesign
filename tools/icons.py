"""One icon family for the redesign (our own drawings): the same line weight, rounded ends and
24-unit grid everywhere, so tiles, the area bar and the climate controls read as one set.

draw(draw, name, cx, cy, size, color): size is the icon's width in pixels; the stroke is 1/12
of it (2 units of 24), never thinner than 2 px, so it survives SYNC's 16-bit screen.
"""
import math

NAMES = ("phone", "map", "home", "media", "climate", "apps", "settings", "carplay", "video", "files",
         "restart", "voice", "seat", "defrost", "defrost_max", "rear", "ac", "ac_max", "recirc", "fan",
         "air_face", "air_feet", "air_screen", "power", "dual", "min_temp")


def draw(d, name, cx, cy, size, color):
    u = size / 24.0  # one grid unit
    w = max(2, round(2 * u))

    def p(x, y):  # grid (0..24) to pixels
        return (cx + (x - 12) * u, cy + (y - 12) * u)

    def line(*points):
        pts = [p(*pt) for pt in points]
        d.line(pts, fill=color, width=w, joint="curve")
        for pt in (pts[0], pts[-1]):  # rounded ends
            d.ellipse((pt[0] - w / 2, pt[1] - w / 2, pt[0] + w / 2, pt[1] + w / 2), fill=color)

    def box(x0, y0, x1, y1, r=2.5):
        d.rounded_rectangle((*p(x0, y0), *p(x1, y1)), radius=r * u, outline=color, width=w)

    def circle(x, y, r, fill=False):
        a, b = p(x - r, y - r), p(x + r, y + r)
        d.ellipse((*a, *b), outline=color, width=w, fill=color if fill else None)

    def arc(x, y, r, start, end):
        a, b = p(x - r, y - r), p(x + r, y + r)
        d.arc((*a, *b), start=start, end=end, fill=color, width=w)

    def tri(*points):
        d.polygon([p(*pt) for pt in points], fill=color)

    def waves(x0, y0):  # three heat waves
        for i in range(3):
            x = x0 + i * 3.5
            line((x, y0), (x + 1.2, y0 - 2), (x, y0 - 4), (x + 1.2, y0 - 6))

    if name == "phone":
        box(7, 2.5, 17, 21.5, 3); line((10.5, 18.5), (13.5, 18.5))
    elif name == "map":
        line((3, 6), (9, 3.5), (15, 6), (21, 3.5), (21, 18), (15, 20.5), (9, 18), (3, 20.5), (3, 6))
        line((9, 3.5), (9, 18)); line((15, 6), (15, 20.5))
    elif name == "home":
        line((3, 11.5), (12, 3.5), (21, 11.5)); line((5.5, 9.5), (5.5, 20.5), (18.5, 20.5), (18.5, 9.5))
        line((10, 20.5), (10, 14.5), (14, 14.5), (14, 20.5))
    elif name == "media":
        line((9, 18), (9, 4.5), (20, 3), (20, 16)); circle(6.5, 18, 2.7, True); circle(17.5, 16, 2.7, True)
    elif name == "climate":  # a thermometer with warm air beside it
        box(5.5, 2.5, 10.5, 15.5, 2.5); circle(8, 18.5, 3.5, True)
        for y in (6, 11, 16):
            line((14, y), (15.5, y - 1.5), (17, y), (18.5, y - 1.5), (20.5, y))
    elif name == "apps":
        for gx in (6, 12, 18):
            for gy in (6, 12, 18):
                circle(gx, gy, 1.4, True)
    elif name == "settings":
        circle(12, 12, 3.2)
        for a in range(0, 360, 45):
            line(p2(12, 12, 6.5, a), p2(12, 12, 9.5, a))
        circle(12, 12, 6.5)
    elif name == "carplay":
        box(3, 5, 21, 19, 3); tri((10, 8.5), (10, 15.5), (16, 12))
    elif name == "video":
        circle(12, 12, 9); tri((10, 8), (10, 16), (16.5, 12))
    elif name == "files":
        line((3, 7), (3, 19.5), (21, 19.5), (21, 8.5), (11.5, 8.5), (9.5, 5.5), (3, 5.5), (3, 7))
    elif name == "restart":
        arc(12, 12, 8.5, -50, 250); tri((17.5, 3.2), (21.8, 7.6), (16, 9.5))
    elif name == "voice":
        box(9, 2.5, 15, 14.5, 3); arc(12, 9.5, 7, 20, 160); line((12, 16.5), (12, 21)); line((8.5, 21), (15.5, 21))
    elif name == "seat":
        line((7, 3.5), (8.5, 14), (17, 14), (18.5, 20.5)); line((8.5, 14), (6.5, 20.5)); waves(10.5, 10)
    elif name in ("defrost", "defrost_max"):
        line((3, 16), (6, 8), (18, 8), (21, 16), (3, 16)); waves(8.5, 14.5)
        if name == "defrost_max":
            line((4, 20.5), (20, 20.5))
    elif name == "rear":
        box(3, 6, 21, 17, 2); waves(8.5, 15); line((4, 20.5), (20, 20.5))
    elif name in ("ac", "ac_max"):  # a snowflake
        for a in (30, 90, 150, 210, 270, 330):
            line((12, 12), p2(12, 12, 9.5, a))
            line(p2(12, 12, 6, a), p2(*p2(12, 12, 6, a), 3, a + 40))
            line(p2(12, 12, 6, a), p2(*p2(12, 12, 6, a), 3, a - 40))
        if name == "ac_max":
            circle(12, 12, 3)
    elif name == "recirc":
        line((3, 17.5), (21, 17.5)); line((5, 17.5), (7, 11), (17, 11), (19, 17.5))
        arc(12, 8.5, 4.5, 180, 360); tri((15.6, 9.6), (18.4, 8), (17, 5.5))
    elif name == "fan":  # three rounded blades around a hub
        circle(12, 12, 2.2, True)
        for a in (-90, 30, 150):
            blade = [p2(12, 12, 2.5, a - 20), p2(12, 12, 6, a - 32), p2(12, 12, 9.5, a - 22),
                     p2(12, 12, 10, a + 5), p2(12, 12, 7, a + 22), p2(12, 12, 2.5, a + 20)]
            d.polygon([p(*pt) for pt in blade], outline=color, width=w)
    elif name in ("air_face", "air_feet", "air_screen"):
        circle(14.5, 4.5, 2.2); line((14.5, 7.5), (13, 14), (18, 14), (19.5, 21)); line((13, 14), (8.5, 19))
        start, end = {"air_face": ((2.5, 9), (10, 6)), "air_feet": ((2.5, 13), (7, 19.5)),
                      "air_screen": ((2.5, 11), (7, 2.5))}[name]
        line(start, end)
        angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
        tri(end, p2(*end, 3.2, angle + 150), p2(*end, 3.2, angle - 150))
    elif name == "power":
        arc(12, 13, 8, -55, 235); line((12, 3), (12, 12))
    elif name == "dual":
        line((8, 4), (8, 20)); line((16, 4), (16, 20)); line((3, 12), (8, 12)); line((16, 12), (21, 12))
    elif name == "min_temp":
        box(9.5, 2.5, 14.5, 16, 2.5); circle(12, 18.5, 3.5, True); line((17.5, 6), (21, 6))
    else:
        raise ValueError(name)


def p2(cx, cy, r, degrees):
    """A grid point at radius r and angle degrees around (cx, cy)."""
    a = math.radians(degrees)
    return (cx + r * math.cos(a), cy + r * math.sin(a))
