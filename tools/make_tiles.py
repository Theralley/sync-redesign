"""Draw the tile pictures for the new SYNC 2 Apps menu (our own drawings, no Ford artwork).

Usage: python3 tools/make_tiles.py OUTFOLDER [--lang sv|en]
Writes <native>.png (155x145, a small tile) and <native>-big.png (295x300, the first tile) for
each app below, plus AllApps.png, the tile that shows the original list. The menu loads them
from \\8inchSkins\\Ford\\Sync\\Apps\\Info\\SyncApps\\Tiles\\ on the car. Swedish is the default
language. Icons come from icons.py, the redesign's one icon family. The pictures stay full
colour (RGB), the only PNG kind SYNC's own screens use, but with fewer colours, so they pack
smaller. Needs Pillow.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import icons

SMALL, BIG = (155, 145), (295, 300)
SURROUND = (0x14, 0x16, 0x1A)  # the menu draws this behind each tile; it fills the corners
PANEL, TEXT, DIM = (30, 33, 40), (236, 238, 242), (160, 166, 178)
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
SCALE = 3  # drawn larger, then scaled down, for smooth edges
COLOURS = 48  # per tile; still full-colour PNG

# native name (from SyncApps.xml) -> accent, icon, {language: (title, subtitle)}
APPS = {
    "AutoKitPlugin": ((214, 160, 72), "carplay", {"sv": ("CarPlay", "och Android Auto"),
                                                 "en": ("CarPlay", "and Android Auto")}),
    "VideoPlayer": ((220, 76, 84), "video", {"sv": ("Video", "MP4 från USB"), "en": ("Video", "MP4 from USB")}),
    "ExplorerPlugin": ((72, 190, 150), "files", {"sv": ("Filer", "Total Commander"),
                                                "en": ("Files", "Total Commander")}),
    "RebootPlugin": ((64, 150, 255), "restart", {"sv": ("Starta om", "SYNC"), "en": ("Restart", "SYNC")}),
    "AllApps": ((150, 150, 160), "apps", {"sv": ("Alla appar", "hela listan"), "en": ("All apps", "the full list")}),
}


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def tile(size, title, subtitle, accent, icon):
    w, h = size[0] * SCALE, size[1] * SCALE
    big = size == BIG
    image = Image.new("RGB", (w, h), SURROUND)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=14 * SCALE, fill=PANEL)
    draw.rounded_rectangle((0, 0, 6 * SCALE, h - 1), radius=3 * SCALE, fill=accent)  # the accent stripe
    cx = w // 2 + 3 * SCALE
    icons.draw(draw, icon, cx, int(h * (0.38 if big else 0.36)), (104 if big else 48) * SCALE, accent)
    title_size, sub_size = (36, 19) if big else (21, 14)
    while draw.textlength(title, font=font(title_size * SCALE, True)) > w - 24 * SCALE and title_size > 10:
        title_size -= 1
    draw.text((cx, h - (72 if big else 42) * SCALE), title, font=font(title_size * SCALE, True), fill=TEXT,
              anchor="mm")
    draw.text((cx, h - (34 if big else 18) * SCALE), subtitle, font=font(sub_size * SCALE), fill=DIM, anchor="mm")
    small = image.resize(size, Image.LANCZOS)
    return small.quantize(COLOURS, dither=Image.Dither.NONE).convert("RGB")


def main(out, lang="sv"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, (accent, icon, words) in APPS.items():
        title, subtitle = words[lang]
        tile(SMALL, title, subtitle, accent, icon).save(out / f"{name}.png", optimize=True, compress_level=9)
        tile(BIG, title, subtitle, accent, icon).save(out / f"{name}-big.png", optimize=True, compress_level=9)
    total = sum(f.stat().st_size for f in out.glob("*.png"))
    print(f"{2 * len(APPS)} tiles ({lang}) in {out}: {total} bytes")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 4) or (len(sys.argv) == 4 and (sys.argv[2] != "--lang" or sys.argv[3] not in ("sv", "en"))):
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[3] if len(sys.argv) == 4 else "sv")
