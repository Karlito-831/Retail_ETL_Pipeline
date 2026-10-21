@echo off
cd /d "%~dp0"
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if exist "..\.venv\Scripts\python.exe" set "PY=..\.venv\Scripts\python.exe"
start "Traditional ETL - 5001" cmd /k ""%PY%" traditional_app.py"
start "Proposed ETL - 5000" cmd /k ""%PY%" app.py"
echo Traditional ETL: http://127.0.0.1:5001
echo Proposed ETL: http://127.0.0.1:5000
echo Proposed website requires .env and running PostgreSQL.
pause
