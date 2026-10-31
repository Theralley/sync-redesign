"""List an SWF's tags, its exported AS2 classes and the strings in its ActionScript code.

Usage: python3 tools/swftags.py FILE.swf   (no Java needed; reads the file only)
"""
import re, struct, sys, zlib
from collections import Counter
NAMES = {0: "End", 1: "ShowFrame", 2: "DefineShape", 6: "DefineBits", 8: "JPEGTables", 9: "SetBackgroundColor",
         10: "DefineFont", 11: "DefineText", 12: "DoAction", 13: "DefineFontInfo", 14: "DefineSound", 20: "DefineBitsLossless",
         21: "DefineBitsJPEG2", 22: "DefineShape2", 26: "PlaceObject2", 28: "RemoveObject2", 32: "DefineShape3",
         33: "DefineText2", 34: "DefineButton2", 35: "DefineBitsJPEG3", 36: "DefineBitsLossless2", 37: "DefineEditText",
         39: "DefineSprite", 43: "FrameLabel", 48: "DefineFont2", 56: "ExportAssets", 57: "ImportAssets",
         59: "DoInitAction", 69: "FileAttributes", 71: "ImportAssets2", 75: "DefineFont3", 77: "Metadata", 88: "DefineFontName"}
data = open(sys.argv[1], "rb").read()
if data[:3] == b"CWS":
    data = data[:8] + zlib.decompress(data[8:])
nbits = data[8] >> 3
pos = 8 + (5 + 4 * nbits + 7) // 8
bits = int.from_bytes(data[8:pos], "big")
total = (pos - 8) * 8
vals = [(bits >> (total - 5 - nbits * (i + 1))) & ((1 << nbits) - 1) for i in range(4)]
print(f"version {data[3]}, stage {vals[1] / 20:.0f}x{vals[3] / 20:.0f}, fps {data[pos + 1]}")
pos += 4
counts, strings, exports, imports = Counter(), Counter(), [], []
def walk(buf, p, end):
    while p < end:
        head = struct.unpack_from("<H", buf, p)[0]; p += 2
        code, length = head >> 6, head & 0x3F
        if length == 0x3F:
            length = struct.unpack_from("<I", buf, p)[0]; p += 4
        body = buf[p:p + length]
        counts[NAMES.get(code, code)] += 1
        if code == 39:
            walk(buf, p + 4, p + length)
        elif code in (12, 59):
            for s in re.findall(rb"[\x20-\x7e]{3,}(?=\x00)", body):
                strings[s.decode()] += 1
        elif code == 56:
            n = struct.unpack_from("<H", body)[0]; q = 2
            for _ in range(n):
                q += 2; e = body.index(b"\0", q); exports.append(body[q:e].decode("latin1")); q = e + 1
        elif code in (57, 71):
            imports.append(body[:body.index(b"\0")].decode("latin1"))
        p += length
        if code == 0:
            return
walk(data, pos, len(data))
print("tags:", dict(counts.most_common()))
print("imports from:", sorted(set(imports)))
print("exports:", exports[:30])
print("code strings:", ", ".join(s for s, _ in strings.most_common(400)))
