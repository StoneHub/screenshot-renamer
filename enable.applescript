on run argv
    set targetPath to item 1 of argv
    tell application "System Events"
        set matches to every folder action whose path is targetPath
        if (count of matches) is 0 then
            set targetAction to make new folder action with properties {name:"Screenshot destination", path:targetPath, enabled:true}
        else
            set targetAction to item 1 of matches
            set enabled of targetAction to true
        end if
        tell targetAction
            if not (exists script "Screenshot Renamer.scpt") then
                make new script at end of scripts with properties {name:"Screenshot Renamer.scpt"}
            end if
            set enabled of script "Screenshot Renamer.scpt" to true
        end tell
        set folder actions enabled to true
        return {folder actions enabled, enabled of targetAction, name of every script of targetAction}
    end tell
end run
