#!/usr/bin/python3
"""Report whether Screenshot Renamer can run here and whether it is installed and switched on. Changes nothing."""
from pathlib import Path
import platform
import runpy
import subprocess
import sys
from install import preflight

# Asks System Events about the folder action without creating or enabling anything.
STATUS_SCRIPT='''on run argv
    tell application "System Events"
        set matches to every folder action whose path is (item 1 of argv)
        if (count of matches) is 0 then return "unattached"
        set targetAction to item 1 of matches
        set scriptState to "script missing"
        if exists script "Screenshot Renamer.scpt" of targetAction then
            set scriptState to (enabled of script "Screenshot Renamer.scpt" of targetAction) as text
        end if
        return ((folder actions enabled) as text) & "," & ((enabled of targetAction) as text) & "," & scriptState
    end tell
end run
'''


def destination(state, home, run):
    """Installed config first, then the macOS screencapture setting, then Desktop."""
    if (state/'config.py').is_file():
        return Path(runpy.run_path(state/'config.py')['SCREENSHOT_DIRECTORY']).expanduser()
    result=run(['/usr/bin/defaults','read','com.apple.screencapture','location'],text=True,capture_output=True)
    return Path(result.stdout.strip()).expanduser() if result.returncode == 0 and result.stdout.strip() else home/'Desktop'


def folder_action(path, run):
    """Return (line, healthy) from System Events for the folder at path."""
    result=run(['/usr/bin/osascript','-',str(path)],input=STATUS_SCRIPT,text=True,capture_output=True)
    if result.returncode != 0:
        return 'Folder action: System Events query failed: '+(result.stderr or result.stdout).strip(), False
    answer=result.stdout.strip()
    if answer == 'unattached':
        return 'Folder action: not attached to '+str(path), False
    switch,action,script=(answer.split(',')+['?','?','?'])[:3]
    line=('Folder action: attached to '+str(path)+'; action enabled '+action
          +'; script enabled '+script+'; Folder Actions switch '+switch)
    return line, (switch,action,script) == ('true','true','true')


def doctor(home=None, run=subprocess.run, fm=Path('/usr/bin/fm'), version=None, out=sys.stdout):
    home=Path.home() if home is None else Path(home)
    state=home/'Library/Application Support/Screenshot Renamer'
    script=home/'Library/Scripts/Folder Action Scripts/Screenshot Renamer.scpt'
    version=version or platform.mac_ver()[0]
    lines=[]
    healthy=True
    problems=preflight(run=run,fm=fm,version=version)
    lines.append('macOS '+version+': '+('/usr/bin/fm present, fm available ok' if not problems else ' '.join(problems)))
    healthy&=not problems
    folder=destination(state,home,run)
    lines.append('Screenshot folder: '+str(folder)+(' exists' if folder.is_dir() else ' missing'))
    healthy&=folder.is_dir()
    lines.append('Compiled script: '+str(script)+(' exists' if script.is_file() else ' missing'))
    healthy&=script.is_file()
    if script.is_file():
        line,ok=folder_action(folder,run)
        lines.append(line)
        healthy&=ok
    else:
        lines.append('Folder action: not checked because the compiled script is missing')
    log=state/'status.log'
    if log.is_file():
        tail=log.read_text().splitlines()[-5:]
        lines.append('status.log, last '+str(len(tail))+' lines:')
        lines.extend('  '+row for row in tail)
    else:
        lines.append('status.log: none at '+str(log))
    lines.append('Result: '+('healthy' if healthy else 'not working; see above'))
    for line in lines: print(line,file=out)
    return 0 if healthy else 1


if __name__ == '__main__':
    raise SystemExit(doctor())
