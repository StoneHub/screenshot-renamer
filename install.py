#!/usr/bin/python3
from pathlib import Path
import os
import fcntl
import json
import platform
import runpy
import shutil
import subprocess
import sys

root=Path(__file__).resolve().parent
state=Path.home()/'Library/Application Support/Screenshot Renamer'
scripts=Path.home()/'Library/Scripts/Folder Action Scripts'
PERMISSIONS=['macOS will ask to allow Terminal (or whatever runs install.py) to control System Events, and later to access the screenshot folder.',
             'Allow both, or the script cannot be attached and screenshots cannot be renamed.']


def screenshot_directory(configured, run=subprocess.run):
    if configured is not None:
        directory=Path(configured).expanduser()
    else:
        result=run(['/usr/bin/defaults','read','com.apple.screencapture','location'],
                   text=True, capture_output=True)
        directory=Path(result.stdout.strip()).expanduser() if result.returncode == 0 else Path.home()/'Desktop'
    directory=directory.resolve()
    if not directory.is_dir():
        raise RuntimeError('Screenshot destination is not a directory: '+str(directory))
    return directory


def preflight(run=subprocess.run, which=shutil.which, fm=Path('/usr/bin/fm'), version=None):
    """Refuse to install a trigger that can never rename anything, and say why in one line each."""
    problems=[]
    if not fm.exists():
        problems.append('/usr/bin/fm is missing. Apple ships it with macOS 27; this Mac runs '
                        +(version or platform.mac_ver()[0])+'.')
    else:
        available=run([str(fm),'available'],text=True,capture_output=True)
        if available.returncode != 0:
            problems.append('fm available failed: '+(available.stderr or available.stdout).strip()
                            +' Enable Apple Intelligence in System Settings and wait for the model to download.')
    if not Path('/usr/bin/osacompile').exists() or not Path('/usr/bin/osascript').exists():
        problems.append('osacompile or osascript is missing.')
    return problems


def announce():
    for line in PERMISSIONS: print(line)


def install():
    configured=runpy.run_path(root/'config.py')['SCREENSHOT_DIRECTORY']
    destination=screenshot_directory(configured)
    os.umask(0o077)
    state.mkdir(parents=True, exist_ok=True)
    scripts.mkdir(parents=True, exist_ok=True)
    with (state/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Upgrade the early prototype without retaining any filename history.
        legacy=state/'history.json'
        processed=state/'processed.json'
        if legacy.exists():
            entries=json.loads(processed.read_text()) if processed.exists() else []
            entries.extend(row['identity'] for row in json.loads(legacy.read_text()))
            processed.write_text(json.dumps(entries[-200:])+'\n')
            processed.chmod(0o600)
        for name in ['renamer.py','schema.json','disable.applescript','uninstall.py']:
            dest=state/name
            if dest.is_symlink(): raise RuntimeError('Refusing symlink: '+str(dest))
            shutil.copy2(root/name,dest)
            dest.chmod(0o600)
        installed_config=state/'config.py'
        if installed_config.is_symlink(): raise RuntimeError('Refusing symlink: '+str(installed_config))
        installed_config.write_text('SCREENSHOT_DIRECTORY = '+repr(str(destination))+'\n')
        installed_config.chmod(0o600)
        for name in ['history.json','history.tmp','renamer.py.previous','schema.json.previous',
                     'disable.applescript.previous','uninstall.py.previous','Screenshot Renamer.previous.scpt']:
            (state/name).unlink(missing_ok=True)
    dest=scripts/'Screenshot Renamer.scpt'
    if dest.is_symlink(): raise RuntimeError('Refusing script symlink')
    subprocess.run(['/usr/bin/osacompile','-o',str(dest),str(root/'FolderAction.applescript')],check=True)
    subprocess.run(['/usr/bin/osascript',str(root/'enable.applescript'),str(destination)],check=True)
    print('Installed screenshot renamer for '+str(destination)+'.')


if __name__ == '__main__':
    announce()
    problems=preflight()
    if problems and '--force' not in sys.argv:
        for line in problems: print('Cannot install: '+line)
        print('Fix the above and run install.py again, or pass --force to install anyway.')
        raise SystemExit(1)
    install()
