"""Build the tiled Apps menu from your car's own SyncApps.swf (SyncExtPack's Apps menu).

Usage: python3 tools/build_apps_menu.py CAR_SYNCAPPS_SWF OUT_SWF

SyncExtPack's menu code has no licence, so it never goes into this repository: this tool
changes your own copy, on your Mac. It decompiles the class SyncAppsCustom with JPEXS FFDec
(pinned, checksum-verified, run in Docker without network), makes processXML() call
showTiles() instead of building the list, adds our tile code (tools/apps_menu_tiles.as), and
compiles that one class back. It then checks that exactly one tag of the file changed.

Needs Docker. Downloads FFDec 26.3.0 once into ~/.cache/sync-redesign.
"""
import hashlib
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

FFDEC = ("https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version26.3.0/ffdec_26.3.0.zip",
         "35f4930eb7c380afe66f2117f90b006deac0631473ad7500bb39c78f68645ecd")
JAVA = "eclipse-temurin@sha256:0b99b3376fbb50dbf9c0af8535fdd5b8eb0d3fdfc8b1e4967f383b6919f6901a"
CACHE = Path.home() / ".cache" / "sync-redesign" / "ffdec-26.3.0"
TILES = Path(__file__).with_name("apps_menu_tiles.as")
ANCHOR = "         super.FillTheList(_loc3_);"  # in processXML, as FFDec 26.3.0 decompiles it
FIELDS = "   var _xmlPath;\n"


def ffdec() -> Path:
    jar = CACHE / "ffdec.jar"
    if jar.is_file():
        return CACHE
    CACHE.mkdir(parents=True, exist_ok=True)
    archive = CACHE / "ffdec.zip"
    urllib.request.urlretrieve(FFDEC[0], archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != FFDEC[1]:
        archive.unlink()
        raise SystemExit("FFDec download does not match its checksum; not using it")
    with zipfile.ZipFile(archive) as zipped:
        zipped.extractall(CACHE)
    return CACHE


def run_ffdec(work: Path, *args: str) -> None:
    subprocess.run(["docker", "run", "--rm", "--network", "none", "-v", f"{ffdec()}:/ffdec:ro",
                    "-v", f"{work}:/work", JAVA, "java", "-Djava.awt.headless=true", "-jar", "/ffdec/ffdec.jar",
                    *args], check=True, capture_output=True)


def tags(data: bytes) -> list[tuple[int, str]]:
    """(tag code, sha256 of its body) for every tag, sprites' tags included."""
    if data[:3] != b"FWS":
        raise SystemExit("expected an uncompressed SWF (FWS)")
    nbits = data[8] >> 3
    out = []

    def walk(p: int, end: int) -> None:
        while p < end:
            head = struct.unpack_from("<H", data, p)[0]
            p += 2
            code, length = head >> 6, head & 0x3F
            if length == 0x3F:
                length = struct.unpack_from("<I", data, p)[0]
                p += 4
            out.append((code, hashlib.sha256(data[p:p + length]).hexdigest()))
            if code == 39:  # DefineSprite
                walk(p + 4, p + length)
            p += length
            if code == 0:
                return
    walk(8 + (5 + 4 * nbits + 7) // 8 + 4, len(data))
    return out


def main(source: str, target: str) -> None:
    original = Path(source).read_bytes()
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        (work / "in.swf").write_bytes(original)
        run_ffdec(work, "-export", "script", "/work/out", "/work/in.swf")
        code = (work / "out/scripts/__Packages/SyncAppsCustom.as").read_text()
        if code.count(ANCHOR) != 1 or code.count(FIELDS) != 1 or "showTiles" in code:
            raise SystemExit("this SyncApps.swf is not the SyncExtPack menu this tool knows; nothing built")
        code = code.replace(ANCHOR, "         this.showTiles(_loc3_);")
        code = code.replace(FIELDS, FIELDS + "   var _tileObjects;\n   var pThis;\n")
        code = code.rstrip()[:-1].rstrip() + "\n" + TILES.read_text() + "}\n"
        patch = work / "patch" / "__Packages"
        patch.mkdir(parents=True)
        (patch / "SyncAppsCustom.as").write_text(code)
        run_ffdec(work, "-importScript", "/work/in.swf", "/work/new.swf", "/work/patch")
        built = (work / "new.swf").read_bytes()
    before, after = tags(original), tags(built)
    changed = [b for a, b in zip(before, after) if a != b]
    if len(before) != len(after) or len(changed) != 1 or changed[0][0] != 59:  # one DoInitAction
        raise SystemExit(f"expected exactly one class to change, got {len(changed)} tags; nothing written")
    Path(target).write_bytes(built)
    print(f"{target}: {len(built)} bytes, sha256 {hashlib.sha256(built).hexdigest()}; "
          f"1 of {len(before)} tags changed (SyncAppsCustom)")


if __name__ == "__main__":
    if len(sys.argv) != 3 or shutil.which("docker") is None:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
