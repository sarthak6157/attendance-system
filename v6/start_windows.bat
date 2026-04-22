@echo off
echo ============================================
echo   Smart Attendance System - TMU
echo ============================================
echo.

cd /d "%~dp0backend"

echo Checking Python...
python --version 2>nul || (echo Python not found! Install from python.org && pause && exit)

echo.
echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo Starting server...
echo.
echo ============================================
echo   Open your browser and go to:
echo   http://localhost:8000
echo ============================================
echo.
start "" "http://localhost:8000"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
