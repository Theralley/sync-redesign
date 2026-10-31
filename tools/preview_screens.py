"""Render Ford's screens on the Mac (plan phase R2), as a baseline before and after a change.

Usage: python3 tools/preview_screens.py CAR_APPS_FOLDER OUTFOLDER [Area/File.swf ...]
CAR_APPS_FOLDER is the drive log's copy of \\8inchSkins\\Ford\\Sync\\Apps (in ~/.s2am).

Renders the first frame of each Flash file with FFDec (the same pinned copy and Docker image
as build_apps_menu.py, no network), as SYNC's designers left it: placeholder texts, no live
data. Writes <Area>_<File>.png and sheet.png. The pictures are Ford's artwork: keep OUTFOLDER
outside this repository.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from build_apps_menu import JAVA, ffdec

SCREENS = ["Home/Home.swf", "Phone/Phone.swf", "Media/Media.swf", "Media/MediaSmartCorner.swf",
           "Climate/Climate.swf", "Nav/Map.swf", "Nav/Nav.swf", "Info/Info.swf", "Menu/Menu.swf",
           "AppConsole/AppConsole.swf"]


def main(apps: str, out: str, screens: list[str]) -> None:
    apps_folder, out_folder = Path(apps), Path(out)
    out_folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        (work / "in").mkdir()
        for screen in screens:
            shutil.copyfile(apps_folder / screen, work / "in" / screen.replace("/", "_"))
        subprocess.run(["docker", "run", "--rm", "--network", "none", "-v", f"{ffdec()}:/ffdec:ro",
                        "-v", f"{work}:/work", JAVA, "java", "-Djava.awt.headless=true", "-jar",
                        "/ffdec/ffdec.jar", "-select", "1", "-export", "frame", "/work/out", "/work/in"],
                       check=True, capture_output=True)
        renders = sorted((work / "out").glob("*/1.png"))
        for render in renders:
            shutil.copyfile(render, out_folder / render.parent.name.replace(".swf", ".png"))
    pictures = sorted(p for p in out_folder.glob("*.png") if p.name != "sheet.png")
    cols, width, height = 3, 400, 240
    sheet = Image.new("RGB", (cols * width, ((len(pictures) + cols - 1) // cols) * (height + 20)), "white")
    for i, picture in enumerate(pictures):
        x, y = (i % cols) * width, (i // cols) * (height + 20)
        sheet.paste(Image.open(picture).convert("RGB").resize((width, height)), (x, y + 20))
        ImageDraw.Draw(sheet).text((x + 4, y + 4), picture.stem, fill="black")
    sheet.save(out_folder / "sheet.png")
    print(f"{len(pictures)} screens rendered in {out_folder} (sheet.png)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:] or SCREENS)
