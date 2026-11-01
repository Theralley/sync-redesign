"""Let Settings, Display dim the screen further at night than Ford allows.

Usage: python3 tools/build_display.py CAR_DISPLAY_SWF OUT_SWF [--floor N]

Takes **your car's own** Menu\\Display\\Display.swf (from the drive log, in ~/.s2am). With the
display in Auto and Auto dim on, the screen's brightness at night follows SYNC's light sensor
plus an offset, "Anpassa utom. dimning", which Ford lets the owner set from -5 to +5. Its floor is
one number in the screen's own code (Display.MIN_LEVEL), changed here in place, as R3b changed
the call list's numbers; nothing else changes. Default floor: -10.

What the backlight really does below -5 is decided by SYNC's native display plugin
(DisplayPlugin.SetAutoDimOffset), not by Flash: it may follow, stop at -5, or refuse, and the
screen shows what it kept when Settings, Display opens again. The way back is Ford's own: the
offset's reset button (one tap to 0) and +, which work from any value. Brightness itself (0 to
14) is left alone: its control turns a negative floor into a positive one.

The result is checked tag by tag against the car's file (only the class Display differs) and
the number must read back as written. A file that is not the screen this was made for is refused.
Display.swf loads when Settings, Display opens, not at start-up. Ford's screens are stored
uncompressed, so the result is exactly as long as the car's file: the car cannot tell a failed
copy by its length, and the import's byte-for-byte check is what proves it went on.
"""
import hashlib
import struct
import sys
from pathlib import Path

import swf_bitmaps
from build_phone_history import class_actions, numbers

CLASS = "__Packages.Display"
FORD = {"MIN_LEVEL": -5, "MAX_LEVEL": 5, "max": 14}  # the offset's range, and brightness's top


def change(data: bytes, floor: int) -> bytes:
    head, body = swf_bitmaps.unpack(data)
    found = swf_bitmaps.tags(body)
    index = class_actions(body, CLASS)
    code, header, contents = found[index]
    actions = bytearray(contents[2:])
    have = {}
    for name, value, offset in numbers(bytes(actions)):
        if name in FORD:
            have.setdefault(name, []).append((value, offset))
    if any(have.get(name) != [(value, have[name][0][1])] for name, value in FORD.items() if name in have) \
            or set(have) != set(FORD):
        raise SystemExit(f"{CLASS} does not hold {FORD} once each: not the screen this was made for")
    struct.pack_into("<i", actions, have["MIN_LEVEL"][0][1], floor)
    after = {n: v for n, v, _ in numbers(bytes(actions)) if n in FORD}
    if after != {**FORD, "MIN_LEVEL": floor}:
        raise SystemExit("the numbers did not read back as written")
    found[index] = (code, header, contents[:2] + bytes(actions))
    result = swf_bitmaps.pack(head, b"".join(h + c for _, h, c in found))
    before, now = swf_bitmaps.tags(body), swf_bitmaps.tags(swf_bitmaps.unpack(result)[1])
    if [t[0] for t in before] != [t[0] for t in now] or \
            [i for i, (x, y) in enumerate(zip(before, now)) if x[1:] != y[1:]] != [index]:
        raise SystemExit("more than the class Display changed")
    return result


def main(argv: list[str]) -> None:
    floor = int(argv[argv.index("--floor") + 1]) if "--floor" in argv else -10
    args = [a for i, a in enumerate(argv) if a != "--floor" and (i == 0 or argv[i - 1] != "--floor")]
    if len(args) != 2 or not -20 <= floor <= -6:
        raise SystemExit(__doc__)
    result = change(Path(args[0]).read_bytes(), floor)
    Path(args[1]).write_bytes(result)
    print(f"{args[1]}: Auto dim offset from {floor} to +5 (Ford: -5); everything else byte for byte; "
          f"sha256 {hashlib.sha256(result).hexdigest()[:16]}, {len(result)} bytes")


if __name__ == "__main__":
    main(sys.argv[1:])
