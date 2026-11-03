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

## The fixed frame in the car (2026-11-02, morning)

- **The cause of the third visit's look was ours.** `swf_bitmaps` wrote 0 into the first byte of
  every pixel of a picture without alpha (DefineBitsLossless, format 5). The format calls the
  byte reserved, but every one of Ford's 313 such pictures holds 0xFF there and the car's player
  reads it as opacity, so our 76 button strips and four corner bars drew transparent: black
  buttons with only an outline, and the theme's glow showing through on Climate. Ford's code
  does not tint the frame: no colour transform, blend or filter reaches it (the theme's
  colouring touches dialogs and indicator glows only). Fixed (47ad11d).
- `bundle-8d9d` ran at 07:39; every part verified byte for byte (Settings > Display with the
  Auto dim offset from -10, Ford's frame back, the fixed frame). SyncExtPack restarts SYNC after
  an install, so the photos from 07:42 show the fixed frame: the buttons and bars are solid.
- **The screen shows dark greys far lighter than their numbers.** Measured in a daylight photo of
  the call history: the black background (39-46), our bars (23,26,32) about (140,158,188), our
  buttons (38,42,51) about (207,217,218), Ford's own menu buttons (49,49,49) about
  (228,224,203). Ford's frame is drawn from the same dark greys (the clock piece is
  (36,36,36), the top bar 62 fading to 28) and photographs silver (2026-10-30). Near black,
  each step of the input shows as roughly 4.5 steps in the photo. How much of it is the phone
  camera and how much the screen is asked; `restyle_frame.py --palette deep` keeps the same
  design near black (bars 6, buttons 13).
- On the Phone screens the top-left area still shows a striped amber glow (being traced).
- Rasmus: "it still feels old/like the old system BUT with some new skins": the next steps are
  layouts, not pictures (Home's cards, then the frame's bars).

## Home as cards in the car (2026-11-02, afternoon)

- `bundle-6bce` ran at about 16:30; every part verified byte for byte on import (2026-11-03):
  the deep theme without glow, the straight deep frame, Home as four cards.
- Rasmus, from the photos: "still very as the old. looks shit. not even align." What they show:
  - **Home's cards were staggered.** Each card was sized to Ford's content, so the left column
    split at y 214/224 and the right at 230/240. Our own preview already showed it; since then
    every preview is measured against the grid before anything goes to the car.
  - The stripes were the left edge of a rounded rectangle, so they curved like brackets, and
    the coloured lines under the corner tabs ended at random places.
  - Everything inside the cards was still Ford's: the compass ball, the 2x3 preset grid with
    outlines, the seat buttons low in an otherwise empty climate card.
  - The side menus (Settings, Info) still looked glossy. Their rows are pictures in `Menu.swf`
    and `Info.swf`, and the outline is drawn by code in the theme's System colour; neither is
    one of the frame's strips.
- **On the photos Home showed no climate temperatures.** The class makes the two fields visible
  but fills them only from the set-point messages, which had not come (the climate was off; see
  the next section). Only the seat buttons showed.
- **On Home the bars repeat the cards.** The phone label shows a Home-only view ("Telefon"), the
  navigation label the area's name, the media label "Underhållning" and the climate label
  "Klimat".
- Black shows as navy at night, and a few levels near black are clearly visible: cards (6,7,9)
  on (0,0,0) read as two tones. The round blobs in the night photos are fingerprints on the glass.
- Two earlier readings were the photo's keystone, not the screen: the selected bottom button
  does not stand 9 px higher, and the bottom-right line does not sit 8 px above the left one
  (renders of the real sprites at their runtime frames).
- The dark outline round all text is also on our own Apps menu, and no Ford code or placement
  uses a filter: the player or the camera, not a target.

## Version 2 in the car (2026-11-03, midday)

- `bundle-6166` ran at about 12:50; all 18 parts verified byte for byte on import: 14 of Ford's
  start-up files changed at once (the frame, Home and its four corners, the five console
  objects, `Media.swf`, the two side menus) and SYNC started normally.
- The photos show the grid, the headings, the black bars with only the clock on Home, the labels
  back on every other screen, and flat side menus.
- **A clip scaled to zero does not stay hidden if the theme sizes it.** The presets' outline clips
  were placed at scale 0; the theme's code sets their width and height when it draws the
  outline, so they came back, at Ford's place, not round our chips.
- **Home's climate card does show the temperatures** when the climate is on: the set-point
  messages arrive then (on the fifth visit's photos the climate was off). A stray "Klimat" text
  appeared beside the seat buttons.
- Only the system colour's outline is borderless in our theme; buttons in the areas' own screens
  (climate, radio, phone) keep Ford's light grey edge (the areas' dayColor 0x666666).

## Next

1. Plan step S2, wallpapers, and a **theme preview on the Mac**: render `Theme.XML` and the
   gradients into mock screens, to choose colours before anything goes to the car.
2. ~~Lighter logger~~: done, the screen is copied every 10 s (sync2-auto-magic 03e2fc5).
3. Find out how SYNC chooses the Ford or the Lincoln skin.
