# UX review of the redesign, from the driver's seat (2026-10-31)

A review of [REDESIGN-PLAN.md](REDESIGN-PLAN.md) and its sketches against how SYNC 2 is used
while driving, with the car's real climate screen and the first tile menu photographed in the
car. The sketches were redrawn after it: [mockups/redesign-overview.png](mockups/redesign-overview.png).

## Rules for every screen

| Rule | Value | Why |
|---|---|---|
| Glance | One main value per card, at least 30 px bold; at most four cards a screen | Readable in under a second, at about 70 cm |
| Contrast | Main text at least 7:1, secondary at least 4.5:1, in day and night | Sunlight and night glare |
| Touch targets | At least 80 px high (about 18 mm on the 8" screen) | Enough with gloves and on a bumpy road |
| Text | Sentence case, no capitals for labels, Swedish first | Capitals read slower; the car is Swedish |
| Icons | One family (`tools/icons.py`): the same 2-unit line on a 24-unit grid, rounded ends | Tiles, area bar and climate read as one set |
| Colour | One accent per area, on a 6 px stripe or a 3 px line; never colour alone for a state | States also show as a lamp, a label or a level |
| Night | The same layout; accents at 78%, text slightly dimmer | Less glare, nothing moves |

Measured on the sketches (WCAG contrast):

| | Day | Night |
|---|---|---|
| Main text on a card | 14.9:1 | 11.4:1 |
| Secondary text on a card | 7.4:1 | 5.8:1 |
| Main text on a button | 12.2:1 | 9.3:1 |
| Secondary text on a button | 6.1:1 | 4.8:1 |

## Findings and what changed

1. **Climate lost controls (serious).** The first climate sketch had eight buttons; the car's
   real climate screen has 21. **Changed:** the climate sketch now keeps every control in
   Ford's own place, only restyled:
   - top: driver temperature − / + , power (with Auto), passenger temperature − / +;
   - middle: driver seat heat, Min temp, air to the windscreen / face / feet, fan + / level /
     −, Dual, passenger seat heat;
   - bottom, in Ford's order: windscreen defrost, Max defrost, rear window, Auto, A/C,
     Max A/C, recirculation.

   Each control that can be on gets a lamp, like Ford's amber mark. **Rule for the plan:**
   climate is restyled in place, never rearranged; the hand must find defrost blind. The three
   air buttons and fan + / − stay about 44 px high, as Ford's, because making them bigger
   would move them. The physical buttons under the screen (AUTO, MAX defrost, A/C,
   recirculation) remain the fallback with gloves.
2. **Touch targets were too small for gloves.** The plan said 64 px; now 80 px, and the area
   bar is 64 px high with icons.
3. **Labels in capitals.** "NOW PLAYING", "NAVIGATION" and the like became sentence case.
4. **No icon family.** Tiles, area bar and climate used unrelated symbols. **Changed:** one
   family of 26 icons. Its first fan looked like a swastika (four hooked blades); it now has
   three rounded blades.
5. **English text on a Swedish car.** SYNC itself already runs in Swedish. **Changed:**
   sketches and tiles are Swedish by default, English on request (`--lang en`).
6. **Media and Phone** got bigger rows (80 px) and fewer items; the source list shows four
   sources, each 76 px high.
7. **The climate tab shows the set temperature** (Rasmus): the driver's, and with Dual on also
   the passenger's, under the icon in place of the word, with a thin divider: "19,0°" or
   "19,0° | 21,5°". Ford's climate data has them (`Climate.TEMPDRIVERSET`,
   `Climate.TEMPCODRIVERSET`, `Climate.DUALBUTTONSTATE`); Ford's own bottom bar
   (`Climate/ClimateConsoleObject.swf`) already shows both with a divider. That part of the bar
   loads with the frame at start-up, so it belongs to phase R8.
8. **Swedish numbers:** temperatures use a decimal comma in Swedish (19,0°), a point in English.
9. **The over-limit mark on the map was too loud** (Rasmus): now only the speed box's edge and a
   short line under the number turn amber; the number keeps its colour ([SPEED.md](SPEED.md)).

## Icons: possible on SYNC 2?

**Yes, for everything we draw ourselves.** The Apps menu tiles are PNG pictures the menu loads
at run time; the car showed them correctly. The area bar, Home, Media and Phone icons would
be pictures inside Ford's Flash screens: possible once phase R3 proves Ford's files accept
changes (pictures first, without code). SYNC's own PNG files are all full colour (RGB or
RGBA), so our pictures stay full colour too: an 8-bit PNG has never been shown on this
player.

## Language: what SYNC 2 allows

| Part | Where the words come from | Swedish? |
|---|---|---|
| SYNC's own menus and messages | SYNC's built-in language setting (Settings, System, Language; `SystemApp.swf`), texts from `\DataManager` | **Yes, already active** (the photos show "<phone> ansluten") |
| Our tiles and our future screens | Pictures and texts we make | **Yes:** Swedish by default, English with `--lang en`, chosen when the job is built |
| Following SYNC's language automatically | Ford's screens read it with `getLocaleInfo(LOCALE_ILANGUAGE)` | Possible later: our code could pick the Swedish or English tiles itself once we know how that call is made (a step for R2's decompiling) |
| AutoKit's own screens (before CarPlay starts) | `lang.zip` in AutoKit's folder: 12 files in UTF-16, 126 lines of `number=text`; no Swedish | **Possible:** a Swedish translation in place of `English.lng` inside `lang.zip`, as a job with an undo. Not built yet |
| CarPlay and Android Auto | The phone | Follows the phone's language (Swedish) |

## Performance: before and after

Measured on the Mac from the car's files and the job folders.

| Item | Before | After | Note |
|---|---|---|---|
| Tile pictures (10 PNG) | 110,721 bytes | 79,231 bytes (−28%) | The same full-colour format, fewer colours; Swedish |
| Apps menu (SyncApps.swf) | 20,654 bytes | 23,575 bytes (+2.9 KB) | Our tile code; loads only when Apps opens, never at start-up |
| Theme (Theme.XML + four gradients) | 1,537,691 bytes | 1,537,691 bytes | Ford's format fixes the size; cannot shrink |
| Drive logger's own processor use | about 13% | about 1.3% (estimated) | The screen is copied every 10 s instead of every second |
| s2am's old job folders on the car | 2.2 MB in 68 files (drive log), more since | 0 after `s2am job cleanup` | **Our own bloat:** each job leaves MortScript behind. The cleanup job is built and tested on the Mac, not yet run |
| A job stick's payload | 0.18 MB (undo) to 1.7 MB (theme) | | About 0.16 MB of every job is MortScript and the runner |

**What runs at start-up:** none of our changes adds anything. The theme files are read at start
as before (same size); the Apps menu, the tiles and the logger only load when used.

**Not ours to remove:** Ford's plugins in `\windows`, the Lincoln skin (26 MB, Ford's) and
everything in `\Windows` stay. SyncExtPack candidates, to decide with Rasmus:
- `AutoKit\MSYH.ttf`, 7.7 MB: a Chinese font. Remove it only after testing that AutoKit still
  draws its text (when the adapter is here), with an undo.
- The Video Player, 11.7 MB: a feature, not bloat; removable with `s2am job remove`.

**Time:** start-up and screen response cannot be measured on the Mac, and SYNC's Flash layer
cannot be captured. In the car:
- start-up: a stopwatch from the key to the Home screen, three times;
- per screen: the iPhone's slow-motion video (240 frames a second) of a tap and the new screen,
  counting frames;
- processor: the drive logger before and after a change (`Desktop.exe` used about 52% at rest
  on 2026-10-31).
