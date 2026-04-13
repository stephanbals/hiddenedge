@echo off
echo ========================================
echo AIJobHunter V4 - Move CV Engine to legacy_cv
echo ========================================

REM Create target folder
if not exist legacy_cv mkdir legacy_cv

echo.
echo Moving CV-related FILES...

REM === analysis folder files ===
if exist analysis\cv_tailor.py move analysis\cv_tailor.py legacy_cv\
if exist analysis\role_rewriter.py move analysis\role_rewriter.py legacy_cv\
if exist analysis\controlled_impact_layer.py move analysis\controlled_impact_layer.py legacy_cv\
if exist analysis\cv_parser.py move analysis\cv_parser.py legacy_cv\
if exist analysis\cv_formatter.py move analysis\cv_formatter.py legacy_cv\
if exist analysis\cv_enhancer.py move analysis\cv_enhancer.py legacy_cv\
if exist analysis\cv_writer.py move analysis\cv_writer.py legacy_cv\

echo.
echo Moving CV-related FOLDERS...

REM === core folder ===
if exist core\cv (
    move core\cv legacy_cv\
)

if exist core\rewrite (
    move core\rewrite legacy_cv\
)

if exist core\generation (
    move core\generation legacy_cv\
)

REM === templates ===
if exist templates (
    echo Moving templates folder...
    move templates legacy_cv\
)

echo.
echo Moving CV-related ROUTES / ENDPOINT FILES...

REM Try common filenames (adjust if needed)
if exist tailor_cv.py move tailor_cv.py legacy_cv\
if exist rewrite_cv.py move rewrite_cv.py legacy_cv\
if exist generate_cv.py move generate_cv.py legacy_cv\
if exist download_cv.py move download_cv.py legacy_cv\

echo.
echo Moving CV-related FRONTEND files...

if exist cv_editor.html move cv_editor.html legacy_cv\
if exist cv_preview.html move cv_preview.html legacy_cv\
if exist download_cv.js move download_cv.js legacy_cv\

echo.
echo ========================================
echo Move complete.
echo ========================================
echo.
echo IMPORTANT:
echo - Nothing is deleted
echo - All moved items are in /legacy_cv
echo - Review before permanent cleanup
echo.
pause