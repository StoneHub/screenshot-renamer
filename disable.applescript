on run argv
    set targetPath to item 1 of argv
    tell application "System Events"
        repeat with targetAction in (every folder action whose path is targetPath)
            if exists script "Screenshot Renamer.scpt" of targetAction then
                set enabled of script "Screenshot Renamer.scpt" of targetAction to false
            end if
        end repeat
    end tell
end run
