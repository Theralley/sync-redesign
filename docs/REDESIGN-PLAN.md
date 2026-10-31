# Plan: a completely new SYNC 2 interface

**Status (2026-10-31):** plan approved by Rasmus; R1 built and rehearsed on the Mac, R2 done.
Nothing goes into the car before Rasmus's car test, one phase at a time. Sketches: [mockups/redesign-overview.png](mockups/redesign-overview.png)
and one picture per screen in [mockups/](mockups/).

## What is already proven in the car

| Proven | How we know |
|---|---|
| Reading the whole system without changing it | Drive log: CE 6.0, i.MX51, 483 MB, the full `\8inchSkins` copied with hashes ([FINDINGS.md](FINDINGS.md)) |
| Changing SYNC's colours, and undoing it | Theme job and its undo stick, both verified byte for byte |
| Replacing a whole screen with our own layout | The tiled Apps menu, photographed working on 2026-10-31 at 11:43: tiles, PNG pictures and taps all on the car's own Flash player |
| Changing one Flash class and nothing else | FFDec decompile → change → compile one class; 1 of 198 tags differs; decompiles back the same |
| Undo carries the originals itself | Works even without the backup on the car |

## Goals

1. **Calm and readable:** dark, flat, one accent colour per area, big type, no glow behind text.
2. **Fewer taps:** Home shows what matters at a glance: what is playing, the route, the phone,
   the climate.
3. **CarPlay and Android Auto first:** one tap from anywhere.
4. **A quicker feel:** fewer animations and layers. `Desktop.exe` uses about 52% of the
   processor even with a still screen.
5. **Always undoable:** every change has an undo stick before it goes in, and nothing risks a
   SYNC that cannot be brought back.

## The look ("SYNC 2 Night")

Reviewed from the driver's seat in [UX-REVIEW.md](UX-REVIEW.md): rules for glance, contrast,
touch targets, icons, language and performance, with before and after numbers.

| Element | Choice |
|---|---|
| Background / cards / buttons | `#0E1014` / `#1E2128` / `#282C35` |
| Text / quiet text | `#ECEEF2` / `#969CA8` |
| Area accents | Phone amber `#D6A048`, Navigation teal `#48BE96`, Media red `#DC4C54`, Climate blue `#4096FF`, Info grey `#9696A0` |
| Type | Headings 30-40 px bold, body 18-22 px, labels 14-16 px, sentence case; Swedish first |
| Touch targets | At least 80 px high (about 18 mm), enough with gloves ([UX-REVIEW.md](UX-REVIEW.md)) |
| Corners / accent | 12-14 px radius; a 6 px accent stripe on the left of each card |
| Day and night | The same layout; only brightness changes |

## Screen by screen

| Screen | Sketch | New layout | Files on the car | Shown at start-up? |
|---|---|---|---|---|
| **Frame** (status bar and area bar on every screen) | all sketches | A thin status bar (title, clock, outside temperature, phone); one area bar at the bottom: Phone, Map, Home, Media, climate temperature | `Apps\AppConsole\AppConsole.swf` (1.1 MB) | **Yes** |
| **Home** | `redesign-home.png` | Four cards: Now playing with controls (large), Navigation (route, arrival), Phone, Climate | `Apps\Home\Home.swf` (184 KB, Flash 10) | **Yes** |
| **Media** | `redesign-media.png` | Sources on the left (FM, DAB, USB, Bluetooth, CarPlay), now playing on the right, big controls, presets | `Apps\Media\` 37 Flash files, 3 MB | No |
| **Phone** | `redesign-phone.png` | Recent calls on the left; Keypad, Contacts, Favourites, Messages as big buttons | `Apps\Phone\` 23 Flash files, 2.7 MB | No |
| **Climate** | `redesign-climate.png` | **Restyled in place:** all 21 of Ford's controls stay where they are (checked against a photo of the car's climate screen) | `Apps\Climate\` 35 Flash files, one per car model | No |
| **Navigation** | `redesign-nav.png` | Ford's map stays; new turn card, arrival card and zoom buttons on top | `Apps\Nav\` 39 Flash files, 4.8 MB | No |
| **Apps** | `apps-menu-v1.png` | Done: big tiles, CarPlay first | SyncExtPack's `SyncApps.swf` | No |
| Settings, dialogs, keyboard | (not sketched) | Same colours and type, later | `Apps\Menu\` 64 files; `Components\` shared by all screens | Components: yes |

## What can and cannot be changed

**Can, proven:** the colours file and gradients; a whole screen's layout through one recompiled
class (Apps menu); pictures the screens load from files (PNG/JPG, as the Apps menu's tiles).

**Can, expected but not yet proven on Ford's own files:**
- Pictures built into a Ford screen, replaced without touching its code (FFDec image replace).
- Ford's own classes, changed the same way as the Apps menu. Ford's screens are Flash 8 and 10
  with ActionScript 2, like the Apps menu.
- The wallpaper (SYNC's own editor) and the start and goodbye animations (MP4, 800x480 H.264,
  which SYNC plays well).

**Cannot, or not realistic:**
- **The map itself:** it is drawn by the navigation engine, not by Flash. Only what lies on top
  of it can change.
- **The reversing camera picture:** a hardware layer.
- The physical buttons; voice control and its spoken prompts (Nuance).
- **Call sound:** that is Bluetooth, not the interface.
- **A new font everywhere at once:** each Flash file carries its own fonts, so a font changes
  screen by screen.
- **The processor:** it stays. Only lighter screens can help.
- **Ford's programs in `\Windows`:** read-only, built into the system image.
- Screenshots of the Flash screens: only photos show them (FINDINGS.md).

**Not known yet:**
- Whether SYNC checks Ford's own Flash files (the Apps menu was SyncExtPack's). Phase R3
  answers it on a screen that is not shown at start-up.
- Which Climate file the Mondeo uses.
- Whether the texts in `\DataManager\*.db` can be changed safely.

## Order of work

Each phase is one change stick and one undo stick, tested parked, imported and verified before
the next.

| Phase | What | Risk |
|---|---|---|
| R0 | **Done:** the colours route, the new Apps menu | |
| R1 | **"Night" colours:** our own `Theme.XML` and gradients (`tools/make_theme.py`). **Built and rehearsed 2026-10-31; waits for the car** | Low: data, start-up but Ford's own format, proven route |
| R2 | **Preview on the Mac:** render Ford's screens with FFDec, before and after a change, so each step is seen before the car. **Done 2026-10-31** (`tools/preview_screens.py`; the pictures stay private) | None |
| R3 | **First Ford screen, not at start-up** (a Phone or Climate sub-screen): pictures only, then one class. Proves Ford's files accept changes | Low to medium |
| R4 | **Media, Phone, Climate**, one screen per visit | Medium |
| R5 | **Navigation overlays** (turn card, buttons) and the **speed box**: the speed limit from Ford's map data beside the GPS speed ([SPEED.md](SPEED.md)) | Medium |
| R6 | **Start-up rehearsal:** change one start-up file that nobody sees (the goodbye animation's still) and undo it, to prove recovery where it matters | Medium |
| R7 | **Home** (start-up): the four cards | High |
| R8 | **Frame** (`AppConsole.swf`, start-up, on every screen) | Highest |
| R9 | **Quicker feel:** fewer animations; measure `Desktop.exe` with the drive logger before and after | Medium |

## Risks and the way back

| Risk | What happens | Prevention and undo |
|---|---|---|
| A changed screen that is not at start-up fails | That screen is empty or wrong; the rest of SYNC works | Undo stick |
| A changed start-up file fails (Home, frame, colours) | SYNC's screens may not start | Phase R6 first; one file at a time; two healthy sticks; undo stick (may still run, untested); last resort: reinstall SYNC 3.10, which also removes SyncExtPack ([RECOVERY.md](RECOVERY.md)) |
| SYNC checks Ford's files | A changed Ford screen is refused | Found in R3, on a screen that is not at start-up |
| Decompiling and compiling changes more than intended | Behaviour drifts | One class at a time; tag comparison (only that class differs); decompile again and compare; Codex review |
| Climate controls stop working | Defrost or heat unreachable: a safety issue | Climate pictures first, code later; test MAX DEFROST, A/C, fan and temperature every time |
| Reversing camera hidden by a new layer | No camera picture | Never cover it; test reverse every time |
| Distraction while driving | | Nothing new to tap while driving; SYNC's own driving lockouts stay as they are (SyncExtPack's Apps menu already switches them off; noted) |
| Packs expire | A stick does nothing | Undo sticks rebuilt in every key window (the current one ends 2026-11-17) |
| A stick breaks | No undo in the car | The 2 GB stick failed on 2026-10-31: use two healthy sticks; every stick is read back after writing |
| Copyright | | Ford's and SyncExtPack's files never go into a repository; every change is built on the Mac from the car's own copies |

## Car test plan, every phase

Before: a fresh drive log if the files may have changed; both sticks written and read back;
the undo stick in the car.

Parked, engine running:
1. Insert the change stick, wait for "Install successfully completed"; SYNC restarts.
2. **Photo** of every changed screen.
3. Checklist: every button on the changed screen; the four areas and Home from each; an
   incoming and an outgoing call; radio, USB and Bluetooth sound; climate (temperature,
   A/C, fan, **MAX DEFROST**); **reverse gear and the camera**; night mode (headlights on);
   the voice button.
4. Cold start: car off, wait a minute, start; check the changed screen again.
5. The first time a kind of file is changed: the undo stick, then a photo of the original.
6. Bring both sticks back; import must say `verified`; results go into the test log.

**Stop rule:** anything odd, put the undo stick in at once, and no second change that day.

## What would help

- A go per phase.
- A second healthy USB stick (FAT32), for the undo.
- Photos of each screen as it looks today (Home, Media, Phone, Climate, Map, Settings), in
  day and night mode: the baseline for the redesign, since screen copies cannot show them.
