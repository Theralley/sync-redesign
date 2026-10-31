# Night screen: what SYNC 2 allows (2026-10-31)

Rasmus: the screen is far too bright at night. Could there be a night mode that shows only the
clock and a little music information? Investigation and sketch only; nothing has gone to the car.

Sketches: [mockups/redesign-night-minimal.png](mockups/redesign-night-minimal.png) (clock, song,
the next turn when a route is on) and [mockups/redesign-night-cover.png](mockups/redesign-night-cover.png)
(the same with an album cover, only if the car ever gets one; see below).

Found in the code of the car's own Flash screens (the drive log's copy of `\8inchSkins`,
decompiled on the Mac; the decompiled code stays private).

## What Ford already has

**Settings, Display** (`Menu/Display/Display.swf`):

| Setting | Values |
|---|---|
| Mode | Auto, Day, Night, Off |
| Brightness | 0 to 14 |
| Auto dim | On, Off |
| Auto dim offset | −5 to +5 |

**Off** is Ford's screen-off (`BackLight` in the frame, `AppConsole.swf`). It switches the
backlight off (`SetBacklight(0)`) and lays a black layer over everything; a touch on that layer
switches it back on. It already gives way when it must:

| Event | What Ford's code does |
|---|---|
| Reverse gear | `DisplayRVC`: screen on for the camera, and off again after it |
| Front camera, park assist | `DisplayFVC`, `checkDisplayForSAPP`, `LoadDriverAssistInternal`: screen on |
| Incoming call, any system message | `syncDialogToTop` calls `DisplayOn` for every system dialog that comes to the top; the incoming call is one (`ShowIncomingCallDialog`) |
| Key off | `HandleKeyOff`: screen on |

**Day and night:** the frame gets `UPDATEDAYNIGHTMODE` from SYNC and stores it as
`ApplicationSettings.DayNightLevel` (1 day, 2 night); every screen then switches its colours. In
Auto this follows the car's own light signal (headlamps or the light sensor; which of the two is
decided in SYNC's native part and is not visible in Flash).

**Try tonight, with nothing changed:** Display, Mode **Auto**, **Auto dim On**, **Auto dim
offset −5**, Brightness low. That is the darkest Ford allows with the screen on. Or **Off**:
dark, a touch wakes it, and the camera and calls take over as in the table.

## The night screen

A third state next to Ford's on and off: the backlight stays on at Ford's night level, and
instead of the black layer comes our dark layer with only:

- the clock, large, in dim grey;
- the song and the artist, small;
- the next turn, only while a route is on;
- nothing to tap except the whole screen: a touch anywhere brings back the full screen.

Measured on the sketches: the night screen gives off **13% of the light of the night Home
screen** at the same backlight (the mean light of the pixels; an LCD also lets a little light
through black, so the real figure is somewhat higher).

| Question | Answer |
|---|---|
| On by itself with the lights? | **Yes.** It follows Ford's day and night signal (`DayNightLevel`), so it comes with the headlamps or the light sensor, as Ford's own night colours do. After a set time without a touch (say 30 s) at night, the screen goes to the night screen |
| On by time as a fallback? | **Yes**, in our code: when the display mode is fixed to Day, a time window (for example 21:00 to 06:00) from SYNC's clock |
| Below Ford's lowest brightness? | **Partly proven, partly to test.** The night screen itself cuts the light to about an eighth without touching the backlight. Whether the backlight goes below Ford's 0 is decided by SYNC's native display plugin (`SetBrightness`): a car test passes values below 0 and reads back what the plugin kept. The undo is Ford's own brightness slider |
| Wake with a touch? | **Yes**, the same way as Ford's Off: the layer takes the touch |
| Calls and the reversing camera? | **Always take over.** The night screen is built into Ford's `BackLight`, so every case in the table above ends it the same way it ends Ford's Off. Car test: reverse, and a call, each with the night screen up |

**Where it lives:** in the frame (`AppConsole.swf`, `BackLight`), which loads at start-up: plan
phase R8, the highest risk. A first, safer step uses the proven Apps menu route: a "Night" tile
that opens the night screen by hand, to test how it looks and how the camera and calls behave
over it, before anything at start-up changes.

## Album covers over Bluetooth

| Part | Finding |
|---|---|
| Ford's media screen | Has a place for the cover and even a Bluetooth case (`MediaPlayer.swf`: `GetAlbumArt`, `ShowAlbumArt("BTStereo", url)`); it shows whatever picture SYNC's native media service hands it |
| SYNC's Bluetooth stack | Modules for stereo audio and remote control (A2DP, AVRCP: `bta2dp`, `btavctp`, `btavdtp`, `btavsvc`), calls (HFP), contacts (PBAP), file push (OPP) and OBEX. **No imaging module (BIP)**, which is how AVRCP 1.6 carries covers |
| So | **Very likely no covers over Bluetooth** on this SYNC 2: the media screen falls back to Ford's Bluetooth picture. The night screen can show a cover only where Ford's screen does |
| Test, nothing changed | Play Spotify over Bluetooth (not through CarPlay), open Ford's Media screen. A cover means SYNC gets one, and the night screen can use the same picture; Ford's plain Bluetooth picture means no |
| With CarPlay | The phone draws the covers inside CarPlay itself; while CarPlay fills the screen, our night screen is not shown |

## Steps

1. Tonight, nothing changed: Ford's Auto dim and Off (above); the Bluetooth cover test.
2. On the Mac: decompile the rest of `BackLight` and the day and night path; render the night
   layer in the preview tool.
3. With Rasmus's go: the "Night" tile in the Apps menu (manual, with its undo), car test:
   look, a touch, reverse, a call, and the brightness test below 0.
4. After R3 has proven a Ford screen and R6 the start-up rehearsal: the automatic night screen
   in the frame (R8), with its undo stick.
