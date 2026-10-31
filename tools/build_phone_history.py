"""Build the call history screen in the new design (plan phase R3).

Usage: python3 tools/build_phone_history.py CAR_PHONEHISTORY_SWF OUT_SWF [--rows] [--preview FOLDER]

Takes **your car's own** Phone\\PhoneHistory\\PhoneHistory.swf (from the drive log, in ~/.s2am).

R3a, always: eight of its pictures are replaced with icons from icons.py, at exactly their
sizes: the outgoing, incoming and missed call marks, the green dial handset, the scroll arrows
and the two small arrows.

R3b, with --rows: bigger rows, as in the sketch: 76 px instead of 50 and three to a page
instead of five, the name at 26 px instead of 20, the icons and arrows centred in the row.
Two numbers in the screen's own code (rowHeight, visibleRowCount) are changed in place, and the
row's layout (where its background, icons, name and arrows sit) through FFDec's XML form of the
file (the pinned copy, in Docker, no network). Nothing is recompiled.

The result is checked tag by tag against the car's file: only the named pictures, and with
--rows the row (sprite 62), its name field (53) and the class PhoneHistory, may differ, and the
two numbers and every row value must read back as written. A file that is not the screen this
was made for (other pictures, other values) is refused. --preview FOLDER gets the new pictures,
enlarged, and with --rows Ford's rows and ours side by side (Ford's artwork: keep it private).
"""
import hashlib
import shutil
import struct
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from PIL import Image, ImageDraw

import icons
import swf_bitmaps
from build_apps_menu import run_ffdec

WHITE, GREEN = (245, 246, 248), (72, 190, 110)
# Ford's picture id -> (its width, height), our icon, the icon's size and line in pixels, colour
PICTURES = {
    30: ((30, 25), "chevron_up", 22, 2.5, WHITE),
    37: ((30, 25), "chevron_down", 22, 2.5, WHITE),
    44: ((30, 30), "call_out", 28, 2.5, WHITE),
    47: ((30, 30), "call_missed", 28, 2.5, WHITE),
    50: ((30, 30), "call_in", 28, 2.5, WHITE),
    56: ((6, 12), "chevron_right", 12, 1.6, WHITE),
    73: ((21, 28), "handset", 26, 2.5, GREEN),
    78: ((12, 18), "chevron_right", 18, 2.2, WHITE),
}
SCALE = 8  # drawn this much larger, then reduced, for smooth edges

ROW_SPRITE, NAME_FIELD, CLASS = "62", "53", "__Packages.PhoneHistory"
ROW_HEIGHT = (50, 76)  # px, Ford's and ours
# the row's parts (placements in sprite 62) -> matrix value: (Ford's, ours), in FFDec's XML units
ROW = {
    "invButtonBG": {"scaleY": ("1.7241211", "2.6206641")},  # the touch area, 50 -> 76 px high
    "bgItem": {"scaleY": ("1.25", "1.9")},  # the row's background, 50 -> 76 px
    "iconCallOutgoing": {"translateY": ("140", "460")},  # twips: our three marks alike, centred
    "iconCallMissed": {"translateY": ("220", "460")},
    "iconCallIncoming": {"translateY": ("220", "460")},
    "txtItem": {"translateY": ("240", "380")},
    "compArrowLeft": {"translateY": ("0", "380")},  # Ford's sat 6 px above the middle; ours centred
    "compArrowRight": {"translateY": ("0", "380")},
}
NAME = {"fontHeight": ("400", "520")}  # twips: 20 -> 26 px
NAME_BOUNDS = {"Ymax": ("655", "775")}  # the field grows with its text
CODE = {"rowHeight": ROW_HEIGHT, "visibleRowCount": (5, 3)}  # in the class PhoneHistory


def picture(name: str, size: tuple[int, int], icon: int, weight: float, colour) -> Image.Image:
    """The icon, centred in a transparent picture of exactly `size`."""
    side = max(size) * SCALE
    mask = Image.new("L", (side, side), 0)
    icons.draw(ImageDraw.Draw(mask), name, side / 2, side / 2, icon * SCALE, 255, round(weight * SCALE))
    mask = mask.resize((max(size), max(size)), Image.LANCZOS)
    left, top = (max(size) - size[0]) // 2, (max(size) - size[1]) // 2
    mask = mask.crop((left, top, left + size[0], top + size[1]))
    return Image.merge("RGBA", (*(Image.new("L", size, c) for c in colour), mask))


def class_actions(body: bytes, name: str) -> int:
    """The index of the DoInitAction tag that holds an exported class."""
    found = swf_bitmaps.tags(body)
    exports = {}
    for code, _, contents in found:
        if code == 56:  # ExportAssets
            q = 2
            for _ in range(struct.unpack_from("<H", contents)[0]):
                ident, end = struct.unpack_from("<H", contents, q)[0], contents.index(b"\0", q + 2)
                exports[contents[q + 2:end].decode("latin1")] = ident
                q = end + 1
    for i, (code, _, contents) in enumerate(found):
        if code == 59 and struct.unpack_from("<H", contents)[0] == exports.get(name):
            return i
    raise SystemExit(f"no class {name} in this file")


def numbers(actions: bytes) -> list[tuple[str, int, int]]:
    """(name, value, offset) for every integer pushed right after a name from the constant pool,
    as an object literal like {rowHeight: 50} compiles."""
    pool, out, p = [], [], 0
    while p < len(actions) and actions[p]:
        op = actions[p]
        p += 1
        if op < 0x80:
            continue
        length = struct.unpack_from("<H", actions, p)[0]
        start, p = p + 2, p + 2 + length
        data = actions[start:p]
        if op == 0x88:  # ConstantPool
            pool, q = [], 2
            for _ in range(struct.unpack_from("<H", data)[0]):
                end = data.index(b"\0", q)
                pool.append(data[q:end].decode("latin1"))
                q = end + 1
        elif op == 0x96:  # Push
            q, last = 0, None
            while q < len(data):
                kind, q = data[q], q + 1
                size = {0: None, 1: 4, 2: 0, 3: 0, 4: 1, 5: 1, 6: 8, 7: 4, 8: 1, 9: 2}[kind]
                if kind == 0:
                    size = data.index(b"\0", q) - q + 1
                if kind == 7 and last is not None:
                    out.append((last, struct.unpack_from("<i", data, q)[0], start + q))
                last = (pool[data[q]] if kind == 8 else pool[struct.unpack_from("<H", data, q)[0]]) \
                    if kind in (8, 9) else None
                q += size
    return out


def change_code(body: bytes) -> bytes:
    """rowHeight and visibleRowCount in PhoneHistory, changed in place (same length)."""
    found = swf_bitmaps.tags(body)
    index = class_actions(body, CLASS)
    code, header, contents = found[index]
    actions = bytearray(contents[2:])
    for name, (ford, ours) in CODE.items():
        hits = [(value, offset) for n, value, offset in numbers(bytes(actions)) if n == name]
        if len(hits) != 1 or hits[0][0] != ford:
            raise SystemExit(f"{name} is not {ford} once in {CLASS}: not the screen this was made for")
        struct.pack_into("<i", actions, hits[0][1], ours)
    found[index] = (code, header, contents[:2] + bytes(actions))
    if {n: v for n, v, _ in numbers(bytes(actions)) if n in CODE} != {n: v[1] for n, v in CODE.items()}:
        raise SystemExit("the numbers did not read back as written")
    return b"".join(h + c for _, h, c in found)


def row_elements(tree: ElementTree.ElementTree) -> tuple[dict, ElementTree.Element]:
    """The row's matrices by placement name, and its name field, from FFDec's XML."""
    tags = tree.getroot().find("tags")
    sprite = next(t for t in tags if t.get("type") == "DefineSpriteTag" and t.get("spriteId") == ROW_SPRITE)
    places = {p.get("name"): p.find("matrix") for p in sprite.find("subTags")
              if p.get("type") == "PlaceObject2Tag" and p.get("name") in ROW}
    field = next(t for t in tags if t.get("type") == "DefineEditTextTag" and t.get("characterID") == NAME_FIELD)
    return places, field


def check_row(tree: ElementTree.ElementTree, which: int) -> None:
    """Every row value is Ford's (which=0) or ours (which=1)."""
    places, field = row_elements(tree)
    wanted = [(places.get(n), k, v) for n, values in ROW.items() for k, v in values.items()]
    wanted += [(field, k, v) for k, v in NAME.items()] + [(field.find("bounds"), k, v) for k, v in NAME_BOUNDS.items()]
    def same(got, want):  # scales are stored as 16.16 fixed point, so to 1/65536
        return got is not None and abs(float(got) - float(want)) <= 1 / 65536
    wrong = [k for element, k, v in wanted if element is None or not same(element.get(k), v[which])]
    if wrong:
        raise SystemExit(f"row values {wrong} are not {'Ford' if which == 0 else 'ours'}: "
                         + ("not the screen this was made for" if which == 0 else "they did not read back"))


def change_row(data: bytes) -> bytes:
    """The row's layout through FFDec's XML form (round trip byte for byte, checked)."""
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        (work / "in.swf").write_bytes(data)
        run_ffdec(work, "-swf2xml", "/work/in.swf", "/work/in.xml")
        tree = ElementTree.parse(work / "in.xml")
        check_row(tree, 0)
        places, field = row_elements(tree)
        for name, values in ROW.items():
            for key, (_, ours) in values.items():
                places[name].set(key, ours)
        for key, (_, ours) in NAME.items():
            field.set(key, ours)
        for key, (_, ours) in NAME_BOUNDS.items():
            field.find("bounds").set(key, ours)
        tree.write(work / "out.xml", encoding="utf-8", xml_declaration=True)
        run_ffdec(work, "-xml2swf", "/work/out.xml", "/work/out.swf")
        run_ffdec(work, "-swf2xml", "/work/out.swf", "/work/back.xml")
        check_row(ElementTree.parse(work / "back.xml"), 1)
        return (work / "out.swf").read_bytes()


def check(old: bytes, new: bytes, rows: bool) -> None:
    """Tag by tag: only what was meant to change did."""
    (head, before), (head2, after) = swf_bitmaps.unpack(old), swf_bitmaps.unpack(new)
    a, b = swf_bitmaps.tags(before), swf_bitmaps.tags(after)
    if head != head2 or [t[0] for t in a] != [t[0] for t in b]:
        raise SystemExit("the header or the list of tags changed")
    allowed = {i for i, (code, _, c) in enumerate(a)
               if code in (20, 36) and swf_bitmaps.picture_info(code, c)[0] in PICTURES}
    if rows:
        allowed.add(class_actions(before, CLASS))
        allowed |= {i for i, (code, _, c) in enumerate(a) if code in (39, 37)
                    and str(struct.unpack_from("<H", c)[0]) in (ROW_SPRITE, NAME_FIELD)}
    changed = {i for i, (x, y) in enumerate(zip(a, b)) if x[1:] != y[1:]}
    if changed - allowed:
        raise SystemExit(f"tags changed that should not have: {sorted(changed - allowed)}")


def preview_rows(ford: bytes, ours: bytes, folder: Path) -> None:
    """Three rows of Ford's and three of ours, with a sample name, side by side."""
    shots = []
    for data, height in ((ford, ROW_HEIGHT[0]), (ours, ROW_HEIGHT[1])):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            (work / "in.swf").write_bytes(data)
            run_ffdec(work, "-swf2xml", "/work/in.swf", "/work/in.xml")
            tree = ElementTree.parse(work / "in.xml")
            places, field = row_elements(tree)
            field.set("initialText", "Anna Andersson")
            sprite = next(t for t in tree.getroot().find("tags") if t.get("spriteId") == ROW_SPRITE).find("subTags")
            for item in list(sprite):  # show one call mark, as at run time
                if item.get("name") in ("iconCallMissed", "iconCallIncoming"):
                    sprite.remove(item)
            tree.write(work / "p.xml", encoding="utf-8", xml_declaration=True)
            run_ffdec(work, "-xml2swf", "/work/p.xml", "/work/p.swf")
            run_ffdec(work, "-selectid", ROW_SPRITE, "-export", "sprite", "/work/shot", "/work/p.swf")
            png = sorted((work / "shot").rglob("*.png"))[0]
            row = Image.open(png).convert("RGB")
            column = Image.new("RGB", (row.width, height * 3), (0, 0, 0))
            for k in range(3):
                column.paste(row.crop((0, 0, row.width, min(row.height, height))), (0, k * height))
            shots.append(column)
    sheet = Image.new("RGB", (shots[0].width + shots[1].width + 20, max(s.height for s in shots)), (255, 255, 255))
    sheet.paste(shots[0], (0, 0))
    sheet.paste(shots[1], (shots[0].width + 20, 0))
    sheet.save(folder / "rows-ford-vs-ours.png")


def main(argv: list[str]) -> None:
    rows = "--rows" in argv
    preview = Path(argv[argv.index("--preview") + 1]) if "--preview" in argv else None
    args = [a for i, a in enumerate(argv) if a != "--rows" and a != "--preview"
            and (i == 0 or argv[i - 1] != "--preview")]
    if len(args) != 2:
        raise SystemExit(__doc__)
    source, target = args
    data = Path(source).read_bytes()
    found = swf_bitmaps.pictures(swf_bitmaps.unpack(data)[1])
    for ident, (size, *_) in PICTURES.items():
        if ident not in found or found[ident][2:] != size:
            raise SystemExit(f"picture {ident} is not the {size[0]}x{size[1]} picture expected: "
                             "this is not the call history screen this tool was made for")
    result = data
    if rows:
        result = change_row(result)
        head, body = swf_bitmaps.unpack(result)
        result = swf_bitmaps.pack(head, change_code(body))
    new = {ident: picture(name, size, icon, weight, colour)
           for ident, (size, name, icon, weight, colour) in PICTURES.items()}
    result = swf_bitmaps.replace(result, new)
    check(data, result, rows)
    Path(target).write_bytes(result)
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        for ident, image in new.items():
            backed = Image.new("RGBA", image.size, (30, 33, 40, 255))
            backed.alpha_composite(image)
            backed.resize((image.width * 6, image.height * 6), Image.NEAREST).save(preview / f"{ident}.png")
        if rows:
            preview_rows(data, result, preview)
    print(f"{target}: {len(new)} pictures replaced" + (", rows 76 px, three to a page" if rows else "")
          + f"; everything else byte for byte; sha256 {hashlib.sha256(result).hexdigest()[:16]}, {len(result)} bytes")


if __name__ == "__main__":
    main(sys.argv[1:])
