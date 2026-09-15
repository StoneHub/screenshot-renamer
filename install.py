#!/usr/bin/python3
from pathlib import Path
import os
import fcntl
import json
import runpy
import shutil
import subprocess

root=Path(__file__).resolve().parent
state=Path.home()/'Library/Application Support/Screenshot Renamer'
scripts=Path.home()/'Library/Scripts/Folder Action Scripts'


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
