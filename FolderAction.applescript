on adding folder items to watchedFolder after receiving addedItems
    set workerPath to (POSIX path of (path to home folder)) & "Library/Application Support/Screenshot Renamer/renamer.py"
    set commandText to "/usr/bin/python3 " & quoted form of workerPath
    repeat with addedItem in addedItems
        set commandText to commandText & " " & quoted form of (POSIX path of addedItem)
    end repeat
    do shell script commandText & " > /dev/null 2>&1 &"
end adding folder items to
