@echo off

echo Creating AIJobHunter project structure...

cd /d C:\projects\aijobhunter

mkdir config
mkdir crawlers
mkdir parsers
mkdir scoring
mkdir database
mkdir reporting
mkdir logs
mkdir scripts

echo Creating placeholder files...

type nul > config\sources.json

type nul > crawlers\linkedin_crawler.py
type nul > crawlers\recruiter_crawler.py
type nul > crawlers\freelance_crawler.py

type nul > parsers\ai_job_parser.py

type nul > scoring\job_match_engine.py

type nul > database\jobs.db

type nul > reporting\daily_digest.py

type nul > run_daily_agent.py

type nul > requirements.txt
type nul > README.md

echo.
echo AIJobHunter structure created successfully.
echo.
pause
