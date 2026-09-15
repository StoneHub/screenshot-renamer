#!/usr/bin/python3
from pathlib import Path
import os
import shutil
import subprocess

root=Path(__file__).resolve().parent
state=Path.home()/'Library/Application Support/Screenshot Renamer'
scripts=Path.home()/'Library/Scripts/Folder Action Scripts'
os.umask(0o077)
state.mkdir(parents=True, exist_ok=True)
scripts.mkdir(parents=True, exist_ok=True)
for name in ['renamer.py','schema.json','disable.applescript']:
    dest=state/name
    if dest.is_symlink(): raise RuntimeError('Refusing symlink: '+str(dest))
    if dest.exists() and dest.read_bytes()!=(root/name).read_bytes():
        shutil.copy2(dest, state/(name+'.previous'))
    shutil.copy2(root/name,dest)
    dest.chmod(0o600)
dest=scripts/'Screenshot Renamer.scpt'
if dest.is_symlink(): raise RuntimeError('Refusing script symlink')
if dest.exists(): shutil.copy2(dest, state/'Screenshot Renamer.previous.scpt')
subprocess.run(['/usr/bin/osacompile','-o',str(dest),str(root/'FolderAction.applescript')],check=True)
subprocess.run(['/usr/bin/osascript',str(root/'enable.applescript'),str(Path.home()/'Desktop')],check=True)
print('Installed Desktop screenshot renamer.')
