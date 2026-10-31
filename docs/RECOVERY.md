# How to undo a change, if something goes wrong

Every change this project makes to the car comes with an **undo stick**, built on the Mac
at the same time as the change and kept in the car. Use the first step that works.

## 1. The undo stick (the normal way)

Every change job backs up the files it replaces on the car
(`\SyncExtendedPack\_s2am\backup\<job>`) and copies that backup onto the change stick,
where the Mac checks it. The undo stick carries the original files itself, checked on the Mac
against what the change replaced, so it works even if the backup on the car is damaged.

```sh
python3 -m s2am job theme --restore <change job> --serial YOURSERIAL   # build it with the change
python3 -m s2am stick prepare /Volumes/<OTHER STICK> --job <the job folder it prints>
```

In the car: insert the undo stick, wait for "Install successfully completed". SYNC restarts
with the old files. Back on the Mac, `s2am stick import` checks every restored file byte
for byte (`verified: the original theme is back`).

- The undo stick is safe to insert at any time. If the change never ran, it puts the same
  original files back, which changes nothing.
- Packs only work inside their key window (the current one ends 2026-11-17 09:35 UTC).
  After that, build the undo stick again; the backup on the car stays where it is.

## 2. If the change stick stopped half-way

The change job checks every file's size after copying. If one did not copy whole, it copies
the backup back and reports `copy-failed`; that copy is not checked, so use the undo stick
(step 1) as well. A change job that was cut short (power off) refuses to run a second time,
so its backup is never overwritten: use the undo stick.

## 3. If SYNC is stuck or the screen freezes

- **Soft reset:** car in Park, hold the **power/volume knob and Seek-Up (⏭)** for about
  10 seconds until the screen goes black. Nothing is uninstalled.
- If that does not help: **switch the car off and open and close the driver's door**, then
  start again. This brought SYNC back every time so far.
- Then use the undo stick (step 1).

## 4. If the screen works but the undo stick will not run

Open **Total Commander** from the Apps menu and copy the files back by hand, from
`\SyncExtendedPack\_s2am\backup\<job>\` to where they came from (for a theme:
`\8inchSkins\Ford\Sync\Themes\`). The change stick also holds a copy of the originals in
`s2am\reports\<job>\backup\`.

## 5. If SYNC's screen does not start at all

Not tested yet, and the reason no change touches a start-up file until steps 1-2 have
worked:

- Insert the undo stick anyway and wait two minutes: SyncExtPack's install service runs
  apart from SYNC's screens, so it may still apply it. Then do a soft reset.
- **Last resort:** reinstall SYNC 3.10 from USB with SyncExtPack's
  [firmware guide](https://github.com/chr0m1ng/syncextpack/blob/main/FIRMWARE_INSTALLATION.md).
  It puts back all of Ford's files and removes SyncExtPack, so its first install has to be
  done again.

## What each change touches

| Change | Files on the car | Shown at start-up? | Undo |
|---|---|---|---|
| Colours (`s2am job theme`) | `\8inchSkins\Ford\Sync\Themes\` Theme.XML and four gradient BMPs | Yes, read when SYNC starts | `theme --restore <job>` |
| Wallpaper (SYNC's own editor) | `\8inchSkins\Ford\Sync\Apps\Home\Wallpapers\` | Yes | Pick another wallpaper in Settings |
| Apps menu (planned) | `\8inchSkins\Ford\Sync\Apps\Info\SyncApps\` | No, only when Apps opens | Restore job (to be built with it) |
