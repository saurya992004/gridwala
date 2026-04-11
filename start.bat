@echo off
setlocal

echo ===================================================
echo     NEXUS GRID - Local Judge Boot Sequence
echo ===================================================

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js and npm were not found in PATH.
  echo Install Node.js 20+ from https://nodejs.org/ and run this file again.
  pause
  exit /b 1
)

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3.11"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
  echo [ERROR] Python 3.11+ was not found in PATH.
  echo Install Python from https://www.python.org/downloads/ and run this file again.
  pause
  exit /b 1
)

echo [1/2] Spinning up FastAPI backend...
start "NexusGrid Backend" cmd /k "cd /d %~dp0nexus-grid\backend && if not exist venv %PYTHON_CMD% -m venv venv && call venv\Scripts\activate && python -m pip install --upgrade pip && python -m pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/2] Launching Next.js frontend...
start "NexusGrid Frontend" cmd /k "cd /d %~dp0nexus-grid\frontend && npm install && npm run dev"

echo.
echo NEXUS GRID is starting.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo.
echo First run can take a few minutes because Python packages and Next.js deps are installed automatically.
echo Keep both terminal windows open while using the app.
echo.
pause
