# sync-redesign

A new look for Ford's SYNC 2 (MyFord Touch, 8" screen), and a quicker feel, done in small
steps that can always be undone. The companion of
[sync2-auto-magic](https://github.com/Theralley/sync2-auto-magic), which builds the USB job
sticks this project uses to read from and write to the car.

**Status (2026-10-31):** the first drive log is in ([docs/FINDINGS.md](docs/FINDINGS.md)): the colours
are a plain XML file and four gradient pictures, and the full Lincoln skin is on the car. The
first change (Lincoln's colours, with its undo stick) is built and rehearsed on the Mac, and
not yet run in the car.

## What SYNC 2's screens are

- Flash files (`.swf`, SWF version 8, ActionScript 2) with PNG and JPG pictures, in
  `\8inchSkins\Ford\Sync\Apps\<area>\<screen>\` on the car, shown by `Desktop.exe`.
- The screen is 800x480; the area above the bottom bar, where the wallpaper goes, is 800x378.
- The code has a theme layer (`SyncThemeUtil`, `SyncThemeButtonArt`, `SetSmartSkins`, day and
  night buttons, colours per area). SyncExtPack already replaces two of Ford's screens, so
  changed screens do load.

The whole plan, with what is known and the safety rules: [docs/PLAN.md](docs/PLAN.md).
How to undo any change, step by step: [docs/RECOVERY.md](docs/RECOVERY.md).
The plan for a new menu, with a first mock-up: [docs/MENU-PLAN.md](docs/MENU-PLAN.md).
The plan for a completely new interface, with sketches per screen: [docs/REDESIGN-PLAN.md](docs/REDESIGN-PLAN.md).
Its review from the driver's seat (glance, gloves, climate, icons, language, performance):
[docs/UX-REVIEW.md](docs/UX-REVIEW.md).
Speed on the map: [docs/SPEED.md](docs/SPEED.md). A night screen, and album covers over Bluetooth:
[docs/NIGHT.md](docs/NIGHT.md). Spotify on SYNC 2, which way: [docs/SPOTIFY.md](docs/SPOTIFY.md).
The next car test, step by step (Swedish): [docs/BILTEST.md](docs/BILTEST.md).

![A mock-up of a new Apps menu (our own drawing)](docs/mockups/apps-menu-v1.png)

## Changing the colours

With sync2-auto-magic, after a drive log:

```sh
python3 -m s2am job theme --preset lincoln --serial YOURSERIAL      # the change stick
python3 -m s2am job theme --restore <that job> --serial YOURSERIAL  # its undo stick, built at once
```

The change backs up the five theme files on the car and the stick, copies the new ones in and
restarts SYNC; the Mac checks every byte after import. The undo stick carries the originals.

## A new Apps menu

The Apps menu (where AutoKit, Video Player and Total Commander live) becomes a grid of big
tiles: CarPlay first, three small tiles, and "All apps", which shows the old list. It is
SyncExtPack's file, not Ford's, and SYNC loads it only when Apps is opened.

```sh
python3 tools/make_tiles.py tiles/
python3 tools/build_apps_menu.py ~/.s2am/SERIAL/reports/<drive log>/skins/8inchSkins/Ford/Sync/Apps/Info/SyncApps/SyncApps.swf SyncApps-tiles.swf
python3 -m s2am job apps-menu --swf SyncApps-tiles.swf --tiles tiles/ --serial YOURSERIAL   # change stick
python3 -m s2am job apps-menu --restore <that job> --serial YOURSERIAL                     # undo stick
```

SyncExtPack publishes its menu without a licence, so this repository never holds its code:
the build changes your own copy on your Mac.

## Collecting data from the car

With sync2-auto-magic, a drive logger stick:

```sh
python3 -m s2am job logger --drive --serial YOURSERIAL
python3 -m s2am stick prepare /Volumes/STICK --job <the job folder it prints>
# in the car: insert, leave it in while you drive, pull it at the end
python3 -m s2am stick import /Volumes/STICK
python3 -m s2am report --serial YOURSERIAL
```

It records the system's facts, processor load and memory every 10 s, a list of every file, a
copy of `\8inchSkins` with SHA-256 hashes, and a screenshot whenever the screen changes. It
only reads from the car.

## Tools

| Tool | What it does |
|---|---|
| `tools/swftags.py FILE.swf` | Lists an SWF's tags, its exported ActionScript 2 classes and the strings in its code. No Java needed |
| `tools/mockup_apps_menu.py OUT.png` | Draws the Apps menu mock-up (our own drawing, Pillow) |
| `tools/make_tiles.py OUTFOLDER [--lang sv\|en]` | Draws the tile pictures for the new Apps menu (our own drawings), Swedish by default, full colour but compact |
| `tools/make_theme.py CAR_THEMES OUT` | The "Night" colours: the car's own Theme.XML and gradients, recoloured in exactly their format |
| `tools/preview_screens.py CAR_APPS OUT` | Renders Ford's screens on the Mac (FFDec) as a baseline; keep the pictures private |
| `tools/mockup_redesign.py OUT [--lang sv\|en]` | Draws the redesign sketches (our own drawings), Swedish by default, and prints how much light the night screen gives off |
| `tools/icons.py` | The redesign's one icon family (26 icons, climate symbols after Ford's own), used by the tiles and the sketches; `python3 -m unittest discover tests` checks it |
| `tools/build_apps_menu.py CAR_SWF OUT_SWF` | Builds the tiled Apps menu from **your car's own** SyncApps.swf: adds `tools/apps_menu_tiles.as` with FFDec (pinned, in Docker) and checks that only one class changed |

## Rules

- **Ford's files never go into this repository**: no screens, no decompiled code, no copies
  from the car, and no screenshots (they can show names and places from your phone). They stay
  on your Mac, in `~/.s2am/`. `.gitignore` blocks `*.swf`, `*.bmp` and the dump folders.
- The repository holds only our own tools and our own artwork. Changed screens are built on
  your Mac from your car's own files.
- Every change comes with a backup on the car and an undo stick, made before the change.

## License

MIT, for this repository's own code and artwork. Ford's files are Ford's.
