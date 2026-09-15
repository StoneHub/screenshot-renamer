#!/usr/bin/python3
"""Disable the trigger and remove Screenshot Renamer's installed files."""
from pathlib import Path
import fcntl
import os
import runpy
import shutil
import subprocess


def uninstall(home=None, run=subprocess.run):
    home = Path.home() if home is None else Path(home)
    state = home / 'Library/Application Support/Screenshot Renamer'
    script = home / 'Library/Scripts/Folder Action Scripts/Screenshot Renamer.scpt'
    if state.is_symlink() or script.is_symlink():
        raise RuntimeError('Refusing an unexpected symlink.')
    if not state.exists() and not script.exists():
        print('Screenshot Renamer is already uninstalled.')
        return None
    if not (state / 'disable.applescript').is_file():
        raise RuntimeError('Missing disable script; no files were moved.')
    # Abort before moving anything if macOS cannot disable the event handler.
    config = runpy.run_path(state / 'config.py')
    run(['/usr/bin/osascript', str(state / 'disable.applescript'), config['SCREENSHOT_DIRECTORY']], check=True)
    with (state / 'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if script.exists():
            script.unlink()
        shutil.rmtree(state)
    print('Uninstalled Screenshot Renamer. Screenshots were not changed.')


if __name__ == '__main__':
    os.umask(0o077)
    uninstall()
