# Plan: a new look for SYNC 2, and a quicker feel

Planned 2026-10-31 by Claude from the files in SyncExtPack and the car's watch logs, reviewed
by Codex. Every step is one job stick built with
[sync2-auto-magic](https://github.com/Theralley/sync2-auto-magic)'s `s2am`, with a check in the
car, parked.

## What we know

- **Ford's screens are Flash files.** They live in `\8inchSkins\Ford\Sync\Apps\<area>\<screen>\`
  as `.swf` files with PNG and JPG pictures, and `Desktop.exe` shows them. The files are
  SWF version 8, 800x480, with ActionScript 2 classes (stored as `__Packages.*` exports).
  The wallpaper area is 800x378.
- **Changed screens load.** SyncExtPack replaces two Ford screens on every car it is installed
  on: the Apps menu (`Info\SyncApps\SyncApps.swf`) and the wallpaper editor's
  `Menu\Display\WallpaperEditor\AddPhotos\AddPhotos.swf`. That proves those two files are not
  locked; it says nothing yet about the others.
- **The code has a theme layer.** Both files call `SyncThemeUtil`, `SyncThemeButtonArt`,
  `SetSmartSkins` and `SyncButtonDayNight`, and sort buttons into Phone, Media, Nav, Climate,
  Menu, Home and Help. Colours and button art may come from shared code, so one change could
  restyle many screens. That is a guess until the car's files are mapped: the classes may be
  compiled into every file.
- **The wallpaper editor checks picture sizes** (`IMAGE_DIMENSION_REQUIREMENTS`), takes
  `.jpg`, `.gif`, `.png` and `.bmp` from USB and copies them to `Apps\Home\Wallpapers\`.
- **There is almost nothing to debloat.** The watch log shows about ten Ford programs: the
  kernel, three driver hosts, `servicesd.exe`, `Desktop.exe` (the screens, 56 threads),
  `mishell.exe`, `SysHealth.exe`, `MiniMedia.exe` and `vca_app.exe`. Each runs a part of the
  car (radio, phone, climate, voice). The work they do inside is not measured yet.
- **Slowness** comes from the hardware and the Flash screens. Lighter screens (shorter
  animations, smaller pictures) are the only lever, and the gain is not known.

## Rules

- **Ford's files never go into this repository**: no screens, no decompiled code, no dumps,
  no screenshots (they can show names and places from the phone). They stay in `~/.s2am/`. The repo holds only our tools and our own pictures; the skin job
  builds changed files on the Mac from the car's own copies, like `patch_waveout.py` does.
- **A wider write allowlist.** Today `s2am` writes only to `\SyncExtendedPack`, its plugins, the
  menu XML and icons. The skin job adds `\8inchSkins\` and nothing else, as its own job type.
- **Change pictures, not code**, as long as possible: swap image tags in place and leave every
  other byte as it was. FFDec's own documentation calls direct ActionScript editing
  experimental.
- **A restore stick exists before any change.** It is built with the same job and kept in the
  car. Packs only work inside their key window (the current one ends 2026-11-17 09:35 UTC), so
  the restore stick is rebuilt in every new window.
- **One screen at a time.** Every change is tested by tapping, in day and night mode, after a
  cold start, and with an incoming call and the reverse camera.

## Steps

| Step | What | Car | Gate |
|---|---|---|---|
| S0 | **Done 2026-10-31, see [FINDINGS.md](FINDINGS.md).** **Drive logger** (`s2am job logger --drive`): copies `\8inchSkins` to the stick with SHA-256 hashes, lists every file and the free space per disk, records the CE version, takes a screenshot whenever the screen changes | Leave it in while driving | The copy matches its hashes |
| S1 | **Baseline**: the same run logs processor load per program and free memory every 10 s. A run without the file copy gives cleaner numbers | 5 min tapping | Numbers per screen change |
| S2 | **Wallpapers**: a generator for 800x378 pictures (dark, plain, modern), added with SYNC's own wallpaper editor | Settings > Display | Shows, no hacking |
| S3 | **Map the screens on the Mac**: which file loads which, where pictures and colours are, whether a shared theme file exists. A byte-exact round trip of one screen | None | Unchanged file rebuilt identical |
| S4 | **Recovery rehearsal** (the first theme change and its undo stick do this, 2026-10-31): install an *unchanged* screen with the skin job, then restore it, both by stick | Two sticks | Reports match the hashes |
| S5 | **First change**: new pictures in one screen that is not shown at start-up, then restore | Test, restore | Works, restore works, cold start OK |
| S6 | **Theme**: `Sync\Themes\Theme.XML` and its four gradient pictures set the colours of every area (found 2026-10-31), so a recolour is five data files. Button art after that | Full test list | All areas, day and night |
| S7 | **Quicker feel**: shorter transitions, lighter pictures, keeping every script that runs when an animation ends | Measure again | Faster than S1, nothing stuck |
| S8 | **New layouts** (a cleaner home screen) | | Separate decision after S7 |

**Last resort** if SYNC does not start: reinstall 3.10 from USB with SyncExtPack's firmware
guide. It wipes SyncExtPack, so the first install has to be redone. It is not tested on this
car, and it is not known whether the stick channel still works when `Desktop.exe` cannot
start. S4 and S5 are ordered so that this never has to be found out: no file shown at
start-up is changed until a restore has worked.

## Open questions

- Does `Desktop.exe` check Ford's other screens (hash or signature)? S5 answers it.
- Does a changed file take effect at once, or only after a restart (caching)? S4.
- Is there a Lincoln skin on an EU car, and could the car be switched to it? S0 answers the first.
