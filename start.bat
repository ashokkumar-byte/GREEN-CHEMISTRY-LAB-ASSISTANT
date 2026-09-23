@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
)
echo Installing requirements...
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if not exist "database" mkdir "database"
echo Starting Green Chemistry Lab Assistant...
echo Open http://127.0.0.1:5000 in your browser
.venv\Scripts\python.exe backend\app.py
pause
