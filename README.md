# sync-redesign

A new look for Ford's SYNC 2 (MyFord Touch, 8" screen), and a quicker feel, done in small
steps that can always be undone. The companion of
[sync2-auto-magic](https://github.com/Theralley/sync2-auto-magic), which builds the USB job
sticks this project uses to read from and write to the car.

**Status (2026-10-31):** planning and data collection. Nothing on the car has been changed.

## What SYNC 2's screens are

- Flash files (`.swf`, SWF version 8, ActionScript 2) with PNG and JPG pictures, in
  `\8inchSkins\Ford\Sync\Apps\<area>\<screen>\` on the car, shown by `Desktop.exe`.
- The screen is 800x480; the area above the bottom bar, where the wallpaper goes, is 800x378.
- The code has a theme layer (`SyncThemeUtil`, `SyncThemeButtonArt`, `SetSmartSkins`, day and
  night buttons, colours per area). SyncExtPack already replaces two of Ford's screens, so
  changed screens do load.

The whole plan, with what is known and the safety rules: [docs/PLAN.md](docs/PLAN.md).

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

## Rules

- **Ford's files never go into this repository**: no screens, no decompiled code, no copies
  from the car, and no screenshots (they can show names and places from your phone). They stay
  on your Mac, in `~/.s2am/`. `.gitignore` blocks `*.swf`, `*.bmp` and the dump folders.
- The repository holds only our own tools and our own artwork. Changed screens are built on
  your Mac from your car's own files.
- Every change comes with a backup on the car and an undo stick, made before the change.

## License

MIT, for this repository's own code and artwork. Ford's files are Ford's.
