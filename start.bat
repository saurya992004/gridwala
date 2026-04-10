@echo off
echo ===================================================
echo     NEXUS GRID - AlgoFest 2026 Boot Sequence
echo ===================================================

echo [1/2] Spinning up FastAPI Physics Engine...
start "Nexus Grid Backend" cmd /k "cd /d %~dp0nexus-grid\backend && if not exist venv python -m venv venv && call venv\Scripts\activate && python -m pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/2] Launching Next.js Command Center...
start "Nexus Grid Frontend" cmd /k "cd /d %~dp0nexus-grid\frontend && npm install && npm run dev"

echo.
echo All systems go! The Command Center will open shortly at http://localhost:3000
echo APIs and WebSockets are streaming on http://localhost:8000
echo.
pause
