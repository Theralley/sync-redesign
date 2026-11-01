# Findings from the car

## First drive log, 2026-10-31

A 22-minute run of sync2-auto-magic's drive logger (`s2am job logger --drive`) in a 2016
Mondeo Mk5, 8" SYNC 2, software 3.10. It only read from the car.

### The system

| | |
|---|---|
| Operating system | Windows CE **6.0** |
| Chip | Freescale **i.MX51** (`platform i.MX51`, `oem Ford Sync GenII`) |
| Memory | 483 MB, about 180 MB free while running |
| Screen | 800x480, 16 bits per pixel |
| Main flash disk | 1277 MB, 417 MB free (holds `\8inchSkins`, `\Windows`, `\Animations`, ...) |
| Other disks | `\UserData` 551 MB, `\SDMemory` 60 GB (navigation maps), `\TempData`, `\GraphicWeather` |

### Where the time goes

The processor was busy **95-100%** of the time while the logger copied files, and about
**80%** afterwards. With the logger's own share taken off, **SYNC is about 70% busy even
when nothing on the screen changes**.

| Program | Share of the processor at rest |
|---|---|
| `Desktop.exe` (Ford's Flash screens) | **about 52%** |
| `NK.EXE` (the kernel) | about 7% |
| `s2amdrive.exe` (the logger: one screen copy per second) | about 13%; to be made lighter |

So the lag is mostly the Flash screens themselves, and a lighter screen is the main lever for
a quicker feel (plan step S7).

### Ford's screens, `\8inchSkins`

- 1253 files, 51 MB: a **Ford** and a complete **Lincoln** skin side by side, 626 files each
  (343 Flash screens, 143 PNG, 110 JPG, XML), in `\8inchSkins\<brand>\Sync\Apps\<area>\`.
- The areas: AppConsole, Climate, DriverAssist, EmergencyAssist, Ev, Home, Info, Media,
  Menu, Nav, Phone, PowerModing, Provisioning, Vui, plus diagnostics.
- **Ford and Lincoln differ in only 9 files:** `Sync\Themes\Theme.XML`, four gradient
  pictures `Sync\Themes\{yellow,green,red,blue}.bmp` (800x240), and four Flash screens
  (AppConsole, Media, Phone, Menu\Vehicle\AmbientLighting). Everything else is identical.
- **The colours are a text file.** `Theme.XML` gives each area (System, TopLeft = phone,
  TopRight = navigation, BottomLeft = media, BottomRight = climate) a button, dialog, day
  and night colour. Ford left a second, more colourful day/night set in it as comments. The
  gradient pictures are the coloured glow at the top or bottom of each area.

So a **new colour theme is five data files** (the XML and four pictures), not Flash code.
That makes plan step S6 much safer than first thought.

### Screenshots

The logger's screen copies show **only the coloured glow, not the buttons and text**. The
Flash screens are drawn on a separate graphics layer that an ordinary screen copy cannot
read; the layer underneath (the gradient pictures) and normal windows (SyncExtPack's
installer) do show. The glow still tells which area was open when.

For pictures of the screens themselves, the Flash files will be rendered on the Mac instead.

### Other things a redesign could change

- `\Animations\Ford\DM8\`: the welcome, goodbye and door-open animations are **MP4 files**
  (`Ford_DM8_Wel_Anim.mp4`, `Ford_DM8_Dep_Anim.mp4`, ...), plus 800x480 16-bit BMP stills.
  The Video Player test showed SYNC plays 800x480 H.264 well. They play at start-up, so they
  wait until a restore has been proven (plan rule).
- `\Nuance` (589 MB) is voice control, `\Gracenote` (66 MB) music recognition,
  `\SDMemory` the navigation maps. None of them is a redesign target.

## First change in the car, 2026-10-31

Lincoln's colours on Ford's theme (`s2am job theme --preset lincoln`), then its undo stick.
Both verified byte for byte after import. **The colours file works, and the undo works.** The
visible change was small: Lincoln's palette is muted, and `Theme.XML` with the gradients
colours only the glow and the area buttons. A bigger look needs our own, bolder palette
(menu plan M2), then the Flash screens themselves (M3 onwards).

Fetching car files for study: files built into SYNC's read-only system image (most of
`\Windows\*.dll`) cannot be copied as files on CE; only files on the flash disk can.

## Which screens load at start-up (2026-10-31)

From the frame's own code (`AppConsole.swf`, decompiled on the Mac; the code stays private):
at start-up it loads the system apps (Home, Menu, Driver Assist and others) and the four
**corner apps**, the main screens of Phone, Navigation, Media and Climate (`LoadCornerApps`,
names from the registry), all hidden until opened. Their sub-screens load only when opened:
for Phone the call history, keypad, phonebook, quick dial and messages. A changed sub-screen
can at worst fail when opened; a changed main screen is read at every start.

## The first bundle in the car (2026-10-31, evening)

- All five parts went on and were verified byte for byte after import, and the undo bundle
  put everything back the same way. The bundle route works in the car.
- **SYNC kept running with a changed Ford file** (the call history, R3b) on the car. Rasmus
  saw the call history unchanged, but cannot say whether SYNC had restarted first, so whether
  SYNC draws our screen is the next visit's question (a photo after the restart).
- **Theme.XML changes are hard to see.** Night dims the glow and strengthens the area buttons a
  little; Rasmus did not notice it. A redesign that is meant to be seen needs the screens
  themselves (R3 onwards), not the colours file.

## SYNC draws a changed Ford screen (2026-11-01)

- Rasmus's photo of the call history after the second visit shows **our R3b screen**: three
  tall rows instead of five, thin chevrons on the scroll buttons instead of Ford's solid
  triangles, and our call icons. So SYNC does not check Ford's Flash files: a changed screen
  (pictures, two numbers in a class, one sprite's layout) loads and runs.
- Rasmus saw it as "no change". The list is a small part of the screen; the frame around it
  (left menu, tabs, top and bottom bars, the glossy buttons) is `AppConsole.swf` and the Phone
  main screen, which load at start-up (R6, R7, R8). Changes inside one list don't show up
  enough to notice. A change he can see needs the frame or a whole screen.

## The restyled frame in the car (2026-11-01, evening)

- `bundle-8fc9` ran; every part verified byte for byte on import: Ford's theme back, then Night
  with borderless buttons, then the restyled frame (`screen-8393`). **SYNC started with the
  changed start-up file**, and every screen in the photos works: Home, Settings, Navigation,
  the call history, the Apps menu, Climate. The first start-up Flash file is proven.
- Rasmus: "home good". Seen in the photos (night, display mode Auto):
  - as intended: flat dark tabs, list rows, setting rows and climate buttons without outlines;
  - **not as intended:** the clock piece and the bottom tabs (Info, Home, Settings) come out
    light blue-grey, the left-hand menu buttons light grey, and on Climate a band across the
    bottom is bright blue with stripes. Measured in one photo: the black background (61,58,57),
    a flat button (74,68,61), the clock piece (139,177,212). Something lightens these pictures
    on the car; being traced in Ford's frame code.

## Next

1. Plan step S2, wallpapers, and a **theme preview on the Mac**: render `Theme.XML` and the
   gradients into mock screens, to choose colours before anything goes to the car.
2. ~~Lighter logger~~: done, the screen is copied every 10 s (sync2-auto-magic 03e2fc5).
3. Find out how SYNC chooses the Ford or the Lincoln skin.
