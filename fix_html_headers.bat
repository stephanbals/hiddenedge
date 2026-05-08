@echo off
setlocal enabledelayedexpansion

echo Cleaning HTML files...

for /r %%f in (*.html) do (
    echo Cleaning: %%f

    findstr /v "^REM" "%%f" > "%%f.tmp"
    move /y "%%f.tmp" "%%f" >nul
)

echo Done.
pause