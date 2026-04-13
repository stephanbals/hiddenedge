@echo off
echo Renaming .gitignore.txt to .gitignore...

if exist ".gitignore.txt" (
    ren ".gitignore.txt" ".gitignore"
    echo Done.
) else (
    echo .gitignore.txt not found.
)

pause