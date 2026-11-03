"""The four quadrant files of the Home screen, laid out for build_home's cards (phase R7 v2).

Usage: python3 tools/build_corners.py CAR_APPS_FOLDER OUT_FOLDER   (build_home.py runs this too)

Takes **your car's own** Phone/PhoneSmartCorner.swf, Nav/NavSmartCorner.swf,
Media/MediaSmartCorner.swf and Climate/ClimateSmartCorner.swf (from the drive log, in ~/.s2am)
and writes them at the same Apps-relative paths under OUT_FOLDER. Each quadrant is a 400x240
Flash file of its own with its own class, data and buttons; Home.swf loads the four and moves
them to the places build_home.OURS gives. Everything inside them is Ford's; this tool only moves
and scales placements and resizes text fields, through FFDec's XML form (EDITS, in quadrant
pixels), so that each quadrant's content sits centred in its card below the heading and nothing
crosses a card edge. No clip is removed or renamed, no tag added: a clip that must not show (the
compass ball) is moved off-stage. Every button keeps its hit clip, its label clip and its press
and release handling (the climate and call controls are safety items), and its `DayNight` clip
Ford's placement: the theme draws each button's 1 px outline into that clip at run time
(SyncThemeButtonArt.DrawIt: a rectangle of the button's size at the clip's origin, then resized
to the button's base box), so with Ford's placement the outline lands exactly on the chip's
fill; a clip scaled to nothing came back one row higher in the car (2026-11-03).

One number pair is changed in code, in place, same length: PhoneSmartCorner.UpdateIconLayout
lays the visible status icons out left to right and then centres the row on the quadrant
(`200 - total * 0.5`); with `385 - total * 1` the row ends at the card's right margin, on the
heading line. The int and the double are found by their pattern, as build_display finds its
numbers, and read back.

Only the intended tags are taken from FFDec's output; every file is checked tag by tag against
the car's (sprites expanded; a changed placement may differ in its matrix only, a text field in
its size, bounds, alignment and colour only; the phone class in its twelve bytes only) and
every value is read back from a second swf2xml. A file that is not the one this was made for
(another placement at a depth, other numbers) is refused, and so is a result as long as the
car's file (the car checks a copy by its size alone): NavSmartCorner's street-field placement
and PhoneSmartCorner's message-field placement are therefore stored one field width wider,
same values. Needs Docker (FFDec, see
build_apps_menu). Keep OUT_FOLDER private: the results hold Ford's artwork.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import swf_bitmaps
import swf_place
import xmlswf as X

FILES = {"PhoneSmartCorner": "Phone/PhoneSmartCorner.swf", "NavSmartCorner": "Nav/NavSmartCorner.swf",
         "MediaSmartCorner": "Media/MediaSmartCorner.swf", "ClimateSmartCorner": "Climate/ClimateSmartCorner.swf"}
FLAT = (1.0, 0.0)  # a divider inside a theme button: x kept (its frame script resets it), no height

# The quadrant files' content, in quadrant pixels, laid out for cards whose body (below the
# heading line, above the bottom margin) spans y 48-184 in the phone quadrant and y 44-180 in
# the others, centred on x 200 (climate: 198). ("container", depth, "name", {x, y, scale}):
# x/y replace the translation, scale the scale; what is not named stays Ford's.
EDITS = {
    "PhoneSmartCorner": {
        "places": [
            ("main", 11, "icons", {"y": 8}),  # battery/signal on the heading line (x: the patched code)
            ("main", 39, "mcTextFieldCntrInst", {"x": 30, "y": 68}),  # "… ansluten": a 340 px centred field, its middle at x 200
            ("main", 37, "mcInactiveCallPanel", {"x": 90, "y": 118}),  # the "do not disturb" chip
            ("main", 43, "compButtonAddPhone", {"x": 90, "y": 118}),  # "connect a phone" in the same place
            (101, 1, "bgButton", {"scale": (220 / 156, 44 / 40)}),  # the chip: 220x44 instead of 208x50
            (101, 7, "txtButton", {"x": 17, "y": 9}),
            (101, 8, "LEDOne", {"x": 222, "y": 22}),
        ],
        "texts": {},
    },
    "NavSmartCorner": {
        "places": [
            ("main", 16, "mcCompass", {"x": 160, "y": -1000}),  # the compass ball: off-stage, still toggled by the code
            ("main", 15, "currentStreetTxt", {"x": 32, "y": 90}),  # no route: the street alone, centred
            ("main", 11, "activeIconInst", {"x": 166, "y": 44}),  # route: turn icon, distance, street, as one block
            ("main", 13, "milesToGoTxt", {"x": 102, "y": 114}),
            ("main", 14, "maneuverStreetTxt", {"x": 32, "y": 140}),
        ],
        "texts": {12: {"fontHeight": 600, "size": 30, "Ymax": 740}},  # the street 26 -> 30 px
    },
    "MediaSmartCorner": {
        "places": [
            (20, 1, "txtFrequency", {"x": -151.5, "y": -80}),  # station name 40 px, centred; RDS lines in the same place
            (20, 3, "txtLabel", {"x": -145.5, "y": -80}),
            (20, 2, "txtLabel2", {"x": -145.5, "y": -55}),
            (33, 5, "txtFrequencyHD", {"x": -145.5, "y": -80}),
            (33, 7, "txtHDLabel", {"x": -145.5, "y": -80}),
            (33, 6, "txtHDLabel2", {"x": -145.5, "y": -55}),
            (40, 8, "txtSatLabel", {"x": -145.5, "y": -80}),
            (40, 7, "txtSatLabel2", {"x": -145.5, "y": -55}),
            (98, 4, "mcAudioSourceIcons", {"x": -16, "y": -76}),  # USB/BT: icon, title, artist, time as one block
            (98, 3, "txtGenreLabel", {"x": -168, "y": -36}),
            (98, 2, "txtAlbumName", {"x": -168, "y": -4}),
            (98, 1, "txtTrackTimeElapsed", {"x": -48, "y": 22}),
            (101, 3, "mcAudioSourceIcons", {"x": -16, "y": -76}),
            (101, 1, "txtTrackNumber", {"x": -168, "y": -30}),
            (101, 2, "txtTrackTime", {"x": -48, "y": 20}),
            (94, 3, "mcCDSourceIcon", {"x": -16, "y": -76}),
            (94, 2, "txtTrackNumber", {"x": -168, "y": -30}),
            (94, 1, "txtTrackTime", {"x": -167, "y": 20}),
            ("main", 36, "mcIconFMSignal", {"x": 108, "y": 18.5, "scale": (0.6, 0.6)}),  # source icon after the heading
            ("main", 21, "dabIcon", {"x": 106, "y": 18, "scale": (0.5, 0.5)}),
            ("main", 49, "satIcon", {"x": 108, "y": 19, "scale": (0.6, 0.6)}),
            ("main", 136, "iconTA", {"x": 341, "y": 13}),  # traffic announcement at the heading line's right
            ("main", 51, "mcPresetPanel", {"x": 22, "y": 92}),  # six chips 112x40, 10 px apart, two rows 8 px apart
            (78, 1, "compPreset1", {"x": 0, "y": 0}),
            (78, 29, "compPreset2", {"x": 122, "y": 0}),
            (78, 45, "compPreset3", {"x": 244, "y": 0}),
            (78, 15, "compPreset4", {"x": 0, "y": 48}),
            (78, 59, "compPreset5", {"x": 122, "y": 48}),
            (78, 71, "compPreset6", {"x": 244, "y": 48}),
            *[(s, 1, "bgPanel", {"scale": (112 / 156, 1.0)}) for s in (49, 56, 63, 67, 73, 77)],
            *[(s, d, "", {"scale": FLAT}) for s, d in ((47, 9), (54, 9), (61, 9), (61, 11), (65, 9), (71, 5), (71, 7), (75, 9))],
        ],
        "texts": {},
    },
    "ClimateSmartCorner": {
        "places": [
            # The set temperatures never get text on this Mondeo (the photos show none), so the card is laid
            # out without them: the seat buttons, a quarter larger, centred in the card's body (y 44-180), at
            # quadrant x 126.5 and 267.5 (the code puts the driver's button at panel-local x 66 and the
            # passenger's at 0, each 66 px wide: centres 99 and 33 panel-local, 123.75 and 41.25 scaled)
            ("main", 11, "mcDriverPanel", {"x": 4.25, "y": 74.5, "scale": (1.25, 1.25)}),
            ("main", 48, "mcPassengerPanel", {"x": 227.75, "y": 74.5, "scale": (1.25, 1.25)}),
            # should the temperatures ever show: 20 px, quiet colour, right-aligned on the heading line,
            # driver then passenger, ending at the card's right margin (quadrant x 376)
            ("main", 79, "txtLeftTemp", {"x": 250, "y": 17}),
            ("main", 80, "txtRightTemp", {"x": 316, "y": 17}),
            # the power button (shown instead of the temperatures when the climate control is off) takes
            # the same slot: 120x36, its icon centred; the no-seat branches of the code then put its y at 74
            ("main", 3, "compPower", {"x": 256, "y": 11}),
            (10, 1, "bgButtonPower", {"scale": (120 / 156, 36 / 40)}),
            (10, 7, "iconPower", {"x": 35, "y": -6.5}),
        ],
        "texts": {67: {"fontHeight": 400, "Xmax": 1160, "Ymax": 560, "align": 1, "color": (150, 156, 168)},
                  68: {"fontHeight": 400, "Xmax": 1160, "Ymax": 560, "align": 1, "color": (150, 156, 168)}},
    },
}
# A result must not keep the car's file length (xmlswf.check_length). NavSmartCorner's and
# PhoneSmartCorner's edits leave them exactly as long as Ford's, so one placement this tool
# moves anyway (the street field, currentStreetTxt: main timeline, depth 15, character 12; the
# phone's message field, mcTextFieldCntrInst: main, depth 39, character 104) is re-encoded with
# a wider translation field: same values, a longer tag (swf_place.move with grow, frame v2's
# device; it takes a field up to 15 bits wide, which rules out placements at 16).
GROW = {"NavSmartCorner": (None, 15, 12), "PhoneSmartCorner": (None, 39, 104)}
PHONE_CLASS = "__Packages.PhoneSmartCorner"
ICON_LAYOUT = {"int": (200, 385), "double": (0.5, 1.0)}  # Ford's and ours: icons._x = INT - total * DOUBLE

# For the preview only: each quadrant in an idle state (a connected phone, FM with six presets,
# no route, two seat heaters), through the XML form: placements the code hides at run time
# dropped, one moved as the code moves it, sample texts set. The temperature fields stay empty,
# as in every photo of this car.
IDLE = {
    "PhoneSmartCorner": {
        "drop": {"main": ["mcActiveCallPanel", "phoneCallFrame", "progressIconInst", "compButtonAddPhone"],
                 87: ["iconEA", "iconE911", "iconRoaming", "iconMessage"],
                 85: ["iconBatteryLife0", "iconBatteryLife1", "iconBatteryLife2", "iconBatteryLife3", "iconBatteryLife5"],
                 86: ["iconRadioSignal0", "iconRadioSignal1", "iconRadioSignal2", "iconRadioSignal3", "iconRadioSignal5"]},
        "text": {103: "Telefon ansluten", 91: "Stör inte"},
    },
    "NavSmartCorner": {
        "drop": {"main": ["compButtonWhereAmI", "compButtonDestination", "compETA", "compButtonCancelRoute",
                          "activeIconInst", "milesToGoTxt", "maneuverStreetTxt"]},
        "text": {12: "Storgatan"},
    },
    "MediaSmartCorner": {
        "drop": {"main": ["racActivationBTIcon", "compButtonPower", "dabIcon", "mcHDRadioScreen", "mcSatRadioScreen",
                          "satIcon", "mcCDScreen", "mcDeviceMetaScreen", "mcDeviceNoMetaScreen", "iconTA"],
                 20: ["txtLabel", "txtLabel2"]},
        "text": {17: "P1", 48: "P2", 62: "P3", 66: "P4", 55: "MIX", 72: "ROCK", 76: "P3"},
    },
    "ClimateSmartCorner": {
        "drop": {"main": ["compPower", "compDriverTemp", "compPassengerTemp", "txtLeftTempCentered", "txtRightTempCentered"],
                 61: ["compCooledSeatsDriver", "compHeatedSteeringWheel"], 64: ["compCooledSeatsPassenger"],
                 30: ["bgButtonPanelSOLO", "LEDTwoHeatedSeatsDriver"], 62: ["bgButtonPanelSOLO", "LEDTwoHeatedSeatsPassenger"]},
        "move": {61: {"compHeatedSeatsDriver": (66, 0)}},
        "text": {},
    },
}
# Ford's sizer rectangles under the theme buttons (hidden at run time; the theme fills the same
# rectangle with its strip, deep (13,14,18), and draws a 1 px outline in theme colour 0x0D0E12)
SIZERS = {"PhoneSmartCorner": [5], "MediaSmartCorner": [6], "ClimateSmartCorner": [3]}
# Preview variants: the chip colour, and sample texts added to the idle state of one file
VARIANTS = {"": ((13, 14, 18), {}), "22": ((22, 24, 30), {}),
            "temps": ((13, 14, 18), {"ClimateSmartCorner": {67: "22.0°", 68: "22.0°"}})}


# What the theme draws on each button at run time, for the preview: a 1 px outline on the
# button's base box (the strip's box), corners rounded (r=3) only where the shape type rounds
# them. Boxes in quadrant px, derived from EDITS so the picture follows the table.
BASE = (156, 40)  # SyncThemeButtonArt.BASE_WIDTH/HEIGHT: every theme button's local box
TL, TM, TR, BL, BM, BR = (1, 0, 0, 0), (0, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1), (0, 0, 0, 0), (0, 0, 1, 0)  # (tl, tr, br, bl)
SOLO, RIBBON_L, RIBBON_R = (1, 1, 1, 1), (1, 0, 0, 1), (0, 1, 1, 0)


def edit(name: str, container, depth: int) -> dict:
    hits = [change for which, d, _, change in EDITS[name]["places"] if which == container and d == depth]
    if len(hits) != 1:
        raise KeyError((name, container, depth))
    return hits[0]


def chip_boxes(name: str) -> list[tuple[float, float, float, float, tuple[int, int, int, int]]]:
    """(x, y, w, h, corners) of every theme button the idle preview shows in this quadrant."""
    if name == "MediaSmartCorner":
        panel = edit(name, "main", 51)
        sx, sy = edit(name, 49, 1)["scale"]
        return [(panel["x"] + edit(name, 78, depth)["x"], panel["y"] + edit(name, 78, depth)["y"], BASE[0] * sx, BASE[1] * sy, corners)
                for depth, corners in ((1, TL), (29, TM), (45, TR), (15, BL), (59, BM), (71, BR))]
    if name == "PhoneSmartCorner":
        panel, (sx, sy) = edit(name, "main", 37), edit(name, 101, 1)["scale"]
        return [(panel["x"], panel["y"], BASE[0] * sx, BASE[1] * sy, SOLO)]
    if name == "ClimateSmartCorner":  # the heated-seat buttons: 66x60 at panel-local x 66 (driver) and 0 (passenger), by the code
        out = []
        for depth, local_x, corners in ((11, 66, RIBBON_L), (48, 0, RIBBON_R)):
            panel = edit(name, "main", depth)
            s = panel["scale"][0]
            out.append((panel["x"] + local_x * s, panel["y"], 66 * s, 60 * s, corners))
        return out
    return []


# ------------------------------------------------------------------ the code change
GET_MEMBER, MULTIPLY, SUBTRACT = 0x4E, 0x0C, 0x0B  # ActionScript 2 opcodes
METHOD = "UpdateIconLayout"


def icon_slots(body: bytes) -> tuple[tuple[int, str, object], tuple[int, str, object]]:
    """The int and the double of `icons._x = INT - total * DOUBLE` as (offset in body, kind,
    value): inside the method UpdateIconLayout, the one place that compiles to the member
    lookup of icons, then a push of "_x", the int, the register and the double, then
    Multiply, Subtract and SetMember, exactly in that order."""
    rows = X.class_pushes(body, PHONE_CLASS)
    start, end = X.method_range(rows, METHOD)
    shape = [("const", "icons"), ("op", GET_MEMBER), ("const", "_x"), ("int", None), ("reg", None), ("double", None),
             ("op", MULTIPLY), ("op", SUBTRACT), ("op", X.SET_MEMBER)]
    hits = [(rows[i + 3], rows[i + 5]) for i in range(len(rows) - len(shape) + 1)
            if start <= rows[i][0] < end
            and all(r[1] == kind and (value is None or r[2] == value) for r, (kind, value) in zip(rows[i:i + len(shape)], shape))]
    if len(hits) != 1:
        raise SystemExit(f"{METHOD}'s numbers found {len(hits)} times in {PHONE_CLASS}, not once: "
                         "not the file this tool was made for")
    return hits[0]


def patch_phone_code(body: bytes) -> bytes:
    (io, _, iv), (do, _, dv) = icon_slots(body)
    if (iv, dv) != (ICON_LAYOUT["int"][0], ICON_LAYOUT["double"][0]):
        raise SystemExit(f"UpdateIconLayout has {iv}, {dv}, not Ford's: not the file this tool was made for")
    out = bytearray(body)
    struct.pack_into("<i", out, io, ICON_LAYOUT["int"][1])
    out[do:do + 8] = X.as2_double_bytes(ICON_LAYOUT["double"][1])
    result = bytes(out)
    (_, _, iv2), (_, _, dv2) = icon_slots(result)
    if (iv2, dv2) != (ICON_LAYOUT["int"][1], ICON_LAYOUT["double"][1]):
        raise SystemExit("UpdateIconLayout's numbers did not read back as written")
    return result


def grow(name: str, body: bytes) -> bytes:
    """The body with GROW's placement re-encoded one field width wider, same translation."""
    if name not in GROW:
        return body
    sprite, depth, character = GROW[name]
    at = swf_place.read(body, sprite, depth, character)
    result = swf_place.move(body, sprite, depth, character, at, at, grow=True)
    if len(result) <= len(body) or swf_place.read(result, sprite, depth, character) != at:
        raise SystemExit(f"{name}: the widened placement did not read back as written")
    return result


# ------------------------------------------------------------------ the XML edits
def apply(root: ET.Element, spec: dict) -> None:
    for which, depth, name, change in spec["places"]:
        place = X.placement(X.container(root, which), depth=depth)
        if (place.get("name") or "") != name:
            raise SystemExit(f"the placement at depth {depth} in {which} is {place.get('name')!r}, not {name!r}: "
                             "not the file this tool was made for")
        X.set_matrix(place, change.get("x"), change.get("y"), change.get("scale"))
    for ident, change in spec["texts"].items():
        field = X.define(root, "DefineEditTextTag", ident)
        if "fontHeight" in change:
            field.set("fontHeight", str(change["fontHeight"]))
        if "Ymax" in change:
            field.find("bounds").set("Ymax", str(change["Ymax"]))
        if "Xmax" in change:
            field.find("bounds").set("Xmax", str(change["Xmax"]))
        if "align" in change:
            field.set("align", str(change["align"]))
            field.set("initialText", (field.get("initialText") or "").replace('align="center"', 'align="right"'))
        if "color" in change:
            for key, value in zip(("red", "green", "blue"), change["color"]):
                field.find("textColor").set(key, str(value))
        if "size" in change:
            field.set("initialText", re.sub(r'size="\d+"', f'size="{change["size"]}"', field.get("initialText") or ""))


def read_back(root: ET.Element, spec: dict) -> None:
    """Every value as written: translations exactly, scales to 1/65536 (16.16 fixed point)."""
    for which, depth, name, change in spec["places"]:
        m = X.placement(X.container(root, which), depth=depth).find("matrix")
        for key, value in (("translateX", change.get("x")), ("translateY", change.get("y"))):
            if value is not None and int(m.get(key)) != int(round(value * X.TWIP)):
                raise SystemExit(f"{name} ({which}, depth {depth}) {key} did not read back as written")
        if "scale" in change:
            got = (float(m.get("scaleX")), float(m.get("scaleY")))
            if m.get("hasScale") != "true" or any(abs(g - w) > 1 / 65536 for g, w in zip(got, change["scale"])):
                raise SystemExit(f"{name} ({which}, depth {depth}) scale did not read back as written: {got}")
    for ident, change in spec["texts"].items():
        field = X.define(root, "DefineEditTextTag", ident)
        bounds = field.find("bounds")
        if "fontHeight" in change and field.get("fontHeight") != str(change["fontHeight"]):
            raise SystemExit(f"text {ident} fontHeight did not read back")
        if any(k in change and bounds.get(k) != str(change[k]) for k in ("Xmax", "Ymax")):
            raise SystemExit(f"text {ident} bounds did not read back")
        if "align" in change and field.get("align") != str(change["align"]):
            raise SystemExit(f"text {ident} align did not read back")
        if "color" in change and tuple(int(field.find("textColor").get(k)) for k in ("red", "green", "blue")) != tuple(change["color"]):
            raise SystemExit(f"text {ident} colour did not read back")
        if "size" in change and f'size="{change["size"]}"' not in (field.get("initialText") or ""):
            raise SystemExit(f"text {ident} size did not read back")


def wanted(spec: dict) -> tuple[set, set, dict]:
    """What to take from FFDec's output: text fields, main placements, placements per sprite."""
    defines = {(X.EDIT_TEXT, i) for i in spec["texts"]}
    main_places, sprite_places = set(), {}
    for which, depth, name, _ in spec["places"]:
        if which == "main":
            main_places.add((depth, name))
        else:
            sprite_places.setdefault(which, set()).add((depth, name))
    return defines, main_places, sprite_places


TEXT_FIELDS = {"fontHeight": {"fontHeight"}, "Xmax": {"bounds"}, "Ymax": {"bounds"}, "align": {"layout", "initialText"},
               "color": {"textColor"}, "size": {"initialText"}}  # which binary fields each table entry may change


def text_allowed(spec: dict) -> dict[int, set[str]]:
    return {ident: set().union(*(TEXT_FIELDS[k] for k in change)) for ident, change in spec["texts"].items()}


def allowed_keys(spec: dict) -> set[tuple]:
    keys = {("DefineEditText", i) for i in spec["texts"]}
    for which, depth, name, _ in spec["places"]:
        prefix = "main" if which == "main" else f"sprite{which}"
        keys |= {(prefix, "PlaceObject2", depth, name), (prefix, "PlaceObject3", depth, name)}
    return keys


def build(name: str, original: bytes, work: Path) -> bytes:
    """One quadrant file, edited, spliced, patched (the phone), read back and checked."""
    if original[:3] != b"FWS" or struct.unpack_from("<I", original, 4)[0] != len(original):
        raise SystemExit(f"{name}: not an uncompressed Flash file of the length its header says")
    spec = EDITS[name]
    tree = X.swf2xml(work, original)
    apply(tree.getroot(), spec)
    rebuilt = X.xml2swf(work, tree)
    head, body = swf_bitmaps.unpack(original)
    defines, main_places, sprite_places = wanted(spec)
    body = grow(name, X.splice(body, swf_bitmaps.unpack(rebuilt)[1], defines, main_places, sprite_places))
    allowed = allowed_keys(spec)
    if name == "PhoneSmartCorner":
        body = patch_phone_code(body)
        slots = [(off, kind) for off, kind, _ in icon_slots(body)]
        allowed.add(("DoInitAction", X.check_class(swf_bitmaps.unpack(original)[1], body, PHONE_CLASS, slots)))
    result = swf_bitmaps.pack(head, body)
    X.check_length(original, result, name)
    read_back(X.swf2xml(work, result, "check").getroot(), spec)
    changed = X.check(original, result, allowed, text_allowed=text_allowed(spec))
    expected = len(spec["places"]) + len(spec["texts"]) + (name == "PhoneSmartCorner")  # an edit equal to Ford's changes nothing
    if len([k for k in changed if k[0] != "DefineSprite"]) > expected:
        raise SystemExit(f"{name}: more tags changed than intended: {changed}")
    return result


# ------------------------------------------------------------------ the preview's idle state
def idle(root: ET.Element, spec: dict, background: tuple[int, int, int]) -> None:
    for which, names in spec.get("drop", {}).items():
        box = X.container(root, which)
        for item in list(box):
            if item.get("type") in ("PlaceObject2Tag", "PlaceObject3Tag") and item.get("name") in names:
                box.remove(item)
    for which, moves in spec.get("move", {}).items():
        for item in X.container(root, which):
            if item.get("name") in moves:
                X.set_matrix(item, *moves[item.get("name")])
    for ident, text in spec.get("text", {}).items():
        field = X.define(root, "DefineEditTextTag", ident)
        html = field.get("initialText") or '<p align="center"></p>'
        if "<font" in html:  # the first font run gets the text; one paragraph only
            html = re.sub(r"(<font[^>]*>).*?(</font>)", lambda m: m.group(1) + text + m.group(2), html, count=1, flags=re.S)
            html = re.sub(r"</p><p.*$", "</p>", html, flags=re.S)
        else:
            html = re.sub(r"(<p[^>]*>).*?(</p>)", lambda m: m.group(1) + text + m.group(2), html, count=1, flags=re.S)
        field.set("initialText", html)
    for tag in root.find("tags"):
        if tag.get("type") == "SetBackgroundColorTag":
            for key, value in zip(("red", "green", "blue"), background):
                tag.find("backgroundColor").set(key, str(value))


def sprite_width(root: ET.Element, sprite: int) -> float:
    """A sprite's width in px from its placed shapes (one level of sprites in between), as the
    player's _width reports it: every child counts, visible or not."""
    xs = []
    shapes = {t.get("shapeId"): t for t in root.find("tags") if t.get("type", "").startswith("DefineShape")}
    sprites = {t.get("spriteId"): t for t in root.find("tags") if t.get("type") == "DefineSpriteTag"}

    def extent(tag: ET.Element, tx: float, sx: float) -> None:
        b = tag.find("shapeBounds")
        xs.extend((tx + sx * int(b.get("Xmin")) / X.TWIP, tx + sx * int(b.get("Xmax")) / X.TWIP))

    for place in X.container(root, sprite):
        if place.get("type") not in ("PlaceObject2Tag", "PlaceObject3Tag"):
            continue
        m = place.find("matrix")
        tx = int(m.get("translateX", "0")) / X.TWIP if m is not None else 0
        sx = float(m.get("scaleX")) if m is not None and m.get("hasScale") == "true" else 1.0
        char = place.get("characterId")
        if char in shapes:
            extent(shapes[char], tx, sx)
        elif char in sprites:
            for inner in sprites[char].find("subTags"):
                if inner.get("type") in ("PlaceObject2Tag", "PlaceObject3Tag") and inner.get("characterId") in shapes:
                    extent(shapes[inner.get("characterId")], tx, sx)
    return max(xs) - min(xs)


def runtime_look(root: ET.Element, name: str, chip: tuple[int, int, int]) -> None:
    """What the code does at run time, for the picture: the sizer rectangles take the theme's
    chip colour; the phone's visible icons are laid out as the patched UpdateIconLayout lays
    them (battery at 0, signal at battery width + 7, icons._x = 385 - total)."""
    for ident in SIZERS.get(name, []):
        colour = X.define(root, "DefineShapeTag", ident).find("shapes").find("fillStyles").find("fillStyles")[0].find("color")
        for key, value in zip(("red", "green", "blue"), chip):
            colour.set(key, str(value))
    if name == "PhoneSmartCorner":
        battery, signal = sprite_width(root, 85), sprite_width(root, 86)
        icons = X.container(root, 87)
        X.set_matrix(X.placement(icons, name="battery"), 0, None)
        X.set_matrix(X.placement(icons, name="radiosignals"), battery + 7, None)
        total = battery + 7 + signal + 7
        X.set_matrix(X.placement(X.container(root, "main"), name="icons"), ICON_LAYOUT["int"][1] - total * ICON_LAYOUT["double"][1], None)


def idle_variants(name: str, data: bytes, work: Path) -> dict[str, bytes]:
    """`<variant>-black` / `<variant>-white` idle builds of one quadrant for the preview; a
    variant with sample texts only for the file that has them."""
    out = {}
    for variant, (chip, extra) in VARIANTS.items():
        if variant not in ("", "22") and name not in extra:
            continue
        for suffix, background in (("black", (0, 0, 0)), ("white", (255, 255, 255))):
            tree = X.swf2xml(work, data, f"{name}-src")
            spec = dict(IDLE[name])
            spec["text"] = {**IDLE[name].get("text", {}), **extra.get(name, {})}
            idle(tree.getroot(), spec, background)
            runtime_look(tree.getroot(), name, chip)
            out[f"{variant}-{suffix}"] = X.xml2swf(work, tree, f"{name}-{variant}{suffix}")
    return out


# ------------------------------------------------------------------ the command line
def build_all(source: Path, target: Path, work: Path) -> dict[str, bytes]:
    results = {}
    for name, rel in FILES.items():
        original = (source / rel).read_bytes()
        result = build(name, original, work / name)
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / rel).write_bytes(result)
        results[name] = result
        print(f"{target / rel}: {len(EDITS[name]['places'])} placements, {len(EDITS[name]['texts'])} text fields"
              + (", two numbers in UpdateIconLayout" if name == "PhoneSmartCorner" else "")
              + f"; everything else byte for byte; sha256 {hashlib.sha256(result).hexdigest()}, {len(result)} bytes")
    return results


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit(__doc__)
    with tempfile.TemporaryDirectory() as temp:
        build_all(Path(argv[0]), Path(argv[1]), Path(temp))


if __name__ == "__main__":
    main(sys.argv[1:])
