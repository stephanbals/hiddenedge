@echo off

echo =========================================
echo HiddenEdge Git Deployment Preparation
echo =========================================

REM =========================================
REM UNSTAGE NON-PRODUCTION FILES
REM =========================================

git restore --staged add_header.bat
git restore --staged fix_html_headers.bat
git restore --staged fix_python_headers.bat
git restore --staged debug_gulp.html
git restore --staged cv.txt
git restore --staged job.txt
git restore --staged word_log.txt


REM =========================================
REM ADD ALL VALID PROJECT FILES
REM =========================================

git add .

REM =========================================
REM SHOW FINAL STATUS
REM =========================================

echo.
echo =========================================
echo FINAL GIT STATUS
echo =========================================

git status

pause