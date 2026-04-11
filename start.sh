#!/bin/bash
set -e

echo "==================================================="
echo "    NEXUS GRID - Local Judge Boot Sequence"
echo "==================================================="

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 was not found. Install Python 3.11+ and run again."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] npm was not found. Install Node.js 20+ and run again."
  exit 1
fi

echo "[1/2] Starting FastAPI backend..."
cd "$ROOT_DIR/nexus-grid/backend"
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
trap "kill $BACKEND_PID" EXIT

echo "[2/2] Starting Next.js frontend..."
cd "$ROOT_DIR/nexus-grid/frontend"
npm install
echo "NEXUS GRID is starting."
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "Keep this terminal open while the frontend runs."
npm run dev
