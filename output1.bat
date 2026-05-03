@echo off
set OUTPUT=project_overview.txt

echo ============================== > %OUTPUT%
echo PROJECT STRUCTURE >> %OUTPUT%
echo ============================== >> %OUTPUT%
tree /F /A >> %OUTPUT%

echo. >> %OUTPUT%
echo ============================== >> %OUTPUT%
echo FILE CONTENTS >> %OUTPUT%
echo ============================== >> %OUTPUT%

for /r %%f in (*.py *.js *.jsx *.ts *.tsx *.json *.md) do (
    echo. >> %OUTPUT%
    echo ============================== >> %OUTPUT%
    echo FILE: %%f >> %OUTPUT%
    echo ============================== >> %OUTPUT%
    type "%%f" >> %OUTPUT%
)

echo Done. Output written to %OUTPUT%
pause