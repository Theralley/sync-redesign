# Spotify on SYNC 2: which way (2026-10-31)

Rasmus: could we make something to install on SYNC that handles Spotify: song, artist, cover,
and play, pause, next? Investigation only; nothing has gone to the car. Checked against the car's
own files (the drive log's copy of `\8inchSkins` and the list of SYNC's system modules).

| Way | Can it be done? | What it takes | Risks | Work |
|---|---|---|---|---|
| **(a) AppLink / SmartDeviceLink** (Spotify had an AppLink app) | **No** | AppLink was on SYNC 1 and SYNC 3. This SYNC 2 has none of it: no AppLink or SmartDeviceLink in its screens or system modules | | |
| **(b) Our own screen for Ford's Bluetooth audio** | **Yes**, without a cover | SYNC already receives song and artist and sends play, pause and next over Bluetooth (AVRCP), for any app on the phone, Spotify included; Ford's media screen shows them. Our screen reads the same data from Ford's media plugin, by the route the Apps menu proved | Low, if opened from the Apps menu (not at start-up); its own undo | Medium: one Flash screen, in our job chain |
| **(c) Spotify's Web API, from the phone or from SYNC** | **Maybe, not worth it** | A link: SYNC has Wi-Fi (`wzcsvc`) and Bluetooth networking (`btpan`), so it could reach the internet through the phone's hotspot. Then our own native SYNC program with HTTPS, a Spotify developer app, a Spotify login token stored on the car, and Premium for play and pause | A login token on the car; whether SYNC's old TLS (CE 6, OpenSSL of its time) still meets Spotify's servers is unknown; a hotspot on every drive; a second or so of delay | High, for a cover and the same buttons |
| **(d) CarPlay through the AutoKit adapter** (already ordered) | **Yes**, all of it | The adapter and SyncExtPack's AutoKit plugin, already on the car. Spotify's own CarPlay app: song, artist, cover, browsing, Siri | To test when it arrives: the steering-wheel buttons, the night look, and calls over CarPlay. (MirrorLink: not on SYNC 2) | None beyond the adapter test |

Covers: SYNC 2's Bluetooth has no imaging module (BIP), so (b) has no cover; over USB, SYNC's
iPod mode plays the phone's own music library, not Spotify ([NIGHT.md](NIGHT.md)).

## Recommendation

**(d) for Spotify itself, and (b) for our screens.** When the adapter comes, Spotify runs in
CarPlay with everything, written and kept up to date by Spotify. Without CarPlay, or in the night
screen, our Media screen shows song and artist and has play, pause and next from Ford's own
Bluetooth data, which works for every music app, not only Spotify. No Spotify-only program on the
car: (a) does not exist on SYNC 2, and (c) puts a login on the car for little gain.

## Steps

1. When the adapter arrives: Spotify in CarPlay, the steering-wheel buttons, a call over CarPlay.
2. The Media screen of the redesign (phase R4) with Ford's Bluetooth data; the night screen
   shows the same song and artist ([NIGHT.md](NIGHT.md)).
