@echo off

cd /d C:\Projects\AIJobHunter

echo =============================
echo Starting AIJobHunter Server
echo =============================

call venv\Scripts\activate

start "" cmd /c python dashboard_server.py

timeout /t 4 > nul

start chrome http://localhost:8000

exit
