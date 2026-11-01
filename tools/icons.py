"""One icon family for the redesign (our own drawings): the same line weight, rounded ends and
24-unit grid everywhere, so tiles, the area bar and the climate controls read as one set.

draw(draw, name, cx, cy, size, color, width=None): size is the icon's width in pixels; the stroke
is 1/12 of it (2 units of 24), never thinner than 2 px, so it survives SYNC's 16-bit screen.
paste(image, name, cx, cy, size, color, weight=None) draws it with smooth edges; weight sets the
stroke in pixels, so icons of different sizes on one screen share one line.

The climate symbols follow the ones on Ford's own climate screen (and ISO 2575), so the hand and
eye find them as before: a windscreen with rising heat, a rear window, a seat with heat, a car
with a loop for recirculation, a four-bladed fan. The fan's blades are each mirror-symmetric, so
the fan as a whole is too and cannot read as a hooked cross (tests/test_icons.py checks it).
"""
import math

from PIL import Image, ImageDraw

NAMES = ("phone", "map", "home", "media", "climate", "apps", "settings", "carplay", "video", "files",
         "restart", "voice", "seat", "defrost", "rear", "ac", "recirc", "fan", "seated", "screen_air",
         "power", "dual", "min_temp", "arrow_right", "arrow_down_right", "turn_right", "handset", "call_out",
         "call_in", "call_missed", "chevron_right", "chevron_up", "chevron_down", "info", "back", "backspace",
         "wifi0", "wifi1", "wifi2", "wifi3", "road", "person_voice")


def draw(d, name, cx, cy, size, color, width=None):
    u = size / 24.0  # one grid unit
    w = width or max(2, round(2 * u))

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

    def wave(x, y0, y1, amp=0.9, turns=1.0):  # a wavy line rising from y0 to y1
        n = 32
        line(*[(x + amp * math.sin(2 * math.pi * turns * k / n), y0 + (y1 - y0) * k / n) for k in range(n + 1)])

    def head(x, y, angle, length=3.2):  # an open arrowhead with its tip at (x, y), pointing at angle
        line(p2(x, y, length, angle + 140), (x, y), p2(x, y, length, angle - 140))

    def handset(ox, oy, k):  # a filled handset, tilted as on a phone key, centred on (ox, oy), k times full size
        c, s = math.cos(math.radians(-35)), math.sin(math.radians(-35))

        def q(x, y):
            x, y = (x - 12) * c - (y - 12) * s, (x - 12) * s + (y - 12) * c
            return (ox + x * k, oy + y * k)
        pts = [p(*q(*p2(19.5, 12, 11, a))) for a in range(122, 239, 4)]
        d.line(pts, fill=color, width=round(4.2 * u * k), joint="curve")
        for a in (122, 238):  # ear and mouth pieces, reaching in towards the face
            end, inner = q(*p2(19.5, 12, 11, a)), q(*p2(19.5, 12, 7.2, a))
            d.line([p(*end), p(*inner)], fill=color, width=round(5.2 * u * k))
            for x, y in (end, inner):
                r = 2.6 * u * k
                d.ellipse((p(x, y)[0] - r, p(x, y)[1] - r, p(x, y)[0] + r, p(x, y)[1] + r), fill=color)

    def windscreen(top, bottom, half=17):  # a windscreen seen from inside: two arcs of one circle
        centre = bottom + 22
        r0, r1 = centre - top, centre - bottom
        arc(12, centre, r0, 270 - half, 270 + half)
        arc(12, centre, r1, 270 - half, 270 + half)
        for side in (-1, 1):
            line(p2(12, centre, r1, 270 + side * half), p2(12, centre, r0, 270 + side * half))

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
    elif name == "seat":  # Ford's heated seat: the seat from the side, heat rising in front of the back
        line((20, 2.5), (17, 18), (4.5, 18), (3, 14.5))  # backrest and cushion
        line((17, 18), (18.5, 21.5))
        for x in (5.5, 9.5, 13.5):
            wave(x, 14, 3.5, 0.8)
    elif name == "defrost":  # Ford's windscreen defrost: heat rising out of the windscreen
        windscreen(3.5, 20)
        for x in (8, 12, 16):
            wave(x, 16.5, 8, 0.7)
    elif name == "rear":  # the rear window, the same heat rising out of it
        box(2.5, 4.5, 21.5, 19.5, 2.5)
        for x in (8, 12, 16):
            wave(x, 16, 8, 0.7)
    elif name == "ac":  # a snowflake
        for a in (30, 90, 150):
            line(p2(12, 12, 10, a), p2(12, 12, 10, a + 180))
        for a in range(30, 390, 60):
            tip = p2(12, 12, 6.5, a)
            line(p2(*tip, 3, a + 135), tip, p2(*tip, 3, a - 135))
    elif name == "recirc":  # Ford's recirculation: a car with the air going round inside it
        line((1.5, 17.5), (1.5, 13.5), (5, 12), (8.5, 6.5), (15.5, 6.5), (19.5, 12), (22.5, 13), (22.5, 17.5))
        arc(12, 14.5, 4, 215, 505)
        head(*p2(12, 14.5, 4, 145), 235, 2.8)
    elif name == "fan":  # four blades, each mirror-symmetric about its own axis, round a hub
        circle(12, 12, 2, True)
        for a in (0, 90, 180, 270):
            base, end, r = p2(12, 12, 3.4, a), p2(12, 12, 7.6, a), 2.6  # a point at the hub, a round end
            g = math.degrees(math.acos(r / 4.2))  # where the straight sides meet the round end
            line(base, *[p2(*end, r, a + 180 + g + k * (360 - 2 * g) / 24) for k in range(25)], base)
    elif name == "seated":  # Ford's air distribution figure: a seated driver facing the windscreen
        circle(16.5, 3.8, 2.6)
        line((15.5, 8), (13.5, 15.5), (6.5, 15.5), (4.5, 21.5))  # back, thigh, shin
        line((14.8, 10.5), (10, 12.5))  # arm
    elif name == "screen_air":  # air to the windscreen: the windscreen with air going up into it
        windscreen(2.5, 11)
        line((12, 21.5), (12, 14)); head(12, 14, -90)
    elif name == "power":
        arc(12, 13, 8, -55, 235); line((12, 3), (12, 12))
    elif name == "dual":  # two thermometers: driver and passenger each set a temperature of their own
        for x, level in ((7, 10), (17, 7)):
            box(x - 2.4, 2.5, x + 2.4, 15.5, 2.4); circle(x, 18.5, 3.2, True); line((x, 15), (x, level))
    elif name == "min_temp":
        box(6.5, 2.5, 11.5, 16, 2.5); circle(9, 18.5, 3.5, True); line((15.5, 9), (21, 9))
    elif name == "arrow_right":
        line((2.5, 12), (21, 12)); head(21, 12, 0, 5)
    elif name == "arrow_down_right":
        line((3, 5), (19, 19)); head(19, 19, 41, 5)
    elif name == "turn_right":
        line((7, 21.5), (7, 13), (8.5, 10.2), (11.5, 9), (20, 9)); head(20, 9, 0, 4.5)
    elif name == "handset":
        handset(12, 12, 1)
    elif name in ("call_out", "call_in", "call_missed"):  # the handset low left, the call's arrow up right
        handset(9, 14.5, 0.72)
        if name == "call_out":
            line((14, 10), (21, 3)); head(21, 3, -45, 4)
        elif name == "call_in":
            line((21, 3), (14, 10)); head(14, 10, 135, 4)
        else:
            line((13, 3.5), (16.8, 7.8), (21.5, 3)); head(21.5, 3, -45, 3.6)
    elif name == "chevron_right":
        line((9, 4), (16, 12), (9, 20))
    elif name in ("chevron_up", "chevron_down"):
        y0, y1 = (16, 8) if name == "chevron_up" else (8, 16)
        line((4, y0), (12, y1), (20, y0))
    elif name == "info":  # a plain i: a dot over a stem with a foot
        circle(12, 4.5, 1.6, True); line((10, 10), (12.5, 10), (12.5, 20.5)); line((10, 20.5), (15, 20.5))
    elif name == "back":  # an arrow turning back on itself
        line((19.5, 19), (19.5, 13), (17.5, 10), (14.5, 9), (4.5, 9)); head(4.5, 9, 180, 4.5)
    elif name == "backspace":  # the delete key: a tag pointing left with a cross in it
        line((8, 5), (21.5, 5), (21.5, 19), (8, 19), (2.5, 12), (8, 5))
        line((11.5, 9), (17.5, 15)); line((17.5, 9), (11.5, 15))
    elif name in ("wifi0", "wifi1", "wifi2", "wifi3"):  # a dot and up to three arcs above it
        circle(12, 19.5, 1.7, True)
        for k, r in enumerate((6, 11, 16)):
            if k < int(name[-1]):
                arc(12, 21, r, 225, 315)
    elif name == "road":  # a road running into the distance
        line((3, 21.5), (9.5, 2.5)); line((21, 21.5), (14.5, 2.5))
        for y0, y1 in ((19, 15.5), (11.5, 8.5), (5.5, 3.5)):
            line((12, y0), (12, y1))
    elif name == "person_voice":  # a head in profile speaking: sound arcs in front of the mouth
        circle(9, 8, 4.2); line((3, 21.5), (4.5, 16), (9, 14), (13.5, 16), (15, 21.5))
        arc(14, 9, 4, -45, 45); arc(14, 9, 8, -45, 45)
    else:
        raise ValueError(name)


def p2(cx, cy, r, degrees):
    """A grid point at radius r and angle degrees around (cx, cy)."""
    a = math.radians(degrees)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def paste(image, name, cx, cy, size, color, weight=None, scale=4):
    """Draw an icon onto image with smooth edges: drawn `scale` times larger, then reduced."""
    n = int(size * 1.5) + 4  # room for strokes that reach past the grid
    mask = Image.new("L", (n * scale, n * scale), 0)
    stroke = round((weight or max(2, size / 12)) * scale)
    draw(ImageDraw.Draw(mask), name, n * scale / 2, n * scale / 2, size * scale, 255, stroke)
    x0, y0 = round(cx - n / 2), round(cy - n / 2)
    image.paste(color, (x0, y0, x0 + n, y0 + n), mask.resize((n, n), Image.LANCZOS))
