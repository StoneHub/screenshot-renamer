# Screenshot Renamer

An on-demand macOS 27 Folder Action that gives newly saved Desktop screenshots descriptive names using Apple's on-device Foundation Model. No menu-bar icon, login app, polling loop, HTTP server, or custom model download.

Example: `2026-09-15 14.35.20 — Workshop Planner Weekend Checklist.png`

## Use

Take a screenshot using your normal Mac hotkeys and save it to Desktop. After the file finishes saving, the helper processes the image, renames it once, and exits. App names are inferred only from visible image content. No foreground-app inspection. Existing screenshots are not scanned or renamed.

Only files carrying Apple's `kMDItemIsScreenCapture` metadata are eligible. Screenshots copied only to the clipboard, saved elsewhere, or stripped of that metadata are not processed. Other Desktop additions can briefly launch the helper; they do not cause model inference. Failed/refused/timed-out generations leave the original filename intact. Apple manages model availability and memory; the helper does not control system model residency.

Requirements: macOS 27, `/usr/bin/fm` with image input, Apple Intelligence enabled and model ready, `/usr/bin/python3` (provided by the installed developer tools on this Mac), and enabled Folder Actions. The script waits for a stable file, serializes overlapping requests, uses an explicit system model with no cloud fallback, and has a 45-second model timeout.

## Install

From this directory:

```sh
/usr/bin/python3 install.py
```

The installer copies the worker and schema to `~/Library/Application Support/Screenshot Renamer`, compiles `Screenshot Renamer.scpt` into `~/Library/Scripts/Folder Action Scripts`, and attaches that script to Desktop using System Events. It enables Folder Actions globally; existing unrelated scripts are preserved. macOS may request Automation or Desktop access. On this installation no existing Folder Actions were registered and the global switch was initially off.

## Undo the latest rename

```sh
/usr/bin/python3 "$HOME/Library/Application Support/Screenshot Renamer/renamer.py" --undo
```

Undo refuses to overwrite an existing original filename or touch a file whose identity/content metadata has changed. It retains the last 200 rename records. Re-running undo walks backwards through them. A screenshot restored by undo is not renamed again.

## Turn it off

```sh
osascript "$HOME/Library/Application Support/Screenshot Renamer/disable.applescript" "$HOME/Desktop"
```

This disables only this script and leaves any unrelated Folder Actions alone. No worker runs between events. An already-running request may finish. Installed files can stay for later re-enabling.

## Privacy and reliability

Only the image is passed to the local system model. No transcript, image copies, app activity history, or model stderr is stored. Local `history.json` stores the old/new paths and file identity needed for undo; filenames may be private. `status.log` contains timestamps and status codes only. State files are account-private. Names are sanitized and Darwin's exclusive atomic rename prevents overwrites. Repeated events are deduplicated by device/inode. The latest 200 identities are retained; only files less than five minutes old are eligible.

Folder Actions are macOS's trigger mechanism, not a guaranteed screenshot event API. The helper only receives added files and does not scan Desktop on startup. A cancelled/incomplete save or delayed/missed event can leave the standard name. A user rename during generation prevents the old path from being renamed. Model output is a fallible description; no screenshot text is executed.

## Tests

```sh
/usr/bin/python3 -m unittest discover -s . -p 'test_*.py'
```

Coverage: bytes/metadata preservation and undo, repeated events, collision handling, ordinary-image filtering, model failure, symlinks/outside paths, in-flight changes, safe undo and filename sanitization.
