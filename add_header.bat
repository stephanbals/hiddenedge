@echo off
setlocal enabledelayedexpansion

REM ================================
REM CONFIG — EDIT THIS HEADER
REM ================================

set HEADER=REM =========================================
set HEADER2=REM HiddenEdge / SB3PM Advisory ^& Services Ltd
set HEADER3=REM Author: Stephan Bals
set HEADER4=REM © 2026 SB3PM Advisory ^& Services Ltd
set HEADER5=REM This code is proprietary and confidential.
set HEADER6=REM Unauthorized use, distribution, or replication is prohibited.
set HEADER7=REM =========================================

echo.
echo Adding headers to files...
echo.

REM ================================
REM PROCESS FILES
REM ================================

for /r %%f in (*.py *.js *.html *.css *.txt) do (

    REM Skip this script itself
    if /i not "%%~nxf"=="add_header.bat" (

        echo Processing: %%f

        REM Check if header already exists
        findstr /c:"SB3PM Advisory" "%%f" >nul
        if errorlevel 1 (

            REM Backup
            copy "%%f" "%%f.bak" >nul

            REM Create temp file
            (
                echo %HEADER%
                echo %HEADER2%
                echo %HEADER3%
                echo %HEADER4%
                echo %HEADER5%
                echo %HEADER6%
                echo %HEADER7%
                echo.
                type "%%f"
            ) > "%%f.tmp"

            move /y "%%f.tmp" "%%f" >nul

            echo   ✔ header added

        ) else (
            echo   → already has header
        )
    )
)

echo.
echo DONE.
pause