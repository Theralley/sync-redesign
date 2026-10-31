"""Draw a mock-up of a new SYNC 2 Apps menu (our own drawing, no Ford artwork).

Usage: python3 tools/mockup_apps_menu.py docs/mockups/apps-menu-v1.png
Needs Pillow. 800x480, the size of SYNC 2's screen; the content area between SYNC's own top
and bottom bars is about 800x378.
"""
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 800, 480
BG, PANEL, TEXT, DIM = (14, 16, 20), (30, 33, 40), (236, 238, 242), (140, 146, 158)
ACCENT = {"phone": (214, 160, 72), "nav": (72, 190, 150), "media": (220, 76, 84), "climate": (64, 150, 255)}
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def tile(draw, box, title, subtitle, accent, big=False):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=14, fill=PANEL)
    draw.rounded_rectangle((x0, y0, x0 + 6, y1), radius=3, fill=accent)  # one accent stripe
    cx, cy = (x0 + x1) // 2 + 3, y0 + (y1 - y0) * (40 if big else 42) // 100
    r = 46 if big else 26
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=accent, width=4 if big else 3)
    draw.text((cx, y1 - (64 if big else 40)), title, font=font(30 if big else 19, True), fill=TEXT, anchor="mm")
    draw.text((cx, y1 - (30 if big else 18)), subtitle, font=font(17 if big else 13), fill=DIM, anchor="mm")


def main(path):
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    # SYNC's own top bar, drawn faintly: the new menu lives between the bars
    draw.rectangle((0, 0, W, 50), fill=(8, 9, 12))
    draw.text((20, 25), "Apps", font=font(22, True), fill=TEXT, anchor="lm")
    draw.text((W - 20, 25), "14:32   12°C", font=font(20), fill=DIM, anchor="rm")
    tile(draw, (16, 64, 392, 412), "CarPlay", "Android Auto  ·  plug in the phone", ACCENT["phone"], big=True)
    small = [("Video Player", "MP4 from USB", ACCENT["media"]), ("Files", "Total Commander", ACCENT["nav"]),
             ("Restart SYNC", "Reboot", ACCENT["climate"]), ("Home", "back to SYNC", (150, 150, 160))]
    for i, (title, subtitle, accent) in enumerate(small):
        x, y = 408 + (i % 2) * 192, 64 + (i // 2) * 176
        tile(draw, (x, y, x + 176, y + 164), title, subtitle, accent)
    # SYNC's own bottom bar with the four areas, drawn faintly
    draw.rectangle((0, H - 52, W, H), fill=(8, 9, 12))
    for i, (name, accent) in enumerate(zip(("Phone", "Navigation", "Media", "Climate"), ACCENT.values())):
        x = 100 + i * 200
        draw.rectangle((x - 60, H - 52, x + 60, H - 49), fill=accent)
        draw.text((x, H - 26), name, font=font(16), fill=DIM, anchor="mm")
    image.save(path)


if __name__ == "__main__":
    main(sys.argv[1])
