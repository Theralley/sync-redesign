"""Replace pictures inside a Flash file with our own, and prove that nothing else changed.

Usage: python3 tools/swf_bitmaps.py IN.swf --list
       python3 tools/swf_bitmaps.py IN.swf OUT.swf ID=picture.png [ID=picture.png ...]

Each ID is a DefineBitsLossless or DefineBitsLossless2 picture in IN.swf (--list shows them);
the new picture must have exactly its width and height, so nothing on the screen moves. Every
other tag is kept byte for byte, as are the version and the compression; after writing, the
file is read back and compared tag by tag. No Java and no Ford code needed: the screen's
ActionScript is not touched.
"""
import struct
import sys
import zlib
from pathlib import Path

from PIL import Image

LOSSLESS, LOSSLESS2 = 20, 36  # DefineBitsLossless (no alpha), DefineBitsLossless2 (alpha)


class SwfError(ValueError):
    pass


def unpack(data: bytes) -> tuple[bytes, bytes]:
    """(signature and version, the uncompressed body after the 8-byte header)."""
    if data[:3] == b"CWS":
        return data[:4], zlib.decompress(data[8:])
    if data[:3] == b"FWS":
        return data[:4], data[8:]
    raise SwfError("not an uncompressed or zlib-compressed Flash file")


def pack(head: bytes, body: bytes) -> bytes:
    length = struct.pack("<I", 8 + len(body))
    return head + length + (zlib.compress(body, 9) if head[:3] == b"CWS" else body)


def tags(body: bytes) -> list[tuple[int, bytes, bytes]]:
    """The top-level tags as (code, header bytes, contents), after the frame header."""
    nbits = body[0] >> 3
    p = (5 + 4 * nbits + 7) // 8 + 4  # the stage rectangle, frame rate and frame count
    out = [(-1, body[:p], b"")]
    while p < len(body):
        start = p
        code, length = struct.unpack_from("<H", body, p)[0] >> 6, struct.unpack_from("<H", body, p)[0] & 0x3F
        p += 2
        if length == 0x3F:
            length = struct.unpack_from("<I", body, p)[0]
            p += 4
        out.append((code, body[start:p], body[p:p + length]))
        p += length
        if code == 0:
            break
    if p != len(body):
        raise SwfError("trailing bytes after the End tag")
    return out


def picture_info(code: int, contents: bytes) -> tuple[int, int, int, int]:
    """(character id, format, width, height) of a lossless picture."""
    ident, fmt, width, height = struct.unpack_from("<HBHH", contents)
    return ident, fmt, width, height


def pictures(body: bytes) -> dict[int, tuple[int, int, int, int]]:
    """character id -> (tag code, format, width, height) for every lossless picture."""
    found = {}
    for code, _, contents in tags(body):
        if code in (LOSSLESS, LOSSLESS2):
            ident, fmt, width, height = picture_info(code, contents)
            found[ident] = (code, fmt, width, height)
    return found


def encode(code: int, ident: int, image: Image.Image) -> bytes:
    """A format-5 (32-bit) lossless picture: premultiplied ARGB, or 0RGB without alpha."""
    pixels = bytearray()
    for r, g, b, a in image.convert("RGBA").getdata():
        if code == LOSSLESS2:
            pixels += bytes((a, r * a // 255, g * a // 255, b * a // 255))
        else:
            pixels += bytes((0, r, g, b))
    return struct.pack("<HBHH", ident, 5, image.width, image.height) + zlib.compress(bytes(pixels), 9)


def decode(code: int, contents: bytes) -> Image.Image:
    """A format-5 picture back to RGBA (for the check after writing)."""
    ident, fmt, width, height = picture_info(code, contents)
    if fmt != 5:
        raise SwfError(f"picture {ident} is format {fmt}, not 5")
    raw = zlib.decompress(contents[7:])
    image = Image.new("RGBA", (width, height))
    data = []
    for i in range(0, len(raw), 4):
        a, r, g, b = raw[i:i + 4]
        if code == LOSSLESS2:
            data.append((r * 255 // a, g * 255 // a, b * 255 // a, a) if a else (0, 0, 0, 0))
        else:
            data.append((r, g, b, 255))
    image.putdata(data)
    return image


def replace(data: bytes, new: dict[int, Image.Image]) -> bytes:
    head, body = unpack(data)
    known = pictures(body)
    for ident, image in new.items():
        if ident not in known:
            raise SwfError(f"no lossless picture {ident} in this file")
        _, _, width, height = known[ident]
        if image.size != (width, height):
            raise SwfError(f"picture {ident} is {width}x{height}; the new one is {image.width}x{image.height}")
    parts = []
    for code, header, contents in tags(body):
        if code in (LOSSLESS, LOSSLESS2) and picture_info(code, contents)[0] in new:
            contents = encode(code, picture_info(code, contents)[0], new[picture_info(code, contents)[0]])
            header = struct.pack("<HI", (code << 6) | 0x3F, len(contents))  # the long form, as Flash wants
        parts.append(header + contents)
    result = pack(head, b"".join(parts))
    check(data, result, new)
    return result


def check(old: bytes, result: bytes, new: dict[int, Image.Image]) -> None:
    """Read the result back: same header, same tags in the same order, only the named
    pictures differ, each with its id, size and the exact new pixels (up to premultiplying)."""
    (old_head, old_body), (head, body) = unpack(old), unpack(result)
    before, after = tags(old_body), tags(body)
    if head != old_head or len(before) != len(after):
        raise SwfError("the header or the number of tags changed")
    for (code, header, contents), (code2, header2, contents2) in zip(before, after):
        if code != code2:
            raise SwfError("the order of the tags changed")
        named = code in (LOSSLESS, LOSSLESS2) and picture_info(code, contents)[0] in new
        if not named and (header, contents) != (header2, contents2):
            raise SwfError(f"tag {code} changed although it was not named")
        if named:
            ident, _, width, height = picture_info(code, contents)
            if picture_info(code2, contents2)[0::2] != (ident, width) or picture_info(code2, contents2)[3] != height:
                raise SwfError(f"picture {ident} changed its id or size")
            back, want = decode(code2, contents2), new[ident].convert("RGBA")
            for (r, g, b, a), (r2, g2, b2, a2) in zip(back.getdata(), want.getdata()):
                if a != a2 or (a and max(abs(r - r2), abs(g - g2), abs(b - b2)) > 255 // a + 1):
                    raise SwfError(f"picture {ident} did not read back as written")


def main(argv: list[str]) -> None:
    if len(argv) == 2 and argv[1] == "--list":
        for ident, (code, fmt, width, height) in sorted(pictures(unpack(Path(argv[0]).read_bytes())[1]).items()):
            print(f"{ident}: {'DefineBitsLossless2' if code == LOSSLESS2 else 'DefineBitsLossless'} "
                  f"format {fmt}, {width}x{height}")
        return
    if len(argv) < 3 or any("=" not in a for a in argv[2:]):
        raise SystemExit(__doc__)
    new = {int(a.split("=", 1)[0]): Image.open(a.split("=", 1)[1]) for a in argv[2:]}
    result = replace(Path(argv[0]).read_bytes(), new)
    Path(argv[1]).write_bytes(result)
    print(f"{argv[1]}: {len(new)} pictures replaced; every other tag byte for byte the same ({len(result)} bytes)")


if __name__ == "__main__":
    main(sys.argv[1:])
