@echo off
setlocal enabledelayedexpansion

echo Cleaning Python files...

for /r %%f in (*.py) do (
    findstr /v "^REM" "%%f" > "%%f.tmp"
    move /y "%%f.tmp" "%%f" >nul
)

echo Done.
pause