# Plan: a new interface menu

Planned 2026-10-31 from the car's own files (drive log of that day). The aim is a cleaner,
quicker menu without ever leaving the car without a way back ([RECOVERY.md](RECOVERY.md)).

## What the menus are made of

| Menu | File on the car | Made by | Start-up? |
|---|---|---|---|
| Home (the four corners) | `Sync\Apps\Home\Home.swf` (184 KB, Flash 10, ActionScript 2 with Flash's standard component library), `EditShortcuts.swf` | Ford | Yes |
| Apps (AutoKit, Video Player, ...) | `Sync\Apps\Info\SyncApps\SyncApps.swf` and `SyncApps.xml`, icons in `Icons\` | SyncExtPack, rebuilt with `swfmill` | No |
| Colours of every menu | `Sync\Themes\Theme.XML` and four gradient BMPs | Ford | Yes |
| Shared parts | `Sync\Components\` (dialogs, keyboard, file browser, icons) | Ford | Yes |

The Home screen reads its corners from plugins (`PluginShortcuts`, `ShortcutPaths`,
`HomeConstants`) and SYNC's data store (`DataManager.GetDMNumber`), so a new Home screen must
keep those calls and the class names Ford's code looks for.

## Steps

| Step | What | Risk | Gate |
|---|---|---|---|
| M1 | **Colours**: `s2am job theme` (Lincoln preset now, our own palette next). Theme preview on the Mac before each change | Low: data files, Ford's own format | **Done 2026-10-31**: change and undo verified in the car; the visible change was small |
| M2 | **Our own palette**: a flat, dark set (deep grey background, one accent per area, less glow), as `Theme.XML` + four 800x240 gradients from a generator in `tools/` | Low | Preview, then car test with undo |
| M3 | **A new Apps menu**: big tiles (CarPlay/Android Auto first), dark and flat, generated with `swfmill` the way SyncExtPack builds its own. Not a start-up file | Low to medium | **Built 2026-10-31** (`tools/build_apps_menu.py`, `make_tiles.py`), rehearsed with the car's files; first car test that day |
| M4 | **Decompile and document Home.swf on the Mac** (FFDec in Docker): which calls fill each corner, which events it sends | None (Mac only) | A written map of Home's code |
| M5 | **A lighter Home**: the same four corners without animations and with fewer layers, to cut `Desktop.exe`'s ~52% processor use at rest. Changes only pictures and timings first, code last | Medium: a start-up file | Only after M1 and M3 have proven undo in the car |
| M6 | **A new Home layout** (for example a big CarPlay tile, clock, now playing) | High | Separate decision after M5 |

## Look and feel

- Dark and flat: near-black background, one clear accent colour per area, no gradients
  behind text. Easier to read at night and cheaper to draw.
- Big touch targets: the 8" screen is far from the driver; tiles at least 180x120 pixels.
- CarPlay / Android Auto as the first tile of the Apps menu, since it will be used most.
- The same layout day and night; only brightness changes.

Mock-ups are our own drawings (no Ford artwork) in `docs/mockups/`.

## How the Apps menu works (from SyncExtPack's SyncApps.swf, 2026-10-31)

- Four ActionScript 2 classes: `SyncApps` (Ford's Apps screen logic), `SyncAppsCustom`
  (SyncExtPack's: reads `SyncApps.xml`), `SetAppsRow` (one row of the list) and
  `SyncButtonDayNight`.
- `SyncAppsCustom.processXML()` turns `SyncApps.xml` into up to ten entries and hands them to
  `SyncApps.FillTheList()`, which builds a 2x5 list (rows 44 px high, 650 px wide) in the area
  x 170-795, y 106-406. The rest of the screen is SYNC's own frame.
- An app starts with `new Plugins.NativeApplet(<native>)`, the `<native>` name from the XML.
- If a stick holds `skeleton_key.dat`, the menu reads its list from `\USB Disk\SyncApps.xml`
  instead: a way to try menu entries without writing to the car.
- SyncExtPack's menu switches off SYNC's while-driving restrictions
  (`BezelDiagnosticsPlugin.SetDrivingRestrictions(false)`). The tiled menu keeps that
  unchanged; the project's rule stays: use the apps when parked.
- Our change: `processXML()` calls `showTiles()` instead, which draws the tiles on top
  (pictures from `Tiles\<native>[-big].png`); "All apps" calls the original `FillTheList()`.
