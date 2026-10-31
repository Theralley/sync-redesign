# Speed on the map: what SYNC 2 allows (2026-10-31)

Rasmus asked whether the current speed, and if possible the speed limit, can be shown on the
map, and perhaps on other screens. Investigation and sketch only; nothing has gone to the car.

Sketches: [mockups/redesign-nav-speed.png](mockups/redesign-nav-speed.png) (68 km/h on a 70
road) and [mockups/redesign-nav-speed-over.png](mockups/redesign-nav-speed-over.png)
(82 km/h: a thin amber line).

## Where the numbers come from

Found in the code strings of the car's own Flash screens (the drive log's copy of
`\8inchSkins`).

| Number | Source on SYNC 2 | Evidence |
|---|---|---|
| **Speed limit** of the road you are on | Ford's navigation map data (the F10 map), handed to the map screen | `Nav/Map.swf` already has a speed-limit sign: `speedLimitIcon`, `currSpeedLimit`, `m_currSegSpeed` (the current road's limit), `updateSpeedLimitIcon`, `initSpeedLimitIconForRegion`, and unit conversion `DECIMETERS_PER_S_TO_KM_PER_HR`. The same names are in about 38 navigation screens and in `AppConsole.swf` |
| **Current speed** from GPS | SYNC's GPS plugin, data `GPS.GPSTRACKINGDATA` (speed and heading) | `BezelDiagnostics/GPS.swf`, SYNC's hidden GPS diagnostics screen, shows `SPEED` and `HEADING` from it |
| Current speed from the car (CAN) | Not found in the screens' code | Not needed: GPS is enough on the screen |

So **Ford's map can already show the limit** where the map data has one. What is new is the
current speed beside it, and a style that makes the pair readable at a glance.

## What can and cannot change

- **Can:** the Flash layer on top of the map (`Map.swf`, Ford's), the way the Apps menu was
  changed: one class at a time, plus pictures. That is plan phase R5 (navigation overlays).
- **Cannot:** the map drawing itself (the navigation engine, not Flash), the instrument
  cluster, or the car's own speed-limit features.
- **Not known yet:** whether Ford's map shows the limit on this car today (map data and a
  setting may decide it), and exactly how a screen asks the GPS plugin for the speed. Both are
  answered by decompiling `Map.swf` and `GPS.swf` on the Mac (phase R2 tools), before any car
  test.

## Design

- **One small box, bottom left of the map**, where the route card is not, in one row: the
  limit as a Swedish sign (yellow, red ring, black number) and the GPS speed beside it, 32 px
  bold, with "km/h" and "GPS" small after it. 156 x 64 px, about 40% of the first box
  (236 x 104): the map dominates (Rasmus, twice: the box and the warning were too big).
- **Over the limit by more than 3 km/h:** the only mark is a thin amber line under the number;
  the number and the box keep their colours. It never blinks or sounds: the cluster and the car
  already warn, and a flashing screen draws the eyes.
- **No GPS fix** (tunnels, garages): the speed shows "–", never a stale number.
- **No limit in the map data:** the sign is left out, the speed stays.
- GPS speed can read lower than the speedometer, which by law may read high; the label says
  GPS so the two are not compared.

## Other screens

- **Home:** the navigation card could carry a small limit sign. The current speed is not added:
  the cluster in front of the driver shows it with less eye movement.
- **Phone, Media, Climate:** nothing. Adding speed there would invite looking at the centre
  screen for something the cluster already shows.

## Risks

| Risk | Answer |
|---|---|
| Distraction | Only on the map, one small box, no motion, no blinking, nothing to tap |
| Wrong number | GPS lag (about a second) and no fix in tunnels: shown as "–"; labelled GPS |
| Processor | One text field updated once a second; no pictures redrawn |
| `Map.swf` breaking | A navigation screen, not a start-up file (to be confirmed); the change has its own undo stick, and phase R3 proves Ford's files accept changes first |

## Steps

1. On the Mac: decompile `GPS.swf` and `Map.swf`; write down the GPS call and how the speed
   limit reaches `speedLimitIcon`.
2. Render the changed map screen on the Mac (preview tool).
3. After R3 has proven a Ford screen: build the `Map.swf` change and its undo; car test,
   parked first, then a short drive.
