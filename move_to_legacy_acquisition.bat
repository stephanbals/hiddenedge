@echo off
echo ========================================
echo AIJobHunter V4 - Move Acquisition Layer
echo ========================================

REM Create target folder
if not exist legacy_acquisition mkdir legacy_acquisition

echo.
echo Moving acquisition FOLDERS...

REM === Move crawler / scraping related folders ===
if exist crawlers move crawlers legacy_acquisition\
if exist scripts move scripts legacy_acquisition\

echo.
echo Moving acquisition FILES...

REM === Move crawler creation / agent runners ===
if exist create_crawler.py move create_crawler.py legacy_acquisition\
if exist create_recruiter_crawler.bat move create_recruiter_crawler.bat legacy_acquisition\

if exist run_agency_agent.py move run_agency_agent.py legacy_acquisition\
if exist run_agency_playwright.py move run_agency_playwright.py legacy_acquisition\
if exist run_arbeidnow_agent.py move run_arbeidnow_agent.py legacy_acquisition\
if exist run_daily_agent.py move run_daily_agent.py legacy_acquisition\
if exist run_indeed_agent.py move run_indeed_agent.py legacy_acquisition\
if exist run_multi_source_agent.py move run_multi_source_agent.py legacy_acquisition\
if exist run_playwright_agent.py move run_playwright_agent.py legacy_acquisition\

REM === Move source configs for crawling ===
if exist sources.json move sources.json legacy_acquisition\

echo.
echo ========================================
echo Move complete.
echo ========================================
echo.
echo IMPORTANT:
echo - Core decision engine is untouched
echo - Crawlers are now isolated
echo - Nothing has been deleted
echo.
pause