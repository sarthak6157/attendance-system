@echo off
echo ========================================
echo   Smart Attendance System - Starting...
echo ========================================
cd backend
pip install -r requirements.txt
echo.
echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop
echo.
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
