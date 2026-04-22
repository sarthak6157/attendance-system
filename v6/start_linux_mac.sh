#!/bin/bash
echo "============================================"
echo "  Smart Attendance System - TMU"
echo "============================================"
echo ""

cd "$(dirname "$0")/backend"

echo "Checking Python..."
python3 --version || { echo "Python3 not found!"; exit 1; }

echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt --quiet

echo ""
echo "Starting server..."
echo ""
echo "============================================"
echo "  Open your browser and go to:"
echo "  http://localhost:8000"
echo "============================================"
echo ""

# Auto open browser
if command -v xdg-open &>/dev/null; then
    sleep 2 && xdg-open http://localhost:8000 &
elif command -v open &>/dev/null; then
    sleep 2 && open http://localhost:8000 &
fi

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
