"""Move a placed object inside a Flash file without recompiling anything.

Usage: python3 tools/swf_place.py IN.swf [SPRITE|main] DEPTH CHARACTER   (prints the translation)

A PlaceObject2 tag carries a MATRIX whose translation (in twips, 1/20 px) is a pair of signed
numbers of a stated bit width. This rewrites those two numbers in place, with the same bit
width, so the tag, the sprite and the file keep their exact lengths. When a value needs more
bits than the stated width, the matrix alone is re-encoded with a wider translation field (its
scale and rotation bits copied as they are) and the tag's and the sprite's length fields follow;
nothing else in the tag moves. A placement whose current values are not the ones expected is
refused. After writing, the matrix is parsed again and must read back as written. Every other
tag in the file is left byte for byte.

A placement is named by (sprite id or None for the main timeline, depth, character id), the
three numbers that identify it before the matrix in the tag.
"""
from __future__ import annotations

import struct

import swf_bitmaps

PLACE2, SPRITE = 26, 39


class Bits:
    """A bit cursor over bytes, most significant bit first (as SWF packs its records)."""

    def __init__(self, data: bytes, bit: int = 0):
        self.data, self.bit = bytearray(data), bit

    def read(self, n: int) -> int:
        value = 0
        for _ in range(n):
            value = (value << 1) | ((self.data[self.bit >> 3] >> (7 - (self.bit & 7))) & 1)
            self.bit += 1
        return value

    def read_signed(self, n: int) -> int:
        value = self.read(n)
        return value - (1 << n) if n and value & (1 << (n - 1)) else value

    def write(self, bit: int, n: int, value: int, signed: bool = True) -> None:
        """value (n bits, signed unless told otherwise) written at absolute bit offset `bit`."""
        low, high = (-(1 << (n - 1)), 1 << (n - 1)) if signed else (0, 1 << n)
        if not low <= value < high:
            raise ValueError(f"{value} does not fit {n} {'signed' if signed else 'unsigned'} bits")
        value &= (1 << n) - 1
        for i in range(n):
            b = bit + i
            mask = 1 << (7 - (b & 7))
            if (value >> (n - 1 - i)) & 1:
                self.data[b >> 3] |= mask
            else:
                self.data[b >> 3] &= ~mask & 0xFF


def matrix_fields(contents: bytes) -> tuple[int, int, int, int, int, int]:
    """For a PlaceObject2's contents: (bit offset where the matrix starts, bit offset of
    NTranslateBits, bit width of the translation, x, y, byte offset after the matrix)."""
    flags = contents[0]
    if not flags & 0x04:
        raise ValueError("placement has no matrix")
    start = 8 * (3 + (2 if flags & 0x02 else 0))
    bits = Bits(contents, start)
    if bits.read(1):  # HasScale
        n = bits.read(5)
        bits.read(n), bits.read(n)
    if bits.read(1):  # HasRotate
        n = bits.read(5)
        bits.read(n), bits.read(n)
    field = bits.bit
    n = bits.read(5)
    x, y = bits.read_signed(n), bits.read_signed(n)
    return start, field, n, x, y, (bits.bit + 7) // 8


def matrix_translate(contents: bytes) -> tuple[int, int, int, int]:
    """(bit offset of TranslateX, its bit width, x, y) in twips."""
    _, field, n, x, y, _ = matrix_fields(contents)
    return field + 5, n, x, y


def signed_bits(*values: int) -> int:
    """The smallest signed bit width that holds every value (SWF's SB fields)."""
    return max(1 + (v.bit_length() if v >= 0 else (-v - 1).bit_length()) for v in values)


def widen(place: bytes, new: tuple[int, int], n: int | None = None) -> bytes:
    """The PlaceObject2 contents with its matrix re-encoded so the translation fits: the bits
    before NTranslateBits copied, the translation written with the width it needs (or `n` bits,
    at least that), byte-padded, the rest of the tag appended unchanged."""
    start, field, _, _, _, after = matrix_fields(place)
    n = max(signed_bits(*new), n or 0)
    if n > 31:
        raise SystemExit("the translation would need more than 31 bits")
    total = (field - start) + 5 + 2 * n
    out, source = Bits(bytes((total + 7) // 8)), Bits(place, start)
    for i in range(field - start):  # HasScale .. the last rotate bit, copied one by one
        if source.read(1):
            out.data[i >> 3] |= 1 << (7 - (i & 7))
    out.write(field - start, 5, n, signed=False)  # NTranslateBits is UB[5]: 0..31
    out.write(field - start + 5, n, new[0])
    out.write(field - start + 5 + n, n, new[1])
    return place[:start // 8] + bytes(out.data) + place[after:]


def inner_tags(contents: bytes) -> list[tuple[int, int, int, int]]:
    """A DefineSprite's own tags as (code, start of header, start of contents, end). Every
    record must lie inside the sprite and the sprite must end with its End tag, or the sprite
    is refused before anything is patched."""
    out, p = [], 4
    while p < len(contents):
        start = p
        if p + 2 > len(contents):
            raise SystemExit("a sprite's record header runs past the sprite")
        head = struct.unpack_from("<H", contents, p)[0]
        code, length = head >> 6, head & 0x3F
        p += 2
        if length == 0x3F:
            if p + 4 > len(contents):
                raise SystemExit("a sprite's record header runs past the sprite")
            length = struct.unpack_from("<I", contents, p)[0]
            p += 4
        if p + length > len(contents):
            raise SystemExit(f"a sprite's record (code {code}) runs past the sprite")
        out.append((code, start, p, p + length))
        p += length
        if code == 0:
            if p != len(contents):
                raise SystemExit("bytes after a sprite's End tag")
            return out
    raise SystemExit("a sprite without its End tag")


def place_key(contents: bytes) -> tuple[int, int | None]:
    """(depth, character id or None) of a PlaceObject2."""
    flags, depth = contents[0], struct.unpack_from("<H", contents, 1)[0]
    return depth, struct.unpack_from("<H", contents, 3)[0] if flags & 0x02 else None


def find(body: bytes, sprite: int | None, depth: int, character: int) -> tuple[int, int, int]:
    """(top-level tag index, start, end of the PlaceObject2's contents within that tag's contents)."""
    found = swf_bitmaps.tags(body)
    hits = []
    for i, (code, _, contents) in enumerate(found):
        if sprite is None and code == PLACE2 and place_key(contents) == (depth, character):
            hits.append((i, 0, len(contents)))
        elif sprite is not None and code == SPRITE and struct.unpack_from("<H", contents)[0] == sprite:
            for icode, _, start, end in inner_tags(contents):
                if icode == PLACE2 and place_key(contents[start:end]) == (depth, character):
                    hits.append((i, start, end))
    where = f"sprite {sprite}" if sprite is not None else "the main timeline"
    if len(hits) != 1:
        raise SystemExit(f"placement depth {depth} of character {character} in {where}: "
                         f"{'not found' if not hits else 'found more than once'}")
    return hits[0]


def read(body: bytes, sprite: int | None, depth: int, character: int) -> tuple[int, int]:
    """The placement's translation (x, y) in twips."""
    i, start, end = find(body, sprite, depth, character)
    return matrix_translate(swf_bitmaps.tags(body)[i][2][start:end])[2:]


def move(body: bytes, sprite: int | None, depth: int, character: int,
         old: tuple[int, int], new: tuple[int, int], grow: bool = False) -> bytes:
    """The body with that placement's translation changed from old to new (twips), in place.
    With grow the matrix is re-encoded with the smallest wider translation field that makes the
    tag at least one byte longer (same values), for a file that must not keep Ford's length."""
    found = swf_bitmaps.tags(body)
    i, start, end = find(body, sprite, depth, character)
    code, header, contents = found[i]
    place = contents[start:end]
    at, n, x, y = matrix_translate(place)
    if (x, y) != tuple(old):
        raise SystemExit(f"placement depth {depth} of character {character} is at {(x, y)} twips, "
                         f"not {tuple(old)}: not the file this was made for")
    if grow:
        width = max(signed_bits(*new), n + 1)
        patched = widen(place, new, width)
        while len(patched) <= len(place):
            width += 1
            patched = widen(place, new, width)
    elif signed_bits(*new) <= n:
        bits = Bits(place)
        bits.write(at, n, new[0])
        bits.write(at + n, n, new[1])
        patched = bytes(bits.data)
        if len(patched) != len(place):
            raise SystemExit("the placement changed its length")
    else:
        patched = widen(place, new)
    if matrix_translate(patched)[2:] != tuple(new) or \
            patched[matrix_fields(patched)[5]:] != place[matrix_fields(place)[5]:]:
        raise SystemExit("the placement did not read back as written")
    if len(patched) == len(place):
        contents = contents[:start] + patched + contents[end:]
    elif sprite is None:
        contents = patched
        header = tag_header(PLACE2, len(contents))
    else:  # the inner tag's header and the sprite's own header follow the new length
        head_start = start - inner_header_length(contents, start)
        contents = contents[:head_start] + tag_header(PLACE2, len(patched)) + patched + contents[end:]
        header = tag_header(SPRITE, len(contents))
    found[i] = (code, header, contents)
    return b"".join(h + c for _, h, c in found)


def tag_header(code: int, length: int) -> bytes:
    """A tag header in the long form, as Flash accepts for every length."""
    return struct.pack("<HI", (code << 6) | 0x3F, length)


def inner_header_length(contents: bytes, start: int) -> int:
    """How many bytes the header of the inner tag whose contents start at `start` takes."""
    for _, hstart, cstart, _ in inner_tags(contents):
        if cstart == start:
            return cstart - hstart
    raise SystemExit("inner tag not found")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    sprite = None if sys.argv[2] == "main" else int(sys.argv[2])
    x, y = read(swf_bitmaps.unpack(Path(sys.argv[1]).read_bytes())[1], sprite, int(sys.argv[3]), int(sys.argv[4]))
    print(f"({x}, {y}) twips = ({x / 20:g}, {y / 20:g}) px")
