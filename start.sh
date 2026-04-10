#!/bin/bash
set -e

echo "==================================================="
echo "    NEXUS GRID - AlgoFest 2026 Boot Sequence"
echo "==================================================="

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/2] Spinning up FastAPI Physics Engine (Background)..."
cd "$ROOT_DIR/nexus-grid/backend"
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
trap "kill $BACKEND_PID" EXIT
cd "$ROOT_DIR"

echo "[2/2] Launching Next.js Command Center..."
cd "$ROOT_DIR/nexus-grid/frontend"
npm install --silent
echo "All systems go! Command Center opening on http://localhost:3000"
npm run dev
